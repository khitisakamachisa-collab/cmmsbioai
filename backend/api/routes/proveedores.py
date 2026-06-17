from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from database import get_session
from models.proveedores import Proveedor, ContactoProveedor
from schemas.proveedor import (
    ProveedorCreate, ProveedorUpdate, ProveedorRead, ProveedorReadWithContactos,
    ContactoProveedorCreate, ContactoProveedorUpdate, ContactoProveedorRead,
)

router = APIRouter(prefix="/proveedores", tags=["Proveedores"])


# ============================================================
# PROVEEDORES - CRUD principal
# ============================================================
@router.post("/", response_model=ProveedorRead, status_code=201)
def crear_proveedor(payload: ProveedorCreate, session: Session = Depends(get_session)):
    """Crea un nuevo proveedor."""
    existe = session.exec(
        select(Proveedor).where(Proveedor.nombre_empresa == payload.nombre_empresa)
    ).first()
    if existe:
        raise HTTPException(status_code=400, detail="Ya existe un proveedor con ese nombre de empresa")

    db_proveedor = Proveedor(**payload.model_dump())
    session.add(db_proveedor)
    session.commit()
    session.refresh(db_proveedor)
    return db_proveedor


@router.get("/", response_model=list[ProveedorRead])
def listar_proveedores(session: Session = Depends(get_session)):
    """Lista todos los proveedores (sin contactos)."""
    return session.exec(select(Proveedor).order_by(Proveedor.nombre_empresa)).all()


@router.get("/con-contactos", response_model=list[ProveedorReadWithContactos])
def listar_proveedores_con_contactos(session: Session = Depends(get_session)):
    """Lista todos los proveedores incluyendo sus contactos asociados."""
    proveedores = session.exec(select(Proveedor).order_by(Proveedor.nombre_empresa)).all()
    resultado = []
    for prov in proveedores:
        contactos = session.exec(
            select(ContactoProveedor).where(ContactoProveedor.proveedor_id == prov.id)
        ).all()
        prov_dict = ProveedorReadWithContactos.model_validate(prov)
        prov_dict.contactos = contactos
        resultado.append(prov_dict)
    return resultado


@router.get("/{proveedor_id}", response_model=ProveedorReadWithContactos)
def obtener_proveedor(proveedor_id: int, session: Session = Depends(get_session)):
    """Obtiene un proveedor por ID incluyendo sus contactos."""
    proveedor = session.get(Proveedor, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    contactos = session.exec(
        select(ContactoProveedor).where(ContactoProveedor.proveedor_id == proveedor_id)
    ).all()
    prov_dict = ProveedorReadWithContactos.model_validate(proveedor)
    prov_dict.contactos = contactos
    return prov_dict


@router.put("/{proveedor_id}", response_model=ProveedorRead)
def actualizar_proveedor(proveedor_id: int, payload: ProveedorUpdate, session: Session = Depends(get_session)):
    """Actualiza los datos de un proveedor."""
    db_proveedor = session.get(Proveedor, proveedor_id)
    if not db_proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    datos = payload.model_dump(exclude_unset=True)
    # Validar unicidad del nombre si se esta cambiando
    if "nombre_empresa" in datos and datos["nombre_empresa"] != db_proveedor.nombre_empresa:
        existe = session.exec(
            select(Proveedor).where(Proveedor.nombre_empresa == datos["nombre_empresa"])
        ).first()
        if existe:
            raise HTTPException(status_code=400, detail="Ya existe un proveedor con ese nombre de empresa")

    for key, value in datos.items():
        setattr(db_proveedor, key, value)

    session.add(db_proveedor)
    session.commit()
    session.refresh(db_proveedor)
    return db_proveedor


@router.delete("/{proveedor_id}", status_code=204)
def eliminar_proveedor(proveedor_id: int, session: Session = Depends(get_session)):
    """Elimina un proveedor y todos sus contactos asociados."""
    db_proveedor = session.get(Proveedor, proveedor_id)
    if not db_proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    # Eliminar contactos asociados primero (cascade manual)
    contactos = session.exec(
        select(ContactoProveedor).where(ContactoProveedor.proveedor_id == proveedor_id)
    ).all()
    for c in contactos:
        session.delete(c)

    session.delete(db_proveedor)
    session.commit()
    return None


# ============================================================
# CONTACTOS DEL PROVEEDOR - Sub-recurso anidado
# ============================================================
@router.post("/{proveedor_id}/contactos", response_model=ContactoProveedorRead, status_code=201)
def agregar_contacto(proveedor_id: int, payload: ContactoProveedorCreate, session: Session = Depends(get_session)):
    """Agrega un contacto a un proveedor existente."""
    proveedor = session.get(Proveedor, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")

    datos = payload.model_dump(exclude_unset=True)
    datos["proveedor_id"] = proveedor_id
    db_contacto = ContactoProveedor(**datos)
    session.add(db_contacto)
    session.commit()
    session.refresh(db_contacto)
    return db_contacto


@router.get("/{proveedor_id}/contactos", response_model=list[ContactoProveedorRead])
def listar_contactos_de_proveedor(proveedor_id: int, session: Session = Depends(get_session)):
    """Lista todos los contactos asociados a un proveedor."""
    proveedor = session.get(Proveedor, proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=404, detail="Proveedor no encontrado")
    return session.exec(
        select(ContactoProveedor).where(ContactoProveedor.proveedor_id == proveedor_id)
    ).all()


@router.put("/contactos/{contacto_id}", response_model=ContactoProveedorRead)
def actualizar_contacto(contacto_id: int, payload: ContactoProveedorUpdate, session: Session = Depends(get_session)):
    """Actualiza un contacto especifico."""
    db_contacto = session.get(ContactoProveedor, contacto_id)
    if not db_contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    datos = payload.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(db_contacto, key, value)

    session.add(db_contacto)
    session.commit()
    session.refresh(db_contacto)
    return db_contacto


@router.delete("/contactos/{contacto_id}", status_code=204)
def eliminar_contacto(contacto_id: int, session: Session = Depends(get_session)):
    """Elimina un contacto especifico."""
    db_contacto = session.get(ContactoProveedor, contacto_id)
    if not db_contacto:
        raise HTTPException(status_code=404, detail="Contacto no encontrado")

    session.delete(db_contacto)
    session.commit()
    return None
