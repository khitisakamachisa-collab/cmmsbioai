from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from datetime import datetime, date, timedelta
from database import get_session
from models.ordenes import OrdenTrabajo, EstadoOT, BitacoraOT
from models.preventivo import TareaPreventiva, TareaRepuesto
from models.repuestos import Repuesto, OtRepuestoUtilizado
from models.costos import OtCostoAdicional
from models.historial import EventoHistorial
from models.users import Usuario
from schemas.orden_trabajo import (
    OrdenTrabajoCreate, OrdenTrabajoRead, OrdenTrabajoUpdate,
    AccionSimple, AccionAsignar, AccionComentario, AccionResolver,
    AccionReincidencia,
)

router = APIRouter(prefix="/ordenes", tags=["Ordenes de Trabajo"])

# ================================================================
# v1.1.0 — FLUJO DE TRABAJO OT (propuesta aprobada 03/10/2026)
# v1.1.1 — Cierre Definitivo y Reincidencias (prompt del usuario)
#
# Reglas implementadas en este archivo:
#   R1: toda OT nace "Abierta" (POST /ordenes/ fuerza el estado).
#   R2: solo transiciones válidas (máquina de estados abajo).
#   R3: resolver exige acciones_realizadas + tiempo_real_invertido.
#   R4: cada acción queda registrada en bitacora_ot.
#   R5: sellos de tiempo (asignación/inicio/resolución) se fijan
#       una sola vez y nunca se sobreescriben.
#   R6: el mecanismo preventivo NO cambia (nace Abierta igual;
#       una reincidencia NO revierte fechas de la tarea preventiva).
#   R7 (v1.1.1, sustituye a la re-apertura): una OT cerrada es
#       INMUTABLE. La re-intervención genera una OT NUEVA vinculada
#       vía /reincidencia (parent_ot_id + failure_sequence).
#   R8 (v1.1.1): el repuesto del almacén puede registrarse DENTRO
#       del flujo (reanudar/resolver) — se valida stock y se
#       descuenta en ese momento, con bitácora.
#
# H2: el PUT genérico ya NO modifica el estado (solo las acciones).
# H4: sellos de tiempo agregados al modelo (ver models/ordenes.py).
# H5: bitácora consultable en GET /ordenes/{id}/bitacora.
#
# Estados del catálogo (v1.1.1 agrega 'En Monitoreo'):
#   Abierta → En Proceso → Esp. Repuesto → Completada / Cancelada
#                        → En Monitoreo (reparado en observación)
# ================================================================

ESTADO_ABIERTA       = "Abierta"
ESTADO_EN_PROCESO    = "En Proceso"
ESTADO_ESP_REPUESTO  = "Esp. Repuesto"
ESTADO_EN_MONITOREO  = "En Monitoreo"   # v1.1.1: estado ACTIVO (no cerrado)
ESTADO_COMPLETADA    = "Completada"     # ≈ REPARADA del prompt
ESTADO_CANCELADA     = "Cancelada"      # ≈ NO_REPARADA / CERRADA del prompt

TRANSICIONES_VALIDAS = {
    ESTADO_ABIERTA:      {ESTADO_EN_PROCESO, ESTADO_CANCELADA},
    ESTADO_EN_PROCESO:   {ESTADO_ESP_REPUESTO, ESTADO_EN_MONITOREO, ESTADO_COMPLETADA, ESTADO_CANCELADA},
    ESTADO_ESP_REPUESTO: {ESTADO_EN_PROCESO, ESTADO_CANCELADA},
    ESTADO_EN_MONITOREO: {ESTADO_EN_PROCESO, ESTADO_COMPLETADA, ESTADO_CANCELADA},
    ESTADO_COMPLETADA:   set(),   # v1.1.1: inmutable — solo sale vía /reincidencia (OT nueva)
    ESTADO_CANCELADA:    set(),   # v1.1.1: inmutable — solo sale vía /reincidencia (OT nueva)
}

ESTADOS_CERRADOS = {ESTADO_COMPLETADA, ESTADO_CANCELADA}


# ----------------------------------------------------------------
# Helpers internos
# ----------------------------------------------------------------

def _get_ot(session: Session, ot_id: int) -> OrdenTrabajo:
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    return db_ot


