from typing import Optional, List
from pydantic import BaseModel
from datetime import date

class TareaRepuestoCreate(BaseModel):
    repuesto_id: int
    cantidad_requerida: int


class TareaRepuestoRead(BaseModel):
    repuesto_id: int
    cantidad_requerida: int
    nombre_repuesto: Optional[str] = None


# Esquema para CREAR una Tarea Preventiva
class TareaPreventivaCreate(BaseModel):
    equipo_id: int
    responsable_id: Optional[int] = None
    titulo: str
    descripcion: Optional[str] = None
    frecuencia_dias: int
    ultima_fecha: Optional[date] = None # Si ya se hizo alguna vez
    repuestos: Optional[List[TareaRepuestoCreate]] = None # Lista de repuestos necesarios

# Esquema para LEER/RESPONDER una Tarea Preventiva
class TareaPreventivaRead(BaseModel):
    id: int
    equipo_id: int
    responsable_id: Optional[int]
    titulo: str
    descripcion: Optional[str]
    frecuencia_dias: int
    ultima_fecha: Optional[date]
    proxima_fecha: Optional[date]
    activa: bool
    repuestos_detalle: Optional[List[TareaRepuestoRead]] = None

    class Config:
        from_attributes = True


# Esquema para ACTUALIZAR
class TareaPreventivaUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    frecuencia_dias: Optional[int] = None
    responsable_id: Optional[int] = None
    activa: Optional[bool] = None
    ultima_fecha: Optional[date] = None
    repuestos: Optional[List[TareaRepuestoCreate]] = None