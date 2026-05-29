from typing import Optional
from datetime import date
from pydantic import BaseModel

# Esquema base (para no repetir código)
class EquipoBase(BaseModel):
    nombre_corto: Optional[str] = None
    modelo: str
    numero_serie: str
    numero_material: Optional[str] = None  # Número de material (variante del modelo)
    marca: str
    fecha_adquisicion: date
    fecha_fin_garantia: Optional[date] = None  # Fecha fin de garantía
    registro_sanitario_bolivia: Optional[str] = None
    ubicacion_actual: Optional[str] = None
    proveedor_principal: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_ruta: Optional[str] = None
    calibracion_proxima: Optional[date] = None
    responsable_tecnico_id: Optional[int] = None
    estado_id: Optional[int] = 1

# Para CREAR (Hereda del base)
class EquipoCreate(EquipoBase):
    pass

# Para LEER (Respuesta al frontend) - Debe incluir el ID
class EquipoRead(EquipoBase):
    id: int

    class Config:
        from_attributes = True

# Para ACTUALIZAR (Todos opcionales para poder editar solo lo que queramos)
class EquipoUpdate(BaseModel):
    nombre_corto: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    numero_material: Optional[str] = None
    marca: Optional[str] = None
    fecha_adquisicion: Optional[date] = None
    fecha_fin_garantia: Optional[date] = None
    registro_sanitario_bolivia: Optional[str] = None
    ubicacion_actual: Optional[str] = None
    proveedor_principal: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_ruta: Optional[str] = None
    calibracion_proxima: Optional[date] = None
    responsable_tecnico_id: Optional[int] = None
    estado_id: Optional[int] = None
