import os
from pathlib import Path
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import Optional, List
from database import get_session
from models.documentos import DocumentoAdjunto
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo
from models.repuestos import Repuesto
from models.herramientas import Herramienta
from config import get_dir, sanitize_filename

router = APIRouter(prefix="/documentos", tags=["Documentos Adjuntos"])

# Extensiones y MIME types permitidos
ALLOWED_EXTENSIONS = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".txt": "text/plain",
    ".zip": "application/zip",
}

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB


def _validate_file(filename: str, file_size: int):
    """Valida extension y tamaño del archivo."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Extension no permitida: {ext}. Permitidas: {', '.join(ALLOWED_EXTENSIONS.keys())}"
        )
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Archivo demasiado grande (max 20 MB). Su archivo: {file_size / 1024 / 1024:.1f} MB"
        )
    return ext, ALLOWED_EXTENSIONS[ext]


def _get_equipo_folder_name(equipo_id: int, session: Session) -> str:
    """
    Genera el nombre de carpeta para un equipo: EXXXX_Modelo_Serie
    """
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        return f"equipo_{equipo_id}"
    equipo_code = f"E{equipo_id:04d}"
    modelo_safe = sanitize_filename(equipo.modelo, "SM")
    serie_safe = sanitize_filename(equipo.numero_serie, "SN")
    return f"{equipo_code}_{modelo_safe}_{serie_safe}"


def _get_ot_folder_name(orden_trabajo_id: int, equipo_id: int, session: Session) -> str:
    """
    Genera el nombre de carpeta para una OT: OTxxxx_Titulo_Modelo_Serie

    Este nombre se usa tanto para:
    - La subcarpeta dentro del equipo: EQUIPOS/Exxxx_Modelo_Serie/OT/OTxxxx_Titulo_Modelo_Serie/
    - El archivo txt de referencia en uploads/OT/: OTxxxx_Titulo_Modelo_Serie.txt

    La consistencia permite relacionar facilmente ambos elementos.
    """
    ot = session.get(OrdenTrabajo, orden_trabajo_id)
    equipo = session.get(Equipo, equipo_id)
    ot_code = f"OT{orden_trabajo_id:04d}"
    titulo_safe = sanitize_filename(ot.titulo, "ST") if ot else "ST"
    modelo_safe = sanitize_filename(equipo.modelo, "SM") if equipo else "SM"
    serie_safe = sanitize_filename(equipo.numero_serie, "SN") if equipo else "SN"
    return f"{ot_code}_{titulo_safe}_{modelo_safe}_{serie_safe}"


def _crear_referencia_ot(orden_trabajo_id: int, equipo_id: int, session: Session):
    """
    Crea un archivo .txt de referencia en uploads/OT/ con informacion del equipo
    al que pertenece la OT. Permite reconstruir la informacion si se pierde la BD.

    Nombre del archivo: OTxxxx_Titulo_Modelo_Serie.txt
    """
    try:
        ot = session.get(OrdenTrabajo, orden_trabajo_id)
        equipo = session.get(Equipo, equipo_id)
        if not ot or not equipo:
            return

        ot_code = f"OT{orden_trabajo_id:04d}"

        # Usar el mismo nombre base para la carpeta OT y el archivo txt
        ot_folder_name = _get_ot_folder_name(orden_trabajo_id, equipo_id, session)
        ref_filename = f"{ot_folder_name}.txt"

        # Directorio raiz de OT
        ot_root = get_dir("ot_documentos")
        ot_root.mkdir(parents=True, exist_ok=True)

        ref_path = ot_root / ref_filename

        equipo_code = f"E{equipo_id:04d}"
        equipo_folder = _get_equipo_folder_name(equipo_id, session)

        contenido = (
            f"=== REFERENCIA DE ORDEN DE TRABAJO ===\n"
            f"Fecha de generacion: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"\n"
            f"--- OT ---\n"
            f"OT ID: {orden_trabajo_id}\n"
            f"OT Codigo: {ot_code}\n"
            f"Titulo/Tipo: {ot.titulo or 'N/A'}\n"
            f"Prioridad: {ot.prioridad or 'N/A'}\n"
            f"Descripcion falla: {ot.descripcion_falla or 'N/A'}\n"
            f"\n"
            f"--- EQUIPO ASOCIADO ---\n"
            f"Equipo ID: {equipo_id}\n"
            f"Equipo Codigo: {equipo_code}\n"
            f"Nombre corto: {equipo.nombre_corto or 'N/A'}\n"
            f"Modelo: {equipo.modelo or 'N/A'}\n"
            f"Marca: {equipo.marca or 'N/A'}\n"
            f"Numero de serie: {equipo.numero_serie or 'N/A'}\n"
            f"Numero de material: {equipo.numero_material or 'N/A'}\n"
            f"Ubicacion: {equipo.ubicacion_actual or 'N/A'}\n"
            f"\n"
            f"--- UBICACION FISICA DE ARCHIVOS ---\n"
            f"Carpeta del equipo: uploads/EQUIPOS/{equipo_folder}/\n"
            f"Documentos de esta OT: uploads/EQUIPOS/{equipo_folder}/OT/{ot_folder_name}/\n"
            f"Este archivo txt: uploads/OT/{ref_filename}\n"
            f"\n"
            f"Nota: El nombre de la carpeta OT y este archivo txt coinciden.\n"
            f"Busque la carpeta OT dentro del equipo con el mismo nombre.\n"
            f"\n"
            f"Este archivo es generado automaticamente por CMMS-BioAI.\n"
            f"Permite reconstruir la relacion OT-Equipo si la base de datos se pierde.\n"
        )

        with open(ref_path, "w", encoding="utf-8") as f:
            f.write(contenido)

    except Exception as e:
        # No fallar la subida del documento si la referencia no se puede crear
        print(f"[documentos.py] WARNING: No se pudo crear referencia OT: {e}")


# --- ENDPOINT: Subir documento ---
@router.post("/")
async def subir_documento(
    file: UploadFile = File(...),
    orden_trabajo_id: Optional[int] = Form(None),
    equipo_id: Optional[int] = Form(None),
    repuesto_id: Optional[int] = Form(None),
    herramienta_id: Optional[int] = Form(None),
    descripcion: Optional[str] = Form(None),
    categoria: Optional[str] = Form("otro"),
    subido_por: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """
    Sube un documento adjunto asociado a una OT, un Equipo, un Repuesto o una Herramienta.
    Se debe proporcionar al menos uno: orden_trabajo_id, equipo_id, repuesto_id o herramienta_id.

    Estructura de carpetas:
    - OT: uploads/EQUIPOS/EXXXX_Modelo_Serie/OT/OTxxxx_Titulo_Modelo_Serie/  (+ referencia en uploads/OT/OTxxxx_Titulo_Modelo_Serie.txt)
    - Equipo: uploads/EQUIPOS/EXXXX_Modelo_Serie/DOC/
    - Repuesto: uploads/INVENTARIO/I0001_Nombre/DOC/
    - Herramienta: uploads/HERRAMIENTAS/H0001_Nombre/DOC/
    """
    if not orden_trabajo_id and not equipo_id and not repuesto_id and not herramienta_id:
        raise HTTPException(status_code=400, detail="Debe indicar orden_trabajo_id, equipo_id, repuesto_id o herramienta_id")

    # Leer el contenido del archivo
    contenido = await file.read()
    ext, mime_type = _validate_file(file.filename, len(contenido))

    # Determinar subdirectorio
    if orden_trabajo_id:
        # Las OTs se guardan dentro de la carpeta del equipo
        # Estructura: uploads/EQUIPOS/EXXXX_Modelo_Serie/OT/OTxxxx_Titulo_Modelo_Serie/
        ot = session.get(OrdenTrabajo, orden_trabajo_id)
        if ot and ot.equipo_id:
            equipo_folder = _get_equipo_folder_name(ot.equipo_id, session)
            ot_folder_name = _get_ot_folder_name(orden_trabajo_id, ot.equipo_id, session)
            subdir = get_dir("equipos_documentos") / equipo_folder / "OT" / ot_folder_name
            # Crear archivo de referencia en uploads/OT/ (mismo nombre que la carpeta + .txt)
            _crear_referencia_ot(orden_trabajo_id, ot.equipo_id, session)
        else:
            # Fallback si no se encuentra la OT o no tiene equipo
            subdir = get_dir("ot_documentos") / f"OT{orden_trabajo_id:04d}"
    elif equipo_id:
        # Estructura: uploads/EQUIPOS/EXXXX_Modelo_Serie/DOC/
        equipo_folder = _get_equipo_folder_name(equipo_id, session)
        subdir = get_dir("equipos_documentos") / equipo_folder / "DOC"
    elif repuesto_id:
        # Estructura: uploads/INVENTARIO/I0001_Nombre/DOC/
        repuesto = session.get(Repuesto, repuesto_id)
        if repuesto:
            rep_code = f"I{repuesto_id:04d}"
            nombre_safe = sanitize_filename(repuesto.nombre_repuesto, "SN")
            folder_name = f"{rep_code}_{nombre_safe}"
            subdir = get_dir("inventario_documentos") / folder_name / "DOC"
        else:
            subdir = get_dir("uploads_base") / f"repuesto_{repuesto_id}"
    elif herramienta_id:
        # Estructura: uploads/HERRAMIENTAS/H0001_Nombre/DOC/
        herramienta = session.get(Herramienta, herramienta_id)
        if herramienta:
            herr_code = f"H{herramienta_id:04d}"
            nombre_safe = sanitize_filename(herramienta.nombre_herramienta, "SN")
            folder_name = f"{herr_code}_{nombre_safe}"
            subdir = get_dir("herramientas_documentos") / folder_name / "DOC"
        else:
            subdir = get_dir("uploads_base") / f"herramienta_{herramienta_id}"
    else:
        subdir = get_dir("uploads_base")
    subdir.mkdir(parents=True, exist_ok=True)

    # Usar el nombre original del archivo; si ya existe, agregar sufijo (1), (2), etc.
    target_name = file.filename
    file_path = subdir / target_name
    counter = 1
    while file_path.exists():
        stem = Path(target_name).stem
        suffix = Path(target_name).suffix
        target_name = f"{stem} ({counter}){suffix}"
        file_path = subdir / target_name
        counter += 1

    # Guardar archivo en disco
    with open(file_path, "wb") as f:
        f.write(contenido)

    # Crear registro en BD
    doc = DocumentoAdjunto(
        orden_trabajo_id=orden_trabajo_id,
        equipo_id=equipo_id,
        repuesto_id=repuesto_id,
        herramienta_id=herramienta_id,
        nombre_archivo=file.filename,
        ruta_archivo=str(file_path),
        tipo_archivo=mime_type,
        tamanio_bytes=len(contenido),
        descripcion=descripcion,
        categoria=categoria,
        subido_por=subido_por
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    return {
        "id": doc.id,
        "nombre_archivo": doc.nombre_archivo,
        "tipo_archivo": doc.tipo_archivo,
        "tamanio_bytes": doc.tamanio_bytes,
        "categoria": doc.categoria,
        "descripcion": doc.descripcion,
        "fecha_subida": doc.fecha_subida.isoformat() if doc.fecha_subida else None,
        "subido_por": doc.subido_por,
        "orden_trabajo_id": doc.orden_trabajo_id,
        "equipo_id": doc.equipo_id,
        "repuesto_id": doc.repuesto_id,
        "herramienta_id": doc.herramienta_id
    }


# --- ENDPOINT: Listar documentos ---
@router.get("/")
def listar_documentos(
    orden_trabajo_id: Optional[int] = Query(None),
    equipo_id: Optional[int] = Query(None),
    repuesto_id: Optional[int] = Query(None),
    herramienta_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """Lista documentos adjuntos filtrados por OT, Equipo, Repuesto o Herramienta."""
    query = select(DocumentoAdjunto)

    if orden_trabajo_id:
        query = query.where(DocumentoAdjunto.orden_trabajo_id == orden_trabajo_id)
    if equipo_id:
        query = query.where(DocumentoAdjunto.equipo_id == equipo_id)
    if repuesto_id:
        query = query.where(DocumentoAdjunto.repuesto_id == repuesto_id)
    if herramienta_id:
        query = query.where(DocumentoAdjunto.herramienta_id == herramienta_id)

    documentos = session.exec(query.order_by(DocumentoAdjunto.fecha_subida.desc())).all()

    resultado = []
    for doc in documentos:
        resultado.append({
            "id": doc.id,
            "nombre_archivo": doc.nombre_archivo,
            "tipo_archivo": doc.tipo_archivo,
            "tamanio_bytes": doc.tamanio_bytes,
            "categoria": doc.categoria,
            "descripcion": doc.descripcion,
            "fecha_subida": doc.fecha_subida.isoformat() if doc.fecha_subida else None,
            "subido_por": doc.subido_por,
            "orden_trabajo_id": doc.orden_trabajo_id,
            "equipo_id": doc.equipo_id,
            "repuesto_id": doc.repuesto_id,
            "herramienta_id": doc.herramienta_id
        })

    return resultado


# --- ENDPOINT: Ver documento (abre en navegador) ---
@router.get("/{doc_id}/ver")
def ver_documento(doc_id: int, session: Session = Depends(get_session)):
    """Abre un documento en el navegador (inline). Para PDF, imagenes, texto, etc."""
    doc = session.get(DocumentoAdjunto, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    file_path = Path(doc.ruta_archivo)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo fisico no encontrado en el servidor")

    return FileResponse(
        path=str(file_path),
        filename=doc.nombre_archivo,
        media_type=doc.tipo_archivo,
        content_disposition_type="inline"
    )


# --- ENDPOINT: Descargar documento ---
@router.get("/{doc_id}/descargar")
def descargar_documento(doc_id: int, session: Session = Depends(get_session)):
    """Descarga un documento adjunto por su ID (fuerza descarga)."""
    doc = session.get(DocumentoAdjunto, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    file_path = Path(doc.ruta_archivo)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo fisico no encontrado en el servidor")

    return FileResponse(
        path=str(file_path),
        filename=doc.nombre_archivo,
        media_type=doc.tipo_archivo,
        content_disposition_type="attachment"
    )


# --- ENDPOINT: Eliminar documento ---
@router.delete("/{doc_id}")
def eliminar_documento(doc_id: int, session: Session = Depends(get_session)):
    """Elimina un documento adjunto (registro BD + archivo fisico).

    Si el documento pertenece a una OT y la carpeta OT queda vacia,
    tambien elimina el archivo .txt de referencia en uploads/OT/.
    """
    doc = session.get(DocumentoAdjunto, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Guardar datos antes de eliminar para limpieza posterior
    ot_id = doc.orden_trabajo_id
    equipo_id_doc = doc.equipo_id

    # Eliminar archivo fisico
    file_path = Path(doc.ruta_archivo)
    ot_folder_was_cleaned = False
    if file_path.exists():
        file_path.unlink()
        # Limpiar directorios vacios (OT subfolder, OT, DOC)
        for _ in range(3):
            parent = file_path.parent
            try:
                if parent.is_dir() and not any(parent.iterdir()):
                    # Verificar si es una carpeta OT (contiene 'OT' en el path)
                    parent_name = parent.name
                    parent.rmdir()
                    file_path = parent
                    # Si la carpeta eliminada parece una carpeta de OT
                    if parent_name.startswith("OT") and "/OT/" in str(file_path):
                        ot_folder_was_cleaned = True
                else:
                    break
            except Exception:
                break

    # Si se elimino la carpeta OT completa, limpiar el archivo .txt de referencia
    if ot_folder_was_cleaned and ot_id and equipo_id_doc:
        try:
            ot_folder_name = _get_ot_folder_name(ot_id, equipo_id_doc, session)
            ref_filename = f"{ot_folder_name}.txt"
            ot_root = get_dir("ot_documentos")
            ref_path = ot_root / ref_filename
            if ref_path.exists():
                ref_path.unlink()
        except Exception:
            pass  # No fallar si no se puede limpiar la referencia

    # Eliminar registro de BD
    session.delete(doc)
    session.commit()

    return {"ok": True, "message": "Documento eliminado"}
