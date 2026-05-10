from typing import Optional
from sqlmodel import Field, SQLModel

class Usuario(SQLModel, table=True):
    __tablename__ = "usuario" # Nombre real en la BD
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: Optional[str] = Field(default=None, unique=True, index=True)
    hashed_password: str
    full_name: Optional[str] = None
    role: str = Field(default="tecnico") 
    is_active: bool = Field(default=True)