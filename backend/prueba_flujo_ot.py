# -*- coding: utf-8 -*-
"""
HISTÓRICO v1.1.0 — NO EJECUTAR
==============================
Este script está roto tras v1.1.1: llama al endpoint /reabrir,
que fue ELIMINADO y sustituido por /reincidencia (cierre
definitivo + OT nueva vinculada). La batería canónica vigente es:
    python prueba_flujo_v111.py   (51 verificaciones)

Se conserva solo como referencia histórica de la era v1.1.0.
-----------------------------------------------------------------
CMMS-BioAI — Prueba integral del Flujo de Trabajo OT (v1.1.0)
=============================================================
Valida las reglas R1–R7 y los endpoints de acción sobre una base
de datos TEMPORAL (carpeta temporal del sistema). NO toca la
base de datos real cmms_bioai.db, por lo que puede ejecutarse
sin miedo en cualquier momento.

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python prueba_flujo_ot.py

Salida esperada: lista de verificaciones "[OK]" y al final "OK ✓".
"""

import os
import sys
import shutil
import tempfile

# ── Aislar la prueba: BD temporal (database.py crea sqlite en el cwd) ──
TMP_DIR = tempfile.mkdtemp(prefix="prueba_flujo_ot_")
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

    # ── Catálogo de estados ──
    estados = client.get("/ordenes/estados/").json()
    est = {e["nombre_estado"]: e["id"] for e in estados}
    check("Catálogo de 5 estados presente", all(k in est for k in
          ["Abierta", "En Proceso", "Esp. Repuesto", "Completada", "Cancelada"]), str(est))

    # ── Equipo y usuarios de prueba (directo en la BD temporal) ──
    from database import engine
    from sqlmodel import Session
    from models.equipos import Equipo
    from models.users import Usuario
    with Session(engine) as s:
        equipo = Equipo(nombre_corto="PRUEBA-FLUJO", modelo="Test-100",
                        numero_serie="FLUJO-TEST-001", marca="TestLab",
                        tipo_equipo="Bomba de Infusión", criticidad="Media")
        s.add(equipo)
        s.commit()
        s.refresh(equipo)
        equipo_id = equipo.id
        tech = s.exec(select(Usuario).where(Usuario.username == "tech")).first()
        admin = s.exec(select(Usuario).where(Usuario.username == "admin")).first()
        tech_id, admin_id = tech.id, admin.id

    # ── R1: no se puede crear la OT en otro estado ──
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Correctivo", "descripcion_falla": "Test R1",
        "estado_id": est["Completada"]})
    check("R1: rechaza crear OT directamente en 'Completada' (400)", r.status_code == 400, r.text)

    # ── R1: la OT nace Abierta aunque no se envíe estado ──
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Correctivo",
        "descripcion_falla": "Falla de prueba del flujo completo",
        "prioridad": "Alta", "fecha_vencimiento": "2026-12-31"})
    check("R1: crear OT sin estado → 200", r.status_code == 200, r.text)
    ot = r.json()
    ot_id = ot["id"]
    check("R1: OT nace en estado 'Abierta'", ot["estado_id"] == est["Abierta"])
    check("R5: OT nueva sin fecha_asignacion", ot["fecha_asignacion"] is None)
    check("H6: fecha_vencimiento aceptada y devuelta", ot["fecha_vencimiento"] == "2026-12-31")

    # ── Bitácora de nacimiento (R4) ──
    bit = client.get(f"/ordenes/{ot_id}/bitacora").json()
    check("R4: bitácora registra 'creada'", any(b["accion"] == "creada" for b in bit))

    # ── No se puede iniciar sin técnico ──
    r = client.post(f"/ordenes/{ot_id}/iniciar", json={})
    check("Flujo: iniciar sin técnico → 400", r.status_code == 400, r.text)

    # ── Asignar técnico (R5) ──
    r = client.post(f"/ordenes/{ot_id}/asignar",
                    json={"tecnico_asignado_id": tech_id, "usuario": "admin"})
    check("Flujo: asignar técnico → 200", r.status_code == 200, r.text)
    check("R5: fecha_asignacion fijada al asignar", r.json()["fecha_asignacion"] is not None)

    # ── Iniciar trabajo (R2) ──
    r = client.post(f"/ordenes/{ot_id}/iniciar", json={"usuario": "tech"})
    check("Flujo: iniciar → 'En Proceso'", r.status_code == 200 and
          r.json()["estado_id"] == est["En Proceso"], r.text)
    check("R5: fecha_inicio_trabajo fijada", r.json()["fecha_inicio_trabajo"] is not None)

    # ── Pausar sin motivo → 400; con motivo → Esp. Repuesto ──
    r = client.post(f"/ordenes/{ot_id}/pausar", json={"comentario": ""})
    check("Flujo: pausar sin motivo → 400", r.status_code == 400, r.text)
    r = client.post(f"/ordenes/{ot_id}/pausar",
                    json={"comentario": "Espera repuesto: kit de bobinas", "usuario": "tech"})
    check("Flujo: pausar → 'Esp. Repuesto'", r.status_code == 200 and
          r.json()["estado_id"] == est["Esp. Repuesto"], r.text)

    # ── R2: transiciones inválidas ──
    r = client.post(f"/ordenes/{ot_id}/iniciar", json={})
    check("R2: 'Esp. Repuesto' no puede pasar a 'En Proceso' vía iniciar → 400", r.status_code == 400, r.text)
    r = client.post(f"/ordenes/{ot_id}/resolver",
                    json={"acciones_realizadas": "x", "tiempo_real_invertido": 1})
    check("R2: resolver desde 'Esp. Repuesto' → 400", r.status_code == 400, r.text)

    # ── Reanudar ──
    r = client.post(f"/ordenes/{ot_id}/reanudar", json={"usuario": "tech"})
    check("Flujo: reanudar → 'En Proceso'", r.status_code == 200 and
          r.json()["estado_id"] == est["En Proceso"], r.text)

    # ── R3: resolver exige los datos de cierre ──
    r = client.post(f"/ordenes/{ot_id}/resolver",
                    json={"acciones_realizadas": "   ", "tiempo_real_invertido": 2})
    check("R3: resolver sin 'acciones_realizadas' → 400", r.status_code == 400, r.text)
    r = client.post(f"/ordenes/{ot_id}/resolver",
                    json={"acciones_realizadas": "Cambio de bobina", "tiempo_real_invertido": 0})
    check("R3: resolver con tiempo 0 → 400", r.status_code == 400, r.text)
    r = client.post(f"/ordenes/{ot_id}/resolver",
                    json={"acciones_realizadas": "Cambio de bobina y calibración",
                          "tiempo_real_invertido": 2.5, "unidad_tiempo": "horas",
                          "usuario": "tech"})
    check("R3: resolver completo → 'Completada'", r.status_code == 200 and
          r.json()["estado_id"] == est["Completada"], r.text)
    check("R5: fecha_resolucion fijada al resolver", r.json()["fecha_resolucion"] is not None)

    # ── H2: OT cerrada es solo lectura por PUT ──
    r = client.put(f"/ordenes/{ot_id}", json={"titulo": "Cambio"})
    check("H2: PUT sobre OT Completada → 400 (solo lectura)", r.status_code == 400, r.text)

    # ── R7: reabrir exige comentario ──
    r = client.post(f"/ordenes/{ot_id}/reabrir", json={"comentario": ""})
    check("R7: reabrir sin comentario → 400", r.status_code == 400, r.text)
    r = client.post(f"/ordenes/{ot_id}/reabrir",
                    json={"comentario": "La falla persiste tras la reparación", "usuario": "admin"})
    check("R7: reabrir con comentario → 'En Proceso'", r.status_code == 200 and
          r.json()["estado_id"] == est["En Proceso"], r.text)

    # ── Cancelar con motivo, reabrir → Abierta, cancelar de nuevo ──
    r = client.post(f"/ordenes/{ot_id}/cancelar",
                    json={"comentario": "Equipo dado de baja", "usuario": "admin"})
    check("Flujo: cancelar con motivo → 'Cancelada'", r.status_code == 200 and
          r.json()["estado_id"] == est["Cancelada"], r.text)
    r = client.post(f"/ordenes/{ot_id}/reabrir",
                    json={"comentario": "Se reactiva el equipo", "usuario": "admin"})
    check("R7: reabrir Cancelada → 'Abierta'", r.status_code == 200 and
          r.json()["estado_id"] == est["Abierta"], r.text)
    client.post(f"/ordenes/{ot_id}/cancelar", json={"comentario": "Cierre final de prueba"})

    # ── H2: PUT ya no acepta estado_id (extra="forbid") ──
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Inspección",
        "descripcion_falla": "Segunda OT para probar PUT"})
    ot2_id = r.json()["id"]
    r = client.put(f"/ordenes/{ot2_id}", json={
        "estado_id": est["Completada"], "titulo": "Inspección"})
    check("H2: PUT con estado_id → 422 (extra prohibido)", r.status_code == 422, r.text)
    r = client.put(f"/ordenes/{ot2_id}?usuario=admin", json={"prioridad": "Urgente"})
    check("H2: PUT sin estado → 200 (edición normal)", r.status_code == 200, r.text)
    bit2 = client.get(f"/ordenes/{ot2_id}/bitacora").json()
    check("R4: PUT registra 'editada' en bitácora", any(b["accion"] == "editada" for b in bit2))

    # ── Asignación en la creación fija sello R5 ──
    r = client.post("/ordenes/", json={
        "equipo_id": equipo_id, "titulo": "Correctivo",
        "descripcion_falla": "OT con técnico desde la creación",
        "tecnico_asignado_id": tech_id})
    ot3 = r.json()
    check("R5: asignar en creación fija fecha_asignacion", ot3["fecha_asignacion"] is not None)
    bit3 = client.get(f"/ordenes/{ot3['id']}/bitacora").json()
    check("R4: bitácora 'creada' + 'asignada' en creación",
          {b["accion"] for b in bit3} >= {"creada", "asignada"})
    client.post(f"/ordenes/{ot3['id']}/cancelar", json={"comentario": "Limpieza de prueba"})

    # ── Bitácora completa de la OT principal ──
    bit = client.get(f"/ordenes/{ot_id}/bitacora").json()
    acciones = [b["accion"] for b in bit]
    esperadas = {"creada", "asignada", "iniciada", "pausada", "reanudada",
                 "resuelta", "reabierta", "cancelada"}
    check("R4: bitácora completa del ciclo de vida", esperadas.issubset(set(acciones)), str(acciones))

    # ── KPIs /reportes/tiempos-etapa ──
    r = client.get("/reportes/tiempos-etapa")
    check("KPIs: GET /reportes/tiempos-etapa → 200", r.status_code == 200, r.text[:200])
    resumen = r.json()["resumen"]
    check("KPIs: MTTA calculado (registrado, ≥0 — en prueba ≈0 por ser instantáneo)",
          resumen["mtta_horas"] is not None and resumen["mtta_horas"] >= 0, str(resumen))
    check("KPIs: reparación bruta ≥ reparación activa (hubo espera de repuesto)",
          (resumen["reparacion_bruta_horas"] or 0) >= (resumen["reparacion_activa_horas"] or 0))
    check("KPIs: tasa de cancelación registrada", resumen["tasa_cancelacion_pct"] is not None)

    r = client.get("/reportes/tiempos-etapa?formato=csv")
    check("KPIs: exportación CSV → 200 text/csv",
          r.status_code == 200 and "text/csv" in r.headers.get("content-type", ""))

# ── Limpieza de la carpeta temporal ──
shutil.rmtree(TMP_DIR, ignore_errors=True)

print("-" * 60)
if all(verificaciones):
    print(f"OK ✓  ({len(verificaciones)} verificaciones pasaron)")
    print("El flujo de trabajo OT v1.1.0 funciona correctamente.")
    sys.exit(0)
else:
    fallos = verificaciones.count(False)
    print(f"FALLO: {fallos} verificación(es) fallaron — revisar arriba.")
    sys.exit(1)
