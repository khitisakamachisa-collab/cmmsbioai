from typing import Optional
from sqlmodel import SQLModel, Field


class Proveedor(SQLModel, table=True):
    """
    Empresa proveedora de equipos, repuestos, herramientas o servicios.
    RF10 - Gestion de Proveedores y Contactos.
    """
    __tablename__ = "proveedor"

    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_empresa: str = Field(index=True, unique=True)
    direccion: Optional[str] = None
    telefono_principal: Optional[str] = None
    email_principal: Optional[str] = None
    pagina_web: Optional[str] = None
    notas_generales: Optional[str] = None


class ContactoProveedor(SQLModel, table=True):
    """
    Persona de contacto asociada a un proveedor.
    Puede haber varios contactos por proveedor (gerente, vendedor, soporte, etc.).
    """
    __tablename__ = "contactoproveedor"

    id: Optional[int] = Field(default=None, primary_key=True)
    proveedor_id: int = Field(foreign_key="proveedor.id", index=True)
    nombre_contacto: str
    cargo: Optional[str] = None
    telefono_contacto: Optional[str] = None
    email_contacto: Optional[str] = None
    notas_contacto: Optional[str] = None
