# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Prueba del Motor de Métricas v2.1 (/reportes)
==========================================================
Valida sobre la BD REAL (la misma de importar_dataset_v21.py; NO la
modifica) que MTBF / MTTR / Disponibilidad apliquen las Reglas de
Negocio v2.1 con el dataset de prueba importado:

  1. MTBF excluye reincidencias (OT 102: ventana_garantia_reparacion
     =True no cuenta como falla nueva en el denominador).
  2. MTTR excluye cierres administrativos (OT 108: excluida_de_MTTR
     =True no infla el promedio).
  3. Disponibilidad ignora falsas alarmas (OT 103/104:
     mdt_excluido_disponibilidad=True no resta disponibilidad).
  4. Baja_Equipo (OT 110) SÍ suma MDT, pero nunca entra al MTTR.
  5. MTTR usa horas ACTIVAS (OT 106: pausa 4h descontada; OT 105:
     logística 267.5h no infla la eficiencia del técnico).
  6. La reincidencia (OT 102) SÍ cuenta en MTTR (solo sale de MTBF).
  7. /reportes/tiempos-etapa conserva el desglose de pausas/logística.
  8. Aliases /reportes/mtbf, /reportes/mttr, /reportes/disponibilidad.

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python prueba_metricas_v21.py

Requisito previo: python importar_dataset_v21.py  (dataset v2.1 en BD)
"""

import os
import sys

# ⚠️ SIN chdir: esta prueba corre contra la BD real (backend/cmms_bioai.db)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import Session, select

from main import app
from database import engine
from models.ordenes import OrdenTrabajo

verificaciones = []


def check(nombre, condicion, extra=""):
    estado = "OK" if condicion else "FALLO"
    verificaciones.append(condicion)
    print(f"[{estado}] {nombre}" + (f"  → {extra}" if extra and not condicion else ""))
    return bool(condicion)


def seccion(titulo, condiciones):
    """Imprime el veredicto ✅/❌ de una sección y lo registra."""
    ok = all(bool(c) for c in condiciones)
    verificaciones.append(ok)
    print(("✅ " if ok else "❌ ") + titulo)
    return ok


def cerca(a, b, tol=0.06):
    return a is not None and b is not None and abs(float(a) - float(b)) <= tol


# ── 0. Dataset presente en la BD real ─────────────────────────────
IDS_DATASET = list(range(101, 116))
with Session(engine) as s:
    ots = {ot.id: ot for ot in s.exec(
        select(OrdenTrabajo).where(OrdenTrabajo.id.in_(IDS_DATASET))).all()}
faltan = [i for i in IDS_DATASET if i not in ots]
if faltan:
    print(f"✗ No se encontraron las OTs del dataset v2.1 (faltan: {faltan})")
    print("  Ejecuta primero:  python importar_dataset_v21.py")
    sys.exit(1)

hoy = date.today()


def en_ventana(ot):
    """Mismo filtro de ventana que aplica el endpoint (hasta hoy)."""
    return bool(ot.fecha_creacion) and ot.fecha_creacion.date() <= hoy


def es_programada(ot):
    return ot.orden_preventiva_id is not None or (ot.tipo_origen_ot or "Usuario") == "Programado"


def fila_de(resp, ot):
    return next((r for r in resp["por_equipo"] if r["equipo_id"] == ot.equipo_id), None)


def correctivas_de(equipo_id, estado_id=4):
    with Session(engine) as s:
        return [o for o in s.exec(select(OrdenTrabajo).where(
            OrdenTrabajo.equipo_id == equipo_id,
            OrdenTrabajo.estado_id == estado_id)).all()
            if en_ventana(o) and not es_programada(o)]


print("=" * 62)
print("PRUEBA MOTOR DE MÉTRICAS v2.1 — dataset de prueba (OTs 101-115)")
print("=" * 62)

with TestClient(app) as client:

    # ── 1. MTBF excluye reincidencias (Regla 3) ──────────────────
    r = client.get("/reportes/mtbf-mttr")
    check("GET /reportes/mtbf-mttr → 200", r.status_code == 200)
    d = r.json()
    fila_bomba = fila_de(d, ots[102])
    correctivas_bomba = correctivas_de(ots[102].equipo_id)
    esperado_raw = len(correctivas_bomba)
    esperado_gar = sum(1 for o in correctivas_bomba if o.ventana_garantia_reparacion)
    c1 = []
    c1.append(check("Bomba: n_fallas_correctivas = %s (101+102 en ventana)" % esperado_raw,
                    fila_bomba is not None and fila_bomba["n_fallas_correctivas"] == esperado_raw))
    c1.append(check("Bomba: n_excluidas_garantia = %s (OT 102 reincidencia <72h)" % esperado_gar,
                    fila_bomba is not None and fila_bomba["n_excluidas_garantia"] == esperado_gar and esperado_gar >= 1))
    c1.append(check("Bomba: n_fallas_reales = %s (denominador MTBF sin la 102)" % (esperado_raw - esperado_gar),
                    fila_bomba is not None and fila_bomba["n_fallas_reales"] == esperado_raw - esperado_gar))
    c1.append(check("Bomba: advertencia_mtbf presente (fallas reales < 3)",
                    fila_bomba is not None and fila_bomba["advertencia_mtbf"] is not None
                    and "mínimo recomendado: 3" in fila_bomba["advertencia_mtbf"]))
    seccion("MTBF excluye reincidencias", c1)

    # ── 6. La reincidencia SÍ cuenta en MTTR (solo sale de MTBF) ─
    c6 = []
    c6.append(check("Bomba: MTTR = 1.5h ((1.5+1.5)/2, la 102 SÍ aporta activas)",
                    fila_bomba is not None and cerca(fila_bomba["mttr_horas"], 1.5)))
    c6.append(check("Bomba: horas_reparacion_activas = 3.0h",
                    fila_bomba is not None and cerca(fila_bomba["horas_reparacion_activas"], 3.0)))
    seccion("Reincidencia en ventana de garantía SÍ cuenta en MTTR", c6)

    # ── 2. MTTR excluye cierres administrativos (Regla 6) ────────
    fila_res = fila_de(d, ots[108])
    validas_res = [o for o in correctivas_de(ots[108].equipo_id) if not o.excluida_de_MTTR]
    # Suma espejo (sin bitácora: OTs sin pausas → activas = brutas − pausa declarada)
    esperado_act = sum(max(((o.fecha_resolucion - o.fecha_inicio_trabajo).total_seconds() / 3600.0
                            if o.fecha_resolucion and o.fecha_inicio_trabajo else
                            (o.tiempo_real_invertido or 0.0))
                           - (o.tiempo_pausa_acumulado or 0.0), 0.0) for o in validas_res)
    c2 = []
    c2.append(check("Resonancia: n_excluidas_mttr >= 1 (OT 108 cierre administrativo)",
                    fila_res is not None and fila_res["n_excluidas_mttr"] >= 1))
    c2.append(check("Resonancia: n_validas_mttr = %d (denominador MTTR)" % len(validas_res),
                    fila_res is not None and fila_res["n_validas_mttr"] == len(validas_res)))
    c2.append(check("Resonancia: activas sumadas = %.1fh (las 122h de la 108 NO entran)" % esperado_act,
                    fila_res is not None and cerca(fila_res["horas_reparacion_activas"], esperado_act)
                    and fila_res["horas_reparacion_activas"] < 122.0))
    c2.append(check("Resonancia: MTTR no inflado por cierre administrativo",
                    fila_res is not None and (fila_res["mttr_horas"] is None or
                                              fila_res["mttr_horas"] < 122.0)))
    seccion("MTTR excluye cierres admin", c2)

    # ── 3. Disponibilidad ignora falsas alarmas (Regla 4) ────────
    fila_mon = fila_de(d, ots[104])
    mon_cand = correctivas_de(ots[104].equipo_id, estado_id=4) + \
               correctivas_de(ots[104].equipo_id, estado_id=5)
    esperado_mdt_ok = sum((o.fecha_resolucion - o.fecha_creacion).total_seconds() / 3600.0
                          for o in mon_cand
                          if not o.mdt_excluido_disponibilidad and o.fecha_resolucion)
    esperado_mdt_excl = sum((o.fecha_resolucion - o.fecha_creacion).total_seconds() / 3600.0
                            for o in mon_cand
                            if o.mdt_excluido_disponibilidad and o.fecha_resolucion)
    c3 = []
    c3.append(check("Monitor: MDT válido = %.2fh (la falsa alarma 103 y el error de usuario 104 no restan)" % esperado_mdt_ok,
                    fila_mon is not None and cerca(fila_mon["mdt_valido_horas"], esperado_mdt_ok)))
    c3.append(check("Monitor: MDT excluido reportado = %.2fh (OT 104)" % esperado_mdt_excl,
                    fila_mon is not None and cerca(fila_mon["mdt_excluido_horas"], esperado_mdt_excl)))
    c3.append(check("Monitor: disponibilidad = 100.0% (sin downtime válido)",
                    fila_mon is not None and fila_mon["disponibilidad_pct"] == 100.0))
    seccion("Disponibilidad ignora falsas alarmas", c3)

    # ── 4. Baja_Equipo SÍ suma MDT, nunca MTTR ───────────────────
    fila_des = fila_de(d, ots[110])
    c4 = []
    c4.append(check("Desfibrilador: MDT de la baja SÍ suma = 99.0h (OT 110)",
                    fila_des is not None and cerca(fila_des["mdt_valido_horas"], 99.0)))
    c4.append(check("Desfibrilador: no entra al MTTR (cancelada, n_validas_mttr = 0)",
                    fila_des is not None and fila_des["n_validas_mttr"] == 0
                    and fila_des["mttr_horas"] is None))
    c4.append(check("Desfibrilador: disponibilidad < 100% (el equipo sí estuvo fuera)",
                    fila_des is not None and fila_des["disponibilidad_pct"] is not None
                    and fila_des["disponibilidad_pct"] < 100.0))
    seccion("Baja_Equipo suma MDT pero no MTTR", c4)

    # ── 5. MTTR usa horas activas (Reglas 11-14) ─────────────────
    fila_rayos = fila_de(d, ots[106])
    fila_eco = fila_de(d, ots[105])
    c5 = []
    c5.append(check("Rayos X: activas = 2.5h (brutas 6.5 − pausa 4.0)",
                    fila_rayos is not None and cerca(fila_rayos["horas_reparacion_activas"], 2.5)
                    and cerca(fila_rayos["mttr_horas"], 2.5)))
    c5.append(check("Ecógrafo: MTTR = 0.0h (logística 267.5h NO infla la eficiencia)",
                    fila_eco is not None and cerca(fila_eco["mttr_horas"], 0.0)
                    and cerca(fila_eco["horas_reparacion_activas"], 0.0)))
    seccion("MTTR usa horas activas (pausas y logística descontadas)", c5)

    # ── Extra: OT 111 programada no es falla ─────────────────────
    fila_cen = fila_de(d, ots[111])
    check("Centrífuga: OT 111 (Programado) no cuenta como falla correctiva",
          fila_cen is None or (fila_cen["n_fallas_correctivas"] == 0 and fila_cen["n_programadas"] >= 1))

    # ── 7. tiempos-etapa conserva desglose de pausas y logística ─
    rt = client.get("/reportes/tiempos-etapa")
    check("GET /reportes/tiempos-etapa → 200", rt.status_code == 200)
    por_ot = {p["ot_id"]: p for p in rt.json()["por_ot"]}
    c7 = []
    c7.append(check("OT 105: espera repuestos = 267.5h, activas = 0.0h",
                    105 in por_ot and cerca(por_ot[105]["horas_espera_repuesto"], 267.5)
                    and cerca(por_ot[105]["horas_reparacion_activas"], 0.0)))
    c7.append(check("OT 106: espera (pausa técnica) = 4.0h, activas = 2.5h",
                    106 in por_ot and cerca(por_ot[106]["horas_espera_repuesto"], 4.0)
                    and cerca(por_ot[106]["horas_reparacion_activas"], 2.5)))
    c7.append(check("OT 108: activas = 122.0h (cierre admin visible en desglose)",
                    108 in por_ot and cerca(por_ot[108]["horas_reparacion_activas"], 122.0)))
    c7.append(check("Banderas v2.1 visibles en por_ot (ventana_garantia en OT 102)",
                    102 in por_ot and por_ot[102]["ventana_garantia_reparacion"] is True))
    rcsv = client.get("/reportes/tiempos-etapa", params={"formato": "csv"})
    c7.append(check("CSV tiempos-etapa → 200 text/csv", rcsv.status_code == 200
                    and "text/csv" in rcsv.headers.get("content-type", "")))
    seccion("tiempos-etapa conserva desglose de pausas y logística", c7)

    # ── 8. Aliases /mtbf, /mttr, /disponibilidad ─────────────────
    c8 = []
    for ruta in ("/reportes/mtbf", "/reportes/mttr", "/reportes/disponibilidad"):
        ra = client.get(ruta)
        mismo = (ra.status_code == 200 and
                 next((x for x in ra.json()["por_equipo"] if x["equipo_id"] == ots[102].equipo_id), {})
                 .get("n_fallas_reales") == (fila_bomba or {}).get("n_fallas_reales"))
        c8.append(check("Alias %s → 200 con payload v2.1 coherente" % ruta, mismo))
    seccion("Aliases /mtbf, /mttr, /disponibilidad operativos", c8)

# ── Resumen ───────────────────────────────────────────────────────
n_ok = sum(1 for v in verificaciones if v)
n_tot = len(verificaciones)
print("=" * 62)
print("RESULTADO: %d/%d verificaciones OK" % (n_ok, n_tot))
if n_ok == n_tot:
    print("OK ✓ — motor de métricas v2.1 validado (MTBF/MTTR/Disponibilidad)")
    sys.exit(0)
print("✗ Hay verificaciones fallidas — revisar arriba")
sys.exit(1)
