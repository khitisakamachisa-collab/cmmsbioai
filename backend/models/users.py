from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime

class Usuario(SQLModel, table=True):
    """
    Tabla Usuarios.
    Almacena técnicos y administradores.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: str = Field(default="tecnico") # 'admin' o 'tecnico'
    is_active: bool = Field(default=True)