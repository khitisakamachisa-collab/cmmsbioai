from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import timedelta, date
from database import get_session
from models.preventivo import TareaPreventiva, TareaRepuesto
from models.ordenes import OrdenTrabajo, EstadoOT
from schemas.preventivo import TareaPreventivaCreate, TareaPreventivaRead, TareaPreventivaUpdate
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/preventivo", tags=["Mantenimiento Preventivo"])

# --- Helper para obtener detalles de repuestos ---
def get_repuestos_detalle(session, tarea_id):
    return session.exec(
        select(TareaRepuesto).where(TareaRepuesto.tarea_preventiva_id == tarea_id)
    ).all()

# --- Endpoint para LISTAR tareas ---
@router.get("/", response_model=list[TareaPreventivaRead])
def listar_tareas(session: Session = Depends(get_session)):
    tareas = session.exec(select(TareaPreventiva)).all()
    resultados = []
    for t in tareas:
        tarea_dict = t.model_dump()
        tarea_dict["repuestos_detalle"] = get_repuestos_detalle(session, t.id)
        resultados.append(tarea_dict)
    return resultados

# --- Endpoint para CREAR tarea ---
@router.post("/", response_model=TareaPreventivaRead)
def crear_tarea(tarea: TareaPreventivaCreate, session: Session = Depends(get_session)):
    """
    v0.9.0: `proxima_fecha` es la fecha REAL programada por el usuario.
    NO se calcula automáticamente. El frontend puede sugerir
    `ultima_fecha + frecuencia_dias`, pero el usuario puede modificarla.

    `frecuencia_dias` es solo una sugerencia/recordatorio, no afecta la fecha del calendario.
    """
    # Crear Tarea con los datos del usuario (incluyendo proxima_fecha si viene)
    nueva_tarea = TareaPreventiva(
        **tarea.model_dump(exclude={"repuestos"})
    )
    session.add(nueva_tarea)
    session.commit()
    session.refresh(nueva_tarea)

    # Guardar Repuestos
    if tarea.repuestos:
        for rep in tarea.repuestos:
            nuevo_rep = TareaRepuesto(
                tarea_preventiva_id=nueva_tarea.id,
                repuesto_id=rep.repuesto_id,
                cantidad_requerida=rep.cantidad_requerida
            )
            session.add(nuevo_rep)
        session.commit()

    session.refresh(nueva_tarea)

    res = nueva_tarea.model_dump()
    repuestos_db = get_repuestos_detalle(session, nueva_tarea.id)
    res["repuestos_detalle"] = [r.model_dump() for r in repuestos_db]
    return res

# --- Endpoint para VER DETALLE ---
@router.get("/{tarea_id}", response_model=TareaPreventivaRead)
def obtener_tarea(tarea_id: int, session: Session = Depends(get_session)):
    db_tarea = session.get(TareaPreventiva, tarea_id)
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    res = db_tarea.model_dump()
    res["repuestos_detalle"] = get_repuestos_detalle(session, tarea_id)
    return res

# --- NUEVO: Endpoint para GENERAR OT desde una tarea preventiva ---
class GenerarOTRequest(BaseModel):
    """Schema para generar OT desde preventivo"""
    prioridad: str = "Media"
    tecnico_asignado_id: Optional[int] = None
    fecha_vencimiento: Optional[date] = None

