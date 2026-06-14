"""
Endpoints de Configuración del sistema CMMS-BioAI.

Configuración:
    - GET  /configuracion/                  → Lee la configuración actual
    - PUT  /configuracion/                  → Actualiza la configuración
    - GET  /configuracion/estados-bd        → Resumen de registros en la BD por tabla

Capa 2 — Escaneo y recuperación:
    - GET  /configuracion/escanear          → Escanea .meta.json y reporta estado
    - POST /configuracion/recuperar         → Recupera registros huérfanos desde .meta.json

Capa 3 — Backup y Restore:
    - GET  /configuracion/backup            → Exporta la BD completa como JSON
    - POST /configuracion/restore           → Importa un backup JSON y restaura la BD
    - GET  /configuracion/backup/descargar  → Descarga backup como archivo
    - POST /configuracion/restore/subir     → Restaura subiendo archivo JSON

Mover archivos:
    - POST /configuracion/mover-archivos    → Mueve archivos entre ubicaciones de uploads_base
"""
import json
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Request
from sqlmodel import Session, select
from starlette.routing import Mount
from fastapi.staticfiles import StaticFiles

from config import get_dir, get_config, update_config, BACKEND_DIR, UPLOADS_DIR
from database import engine
from models.equipos import Equipo
from models.repuestos import Repuesto, OtRepuestoUtilizado
from models.herramientas import Herramienta
from models.documentos import DocumentoAdjunto
from models.ordenes import OrdenTrabajo, EstadoOT
from models.estados import EstadoEquipo
from models.preventivo import TareaPreventiva, TareaRepuesto
from models.historial import EventoHistorial
from models.users import Usuario

router = APIRouter(prefix="/configuracion", tags=["Configuracion"])


# ──────────────────────────────────────────────────────────
# Utilidades internas
# ──────────────────────────────────────────────────────────

def _remount_uploads(app):
    """
    Re-monta el directorio de archivos estaticos /uploads.
    
    Se debe llamar despues de cambiar uploads_base en config.json.
    Esto permite que las imagenes y documentos se sirvan desde la
    nueva ubicacion SIN necesidad de reiniciar el backend.
    
    Como funciona:
        1. Elimina el mount viejo de /uploads
        2. Crea un nuevo mount apuntando al uploads_base actual
    """
    new_path = str(get_dir("uploads_base"))
    
    # Eliminar el mount viejo de /uploads
    app.routes = [
        route for route in app.routes
        if not (isinstance(route, Mount) and route.path == "/uploads")
    ]
    
    # Agregar el nuevo mount
    app.mount("/uploads", StaticFiles(directory=new_path), name="uploads")


def _date_to_str(obj):
    """Convierte date/datetime a string para serialización JSON."""
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    return obj


def _model_to_dict(instance) -> dict:
    """Convierte un modelo SQLModel a diccionario, manejando tipos especiales."""
    d = {}
    for key, value in instance.model_dump().items():
        d[key] = _date_to_str(value)
    return d


# ──────────────────────────────────────────────────────────
# GET /configuracion/ — Leer configuración actual
# ──────────────────────────────────────────────────────────

@router.get("/")
def get_configuracion():
    """Devuelve la configuración actual del sistema (config.json)."""
    return get_config()


# ──────────────────────────────────────────────────────────
# PUT /configuracion/ — Actualizar configuración
# ──────────────────────────────────────────────────────────

