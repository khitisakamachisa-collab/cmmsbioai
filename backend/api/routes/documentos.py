import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import FileResponse
from sqlmodel import Session, select
from typing import Optional, List
from database import get_session
from models.documentos import DocumentoAdjunto
from models.equipos import Equipo
from config import get_dir

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


# --- ENDPOINT: Subir documento ---
@router.post("/")
async def subir_documento(
    file: UploadFile = File(...),
    orden_trabajo_id: Optional[int] = Form(None),
    equipo_id: Optional[int] = Form(None),
    descripcion: Optional[str] = Form(None),
    categoria: Optional[str] = Form("otro"),
    subido_por: Optional[str] = Form(None),
    session: Session = Depends(get_session)
):
    """
    Sube un documento adjunto asociado a una OT o a un Equipo.
    Se debe proporcionar al menos uno: orden_trabajo_id o equipo_id.
    """
    if not orden_trabajo_id and not equipo_id:
        raise HTTPException(status_code=400, detail="Debe indicar orden_trabajo_id o equipo_id")

    # Leer el contenido del archivo
    contenido = await file.read()
    ext, mime_type = _validate_file(file.filename, len(contenido))

    # Determinar subdirectorio
    if orden_trabajo_id:
        subdir = get_dir("ot_documentos") / f"ot_{orden_trabajo_id}"
    elif equipo_id:
        # Estructura: uploads/EQUIPOS/EXXXX_numero_serie/DOC/
        equipo = session.get(Equipo, equipo_id)
        if equipo:
            equipo_code = f"E{equipo_id:04d}"
            serie_safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in (equipo.numero_serie or "SN"))
            folder_name = f"{equipo_code}_{serie_safe}"
            subdir = get_dir("equipos_documentos") / folder_name / "DOC"
        else:
            # Fallback si no se encuentra el equipo
            subdir = get_dir("uploads_base") / f"equipo_{equipo_id}"
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
        "equipo_id": doc.equipo_id
    }


# --- ENDPOINT: Listar documentos ---
@router.get("/")
def listar_documentos(
    orden_trabajo_id: Optional[int] = Query(None),
    equipo_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Lista documentos adjuntos filtrados por OT o Equipo.
    """
    query = select(DocumentoAdjunto)

    if orden_trabajo_id:
        query = query.where(DocumentoAdjunto.orden_trabajo_id == orden_trabajo_id)
    if equipo_id:
        query = query.where(DocumentoAdjunto.equipo_id == equipo_id)

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
            "equipo_id": doc.equipo_id
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
    """Elimina un documento adjunto (registro BD + archivo fisico)."""
    doc = session.get(DocumentoAdjunto, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    # Eliminar archivo fisico
    file_path = Path(doc.ruta_archivo)
    if file_path.exists():
        file_path.unlink()
        # Limpiar directorio vacio
        parent = file_path.parent
        try:
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except Exception:
            pass

    # Eliminar registro de BD
    session.delete(doc)
    session.commit()

    return {"ok": True, "message": "Documento eliminado"}
