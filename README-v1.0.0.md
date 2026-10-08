# CMMS-BioAI v1.0.0 — RF07 MÓDULO PREDICTIVO (PLN + RUL + XAI)

> **Modelo híbrido interpretable de mantenimiento predictivo para bombas de infusión**
> Pipeline PLN (TF-IDF + SVM) → RUL (XGBoost) → Explicabilidad (SHAP) · 100% offline-first · sin GPU

Esta versión implementa el **RF07 (Módulo de Inteligencia Artificial)**, núcleo científico de la tesis de maestría. El módulo administrativo (RF01–RF06, RF08–RF12) permanece intacto.

---

## 1. Qué se añade en v1.0.0

| Componente | Descripción |
|---|---|
| **Pipeline PLN** | Preprocesamiento en 3 niveles (ablación) + TF-IDF (1.500 términos) + SVM lineal calibrado → clasificación de fallas en 6 categorías (eléctrica, mecánica, software, sensor, calibración, otra) |
| **Modelo RUL** | XGBoost Regressor con 12 features híbridas (6 estructuradas + 6 probabilidades PLN) → días hasta la próxima falla |
| **Módulo XAI** | SHAP (TreeExplainer) + texto explicativo diagnóstico en español, auditable según DECIDE-AI |
| **Estudio de ablación** | Tabla comparativa N1/N2/N3 (F1, AUC-ROC, RMSE, MAE) + prueba estadística pareada por protocolo de la tesis (Shapiro-Wilk → t de Student/Wilcoxon) |
| **Validación H1** | CV estratificada **por equipo** (StratifiedGroupKFold k=5): híbrido vs solo estructurado |
| **Cronómetro H3** | `time.perf_counter()` alrededor del pipeline completo + log JSONL de cada inferencia |
| **Dataset sintético** | 220 OTs de bombas de infusión en español con sinónimos, abreviaturas, errores ortográficos y "dialectos" técnicos por equipo (n=219 de Cochran + 1 margen) |
| **API `/ia/*`** | 11 endpoints REST integrados al FastAPI existente |
| **Dashboard Vue** | Vista Predictivo: semáforo RUL del parque, panel SHAP por bomba, importancia global, exportación anonimizada |
| **Modelo Equipo** | Nuevos campos `tipo_equipo` (catálogo) y `criticidad` (Baja/Media/Alta) con migración automática SQLite |

### Resultados con el dataset sintético (semilla 42)

| Indicador | Valor | Referencia tesis |
|---|---|---|
| F1-Score producción (N3) | **0.924** | H1: ≥ 0.85 ✓ |
| AUC-ROC OvR producción | **0.963** | H1: ≥ 0.85 ✓ |
| RMSE RUL | **23.6 días** | reportado |
| MAE RUL | **17.1 días** | reportado |
| H1 (híbrido vs estructurado) | **+228 % F1**, p = 3.8e-05 | H1: ≥15%, α=0.05 ✓ |
| Ablación N3 vs N2 | F1 0.923 vs 0.877, p = 0.049 (t unilateral) | valida propuesta ✓ |
| H3 tiempo de inferencia | media **3 ms**, p95 **2.9 ms**, máx 21 ms | H3: < 2 s ✓ |

> Los valores exactos pueden variar mínimamente al reentrenar en Windows; la semilla fija (42) mantiene la reproducibilidad del estudio.

---

## 2. Archivos nuevos y modificados

