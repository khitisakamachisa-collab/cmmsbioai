"""
Modelo OtCostoAdicional - RF11 v0.9.1
Tabla para registrar múltiples costos individuales asociados a una Orden de Trabajo.
Reemplaza los campos `costo_adicional` y `costos_adicionales` de OrdenTrabajo.
"""
from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import date, datetime


class OtCostoAdicional(SQLModel, table=True):
    """
    Costo adicional asociado a una Orden de Trabajo - RF11 v0.9.1.
    Permite registrar múltiples costos con descripción, monto, tipo y fecha.
    Los documentos justificativos (facturas, recibos) se asocian vía
    DocumentoAdjunto con ot_costo_id.
    """
    __tablename__ = "otcostoadicional"

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_trabajo_id: int = Field(foreign_key="ordentrabajo.id", index=True)

    # Datos del costo
    tipo_costo: str              # enum: Transporte, Servicio Externo, Repuesto No Inv., etc.
    descripcion_costo: str       # qué se compró/pagó (ej: "Transporte al hospital remoto")
    monto_costo: float           # monto del costo

    # Fechas
    fecha_registro: Optional[date] = None    # fecha del costo (default = hoy)
    fecha_creacion: datetime = Field(default_factory=datetime.now)  # auditoría

    # Auditoría
    subido_por: Optional[str] = None         # username del usuario que registró el costo
