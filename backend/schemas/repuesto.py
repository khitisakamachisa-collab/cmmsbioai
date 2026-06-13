from pydantic import BaseModel
from typing import Optional
from datetime import date as date_type

class RepuestoCreate(BaseModel):
    nombre_repuesto: str
    numero_serie: Optional[str] = None
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    especificaciones_tecnicas: Optional[str] = None
    cantidad_disponible: int = 0
    unidad_medida: str = "unidad"
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None
    proveedor_ultimo: Optional[str] = None
    fecha_ultima_entrada: Optional[date_type] = None
    precio_referencia: Optional[float] = None

class RepuestoRead(BaseModel):
    id: int
    nombre_repuesto: str
    numero_serie: Optional[str] = None
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    especificaciones_tecnicas: Optional[str] = None
    cantidad_disponible: int
    unidad_medida: str
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None
    proveedor_ultimo: Optional[str] = None
    fecha_ultima_entrada: Optional[date_type] = None
    precio_referencia: Optional[float] = None
    imagen_ruta: Optional[str] = None

    class Config:
        from_attributes = True


class RepuestoUpdate(BaseModel):
    nombre_repuesto: Optional[str] = None
    numero_serie: Optional[str] = None
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    especificaciones_tecnicas: Optional[str] = None
    cantidad_disponible: Optional[int] = None
    unidad_medida: Optional[str] = None
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None
    proveedor_ultimo: Optional[str] = None
    fecha_ultima_entrada: Optional[date_type] = None
    precio_referencia: Optional[float] = None
    imagen_ruta: Optional[str] = None
