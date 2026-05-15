from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

# Esquema base
class OrdenTrabajoBase(BaseModel):
    equipo_id: int
    estado_id: int
    prioridad: str = "Media"
    tecnico_asignado_id: Optional[int] = None # NUEVO: Permitir asignar técnico
    titulo: str
    descripcion_falla: str
    fecha_vencimiento: Optional[date] = None
    
    # Campos que antes faltaban o eran opcionales
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None

# Esquema para Crear
class OrdenTrabajoCreate(OrdenTrabajoBase):
    pass

# Esquema para Leer (Respuesta)
class OrdenTrabajoRead(OrdenTrabajoBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    repuestos_usados: Optional[List] = None # <--- AGREGA ESTA LÍNEA
    class Config:
        from_attributes = True

# Esquema para Actualizar (Permite editar todo)
class OrdenTrabajoUpdate(BaseModel):
    estado_id: Optional[int] = None
    prioridad: Optional[str] = None
    tecnico_asignado_id: Optional[int] = None # NUEVO: Permitir cambiar técnico
    titulo: Optional[str] = None
    descripcion_falla: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    fecha_vencimiento: Optional[date] = None
    repuestos_utilizados: Optional[List[dict]] = None