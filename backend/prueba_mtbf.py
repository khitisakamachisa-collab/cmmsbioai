"""Prueba del endpoint /reportes/mtbf-mttr (JSON + CSV)."""
import sys
sys.path.insert(0, ".")
from datetime import datetime, date, timedelta

from fastapi.testclient import TestClient
from main import app
from database import engine
from sqlmodel import Session, select
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo
from models.preventivo import TareaPreventiva

with TestClient(app) as c:  # crea BD + seed
    # 1. Crear 2 equipos vía API
    r1 = c.post("/equipos/", json={
        "nombre_corto": "Bomba Test UCI", "modelo": "Infusomat", "numero_serie": "MTBF-001",
        "marca": "B.Braun", "fecha_adquisicion": "2024-01-10", "criticidad": "Alta",
        "tipo_equipo": "Bomba de Infusión", "ubicacion_actual": "UCI"})
    r2 = c.post("/equipos/", json={
        "nombre_corto": "Monitor Test P3", "modelo": "SVM-8000", "numero_serie": "MTBF-002",
        "marca": "Siemens", "criticidad": "Media", "tipo_equipo": "Monitor",
        "ubicacion_actual": "Piso 3"})
    print("Creación equipos:", r1.status_code, r2.status_code)
    eq_id = r1.json().get("id")
    eq2_id = r2.json().get("id")

    # 2. Insertar correctivas completadas con tiempos (vía sesión)
    with Session(engine) as s:
        hoy = datetime.now()
        datos = [
            (eq_id, 200, "Oclusion de linea", 2.5, "horas"),
            (eq_id, 120, "No carga bateria", 1.0, "horas"),
            (eq_id, 40,  "Deriva de flujo",  1.5, "dias"),
            (eq2_id, 60, "Pantalla parpadea", 0.5, "horas"),
        ]
        for eid, dias, titulo, tiempo, unidad in datos:
            s.add(OrdenTrabajo(
                equipo_id=eid, titulo=titulo, descripcion_falla=titulo,
                prioridad="Alta", estado_id=4,
                fecha_creacion=hoy - timedelta(days=dias),
                tiempo_real_invertido=tiempo, unidad_tiempo=unidad))
        # Una preventiva completada, VINCULADA a su tarea preventiva
        # (con orden_preventiva_id → el sistema NO debe contarla como falla)
        tarea = TareaPreventiva(equipo_id=eq_id, titulo="Preventivo trimestral",
                                frecuencia_dias=90, proxima_fecha=hoy.date())
        s.add(tarea)
        s.commit()
        s.refresh(tarea)
        s.add(OrdenTrabajo(
            equipo_id=eq_id, titulo="Preventivo trimestral", descripcion_falla="preventivo",
            prioridad="Media", estado_id=4, fecha_creacion=hoy - timedelta(days=90),
            tiempo_real_invertido=2.0, unidad_tiempo="horas",
            orden_preventiva_id=tarea.id))
        s.commit()
        print("4 correctivas + 1 preventiva (vinculada a tarea preventiva) insertadas")

    # 3. JSON
    r = c.get("/reportes/mtbf-mttr")
    d = r.json()
    print("\n== JSON:", r.status_code)
    for row in d["por_equipo"][:4]:
        print(f"  EQ {row['nombre_corto']} [{row['tipo_equipo']}]: fallas={row['n_fallas_correctivas']}"
              f" h_rep={row['horas_reparacion']} MTBF={row['mtbf_horas']}h"
              f" MTTR={row['mttr_horas']}h Disp={row['disponibilidad_pct']}%")
    for t in d["por_tipo_equipo"]:
        print(f"  TIPO {t['tipo_equipo']}: equipos={t['n_equipos']} fallas={t['n_fallas_correctivas']}"
              f" MTBF={t['mtbf_horas']}h MTTR={t['mttr_horas']}h Disp={t['disponibilidad_pct']}%")

    # 4. Verificación manual (bomba: desde 2024-01-10, 3 fallas, 39.5h reparación)
    row = next((r for r in d["por_equipo"] if r["n_fallas_correctivas"] == 3), None)
    if row:
        h_cal = (date.fromisoformat(row["periodo_fin"]) - date.fromisoformat(row["periodo_inicio"])).days * 24
        h_op = h_cal - row["horas_reparacion"]
        mtbf_esperado = round(h_op / 3, 1)
        mttr_esperado = round((2.5 + 1.0 + 36.0) / 3, 1)
        disp_esperada = round(mtbf_esperado / (mtbf_esperado + mttr_esperado) * 100, 1)
        ok = (row["mtbf_horas"] == mtbf_esperado and row["mttr_horas"] == mttr_esperado
              and row["disponibilidad_pct"] == disp_esperada)
        print(f"\nVerificación bomba: h_cal={h_cal} h_op={h_op:.1f} → MTBF {row['mtbf_horas']}=={mtbf_esperado},"
              f" MTTR {row['mttr_horas']}=={mttr_esperado}, Disp {row['disponibilidad_pct']}=={disp_esperada} → {'OK ✓' if ok else 'ERROR ✗'}")

    # 5. Filtro por periodo (últimos 100 días → solo 1 falla de la bomba)
    r3 = c.get("/reportes/mtbf-mttr", params={"fecha_desde": str((datetime.now() - timedelta(days=100)).date())})
    row3 = next((x for x in r3.json()["por_equipo"] if x["equipo_id"] == eq_id), None)
    print(f"\nFiltro 100 días: fallas={row3['n_fallas_correctivas']} (esperado 1: solo deriva 40d; batería 120d fuera, preventiva no cuenta)")

    # 6. CSV
    r2b = c.get("/reportes/mtbf-mttr?formato=csv")
    print("\n== CSV:", r2b.status_code, "|", r2b.headers.get("content-disposition", "")[:60])
    lineas = r2b.text.strip().splitlines()
    print("Cabecera:", lineas[0][:100])
    print("Fila:", (lineas[1][:115] if len(lineas) > 1 else "(sin filas)"))

    # 7. Limpieza: elimina los datos de prueba para no contaminar la BD real
    with Session(engine) as s:
        ids = [eq_id, eq2_id]
        for ot in s.exec(select(OrdenTrabajo).where(OrdenTrabajo.equipo_id.in_(ids))).all():
            s.delete(ot)
        for tp in s.exec(select(TareaPreventiva).where(TareaPreventiva.equipo_id.in_(ids))).all():
            s.delete(tp)
        for e in s.exec(select(Equipo).where(Equipo.id.in_(ids))).all():
            s.delete(e)
        s.commit()
    print("\nLimpieza: equipos/OTs de prueba eliminados — la BD queda como estaba ✓")
