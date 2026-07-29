from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from database import get_session
from models.historial import EventoHistorial
from models.ordenes import OrdenTrabajo
from models.equipos import Equipo
from models.users import Usuario
from models.repuestos import OtRepuestoUtilizado, Repuesto
from schemas.historial import EventoHistorialCreate, EventoHistorialRead, EventoHistorialUpdate

router = APIRouter(prefix="/historial", tags=["Historial de Mantenimiento"])


def enriquecer_evento(session: Session, evento: EventoHistorial) -> dict:
    """Agrega campos extra al evento para la vista: nombre de equipo, técnico, OT título."""
    data = evento.model_dump()

    # Nombre del equipo
    equipo = session.get(Equipo, evento.equipo_id)
    data["equipo_nombre"] = equipo.nombre_corto if equipo else "Desconocido"

    # Nombre del técnico
    if evento.tecnico_id:
        tecnico = session.get(Usuario, evento.tecnico_id)
        data["tecnico_nombre"] = tecnico.full_name if tecnico else "Desconocido"
    else:
        data["tecnico_nombre"] = None

    # Título de la OT
    if evento.orden_trabajo_id:
        ot = session.get(OrdenTrabajo, evento.orden_trabajo_id)
        data["ot_titulo"] = ot.titulo if ot else None
    else:
        data["ot_titulo"] = None

    return data


# --- Obtener historial de un equipo ---
@router.get("/equipo/{equipo_id}", response_model=list[EventoHistorialRead])
def historial_por_equipo(equipo_id: int, session: Session = Depends(get_session)):
    equipo = session.get(Equipo, equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    eventos = session.exec(
        select(EventoHistorial)
        .where(EventoHistorial.equipo_id == equipo_id)
        .order_by(EventoHistorial.fecha_evento.desc())
    ).all()

    return [enriquecer_evento(session, e) for e in eventos]


# --- Listar todo el historial (con filtro opcional por equipo) ---
@router.get("/", response_model=list[EventoHistorialRead])
def listar_historial(equipo_id: Optional[int] = None, session: Session = Depends(get_session)):
    if equipo_id:
        eventos = session.exec(
            select(EventoHistorial)
            .where(EventoHistorial.equipo_id == equipo_id)
            .order_by(EventoHistorial.fecha_evento.desc())
        ).all()
    else:
        eventos = session.exec(
            select(EventoHistorial).order_by(EventoHistorial.fecha_evento.desc())
        ).all()

    return [enriquecer_evento(session, e) for e in eventos]


# --- Obtener un evento específico ---
@router.get("/{evento_id}", response_model=EventoHistorialRead)
def obtener_evento(evento_id: int, session: Session = Depends(get_session)):
    evento = session.get(EventoHistorial, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    return enriquecer_evento(session, evento)


# --- Crear evento manual ---
@router.post("/", response_model=EventoHistorialRead)
def crear_evento(evento: EventoHistorialCreate, session: Session = Depends(get_session)):
    # Validar equipo
    equipo = session.get(Equipo, evento.equipo_id)
    if not equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")

    nuevo = EventoHistorial(**evento.model_dump(exclude_unset=True))
    session.add(nuevo)
    session.commit()
    session.refresh(nuevo)
    return enriquecer_evento(session, nuevo)


# --- Actualizar evento ---
@router.put("/{evento_id}", response_model=EventoHistorialRead)
def actualizar_evento(evento_id: int, evento_data: EventoHistorialUpdate, session: Session = Depends(get_session)):
    evento = session.get(EventoHistorial, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")

    for key, value in evento_data.model_dump(exclude_unset=True).items():
        setattr(evento, key, value)

    session.add(evento)
    session.commit()
    session.refresh(evento)
    return enriquecer_evento(session, evento)


# --- Eliminar evento ---
@router.delete("/{evento_id}")
def eliminar_evento(evento_id: int, session: Session = Depends(get_session)):
    evento = session.get(EventoHistorial, evento_id)
    if not evento:
        raise HTTPException(status_code=404, detail="Evento no encontrado")
    session.delete(evento)
    session.commit()
    return {"ok": True, "message": "Evento eliminado"}
