"""
Utilidad para escribir archivos .meta.json junto a las carpetas de entidades.

Cada vez que se sube una imagen o un documento, se actualiza el archivo .meta.json
correspondiente con los metadatos de la entidad y sus documentos adjuntos.

Esto permite la recuperación de datos si la base de datos SQLite se pierde.
"""
import json
from pathlib import Path
from typing import Optional


def write_meta_json(carpeta: Path, data: dict):
    """
    Escribe o actualiza el archivo .meta.json en la carpeta dada.
    Si ya existe, hace merge con los datos existentes.
    """
    meta_path = carpeta / ".meta.json"
    
    existing = {}
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {}
    
    # Merge: los datos nuevos sobreescriben los existentes
    existing.update(data)
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def build_equipo_meta(equipo, imagen_ruta: Optional[str] = None) -> dict:
    """
    Construye el diccionario de metadatos para un equipo - RF01 v0.9.0.

    Incluye los nuevos campos (observaciones, fecha_inicio_garantia, condicion_origen,
    proveedor_principal_id) y excluye los campos obsoletos (registro_sanitario_bolivia,
    calibracion_proxima, responsable_tecnico_id, proveedor_principal texto).
    """
    data = {
        "entidad_tipo": "equipo",
        "id": equipo.id,
        "nombre_corto": equipo.nombre_corto,
        "codigo": f"E{equipo.id:04d}",
        "modelo": equipo.modelo,
        "marca": equipo.marca,
        "numero_serie": equipo.numero_serie,
        "numero_material": equipo.numero_material,
        "ubicacion_actual": equipo.ubicacion_actual,
        "estado_id": equipo.estado_id,
        # NUEVO v0.9.0: FK a Proveedor (en vez de texto libre)
        "proveedor_principal_id": equipo.proveedor_principal_id,
        # NUEVO v0.9.0: origen del equipo
        "condicion_origen": equipo.condicion_origen,
        # NUEVO v0.9.0: fecha de inicio de garantía
        "fecha_inicio_garantia": equipo.fecha_inicio_garantia.isoformat() if equipo.fecha_inicio_garantia else None,
        "fecha_fin_garantia": equipo.fecha_fin_garantia.isoformat() if equipo.fecha_fin_garantia else None,
        # NUEVO v0.9.0: observaciones operativas
        "observaciones": equipo.observaciones,
        # CAMPOS ELIMINADOS en v0.9.0 (no se incluyen):
        # - registro_sanitario_bolivia (universalidad)
        # - calibracion_proxima (gestionado vía MP/OT)
        # - responsable_tecnico_id (asignación en OT/MP)
        # - proveedor_principal (texto, reemplazado por proveedor_principal_id FK)
    }
    if imagen_ruta:
        data["imagen_ruta"] = imagen_ruta
    elif hasattr(equipo, 'imagen_ruta') and equipo.imagen_ruta:
        data["imagen_ruta"] = equipo.imagen_ruta
    return data


def build_repuesto_meta(repuesto, imagen_ruta: Optional[str] = None) -> dict:
    """Construye el diccionario de metadatos para un repuesto."""
    data = {
        "entidad_tipo": "repuesto",
        "id": repuesto.id,
        "nombre_repuesto": repuesto.nombre_repuesto,
        "codigo": f"R{repuesto.id:04d}",
        "numero_serie": repuesto.numero_serie,
        "numero_material": repuesto.numero_material,
        "descripcion": repuesto.descripcion,
        "especificaciones_tecnicas": repuesto.especificaciones_tecnicas,
        "cantidad_disponible": repuesto.cantidad_disponible,
        "unidad_medida": repuesto.unidad_medida,
        "ubicacion_almacen": repuesto.ubicacion_almacen,
        "nivel_stock_minimo": repuesto.nivel_stock_minimo,
        "proveedor_ultimo": repuesto.proveedor_ultimo,
        "precio_referencia": repuesto.precio_referencia,
    }
    if imagen_ruta:
        data["imagen_ruta"] = imagen_ruta
    return data


def build_herramienta_meta(herramienta, imagen_ruta: Optional[str] = None) -> dict:
    """Construye el diccionario de metadatos para una herramienta."""
    data = {
        "entidad_tipo": "herramienta",
        "id": herramienta.id,
        "nombre_herramienta": herramienta.nombre_herramienta,
        "codigo": f"H{herramienta.id:04d}",
        "numero_identificacion": herramienta.numero_identificacion,
        "descripcion": herramienta.descripcion,
        "categoria": herramienta.categoria,
        "cantidad_disponible": herramienta.cantidad_disponible,
        "unidad_medida": herramienta.unidad_medida,
        "ubicacion_almacen": herramienta.ubicacion_almacen,
        "estado_uso": herramienta.estado_uso,
        "costo_adquisicion": herramienta.costo_adquisicion,
        "proveedor_ultimo": herramienta.proveedor_ultimo,
        "observaciones": herramienta.observaciones,
    }
    if imagen_ruta:
        data["imagen_ruta"] = imagen_ruta
    return data


def update_doc_meta_json(doc_dir: Path, doc_entry: dict):
    """
    Actualiza el archivo .meta.json dentro de la carpeta DOC/
    con la información de un documento recién subido.
    """
    meta_path = doc_dir / ".meta.json"
    
    existing = {"documentos": []}
    if meta_path.exists():
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing = {"documentos": []}
    
    if "documentos" not in existing:
        existing["documentos"] = []
    
    # Agregar o actualizar la entrada del documento
    found = False
    for i, doc in enumerate(existing["documentos"]):
        if doc.get("nombre_archivo") == doc_entry.get("nombre_archivo"):
            existing["documentos"][i] = doc_entry
            found = True
            break
    
    if not found:
        existing["documentos"].append(doc_entry)
    
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def remove_doc_meta_json(doc_dir: Path, nombre_archivo: str):
    """
    Elimina la entrada de un documento del archivo .meta.json
    dentro de la carpeta DOC/.
    """
    meta_path = doc_dir / ".meta.json"
    
    if not meta_path.exists():
        return
    
    try:
        with open(meta_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    except (json.JSONDecodeError, IOError):
        return
    
    if "documentos" in existing:
        existing["documentos"] = [
            doc for doc in existing["documentos"]
            if doc.get("nombre_archivo") != nombre_archivo
        ]
        
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2, ensure_ascii=False)
