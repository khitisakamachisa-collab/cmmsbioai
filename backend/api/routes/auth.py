from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from database import get_session
from models.users import Usuario
from utils.security import verify_password, create_access_token

router = APIRouter(tags=["Auth"])

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    # 1. Buscar usuario por username
    user = session.exec(select(Usuario).where(Usuario.username == form_data.username)).first()
    
    if not user:
        raise HTTPException(status_code=400, detail="Usuario incorrecto")
    
    # 2. Verificar contraseña
    # form_data.password es la contraseña en texto plano que envía el frontend
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Contraseña incorrecta")
    
    # 3. Crear Token
    access_token = create_access_token(data={"sub": user.username})
    
    # 4. Devolver token (Formato estándar OAuth2)
    return {"access_token": access_token, "token_type": "bearer"}