"""Prueba end-to-end de los endpoints /ia/ con TestClient de FastAPI."""
import sys
sys.path.insert(0, ".")

from fastapi.testclient import TestClient
from main import app

# El context manager ejecuta el lifespan (crea tablas + seed + migraciones)
client = TestClient(app)
client.__enter__()

print("=== 1. GET /ia/estado ===")
r = client.get("/ia/estado")
print(r.status_code, {k: r.json()[k] for k in ["entrenado", "tipo_equipo_objetivo"]})

print("\n=== 2. Crear bombas de infusión de prueba (POST /equipos/) ===")
bombas = [
    {"nombre_corto": "Bomba Infusomat UCI-1", "modelo": "Infusomat Space", "numero_serie": "TEST-BI-001",
     "marca": "B.Braun", "fecha_adquisicion": "2019-05-10", "criticidad": "Alta",
     "tipo_equipo": "Bomba de Infusión", "ubicacion_actual": "UCI Adultos"},
    {"nombre_corto": "Bomba Agilia Neo-2", "modelo": "Agilia SP", "numero_serie": "TEST-BI-002",
     "marca": "Fresenius", "fecha_adquisicion": "2022-08-01", "criticidad": "Alta",
     "tipo_equipo": "Bomba de Infusión", "ubicacion_actual": "Neonatología"},
    {"nombre_corto": "Monitor Siemens (control)", "modelo": "SVM-8000", "numero_serie": "TEST-MON-001",
     "marca": "Siemens", "criticidad": "Media", "tipo_equipo": "Monitor", "ubicacion_actual": "Piso 3"},
]
ids = {}
for b in bombas:
    r = client.post("/equipos/", json=b)
    print(f"  {b['numero_serie']}: {r.status_code}")
    if r.status_code in (200, 201):
        d = r.json()
        ids[b["numero_serie"]] = d.get("id") or d.get("id_equipo") or d.get("id_equipo")

print("\n=== 3. Crear OTs con texto libre (POST /ordenes/) ===")
ots = [
    ("TEST-BI-001", "oclusión en la línea de infusión, tapado del sistema", "Correctivo"),
    ("TEST-BI-001", "reincide la oclusion, alarma constante, tercer reporte", "Correctivo"),
    ("TEST-BI-001", "deriva de flujo del +7% en verificación, se calibra", "Correctivo"),
    ("TEST-BI-002", "la batería no carga, se apaga solo", "Correctivo"),
]
for serie, texto, titulo in ots:
    eid = ids.get(serie)
    if not eid:
        continue
    r = client.post("/ordenes/", json={
        "equipo_id": eid, "titulo": titulo, "descripcion_falla": texto,
        "prioridad": "Alta", "estado_id": 4,
    })
    print(f"  OT {serie}: {r.status_code}")

print("\n=== 4. Entrenar (POST /ia/entrenar) ===")
r = client.post("/ia/entrenar?usar_dataset_sintetico=true")
print(r.status_code, "F1:", r.json().get("clasificacion", {}).get("f1_macro"))

print("\n=== 5. GET /ia/resumen (semáforo del parque) ===")
r = client.get("/ia/resumen")
d = r.json()
print(r.status_code, "total:", d.get("total"), "conteo:", d.get("conteo_semaforo"))
for b in d.get("bombas", []):
    print(f"  {b.get('nombre_corto')}: RUL={b.get('rul_dias')} días → {b.get('semaforo', {}).get('etiqueta')}")

print("\n=== 6. GET /ia/predict/{id} de la bomba 1 (con SHAP) ===")
bid = ids.get("TEST-BI-001")
r = client.get(f"/ia/predict/{bid}")
d = r.json()
print(r.status_code, "RUL:", d.get("rul_dias"), "| tipo:", d.get("tipo_falla_predicho"), "| ms:", d.get("tiempo_ms"))
print("  Explicación:", d.get("explicacion", "")[:150], "...")

print("\n=== 7. GET /ia/metricas ===")
r = client.get("/ia/metricas")
print(r.status_code, "clasificación:", r.json().get("clasificacion", {}).get("f1_macro"),
      "| regresión:", r.json().get("regresion", {}).get("rmse_dias"))

print("\n=== 8. GET /ia/h3 ===")
r = client.get("/ia/h3")
print(r.status_code, r.json())

print("\n=== 9. Predicción de equipo NO-bomba (debe rechazar) ===")
mid = ids.get("TEST-MON-001")
r = client.get(f"/ia/predict/{mid}")
print(r.status_code, r.json().get("detail", "")[:80])

print("\n=== 10. Exportación anonimizada ===")
r = client.get("/ia/exportar/tiempos")
print("CSV tiempos:", r.status_code, r.headers.get("content-disposition", "")[:60])
