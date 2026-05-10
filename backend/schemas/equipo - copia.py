from pydantic import BaseModel
from typing import Optional
from datetime import date
from typing import Optional # <--- Agrega esto arriba si no existe


class EquipoCreate(BaseModel):
    nombre_corto: Optional[str] = None
    modelo: str
    numero_serie: str
    marca: str
    fecha_adquisicion: date
    registro_sanitario_bolivia: Optional[str] = None
    ubicacion_actual: Optional[str] = None
    proveedor_principal: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_ruta: Optional[str] = None
    calibracion_proxima: Optional[date] = None
    # Llaves Foráneas
    responsable_tecnico_id: Optional[int] = None
    #estado_id: int
    estado_id: int = 1
    #estado_id: Optional[int] = None

# NUEVA CLASE PARA EDITAR
class EquipoUpdate(BaseModel):
    nombre_corto: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    marca: Optional[str] = None
    fecha_adquisicion: Optional[date] = None
    ubicacion_actual: Optional[str] = None
    estado_id: Optional[int] = None
    # Puedes agregar más campos aquí si quieres permitir editarlos

class EquipoRead(BaseModel):
    id: int
    nombre_corto: Optional[str]
    modelo: str
    numero_serie: str
    marca: str
    fecha_adquisicion: date
    ubicacion_actual: Optional[str]
    estado_id: int
    responsable_tecnico_id: Optional[int]

    class Config:
        from_attributes = True