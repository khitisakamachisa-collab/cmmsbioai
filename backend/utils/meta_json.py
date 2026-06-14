"""
Utilidad para generar archivos .meta.json junto a los archivos subidos.

Cada vez que se sube una imagen, se crea/actualiza un .meta.json en la carpeta
del equipo/repuesto/herramienta con los datos clave del registro de la BD.

Cada vez que se sube un documento, se agrega una entrada al array "documentos"
del .meta.json de la carpeta DOC/ u OT/. Así un solo archivo contiene la
información de todos los documentos de esa carpeta.

Esto permite recuperar la información si la base de datos se pierde o se
regenera. La futura página Configuración (Capa 2) usará estos archivos
para escanear y reconstruir registros huérfanos.

Estructura de ejemplo:
    uploads/EQUIPOS/E0001_SC7000_SN001/
    ├── E0001_SC7000_SN001.jpg       ← la imagen
    ├── .meta.json                    ← metadatos del equipo
    └── DOC/                          ← documentos adjuntos
        ├── manual.pdf
        ├── factura.xlsx
        └── .meta.json                ← lista de todos los documentos:
            {
              "documentos": [
                { "documento_id": 1, "nombre_archivo": "manual.pdf", ... },
                { "documento_id": 2, "nombre_archivo": "factura.xlsx", ... }
              ]
            }
"""
import json
from pathlib import Path
from datetime import datetime


def write_meta_json(folder_path: Path, data: dict) -> None:
    """
    Escribe un archivo .meta.json en la carpeta especificada.

    Args:
        folder_path: Ruta de la carpeta donde se guardará el .meta.json
        data: Diccionario con los metadatos a guardar.
              Se agregará automáticamente el campo 'fecha_creacion_meta'.

    El archivo se escribe con indent=2 y ensure_ascii=False para
    que los caracteres especiales (ñ, acentos) sean legibles.
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    # Agregar timestamp de creación del meta
    meta = {**data, "fecha_creacion_meta": datetime.now().isoformat()}

    meta_path = folder_path / ".meta.json"

    # Si ya existe un .meta.json, hacer merge (no sobreescribir campos existentes
    # que puedan haber sido actualizados manualmente)
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            # Merge: los nuevos datos sobreescriben los existentes
            existing.update(meta)
            meta = existing
        except (json.JSONDecodeError, IOError):
            pass  # Si hay error, sobreescribir

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def delete_meta_json(folder_path: Path) -> None:
    """
    Elimina el archivo .meta.json de la carpeta especificada.
    Se llama cuando se elimina una imagen o un registro completo.
    """
    meta_path = Path(folder_path) / ".meta.json"
    if meta_path.exists():
        try:
            meta_path.unlink()
        except OSError:
            pass


# ─── Funciones para documentos (un solo .meta.json con lista) ───

def append_doc_to_meta_json(folder_path: Path, doc_data: dict) -> None:
    """
    Agrega un documento al array "documentos" del .meta.json de la carpeta.

    Si el archivo no existe, lo crea con la estructura:
        { "documentos": [doc_data] }
    Si ya existe, lee el array, agrega el nuevo documento y guarda.

    Args:
        folder_path: Ruta de la carpeta DOC/ u OT/ donde están los documentos
        doc_data: Diccionario con los metadatos del documento (de build_documento_meta)
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        folder_path.mkdir(parents=True, exist_ok=True)

    meta_path = folder_path / ".meta.json"

    # Agregar timestamp al documento individual
    doc_entry = {**doc_data, "fecha_creacion_meta": datetime.now().isoformat()}

    # Leer .meta.json existente o crear uno nuevo
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
        except (json.JSONDecodeError, IOError):
            meta = {}
    else:
        meta = {}

    # Asegurar que existe el array "documentos"
    if "documentos" not in meta:
        meta["documentos"] = []

    # Agregar el nuevo documento al array
    meta["documentos"].append(doc_entry)

    # Actualizar timestamp del archivo
    meta["fecha_actualizacion_meta"] = datetime.now().isoformat()

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


