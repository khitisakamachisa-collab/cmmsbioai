from typing import Optional, List, Any
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
    pass

# Esquema para Leer (Respuesta)
# v0.9.1: costos_adicionales ahora es una lista de OtCostoAdicional (no un float)
#          y se agrega total_costos_adicionales. Los campos costo_adicional y
#          costos_adicionales (float) se mantienen como Optional para compatibilidad
#          con la BD SQLite (que aún los tiene como columnas), pero no se usan.
class OrdenTrabajoRead(OrdenTrabajoBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    # v0.9.1: campos obsoletos mantenidos para compatibilidad con BD existente
    costo_adicional: Optional[float] = None
    costos_adicionales_legacy: Optional[float] = None  # renombrado para evitar conflicto
    # v0.9.1: nuevos campos para RF11
    repuestos_usados: Optional[List[Any]] = None
    costos_adicionales: Optional[List[Any]] = None  # ahora es lista de OtCostoAdicional
    total_costos_adicionales: Optional[float] = None
    # v0.9.2: FK opcional a Contrato (RF12)
    contrato_id: Optional[int] = None
    class Config:
        from_attributes = True

# Esquema para Actualizar (Permite editar todo)
# v0.9.1: eliminados costo_adicional y costos_adicionales (reemplazados por OtCostoAdicional)
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
    repuestos_utilizados: Optional[List[dict]] = None
    contrato_id: Optional[int] = None  # v0.9.2: RF12
