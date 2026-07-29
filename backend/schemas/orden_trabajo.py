from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

# Esquema base
class OrdenTrabajoBase(BaseModel):
    equipo_id: int
    estado_id: int
    prioridad: str = "Media"
    tecnico_asignado_id: Optional[int] = None
    titulo: str
    descripcion_falla: str
    fecha_vencimiento: Optional[date] = None
    orden_preventiva_id: Optional[int] = None
    
    # Campos de cierre
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    unidad_tiempo: Optional[str] = "horas"  # "horas" o "dias"

# Esquema para Crear
class OrdenTrabajoCreate(OrdenTrabajoBase):
    # v0.9.23: fecha_creacion editable (datetime completo: fecha + hora)
    fecha_creacion: Optional[datetime] = None
    # v0.9.19: permitir recibir repuestos_utilizados al crear la OT
    repuestos_utilizados: Optional[List[dict]] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None

# Esquema para Leer (Respuesta)
class OrdenTrabajoRead(OrdenTrabajoBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None
    repuestos_usados: Optional[List] = None
    class Config:
        from_attributes = True

# Esquema para Actualizar (Permite editar todo)
class OrdenTrabajoUpdate(BaseModel):
    estado_id: Optional[int] = None
    prioridad: Optional[str] = None
    tecnico_asignado_id: Optional[int] = None
    titulo: Optional[str] = None
    descripcion_falla: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    unidad_tiempo: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    # v0.9.23: fecha_creacion editable (datetime completo: fecha + hora)
    fecha_creacion: Optional[datetime] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None
    repuestos_utilizados: Optional[List[dict]] = None