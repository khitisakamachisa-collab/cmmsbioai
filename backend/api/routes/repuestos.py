from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.repuestos import Repuesto
from schemas.repuesto import RepuestoCreate, RepuestoRead, RepuestoUpdate

router = APIRouter(prefix="/repuestos", tags=["Inventario"])

@router.post("/", response_model=RepuestoRead)
def crear_repuesto(repuesto: RepuestoCreate, session: Session = Depends(get_session)):
    db_rep = Repuesto(**repuesto.model_dump())
    session.add(db_rep)
    session.commit()
    session.refresh(db_rep)
    return db_rep

@router.get("/", response_model=list[RepuestoRead])
def listar_repuestos(session: Session = Depends(get_session)):
    repuestos = session.exec(select(Repuesto)).all()
    return repuestos


@router.get("/{rep_id}", response_model=RepuestoRead)
def obtener_repuesto(rep_id: int, session: Session = Depends(get_session)):
    db_rep = session.get(Repuesto, rep_id)
    if not db_rep:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    return db_rep


@router.put("/{rep_id}", response_model=RepuestoRead)
def actualizar_repuesto(
    rep_id: int,
    datos: RepuestoUpdate,
    session: Session = Depends(get_session),
):
    db_rep = session.get(Repuesto, rep_id)
    if not db_rep:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(db_rep, key, value)
    session.add(db_rep)
    session.commit()
    session.refresh(db_rep)
    return db_rep


@router.delete("/{rep_id}")
def eliminar_repuesto(rep_id: int, session: Session = Depends(get_session)):
    db_rep = session.get(Repuesto, rep_id)
    if not db_rep:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    session.delete(db_rep)
    session.commit()
    return {"ok": True, "message": "Repuesto eliminado"}