def _get_estado(session: Session, nombre: str) -> EstadoOT:
    est = session.exec(select(EstadoOT).where(EstadoOT.nombre_estado == nombre)).first()
    if not est:
        raise HTTPException(status_code=500, detail=f"No se encontró el estado '{nombre}' en la BD")
    return est


def _nombre_estado(session: Session, estado_id: int) -> str:
    est = session.get(EstadoOT, estado_id)
    return est.nombre_estado if est else "?"


def _bitacora(session: Session, ot: OrdenTrabajo, accion: str, *,
              estado_anterior: Optional[str] = None, estado_nuevo: Optional[str] = None,
              comentario: Optional[str] = None, usuario: Optional[str] = None):
    """R4: registra una entrada en la bitácora de la OT."""
    session.add(BitacoraOT(
        orden_trabajo_id=ot.id,
        accion=accion,
        usuario=(usuario or "sistema"),
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        comentario=(comentario or None),
    ))


def _procesar_repuestos_costos(session: Session, ot: OrdenTrabajo,
                               repuestos: Optional[list], costos: Optional[list]) -> Optional[str]:
    """R8 (v1.1.1): registra repuestos del almacén y costos adicionales
    DENTRO del flujo (reanudar/resolver). Valida stock y descuenta en el
    momento, crea los registros y devuelve un resumen para la bitácora.
    - repuestos: [{repuesto_id, cantidad}]
    - costos:    [{tipo_costo, descripcion_costo, monto_costo}]"""
    partes: list[str] = []

    if repuestos:
        # v1.1.1: otrepuestoutilizado tiene PK compuesta (ot, repuesto) →
        # 1 sola fila por repuesto. Se AGREGAN cantidades (mismo payload
        # o filas ya existentes del flujo) en lugar de duplicar filas.
        agregado: dict[int, int] = {}
        orden_ids: list[int] = []
        for item in repuestos:
            rep_id = item.get("repuesto_id")
            cant = item.get("cantidad")
            if not rep_id or not cant or cant <= 0:
                continue
            if rep_id not in agregado:
                agregado[rep_id] = 0
                orden_ids.append(rep_id)
            agregado[rep_id] += cant

        for rep_id in orden_ids:
            cant = agregado[rep_id]
            db_rep = session.get(Repuesto, rep_id)
            if not db_rep:
                raise HTTPException(status_code=404, detail=f"Repuesto ID {rep_id} no encontrado")
            if db_rep.cantidad_disponible < cant:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuficiente de {db_rep.nombre_repuesto} "
                           f"(disponible: {db_rep.cantidad_disponible}, solicitado: {cant})"
                )
            db_rep.cantidad_disponible -= cant
            session.add(db_rep)
            uso = session.get(OtRepuestoUtilizado, (ot.id, rep_id))
            if uso:
                uso.cantidad_utilizada += cant
                session.add(uso)
            else:
                session.add(OtRepuestoUtilizado(
                    orden_trabajo_id=ot.id, repuesto_id=rep_id, cantidad_utilizada=cant
                ))
            partes.append(f"{db_rep.nombre_repuesto} x{cant}")

    if costos:
        for c in costos:
            monto = c.get("monto_costo")
            if not monto or monto <= 0:
                continue
            session.add(OtCostoAdicional(
                orden_trabajo_id=ot.id,
                tipo_costo=(c.get("tipo_costo") or "Otro"),
                descripcion_costo=(c.get("descripcion_costo") or ""),
                monto_costo=monto,
            ))
            partes.append(f"Costo {c.get('tipo_costo') or 'Otro'}: Bs {monto}")

    return ("Repuestos/Costos: " + "; ".join(partes)) if partes else None


def _orden_response(session: Session, db_ot: OrdenTrabajo) -> dict:
    session.refresh(db_ot)
    repuestos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == db_ot.id)
    ).all()
    data = db_ot.model_dump()
    data["repuestos_usados"] = [r.model_dump() for r in repuestos]
    return data