### Nuevos
```
backend/
├── ml/                                # ← MÓDULO PREDICTIVO COMPLETO (nuevo)
│   ├── __init__.py
│   ├── config.py                      # Parámetros científicos (semilla, niveles, features, semáforo)
│   ├── preprocesamiento.py            # N1/N2/N3 (diccionario de sinónimos + stop words + stemming)
│   ├── pln.py                         # TF-IDF + SVM calibrado + métricas F1/AUC
│   ├── rul.py                         # XGBoost/RandomForest + features híbridas
│   ├── xai.py                         # SHAP + texto explicativo en español
│   ├── ablation.py                    # Estudio de ablación + prueba N3 vs N2
│   ├── validacion.py                  # StratifiedGroupKFold por equipo + hipótesis H1
│   ├── metrics_logger.py              # Cronómetro perf_counter + logs JSONL (H3)
│   ├── entrenar.py                    # Entrenamiento del pipeline de producción
│   ├── predictor.py                   # Inferencia runtime (API/dashboard) con warm-up
│   ├── exportar.py                    # Exportación científica ANONIMIZADA (CSV/JSON)
│   ├── main_pipeline.py               # CLI: dataset|entrenar|ablacion|h1|todo
│   ├── prueba_inferencia.py           # Ejemplo de uso del predictor
│   ├── data/
│   │   ├── generar_dataset.py         # Generador del dataset sintético (220 OTs)
│   │   ├── sinonimos_biomedicos.json  # Diccionario de sinónimos (EDITABLE)
│   │   └── dataset_ot_bombas.csv      # Dataset generado
│   ├── models/                        # Modelos entrenados (joblib) — generados
│   ├── reports/                       # Reportes científicos CSV/JSON — generados
│   └── logs/                          # Log de inferencias JSONL — generado
├── api/routes/ia.py                   # ← Router REST /ia/* (nuevo)
└── prueba_api_ia.py                   # Script de prueba end-to-end de la API

frontend/src/views/PredictivoView.vue  # ← Dashboard predictivo (nuevo)
README-v1.0.0.md                       # Este archivo
```

### Modificados (reemplazar los existentes)
```
backend/main.py                 # incluye el router /ia
backend/database.py             # migración v1.0.0 (tipo_equipo + criticidad)
backend/models/equipos.py       # campos tipo_equipo + criticidad
backend/schemas/equipo.py       # campos + validadores
backend/requirements.txt        # + scikit-learn, xgboost, shap, pandas, nltk, scipy (+ pin sqlmodel<0.0.22)
frontend/src/router/index.js    # ruta /predictivo
frontend/src/components/Sidebar.vue   # ítem "Predictivo 🧠"
frontend/src/views/EquiposView.vue    # selects Tipo de Equipo + Criticidad
```

---

## 3. Cómo aplicar (Windows 11)

1. **Copia los archivos** del ZIP sobre tu proyecto local (respeta la estructura de carpetas; reemplaza los modificados).
2. **Instala las nuevas dependencias** (con tu venv activado):
   ```bat
   cd backend
   pip install -r requirements.txt
   ```
   > Nota: si ya tenías `sqlmodel` actualizado y las OTs fallan con un error de *timezone*, el pin `sqlmodel<0.0.22` del requirements lo corrige.
3. **Arranca el backend** (crea tablas/migraciones automáticamente):
   ```bat
   uvicorn main:app --reload
   ```
4. **Entrena el pipeline** (una sola vez, ~5 s):
   ```bat
   python -m ml.entrenar
   ```
5. **Compila el frontend**:
   ```bat
   cd ../frontend
   npm run build
   ```
6. Refresca el navegador con **Ctrl+F5** y entra al menú **🧠 Predictivo**.

---

## 4. Ejecución del estudio científico (para la tesis)

Desde `backend/`:

```bat
python -m ml.main_pipeline todo       # dataset + entrenamiento + ablación + H1 + exportación
python -m ml.main_pipeline ablacion   # solo ablación (tabla N1/N2/N3 + prueba estadística)
python -m ml.main_pipeline h1         # solo contraste H1 (híbrido vs estructurado)
```

Reportes generados en `backend/ml/reports/` (todos **anonimizados** — sin técnicos, pacientes ni instituciones):

| Archivo | Uso en la tesis |
|---|---|
| `ablacion_resultados.csv/.json` | Tabla comparativa N1/N2/N3 + prueba N3 vs N2 (Fase 2) |
| `hipotesis_h1_hibrido_vs_estructurado.json` | Contraste H1 con CV estratificada por equipo |
| `predicciones_vs_realidad.csv` | RMSE/MAE del RUL (out-of-fold) |
| `matriz_confusion.csv` | F1-Score del clasificador |
| `tiempos_inferencia.csv` | Validación H3 (60 inferencias cronometradas) |
| `valores_shap.csv` | Insumo del cuestionario Likert con expertos (H2) |
| `validacion_cruzada.json` | Métricas por pliegue con detalle |

