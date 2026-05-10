from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.users import Usuario # Importamos del archivo user.py existente
from passlib.context import CryptContext

router = APIRouter(prefix="/users", tags=["Users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

    import hashlib # Agrega esto al inicio del archivo

    # ... dentro de la función ...
    # Encriptar usando SHA256 (método estándar de Python, compatible con todo)
    hashed_password = hashlib.sha256(usuario_data["password"].encode()).hexdigest()
    
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