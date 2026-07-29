"""
Endpoints CRUD para OtCostoAdicional - RF11 v0.9.1
v0.9.21: API restaurada para gestion de multiples costos por OT.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from database import get_session
from models.costos import OtCostoAdicional
from models.ordenes import OrdenTrabajo
from schemas.costo import (
    OtCostoAdicionalCreate,
    OtCostoAdicionalUpdate,
    OtCostoAdicionalRead,
    TIPOS_COSTO_VALIDOS,
)

router = APIRouter(prefix="/costos", tags=["Costos Adicionales OT"])


@router.post("/", response_model=OtCostoAdicionalRead, status_code=201)
def crear_costo(payload: OtCostoAdicionalCreate, session: Session = Depends(get_session)):
    """Crea un costo adicional asociado a una OT."""
    ot = session.get(OrdenTrabajo, payload.orden_trabajo_id)
    if not ot:
        raise HTTPException(status_code=404, detail=f"OT ID {payload.orden_trabajo_id} no encontrada")
    costo = OtCostoAdicional(**payload.model_dump())
    session.add(costo)
    session.commit()
    session.refresh(costo)
    return costo


@router.get("/", response_model=list[OtCostoAdicionalRead])
def listar_costos(orden_trabajo_id: Optional[int] = None, session: Session = Depends(get_session)):
    """Lista costos adicionales, opcionalmente filtrados por orden_trabajo_id."""
    query = select(OtCostoAdicional)
    if orden_trabajo_id:
        query = query.where(OtCostoAdicional.orden_trabajo_id == orden_trabajo_id)
    return session.exec(query.order_by(OtCostoAdicional.fecha_creacion.desc())).all()


@router.get("/tipos/lista")
def listar_tipos_costo():
    """Lista los tipos de costo válidos."""
    return sorted(list(TIPOS_COSTO_VALIDOS))


@router.get("/{costo_id}", response_model=OtCostoAdicionalRead)
def obtener_costo(costo_id: int, session: Session = Depends(get_session)):
    costo = session.get(OtCostoAdicional, costo_id)
    if not costo:
        raise HTTPException(status_code=404, detail="Costo no encontrado")
    return costo


@router.put("/{costo_id}", response_model=OtCostoAdicionalRead)
def actualizar_costo(costo_id: int, payload: OtCostoAdicionalUpdate, session: Session = Depends(get_session)):
    db_costo = session.get(OtCostoAdicional, costo_id)
    if not db_costo:
        raise HTTPException(status_code=404, detail="Costo no encontrado")
    datos = payload.model_dump(exclude_unset=True)
    for key, value in datos.items():
        setattr(db_costo, key, value)
    session.add(db_costo)
    session.commit()
    session.refresh(db_costo)
    return db_costo


@router.delete("/{costo_id}", status_code=204)
def eliminar_costo(costo_id: int, session: Session = Depends(get_session)):
    db_costo = session.get(OtCostoAdicional, costo_id)
    if not db_costo:
        raise HTTPException(status_code=404, detail="Costo no encontrado")
    session.delete(db_costo)
    session.commit()
    return None


@router.get("/ot/{orden_trabajo_id}/total")
def total_costos_ot(orden_trabajo_id: int, session: Session = Depends(get_session)):
    """Retorna el total de costos adicionales de una OT."""
    ot = session.get(OrdenTrabajo, orden_trabajo_id)
    if not ot:
        raise HTTPException(status_code=404, detail="OT no encontrada")
    costos = session.exec(
        select(OtCostoAdicional).where(OtCostoAdicional.orden_trabajo_id == orden_trabajo_id)
    ).all()
    total = sum(c.monto_costo for c in costos)
    return {
        "orden_trabajo_id": orden_trabajo_id,
        "cantidad_costos": len(costos),
        "total": round(total, 2)
    }
