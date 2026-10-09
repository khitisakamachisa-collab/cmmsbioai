# -*- coding: utf-8 -*-
r"""
CMMS-BioAI — Diagnóstico del Motor de Métricas v2.1.2 (SOLO LECTURA)
====================================================================
Muestra, con la MISMA lógica del motor (v2.1.2), cómo se construye la
ventana calendario de cada equipo y qué OTs entran al cálculo, para
poder auditar MTBF / MTTR / Disponibilidad contra la BD real.

  - No modifica nada: solo lectura (como prueba_metricas_v21.py).
  - ventana_fuente: fecha_desde | fecha_adquisicion | primera_OT.
  - Si la ventana da 0 días (primera OT de HOY), el motor v2.1.2 usa
    PRECISIÓN HORARIA → la disponibilidad ya no se congela en None.

Uso:
    cd D:\cmmsbioai\backend
    venv\Scripts\activate
    python diagnostico_metricas_v21.py
"""
import os
import sys
from datetime import date, datetime, time, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select

from database import engine
from models import EstadoOT
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo
from api.routes.reportes import _es_programada, _mdt_horas

IDS_DATASET = set(range(101, 116))


def etiqueta(ot) -> str:
    return "[DATASET]" if ot.id in IDS_DATASET else "[TUYA   ]"


NOMBRE_ESTADO = {}


print("=" * 66)
print(f"DIAGNÓSTICO BD REAL — ventana del motor: hasta {date.today()}")
print("Motor v2.1.2: ventana con precisión horaria si es menor a 24h")
print("=" * 66)

with Session(engine) as s:
    estados = {e.id: e.nombre_estado for e in s.exec(select(EstadoOT)).all()}
    equipos = s.exec(select(Equipo)).all()
    ots_todas = s.exec(select(OrdenTrabajo)).all()
    hoy = date.today()

    for eq in sorted(equipos, key=lambda x: x.id):
        ots_eq = [o for o in ots_todas
                  if o.equipo_id == eq.id and o.fecha_creacion
                  and o.fecha_creacion.date() <= hoy]
        cerradas = [o for o in ots_eq if o.estado_id in (4, 5)]
        programadas = [o for o in cerradas if _es_programada(o)]
        candidatos = [o for o in cerradas if not _es_programada(o)]

        print(f"\n■ EQUIPO [{eq.id}] {eq.nombre_corto}")
        print(f"  fecha_adquisicion = {eq.fecha_adquisicion}")

        # — ventana de observación (espejo exacto del motor v2.1.2) —
        fechas_dt = [o.fecha_creacion for o in (candidatos + programadas) if o.fecha_creacion]
        fechas = [d.date() for d in fechas_dt]
        if eq.fecha_adquisicion:
            inicio, fuente = eq.fecha_adquisicion, "fecha_adquisicion"
        elif fechas:
            inicio, fuente = min(fechas), "primera_OT"
        else:
            print("  ventana: (sin datos → el equipo no aparece en el reporte)")
            continue
        dias = max((hoy - inicio).days, 0)
        if dias > 0:
            horas_cal = dias * 24.0
        else:
            fin_dt = datetime.combine(hoy, time.min) + timedelta(days=1)
            inicio_dt = min(fechas_dt) if (fuente == "primera_OT" and fechas_dt) else \
                (inicio if isinstance(inicio, datetime) else datetime.combine(inicio, time.min))
            horas_cal = max((fin_dt - inicio_dt).total_seconds() / 3600.0, 0.0)
        print(f"  ventana: fuente={fuente}  inicio={inicio}  dias={dias}"
              f"  horas_calendario={round(horas_cal, 1)}h")

        # — MDT válido / excluido (espejo del motor) —
        mdt_val = mdt_excl = 0.0
        for o in candidatos:
            m = _mdt_horas(o)
            if m is None:
                continue
            if o.mdt_excluido_disponibilidad:
                mdt_excl += m
            else:
                mdt_val += m
        disp = round(max(horas_cal - mdt_val, 0.0) / horas_cal * 100.0, 1) if horas_cal > 0 else \
            (0.0 if mdt_val > 0 else None)
        print(f"  MDT válido={round(mdt_val, 1)}h  excluido={round(mdt_excl, 1)}h"
              f"  → disponibilidad esperada = {disp}%")

        n_ds = sum(1 for o in candidatos if o.id in IDS_DATASET)
        n_ty = len(candidatos) - n_ds
        print(f"  OTs que entran al cálculo (cerradas 4/5, no programadas, en ventana):"
              f" {len(candidatos)}  [dataset: {n_ds} | tuyas: {n_ty}]"
              + (f"  (+{len(programadas)} programadas que también delimitan la ventana)"
                 if programadas else ""))

        for ot in sorted(cerradas, key=lambda x: x.fecha_creacion):
            print(f"    OT {ot.id:>4} {etiqueta(ot)} {estados.get(ot.estado_id, ot.estado_id):<11}"
                  f" creada {ot.fecha_creacion:%Y-%m-%d %H:%M}  '{ot.titulo}'")
            print(f"             banderas: garantia={bool(ot.ventana_garantia_reparacion)}"
                  f" exclMTTR={bool(ot.excluida_de_MTTR)}"
                  f" exclMDT={bool(ot.mdt_excluido_disponibilidad)}"
                  f" pausa={float(ot.tiempo_pausa_acumulado or 0.0)}h")

print("\n" + "=" * 66)
print("LECTURA ESPERADA (motor v2.1.2):")
print("  • Ningún equipo con OTs en ventana muestra horas_calendario = 0h:")
print("    si la primera OT es de HOY, la ventana usa precisión horaria.")
print("  • Si ventana_fuente = primera_OT y la ventana es corta, es NORMAL")
print("    que la disponibilidad salga 0% cuando el MDT supera la ventana")
print("    (p.ej. la Baja del Desfibrilador: 99h de MDT vs. unas pocas h).")
print("  • Para ventanas realistas (meses/años) y valores de demo, ejecuta:")
print("        python completar_fechas_adquisicion_demo.py")
print("  • La prueba completa sigue siendo: python prueba_metricas_v21.py")
print("=" * 66)
