from sqlmodel import SQLModel, Field
from typing import Optional

class EstadoEquipo(SQLModel, table=True):
    # Forzamos el nombre de la tabla para que coincida con tu BD y el FK
    __tablename__ = "estadoequipo"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_estado: str = Field(unique=True)

    # NUEVO: Campo para guardar el código de color (ej: #27ae60)
    # Le damos un valor por defecto (gris) por si no se especifica
    color: str = Field(default="#95a5a6")