def _al_completar_ot(session: Session, db_ot: OrdenTrabajo):
    """Lógica que antes vivía en el PUT: al completarse una OT,
    actualiza la tarea preventiva de origen y registra el evento
    en el historial del equipo. (R6: el mecanismo preventivo no cambia.)"""
    # 1) Si la OT viene de preventivo, avanzar la tarea
    if db_ot.orden_preventiva_id:
        tarea = session.get(TareaPreventiva, db_ot.orden_preventiva_id)
        if tarea:
            hoy = date.today()
            tarea.ultima_fecha = hoy
            tarea.proxima_fecha = hoy + timedelta(days=tarea.frecuencia_dias)
            session.add(tarea)
            session.commit()

    # 2) Insertar evento en el historial automáticamente
    tipo_evento = "preventivo" if db_ot.orden_preventiva_id else "correctivo"

    repuestos_usados_txt = None
    repuestos_list = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == db_ot.id)
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


# ----------------------------------------------------------------
# Estados de OT (catálogo)
# ----------------------------------------------------------------

@router.post("/estados/", tags=["Estados OT"])
def crear_estado_ot(nombre: str, session: Session = Depends(get_session)):
    nuevo_estado = EstadoOT(nombre_estado=nombre)
    session.add(nuevo_estado)
    session.commit()
    session.refresh(nuevo_estado)
    return nuevo_estado


@router.get("/estados/", tags=["Estados OT"])
def listar_estados_ot(session: Session = Depends(get_session)):
    return session.exec(select(EstadoOT)).all()


# ----------------------------------------------------------------
# CREAR una OT — R1: nace SIEMPRE "Abierta"
# ----------------------------------------------------------------

@router.post("/", response_model=OrdenTrabajoRead)
def crear_orden(orden: OrdenTrabajoCreate, session: Session = Depends(get_session)):
    orden_dict = orden.model_dump()
    repuestos_recibidos = orden_dict.pop("repuestos_utilizados", None)

    # v0.9.23: fecha_creacion editable; si no viene, default_factory del modelo
    if orden_dict.get("fecha_creacion") is None:
        orden_dict.pop("fecha_creacion", None)

    # --- R1: toda OT nace "Abierta" ---
    estado_abierta = _get_estado(session, ESTADO_ABIERTA)
    estado_recibido = orden_dict.pop("estado_id", None)
    if estado_recibido is not None and estado_recibido != estado_abierta.id:
        raise HTTPException(
            status_code=400,
            detail="Regla R1: toda OT se crea en estado 'Abierta'. "
                   "Use las acciones del flujo (/asignar, /iniciar, ...) para avanzarla."
        )
    orden_dict["estado_id"] = estado_abierta.id

    db_orden = OrdenTrabajo(**orden_dict)
    session.add(db_orden)
    session.commit()
    session.refresh(db_orden)

    # v0.9.19: repuestos utilizados al crear (descuenta stock)
    if repuestos_recibidos:
        for item in repuestos_recibidos:
            rep_id = item.get('repuesto_id')
            cant = item.get('cantidad')
            if not rep_id or not cant:
                continue
            db_rep = session.get(Repuesto, rep_id)
            if not db_rep:
                raise HTTPException(status_code=404, detail=f"Repuesto ID {rep_id} no encontrado")
            if db_rep.cantidad_disponible < cant:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente de {db_rep.nombre_repuesto}")
            db_rep.cantidad_disponible -= cant
            session.add(db_rep)
            uso = OtRepuestoUtilizado(
                orden_trabajo_id=db_orden.id,
                repuesto_id=rep_id,
                cantidad_utilizada=cant
            )
            session.add(uso)
        session.commit()
        session.refresh(db_orden)

    # --- R5: asignación en la creación fija el sello fecha_asignacion ---
    if db_orden.tecnico_asignado_id:
        db_orden.fecha_asignacion = db_orden.fecha_creacion or datetime.now()
        session.add(db_orden)
        session.commit()
        session.refresh(db_orden)

    # --- R4: bitácora ---
    _bitacora(session, db_orden, "creada", estado_nuevo=ESTADO_ABIERTA,
              comentario="OT creada (nace Abierta — R1)")
    if db_orden.tecnico_asignado_id:
        _bitacora(session, db_orden, "asignada", estado_anterior=ESTADO_ABIERTA,
                  estado_nuevo=ESTADO_ABIERTA, comentario="Asignada en la creación")
    session.commit()

    return db_orden


