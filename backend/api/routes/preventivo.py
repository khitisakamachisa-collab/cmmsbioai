from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import timedelta
from database import get_session
from models.preventivo import TareaPreventiva, TareaRepuesto
from schemas.preventivo import TareaPreventivaCreate, TareaPreventivaRead, TareaPreventivaUpdate

router = APIRouter(prefix="/preventivo", tags=["Mantenimiento Preventivo"])

# Endpoint para CREAR una tarea
@router.post("/", response_model=TareaPreventivaRead)
def crear_tarea(tarea: TareaPreventivaCreate, session: Session = Depends(get_session)):
    # 1. Calcular la próxima fecha
    proxima_fecha = None
    if tarea.ultima_fecha:
        proxima_fecha = tarea.ultima_fecha + timedelta(days=tarea.frecuencia_dias)
    
    # 2. Crear el objeto TareaPreventiva
    nueva_tarea = TareaPreventiva(
        **tarea.model_dump(exclude={"repuestos"}), # Excluimos repuestos para tratarlos aparte
        proxima_fecha=proxima_fecha
    )
    session.add(nueva_tarea)
    session.commit()
    session.refresh(nueva_tarea)
    
    # 3. Agregar los repuestos asociados si vinieron
    if tarea.repuestos:
        for rep in tarea.repuestos:
            nuevo_rep = TareaRepuesto(
                tarea_preventiva_id=nueva_tarea.id,
                repuesto_id=rep.repuesto_id,
                cantidad_requerida=rep.cantidad_requerida
            )
            session.add(nuevo_rep)
        session.commit()

    return nueva_tarea

# Endpoint para LISTAR tareas
@router.get("/", response_model=list[TareaPreventivaRead])
def listar_tareas(session: Session = Depends(get_session)):
    tareas = session.exec(select(TareaPreventiva)).all()
    return tareas

# Endpoint para ACTUALIZAR una tarea
@router.put("/{tarea_id}", response_model=TareaPreventivaRead)
def actualizar_tarea(tarea_id: int, tarea_data: TareaPreventivaUpdate, session: Session = Depends(get_session)):
    db_tarea = session.get(TareaPreventiva, tarea_id)
    if not db_tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    tarea_dict = tarea_data.model_dump(exclude_unset=True)
    for key, value in tarea_dict.items():
        setattr(db_tarea, key, value)
    
    # Recalcular próxima fecha si cambió frecuencia o última fecha
    if db_tarea.ultima_fecha:
        db_tarea.proxima_fecha = db_tarea.ultima_fecha + timedelta(days=db_tarea.frecuencia_dias)
        session.add(db_tarea)
    session.commit()
    session.refresh(db_tarea)
    return db_tarea

@router.delete("/{tarea_id}")
def eliminar_tarea(tarea_id: int, session: Session = Depends(get_session)):
    tarea = session.get(TareaPreventiva, tarea_id)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    session.delete(tarea)
    session.commit()
    return {"ok": True, "message": "Tarea eliminada"}