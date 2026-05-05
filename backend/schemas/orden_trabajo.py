from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime # <--- IMPORTANTE: Importar datetime

# Clase auxiliar para recibir un repuesto individual
class RepuestoUsado(BaseModel):
    repuesto_id: int
    cantidad: int

class OrdenTrabajoCreate(BaseModel):
    equipo_id: int
    estado_id: int
    prioridad: str
    tecnico_asignado_id: Optional[int] = None
    fecha_vencimiento: Optional[str] = None
    titulo: str
    descripcion_falla: str

class OrdenTrabajoRead(BaseModel):
    id: int
    equipo_id: int
    estado_id: int
    prioridad: str
    titulo: str
    descripcion_falla: str
    fecha_creacion: datetime # <--- CORRECCIÓN: Cambiar de 'str' a 'datetime'

    class Config:
        from_attributes = True

class OrdenTrabajoUpdate(BaseModel):
    estado_id: int
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    costo_adicional: Optional[float] = None
    repuestos_utilizados: Optional[List[RepuestoUsado]] = None