# ----------------------------------------------------------------
# LISTAR / VER
# ----------------------------------------------------------------

@router.get("/", response_model=list[OrdenTrabajoRead])
def listar_ordenes(equipo_id: Optional[int] = None, session: Session = Depends(get_session)):
    if equipo_id:
        ordenes = session.exec(select(OrdenTrabajo).where(OrdenTrabajo.equipo_id == equipo_id)).all()
    else:
        ordenes = session.exec(select(OrdenTrabajo)).all()
    return ordenes


@router.get("/{ot_id}", response_model=OrdenTrabajoRead)
def obtener_orden(ot_id: int, session: Session = Depends(get_session)):
    db_ot = _get_ot(session, ot_id)
    repuestos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
    ).all()
    data = db_ot.model_dump()
    data["repuestos_usados"] = repuestos
    return data


# v1.1.0 (H5): bitácora de la OT, de la más reciente a la más antigua
@router.get("/{ot_id}/bitacora")
def bitacora_de_ot(ot_id: int, session: Session = Depends(get_session)):
    _get_ot(session, ot_id)
    entradas = session.exec(
        select(BitacoraOT)
        .where(BitacoraOT.orden_trabajo_id == ot_id)
        .order_by(BitacoraOT.fecha.desc(), BitacoraOT.id.desc())
    ).all()
    return [e.model_dump() for e in entradas]


# ----------------------------------------------------------------
# ACTUALIZAR (edición de contenido) — H2: SIN cambio de estado
# ----------------------------------------------------------------

@router.put("/{ot_id}", response_model=OrdenTrabajoRead)
def actualizar_orden(ot_id: int, ot_data: OrdenTrabajoUpdate,
                     usuario: Optional[str] = None,
                     session: Session = Depends(get_session)):
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    # H2: una OT cerrada es un registro de solo lectura
    if actual in ESTADOS_CERRADOS:
        raise HTTPException(
            status_code=400,
            detail=f"La OT está {actual}: es un registro de solo lectura. "
                   f"Use la acción /reincidencia para crear una nueva OT vinculada (regla R7) si necesita darle continuidad."
        )

    ot_data_dict = ot_data.model_dump(exclude_unset=True)
    repuestos_recibidos = ot_data_dict.pop("repuestos_utilizados", None)
    campos_editados = sorted(ot_data_dict.keys())

    for key, value in ot_data_dict.items():
        setattr(db_ot, key, value)

    # --- Lógica de stock (igual que v0.9.19) ---
    repuestos_previos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
    ).all()
    for rp in repuestos_previos:
        rep_previo = session.get(Repuesto, rp.repuesto_id)
        if rep_previo:
            rep_previo.cantidad_disponible += rp.cantidad_utilizada
            session.add(rep_previo)
        session.delete(rp)
    if repuestos_previos:
        session.flush()

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

    # R4: dejar constancia de la edición
    _bitacora(session, db_ot, "editada", estado_anterior=actual, estado_nuevo=actual,
              comentario=("Campos: " + ", ".join(campos_editados)) if campos_editados else None,
              usuario=usuario)

    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


# ----------------------------------------------------------------
# v1.1.0 — ACCIONES DEL FLUJO (endpoints)
# ----------------------------------------------------------------

