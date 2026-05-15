from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import Optional
from database import get_session
from models.ordenes import OrdenTrabajo, EstadoOT
from models.repuestos import Repuesto, OtRepuestoUtilizado
from schemas.orden_trabajo import OrdenTrabajoCreate, OrdenTrabajoRead, OrdenTrabajoUpdate

router = APIRouter(prefix="/ordenes", tags=["Ordenes de Trabajo"])

# Endpoint para crear estados de OT
@router.post("/estados/", tags=["Estados OT"])
def crear_estado_ot(nombre: str, session: Session = Depends(get_session)):
    nuevo_estado = EstadoOT(nombre_estado=nombre)
    session.add(nuevo_estado)
    session.commit()
    session.refresh(nuevo_estado)
    return nuevo_estado

# Endpoint para listar estados de OT
@router.get("/estados/", tags=["Estados OT"])
def listar_estados_ot(session: Session = Depends(get_session)):
    return session.exec(select(EstadoOT)).all()

# Endpoint para CREAR una OT
@router.post("/", response_model=OrdenTrabajoRead)
def crear_orden(orden: OrdenTrabajoCreate, session: Session = Depends(get_session)):
    db_orden = OrdenTrabajo(**orden.model_dump())
    session.add(db_orden)
    session.commit()
    session.refresh(db_orden)
    return db_orden

# Endpoint para LISTAR OTs
@router.get("/", response_model=list[OrdenTrabajoRead])
def listar_ordenes(equipo_id: Optional[int] = None, session: Session = Depends(get_session)):
    if equipo_id:
        ordenes = session.exec(select(OrdenTrabajo).where(OrdenTrabajo.equipo_id == equipo_id)).all()
    else:
        ordenes = session.exec(select(OrdenTrabajo)).all()
    return ordenes

# --- NUEVO: Endpoint para VER UNA OT por ID ---
# --- Endpoint para VER UNA OT por ID (Corregido) ---
@router.get("/{ot_id}", response_model=OrdenTrabajoRead)
def obtener_orden(ot_id: int, session: Session = Depends(get_session)):
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    
    # 1. Buscar repuestos utilizados
    repuestos = session.exec(
        select(OtRepuestoUtilizado).where(OtRepuestoUtilizado.orden_trabajo_id == ot_id)
    ).all()
    
    # 2. Convertir el objeto a diccionario para poder agregarle datos extra
    data = db_ot.model_dump()
    
    # 3. Agregar la lista de repuestos al diccionario
    data["repuestos_usados"] = repuestos
    
    return data
# ----------------------------------------------

# Endpoint para ACTUALIZAR (Cerrar) una OT con lógica de stock
@router.put("/{ot_id}", response_model=OrdenTrabajoRead)
def actualizar_orden(ot_id: int, ot_data: OrdenTrabajoUpdate, session: Session = Depends(get_session)):
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden de Trabajo no encontrada")
    
    ot_data_dict = ot_data.model_dump(exclude_unset=True)
    repuestos_recibidos = ot_data_dict.pop("repuestos_utilizados", None)
    
    # Actualizar campos simples
    for key, value in ot_data_dict.items():
        setattr(db_ot, key, value)
    
    # Lógica de Stock
    if repuestos_recibidos:
        for item in repuestos_recibidos:
            rep_id = item['repuesto_id']
            cant = item['cantidad']
            
            db_rep = session.get(Repuesto, rep_id)
            if not db_rep:
                raise HTTPException(status_code=404, detail=f"Repuesto ID {rep_id} no encontrado")
            
            if db_rep.cantidad_disponible < cant:
                raise HTTPException(status_code=400, detail=f"Stock insuficiente de {db_rep.nombre_repuesto}")

            db_rep.cantidad_disponible -= cant
            session.add(db_rep)

            uso = OtRepuestoUtilizado(
                orden_trabajo_id=ot_id,
                repuesto_id=rep_id,
                cantidad_utilizada=cant
            )
            session.add(uso)
    
    session.add(db_ot)
    session.commit()
    session.refresh(db_ot)
    return db_ot

# Endpoint para ELIMINAR (opcional, pero buena práctica tenerlo si el frontend lo usa)
@router.delete("/{ot_id}")
def eliminar_orden(ot_id: int, session: Session = Depends(get_session)):
    db_ot = session.get(OrdenTrabajo, ot_id)
    if not db_ot:
        raise HTTPException(status_code=404, detail="Orden no encontrada")
    session.delete(db_ot)
    session.commit()
    return {"ok": True, "message": "Orden eliminada"}