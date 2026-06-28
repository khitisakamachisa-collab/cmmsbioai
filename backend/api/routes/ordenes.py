from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, date, timedelta
from database import get_session
from models.ordenes import OrdenTrabajo, EstadoOT
from models.preventivo import TareaPreventiva, TareaRepuesto
from models.repuestos import Repuesto, OtRepuestoUtilizado
from models.historial import EventoHistorial
from schemas.orden_trabajo import OrdenTrabajoCreate, OrdenTrabajoRead, OrdenTrabajoUpdate

router = APIRouter(prefix="/ordenes", tags=["Ordenes de Trabajo"])

# Endpoint para crear estados de OT
@router.post("/estados/", tags=["Estados OT"])
def crear_estado_ot(nombre: str, session: Session = Depends(get_session)):
    nuevo_estado = EstadoOT(nombre_estado=nombre)
    session.add(nuevo_estado)
    session.commit()
    session.refresh(nuevo_estado)
    return nuevo_estado

# Endpoint para listar estados de OT
@router.get("/estados/", tags=["Estados OT"])
def listar_estados_ot(session: Session = Depends(get_session)):
    return session.exec(select(EstadoOT)).all()

# Endpoint para CREAR una OT
@router.post("/", response_model=OrdenTrabajoRead)
def crear_orden(orden: OrdenTrabajoCreate, session: Session = Depends(get_session)):
    db_orden = OrdenTrabajo(**orden.model_dump())
    session.add(db_orden)
    session.commit()
    session.refresh(db_orden)
    return db_orden

# Endpoint para LISTAR OTs
@router.get("/", response_model=list[OrdenTrabajoRead])
def listar_ordenes(equipo_id: Optional[int] = None, session: Session = Depends(get_session)):
    if equipo_id:
        ordenes = session.exec(select(OrdenTrabajo).where(OrdenTrabajo.equipo_id == equipo_id)).all()
    else:
        ordenes = session.exec(select(OrdenTrabajo)).all()
    return ordenes

# --- Endpoint para VER UNA OT por ID ---
@router.get("/{ot_id}", response_model=OrdenTrabajoRead)
def obtener_orden(ot_id: int, session: Session = Depends(get_session)):
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    
    # Buscar repuestos utilizados
    repuestos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
    ).all()
    
    data = db_ot.model_dump()
    data["repuestos_usados"] = repuestos
    
    return data

# Endpoint para ACTUALIZAR (Cerrar) una OT con lógica de stock + actualización de preventivo
@router.put("/{ot_id}", response_model=OrdenTrabajoRead)
def actualizar_orden(ot_id: int, ot_data: OrdenTrabajoUpdate, session: Session = Depends(get_session)):
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    
    # Guardar estado anterior para detectar cierre
    estado_anterior_id = db_ot.estado_id
    
    ot_data_dict = ot_data.model_dump(exclude_unset=True)
    repuestos_recibidos = ot_data_dict.pop("repuestos_utilizados", None)
    
    # Actualizar campos simples
    for key, value in ot_data_dict.items():
        setattr(db_ot, key, value)
    
    # Lógica de Stock
    # 1) Revertir repuestos previamente registrados para esta OT (si los hay)
    repuestos_previos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
    ).all()
    for rp in repuestos_previos:
        # Devolver stock
        rep_previo = session.get(Repuesto, rp.repuesto_id)
        if rep_previo:
            rep_previo.cantidad_disponible += rp.cantidad_utilizada
            session.add(rep_previo)
        session.delete(rp)
    # Hacer flush para que los DELETE se apliquen antes de los INSERT
    if repuestos_previos:
        session.flush()

    # 2) Insertar los nuevos repuestos utilizados
    if repuestos_recibidos:
        for item in repuestos_recibidos:
            rep_id = item['repuesto_id']
            cant = item['cantidad']
            
            db_rep = session.get(Repuesto, rep_id)
            if not db_rep:
                raise HTTPException(status_code=404, detail=f"Repuesto ID {rep_id} no encontrado")
            
            if db_rep.cantidad_disponible < cant:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente de {db_rep.nombre_repuesto}")

            db_rep.cantidad_disponible -= cant
            session.add(db_rep)

            uso = OtRepuestoUtilizado(
                orden_trabajo_id=ot_id,
                repuesto_id=rep_id,
                cantidad_utilizada=cant
            )
            session.add(uso)
    
    session.add(db_ot)
    session.commit()
    
    # === LÓGICA AL COMPLETAR UNA OT ===
    # Verificar si el estado cambió a "Completada"
    estado_completada = session.exec(
        select(EstadoOT).where(EstadoOT.nombre_estado == "Completada")
    ).first()

    if estado_completada and db_ot.estado_id == estado_completada.id:
        # 1) Si la OT viene de preventivo, actualizar la tarea
        if db_ot.orden_preventiva_id:
            tarea = session.get(TareaPreventiva, db_ot.orden_preventiva_id)
            if tarea:
                hoy = date.today()
                tarea.ultima_fecha = hoy
                tarea.proxima_fecha = hoy + timedelta(days=tarea.frecuencia_dias)
                session.add(tarea)
                session.commit()

        # 2) Insertar evento en el historial automáticamente
        # Determinar tipo de evento
        tipo_evento = "preventivo" if db_ot.orden_preventiva_id else "correctivo"

        # Construir resumen de repuestos utilizados
        repuestos_usados_txt = None
        repuestos_list = session.exec(
            select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
        ).all()
        if repuestos_list:
            partes = []
            for ru in repuestos_list:
                rep = session.get(Repuesto, ru.repuesto_id)
                nombre = rep.nombre_repuesto if rep else f"Repuesto#{ru.repuesto_id}"
                partes.append(f"{nombre} (x{ru.cantidad_utilizada})")
            repuestos_usados_txt = ", ".join(partes)

        evento = EventoHistorial(
            equipo_id=db_ot.equipo_id,
            orden_trabajo_id=db_ot.id,
            tipo_evento=tipo_evento,
            descripcion=db_ot.titulo,
            tecnico_id=db_ot.tecnico_asignado_id,
            fecha_evento=datetime.now(),
            acciones_realizadas=db_ot.acciones_realizadas,
            tiempo_invertido=db_ot.tiempo_real_invertido,
            costo=db_ot.costo_adicional,
            repuestos_utilizados=repuestos_usados_txt
        )
        session.add(evento)
        session.commit()
    
    # Refresh DESPUÉS de todos los commits para que model_dump() tenga todos los datos
    session.refresh(db_ot)
    
    # Preparar respuesta con repuestos
    repuestos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
    ).all()
    
    data = db_ot.model_dump()
    data["repuestos_usados"] = [r.model_dump() for r in repuestos]
    return data

# Endpoint para ELIMINAR
@router.delete("/{ot_id}")
def eliminar_orden(ot_id: int, session: Session = Depends(get_session)):
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    session.delete(db_ot)
    session.commit()
    return {"ok": True, "message": "Orden eliminada"}
