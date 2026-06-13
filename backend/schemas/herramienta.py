from pydantic import BaseModel
from typing import Optional
from datetime import date as date_type


class HerramientaCreate(BaseModel):
    nombre_herramienta: str
    numero_identificacion: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: str = "Herramienta Manual"
    cantidad_disponible: int = 1
    unidad_medida: str = "unidad"
    ubicacion_almacen: Optional[str] = None
    estado_uso: str = "Disponible"
    costo_adquisicion: Optional[float] = None
    fecha_adquisicion: Optional[date_type] = None
    proveedor_ultimo: Optional[str] = None
    observaciones: Optional[str] = None


class HerramientaRead(BaseModel):
    id: int
    nombre_herramienta: str
    numero_identificacion: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: str
    cantidad_disponible: int
    unidad_medida: str
    ubicacion_almacen: Optional[str] = None
    estado_uso: str
    imagen_ruta: Optional[str] = None
    costo_adquisicion: Optional[float] = None
    fecha_adquisicion: Optional[date_type] = None
    proveedor_ultimo: Optional[str] = None
    observaciones: Optional[str] = None

    class Config:
        from_attributes = True


class HerramientaUpdate(BaseModel):
    nombre_herramienta: Optional[str] = None
    numero_identificacion: Optional[str] = None
    descripcion: Optional[str] = None
    categoria: Optional[str] = None
    cantidad_disponible: Optional[int] = None
    unidad_medida: Optional[str] = None
    ubicacion_almacen: Optional[str] = None
    estado_uso: Optional[str] = None
    imagen_ruta: Optional[str] = None
    costo_adquisicion: Optional[float] = None
    fecha_adquisicion: Optional[date_type] = None
    proveedor_ultimo: Optional[str] = None
    observaciones: Optional[str] = None