También descargables desde la interfaz (**🧠 Predictivo → botones de exportación**) o vía API: `GET /ia/exportar/{predicciones|matriz|tiempos|shap|ablacion}?formato=csv|json`.

---

## 5. API del módulo (Swagger: `http://127.0.0.1:8000/docs`)

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/ia/estado` | ¿Modelos entrenados? + métricas del último entrenamiento |
| POST | `/ia/entrenar` | Entrena el pipeline completo (dataset sintético o CSV real normalizado) |
| GET | `/ia/resumen` | Semáforo RUL de todas las bombas (dashboard) |
| GET | `/ia/predict/{equipo_id}` | Predicción completa de una bomba (RUL + SHAP + explicación + tiempo) |
| POST | `/ia/predict` | Predicción manual con datos explícitos (útil para la evaluación Likert) |
| GET | `/ia/metricas` | F1, AUC, RMSE, MAE + importancia global SHAP |
| GET | `/ia/ablation` | Tabla de ablación (`?ejecutar=true` para recalcular) |
| GET | `/ia/h1` | Contraste H1 |
| GET | `/ia/h3` | Estadísticas de tiempos de inferencia |
| GET | `/ia/logs` | Últimas inferencias del log JSONL |
| GET | `/ia/exportar/{tipo}` | Descarga CSV/JSON anonimizado |

**Delimitación de la tesis aplicada:** el módulo solo predice equipos con `tipo_equipo = "Bomba de Infusión"`; los demás equipos devuelven HTTP 400 con mensaje explicativo.

---

## 6. Datos reales (cuando estén disponibles)

Para entrenar con los historiales 2023–2025 del hospital, normaliza tus datos al formato del dataset sintético (mismas 22 columnas; revisa el encabezado de `backend/ml/data/dataset_ot_bombas.csv`), guarda el CSV y ajusta `DATASET_CSV` en `backend/ml/config.py`. La estructura de columnas es idéntica a la salida de la **Ficha de Extracción** del protocolo (tesis §3.7) y respeta los criterios de inclusión/exclusión/eliminación (§3.6.4).

Requisitos mínimos por equipo: historial ≥ 12 meses y ≥ 3 intervenciones. Las OTs con >30% de datos faltantes o texto ilegible deben eliminarse antes del entrenamiento.

---

## 7. Decisiones técnicas documentadas

- **SVM lineal calibrado** (en lugar de NB): el núcleo es TF-IDF + SVM lineal según la tesis; la calibración sigmoide aporta `predict_proba` para las features del RUL sin alterar el algoritmo.
- **XGBoost con árboles de profundidad 3**: n≈220 OTs; profundidad baja evita el sobreajuste (documentado en `ml/config.py`).
- **Warm-up del predictor**: SHAP/XGBoost se calientan al cargar los modelos para que la **primera** inferencia real también cumpla H3.
- **Dialectos técnicos por equipo en el dataset sintético**: cada bomba usa un vocabulario propio (correlación intraclase por equipo), el fenómeno que motiva la estratificación por equipo y el valor del diccionario N3.
- **Ambigüedad diagnóstica**: ~20% de las fallas mecánicas/sensor/software comparten el mismo texto-síntoma ("alarma de oclusión") con distinta causa raíz — acota el F1 máximo alcanzable de forma realista.
- **Anonimización**: las exportaciones usan códigos EQ-XX/OT-XXXX y excluyen técnicos, pacientes e instituciones (Ley 164 / restricción 6 del PROMPT MAESTRO).
- **`sqlmodel<0.0.22`**: las versiones 0.0.22+ exigen timezone en datetimes y rompen la creación de OTs del CMMS existente.
