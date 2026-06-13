from typing import Optional
from datetime import date as date_type
from sqlmodel import Field, SQLModel


class Herramienta(SQLModel, table=True):
    """
    Inventario de Herramientas y Materiales de Trabajo del taller biomédico.
    
    Diferenciado de Repuestos: las herramientas NO se consumen en una OT,
    solo cambia su estado_uso. Su costo se contabiliza como costo operativo
    del departamento, no como costo de mantenimiento de un equipo individual.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_herramienta: str
    numero_identificacion: Optional[str] = Field(default=None, unique=True)
    descripcion: Optional[str] = None
    categoria: str = Field(default="Herramienta Manual")  # Instrumento de Medición / Herramienta Manual / Consumible / Kit
    cantidad_disponible: int = Field(default=1)
    unidad_medida: str = Field(default="unidad")
    ubicacion_almacen: Optional[str] = None
    estado_uso: str = Field(default="Disponible")  # Disponible / En Uso / En Reparación / Dado de Baja
    imagen_ruta: Optional[str] = None
    costo_adquisicion: Optional[float] = None
    fecha_adquisicion: Optional[date_type] = None
    proveedor_ultimo: Optional[str] = None
    observaciones: Optional[str] = None
