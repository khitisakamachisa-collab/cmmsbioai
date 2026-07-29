from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date


class EventoHistorialCreate(BaseModel):
    """Schema para crear un evento de historial manualmente"""
    equipo_id: int
    orden_trabajo_id: Optional[int] = None
    tipo_evento: str  # "preventivo", "correctivo", "calibracion", "otro"
    descripcion: str
    tecnico_id: Optional[int] = None
    fecha_evento: Optional[datetime] = None
    acciones_realizadas: Optional[str] = None
    tiempo_invertido: Optional[float] = None
    costo: Optional[float] = None
    repuestos_utilizados: Optional[str] = None


class EventoHistorialRead(BaseModel):
    """Schema para leer/retornar eventos de historial"""
    id: int
    equipo_id: int
    orden_trabajo_id: Optional[int] = None
    tipo_evento: str
    descripcion: str
    tecnico_id: Optional[int] = None
    fecha_evento: Optional[datetime] = None
    acciones_realizadas: Optional[str] = None
    tiempo_invertido: Optional[float] = None
    costo: Optional[float] = None
    repuestos_utilizados: Optional[str] = None

    # Campos extra para la vista (no están en la tabla, se llenan en la consulta)
    equipo_nombre: Optional[str] = None
    tecnico_nombre: Optional[str] = None
    ot_titulo: Optional[str] = None

    class Config:
        from_attributes = True


class EventoHistorialUpdate(BaseModel):
    """Schema para actualizar un evento de historial"""
    tipo_evento: Optional[str] = None
    descripcion: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    tiempo_invertido: Optional[float] = None
    costo: Optional[float] = None
    repuestos_utilizados: Optional[str] = None
