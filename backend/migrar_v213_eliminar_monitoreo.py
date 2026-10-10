# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Migración v2.1.3: eliminar el estado de OT 'En Monitoreo'
=======================================================================
Runner manual de _migrate_eliminar_en_monitoreo() (database.py).

La migración TAMBIÉN corre automáticamente al arrancar el backend
(lifespan → create_db_and_tables), así que este script es OPCIONAL:
sirve para aplicarla a mano (o verificarla dos veces) y ver el reporte
sin levantar el servidor.

Qué hace (IDEMPOTENTE — puede correrse 2+ veces sin error):
  1. Toda OrdenTrabajo en 'En Monitoreo' pasa a 'Completada'
     (cierre automático). Sello R5: fecha_resolucion solo se fija si
     faltaba; pausa técnica abierta se cierra.
  2. Cada OT migrada recibe bitácora accion='cierre_automatico' con
     usuario='sistema'. El historial previo NO se borra ni se toca.
  3. El estado se elimina del catálogo estadoot (6 → 5 estados).
  4. NO toca el estado de EQUIPO 'En Monitoreo' (tabla estadoequipo,
     concepto IoT distinto y vigente).

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python migrar_v213_eliminar_monitoreo.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import _migrate_eliminar_en_monitoreo  # noqa: E402

if __name__ == "__main__":
    print("=" * 66)
    print("MIGRACIÓN v2.1.3 — eliminar estado de OT 'En Monitoreo'")
    print("=" * 66)
    _migrate_eliminar_en_monitoreo()
    print("-" * 66)
    print("Listo. Verificación sugerida:")
    print("  · GET /ordenes/estados/  → deben quedar 5 estados (sin 'En Monitoreo')")
    print("  · Bitácora de cada OT migrada → entrada accion='cierre_automatico'")
    print("Si no apareció ningún mensaje ✅, la BD ya estaba migrada (idempotente).")
