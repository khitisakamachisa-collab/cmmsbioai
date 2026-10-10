# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Prueba integral del parche v1.1.1
==============================================
Valida sobre una BD TEMPORAL (no toca cmms_bioai.db):

  A. FIX 422:     PUT del lápiz acepta equipo_id (y sigue rechazando estado_id).
  B. R7 v1.1.1:   OT cerrada INMUTABLE — /reabrir eliminado; /reincidencia
                  crea una OT NUEVA vinculada (parent_ot_id, failure_sequence).
  C. v2.1.3:      estado 'En Monitoreo' ELIMINADO — /monitorear responde 404,
                  el lápiz sigue funcionando y el cierre es directo
                  En Proceso → Completada.
  D. R8:          repuestos del almacén y costos DENTRO del flujo
                  (reanudar/resolver) con validación de stock.
  E. Reportes:    /reportes/tiempos-etapa con reincidencias + /reportes/bitacora-csv
                  por OT y por EQUIPO.

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python prueba_flujo_v111.py

Salida esperada: lista de verificaciones "[OK]" y al final "OK ✓".
"""

import os
import sys
import tempfile

# ── Aislar la prueba: BD temporal (database.py crea sqlite en el cwd) ──
TMP_DIR = tempfile.mkdtemp(prefix="prueba_flujo_v111_")
os.chdir(TMP_DIR)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient  # noqa: E402
from sqlmodel import Session, select  # noqa: E402
from main import app  # noqa: E402

verificaciones = []


def check(nombre, condicion, extra=""):
    estado = "OK" if condicion else "FALLO"
    verificaciones.append(condicion)
    print(f"[{estado}] {nombre}" + (f"  → {extra}" if extra and not condicion else ""))


with TestClient(app) as client:

    # ── Catálogo de estados (v2.1.3: 5 estados, sin 'En Monitoreo') ──
    estados = client.get("/ordenes/estados/").json()
    est = {e["nombre_estado"]: e["id"] for e in estados}
    check("Catálogo v2.1.3: 5 estados y SIN 'En Monitoreo'",
          "En Monitoreo" not in est and len(est) == 5, str(list(est)))

    # ── Equipo, repuesto y usuarios de prueba (directo en la BD temporal) ──
    from database import engine
    from models.equipos import Equipo
    from models.repuestos import Repuesto
    from models.users import Usuario
    with Session(engine) as s:
        equipo = Equipo(nombre_corto="PRUEBA-V111", modelo="Test-111",
                        numero_serie="V111-TEST-001", marca="TestLab",
                        tipo_equipo="Bomba de Infusión", criticidad="Media")
        s.add(equipo)
        s.commit()
        s.refresh(equipo)
        equipo_id = equipo.id
        rep = Repuesto(nombre_repuesto="Kit de bobinas v111",
                       numero_material="KIT-V111", cantidad_disponible=5,
                       unidad_medida="unidad", nivel_stock_minimo=1)
        s.add(rep)
        s.commit()
        s.refresh(rep)
        rep_id = rep.id
        tech = s.exec(select(Usuario).where(Usuario.username == "tech")).first()
        tech_id = tech.id

    # ════════════════════════════════════════════════════════════
    # A. FIX 422 — el lápiz vuelve a funcionar
    # ════════════════════════════════════════════════════════════
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Correctivo",
        "descripcion_falla": "Falla base para el fix 422",
        "prioridad": "Alta"})
    check("Crear OT base → 200", r.status_code == 200, r.text)
    ot_a = r.json()
    ot_a_id = ot_a["id"]

    # Payload EXACTO del modal Editar del frontend (incluye equipo_id)
    r = client.put(f"/ordenes/{ot_a_id}", json={
        "equipo_id": equipo_id,
        "prioridad": "Urgente",
        "titulo": "Correctivo",
        "descripcion_falla": "Falla base editada (fix 422)",
        "tecnico_asignado_id": None,
        "unidad_tiempo": "horas",
        "tiempo_real_invertido": None,
        "acciones_realizadas": "",
        "fecha_creacion": "2026-10-02T10:00",
        "repuestos_utilizados": []})
    check("A-FIX 422: PUT del lápiz con equipo_id → 200 (ya no 422)", r.status_code == 200, r.text)
    check("A: edición aplicada (descripcion)", r.status_code == 200 and "fix 422" in r.json()["descripcion_falla"])
    check("A: edición aplicada (prioridad)", r.status_code == 200 and r.json()["prioridad"] == "Urgente")

    bit = client.get(f"/ordenes/{ot_a_id}/bitacora").json()
    check("A: edición queda en bitácora ('editada')", any(b["accion"] == "editada" for b in bit))

    # estado_id sigue prohibido por PUT (H2)
    r = client.put(f"/ordenes/{ot_a_id}", json={"estado_id": est["Completada"]})
    check("A-H2: PUT con estado_id sigue rechazado (422)", r.status_code == 422, r.text)

    # ════════════════════════════════════════════════════════════
    # B. Ciclo completo hasta cerrar la OT base
    # ════════════════════════════════════════════════════════════
    r = client.post(f"/ordenes/{ot_a_id}/asignar", json={"tecnico_asignado_id": tech_id, "usuario": "admin"})
    check("B: asignar técnico → 200", r.status_code == 200, r.text)
    r = client.post(f"/ordenes/{ot_a_id}/iniciar", json={"usuario": "tech"})
    check("B: iniciar → En Proceso", r.status_code == 200, r.text)
    r = client.post(f"/ordenes/{ot_a_id}/resolver", json={
        "acciones_realizadas": "Se reemplazó el capacitor de la placa base",
        "tiempo_real_invertido": 1.5, "unidad_tiempo": "horas", "usuario": "tech"})
    check("B: resolver → Completada", r.status_code == 200, r.text)
    ot_cerrada = r.json()

    # OT cerrada = inmutable
    r = client.put(f"/ordenes/{ot_a_id}", json={"prioridad": "Baja"})
    check("B-R7: PUT sobre OT Completada → 400 (solo lectura)", r.status_code == 400, r.text)

    # /reabrir fue ELIMINADO
    r = client.post(f"/ordenes/{ot_a_id}/reabrir", json={"comentario": "intento de reapertura"})
    check("B-R7: endpoint /reabrir eliminado (404/405)", r.status_code in (404, 405), str(r.status_code))

    # Reincidencia: motivo obligatorio
    r = client.post(f"/ordenes/{ot_a_id}/reincidencia", json={"comentario": "  "})
    check("B-R7: reincidencia sin motivo → 400", r.status_code == 400, r.text)

    # Reincidencia sobre OT NO cerrada → 400
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Correctivo", "descripcion_falla": "OT abierta auxiliar"})
    ot_aux_id = r.json()["id"]
    r = client.post(f"/ordenes/{ot_aux_id}/reincidencia", json={"comentario": "todavía abierta"})
    check("B-R7: reincidencia sobre OT abierta → 400", r.status_code == 400, r.text)

    # Reincidencia válida → OT NUEVA vinculada
    r = client.post(f"/ordenes/{ot_a_id}/reincidencia", json={
        "comentario": "Recae la misma falla: la placa volvió a fallar", "usuario": "admin"})
    check("B-R7: reincidencia → 200", r.status_code == 200, r.text)
    ot_b = r.json()
    ot_b_id = ot_b["id"]
    check("B-R7: OT nueva con ID distinto", ot_b_id != ot_a_id)
    check("B-R7: parent_ot_id = OT anterior", ot_b["parent_ot_id"] == ot_a_id)
    check("B-R7: failure_sequence = 2", ot_b["failure_sequence"] == 2)
    check("B-R1: reincidencia nace Abierta", ot_b["estado_id"] == est["Abierta"])
    check("B-R5: técnico heredado y fecha_asignacion fijada",
          ot_b["tecnico_asignado_id"] == tech_id and ot_b["fecha_asignacion"] is not None)
    check("B: descripción menciona la reincidencia", f"Reincidencia de OT #{ot_a_id}" in ot_b["descripcion_falla"])

    # La OT madre sigue cerrada e intacta
    madre = client.get(f"/ordenes/{ot_a_id}").json()
    check("B: la OT madre sigue Completada (inmutable)", madre["estado_id"] == est["Completada"])
    bit_madre = client.get(f"/ordenes/{ot_a_id}/bitacora").json()
    check("B: bitácora de la madre registra 'reincidencia'",
          any(b["accion"] == "reincidencia" and f"Generó OT #{ot_b_id}" in (b["comentario"] or "") for b in bit_madre))
    bit_hija = client.get(f"/ordenes/{ot_b_id}/bitacora").json()
    check("B: bitácora de la hija registra nacimiento por reincidencia",
          any(b["accion"] == "creada" and "Reincidencia de OT" in (b["comentario"] or "") for b in bit_hija))

    # Cadena: reincidencia de la reincidencia → secuencia 3
    client.post(f"/ordenes/{ot_b_id}/asignar", json={"tecnico_asignado_id": tech_id})
    client.post(f"/ordenes/{ot_b_id}/iniciar", json={})
    client.post(f"/ordenes/{ot_b_id}/resolver", json={
        "acciones_realizadas": "Segunda intervención", "tiempo_real_invertido": 1.0})
    r = client.post(f"/ordenes/{ot_b_id}/reincidencia", json={"comentario": "tercera vez", "usuario": "admin"})
    check("B-cadena: reincidencia de reincidencia → secuencia 3",
          r.status_code == 200 and r.json()["failure_sequence"] == 3 and r.json()["parent_ot_id"] == ot_b_id, r.text)
    ot_c_id = r.json()["id"]

    # ════════════════════════════════════════════════════════════
    # C. v2.1.3 — estado 'En Monitoreo' eliminado del sistema
    # ════════════════════════════════════════════════════════════
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Correctivo", "descripcion_falla": "OT para cierre directo"})
    ot_m_id = r.json()["id"]
    client.post(f"/ordenes/{ot_m_id}/asignar", json={"tecnico_asignado_id": tech_id})
    client.post(f"/ordenes/{ot_m_id}/iniciar", json={})

    # El endpoint /monitorear fue eliminado junto con el estado
    r = client.post(f"/ordenes/{ot_m_id}/monitorear", json={"usuario": "tech"})
    check("C-v2.1.3: /monitorear eliminado (404)", r.status_code == 404, str(r.status_code))

    # El intento NO dejó la OT a medias: sigue en En Proceso
    check("C-v2.1.3: la OT sigue en En Proceso tras el 404",
          client.get(f"/ordenes/{ot_m_id}").json()["estado_id"] == est["En Proceso"])

    # La OT activa sigue editable por lápiz (paridad con lo que hacía En Monitoreo)
    r = client.put(f"/ordenes/{ot_m_id}", json={"descripcion_falla": "OT activa, editada"})
    check("C-v2.1.3: OT en En Proceso sigue editable (PUT → 200)", r.status_code == 200, r.text)

    # Cierre directo sin pasar por monitoreo: En Proceso → Completada
    r = client.post(f"/ordenes/{ot_m_id}/resolver", json={
        "acciones_realizadas": "Intervención rápida, cierre directo",
        "tiempo_real_invertido": 0.5, "usuario": "tech"})
    check("C-v2.1.3: cierre directo En Proceso → Completada", r.status_code == 200 and r.json()["estado_id"] == est["Completada"], r.text)

    # ════════════════════════════════════════════════════════════
    # D. R8 — repuestos y costos DENTRO del flujo (reanudar/resolver)
    # ════════════════════════════════════════════════════════════
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Cambio de repuesto", "descripcion_falla": "OT para flujo con repuesto"})
    ot_r_id = r.json()["id"]
    client.post(f"/ordenes/{ot_r_id}/asignar", json={"tecnico_asignado_id": tech_id})
    client.post(f"/ordenes/{ot_r_id}/iniciar", json={})
    client.post(f"/ordenes/{ot_r_id}/pausar", json={"comentario": "espera kit de bobinas"})

    # Stock insuficiente: pedido 99 de 5 → 400 y el estado NO cambia
    r = client.post(f"/ordenes/{ot_r_id}/reanudar", json={
        "repuestos_utilizados": [{"repuesto_id": rep_id, "cantidad": 99}]})
    check("D-R8: stock insuficiente en reanudar → 400", r.status_code == 400, r.text)
    check("D-R8: el estado NO cambia si falla el stock", client.get(f"/ordenes/{ot_r_id}").json()["estado_id"] == est["Esp. Repuesto"])

    # Reanudar con repuesto válido (2 unidades) + costo
    r = client.post(f"/ordenes/{ot_r_id}/reanudar", json={
        "comentario": "llegó el kit",
        "repuestos_utilizados": [{"repuesto_id": rep_id, "cantidad": 2}],
        "costos_adicionales": [{"tipo_costo": "Transporte", "descripcion_costo": "Courier Santa Cruz", "monto_costo": 150.0}],
        "usuario": "tech"})
    check("D-R8: reanudar con repuesto+costo → 200", r.status_code == 200, r.text)
    check("D-R8: estado vuelve a En Proceso", r.json()["estado_id"] == est["En Proceso"])

    with Session(engine) as s:
        rep_db = s.get(Repuesto, rep_id)
        check("D-R8: stock descontado (5 → 3)", rep_db.cantidad_disponible == 3, f"stock={rep_db.cantidad_disponible}")
    detalle = client.get(f"/ordenes/{ot_r_id}").json()
    check("D-R8: repuesto ligado a la OT", any(u["repuesto_id"] == rep_id and u["cantidad_utilizada"] == 2
                                               for u in detalle["repuestos_usados"]), str(detalle["repuestos_usados"]))
    costos_ot = client.get(f"/costos/?orden_trabajo_id={ot_r_id}").json()
    check("D-R8: costo registrado en el flujo", any(c["monto_costo"] == 150.0 for c in costos_ot), str(costos_ot))
    bit_r = client.get(f"/ordenes/{ot_r_id}/bitacora").json()
    reanudada = next(b for b in bit_r if b["accion"] == "reanudada")
    check("D-R8: bitácora de reanudada menciona repuesto/costo",
          "Kit de bobinas" in (reanudada["comentario"] or "") and "150.0" in (reanudada["comentario"] or ""),
          reanudada["comentario"])

    # Resolver con repuesto final + stock exacto
    r = client.post(f"/ordenes/{ot_r_id}/resolver", json={
        "acciones_realizadas": "Kit instalado y calibrado", "tiempo_real_invertido": 2.0,
        "repuestos_utilizados": [{"repuesto_id": rep_id, "cantidad": 3}], "usuario": "tech"})
    check("D-R8: resolver con repuesto → 200", r.status_code == 200, r.text)
    with Session(engine) as s:
        rep_db = s.get(Repuesto, rep_id)
        check("D-R8: stock 3 → 0 tras resolver", rep_db.cantidad_disponible == 0, f"stock={rep_db.cantidad_disponible}")

    # ════════════════════════════════════════════════════════════
    # E. Reportes: reincidencias en tiempos-etapa + bitacora-csv
    # ════════════════════════════════════════════════════════════
    r = client.get("/reportes/tiempos-etapa").json()
    resumen = r["resumen"]
    check("E: resumen incluye n_reincidencias", "n_reincidencias" in resumen)
    check("E: resumen incluye tasa_reincidencia_pct", "tasa_reincidencia_pct" in resumen)
    check("E: n_reincidencias = 2 (OT #b y #c)", resumen["n_reincidencias"] == 2, str(resumen))
    fila_b = next((f for f in r["por_ot"] if f["ot_id"] == ot_b_id), None)
    check("E: por_ot incluye parent_ot_id y failure_sequence",
          fila_b is not None and fila_b["parent_ot_id"] == ot_a_id and fila_b["failure_sequence"] == 2)

    rcsv = client.get("/reportes/tiempos-etapa", params={"formato": "csv"})
    check("E: CSV tiempos-etapa → 200 text/csv", rcsv.status_code == 200 and "text/csv" in rcsv.headers.get("content-type", ""))
    check("E: CSV incluye columnas de reincidencia", "parent_ot_id" in rcsv.text and "failure_sequence" in rcsv.text)

    # Bitácora CSV por OT
    r = client.get("/reportes/bitacora-csv", params={"ot_id": ot_a_id})
    check("E: bitacora-csv por OT → 200", r.status_code == 200, r.text[:200])
    check("E: bitacora-csv OT contiene 'reincidencia'", "reincidencia" in r.text)
    check("E: cabecera CSV correcta", "fecha,ot_id,accion,usuario,estado_anterior,estado_nuevo,comentario" in r.text)

    # Bitácora CSV por EQUIPO (todas las OTs)
    r = client.get("/reportes/bitacora-csv", params={"equipo_id": equipo_id})
    check("E: bitacora-csv por EQUIPO → 200", r.status_code == 200, r.text[:200])
    check("E: bitácora de equipo incluye varias OTs",
          f",{ot_a_id}," in r.text and f",{ot_b_id}," in r.text and f",{ot_c_id}," in r.text)

    # Sin parámetros → 400
    r = client.get("/reportes/bitacora-csv")
    check("E: bitacora-csv sin parámetros → 400", r.status_code == 400, r.text)

    # ── Resultado final ──
    total = len(verificaciones)
    ok = sum(verificaciones)
    print("\n" + "=" * 60)
    print(f"RESULTADO: {ok}/{total} verificaciones OK")
    if ok == total:
        print("OK ✓ — parche v1.1.1 + v2.1.3 validados (fix 422, reincidencia, sin 'En Monitoreo', R8, reportes)")
    else:
        print("HAY FALLOS ✗ — revisar líneas [FALLO] arriba")
    # Limpieza de la carpeta temporal
    import shutil
    shutil.rmtree(TMP_DIR, ignore_errors=True)
    sys.exit(0 if ok == total else 1)
