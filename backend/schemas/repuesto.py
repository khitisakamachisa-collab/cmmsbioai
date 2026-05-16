from pydantic import BaseModel
from typing import Optional

class RepuestoCreate(BaseModel):
    nombre_repuesto: str
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad_disponible: int = 0
    unidad_medida: str = "unidad"
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None

class RepuestoRead(BaseModel):
    id: int
    nombre_repuesto: str
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad_disponible: int
    unidad_medida: str
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None
    imagen: Optional[str] = None

    class Config:
        from_attributes = True


class RepuestoUpdate(BaseModel):
    nombre_repuesto: Optional[str] = None
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad_disponible: Optional[int] = None
    unidad_medida: Optional[str] = None
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None