from fastapi import APIRouter, Depends
from sqlmodel import Session, select, func
from database import get_session
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo
from models.repuestos import Repuesto
from models.estados import EstadoEquipo, EstadoOT  # Importa ambos modelos de estados

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/metrics")
def get_dashboard_metrics(session: Session = Depends(get_session)):
    """
    Endpoint para obtener métricas globales del Dashboard.
    Retorna:
    - total_equipos: Total de equipos registrados.
    - equipos_operativos: Equipos en estado "Operativo".
    - equipos_no_operativos: Equipos NO en estado "Operativo".
    - ot_pendientes: Órdenes de trabajo en estado "Pendiente".
    - ot_en_progreso: Órdenes de trabajo en estado "En Progreso".
    - ot_completadas: Órdenes de trabajo en estado "Completada".
    - repuestos_criticos: Repuestos con stock < 5.
    """
    # Métricas de equipos
    total_equipos = session.exec(select(func.count(Equipo.id))).one()

    # Obtener el ID del estado "Operativo" para equipos
    estado_operativo = session.exec(
        select(EstadoEquipo.id).where(EstadoEquipo.nombre_estado == "Operativo")
    ).first()

    equipos_operativos = session.exec(
        select(func.count(Equipo.id)).where(Equipo.estado_id == estado_operativo.id)
    ).one() if estado_operativo else 0

    equipos_no_operativos = total_equipos - equipos_operativos

    # Obtener IDs de estados de OT dinámicamente
    estado_pendiente = session.exec(
        select(EstadoOT.id).where(EstadoOT.nombre_estado == "Pendiente")
    ).first()
    estado_en_progreso = session.exec(
        select(EstadoOT.id).where(EstadoOT.nombre_estado == "En Progreso")
    ).first()
    estado_completada = session.exec(
        select(EstadoOT.id).where(EstadoOT.nombre_estado == "Completada")
    ).first()

    # Métricas de órdenes de trabajo
    ot_pendientes = session.exec(
        select(func.count(OrdenTrabajo.id)).where(OrdenTrabajo.estado_id == estado_pendiente.id)
    ).one() if estado_pendiente else 0

    ot_en_progreso = session.exec(
        select(func.count(OrdenTrabajo.id)).where(OrdenTrabajo.estado_id == estado_en_progreso.id)
    ).one() if estado_en_progreso else 0

    ot_completadas = session.exec(
        select(func.count(OrdenTrabajo.id)).where(OrdenTrabajo.estado_id == estado_completada.id)
    ).one() if estado_completada else 0

    # Métricas de inventario (repuestos críticos: stock < 5)
    repuestos_criticos = session.exec(
        select(func.count(Repuesto.id)).where(Repuesto.cantidad_disponible < 5)
    ).one()

    return {
        "total_equipos": total_equipos,
        "equipos_operativos": equipos_operativos,
        "equipos_no_operativos": equipos_no_operativos,
        "ot_pendientes": ot_pendientes,
        "ot_en_progreso": ot_en_progreso,
        "ot_completadas": ot_completadas,
        "repuestos_criticos": repuestos_criticos
    }