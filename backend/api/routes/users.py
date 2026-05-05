from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.users import Usuario
from schemas.user import UserCreate, UserRead
from utils.security import get_password_hash

router = APIRouter(prefix="/users", tags=["Usuarios"])

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    existe = session.exec(select(Usuario).where(Usuario.username == user.username)).first()
    if existe:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya está registrado")
    
    hashed_pw = get_password_hash(user.password)
    db_user = Usuario(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        hashed_password=hashed_pw
    )
    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

@router.get("/", response_model=list[UserRead])
def read_users(session: Session = Depends(get_session)):
    users = session.exec(select(Usuario)).all()
    return users