@router.post("/{ot_id}/asignar", response_model=OrdenTrabajoRead)
def asignar_tecnico(ot_id: int, accion: AccionAsignar, session: Session = Depends(get_session)):
    """Asignar (o reasignar) técnico. Válido en Abierta / En Proceso / Esp. Repuesto.
    Fija fecha_asignacion solo la primera vez (R5)."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)
    if actual in ESTADOS_CERRADOS:
        raise HTTPException(status_code=400,
            detail=f"No se puede asignar una OT {actual}. Use la acción /reincidencia para crear una nueva OT vinculada (R7).")

    tecnico = session.get(Usuario, accion.tecnico_asignado_id)
    if not tecnico:
        raise HTTPException(status_code=404, detail=f"Usuario ID {accion.tecnico_asignado_id} no encontrado")

    db_ot.tecnico_asignado_id = accion.tecnico_asignado_id
    if db_ot.fecha_asignacion is None:  # R5: primera escritura inmutable
        db_ot.fecha_asignacion = datetime.now()

    _bitacora(session, db_ot, "asignada", estado_anterior=actual, estado_nuevo=actual,
              comentario=accion.comentario or f"Técnico: {tecnico.full_name or tecnico.username}",
              usuario=accion.usuario)
    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/iniciar", response_model=OrdenTrabajoRead)
def iniciar_trabajo(ot_id: int, accion: AccionSimple, session: Session = Depends(get_session)):
    """Abierta → En Proceso. Requiere técnico asignado.
    Fija fecha_inicio_trabajo solo la primera vez (R5)."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if actual != ESTADO_ABIERTA:
        raise HTTPException(status_code=400,
            detail=f"Transición inválida (R2): '{actual}' no puede pasar a '{ESTADO_EN_PROCESO}'. Válidas: {sorted(TRANSICIONES_VALIDAS[actual]) or 'ninguna'}")
    if not db_ot.tecnico_asignado_id:
        raise HTTPException(status_code=400,
            detail="No se puede iniciar el trabajo sin técnico asignado. Use /asignar primero.")

    db_ot.estado_id = _get_estado(session, ESTADO_EN_PROCESO).id
    if db_ot.fecha_inicio_trabajo is None:  # R5
        db_ot.fecha_inicio_trabajo = datetime.now()

    _bitacora(session, db_ot, "iniciada", estado_anterior=actual, estado_nuevo=ESTADO_EN_PROCESO,
              comentario=accion.comentario, usuario=accion.usuario)
    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/pausar", response_model=OrdenTrabajoRead)
def pausar_trabajo(ot_id: int, accion: AccionComentario, session: Session = Depends(get_session)):
    """En Proceso → Esp. Repuesto. Motivo obligatorio (p. ej. 'espera repuesto X').
    El intervalo pausa→reanudación alimenta el KPI 'tiempo en espera de repuestos'."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if ESTADO_ESP_REPUESTO not in TRANSICIONES_VALIDAS[actual]:
        raise HTTPException(status_code=400,
            detail=f"Transición inválida (R2): '{actual}' no puede pasar a '{ESTADO_ESP_REPUESTO}'.")
    if not accion.comentario or not accion.comentario.strip():
        raise HTTPException(status_code=400, detail="Debe indicar el motivo de la pausa (R7).")

    db_ot.estado_id = _get_estado(session, ESTADO_ESP_REPUESTO).id
    _bitacora(session, db_ot, "pausada", estado_anterior=actual, estado_nuevo=ESTADO_ESP_REPUESTO,
              comentario=accion.comentario, usuario=accion.usuario)
    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/reanudar", response_model=OrdenTrabajoRead)
def reanudar_trabajo(ot_id: int, accion: AccionSimple, session: Session = Depends(get_session)):
    """Esp. Repuesto → En Proceso (también En Monitoreo → En Proceso si recae).
    Cierra el intervalo de espera de repuestos.
    v1.1.1 (R8): puede recibir repuestos_utilizados (se descuentan del almacén
    aquí, forzando que existan en inventario) y costos_adicionales."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if actual not in (ESTADO_ESP_REPUESTO, ESTADO_EN_MONITOREO):
        raise HTTPException(status_code=400,
            detail=f"Transición inválida (R2): solo una OT '{ESTADO_ESP_REPUESTO}' o '{ESTADO_EN_MONITOREO}' puede reanudarse.")

    # R8: alta de repuestos/costos dentro del flujo (antes de cambiar estado,
    # para que un error de stock no deje la transición a medias)
    resumen_rc = _procesar_repuestos_costos(session, db_ot,
                                            accion.repuestos_utilizados,
                                            accion.costos_adicionales)

    db_ot.estado_id = _get_estado(session, ESTADO_EN_PROCESO).id
    comentario = accion.comentario
    if resumen_rc:
        comentario = f"{comentario} — {resumen_rc}" if comentario else resumen_rc
    _bitacora(session, db_ot, "reanudada", estado_anterior=actual, estado_nuevo=ESTADO_EN_PROCESO,
              comentario=comentario, usuario=accion.usuario)
    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/monitorear", response_model=OrdenTrabajoRead)
