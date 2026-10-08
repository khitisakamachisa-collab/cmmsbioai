from pydantic import BaseModel, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    """v1.1.2 (I6): valida el POST /users/ con schema real (antes llegaba un dict crudo).

    Campos tal como los envía UsuariosView.vue (formData):
    { nombre_completo, email, password, rol }
    Se mantiene 'rol' (no 'role') para no romper el frontend existente;
    users.py lo mapea a Usuario.role.
    """
    email: str
    password: str
    nombre_completo: Optional[str] = None
    rol: str = "tecnico"


class UserRead(BaseModel):
    """v1.1.2 (I6): respuesta de /users/ SIN hashed_password (nunca exponer hashes)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = "tecnico"
    is_active: bool = True
