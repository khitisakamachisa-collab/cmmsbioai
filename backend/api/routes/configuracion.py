"""
Endpoints de Configuración del sistema CMMS-BioAI.

Capa 2 — Escaneo y recuperación:
    - GET  /configuracion/escanear          → Escanea .meta.json y reporta estado
    - POST /configuracion/recuperar         → Recupera registros huérfanos desde .meta.json

Capa 3 — Backup y Restore:
    - GET  /configuracion/backup            → Exporta la BD completa como JSON
    - POST /configuracion/restore           → Importa un backup JSON y restaura la BD

Configuración:
    - GET  /configuracion/                  → Lee la configuración actual
    - PUT  /configuracion/                  → Actualiza la configuración
    - GET  /configuracion/estados-bd        → Resumen de registros en la BD por tabla
"""
import json
import shutil
from datetime import datetime, date
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlmodel import Session, select

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
def put_configuracion(new_config: dict):
    """Actualiza la configuración del sistema y la guarda en config.json."""
    try:
        update_config(new_config)
        return {"mensaje": "Configuración actualizada correctamente", "config": get_config()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al actualizar configuración: {str(e)}")


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

    Devuelve:
    - Lista de entidades encontradas en archivos
    - Cuáles ya existen en BD y cuáles son huérfanas (solo en archivo)
    - Resumen estadístico
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

    # Escanear directorios de uploads
    uploads_base = UPLOADS_DIR

    # Mapa: carpeta base → tipo de entidad
    carpetas_entidad = {
        "EQUIPOS": "equipos",
        "REPUESTOS": "repuestos",
        "HERRAMIENTAS": "herramientas",
    }

    for carpeta_nombre, tipo in carpetas_entidad.items():
        carpeta = uploads_base / carpeta_nombre
        if not carpeta.exists():
            continue

        # Escanear subcarpetas de entidades (E0001_xxx, R0001_xxx, H0001_xxx)
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

            # Extraer ID del metadato
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

            # Verificar si es huérfano (existe en archivo pero no en BD)
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

    # Calcular resumen
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

    Los documentos se recuperan si su entidad padre existe (en BD o recién recuperada).

    Devuelve un resumen de cuántos registros fueron recuperados.
    """
    recuperados = {
        "equipos": 0,
        "repuestos": 0,
        "herramientas": 0,
        "documentos": 0,
    }
    errores = []

    uploads_base = UPLOADS_DIR

    # Paso 1: Recuperar entidades principales (Equipos, Repuestos, Herramientas)
    carpetas_entidad = {
        "EQUIPOS": ("equipos", Equipo),
        "REPUESTOS": ("repuestos", Repuesto),
        "HERRAMIENTAS": ("herramientas", Herramienta),
    }

    # Track IDs recuperados en esta sesión para resolver documentos después
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

                # Verificar si ya existe en BD
                existente = session.exec(select(modelo).where(modelo.id == entidad_id)).first()
                if existente:
                    continue

                # Crear registro desde metadatos
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
                            # Campos requeridos sin datos en meta → valores por defecto
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

        # Paso 2: Recuperar documentos si su entidad padre existe
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

                    # Verificar si ya existe en BD
                    existente = session.exec(
                        select(DocumentoAdjunto).where(DocumentoAdjunto.id == doc_id)
                    ).first()
                    if existente:
                        continue

                    # Verificar que la entidad padre existe (en BD o recién recuperada)
                    padre_tipo = doc_entry.get("entidad_tipo", tipo)
                    padre_id = doc_entry.get("entidad_id")

                    if padre_tipo and padre_id:
                        # Verificar existencia del padre
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

                    # Crear documento
                    try:
                        # Inferir ruta_archivo desde la carpeta
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
                            # Asignar FK según tipo de entidad padre
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
    Exporta toda la base de datos como un diccionario JSON.
    Cada tabla se exporta como una lista de diccionarios.

    El resultado incluye metadatos: fecha, versión y totales.
    """
    backup = {
        "metadatos": {
            "sistema": "CMMS-BioAI",
            "version": "1.0",
            "fecha_backup": datetime.now().isoformat(),
            "descripcion": "Backup completo de la base de datos",
        },
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

    # Agregar totales a metadatos
    backup["metadatos"]["totales"] = {
        nombre: len(registros) for nombre, registros in backup["datos"].items()
    }

    return backup


@router.post("/restore")
def restaurar_backup(backup_data: dict):
    """
    Restaura la base de datos desde un backup JSON.

    ADVERTENCIA: Esta operación elimina todos los datos existentes
    y los reemplaza con los del backup.

    El backup debe tener la estructura generada por GET /configuracion/backup.
    """
    if "datos" not in backup_data:
        raise HTTPException(status_code=400, detail="El backup no tiene la estructura esperada (falta clave 'datos')")

    datos = backup_data["datos"]
    restaurados = {}
    errores = []

    # Orden de restauración respetando FKs
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
        # Desactivar verificación de FK temporalmente para SQLite
        session.exec(select(1))  # Para asegurar conexión

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
                    # Filtrar campos que no pertenecen al modelo
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
        "errores": errores,
        "backup_origen": backup_data.get("metadatos", {}),
    }


# ──────────────────────────────────────────────────────────
# Extra: Descargar backup como archivo
# ──────────────────────────────────────────────────────────

@router.get("/backup/descargar")
def descargar_backup():
    """
    Genera y devuelve el backup como un archivo JSON descargable.
    El archivo se guarda temporalmente y se sirve para descarga.
    """
    from fastapi.responses import FileResponse
    import tempfile

    # Generar backup
    backup = generar_backup()

    # Crear archivo temporal
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


# ──────────────────────────────────────────────────────────
# Extra: Subir backup como archivo
# ──────────────────────────────────────────────────────────

@router.post("/restore/subir")
def subir_backup(archivo: UploadFile = File(...)):
    """
    Sube un archivo JSON de backup y restaura la base de datos.

    ADVERTENCIA: Esta operación elimina todos los datos existentes.
    """
    if not archivo.filename.endswith(".json"):
        raise HTTPException(status_code=400, detail="El archivo debe ser un .json")

    try:
        contenido = archivo.file.read()
        backup_data = json.loads(contenido.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo JSON: {str(e)}")

    return restaurar_backup(backup_data)