def remove_doc_from_meta_json(folder_path: Path, nombre_archivo: str) -> None:
    """
    Elimina un documento del array "documentos" del .meta.json de la carpeta.

    Se llama cuando se elimina un documento del sistema.

    Args:
        folder_path: Ruta de la carpeta DOC/ u OT/
        nombre_archivo: Nombre del archivo a eliminar del registro (ej: "manual.pdf")
    """
    folder_path = Path(folder_path)
    meta_path = folder_path / ".meta.json"

    if not meta_path.exists():
        return

    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
    except (json.JSONDecodeError, IOError):
        return

    if "documentos" not in meta:
        return

    # Filtrar el documento eliminado
    meta["documentos"] = [
        d for d in meta["documentos"]
        if d.get("nombre_archivo") != nombre_archivo
    ]

    # Actualizar timestamp
    meta["fecha_actualizacion_meta"] = datetime.now().isoformat()

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)


# ─── Builders de metadatos por entidad ───

def build_equipo_meta(equipo, imagen_ruta: str = None) -> dict:
    """Construye el diccionario de metadatos para un Equipo."""
    meta = {
        "tipo": "equipo",
        "id": equipo.id,
        "nombre_corto": equipo.nombre_corto,
        "modelo": equipo.modelo,
        "numero_serie": equipo.numero_serie,
        "numero_material": equipo.numero_material,
        "marca": equipo.marca,
        "ubicacion_actual": equipo.ubicacion_actual,
        "estado_id": equipo.estado_id,
        "proveedor_principal": equipo.proveedor_principal,
        "registro_sanitario_bolivia": equipo.registro_sanitario_bolivia,
    }
    if imagen_ruta:
        meta["imagen_ruta"] = imagen_ruta
    return meta


def build_repuesto_meta(repuesto, imagen_ruta: str = None) -> dict:
    """Construye el diccionario de metadatos para un Repuesto."""
    meta = {
        "tipo": "repuesto",
        "id": repuesto.id,
        "nombre_repuesto": repuesto.nombre_repuesto,
        "numero_serie": repuesto.numero_serie,
        "numero_material": repuesto.numero_material,
        "descripcion": repuesto.descripcion,
        "cantidad_disponible": repuesto.cantidad_disponible,
        "unidad_medida": repuesto.unidad_medida,
        "ubicacion_almacen": repuesto.ubicacion_almacen,
        "nivel_stock_minimo": repuesto.nivel_stock_minimo,
        "proveedor_ultimo": repuesto.proveedor_ultimo,
    }
    if imagen_ruta:
        meta["imagen_ruta"] = imagen_ruta
    return meta


def build_herramienta_meta(herramienta, imagen_ruta: str = None) -> dict:
    """Construye el diccionario de metadatos para una Herramienta."""
    meta = {
        "tipo": "herramienta",
        "id": herramienta.id,
        "nombre_herramienta": herramienta.nombre_herramienta,
        "numero_identificacion": herramienta.numero_identificacion,
        "descripcion": herramienta.descripcion,
        "categoria": herramienta.categoria,
        "cantidad_disponible": herramienta.cantidad_disponible,
        "unidad_medida": herramienta.unidad_medida,
        "ubicacion_almacen": herramienta.ubicacion_almacen,
        "estado_uso": herramienta.estado_uso,
        "costo_adquisicion": herramienta.costo_adquisicion,
        "proveedor_ultimo": herramienta.proveedor_ultimo,
    }
    if imagen_ruta:
        meta["imagen_ruta"] = imagen_ruta
    return meta


def build_documento_meta(doc, entidad_tipo: str, entidad_id: int, entidad_nombre: str) -> dict:
    """Construye el diccionario de metadatos para un DocumentoAdjunto."""
    return {
        "documento_id": doc.id,
        "entidad_tipo": entidad_tipo,
        "entidad_id": entidad_id,
        "entidad_nombre": entidad_nombre,
        "nombre_archivo": doc.nombre_archivo,
        "categoria": doc.categoria,
        "descripcion": doc.descripcion,
        "subido_por": doc.subido_por,
        "tamanio_bytes": doc.tamanio_bytes,
    }