@router.put("/")
def put_configuracion(new_config: dict, request: Request):
    """
    Actualiza la configuración del sistema y la guarda en config.json.
    
    Solo permite actualizar:
        - empresa.nombre (nombre del sistema)
        - directorios.uploads_base (carpeta base de almacenamiento)
    
    Las sub-carpetas (EQUIPOS, REPUESTOS, etc.) son fijas y relativas a uploads_base.
    Los campos sistema.* son de solo lectura.
    
    Si uploads_base cambia, el sistema re-monta automaticamente los archivos
    estaticos sin necesidad de reiniciar el backend.
    
    Parametro opcional en new_config:
        - mover_archivos: true  → mueve los archivos de la ubicacion anterior a la nueva
        - mover_archivos: false → solo cambia la config (el usuario movera los archivos)
    """
    current = get_config()
    old_uploads_base = current.get("directorios", {}).get("uploads_base", "uploads")
    
    # Construir la nueva configuración, solo permitiendo campos editables
    merged = {
        "empresa": {"nombre": current.get("empresa", {}).get("nombre", "CMMS-BioAI")},
        "directorios": dict(current.get("directorios", {})),
        "sistema": current.get("sistema", {})  # No modificar nunca
    }
    
    # Actualizar empresa.nombre si viene
    if "empresa" in new_config and "nombre" in new_config["empresa"]:
        nombre = new_config["empresa"]["nombre"].strip()
        if not nombre:
            raise HTTPException(status_code=400, detail="El nombre del sistema no puede estar vacío")
        merged["empresa"]["nombre"] = nombre
    
    # Detectar si uploads_base va a cambiar
    uploads_base_changed = False
    new_uploads_base = None
    
    # Actualizar uploads_base si viene
    if "directorios" in new_config and "uploads_base" in new_config["directorios"]:
        uploads_base = new_config["directorios"]["uploads_base"].strip()
        if not uploads_base:
            raise HTTPException(status_code=400, detail="La carpeta base no puede estar vacía")
        
        # Verificar que la ruta es válida y escribible
        test_path = Path(uploads_base) if Path(uploads_base).is_absolute() else BACKEND_DIR / uploads_base
        try:
            test_path.mkdir(parents=True, exist_ok=True)
            test_file = test_path / ".cmms_write_test"
            test_file.write_text("test")
            test_file.unlink()
        except (OSError, PermissionError) as e:
            raise HTTPException(
                status_code=400, 
                detail=f"No se puede escribir en la ruta '{uploads_base}': {str(e)}"
            )
        
        if uploads_base != old_uploads_base:
            uploads_base_changed = True
            new_uploads_base = uploads_base
        
        merged["directorios"]["uploads_base"] = uploads_base
    
    try:
        update_config(merged)
        
        mensaje = "Configuración actualizada correctamente"
        archivos_movidos = False
        requiere_reinicio = False
        
        # Si uploads_base cambio, mover archivos y re-montar
        if uploads_base_changed and new_uploads_base:
            # Determinar si se deben mover los archivos
            mover = new_config.get("mover_archivos", True)  # Por defecto: mover
            
            old_path = Path(old_uploads_base) if Path(old_uploads_base).is_absolute() else BACKEND_DIR / old_uploads_base
            new_path = Path(new_uploads_base) if Path(new_uploads_base).is_absolute() else BACKEND_DIR / new_uploads_base
            old_path = old_path.resolve()
            new_path = new_path.resolve()
            
            if mover and old_path.exists() and old_path != new_path:
                # Mover archivos de la ubicacion anterior a la nueva
                try:
                    archivos_origen = [f for f in old_path.rglob("*") if f.is_file()]
                    total_archivos = len(archivos_origen)
                    
                    if total_archivos > 0:
                        # Verificar espacio en destino
                        total_bytes = sum(f.stat().st_size for f in archivos_origen)
                        destino_stat = shutil.disk_usage(new_path)
                        if total_bytes > destino_stat.free:
                            mensaje += f". ADVERTENCIA: Espacio insuficiente en '{new_uploads_base}'. Los archivos NO se movieron. Mueva los archivos manualmente."
                        else:
                            # FASE 1: Copiar archivos
                            copiados = 0
                            errores_copia = []
                            for archivo in archivos_origen:
                                try:
                                    rel_path = archivo.relative_to(old_path)
                                    destino_file = new_path / rel_path
                                    destino_file.parent.mkdir(parents=True, exist_ok=True)
                                    shutil.copy2(str(archivo), str(destino_file))
                                    copiados += 1
                                except Exception as e:
                                    errores_copia.append(str(e))
                            
                            if errores_copia:
                                mensaje += f". ADVERTENCIA: {len(errores_copia)} errores al copiar archivos. Los archivos originales NO se eliminaron."
                            else:
                                # FASE 2: Verificar copia
                                archivos_destino = [f for f in new_path.rglob("*") if f.is_file()]
                                if len(archivos_destino) >= total_archivos:
                                    # FASE 3: Eliminar originales
                                    try:
                                        shutil.rmtree(str(old_path))
                                        archivos_movidos = True
                                        mensaje += f". Se movieron {copiados} archivos de '{old_uploads_base}' a '{new_uploads_base}'."
                                    except Exception as e:
                                        archivos_movidos = True
                                        mensaje += f". Archivos copiados a '{new_uploads_base}' pero no se pudo eliminar la carpeta original: {str(e)}."
                                else:
                                    mensaje += f". ADVERTENCIA: Verificacion fallida. Los archivos originales NO se eliminaron."
                    else:
                        mensaje += f". La carpeta anterior '{old_uploads_base}' estaba vacia."
                except Exception as e:
                    mensaje += f". ADVERTENCIA: Error al mover archivos: {str(e)}. Mueva los archivos manualmente."
            elif not mover:
                mensaje += f". Los archivos NO se movieron automaticamente. Mueva los archivos de '{old_uploads_base}' a '{new_uploads_base}' manualmente."
            
            # Re-montar archivos estaticos (sin necesidad de reiniciar)
            try:
                _remount_uploads(request.app)
                mensaje += " Archivos estaticos recargados automaticamente (no es necesario reiniciar)."
            except Exception as e:
                requiere_reinicio = True
                mensaje += f". ADVERTENCIA: No se pudo recargar la ubicacion de archivos. Reinicie el backend: {str(e)}"
        
        return {
            "mensaje": mensaje,
            "config": get_config(),
            "archivos_movidos": archivos_movidos,
            "requiere_reinicio": requiere_reinicio
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar configuración: {str(e)}")


# ──────────────────────────────────────────────────────────
# POST /configuracion/mover-archivos — Mover archivos a nueva ubicación
# ──────────────────────────────────────────────────────────

@router.post("/mover-archivos")
def mover_archivos(data: dict, request: Request):
    """
    Mueve todos los archivos de la ubicación anterior de uploads_base a la nueva.
    
    El body debe contener: { "origen": "ruta_anterior", "destino": "ruta_nueva" }
    
    Estrategia segura:
    1. Copiar todos los archivos al destino
    2. Verificar que la copia fue exitosa
    3. Eliminar los archivos originales solo si la copia fue completa
    4. Actualizar config.json con la nueva ubicacion
    5. Re-montar archivos estaticos (sin reiniciar)
    """
    origen_rel = data.get("origen")
    destino_rel = data.get("destino")
    
    if not origen_rel or not destino_rel:
        raise HTTPException(status_code=400, detail="Se requieren 'origen' y 'destino'")
    
    # Construir rutas absolutas
    origen_abs = Path(origen_rel) if Path(origen_rel).is_absolute() else BACKEND_DIR / origen_rel
    destino_abs = Path(destino_rel) if Path(destino_rel).is_absolute() else BACKEND_DIR / destino_rel
    
    # Normalizar rutas
    origen_abs = origen_abs.resolve()
    destino_abs = destino_abs.resolve()
    
    if origen_abs == destino_abs:
        raise HTTPException(status_code=400, detail="El origen y destino son la misma ruta")
    
    if not origen_abs.exists():
        raise HTTPException(status_code=400, detail=f"La ruta de origen no existe: {origen_abs}")
    
    # Verificar permisos de escritura en destino
    try:
        destino_abs.mkdir(parents=True, exist_ok=True)
        test_file = destino_abs / ".cmms_move_test"
        test_file.write_text("test")
        test_file.unlink()
    except (OSError, PermissionError) as e:
        raise HTTPException(status_code=400, detail=f"Sin permisos de escritura en destino: {str(e)}")
    
    # Contar archivos a mover
    archivos_origen = [f for f in origen_abs.rglob("*") if f.is_file()]
    total_archivos = len(archivos_origen)
    total_bytes = sum(f.stat().st_size for f in archivos_origen)
    
    if total_archivos == 0:
        return {
            "mensaje": "No hay archivos para mover (carpeta de origen vacía)",
            "archivos_movidos": 0,
            "bytes_movidos": 0
        }
    
    # Verificar espacio disponible en destino
    destino_stat = shutil.disk_usage(destino_abs)
    if total_bytes > destino_stat.free:
        raise HTTPException(
            status_code=400,
            detail=f"Espacio insuficiente en destino. Necesario: {total_bytes:,} bytes, Disponible: {destino_stat.free:,} bytes"
        )
    
    # FASE 1: Copiar archivos al destino
    copiados = 0
    errores_copia = []
    
    for archivo in archivos_origen:
        try:
            # Calcular ruta relativa al origen
            rel_path = archivo.relative_to(origen_abs)
            destino_file = destino_abs / rel_path
            
            # Crear directorio padre si no existe
            destino_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Copiar archivo
            shutil.copy2(str(archivo), str(destino_file))
            copiados += 1
        except Exception as e:
            errores_copia.append(f"Error copiando {archivo.name}: {str(e)}")
    
    if errores_copia:
        # Limpiar archivos copiados si hubo errores
        for archivo in archivos_origen:
            try:
                rel_path = archivo.relative_to(origen_abs)
                destino_file = destino_abs / rel_path
                if destino_file.exists():
                    destino_file.unlink()
            except:
                pass
        raise HTTPException(
            status_code=500,
            detail=f"Errores durante la copia ({len(errores_copia)}). Operación cancelada. Errores: {errores_copia[:5]}"
        )
    
    # FASE 2: Verificar integridad (comparar cantidad de archivos)
    archivos_destino = [f for f in destino_abs.rglob("*") if f.is_file()]
    if len(archivos_destino) != total_archivos + (1 if (destino_abs / ".cmms_move_test").exists() else 0):
        # No coincide, no eliminar origen
        raise HTTPException(
            status_code=500,
            detail=f"Verificación fallida: se copiaron {len(archivos_destino)} archivos pero se esperaban {total_archivos}. Los archivos originales NO se eliminaron."
        )
    
    # FASE 3: Eliminar archivos originales (la copia fue exitosa)
    try:
        shutil.rmtree(str(origen_abs))
    except Exception as e:
        # No es crítico — los archivos están en ambos lugares
        return {
            "mensaje": f"Archivos copiados exitosamente pero no se pudo eliminar la carpeta original: {str(e)}",
            "archivos_movidos": copiados,
            "bytes_movidos": total_bytes,
            "origen_mantenido": True
        }
    
    # Actualizar config.json con la nueva ubicacion (destino)
    current = get_config()
    destino_config = data.get("destino", "")
    if destino_config:
        current["directorios"]["uploads_base"] = destino_config
        update_config(current)
    
    # Re-montar archivos estaticos (sin necesidad de reiniciar)
    requiere_reinicio = False
    try:
        _remount_uploads(request.app)
    except Exception as e:
        requiere_reinicio = True
    
    mensaje = "Archivos movidos exitosamente"
    if requiere_reinicio:
        mensaje += ". ADVERTENCIA: No se pudo recargar la ubicacion. Reinicie el backend."
    else:
        mensaje += " Archivos estaticos recargados automaticamente (no es necesario reiniciar)."
    
    return {
        "mensaje": mensaje,
        "archivos_movidos": copiados,
        "bytes_movidos": total_bytes,
        "origen": str(origen_abs),
        "destino": str(destino_abs),
        "requiere_reinicio": requiere_reinicio
    }


# ──────────────────────────────────────────────────────────
# GET /configuracion/estados-bd — Resumen de registros en BD
# ──────────────────────────────────────────────────────────

@router.get("/estados-bd")
def get_estados_bd():
    """Devuelve un resumen de la cantidad de registros por tabla en la BD."""
    with Session(engine) as session:
        return {
            "equipos": len(session.exec(select(Equipo)).all()),
            "repuestos": len(session.exec(select(Repuesto)).all()),
            "herramientas": len(session.exec(select(Herramienta)).all()),
            "ordenes_trabajo": len(session.exec(select(OrdenTrabajo)).all()),
            "documentos": len(session.exec(select(DocumentoAdjunto)).all()),
            "eventos_historial": len(session.exec(select(EventoHistorial)).all()),
            "tareas_preventivas": len(session.exec(select(TareaPreventiva)).all()),
            "usuarios": len(session.exec(select(Usuario)).all()),
            "estados_equipo": len(session.exec(select(EstadoEquipo)).all()),
            "estados_ot": len(session.exec(select(EstadoOT)).all()),
        }


# ──────────────────────────────────────────────────────────
# CAPA 2: Escaneo y Recuperación
# ──────────────────────────────────────────────────────────

@router.get("/escanear")
def escanear_meta_json():
    """
    Escanea todos los archivos .meta.json en el directorio uploads
    y los compara con los registros existentes en la BD.
    """
    resultados = {
        "equipos": {"en_archivos": [], "en_bd": 0, "huerfanos": []},
        "repuestos": {"en_archivos": [], "en_bd": 0, "huerfanos": []},
        "herramientas": {"en_archivos": [], "en_bd": 0, "huerfanos": []},
        "documentos": {"en_archivos": [], "en_bd": 0, "huerfanos": []},
    }

    with Session(engine) as session:
        ids_equipos_bd = set(e.id for e in session.exec(select(Equipo)).all())
        ids_repuestos_bd = set(r.id for r in session.exec(select(Repuesto)).all())
        ids_herramientas_bd = set(h.id for h in session.exec(select(Herramienta)).all())
        ids_docs_bd = set(d.id for d in session.exec(select(DocumentoAdjunto)).all())

        resultados["equipos"]["en_bd"] = len(ids_equipos_bd)
        resultados["repuestos"]["en_bd"] = len(ids_repuestos_bd)
        resultados["herramientas"]["en_bd"] = len(ids_herramientas_bd)
        resultados["documentos"]["en_bd"] = len(ids_docs_bd)

    uploads_base = UPLOADS_DIR

    carpetas_entidad = {
        "EQUIPOS": "equipos",
        "REPUESTOS": "repuestos",
        "HERRAMIENTAS": "herramientas",
    }

    for carpeta_nombre, tipo in carpetas_entidad.items():
        carpeta = uploads_base / carpeta_nombre
        if not carpeta.exists():
            continue

        for subdir in sorted(carpeta.iterdir()):
            if not subdir.is_dir():
                continue

            meta_path = subdir / ".meta.json"
            if not meta_path.exists():
                continue

            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    meta = json.load(f)
            except (json.JSONDecodeError, IOError):
                continue

            entidad_id = meta.get("id")
            if entidad_id is None:
                continue

            info = {
                "id": entidad_id,
                "carpeta": str(subdir.relative_to(uploads_base)),
                "nombre": meta.get("nombre_corto") or meta.get("nombre_repuesto") or meta.get("nombre_herramienta") or subdir.name,
                "tipo_meta": meta.get("tipo", tipo),
            }

            resultados[tipo]["en_archivos"].append(info)

            ids_bd = {
                "equipos": ids_equipos_bd,
                "repuestos": ids_repuestos_bd,
                "herramientas": ids_herramientas_bd,
            }.get(tipo, set())

            if entidad_id not in ids_bd:
                resultados[tipo]["huerfanos"].append(info)

            # Escanear documentos en subcarpeta DOC/
            doc_dir = subdir / "DOC"
            if doc_dir.exists():
                doc_meta_path = doc_dir / ".meta.json"
                if doc_meta_path.exists():
                    try:
                        with open(doc_meta_path, "r", encoding="utf-8") as f:
                            doc_meta = json.load(f)
                        for doc_entry in doc_meta.get("documentos", []):
                            doc_id = doc_entry.get("documento_id")
                            doc_info = {
                                "id": doc_id,
                                "nombre_archivo": doc_entry.get("nombre_archivo"),
                                "entidad_tipo": tipo,
                                "entidad_id": entidad_id,
                                "carpeta": str(doc_dir.relative_to(uploads_base)),
                            }
                            resultados["documentos"]["en_archivos"].append(doc_info)
                            if doc_id not in ids_docs_bd:
                                resultados["documentos"]["huerfanos"].append(doc_info)
                    except (json.JSONDecodeError, IOError):
                        pass

    resumen = {
        "total_en_archivos": sum(len(v["en_archivos"]) for v in resultados.values() if v != resultados["documentos"]),
        "total_en_bd": sum(v["en_bd"] for v in resultados.values() if v != resultados["documentos"]),
        "total_huerfanos": sum(len(v["huerfanos"]) for v in resultados.values()),
        "total_docs_en_archivos": len(resultados["documentos"]["en_archivos"]),
        "total_docs_huerfanos": len(resultados["documentos"]["huerfanos"]),
    }

    return {"resumen": resumen, "detalle": resultados}


@router.post("/recuperar")
def recuperar_desde_meta_json():
    """
    Recupera registros huérfanos desde los archivos .meta.json.
    Para cada entidad encontrada en archivos que no exista en la BD,
    crea el registro con los datos disponibles en el .meta.json.
    """
    recuperados = {
        "equipos": 0,
        "repuestos": 0,
        "herramientas": 0,
        "documentos": 0,
    }
    errores = []

    uploads_base = UPLOADS_DIR

    carpetas_entidad = {
        "EQUIPOS": ("equipos", Equipo),
        "REPUESTOS": ("repuestos", Repuesto),
        "HERRAMIENTAS": ("herramientas", Herramienta),
    }

    ids_recuperados = {"equipos": set(), "repuestos": set(), "herramientas": set()}

    with Session(engine) as session:
        for carpeta_nombre, (tipo, modelo) in carpetas_entidad.items():
            carpeta = uploads_base / carpeta_nombre
            if not carpeta.exists():
                continue

            for subdir in sorted(carpeta.iterdir()):
                if not subdir.is_dir():
                    continue

                meta_path = subdir / ".meta.json"
                if not meta_path.exists():
                    continue

                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except (json.JSONDecodeError, IOError) as e:
                    errores.append(f"Error leyendo {meta_path}: {str(e)}")
                    continue

                entidad_id = meta.get("id")
                if entidad_id is None:
                    continue

                existente = session.exec(select(modelo).where(modelo.id == entidad_id)).first()
                if existente:
                    continue

                try:
                    if tipo == "equipos":
                        registro = Equipo(
                            id=entidad_id,
                            nombre_corto=meta.get("nombre_corto"),
                            modelo=meta.get("modelo", "Sin modelo"),
                            numero_serie=meta.get("numero_serie", f"REC-{entidad_id}"),
                            numero_material=meta.get("numero_material"),
                            marca=meta.get("marca", "Sin marca"),
                            ubicacion_actual=meta.get("ubicacion_actual"),
                            estado_id=meta.get("estado_id", 1),
                            proveedor_principal=meta.get("proveedor_principal"),
                            registro_sanitario_bolivia=meta.get("registro_sanitario_bolivia"),
                            imagen_ruta=meta.get("imagen_ruta"),
                            fecha_adquisicion=meta.get("fecha_adquisicion", date(2000, 1, 1)),
                        )
                    elif tipo == "repuestos":
                        registro = Repuesto(
                            id=entidad_id,
                            nombre_repuesto=meta.get("nombre_repuesto", "Repuesto recuperado"),
                            numero_serie=meta.get("numero_serie"),
                            numero_material=meta.get("numero_material"),
                            descripcion=meta.get("descripcion"),
                            especificaciones_tecnicas=meta.get("especificaciones_tecnicas"),
                            cantidad_disponible=meta.get("cantidad_disponible", 0),
                            unidad_medida=meta.get("unidad_medida", "unidad"),
                            ubicacion_almacen=meta.get("ubicacion_almacen"),
                            nivel_stock_minimo=meta.get("nivel_stock_minimo"),
                            proveedor_ultimo=meta.get("proveedor_ultimo"),
                            imagen_ruta=meta.get("imagen_ruta"),
                        )
                    elif tipo == "herramientas":
                        registro = Herramienta(
                            id=entidad_id,
                            nombre_herramienta=meta.get("nombre_herramienta", "Herramienta recuperada"),
                            numero_identificacion=meta.get("numero_identificacion"),
                            descripcion=meta.get("descripcion"),
                            categoria=meta.get("categoria", "Herramienta Manual"),
                            cantidad_disponible=meta.get("cantidad_disponible", 1),
                            unidad_medida=meta.get("unidad_medida", "unidad"),
                            ubicacion_almacen=meta.get("ubicacion_almacen"),
                            estado_uso=meta.get("estado_uso", "Disponible"),
                            costo_adquisicion=meta.get("costo_adquisicion"),
                            proveedor_ultimo=meta.get("proveedor_ultimo"),
                            imagen_ruta=meta.get("imagen_ruta"),
                        )

                    session.add(registro)
                    ids_recuperados[tipo].add(entidad_id)
                    recuperados[tipo] += 1
                except Exception as e:
                    errores.append(f"Error recuperando {tipo} ID {entidad_id}: {str(e)}")

        # Paso 2: Recuperar documentos
        for carpeta_nombre, (tipo, modelo) in carpetas_entidad.items():
            carpeta = uploads_base / carpeta_nombre
            if not carpeta.exists():
                continue

            for subdir in sorted(carpeta.iterdir()):
                if not subdir.is_dir():
                    continue

                doc_dir = subdir / "DOC"
                doc_meta_path = doc_dir / ".meta.json"
                if not doc_meta_path.exists():
                    continue

                try:
                    with open(doc_meta_path, "r", encoding="utf-8") as f:
                        doc_meta = json.load(f)
                except (json.JSONDecodeError, IOError):
                    continue

                for doc_entry in doc_meta.get("documentos", []):
                    doc_id = doc_entry.get("documento_id")
                    if doc_id is None:
                        continue

                    existente = session.exec(
                        select(DocumentoAdjunto).where(DocumentoAdjunto.id == doc_id)
                    ).first()
                    if existente:
                        continue

                    padre_tipo = doc_entry.get("entidad_tipo", tipo)
                    padre_id = doc_entry.get("entidad_id")

                    if padre_tipo and padre_id:
                        padre_existe = padre_id in ids_recuperados.get(padre_tipo, set())
                        if not padre_existe:
                            modelo_padre = {
                                "equipos": Equipo,
                                "repuestos": Repuesto,
                                "herramientas": Herramienta,
                            }.get(padre_tipo)
                            if modelo_padre:
                                padre = session.exec(
                                    select(modelo_padre).where(modelo_padre.id == padre_id)
                                ).first()
                                padre_existe = padre is not None

                        if not padre_existe:
                            continue

                    try:
                        nombre_archivo = doc_entry.get("nombre_archivo", "")
                        ruta_archivo = doc_entry.get("ruta_archivo") or str(doc_dir.relative_to(uploads_base) / nombre_archivo)

                        doc_registro = DocumentoAdjunto(
                            id=doc_id,
                            nombre_archivo=nombre_archivo,
                            ruta_archivo=ruta_archivo,
                            tipo_archivo=doc_entry.get("tipo_archivo", "application/octet-stream"),
                            tamanio_bytes=doc_entry.get("tamanio_bytes", 0),
                            descripcion=doc_entry.get("descripcion"),
                            categoria=doc_entry.get("categoria"),
                            subido_por=doc_entry.get("subido_por"),
                            equipo_id=padre_id if padre_tipo == "equipos" else None,
                            repuesto_id=padre_id if padre_tipo == "repuestos" else None,
                            herramienta_id=padre_id if padre_tipo == "herramientas" else None,
                        )
                        session.add(doc_registro)
                        recuperados["documentos"] += 1
                    except Exception as e:
                        errores.append(f"Error recuperando documento ID {doc_id}: {str(e)}")

        session.commit()

    return {
        "mensaje": "Recuperación completada",
        "recuperados": recuperados,
        "total_recuperados": sum(recuperados.values()),
        "errores": errores,
    }


# ──────────────────────────────────────────────────────────
# CAPA 3: Backup y Restore
# ──────────────────────────────────────────────────────────

@router.get("/backup")
def generar_backup():
    """
    Exporta toda la base de datos y la configuración como un diccionario JSON.
    Cada tabla se exporta como una lista de diccionarios.
    La configuración (config.json) se incluye para permitir restauración completa.
    """
    backup = {
        "metadatos": {
            "sistema": "CMMS-BioAI",
            "version": "1.1",
            "fecha_backup": datetime.now().isoformat(),
            "descripcion": "Backup completo de la base de datos y configuración",
        },
        "configuracion": get_config(),
        "datos": {}
    }

    tablas = [
        ("estados_equipo", EstadoEquipo),
        ("estados_ot", EstadoOT),
        ("usuarios", Usuario),
        ("equipos", Equipo),
        ("repuestos", Repuesto),
        ("herramientas", Herramienta),
        ("ordenes_trabajo", OrdenTrabajo),
        ("documentos", DocumentoAdjunto),
        ("eventos_historial", EventoHistorial),
        ("tareas_preventivas", TareaPreventiva),
        ("tareas_repuestos", TareaRepuesto),
        ("ot_repuestos_utilizados", OtRepuestoUtilizado),
    ]

    with Session(engine) as session:
        for nombre, modelo in tablas:
            registros = session.exec(select(modelo)).all()
            backup["datos"][nombre] = [_model_to_dict(r) for r in registros]

    backup["metadatos"]["totales"] = {
        nombre: len(registros) for nombre, registros in backup["datos"].items()
    }

    # Incluir conteo de configuración en metadatos
    backup["metadatos"]["incluye_configuracion"] = True

    return backup


@router.post("/restore")
def restaurar_backup(backup_data: dict):
    """
    Restaura la base de datos y la configuración desde un backup JSON.
    ADVERTENCIA: Esta operación elimina todos los datos existentes.
    
    Si el backup contiene la clave 'configuracion', también restaura config.json.
    Si no la contiene (backups antiguos), solo restaura la BD (retrocompatible).
    """
    if "datos" not in backup_data:
        raise HTTPException(status_code=400, detail="El backup no tiene la estructura esperada (falta clave 'datos')")

    datos = backup_data["datos"]
    restaurados = {}
    errores = []
    config_restaurada = False

    # Restaurar configuración si está presente en el backup
    # IMPORTANTE: Se preserva el uploads_base actual del sistema, ya que los
    # archivos fisicos pueden estar en una ubicacion diferente a la del backup.
    # Las rutas en la BD son RELATIVAS a uploads_base, asi que funcionan
    # sin importar donde esten los archivos, siempre que existan fisicamente.
    if "configuracion" in backup_data:
        try:
            config_backup = backup_data["configuracion"]
            # Validar estructura mínima
            if isinstance(config_backup, dict) and ("empresa" in config_backup or "directorios" in config_backup):
                current = get_config()
                # Preservar el uploads_base ACTUAL (no sobrescribir con el del backup)
                current_uploads_base = current.get("directorios", {}).get("uploads_base", "uploads")
                merged = {
                    "empresa": config_backup.get("empresa", current.get("empresa", {})),
                    "directorios": config_backup.get("directorios", current.get("directorios", {})),
                    "sistema": config_backup.get("sistema", current.get("sistema", {})),
                }
                # Siempre preservar el uploads_base actual
                merged["directorios"]["uploads_base"] = current_uploads_base
                update_config(merged)
                config_restaurada = True
        except Exception as e:
            errores.append(f"Error restaurando configuración: {str(e)}")

    orden_tablas = [
        ("estados_equipo", EstadoEquipo),
        ("estados_ot", EstadoOT),
        ("usuarios", Usuario),
        ("equipos", Equipo),
        ("repuestos", Repuesto),
        ("herramientas", Herramienta),
        ("ordenes_trabajo", OrdenTrabajo),
        ("documentos", DocumentoAdjunto),
        ("eventos_historial", EventoHistorial),
        ("tareas_preventivas", TareaPreventiva),
        ("tareas_repuestos", TareaRepuesto),
        ("ot_repuestos_utilizados", OtRepuestoUtilizado),
    ]

    with Session(engine) as session:
        # Limpiar tablas en orden inverso (hijas primero)
        for nombre, modelo in reversed(orden_tablas):
            if nombre in datos:
                for registro in session.exec(select(modelo)).all():
                    session.delete(registro)

        session.commit()

        # Insertar datos en orden (padres primero)
        for nombre, modelo in orden_tablas:
            if nombre not in datos:
                continue

            count = 0
            for registro_dict in datos[nombre]:
                try:
                    campos_modelo = set(modelo.model_fields.keys())
                    datos_filtrados = {k: v for k, v in registro_dict.items() if k in campos_modelo}

                    # Manejar campos fecha
                    for key, value in datos_filtrados.items():
                        if value is not None and isinstance(value, str):
                            field_info = modelo.model_fields.get(key)
                            if field_info:
                                annotation = str(field_info.annotation)
                                if "date" in annotation.lower() and "time" not in annotation.lower():
                                    try:
                                        datos_filtrados[key] = date.fromisoformat(value)
                                    except (ValueError, TypeError):
                                        pass
                                elif "datetime" in annotation.lower():
                                    try:
                                        datos_filtrados[key] = datetime.fromisoformat(value)
                                    except (ValueError, TypeError):
                                        pass

                    registro = modelo(**datos_filtrados)
                    session.add(registro)
                    count += 1
                except Exception as e:
                    errores.append(f"Error restaurando {nombre} (ID {registro_dict.get('id', '?')}): {str(e)}")

            restaurados[nombre] = count

        session.commit()

    return {
        "mensaje": "Restauración completada",
        "restaurados": restaurados,
        "total_registros": sum(restaurados.values()),
        "config_restaurada": config_restaurada,
        "errores": errores,
        "backup_origen": backup_data.get("metadatos", {}),
    }


@router.get("/backup/descargar")
def descargar_backup():
    """Genera y devuelve el backup como un archivo JSON descargable."""
    from fastapi.responses import FileResponse
    import tempfile

    backup = generar_backup()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"cmms_bioai_backup_{timestamp}.json"
    temp_dir = Path(tempfile.gettempdir())
    temp_path = temp_dir / filename

    with open(temp_path, "w", encoding="utf-8") as f:
        json.dump(backup, f, indent=2, ensure_ascii=False)

    return FileResponse(
        path=str(temp_path),
        media_type="application/json",
        filename=filename,
    )


@router.post("/restore/subir")
def subir_backup(archivo: UploadFile = File(...)):
    """Sube un archivo JSON de backup y restaura la base de datos."""
    if not archivo.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un .json")

    try:
        contenido = archivo.file.read()
        backup_data = json.loads(contenido.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo JSON: {str(e)}")

    return restaurar_backup(backup_data)
