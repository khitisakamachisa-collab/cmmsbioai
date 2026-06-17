from typing import Optional, List
from pydantic import BaseModel


# ============================================================
# CONTACTOS PROVEEDOR
# ============================================================
class ContactoProveedorCreate(BaseModel):
    proveedor_id: Optional[int] = None  # Se asigna desde la URL en la ruta anidada
    nombre_contacto: str
    cargo: Optional[str] = None
    telefono_contacto: Optional[str] = None
    email_contacto: Optional[str] = None
    notas_contacto: Optional[str] = None


class ContactoProveedorUpdate(BaseModel):
    nombre_contacto: Optional[str] = None
    cargo: Optional[str] = None
    telefono_contacto: Optional[str] = None
    email_contacto: Optional[str] = None
    notas_contacto: Optional[str] = None


class ContactoProveedorRead(BaseModel):
    id: int
    proveedor_id: int
    nombre_contacto: str
    cargo: Optional[str]
    telefono_contacto: Optional[str]
    email_contacto: Optional[str]
    notas_contacto: Optional[str]

    class Config:
        from_attributes = True


# ============================================================
# PROVEEDORES
# ============================================================
class ProveedorCreate(BaseModel):
    nombre_empresa: str
    direccion: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    pagina_web: Optional[str] = None
    notas_generales: Optional[str] = None


class ProveedorUpdate(BaseModel):
    nombre_empresa: Optional[str] = None
    direccion: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    pagina_web: Optional[str] = None
    notas_generales: Optional[str] = None


class ProveedorRead(BaseModel):
    id: int
    nombre_empresa: str
    direccion: Optional[str]
    telefono_principal: Optional[str]
    email_principal: Optional[str]
    pagina_web: Optional[str]
    notas_generales: Optional[str]

    class Config:
        from_attributes = True


class ProveedorReadWithContactos(ProveedorRead):
    """Proveedor con su lista de contactos asociados."""
    contactos: List[ContactoProveedorRead] = []
