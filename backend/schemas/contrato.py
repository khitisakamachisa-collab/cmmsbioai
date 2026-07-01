"""
Schemas para Contrato y ContratoEquipo - RF12 v0.9.2
"""
from typing import Optional, List, Any
from pydantic import BaseModel, field_validator
from datetime import datetime, date

TIPOS_CONTRATO = {
    'Comodato', 'Mantenimiento Preventivo', 'Mantenimiento Correctivo',
    'Leasing', 'Garantía Extendida', 'Soporte Técnico', 'Servicio Integral', 'Otro'
}
PERIODICIDADES = {'Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual'}
MONEDAS = {'BOB'}  # v0.9.15: solo Bolivianos para todo el proyecto


class ContratoCreate(BaseModel):
    proveedor_id: int
    tipo_contrato: str
    fecha_inicio: date
    fecha_fin: date
    costo_total: Optional[float] = None
    costo_periodico: Optional[float] = None
    periodicidad_costo: str = "Único"
    moneda: str = "BOB"  # v0.9.15: solo BOB
    cobertura_detalle: Optional[str] = None
    tiempo_respuesta: Optional[str] = None
    horario_servicio: Optional[str] = None
    notas: Optional[str] = None
    equipos_ids: Optional[List[int]] = None

    @field_validator('tipo_contrato')
    @classmethod
    def validate_tipo(cls, v):
        if v not in TIPOS_CONTRATO:
            raise ValueError(f'tipo_contrato debe ser uno de: {", ".join(sorted(TIPOS_CONTRATO))}')
        return v

    @field_validator('periodicidad_costo')
    @classmethod
    def validate_periodicidad(cls, v):
        if v not in PERIODICIDADES:
            raise ValueError(f'periodicidad_costo debe ser uno de: {", ".join(sorted(PERIODICIDADES))}')
        return v

    @field_validator('moneda')
    @classmethod
    def validate_moneda(cls, v):
        if v not in MONEDAS:
            raise ValueError(f'moneda debe ser uno de: {", ".join(sorted(MONEDAS))}')
        return v


class ContratoUpdate(BaseModel):
    tipo_contrato: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    costo_total: Optional[float] = None
    costo_periodico: Optional[float] = None
    periodicidad_costo: Optional[str] = None
    moneda: Optional[str] = None
    cobertura_detalle: Optional[str] = None
    tiempo_respuesta: Optional[str] = None
    horario_servicio: Optional[str] = None
    notas: Optional[str] = None
    equipos_ids: Optional[List[int]] = None

    @field_validator('tipo_contrato')
    @classmethod
    def validate_tipo(cls, v):
        if v is None or v == '':
            return v
        if v not in TIPOS_CONTRATO:
            raise ValueError(f'tipo_contrato debe ser uno de: {", ".join(sorted(TIPOS_CONTRATO))}')
        return v

    @field_validator('periodicidad_costo')
    @classmethod
    def validate_periodicidad(cls, v):
        if v is None or v == '':
            return v
        if v not in PERIODICIDADES:
            raise ValueError(f'periodicidad_costo debe ser uno de: {", ".join(sorted(PERIODICIDADES))}')
        return v

    @field_validator('moneda')
    @classmethod
    def validate_moneda(cls, v):
        if v is None or v == '':
            return v
        if v not in MONEDAS:
            raise ValueError(f'moneda debe ser uno de: {", ".join(sorted(MONEDAS))}')
        return v


class ContratoRead(BaseModel):
    id: int
    proveedor_id: int
    tipo_contrato: str
    fecha_inicio: date
    fecha_fin: date
    costo_total: Optional[float]
    costo_periodico: Optional[float]
    periodicidad_costo: str
    moneda: str
    cobertura_detalle: Optional[str]
    tiempo_respuesta: Optional[str]
    horario_servicio: Optional[str]
    notas: Optional[str]
    fecha_creacion: datetime
    activo: Optional[bool] = None
    dias_restantes: Optional[int] = None
    equipos: Optional[List[Any]] = None
    proveedor_nombre: Optional[str] = None

    class Config:
        from_attributes = True
