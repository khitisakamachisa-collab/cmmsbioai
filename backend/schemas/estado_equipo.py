from pydantic import BaseModel
from typing import Optional

# Schema para crear un estado (lo que envía el frontend)
class EstadoEquipoCreate(BaseModel):
    nombre_estado: str
    color: str = "#95a5a6"  # Color por defecto (gris)

# Schema para leer un estado (lo que devuelve el backend, incluye el ID)
class EstadoEquipoRead(BaseModel):
    id: int
    nombre_estado: str
    color: str = "#95a5a6"

    class Config:
        from_attributes = True