@router.post("/{tarea_id}/generar-ot")
def generar_ot_desde_preventivo(tarea_id: int, req: GenerarOTRequest, session: Session = Depends(get_session)):
    """
    Genera una Orden de Trabajo a partir de una tarea preventiva.
    - Copia equipo_id, responsable como técnico asignado
    - Vincula la OT con la tarea via orden_preventiva_id
    - Pre-llena los repuestos del kit en la OT
    """
    # 1. Obtener la tarea preventiva
    tarea = session.get(TareaPreventiva, tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea preventiva no encontrada")
    
    # 2. Verificar que no exista ya una OT abierta para esta tarea
    estado_abierta = session.exec(
        select(EstadoOT).where(EstadoOT.nombre_estado == "Abierta")
    ).first()
    estado_en_proceso = session.exec(
        select(EstadoOT).where(EstadoOT.nombre_estado == "En Proceso")
    ).first()
    
    estados_abiertos = set()
    if estado_abierta:
        estados_abiertos.add(estado_abierta.id)
    if estado_en_proceso:
        estados_abiertos.add(estado_en_proceso.id)
    
    ot_existente = session.exec(
        select(OrdenTrabajo).where(
            OrdenTrabajo.orden_preventiva_id == tarea_id,
            OrdenTrabajo.estado_id.in_(estados_abiertos)
        )
    ).first()
    
    if ot_existente:
        raise HTTPException(
            status_code=400, 
            detail=f"Ya existe una OT abierta (#{ot_existente.id}) para esta tarea preventiva"
        )
    
    # 3. Crear la OT
    tecnico_id = req.tecnico_asignado_id or tarea.responsable_id
    
    if not estado_abierta:
        raise HTTPException(status_code=500, detail="No se encontró el estado 'Abierta' en la BD")
    
    nueva_ot = OrdenTrabajo(
        equipo_id=tarea.equipo_id,
        estado_id=estado_abierta.id,
        prioridad=req.prioridad,
        tecnico_asignado_id=tecnico_id,
        titulo=f"[Preventivo] {tarea.titulo}",
        descripcion_falla=f"Orden generada automáticamente desde tarea preventiva #{tarea_id}: {tarea.titulo}",
        fecha_vencimiento=req.fecha_vencimiento or tarea.proxima_fecha,
        orden_preventiva_id=tarea_id
    )
    session.add(nueva_ot)
    session.commit()
    session.refresh(nueva_ot)
    
    # 4. Copiar repuestos del kit a la OT (pre-llenar como sugerencia)
    repuestos_kit = get_repuestos_detalle(session, tarea_id)
    repuestos_copiados = []
    for rp in repuestos_kit:
        repuestos_copiados.append({
            "repuesto_id": rp.repuesto_id,
            "cantidad": rp.cantidad_requerida,
            "nombre": session.get(rp.repuesto_id.__class__, rp.repuesto_id) if False else None
        })
    
    # Devolver la OT creada + info de repuestos del kit
    resultado = nueva_ot.model_dump()
    resultado["repuestos_kit"] = [
        {"repuesto_id": r.repuesto_id, "cantidad_requerida": r.cantidad_requerida}
        for r in repuestos_kit
    ]
    
    return resultado

# --- Endpoint para ACTUALIZAR tarea ---
@router.put("/{tarea_id}", response_model=TareaPreventivaRead)
def actualizar_tarea(tarea_id: int, tarea_data: TareaPreventivaUpdate, session: Session = Depends(get_session)):
    """
    v0.9.0: NO se recalcula `proxima_fecha` automáticamente.
    El usuario setea `proxima_fecha` directamente con el date picker.
    `frecuencia_dias` es solo recordatorio, no afecta la fecha del calendario.
    """
    db_tarea = session.get(TareaPreventiva, tarea_id)
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    tarea_dict = tarea_data.model_dump(exclude_unset=True)

    # Actualizar campos simples (incluyendo proxima_fecha si viene)
    for key, value in tarea_dict.items():
        if key != "repuestos":
            setattr(db_tarea, key, value)

    # NO recalculamos proxima_fecha: el usuario es quien decide la fecha real

    session.add(db_tarea)

    # Actualizar Repuestos
    if "repuestos" in tarea_dict:
        session.exec(
            TareaRepuesto.__table__.delete().where(TareaRepuesto.tarea_preventiva_id == tarea_id)
        )
        for rep in tarea_dict["repuestos"]:
            nuevo = TareaRepuesto(
                tarea_preventiva_id=tarea_id,
                repuesto_id=rep["repuesto_id"],
                cantidad_requerida=rep["cantidad_requerida"]
            )
            session.add(nuevo)

    session.commit()
    session.refresh(db_tarea)

    res = db_tarea.model_dump()
    res["repuestos_detalle"] = get_repuestos_detalle(session, tarea_id)
    return res

# --- Endpoint para ELIMINAR ---
@router.delete("/{tarea_id}")
def eliminar_tarea(tarea_id: int, session: Session = Depends(get_session)):
    tarea = session.get(TareaPreventiva, tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    session.delete(tarea)
    session.commit()
    return {"ok": True}
