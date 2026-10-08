from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from database import get_session
from models.users import Usuario
from schemas.user import UserCreate, UserRead
from utils.security import get_password_hash  # Mismo bcrypt que auth.py

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/", response_model=List[UserRead])
def listar_usuarios(session: Session = Depends(get_session)):
    """v1.1.2 (I6): responde con UserRead — ya NO expone hashed_password."""
    usuarios = session.exec(select(Usuario)).all()
    return [UserRead.model_validate(u) for u in usuarios]


@router.post("/", response_model=UserRead)
def crear_usuario(datos: UserCreate, session: Session = Depends(get_session)):
    """v1.1.2 (I6): valida entrada con UserCreate (antes dict crudo) y
    responde con UserRead (sin hash). Comportamiento anterior preservado:
    username = email, rol del frontend -> Usuario.role."""
    existe = session.exec(
        select(Usuario).where(Usuario.email == datos.email)
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    existe_username = session.exec(
        select(Usuario).where(Usuario.username == datos.email)
    ).first()
    if existe_username:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")

    nuevo_usuario = Usuario(
        username=datos.email,  # Se usa email como username (igual que antes)
        email=datos.email,
        full_name=datos.nombre_completo,
        hashed_password=get_password_hash(datos.password),
        role=datos.rol or "tecnico",
        is_active=True,
    )
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return UserRead.model_validate(nuevo_usuario)
