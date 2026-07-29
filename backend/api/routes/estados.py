from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.estados import EstadoEquipo
from schemas.estado_equipo import EstadoEquipoCreate, EstadoEquipoRead

router = APIRouter(prefix="/estados-equipo", tags=["Estados Equipo"])

# Endpoint para CREAR un estado
@router.post("/", response_model=EstadoEquipoRead)
def crear_estado(estado: EstadoEquipoCreate, session: Session = Depends(get_session)):
    # Verificar si ya existe
    existe = session.exec(select(EstadoEquipo).where(EstadoEquipo.nombre_estado == estado.nombre_estado)).first()
    if existe:
        raise HTTPException(status_code=400, detail="El estado ya existe")
    
    db_estado = EstadoEquipo(**estado.model_dump())
    session.add(db_estado)
    session.commit()
    session.refresh(db_estado)
    return db_estado

# Endpoint para LISTAR estados
@router.get("/", response_model=list[EstadoEquipoRead])
def listar_estados(session: Session = Depends(get_session)):
    estados = session.exec(select(EstadoEquipo)).all()
    return estados

# Endpoint para OBTENER un estado por ID
@router.get("/{estado_id}", response_model=EstadoEquipoRead)
def obtener_estado(estado_id: int, session: Session = Depends(get_session)):
    estado = session.get(EstadoEquipo, estado_id)
    if not estado:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    return estado

# Endpoint para ACTUALIZAR un estado
@router.put("/{estado_id}", response_model=EstadoEquipoRead)
def actualizar_estado(estado_id: int, nombre_estado: str, color: str = "#95a5a6", session: Session = Depends(get_session)):
    db_estado = session.get(EstadoEquipo, estado_id)
    if not db_estado:
        raise HTTPException(status_code=404, detail="Estado no encontrado")
    db_estado.nombre_estado = nombre_estado
    db_estado.color = color
    session.add(db_estado)
    session.commit()
    session.refresh(db_estado)
    return db_estado