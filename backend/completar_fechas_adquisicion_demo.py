# -*- coding: utf-8 -*-
r"""
CMMS-BioAI — Completa fecha_adquisicion de los equipos del dataset v2.1
=======================================================================
(PATCH v2.1.2 — OPCIONAL, recomendado para la demo de la tesis)

¿Por qué? Sin fecha_adquisicion, la ventana calendario del motor de
métricas v2.1 arranca en la primera OT del equipo (fallback), lo que da
ventanas de pocos días y disponibilidad 0% en equipos cuyo MDT del
dataset supera esa ventana (Ecógrafo 270h, Resonancia 128h, Baja del
Desfibrilador 99h). Con fecha_adquisicion real la ventana pasa a ser de
meses/años y los indicadores muestran valores realistas (95-100%).

SEGURIDAD:
  - SOLO completa cuando fecha_adquisicion está VACÍA (nunca sobrescribe).
  - Solo toca los equipos del dataset v2.1 listados abajo.
  - Idempotente: puedes ejecutarlo las veces que quieras.
  - No crea ni borra equipos, OTs ni bitácora.

NOTA — Centrífuga Eppendorf queda excluida a propósito: su única OT del
dataset (111, Programado) fue creada el 2026-10-09 07:00; mientras no
entre en la ventana, asignarle fecha haría aparecer su fila sin OTs en
ventana. Asígnale fecha desde la UI a partir del 2026-10-09, o añádela
aquí más adelante. (Autoclave/Microscopio/Balanza/ECG sí se completan:
ninguna verificación depende de que su fila aparezca o no.)

Uso (Windows):
    cd D:\cmmsbioai\backend
    venv\Scripts\activate
    python completar_fechas_adquisicion_demo.py
"""
import os
import sys
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select

from database import engine
from models.equipos import Equipo

FECHAS_DEMO = {
    "Bomba de Infusión 1":      "2025-12-10",
    "Monitor Signos Vitales":   "2025-11-15",
    "Ecógrafo 4D":              "2024-08-20",
    "Equipo de Rayos X":        "2023-05-10",
    "Máquina de Hemodiálisis":  "2025-03-18",
    "Resonancia Magnética":     "2022-09-30",
    "Ventilador Mecánico":      "2025-08-12",
    "Desfibrilador Zoll":       "2025-12-01",
    "Autoclave Steris":         "2024-10-05",
    "Microscopio Olympus":      "2023-11-22",
    "Balanza Analítica":        "2025-06-08",
    "Electrocardiógrafo GE":    "2025-01-27",
}

print("=" * 66)
print("COMPLETAR fecha_adquisicion — equipos del dataset v2.1 (solo si está vacía)")
print("=" * 66)

cambios, sin_cambio, no_existe = [], [], []
with Session(engine) as s:
    for nombre, iso in FECHAS_DEMO.items():
        eq = s.exec(select(Equipo).where(Equipo.nombre_corto == nombre)).first()
        if eq is None:
            no_existe.append(nombre)
            continue
        if eq.fecha_adquisicion:
            sin_cambio.append((nombre, str(eq.fecha_adquisicion)))
            continue
        eq.fecha_adquisicion = date.fromisoformat(iso)
        cambios.append((nombre, iso))
    s.commit()

    print("\n● Asignadas ahora (%d):" % len(cambios))
    for nombre, iso in cambios:
        print(f"   {nombre:<28} → {iso}")
    print("\n● Ya tenían fecha, sin cambios (%d):" % len(sin_cambio))
    for nombre, f in sin_cambio:
        print(f"   {nombre:<28} → {f} (se conserva)")
    if no_existe:
        print("\n● No encontrados en la BD (%d):" % len(no_existe))
        for nombre in no_existe:
            print(f"   {nombre}")
    if not cambios:
        print("\nNada por hacer: todos los equipos ya tenían fecha_adquisicion ✓")

    # Tabla resultante con la ventana estimada del motor
    print("\n" + "-" * 66)
    print("VENTANA CALENDARIO resultante (fecha_adquisicion → hoy):")
    hoy = date.today()
    for eq in s.exec(select(Equipo)).all():
        if eq.fecha_adquisicion:
            dias = (hoy - eq.fecha_adquisicion).days
            print(f"   {eq.nombre_corto:<28} {eq.fecha_adquisicion}  ({max(dias,0)} días ≈ {max(dias,0)*24} h)")
        else:
            print(f"   {eq.nombre_corto:<28} (sin fecha → el motor usará la primera OT)")
    print("-" * 66)
    print("\nListo. Reinicia/actualiza /reportes/mtbf-mttr para ver las nuevas ventanas.")
