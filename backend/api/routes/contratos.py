"""
Endpoints CRUD para Contratos - RF12 v0.9.2
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from datetime import datetime, date
from database import get_session
from models.contratos import Contrato, ContratoEquipo
from models.proveedores import Proveedor
from models.equipos import Equipo
from schemas.contrato import ContratoCreate, ContratoUpdate, ContratoRead

router = APIRouter(prefix="/contratos", tags=["Contratos"])


def _calcular_estado(fecha_inicio, fecha_fin):
    hoy = date.today()
    activo = False
    dias_restantes = None
    if isinstance(fecha_inicio, datetime):
        fecha_inicio = fecha_inicio.date()
    if isinstance(fecha_fin, datetime):
        fecha_fin = fecha_fin.date()
    if fecha_inicio and fecha_fin:
        if fecha_inicio <= hoy <= fecha_fin:
            activo = True
            dias_restantes = (fecha_fin - hoy).days
        elif fecha_fin < hoy:
            activo = False
            dias_restantes = (fecha_fin - hoy).days
        else:
            activo = False
            dias_restantes = (fecha_inicio - hoy).days
    return activo, dias_restantes


def _enriquecer_contrato(session, contrato):
    data = contrato.model_dump()
    activo, dias_restantes = _calcular_estado(contrato.fecha_inicio, contrato.fecha_fin)
    data['activo'] = activo
    data['dias_restantes'] = dias_restantes
    proveedor = session.get(Proveedor, contrato.proveedor_id)
    data['proveedor_nombre'] = proveedor.nombre_empresa if proveedor else 'N/A'
    asociaciones = session.exec(
        select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato.id)
    ).all()
    equipos = []
    for a in asociaciones:
        eq = session.get(Equipo, a.equipo_id)
        if eq:
            equipos.append({'id': eq.id, 'nombre_corto': eq.nombre_corto, 'modelo': eq.modelo,
                           'numero_serie': eq.numero_serie, 'ubicacion_actual': eq.ubicacion_actual})
    data['equipos'] = equipos
    return data


@router.post("/", response_model=ContratoRead, status_code=201)
def crear_contrato(payload: ContratoCreate, session: Session = Depends(get_session)):
    proveedor = session.get(Proveedor, payload.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=400, detail=f"Proveedor ID {payload.proveedor_id} no existe")
    if payload.fecha_fin < payload.fecha_inicio:
        raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")
    datos = payload.model_dump(exclude={'equipos_ids'})
    datos['fecha_inicio'] = datetime.combine(datos['fecha_inicio'], datetime.min.time())
    datos['fecha_fin'] = datetime.combine(datos['fecha_fin'], datetime.min.time())
    nuevo = Contrato(**datos)
    session.add(nuevo)
    session.flush()
    if payload.equipos_ids:
        for eq_id in payload.equipos_ids:
            eq = session.get(Equipo, eq_id)
            if eq:
                session.add(ContratoEquipo(contrato_id=nuevo.id, equipo_id=eq_id))
    session.commit()
    session.refresh(nuevo)
    return _enriquecer_contrato(session, nuevo)


@router.get("/", response_model=list[ContratoRead])
def listar_contratos(proveedor_id: int = None, equipo_id: int = None, vigente: bool = None, session: Session = Depends(get_session)):
    query = select(Contrato)
    if proveedor_id:
        query = query.where(Contrato.proveedor_id == proveedor_id)
    if equipo_id:
        contrato_ids = select(ContratoEquipo.contrato_id).where(ContratoEquipo.equipo_id == equipo_id)
        query = query.where(Contrato.id.in_(contrato_ids))
    contratos = session.exec(query.order_by(Contrato.fecha_fin.desc())).all()
    resultado = []
    for c in contratos:
        data = _enriquecer_contrato(session, c)
        if vigente is True and not data['activo']:
            continue
        if vigente is False and data['activo']:
            continue
        resultado.append(data)
    return resultado


@router.get("/{contrato_id}", response_model=ContratoRead)
def obtener_contrato(contrato_id: int, session: Session = Depends(get_session)):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return _enriquecer_contrato(session, contrato)


@router.put("/{contrato_id}", response_model=ContratoRead)
def actualizar_contrato(contrato_id: int, payload: ContratoUpdate, session: Session = Depends(get_session)):
    db_contrato = session.get(Contrato, contrato_id)
    if not db_contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    datos = payload.model_dump(exclude_unset=True)
    equipos_ids = datos.pop('equipos_ids', None)
    for key, value in datos.items():
        if key in ('fecha_inicio', 'fecha_fin') and value:
            value = datetime.combine(value, datetime.min.time())
        setattr(db_contrato, key, value)
    if db_contrato.fecha_fin < db_contrato.fecha_inicio:
        raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")
    session.add(db_contrato)
    if equipos_ids is not None:
        existing = session.exec(select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato_id)).all()
        for e in existing:
            session.delete(e)
        session.flush()
        for eq_id in equipos_ids:
            eq = session.get(Equipo, eq_id)
            if eq:
                session.add(ContratoEquipo(contrato_id=contrato_id, equipo_id=eq_id))
    session.commit()
    session.refresh(db_contrato)
    return _enriquecer_contrato(session, db_contrato)


@router.delete("/{contrato_id}")
def eliminar_contrato(contrato_id: int, session: Session = Depends(get_session)):
    db_contrato = session.get(Contrato, contrato_id)
    if not db_contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    asociaciones = session.exec(select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato_id)).all()
    for a in asociaciones:
        session.delete(a)
    session.delete(db_contrato)
    session.commit()
    return {"ok": True, "message": "Contrato eliminado"}


@router.get("/tipos/lista")
def listar_tipos_contrato():
    return ['Comodato', 'Mantenimiento Preventivo', 'Mantenimiento Correctivo',
            'Leasing', 'Garantía Extendida', 'Soporte Técnico', 'Servicio Integral', 'Otro']


@router.get("/monedas/lista")
def listar_monedas():
    return ['USD', 'EUR', 'BOB', 'MXN', 'ARS', 'CLP', 'COP', 'PEN', 'BRL', 'Otro']


@router.get("/periodicidades/lista")
def listar_periodicidades():
    return ['Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual']
