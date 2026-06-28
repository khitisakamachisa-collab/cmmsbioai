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

    Incluye:
    - Entidades (equipos, repuestos, herramientas) desde .meta.json en su carpeta raíz
    - Órdenes de Trabajo desde el archivo .txt de referencia en uploads/OT/
    - Documentos desde .meta.json en subcarpetas DOC/ y OT/OTxxxx/ de cada entidad
    - Detecta imágenes faltantes: si el .meta.json tiene imagen_ruta pero el
      registro en BD tiene imagen_ruta=None, se reporta como "imagen_faltante"
    """
    resultados = {
        "equipos": {"en_archivos": [], "en_bd": 0, "huerfanos": [], "imagenes_faltantes": []},
        "repuestos": {"en_archivos": [], "en_bd": 0, "huerfanos": [], "imagenes_faltantes": []},
        "herramientas": {"en_archivos": [], "en_bd": 0, "huerfanos": [], "imagenes_faltantes": []},
        "ordenes": {"en_archivos": [], "en_bd": 0, "huerfanos": []},
        "documentos": {"en_archivos": [], "en_bd": 0, "huerfanos": []},
    }

    with Session(engine) as session:
        ids_equipos_bd = {e.id: e for e in session.exec(select(Equipo)).all()}
        ids_repuestos_bd = {r.id: r for r in session.exec(select(Repuesto)).all()}
        ids_herramientas_bd = {h.id: h for h in session.exec(select(Herramienta)).all()}
        ids_ots_bd = {o.id: o for o in session.exec(select(OrdenTrabajo)).all()}
        ids_docs_bd = set(d.id for d in session.exec(select(DocumentoAdjunto)).all())

        resultados["equipos"]["en_bd"] = len(ids_equipos_bd)
        resultados["repuestos"]["en_bd"] = len(ids_repuestos_bd)
        resultados["herramientas"]["en_bd"] = len(ids_herramientas_bd)
        resultados["ordenes"]["en_bd"] = len(ids_ots_bd)
        resultados["documentos"]["en_bd"] = len(ids_docs_bd)

    uploads_base = UPLOADS_DIR

    carpetas_entidad = {
        "EQUIPOS": ("equipos", ids_equipos_bd),
        "REPUESTOS": ("repuestos", ids_repuestos_bd),
        "HERRAMIENTAS": ("herramientas", ids_herramientas_bd),
    }

    # ─── Paso 1: Escanear entidades (equipos, repuestos, herramientas) ───
    for carpeta_nombre, (tipo, bd_dict) in carpetas_entidad.items():
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
                "tipo_meta": meta.get("entidad_tipo", tipo),
                "tiene_imagen_meta": bool(meta.get("imagen_ruta")),
            }

            resultados[tipo]["en_archivos"].append(info)

            if entidad_id not in bd_dict:
                resultados[tipo]["huerfanos"].append(info)
            else:
                # El registro existe en BD — verificar si le falta imagen_ruta
                registro_bd = bd_dict[entidad_id]
                imagen_meta = meta.get("imagen_ruta")
                if imagen_meta and not registro_bd.imagen_ruta:
                    resultados[tipo]["imagenes_faltantes"].append({
                        "id": entidad_id,
                        "carpeta": str(subdir.relative_to(uploads_base)),
                        "nombre": info["nombre"],
                        "imagen_ruta_meta": imagen_meta,
                        "imagen_ruta_bd": registro_bd.imagen_ruta,
                    })

            # ─── Escanear documentos en subcarpeta DOC/ ───
            doc_dir = subdir / "DOC"
            if doc_dir.exists():
                _escanear_documentos_carpeta(doc_dir, tipo, entidad_id, ids_docs_bd, resultados, uploads_base)

            # ─── Escanear documentos en subcarpetas OT/OTxxxx/ (solo para equipos) ───
            if tipo == "equipos":
                ot_root = subdir / "OT"
                if ot_root.exists():
                    for ot_subdir in sorted(ot_root.iterdir()):
                        if not ot_subdir.is_dir() or not ot_subdir.name.startswith("OT"):
                            continue
                        # Las carpetas OT/OTxxxx/ contienen .meta.json con documentos
                        _escanear_documentos_carpeta(ot_subdir, "ordentrabajo", None, ids_docs_bd, resultados, uploads_base, parse_ot_id_from_name=True, ot_folder_name=ot_subdir.name)

    # ─── Paso 2: Escanear Órdenes de Trabajo desde archivos .txt en uploads/OT/ ───
    ot_root = uploads_base / "OT"
    if ot_root.exists():
        for txt_file in sorted(ot_root.iterdir()):
            if not txt_file.is_file() or not txt_file.name.endswith(".txt"):
                continue
            ot_info = _parse_ot_txt_referencia(txt_file)
            if ot_info is None:
                continue
            ot_id = ot_info.get("id")
            if ot_id is None:
                continue

            info = {
                "id": ot_id,
                "carpeta": str(txt_file.relative_to(uploads_base)),
                "titulo": ot_info.get("titulo", "N/A"),
                "equipo_id": ot_info.get("equipo_id"),
                "equipo_codigo": ot_info.get("equipo_codigo"),
                "equipo_nombre": ot_info.get("equipo_nombre"),
                "prioridad": ot_info.get("prioridad"),
            }
            resultados["ordenes"]["en_archivos"].append(info)
            if ot_id not in ids_ots_bd:
                resultados["ordenes"]["huerfanos"].append(info)

    # ─── Resumen ───
    resumen = {
        "total_en_archivos": sum(len(v["en_archivos"]) for k, v in resultados.items() if k != "documentos"),
        "total_en_bd": sum(v["en_bd"] for k, v in resultados.items() if k != "documentos"),
        "total_huerfanos": sum(len(v["huerfanos"]) for v in resultados.values()),
        "total_imagenes_faltantes": sum(len(v.get("imagenes_faltantes", [])) for v in resultados.values()),
        "total_docs_en_archivos": len(resultados["documentos"]["en_archivos"]),
        "total_docs_huerfanos": len(resultados["documentos"]["huerfanos"]),
    }

    return {"resumen": resumen, "detalle": resultados}


def _escanear_documentos_carpeta(doc_dir, padre_tipo, padre_id, ids_docs_bd,
                                  resultados, uploads_base,
                                  parse_ot_id_from_name=False, ot_folder_name=None):
    """
    Lee el .meta.json de una carpeta de documentos y agrega las entradas al resultado.
    Si parse_ot_id_from_name=True, intenta extraer el OT ID desde el nombre de la carpeta.
    """
    doc_meta_path = doc_dir / ".meta.json"
    if not doc_meta_path.exists():
        return

    try:
        with open(doc_meta_path, "r", encoding="utf-8") as f:
            doc_meta = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    for doc_entry in doc_meta.get("documentos", []):
        doc_id = doc_entry.get("documento_id")
        if doc_id is None:
            continue

        # Determinar el padre_type y padre_id reales desde el doc_entry
        # (más confiable que el parámetro padre_tipo, porque los docs de OT
        # tienen entidad_tipo="ot" en su .meta.json)
        ent_tipo = doc_entry.get("entidad_tipo") or padre_tipo
        ent_id = doc_entry.get("entidad_id") or padre_id

        doc_info = {
            "id": doc_id,
            "nombre_archivo": doc_entry.get("nombre_archivo"),
            "entidad_tipo": ent_tipo,
            "entidad_id": ent_id,
            "carpeta": str(doc_dir.relative_to(uploads_base)),
        }
        resultados["documentos"]["en_archivos"].append(doc_info)
        if doc_id not in ids_docs_bd:
            resultados["documentos"]["huerfanos"].append(doc_info)


def _parse_ot_txt_referencia(txt_path: Path) -> Optional[dict]:
    """
    Lee un archivo .txt de referencia de OT (en uploads/OT/) y extrae los datos.

    Formato esperado (líneas clave):
        OT ID: 1
        OT Codigo: OT0001
        Titulo/Tipo: Correctivo
        Prioridad: Alta
        Equipo ID: 1
        Equipo Codigo: E0001
        Nombre corto: Microscopio Olympus CX23
        Modelo: CX23
    """
    try:
        with open(txt_path, "r", encoding="utf-8") as f:
            contenido = f.read()
    except (IOError, UnicodeDecodeError):
        return None

    datos = {}
    for linea in contenido.splitlines():
        if ":" not in linea:
            continue
        clave, _, valor = linea.partition(":")
        clave = clave.strip()
        valor = valor.strip()
        if not clave or not valor:
            continue

        if clave == "OT ID":
            try:
                datos["id"] = int(valor)
            except ValueError:
                pass
        elif clave == "OT Codigo":
            datos["codigo"] = valor
        elif clave == "Titulo/Tipo":
            datos["titulo"] = valor
        elif clave == "Prioridad":
            datos["prioridad"] = valor
        elif clave == "Descripcion falla":
            datos["descripcion_falla"] = valor
        elif clave == "Equipo ID":
            try:
                datos["equipo_id"] = int(valor)
            except ValueError:
                pass
        elif clave == "Equipo Codigo":
            datos["equipo_codigo"] = valor
        elif clave == "Nombre corto":
            datos["equipo_nombre"] = valor
        elif clave == "Modelo":
            datos["equipo_modelo"] = valor
        elif clave == "Marca":
            datos["equipo_marca"] = valor
        elif clave == "Numero de serie":
            datos["equipo_numero_serie"] = valor

    if "id" not in datos:
        return None
    return datos


@router.post("/recuperar")
def recuperar_desde_meta_json():
    """
    Recupera registros huérfanos desde los archivos .meta.json y .txt de referencia.

    Operaciones que realiza:
    1. Crear registros de equipos/repuestos/herramientas que existen en archivos
       pero no en BD (huérfanos).
    2. Sincronizar imagen_ruta: si el registro existe en BD pero SIN imagen_ruta,
       y el .meta.json lo tiene, actualizar el registro.
    3. Crear registros de Órdenes de Trabajo desde los .txt de referencia en uploads/OT/.
    4. Crear registros de DocumentoAdjunto huérfanos desde los .meta.json en
       carpetas DOC/ y OT/OTxxxx/ de cada entidad.
    """
    recuperados = {
        "equipos": 0,
        "repuestos": 0,
        "herramientas": 0,
        "ordenes": 0,
        "documentos": 0,
        "imagenes_sincronizadas": 0,
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
        # ─── Paso 1: Recuperar entidades + sincronizar imagen_ruta ───
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
                    # ─── Sincronizar imagen_ruta si falta en BD pero está en .meta.json ───
                    imagen_meta = meta.get("imagen_ruta")
                    if imagen_meta and not existente.imagen_ruta:
                        try:
                            existente.imagen_ruta = imagen_meta
                            session.add(existente)
                            recuperados["imagenes_sincronizadas"] += 1
                        except Exception as e:
                            errores.append(f"Error sincronizando imagen de {tipo} ID {entidad_id}: {str(e)}")
                    continue  # No crear nuevo registro

                # ─── Crear registro nuevo (huérfano) ───
                try:
                    if tipo == "equipos":
                        # v0.9.0: usar nuevos campos, ignorar campos obsoletos
                        # Si el .meta.json tiene proveedor_principal (texto viejo),
                        # intentar resolver a proveedor_principal_id buscando por nombre
                        prov_id = meta.get("proveedor_principal_id")
                        if not prov_id and meta.get("proveedor_principal"):
                            prov_nombre = meta.get("proveedor_principal")
                            prov_obj = session.exec(
                                select(Proveedor).where(Proveedor.nombre_empresa == prov_nombre)
                            ).first()
                            if prov_obj:
                                prov_id = prov_obj.id
                            else:
                                # Crear proveedor al vuelo (igual que en import-excel)
                                nuevo_prov = Proveedor(nombre_empresa=prov_nombre)
                                session.add(nuevo_prov)
                                session.flush()
                                prov_id = nuevo_prov.id

                        registro = Equipo(
                            id=entidad_id,
                            nombre_corto=meta.get("nombre_corto") or "Equipo recuperado",
                            modelo=meta.get("modelo", "Sin modelo"),
                            numero_serie=meta.get("numero_serie", f"REC-{entidad_id}"),
                            numero_material=meta.get("numero_material"),
                            marca=meta.get("marca", "Sin marca"),
                            ubicacion_actual=meta.get("ubicacion_actual"),
                            estado_id=meta.get("estado_id", 1),
                            proveedor_principal_id=prov_id,
                            condicion_origen=meta.get("condicion_origen"),
                            fecha_inicio_garantia=meta.get("fecha_inicio_garantia"),
                            fecha_fin_garantia=meta.get("fecha_fin_garantia"),
                            observaciones=meta.get("observaciones"),
                            descripcion=meta.get("descripcion"),
                            imagen_ruta=meta.get("imagen_ruta"),
                            fecha_adquisicion=meta.get("fecha_adquisicion"),
                            # CAMPOS ELIMINADOS en v0.9.0 (no se setean):
                            # - registro_sanitario_bolivia
                            # - calibracion_proxima
                            # - responsable_tecnico_id
                            # - proveedor_principal (texto, reemplazado por proveedor_principal_id)
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

        # ─── Paso 2: Recuperar Órdenes de Trabajo desde .txt en uploads/OT/ ───
        ot_root = uploads_base / "OT"
        if ot_root.exists():
            for txt_file in sorted(ot_root.iterdir()):
                if not txt_file.is_file() or not txt_file.name.endswith(".txt"):
                    continue
                ot_info = _parse_ot_txt_referencia(txt_file)
                if ot_info is None:
                    continue
                ot_id = ot_info.get("id")
                if ot_id is None:
                    continue

                existente = session.exec(
                    select(OrdenTrabajo).where(OrdenTrabajo.id == ot_id)
                ).first()
                if existente:
                    continue

                equipo_id = ot_info.get("equipo_id")
                if equipo_id is None:
                    errores.append(f"OT ID {ot_id}: no se pudo determinar equipo_id desde {txt_file.name}")
                    continue

                # Verificar que el equipo existe (recién recuperado o preexistente)
                equipo = session.get(Equipo, equipo_id)
                if not equipo:
                    errores.append(f"OT ID {ot_id}: equipo_id {equipo_id} no existe en BD, no se puede recuperar la OT")
                    continue

                try:
                    # Buscar estado por defecto (Abierta = id 1)
                    estado_ot = session.get(EstadoOT, 1)
                    estado_id = estado_ot.id if estado_ot else 1

                    nueva_ot = OrdenTrabajo(
                        id=ot_id,
                        equipo_id=equipo_id,
                        estado_id=estado_id,
                        prioridad=ot_info.get("prioridad", "Media"),
                        titulo=ot_info.get("titulo", "OT recuperada"),
                        descripcion_falla=ot_info.get("descripcion_falla", "OT recuperada desde archivo .txt de referencia"),
                        fecha_creacion=datetime.now(),
                    )
                    session.add(nueva_ot)
                    recuperados["ordenes"] += 1
                except Exception as e:
                    errores.append(f"Error recuperando OT ID {ot_id}: {str(e)}")

        # ─── Paso 3: Recuperar documentos desde DOC/ y OT/OTxxxx/ ───
        for carpeta_nombre, (tipo, modelo) in carpetas_entidad.items():
            carpeta = uploads_base / carpeta_nombre
            if not carpeta.exists():
                continue

            for subdir in sorted(carpeta.iterdir()):
                if not subdir.is_dir():
                    continue

                # Documentos en DOC/
                doc_dir = subdir / "DOC"
                if doc_dir.exists():
                    _recuperar_documentos_carpeta(doc_dir, session, ids_recuperados, recuperados, errores, uploads_base)

                # Documentos en OT/OTxxxx/ (solo equipos)
                if tipo == "equipos":
                    ot_root_eq = subdir / "OT"
                    if ot_root_eq.exists():
                        for ot_subdir in sorted(ot_root_eq.iterdir()):
                            if not ot_subdir.is_dir() or not ot_subdir.name.startswith("OT"):
                                continue
                            _recuperar_documentos_carpeta(ot_subdir, session, ids_recuperados, recuperados, errores, uploads_base, allow_ot_docs=True)

        session.commit()

    return {
        "mensaje": "Recuperación completada",
        "recuperados": recuperados,
        "total_recuperados": sum(recuperados.values()),
        "errores": errores,
    }


def _recuperar_documentos_carpeta(doc_dir, session, ids_recuperados, recuperados,
                                    errores, uploads_base, allow_ot_docs=False):
    """
    Recupera documentos huérfanos desde un .meta.json dentro de una carpeta DOC/ u OT/OTxxxx/.
    Si allow_ot_docs=True, acepta documentos con entidad_tipo="ot" y los asocia a la OT.
    """
    doc_meta_path = doc_dir / ".meta.json"
    if not doc_meta_path.exists():
        return

    try:
        with open(doc_meta_path, "r", encoding="utf-8") as f:
            doc_meta = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    for doc_entry in doc_meta.get("documentos", []):
        doc_id = doc_entry.get("documento_id")
        if doc_id is None:
            continue

        existente = session.exec(
            select(DocumentoAdjunto).where(DocumentoAdjunto.id == doc_id)
        ).first()
        if existente:
            continue

        padre_tipo = doc_entry.get("entidad_tipo")
        padre_id = doc_entry.get("entidad_id")

        # Normalizar "ot" → "ordentrabajo"
        if padre_tipo == "ot":
            padre_tipo = "ordentrabajo"

        # Validar que el padre exista
        if padre_tipo and padre_id:
            modelo_padre = {
                "equipos": Equipo,
                "repuestos": Repuesto,
                "herramientas": Herramienta,
                "ordentrabajo": OrdenTrabajo,
            }.get(padre_tipo)

            if modelo_padre:
                padre = session.exec(
                    select(modelo_padre).where(modelo_padre.id == padre_id)
                ).first()
                if not padre:
                    # Si es OT y no se permite recuperar docs de OT aquí, saltar
                    if padre_tipo == "ordentrabajo" and not allow_ot_docs:
                        continue
                    errores.append(f"Documento ID {doc_id}: padre {padre_tipo} ID {padre_id} no existe")
                    continue
            elif padre_tipo not in ("equipos", "repuestos", "herramientas", "ordentrabajo"):
                # Tipo desconocido, intentar inferir desde la ruta
                ruta_lower = str(doc_dir).lower().replace("\\", "/")
                if "/ot/" in ruta_lower or "/ot" in ruta_lower:
                    padre_tipo = "ordentrabajo"
                elif "equipos" in ruta_lower:
                    padre_tipo = "equipos"
                elif "repuestos" in ruta_lower:
                    padre_tipo = "repuestos"
                elif "herramientas" in ruta_lower:
                    padre_tipo = "herramientas"

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
                orden_trabajo_id=padre_id if padre_tipo == "ordentrabajo" else None,
                equipo_id=padre_id if padre_tipo == "equipos" else None,
                repuesto_id=padre_id if padre_tipo == "repuestos" else None,
                herramienta_id=padre_id if padre_tipo == "herramientas" else None,
            )
            session.add(doc_registro)
            recuperados["documentos"] += 1
        except Exception as e:
            errores.append(f"Error recuperando documento ID {doc_id}: {str(e)}")


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


# ──────────────────────────────────────────────────────────
# MODO TEST: Cargar datos de ejemplo y Limpiar BD
# ──────────────────────────────────────────────────────────

@router.post("/cargar-test")
def cargar_datos_test():
    """
    Carga datos de ejemplo (modo TEST) en la base de datos.

    Crea:
    - 3 usuarios TEST (admin/tech/user) - si no existen
    - 5 proveedores con contactos
    - 8 equipos con todos los estados posibles
    - 5 repuestos con stock
    - 5 herramientas con categorías
    - 5 OTs (correctivas y preventivas)
    - 5 tareas preventivas
    - Eventos de historial

    Útil para:
    - Probar el sistema sin tener que crear datos a mano
    - Capacitar a usuarios finales
    - Reproducir escenarios complejos

    NO borra datos existentes. Si ya hay datos, los nuevos se agregan.
    Para empezar limpio: usar /limpiar-bd primero.
    """
    from database import engine
    from models.users import Usuario
    from models.proveedores import Proveedor, ContactoProveedor
    from models.repuestos import Repuesto
    from models.herramientas import Herramienta
    from models.ordenes import OrdenTrabajo, EstadoOT
    from models.preventivo import TareaPreventiva
    from models.historial import EventoHistorial
    from models.estados import EstadoEquipo
    import bcrypt

    resumen = {
        "usuarios": 0,
        "proveedores": 0,
        "contactos": 0,
        "equipos": 0,
        "repuestos": 0,
        "herramientas": 0,
        "ots": 0,
        "mps": 0,
        "historial": 0,
    }

    with Session(engine) as session:
        # === 1. Usuarios TEST (si no existen) ===
        usuarios_test = [
            ("admin", "admin", "admin",   "Administrador del Sistema", "admin@biolab.com"),
            ("tech",  "tech",  "tecnico", "Técnico Biomédico",         "tech@biolab.com"),
            ("user",  "user",  "tecnico", "Usuario Regular",           "user@biolab.com"),
        ]
        for username, password, role, full_name, email in usuarios_test:
            existe = session.exec(select(Usuario).where(Usuario.username == username)).first()
            if not existe:
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                session.add(Usuario(
                    username=username, email=email, hashed_password=hashed,
                    full_name=full_name, role=role, is_active=True
                ))
                resumen["usuarios"] += 1

        # Obtener IDs de usuarios para referencias
        admin_user = session.exec(select(Usuario).where(Usuario.username == "admin")).first()
        tech_user = session.exec(select(Usuario).where(Usuario.username == "tech")).first()
        tech_id = tech_user.id if tech_user else 1

        # === 2. Proveedores ===
        proveedores_test = [
            ("TechMed Bolivia SRL", "Cochabamba", "Av. Blanco Galindo km 7.5", "+591 4 4223344", "ventas@techmed.bo", "https://techmed.bo"),
            ("BioSupply Andina", "La Paz", "Calle Mercado N° 1234", "+591 2 2445566", "info@biosupply.bo", "https://biosupply.bo"),
            ("MedEquip Bolivia SA", "Santa Cruz", "Tercer Anillo Interno", "+591 3 3467788", "ventas@medequip.bo", ""),
            ("LabTech SRL", "Cochabamba", "Av. América Esq. Esteban Arze", "+591 4 4521199", "contacto@labtech.bo", "https://labtech.bo"),
            ("Hospimed Bolivia", "La Paz", "Av. 6 de Agosto N° 2115", "+591 2 2150500", "ventas@hospimed.bo", "https://hospimed.bo"),
        ]
        proveedores_ids = {}
        for nombre, ciudad, dir_, tel, email, web in proveedores_test:
            existe = session.exec(select(Proveedor).where(Proveedor.nombre_empresa == nombre)).first()
            if existe:
                proveedores_ids[nombre] = existe.id
                continue
            prov = Proveedor(
                nombre_empresa=nombre, ciudad=ciudad, direccion=dir_,
                telefono_principal=tel, email_principal=email, pagina_web=web,
                notas_generales=f"Proveedor de prueba para modo TEST"
            )
            session.add(prov)
            session.flush()
            proveedores_ids[nombre] = prov.id
            resumen["proveedores"] += 1

        # === 3. Contactos de proveedores ===
        contactos_test = [
            ("TechMed Bolivia SRL", "Carlos Mendoza", "Gerente de Ventas", "+591 70122334", "carlos.mendoza@techmed.bo"),
            ("TechMed Bolivia SRL", "Patricia Rocha", "Jefa de Soporte Técnico", "+591 70255667", "soporte@techmed.bo"),
            ("BioSupply Andina", "Roberto Suarez", "Vendedor Senior", "+591 71234567", "rsuarez@biosupply.bo"),
            ("LabTech SRL", "Jimena Calderón", "Ejecutiva de Ventas", "+591 73322110", "jimena@labtech.bo"),
        ]
        for prov_nombre, contacto_nombre, cargo, tel, email in contactos_test:
            prov_id = proveedores_ids.get(prov_nombre)
            if not prov_id:
                continue
            existe = session.exec(
                select(ContactoProveedor).where(
                    ContactoProveedor.proveedor_id == prov_id,
                    ContactoProveedor.nombre_contacto == contacto_nombre
                )
            ).first()
            if existe:
                continue
            session.add(ContactoProveedor(
                proveedor_id=prov_id, nombre_contacto=contacto_nombre,
                cargo=cargo, telefono_contacto=tel, email_contacto=email
            ))
            resumen["contactos"] += 1

        # === 4. Equipos (8 con estados variados) ===
        equipos_test = [
            # (nombre_corto, modelo, serie, marca, ubicacion, estado_id, proveedor, condicion, fecha_adq, fecha_inicio_gar, fecha_fin_gar, desc, obs)
            ("Microscopio Olympus CX23", "CX23", "MIC-OLY-001", "Olympus", "Lab. Microbiología", 1, "TechMed Bolivia SRL", "Compra",
             date(2025, 3, 15), date(2025, 3, 15), date(2027, 3, 15),
             "Microscopio binocular para microbiología clínica", "Funciona correctamente"),
            ("Centrífuga Eppendorf 5424", "5424", "CEN-EPP-002", "Eppendorf", "Lab. Hematología", 2, "BioSupply Andina", "Compra",
             date(2025, 7, 20), date(2025, 7, 20), date(2027, 7, 20),
             "Centrífuga de mesa 24 tubos", "En mantenimiento preventivo"),
            ("Autoclave Steris Amsco 3043", "3043", "AUT-STR-003", "Steris", "Central de Esterilización", 1, "MedEquip Bolivia SA", "Compra",
             date(2021, 1, 10), date(2021, 1, 10), date(2023, 1, 10),
             "Autoclave hospitalaria vertical, 400L", "Garantía vencida"),
            ("Monitor Signos Vitales Mindray", "uMEC10", "MON-MIN-005", "Mindray", "UCI Box 3", 7, "Hospimed Bolivia", "Donación",
             date(2025, 11, 5), date(2025, 11, 5), date(2027, 11, 5),
             "Monitor multiparámetro con SpO2, ECG, NIBP", "Esperando repuesto: sensor SpO2"),
            ("Electrocardiógrafo GE MAC 2000", "MAC 2000", "ELE-GEE-006", "GE Healthcare", "Cardiología", 1, "TechMed Bolivia SRL", "Compra",
             date(2020, 9, 15), date(2020, 9, 15), date(2022, 9, 15),
             "ECG 12 derivaciones con interpretación", "Garantía vencida, funciona OK"),
            ("Desfibrilador Zoll R Series", "R Series", "DES-ZOL-009", "Zoll", "Emergencias", 4, "Hospimed Bolivia", "Compra",
             date(2025, 4, 18), date(2025, 4, 18), date(2027, 4, 18),
             "Desfibrilador biphasic con monitor y marcapasos", "Fuera de servicio por falla eléctrica"),
            ("Bomba de Infusión B. Braun", "Infusomat Space", "BOM-BRA-011", "B. Braun", "UCI Box 1", 6, "MedEquip Bolivia SA", "Leasing",
             date(2025, 12, 10), date(2025, 12, 10), date(2027, 12, 10),
             "Bomba de infusión volumétrica con modo PCA", "En inspección"),
            ("Balanza Analítica Sartorius", "Quintix 224", "BAL-SAR-008", "Sartorius", "Lab. Control Calidad", 1, "LabTech SRL", "Compra",
             date(2021, 8, 12), date(2021, 8, 12), date(2023, 8, 12),
             "Balanza analítica 220g / 0.1mg", "Calibración interna, funciona OK"),
        ]
        equipos_ids = {}
        for eq_data in equipos_test:
            (nombre, modelo, serie, marca, ubic, est_id, prov_nombre, cond,
             f_adq, f_ing, f_fin, desc, obs) = eq_data
            existe = session.exec(select(Equipo).where(Equipo.numero_serie == serie)).first()
            if existe:
                equipos_ids[serie] = existe.id
                continue
            prov_id = proveedores_ids.get(prov_nombre)
            nuevo_eq = Equipo(
                nombre_corto=nombre, modelo=modelo, numero_serie=serie, marca=marca,
                fecha_adquisicion=f_adq, fecha_inicio_garantia=f_ing, fecha_fin_garantia=f_fin,
                ubicacion_actual=ubic, estado_id=est_id, proveedor_principal_id=prov_id,
                condicion_origen=cond, descripcion=desc, observaciones=obs
            )
            session.add(nuevo_eq)
            session.flush()
            equipos_ids[serie] = nuevo_eq.id
            resumen["equipos"] += 1

        # === 5. Repuestos ===
        repuestos_test = [
            ("Filtro HEPA para cabina de flujo", "FLT-HEP-001", 3, "unidad", "Almacén B - Estante 1", 2, "BioSupply Andina"),
            ("Lámpara UV para autoclave", "LMP-UV-002", 5, "unidad", "Almacén B - Estante 1", 2, "MedEquip Bolivia SA"),
            ("Cable ECG 12 derivaciones", "CBL-ECG-007", 3, "unidad", "Almacén C - Gabinete 1", 2, "TechMed Bolivia SRL"),
            ("Sensor SpO2 dedo adulto", "SNR-SPO-008", 4, "unidad", "UCI - Armario", 2, "Hospimed Bolivia"),
            ("Batería interna desfibrilador", "BAT-DEF-010", 2, "unidad", "Emergencias - Armario", 1, "Hospimed Bolivia"),
        ]
        for nombre, codigo, cant, unidad, ubic, stock_min, prov_nombre in repuestos_test:
            existe = session.exec(select(Repuesto).where(Repuesto.numero_material == codigo)).first()
            if existe:
                continue
            prov_id = proveedores_ids.get(prov_nombre)
            session.add(Repuesto(
                nombre_repuesto=nombre, numero_material=codigo,
                cantidad_disponible=cant, unidad_medida=unidad,
                ubicacion_almacen=ubic, nivel_stock_minimo=stock_min,
                proveedor_ultimo=prov_nombre
            ))
            resumen["repuestos"] += 1

        # === 6. Herramientas ===
        herramientas_test = [
            ("Osciloscopio digital Rigol DS1054Z", "OSC-001", "Instrumento de Medición", 1, "Taller - Estante A1", "Disponible"),
            ("Multímetro Fluke 87V", "MUL-002", "Instrumento de Medición", 2, "Taller - Estante A1", "Disponible"),
            ("Analizador de seguridad eléctrica Fluke ESA620", "ANA-003", "Instrumento de Medición", 1, "Taller - Estante A2", "En Uso"),
            ("Juego de destornilladores aislados Wiha", "DES-004", "Herramienta Manual", 3, "Taller - Cajón B1", "Disponible"),
            ("Alcohol isopropílico 99%", "ALC-006", "Consumible", 5, "Taller - Estante C2", "Disponible"),
        ]
        for nombre, codigo, cat, cant, ubic, estado_uso in herramientas_test:
            existe = session.exec(select(Herramienta).where(Herramienta.numero_identificacion == codigo)).first()
            if existe:
                continue
            session.add(Herramienta(
                nombre_herramienta=nombre, numero_identificacion=codigo,
                categoria=cat, cantidad_disponible=cant, unidad_medida="unidad",
                ubicacion_almacen=ubic, estado_uso=estado_uso
            ))
            resumen["herramientas"] += 1

        # === 7. Órdenes de Trabajo ===
        # Solo crear OTs si hay equipos
        if equipos_ids:
            estado_ot_abierta = session.get(EstadoOT, 1)  # Abierta
            estado_ot_proceso = session.get(EstadoOT, 2)  # En Proceso
            estado_ot_completada = session.get(EstadoOT, 4)  # Completada

            ots_test = [
                # (titulo, equipo_serie, estado_id, prioridad, descripcion, tecnico_id)
                ("Correctivo", "MIC-OLY-001", 1, "Media", "Microscopio no enfoca correctamente en objetivo 40x", tech_id),
                ("Mantenimiento Preventivo", "CEN-EPP-002", 2, "Baja", "Mantenimiento preventivo trimestral", tech_id),
                ("Correctivo", "MON-MIN-005", 3, "Alta", "Sensor SpO2 no responde, requiere repuesto", tech_id),
                ("Calibración", "BAL-SAR-008", 4, "Media", "Calibración anual de balanza analítica", tech_id),
                ("Inspección", "DES-ZOL-009", 1, "Urgente", "Desfibrilador no enciende, revisar fuente de poder", tech_id),
            ]
            for titulo, serie, est_id, prioridad, desc, tec_id in ots_test:
                eq_id = equipos_ids.get(serie)
                if not eq_id:
                    continue
                session.add(OrdenTrabajo(
                    equipo_id=eq_id, estado_id=est_id, prioridad=prioridad,
                    tecnico_asignado_id=tec_id, titulo=titulo, descripcion_falla=desc,
                    fecha_creacion=datetime.now()
                ))
                resumen["ots"] += 1

        # === 8. Tareas Preventivas ===
        if equipos_ids:
            mps_test = [
                # (titulo, equipo_serie, frecuencia, proxima_fecha, descripcion)
                ("Mantenimiento Preventivo Trimestral", "MIC-OLY-001", 90, date.today(), "Limpieza de lentes, revisión mecánica"),
                ("Calibración Anual", "BAL-SAR-008", 365, date.today(), "Calibración con pesas patrón"),
                ("Mantenimiento Preventivo Semestral", "CEN-EPP-002", 180, date.today(), "Lubricación de rotor, limpieza"),
                ("Inspección de Seguridad Eléctrica", "MON-MIN-005", 365, date.today(), "Prueba de seguridad según IEC 62353"),
                ("Mantenimiento Preventivo Anual", "AUT-STR-003", 365, date.today(), "Limpieza profunda, cambio de filtros"),
            ]
            for titulo, serie, freq, prox_fecha, desc in mps_test:
                eq_id = equipos_ids.get(serie)
                if not eq_id:
                    continue
                existe = session.exec(
                    select(TareaPreventiva).where(
                        TareaPreventiva.equipo_id == eq_id,
                        TareaPreventiva.titulo == titulo
                    )
                ).first()
                if existe:
                    continue
                session.add(TareaPreventiva(
                    equipo_id=eq_id, titulo=titulo, descripcion=desc,
                    frecuencia_dias=freq, proxima_fecha=prox_fecha,
                    responsable_id=tech_id, activa=True
                ))
                resumen["mps"] += 1

        # === 9. Historial (algunos eventos) ===
        if equipos_ids:
            eq1 = equipos_ids.get("MIC-OLY-001")
            eq3 = equipos_ids.get("AUT-STR-003")
            eq6 = equipos_ids.get("BAL-SAR-008")
            historial_test = [
                (eq1, "correctivo", "Cambio de lámpara halógena", tech_id),
                (eq3, "preventivo", "Limpieza de filtros y válvulas", tech_id),
                (eq6, "calibracion", "Calibración con pesas patrón certificadas", tech_id),
            ]
            for eq_id, tipo, desc, tec_id in historial_test:
                if not eq_id:
                    continue
                session.add(EventoHistorial(
                    equipo_id=eq_id, tipo_evento=tipo, descripcion=desc,
                    tecnico_id=tec_id, fecha_evento=datetime.now(),
                    acciones_realizadas=desc
                ))
                resumen["historial"] += 1

        session.commit()

    return {
        "mensaje": "Datos TEST cargados correctamente",
        "resumen": resumen,
        "total_creados": sum(resumen.values()),
        "nota": (
            "Los datos TEST se agregaron a los existentes. "
            "Si querías empezar limpio, ejecuta /configuracion/limpiar-bd primero."
        )
    }


@router.post("/limpiar-bd")
def limpiar_base_de_datos():
    """
    Limpia TODA la base de datos excepto:
    - Usuarios admin/tech/user (los 3 usuarios TEST)
    - Estados de equipo (catálogo de 19 estados)
    - Estados de OT (catálogo de 5 estados)
    - Configuración del sistema (config.json)

    Borra:
    - Equipos, Repuestos, Herramientas, Proveedores, Contactos
    - Órdenes de Trabajo, Tareas Preventivas, Eventos de Historial
    - Documentos Adjuntos
    - Carpetas físicas en uploads/ (excepto la carpeta en sí)

    Útil para:
    - Empezar limpio antes de cargar datos TEST
    - Eliminar datos de prueba antes de usar el sistema en producción
    """
    from database import engine
    from models.users import Usuario
    from models.proveedores import Proveedor, ContactoProveedor
    from models.repuestos import Repuesto, OtRepuestoUtilizado
    from models.herramientas import Herramienta
    from models.ordenes import OrdenTrabajo
    from models.preventivo import TareaPreventiva, TareaRepuesto
    from models.historial import EventoHistorial
    from models.documentos import DocumentoAdjunto
    import shutil

    resumen = {}

    with Session(engine) as session:
        # Contar antes de borrar
        resumen["documentos_eliminados"] = len(session.exec(select(DocumentoAdjunto)).all())
        resumen["historial_eliminado"] = len(session.exec(select(EventoHistorial)).all())
        resumen["tarea_repuesto_eliminado"] = len(session.exec(select(TareaRepuesto)).all())
        resumen["ot_repuesto_utilizado_eliminado"] = len(session.exec(select(OtRepuestoUtilizado)).all())
        resumen["mps_eliminadas"] = len(session.exec(select(TareaPreventiva)).all())
        resumen["ots_eliminadas"] = len(session.exec(select(OrdenTrabajo)).all())
        resumen["herramientas_eliminadas"] = len(session.exec(select(Herramienta)).all())
        resumen["repuestos_eliminados"] = len(session.exec(select(Repuesto)).all())
        resumen["contactos_eliminados"] = len(session.exec(select(ContactoProveedor)).all())
        resumen["proveedores_eliminados"] = len(session.exec(select(Proveedor)).all())
        resumen["equipos_eliminados"] = len(session.exec(select(Equipo)).all())

        # Borrar en orden (respetando FKs)
        # 1. Documentos (pueden referenciar OT, Equipo, Repuesto, Herramienta)
        for d in session.exec(select(DocumentoAdjunto)).all():
            session.delete(d)
        # 2. Historial (referencia Equipo, OT, Usuario)
        for h in session.exec(select(EventoHistorial)).all():
            session.delete(h)
        # 3. TareaRepuesto (referencia TareaPreventiva, Repuesto)
        for tr in session.exec(select(TareaRepuesto)).all():
            session.delete(tr)
        # 4. OtRepuestoUtilizado (referencia OT, Repuesto)
        for oru in session.exec(select(OtRepuestoUtilizado)).all():
            session.delete(oru)
        # 5. Tareas Preventivas (referencia Equipo, Usuario)
        for mp in session.exec(select(TareaPreventiva)).all():
            session.delete(mp)
        # 6. Órdenes de Trabajo (referencia Equipo, EstadoOT, Usuario)
        for ot in session.exec(select(OrdenTrabajo)).all():
            session.delete(ot)
        # 7. Herramientas
        for her in session.exec(select(Herramienta)).all():
            session.delete(her)
        # 8. Repuestos
        for rep in session.exec(select(Repuesto)).all():
            session.delete(rep)
        # 9. Contactos de proveedores (referencian Proveedor)
        for c in session.exec(select(ContactoProveedor)).all():
            session.delete(c)
        # 10. Proveedores
        for p in session.exec(select(Proveedor)).all():
            session.delete(p)
        # 11. Equipos (al final, después de borrar sus dependencias)
        for eq in session.exec(select(Equipo)).all():
            session.delete(eq)

        session.commit()

    # Borrar archivos físicos en uploads/ (excepto la carpeta base)
    uploads_base = UPLOADS_DIR
    if uploads_base.exists():
        for item in uploads_base.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            elif item.is_file() and item.name != ".gitkeep":
                item.unlink()

    return {
        "mensaje": "Base de datos limpiada correctamente",
        "resumen": resumen,
        "nota": (
            "Se conservaron: usuarios (admin/tech/user), estados de equipo, "
            "estados de OT y configuración del sistema. "
            "Las carpetas físicas en uploads/ también fueron borradas."
        )
    }
