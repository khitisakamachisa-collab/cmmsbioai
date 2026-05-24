from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.users import Usuario
from utils.security import get_password_hash  # Usar el mismo bcrypt que auth.py

router = APIRouter(prefix="/users", tags=["Users"])

@router.get("/")
def listar_usuarios(session: Session = Depends(get_session)):
    usuarios = session.exec(select(Usuario)).all()
    return usuarios

@router.post("/")
def crear_usuario(usuario_data: dict, session: Session = Depends(get_session)):
    # Verificar email
    existe = session.exec(select(Usuario).where(Usuario.email == usuario_data["email"])).first()
    if existe:
        raise HTTPException(status_code=400, detail="El email ya está registrado")

    # Hashear contraseña con bcrypt (mismo método que usa auth.py para verificar)
    hashed_password = get_password_hash(usuario_data["password"])
    
    nuevo_usuario = Usuario(
        username=usuario_data["email"], # Usamos email como username
        email=usuario_data["email"],
        full_name=usuario_data["nombre_completo"],
        hashed_password=hashed_password,
        role=usuario_data.get("rol", "tecnico"),
        is_active=True
    )
    session.add(nuevo_usuario)
    session.commit()
    session.refresh(nuevo_usuario)
    return nuevo_usuario