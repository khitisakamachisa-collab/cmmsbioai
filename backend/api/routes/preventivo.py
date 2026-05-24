from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import timedelta
from database import get_session
from models.preventivo import TareaPreventiva, TareaRepuesto
from schemas.preventivo import TareaPreventivaCreate, TareaPreventivaRead, TareaPreventivaUpdate

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
        # Convertimos a diccionario
        tarea_dict = t.model_dump()
        # Agregamos los detalles de repuestos
        tarea_dict["repuestos_detalle"] = get_repuestos_detalle(session, t.id)
        resultados.append(tarea_dict)
    return resultados

# --- Endpoint para CREAR tarea ---
@router.post("/", response_model=TareaPreventivaRead)
def crear_tarea(tarea: TareaPreventivaCreate, session: Session = Depends(get_session)):
    # 1. Calcular próxima fecha
    proxima_fecha = None
    if tarea.ultima_fecha:
        proxima_fecha = tarea.ultima_fecha + timedelta(days=tarea.frecuencia_dias)
    
    # 2. Crear Tarea
    nueva_tarea = TareaPreventiva(
        **tarea.model_dump(exclude={"repuestos"}),
        proxima_fecha=proxima_fecha
    )
    session.add(nueva_tarea)
    session.commit()
    session.refresh(nueva_tarea)
    
    # 3. Guardar Repuestos
    if tarea.repuestos:
        for rep in tarea.repuestos:
            nuevo_rep = TareaRepuesto(
                tarea_preventiva_id=nueva_tarea.id,
                repuesto_id=rep.repuesto_id,
                cantidad_requerida=rep.cantidad_requerida
            )
            session.add(nuevo_rep)
        session.commit()

    # Refrescar la tarea DESPUÉS de todos los commits
    # (el segundo commit expira los atributos del objeto)
    session.refresh(nueva_tarea)

    # Preparar respuesta - convertir TODO a diccionarios
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

# --- Endpoint para ACTUALIZAR tarea ---
@router.put("/{tarea_id}", response_model=TareaPreventivaRead)
def actualizar_tarea(tarea_id: int, tarea_data: TareaPreventivaUpdate, session: Session = Depends(get_session)):
    db_tarea = session.get(TareaPreventiva, tarea_id)
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    tarea_dict = tarea_data.model_dump(exclude_unset=True)
    
    # Actualizar campos simples
    for key, value in tarea_dict.items():
        if key != "repuestos":
            setattr(db_tarea, key, value)
    
    # Recalcular fecha
    if db_tarea.ultima_fecha:
        db_tarea.proxima_fecha = db_tarea.ultima_fecha + timedelta(days=db_tarea.frecuencia_dias)
    
    session.add(db_tarea)
    
    # Actualizar Repuestos
    if "repuestos" in tarea_dict:
        # Borrar anteriores
        session.exec(
            TareaRepuesto.__table__.delete().where(TareaRepuesto.tarea_preventiva_id == tarea_id)
        )
        # Agregar nuevos (model_dump ya convirtió a diccionarios)
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