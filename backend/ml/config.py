"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/config.py
Configuración central del pipeline PLN + RUL + XAI.

Tesis: "Modelo híbrido interpretable de mantenimiento predictivo (PLN + RUL)
para bombas de infusión en entornos de conectividad limitada".

Restricciones del PROMPT MAESTRO:
- 100% offline-first (sin APIs externas, sin CDNs, sin nube)
- Sin GPU: solo TF-IDF, Naive Bayes, SVM, Random Forest, XGBoost
- Tiempo de inferencia < 2 segundos (time.perf_counter)
- Corpus técnico en español (hospitalario/biomédico)
"""

from pathlib import Path

# ============================================================
# RUTAS (relativas a la carpeta ml/ — compatible Windows/Linux)
# ============================================================
ML_DIR = Path(__file__).resolve().parent
DATA_DIR = ML_DIR / "data"
MODELS_DIR = ML_DIR / "models"
REPORTS_DIR = ML_DIR / "reports"
LOGS_DIR = ML_DIR / "logs"

DATASET_CSV = DATA_DIR / "dataset_ot_bombas.csv"
SINONIMOS_JSON = DATA_DIR / "sinonimos_biomedicos.json"

# Archivos de modelos entrenados (joblib)
MODELO_CLASIFICADOR = MODELS_DIR / "clasificador_fallas.joblib"
MODELO_RUL = MODELS_DIR / "modelo_rul.joblib"
VECTORIZADOR_N1 = MODELS_DIR / "tfidf_n1.joblib"
VECTORIZADOR_N2 = MODELS_DIR / "tfidf_n2.joblib"
VECTORIZADOR_N3 = MODELS_DIR / "tfidf_n3.joblib"
LABEL_ENCODER = MODELS_DIR / "label_encoder.joblib"
METRICAS_ENTRENAMIENTO = MODELS_DIR / "metricas_entrenamiento.json"

# Log de inferencias (valida H3 de la tesis)
LOG_INFERENCIAS = LOGS_DIR / "log_inferencias.jsonl"
LOG_ENTRENAMIENTOS = LOGS_DIR / "log_entrenamientos.jsonl"

# Reportes científicos
REPORTE_ABLACION_CSV = REPORTS_DIR / "ablacion_resultados.csv"
REPORTE_ABLACION_JSON = REPORTS_DIR / "ablacion_resultados.json"
REPORTE_CV_JSON = REPORTS_DIR / "validacion_cruzada.json"
REPORTE_H1_JSON = REPORTS_DIR / "hipotesis_h1_hibrido_vs_estructurado.json"
REPORTE_PREDICCIONES_CSV = REPORTS_DIR / "predicciones_vs_realidad.csv"
REPORTE_MATRIZ_CONFUSION_CSV = REPORTS_DIR / "matriz_confusion.csv"
REPORTE_TIEMPOS_CSV = REPORTS_DIR / "tiempos_inferencia.csv"
REPORTE_SHAP_CSV = REPORTS_DIR / "valores_shap.csv"

# ============================================================
# PARÁMETROS CIENTÍFICOS (según tesis)
# ============================================================

# Semilla aleatoria para reproducibilidad del estudio
RANDOM_SEED = 42

# Taxonomía de tipos de falla (Cap. 1.9 de la tesis: operacionalización de variables)
# NOTA: orden alfabético requerido por roc_auc_score(labels=...) — mantener ordenado.
CATEGORIAS_FALLA = [
    "calibracion",
    "electrica",
    "mecanica",
    "otra",
    "sensor",
    "software",
]

# 3 niveles de preprocesamiento para el estudio de ablación (Fase 2 de la tesis)
NIVELES_PREPROCESAMIENTO = {
    "N1": "Texto crudo (solo tokenización básica)",
    "N2": "Limpieza genérica agresiva (stop words + stemming Snowball español)",
    "N3": "Limpieza consciente del dominio (diccionario de sinónimos biomédicos)",
}

# Vectorización TF-IDF con vocabulario acotado (tesis: máx 1000-2000 términos)
TFIDF_MAX_FEATURES = 1500

# Clasificadores PLN permitidos (tesis: Naive Bayes multinomial o SVM lineal)
CLASIFICADOR_PLN = "SVM"        # "NB" o "SVM" — SVM lineal suele superar a NB con TF-IDF
SVM_C = 1.0                     # Parámetro de regularización del SVM lineal
NB_ALPHA = 0.5                  # Suavizado de Laplace para MultinomialNB

# Modelo RUL (tesis: Random Forest Regressor o XGBoost Regressor)
RUL_ALGORITMO = "XGBoost"       # "RandomForest" o "XGBoost"
RUL_N_ESTIMATORS = 250
RUL_MAX_DEPTH = 3               # Árboles poco profundos: n≈220 → evitar sobreajuste
RUL_LEARNING_RATE = 0.05        # Solo XGBoost
RUL_SUBSAMPLE = 0.8             # Solo XGBoost
RUL_COLSAMPLE = 0.8             # Solo XGBoost

# Validación cruzada estratificada (tesis: K-Fold Stratified k=5, por equipo)
CV_FOLDS = 5

# Umbral de relevancia estadística
ALPHA_ESTADISTICO = 0.05

# Hipótesis H1 de la tesis: el híbrido supera en >= 15% el F1 del modelo estructurado
H1_MEJORA_MINIMA = 0.15

# Hipótesis H3 de la tesis: tiempo de inferencia < 2 s en hardware estándar sin GPU
H3_TIEMPO_MAXIMO_S = 2.0

# ============================================================
# SEMAFORIZACIÓN DEL DASHBOARD PREDICTIVO (RUL en días)
# ============================================================
SEMAFORO = {
    "rojo": {"max_dias": 30, "color": "#ef4444", "etiqueta": "Crítico"},
    "amarillo": {"max_dias": 90, "color": "#eab308", "etiqueta": "Atención"},
    "verde": {"max_dias": None, "color": "#16a34a", "etiqueta": "Estable"},
}


def semaforo_para_rul(rul_dias: float) -> dict:
    """Devuelve {'nivel','color','etiqueta'} según el RUL estimado (días)."""
    if rul_dias is None:
        return {"nivel": "sin_datos", "color": "#9ca3af", "etiqueta": "Sin datos"}
    if rul_dias <= SEMAFORO["rojo"]["max_dias"]:
        return {"nivel": "rojo", "color": SEMAFORO["rojo"]["color"], "etiqueta": SEMAFORO["rojo"]["etiqueta"]}
    if rul_dias <= SEMAFORO["amarillo"]["max_dias"]:
        return {"nivel": "amarillo", "color": SEMAFORO["amarillo"]["color"], "etiqueta": SEMAFORO["amarillo"]["etiqueta"]}
    return {"nivel": "verde", "color": SEMAFORO["verde"]["color"], "etiqueta": SEMAFORO["verde"]["etiqueta"]}


# ============================================================
# FEATURES ESTRUCTURADAS DEL MODELO RUL (con etiquetas para XAI)
# ============================================================
# Orden estable: el modelo se entrena con este orden exacto.
FEATURES_RUL = [
    "edad_anios",
    "criticidad_puntaje",
    "dias_desde_ultima_intervencion",
    "num_ot_previas_12m",
    "num_reportes_oclusion_previos",
    "deriva_calibracion_previa",
    "prob_electrica",
    "prob_mecanica",
    "prob_software",
    "prob_sensor",
    "prob_calibracion",
    "prob_otra",
]

# Etiquetas legibles (español) para el módulo XAI y el dashboard
ETIQUETAS_FEATURES = {
    "edad_anios": "Antigüedad del equipo (años)",
    "criticidad_puntaje": "Criticidad del equipo (1-3)",
    "dias_desde_ultima_intervencion": "Días desde la última intervención",
    "num_ot_previas_12m": "N.º de OTs correctivas previas (12 meses)",
    "num_reportes_oclusion_previos": "N.º de reportes previos de 'oclusión'",
    "deriva_calibracion_previa": "Deriva previa en calibración",
    "prob_electrica": "Riesgo textual de falla eléctrica (PLN)",
    "prob_mecanica": "Riesgo textual de falla mecánica (PLN)",
    "prob_software": "Riesgo textual de falla de software (PLN)",
    "prob_sensor": "Riesgo textual de falla de sensor (PLN)",
    "prob_calibracion": "Riesgo de deriva metrológica (PLN)",
    "prob_otra": "Riesgo textual de otro tipo (PLN)",
}

# Puntaje de criticidad usado como feature estructurada (Alta=3, Media=2, Baja=1)
CRITICIDAD_PUNTAJE = {"Baja": 1, "Media": 2, "Alta": 3}

# Tipo de equipo que activa el módulo predictivo (delimitación de la tesis)
TIPO_EQUIPO_OBJETIVO = "Bomba de Infusión"

# Asegurar carpetas
for _d in (DATA_DIR, MODELS_DIR, REPORTS_DIR, LOGS_DIR):
    _d.mkdir(parents=True, exist_ok=True)
