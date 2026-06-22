"""
Modelos Contrato y ContratoEquipo - RF12 v0.9.2
Gestión de contratos de mantenimiento y servicios con proveedores.
"""
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime


class Contrato(SQLModel, table=True):
    """
    Contrato de mantenimiento/servicio con un proveedor - RF12 v0.9.2.

    El campo 'activo' NO se guarda en BD, se calcula en runtime:
    activo = fecha_inicio <= hoy <= fecha_fin
    """
    __tablename__ = "contrato"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con proveedor (N:1)
    proveedor_id: int = Field(foreign_key="proveedor.id", index=True)

    # Tipo y vigencia
    tipo_contrato: str  # enum: Comodato, Mantenimiento Preventivo, Mantenimiento Correctivo, Leasing, Garantía Extendida, Soporte Técnico, Servicio Integral, Otro
    fecha_inicio: datetime  # NOT NULL
    fecha_fin: datetime     # NOT NULL

    # Costos
    costo_total: Optional[float] = None
    costo_periodico: Optional[float] = None
    periodicidad_costo: str = "Único"  # enum: Único, Mensual, Trimestral, Semestral, Anual
    moneda: str = "USD"  # enum: USD, EUR, BOB, MXN, ARS, CLP, COP, PEN, BRL, Otro

    # Detalles del servicio
    cobertura_detalle: Optional[str] = None
    tiempo_respuesta: Optional[str] = None  # ej: "24 hs", "48 hs"
    horario_servicio: Optional[str] = None  # ej: "Lun-Vie 8-18hs"

    # Notas y auditoría
    notas: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.now)


class ContratoEquipo(SQLModel, table=True):
    """
    Relación N:M entre Contrato y Equipo - RF12 v0.9.2.
    Un contrato puede cubrir 0, 1 o N equipos.
    Un equipo puede estar cubierto por 0, 1 o N contratos.
    """
    __tablename__ = "contrato_equipo"

    contrato_id: int = Field(foreign_key="contrato.id", primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id", primary_key=True)
