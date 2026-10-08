"""
Limpieza UNIQUE: elimina de la base de datos los equipos/OTs de prueba
creados por una versión anterior de prueba_mtbf.py (seriales MTBF-001 y
MTBF-002), para que no contaminen los indicadores MTBF/MTTR del Cap. IV.

Uso (desde D:\\cmmsbioai\\backend):
    python limpiar_datos_prueba.py
"""
import sys
sys.path.insert(0, ".")

from sqlmodel import Session, select
from database import engine
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo
from models.preventivo import TareaPreventiva

SERIALES_PRUEBA = ("MTBF-001", "MTBF-002")

with Session(engine) as s:
    equipos = s.exec(select(Equipo).where(Equipo.numero_serie.in_(SERIALES_PRUEBA))).all()
    if not equipos:
        print("No hay equipos de prueba (MTBF-001 / MTBF-002) en la BD. Nada que hacer.")
        sys.exit(0)

    ids = [e.id for e in equipos]
    print("Equipos de prueba encontrados:")
    for e in equipos:
        print(f"  id={e.id}  {e.nombre_corto}  (serie {e.numero_serie})")

    n_ot = n_tp = 0
    # 1) OTs asociadas (hijas primero, para respetar integridad referencial)
    for ot in s.exec(select(OrdenTrabajo).where(OrdenTrabajo.equipo_id.in_(ids))).all():
        s.delete(ot)
        n_ot += 1
    # 2) Tareas preventivas asociadas
    for tp in s.exec(select(TareaPreventiva).where(TareaPreventiva.equipo_id.in_(ids))).all():
        s.delete(tp)
        n_tp += 1
    # 3) Equipos de prueba
    for e in equipos:
        s.delete(e)

    s.commit()
    print(f"\nLimpieza OK: {len(equipos)} equipos, {n_ot} OTs y {n_tp} tareas "
          f"preventivas de prueba eliminados. La BD quedó lista para datos reales.")