def monitorear_ot(ot_id: int, accion: AccionSimple, session: Session = Depends(get_session)):
    """v1.1.1: En Proceso → En Monitoreo. El equipo quedó reparado pero queda
    en observación antes del cierre definitivo. Estado ACTIVO: admite asignar,
    editar contenido y volver a En Proceso si recae."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if ESTADO_EN_MONITOREO not in TRANSICIONES_VALIDAS[actual]:
        raise HTTPException(status_code=400,
            detail=f"Transición inválida (R2): '{actual}' no puede pasar a '{ESTADO_EN_MONITOREO}'.")

    db_ot.estado_id = _get_estado(session, ESTADO_EN_MONITOREO).id
    _bitacora(session, db_ot, "monitoreo", estado_anterior=actual, estado_nuevo=ESTADO_EN_MONITOREO,
              comentario=accion.comentario or "Equipo reparado, en observación antes del cierre definitivo",
              usuario=accion.usuario)
    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/resolver", response_model=OrdenTrabajoRead)
def resolver_ot(ot_id: int, accion: AccionResolver, session: Session = Depends(get_session)):
    """En Proceso → Completada. Cierre con datos obligatorios (R3):
    acciones_realizadas + tiempo_real_invertido. Fija fecha_resolucion (R5).
    Dispara la lógica preventiva y de historial (R6)."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if ESTADO_COMPLETADA not in TRANSICIONES_VALIDAS[actual]:
        raise HTTPException(status_code=400,
            detail=f"Transición inválida (R2): '{actual}' no puede pasar a '{ESTADO_COMPLETADA}'. "
                   f"Válidas: {sorted(TRANSICIONES_VALIDAS[actual]) or 'ninguna'}")

    if not db_ot.tecnico_asignado_id:
        raise HTTPException(status_code=400,
            detail="No se puede resolver una OT sin técnico asignado. Use /asignar primero.")
    if not accion.acciones_realizadas or not accion.acciones_realizadas.strip():
        raise HTTPException(status_code=400, detail="R3: 'acciones_realizadas' (solución aplicada) es obligatorio.")
    if accion.tiempo_real_invertido is None or accion.tiempo_real_invertido <= 0:
        raise HTTPException(status_code=400, detail="R3: 'tiempo_real_invertido' debe ser mayor que 0.")
    if accion.unidad_tiempo not in ("horas", "dias"):
        raise HTTPException(status_code=400, detail="'unidad_tiempo' debe ser 'horas' o 'dias'.")

    # R8 (v1.1.1): alta de repuestos/costos al cierre (antes de cambiar estado,
    # para que un error de stock no deje la transición a medias)
    resumen_rc = _procesar_repuestos_costos(session, db_ot,
                                            accion.repuestos_utilizados,
                                            accion.costos_adicionales)

    db_ot.estado_id = _get_estado(session, ESTADO_COMPLETADA).id
    db_ot.acciones_realizadas = accion.acciones_realizadas
    db_ot.tiempo_real_invertido = accion.tiempo_real_invertido
    db_ot.unidad_tiempo = accion.unidad_tiempo
    if db_ot.fecha_resolucion is None:  # R5
        db_ot.fecha_resolucion = datetime.now()

    comentario = accion.comentario
    if resumen_rc:
        comentario = f"{comentario} — {resumen_rc}" if comentario else resumen_rc
    _bitacora(session, db_ot, "resuelta", estado_anterior=actual, estado_nuevo=ESTADO_COMPLETADA,
              comentario=comentario, usuario=accion.usuario)
    session.add(db_ot)
    session.commit()

    # R6: lógica preventiva + historial (antes vivía en el PUT)
    _al_completar_ot(session, db_ot)
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/cancelar", response_model=OrdenTrabajoRead)
def cancelar_ot(ot_id: int, accion: AccionComentario, session: Session = Depends(get_session)):
    """Abierta / En Proceso / Esp. Repuesto → Cancelada. Motivo obligatorio."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if ESTADO_CANCELADA not in TRANSICIONES_VALIDAS[actual]:
        raise HTTPException(status_code=400,
            detail=f"Transición inválida (R2): una OT '{actual}' no se cancela; ya está cerrada.")
    if not accion.comentario or not accion.comentario.strip():
        raise HTTPException(status_code=400, detail="Debe indicar el motivo de la cancelación (R7).")

    db_ot.estado_id = _get_estado(session, ESTADO_CANCELADA).id
    _bitacora(session, db_ot, "cancelada", estado_anterior=actual, estado_nuevo=ESTADO_CANCELADA,
              comentario=accion.comentario, usuario=accion.usuario)
    session.add(db_ot)
    session.commit()
    return _orden_response(session, db_ot)


@router.post("/{ot_id}/reincidencia", response_model=OrdenTrabajoRead)
def reincidencia_ot(ot_id: int, accion: AccionReincidencia, session: Session = Depends(get_session)):
    """v1.1.1 (R7 — sustituye a /reabrir, prompt 'Cierre Definitivo y
    Reapertura'): la OT cerrada es INMUTABLE. Si la misma falla vuelve a
    intervenirse, se crea una OT NUEVA (R1: nace Abierta) vinculada con
    parent_ot_id = esta OT y failure_sequence incrementada. Así cada OT
    individual conserva su inicio/cierre y MTBF/MTTR no se distorsionan.
    R6: NO hereda orden_preventiva_id (no doble-avanza la tarea preventiva)."""
    db_ot = _get_ot(session, ot_id)
    actual = _nombre_estado(session, db_ot.estado_id)

    if actual not in ESTADOS_CERRADOS:
        raise HTTPException(status_code=400,
            detail=f"Solo una OT {ESTADO_COMPLETADA} o {ESTADO_CANCELADA} genera reincidencia (actual: {actual}).")
    if not accion.comentario or not accion.comentario.strip():
        raise HTTPException(status_code=400,
            detail="Debe indicar el motivo de la reincidencia (qué volvió a fallar o por qué se interviene de nuevo).")

    nueva_secuencia = (db_ot.failure_sequence or 1) + 1

    nueva = OrdenTrabajo(
        equipo_id=db_ot.equipo_id,
        estado_id=_get_estado(session, ESTADO_ABIERTA).id,
        prioridad=db_ot.prioridad,
        tecnico_asignado_id=db_ot.tecnico_asignado_id,  # se hereda; puede reasignarse luego
        titulo=db_ot.titulo,
        descripcion_falla=(
            f"{db_ot.descripcion_falla}\n\n"
            f"[Reincidencia de OT #{db_ot.id} — secuencia {nueva_secuencia}] {accion.comentario.strip()}"
        ),
        parent_ot_id=db_ot.id,
        failure_sequence=nueva_secuencia,
    )
    session.add(nueva)
    session.commit()
    session.refresh(nueva)

    # R5: si hereda técnico, la asignación nace hecha
    if nueva.tecnico_asignado_id:
        nueva.fecha_asignacion = datetime.now()
        session.add(nueva)
        session.commit()
        session.refresh(nueva)

    # R4: constancia en ambas bitácoras
    _bitacora(session, nueva, "creada", estado_nuevo=ESTADO_ABIERTA,
              comentario=f"Reincidencia de OT #{db_ot.id} (secuencia {nueva_secuencia}): {accion.comentario.strip()}",
              usuario=accion.usuario)
    if nueva.tecnico_asignado_id:
        _bitacora(session, nueva, "asignada", estado_anterior=ESTADO_ABIERTA, estado_nuevo=ESTADO_ABIERTA,
                  comentario="Técnico heredado de la OT anterior", usuario=accion.usuario)
    _bitacora(session, db_ot, "reincidencia", estado_anterior=actual, estado_nuevo=actual,
              comentario=f"Generó OT #{nueva.id} (secuencia {nueva_secuencia}): {accion.comentario.strip()}",
              usuario=accion.usuario)
    session.commit()
    return nueva


# ----------------------------------------------------------------
# ELIMINAR (limpieza administrativa; la bitácora queda huérfana)
# ----------------------------------------------------------------

@router.delete("/{ot_id}")
def eliminar_orden(ot_id: int, session: Session = Depends(get_session)):
    db_ot = _get_ot(session, ot_id)
    session.delete(db_ot)
    session.commit()
    return {"ok": True, "message": "Orden eliminada"}
