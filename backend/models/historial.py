from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class EventoHistorial(SQLModel, table=True):
    """Registro automático de eventos de mantenimiento por equipo.
    Se inserta automáticamente cuando se completa una Orden de Trabajo."""
    __tablename__ = "eventohistorial"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Equipo al que pertenece el evento
    equipo_id: int = Field(foreign_key="equipo.id")

    # OT que generó el evento (si aplica)
    orden_trabajo_id: Optional[int] = Field(default=None, foreign_key="ordentrabajo.id")

    # Tipo de evento: "preventivo", "correctivo", "calibracion", "otro"
    tipo_evento: str

    # Descripción del evento
    descripcion: str

    # Técnico que realizó el trabajo
    tecnico_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    # Fechas
    fecha_evento: datetime = Field(default_factory=datetime.now)

    # Detalles adicionales
    acciones_realizadas: Optional[str] = None
    tiempo_invertido: Optional[float] = None
    costo: Optional[float] = None

    # Repuestos utilizados (resumen textual)
    repuestos_utilizados: Optional[str] = None
