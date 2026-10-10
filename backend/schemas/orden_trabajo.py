from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, date

# Esquema base
class OrdenTrabajoBase(BaseModel):
    equipo_id: int
    # v1.1.0 (R1): estado_id opcional — el backend fuerza SIEMPRE nacimiento en "Abierta".
    # Si el cliente envía un estado distinto, se rechaza con 400.
    estado_id: Optional[int] = None
    prioridad: str = "Media"
    tecnico_asignado_id: Optional[int] = None
    titulo: str
    descripcion_falla: str
    fecha_vencimiento: Optional[date] = None
    orden_preventiva_id: Optional[int] = None
    
    # Campos de cierre
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    unidad_tiempo: Optional[str] = "horas"  # "horas" o "dias"

# Esquema para Crear
class OrdenTrabajoCreate(OrdenTrabajoBase):
    # v0.9.23: fecha_creacion editable (datetime completo: fecha + hora)
    fecha_creacion: Optional[datetime] = None
    # v0.9.19: permitir recibir repuestos_utilizados al crear la OT
    repuestos_utilizados: Optional[List[dict]] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None

# Esquema para Leer (Respuesta)
class OrdenTrabajoRead(OrdenTrabajoBase):
    id: int
    fecha_creacion: Optional[datetime] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None
    repuestos_usados: Optional[List] = None
    # v1.1.0: sellos de tiempo del flujo (R5)
    fecha_asignacion: Optional[datetime] = None
    fecha_inicio_trabajo: Optional[datetime] = None
    fecha_resolucion: Optional[datetime] = None
    # v1.1.1 (prompt "Cierre Definitivo y Reapertura"): cadena de reincidencias
    parent_ot_id: Optional[int] = None
    failure_sequence: Optional[int] = 1
    class Config:
        from_attributes = True

# Esquema para Actualizar (Permite editar todo)
# v1.1.0 (H2): estado_id YA NO es editable por PUT genérico.
# El estado solo cambia mediante las acciones del flujo:
#   /asignar /iniciar /pausar /reanudar /resolver /cancelar
# extra="forbid" → si un cliente envía estado_id, responde 422 explícito.
# v1.1.1 FIX 422: se declara equipo_id — el modal Editar del frontend lo envía
# siempre; al no estar declarado, TODO guardado del lápiz respondía 422.
class OrdenTrabajoUpdate(BaseModel):
    model_config = {"extra": "forbid"}

    equipo_id: Optional[int] = None
    prioridad: Optional[str] = None
    tecnico_asignado_id: Optional[int] = None
    titulo: Optional[str] = None
    descripcion_falla: Optional[str] = None
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    unidad_tiempo: Optional[str] = None
    fecha_vencimiento: Optional[date] = None
    # v0.9.23: fecha_creacion editable (datetime completo: fecha + hora)
    fecha_creacion: Optional[datetime] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None
    repuestos_utilizados: Optional[List[dict]] = None


# ============================================================
# v1.1.0 — Esquemas de las ACCIONES del flujo OT
# usuario: quien ejecuta (username del token/localStorage).
# Pendiente H7 (v1.2): tomarlo del JWT con autorización por rol.
# ============================================================

class AccionSimple(BaseModel):
    """Iniciar / Reanudar — sin datos obligatorios.
    (v2.1.3: /monitorear eliminado junto con el estado 'En Monitoreo'.)
    v1.1.1: reanudar/resolver pueden recibir repuestos y costos para
    registrarlos DENTRO del flujo (el repuesto se descuenta del almacén
    en ese momento y queda en bitácora)."""
    comentario: Optional[str] = None
    usuario: Optional[str] = None
    repuestos_utilizados: Optional[List[dict]] = None   # [{repuesto_id, cantidad}]
    costos_adicionales: Optional[List[dict]] = None     # [{tipo_costo, descripcion_costo, monto_costo}]

class AccionAsignar(BaseModel):
    tecnico_asignado_id: int
    comentario: Optional[str] = None
    usuario: Optional[str] = None

class AccionComentario(BaseModel):
    """Pausar / Cancelar — motivo obligatorio (R7)."""
    comentario: str
    usuario: Optional[str] = None

class AccionResolver(BaseModel):
    """Resolver y completar — cierre con datos obligatorios (R3)."""
    acciones_realizadas: str
    tiempo_real_invertido: float
    unidad_tiempo: Optional[str] = "horas"  # "horas" | "dias"
    comentario: Optional[str] = None
    usuario: Optional[str] = None
    repuestos_utilizados: Optional[List[dict]] = None   # v1.1.1: alta con descuento de stock
    costos_adicionales: Optional[List[dict]] = None     # v1.1.1: costos desde el flujo

# v1.1.1 (prompt "Cierre Definitivo y Reapertura"): sustituye a /reabrir.
# La OT cerrada es inmutable; la re-intervención genera una OT NUEVA vinculada.
class AccionReincidencia(BaseModel):
    """Generar OT de reincidencia desde una OT cerrada.
    motivo: qué volvió a fallar / por qué se interviene de nuevo (obligatorio)."""
    comentario: str
    usuario: Optional[str] = None