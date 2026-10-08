"""Prueba de inferencia completa (H3) + explicación SHAP (H2)."""
from ml.predictor import predecir, construir_datos_bomba

# Caso 1: bomba problemática con historial de oclusiones (ejemplo de la tesis)
equipo = {
    "id": 5,
    "nombre_corto": "Bomba Infusomat Space",
    "modelo": "Infusomat Space",
    "numero_serie": "BI-005-4421",
    "fecha_adquisicion": "2018-03-15",
    "criticidad": "Alta",
    "ubicacion_actual": "UCI Adultos",
}
historial = [
    {"fecha_ot": "2025-04-10", "tipo_mantenimiento": "correctivo",
     "descripcion_falla": "oclusión en la línea, tapado recurrente del sistema"},
    {"fecha_ot": "2025-06-22", "tipo_mantenimiento": "correctivo",
     "descripcion_falla": "reincide la obstruccion, tercer reporte del mes"},
    {"fecha_ot": "2025-08-01", "tipo_mantenimiento": "calibracion_programada",
     "descripcion_falla": "deriva de flujo del +5%, se ajusta calibración"},
    {"fecha_ot": "2025-09-18", "tipo_mantenimiento": "correctivo",
     "descripcion_falla": "alrama de oclusion constante otra vez, se purgo y persiste"},
]

datos = construir_datos_bomba(equipo, historial)
print("=== DATOS CONSTRUIDOS ===")
for k, v in datos.items():
    print(f"  {k}: {v}")

r = predecir(datos, equipo_id=5, numero_serie="BI-005-4421")
print("\n=== PREDICCIÓN COMPLETA ===")
print(f"RUL: {r['rul_dias']} días → semáforo {r['semaforo']['nivel']} ({r['semaforo']['etiqueta']})")
print(f"Tipo de falla: {r['tipo_falla_predicho']}")
print(f"Probabilidades: {r['probabilidades']}")
print(f"Tiempo inferencia: {r['tiempo_ms']} ms — cumple H3 (<2000ms): {r['cumple_h3']}")
print(f"\n=== EXPLICACIÓN (XAI/SHAP) ===\n{r['explicacion']}")
print("\nTop SHAP:")
for s in r["shap_top"]:
    print(f"  {s['etiqueta']}: {s['shap']} ({s['direccion']})")

# Caso 2: bomba nueva sin historial
equipo2 = {"id": 20, "nombre_corto": "Bomba Agilia", "modelo": "Agilia SP",
           "numero_serie": "BI-020-8810", "fecha_adquisicion": "2024-11-01",
           "criticidad": "Alta", "ubicacion_actual": "Neonatología"}
datos2 = construir_datos_bomba(equipo2, [])
r2 = predecir(datos2, equipo_id=20, numero_serie="BI-020-8810")
print("\n=== CASO 2: bomba nueva sin historial ===")
print(f"RUL: {r2['rul_dias']} días — tipo: {r2['tipo_falla_predicho']} — {r2['tiempo_ms']} ms")
print(r2["explicacion"])
