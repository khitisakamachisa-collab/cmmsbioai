from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.estados import EstadoEquipo
from schemas.estado_equipo import EstadoEquipoCreate, EstadoEquipoRead

router = APIRouter(prefix="/estados-equipo", tags=["Estados Equipo"])

# Endpoint para CREAR un estado
@router.post("/", response_model=EstadoEquipoRead)
def crear_estado(estado: EstadoEquipoCreate, session: Session = Depends(get_session)):
    # Verificar si ya existe (opcional pero bueno)
    existe = session.exec(select(EstadoEquipo).where(EstadoEquipo.nombre_estado == estado.nombre_estado)).first()
    if existe:
        raise HTTPException(status_code=400, detail="El estado ya existe")
    
    db_estado = EstadoEquipo(**estado.model_dump()) # O EstadoEquipo(**estado.dict())
    session.add(db_estado)
    session.commit()
    session.refresh(db_estado)
    return db_estado

# Endpoint para LISTAR estados
@router.get("/", response_model=list[EstadoEquipoRead])
def listar_estados(session: Session = Depends(get_session)):
    estados = session.exec(select(EstadoEquipo)).all()
    return estados