from typing import Optional
from datetime import date
from pydantic import BaseModel, field_validator


# Esquema base (para no repetir código) - RF01 v0.9.0
class EquipoBase(BaseModel):
    # Identificación (todos obligatorios excepto numero_material)
    nombre_corto: str                                          # NOT NULL (era opcional)
    modelo: str
    numero_serie: str
    numero_material: Optional[str] = None
    marca: str

    # Fechas
    fecha_adquisicion: Optional[date] = None                   # Opcional (era obligatorio)
    fecha_inicio_garantia: Optional[date] = None               # NUEVO
    fecha_fin_garantia: Optional[date] = None

    # Ubicación y estado
    ubicacion_actual: Optional[str] = None
    estado_id: Optional[int] = 1

    # Proveedor (FK en vez de texto libre)
    proveedor_principal_id: Optional[int] = None               # NUEVO

    # Origen
    condicion_origen: Optional[str] = None                     # NUEVO (enum)

    # Descripción
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None                        # NUEVO

    # Imagen
    imagen_ruta: Optional[str] = None

    @field_validator('condicion_origen')
    @classmethod
    def validate_condicion_origen(cls, v):
        """Valida que condicion_origen sea uno de los 9 valores permitidos."""
        if v is None or v == '':
            return v
        valores_validos = {
            'Compra', 'Donación', 'Préstamo', 'Demostración', 'Evaluación',
            'Leasing', 'Renta', 'Comodato', 'Otro'
        }
        if v not in valores_validos:
            raise ValueError(
                f'condicion_origen debe ser uno de: {", ".join(sorted(valores_validos))}'
            )
        return v

    @field_validator('fecha_fin_garantia')
    @classmethod
    def validate_fechas_garantia(cls, v, info):
        """Valida que fecha_fin_garantia >= fecha_inicio_garantia si ambas están seteadas."""
        if v is None:
            return v
        inicio = info.data.get('fecha_inicio_garantia') if info.data else None
        if inicio and v < inicio:
            raise ValueError(
                'fecha_fin_garantia debe ser mayor o igual a fecha_inicio_garantia'
            )
        return v


# Para CREAR (Hereda del base)
class EquipoCreate(EquipoBase):
    pass


# Para LEER (Respuesta al frontend) - Debe incluir el ID
class EquipoRead(EquipoBase):
    id: int

    class Config:
        from_attributes = True


# Para ACTUALIZAR (Todos opcionales para poder editar solo lo que queramos)
# NOTA: modelo, marca, numero_serie NO se incluyen aquí porque NO son editables
#        después de creado el equipo. El endpoint PUT debe rechazar cambios en estos campos.
class EquipoUpdate(BaseModel):
    nombre_corto: Optional[str] = None
    numero_material: Optional[str] = None
    fecha_adquisicion: Optional[date] = None
    fecha_inicio_garantia: Optional[date] = None
    fecha_fin_garantia: Optional[date] = None
    ubicacion_actual: Optional[str] = None
    estado_id: Optional[int] = None
    proveedor_principal_id: Optional[int] = None
    condicion_origen: Optional[str] = None
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None
    imagen_ruta: Optional[str] = None

    @field_validator('condicion_origen')
    @classmethod
    def validate_condicion_origen(cls, v):
        """Valida que condicion_origen sea uno de los 9 valores permitidos."""
        if v is None or v == '':
            return v
        valores_validos = {
            'Compra', 'Donación', 'Préstamo', 'Demostración', 'Evaluación',
            'Leasing', 'Renta', 'Comodato', 'Otro'
        }
        if v not in valores_validos:
            raise ValueError(
                f'condicion_origen debe ser uno de: {", ".join(sorted(valores_validos))}'
            )
        return v
