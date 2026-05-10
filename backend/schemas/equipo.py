from typing import Optional
from datetime import date
from pydantic import BaseModel

# Esquema base (para no repetir código)
class EquipoBase(BaseModel):
    nombre_corto: Optional[str] = None
    modelo: str
    numero_serie: str
    marca: str
    fecha_adquisicion: date
    registro_sanitario_bolivia: Optional[str] = None # NUEVO
    ubicacion_actual: Optional[str] = None
    proveedor_principal: Optional[str] = None # NUEVO
    descripcion: Optional[str] = None # NUEVO
    # imagen_ruta: Optional[str] = None # Lo dejamos comentado por ahora
    calibracion_proxima: Optional[date] = None # NUEVO
    responsable_tecnico_id: Optional[int] = None # NUEVO
    estado_id: Optional[int] = 1

# Para CREAR (Hereda del base)
class EquipoCreate(EquipoBase):
    pass

# Para LEER (Respuesta al frontend) - Debe incluir el ID
class EquipoRead(EquipoBase):
    id: int

    class Config:
        from_attributes = True # (Antes orm_mode = True)

# Para ACTUALIZAR (Todos opcionales para poder editar solo lo que queramos)
class EquipoUpdate(BaseModel):
    nombre_corto: Optional[str] = None
    modelo: Optional[str] = None
    numero_serie: Optional[str] = None
    marca: Optional[str] = None
    fecha_adquisicion: Optional[date] = None
    registro_sanitario_bolivia: Optional[str] = None # NUEVO
    ubicacion_actual: Optional[str] = None
    proveedor_principal: Optional[str] = None # NUEVO
    descripcion: Optional[str] = None # NUEVO
    calibracion_proxima: Optional[date] = None # NUEVO
    responsable_tecnico_id: Optional[int] = None # NUEVO
    estado_id: Optional[int] = None
    