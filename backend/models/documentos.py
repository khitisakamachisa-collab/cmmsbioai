from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class DocumentoAdjunto(SQLModel, table=True):
    """
    Tabla DocumentoAdjunto.
    Almacena referencias a archivos subidos (manuales, fotos, reportes, etc.)
    asociados a una Orden de Trabajo o a un Equipo.
    """
    __tablename__ = "documentoadjunto"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Entidad asociada: puede ser una OT, un Equipo o un Repuesto
    # Se usa uno u otro, los demás quedan en NULL
    orden_trabajo_id: Optional[int] = Field(default=None, foreign_key="ordentrabajo.id")
    equipo_id: Optional[int] = Field(default=None, foreign_key="equipo.id")
    repuesto_id: Optional[int] = Field(default=None, foreign_key="repuesto.id")

    # Datos del archivo
    nombre_archivo: str                          # Nombre original del archivo
    ruta_archivo: str                            # Ruta relativa en el servidor (ej: uploads/ot_5/foto.jpg)
    tipo_archivo: str                            # MIME type (ej: application/pdf, image/png)
    tamanio_bytes: int                           # Tamaño del archivo

    # Metadatos
    descripcion: Optional[str] = None            # Descripcion breve del documento
    categoria: Optional[str] = None              # Ej: manual, foto, reporte, garantia, otro
    fecha_subida: datetime = Field(default_factory=datetime.now)
    subido_por: Optional[str] = None             # Username de quien subio el archivo
