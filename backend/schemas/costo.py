"""
Schemas para OtCostoAdicional - RF11 v0.9.1
"""
from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, field_validator


TIPOS_COSTO_VALIDOS = {
    'Transporte', 'Servicio Externo', 'Repuesto No Inventariado',
    'Herramienta Renta', 'Honorarios / Mano de Obra',
    'Insumos / Materiales', 'Viáticos', 'Otro'
}


class OtCostoAdicionalCreate(BaseModel):
    orden_trabajo_id: int
    tipo_costo: str
    descripcion_costo: str
    monto_costo: float
    fecha_registro: Optional[date] = None
    subido_por: Optional[str] = None

    @field_validator('tipo_costo')
    @classmethod
    def validate_tipo_costo(cls, v):
        if v not in TIPOS_COSTO_VALIDOS:
            raise ValueError(f'tipo_costo debe ser uno de: {", ".join(sorted(TIPOS_COSTO_VALIDOS))}')
        return v

    @field_validator('monto_costo')
    @classmethod
    def validate_monto(cls, v):
        if v < 0:
            raise ValueError('monto_costo debe ser un número positivo')
        return v


class OtCostoAdicionalUpdate(BaseModel):
    tipo_costo: Optional[str] = None
    descripcion_costo: Optional[str] = None
    monto_costo: Optional[float] = None
    fecha_registro: Optional[date] = None

    @field_validator('tipo_costo')
    @classmethod
    def validate_tipo_costo(cls, v):
        if v is None or v == '':
            return v
        if v not in TIPOS_COSTO_VALIDOS:
            raise ValueError(f'tipo_costo debe ser uno de: {", ".join(sorted(TIPOS_COSTO_VALIDOS))}')
        return v


class OtCostoAdicionalRead(BaseModel):
    id: int
    orden_trabajo_id: int
    tipo_costo: str
    descripcion_costo: str
    monto_costo: float
    fecha_registro: Optional[date]
    fecha_creacion: datetime
    subido_por: Optional[str]

    class Config:
        from_attributes = True
