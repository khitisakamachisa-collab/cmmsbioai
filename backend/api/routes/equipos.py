from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.equipos import Equipo
from models.estados import EstadoEquipo
from models.users import Usuario # Asegúrate de que esta ruta sea correcta
from schemas.equipo import EquipoCreate, EquipoRead, EquipoUpdate

router = APIRouter(prefix="/equipos", tags=["Equipos"])

# NUEVO: Endpoint para listar técnicos (usuarios)
@router.get("/tecnicos")
def listar_tecnicos(session: Session = Depends(get_session)):
    tecnicos = session.exec(select(Usuario)).all()
    # Devolvemos solo lo necesario para el selector
    return [{"id": t.id, "username": t.username} for t in tecnicos]

@router.post("/", response_model=EquipoRead)
def crear_equipo(equipo: EquipoCreate, session: Session = Depends(get_session)):
    existe = session.exec(select(Equipo).where(Equipo.numero_serie == equipo.numero_serie)).first()
    if existe:
        raise HTTPException(status_code=400, detail="El número de serie ya está registrado")
    
    db_equipo = Equipo(**equipo.model_dump())
    session.add(db_equipo)
    session.commit()
    session.refresh(db_equipo)
    return db_equipo

@router.get("/", response_model=list[EquipoRead])
def listar_equipos(session: Session = Depends(get_session)):
    equipos = session.exec(select(Equipo)).all()
    return equipos

@router.put("/{equipo_id}", response_model=EquipoRead)
def actualizar_equipo(equipo_id: int, equipo_data: EquipoUpdate, session: Session = Depends(get_session)):
    db_equipo = session.get(Equipo, equipo_id)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    equipo_data_dict = equipo_data.model_dump(exclude_unset=True)
    for key, value in equipo_data_dict.items():
        setattr(db_equipo, key, value)
    
    session.add(db_equipo)
    session.commit()
    session.refresh(db_equipo)
    return db_equipo

@router.delete("/{equipo_id}")
def eliminar_equipo(equipo_id: int, session: Session = Depends(get_session)):
    db_equipo = session.get(Equipo, equipo_id)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    session.delete(db_equipo)
    session.commit()
    return {"ok": True, "message": "Equipo eliminado"}

# ---------------------------------------------------------
# ENDPOINT CORREGIDO: LEE DE LA BASE DE DATOS
# ---------------------------------------------------------
@router.get("/estados")
def listar_estados(session: Session = Depends(get_session)):
    # Usa EstadoEquipo aquí
    estados = session.exec(select(EstadoEquipo)).all()
    return estados

# ... imports existentes ...

# Endpoint para CREAR un nuevo estado (Solo para administración inicial)
@router.post("/estados")
def crear_estado(nombre_estado: str, session: Session = Depends(get_session)):
    # Creamos el objeto usando el modelo Estado
    nuevo_estado = Estado(nombre_estado=nombre_estado)
    session.add(nuevo_estado)
    session.commit()
    session.refresh(nuevo_estado)
    return nuevo_estado