from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from database import get_session
from models.repuestos import Repuesto
from schemas.repuesto import RepuestoCreate, RepuestoRead

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