"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/predictor.py
Inferencia en runtime para la API (FastAPI) y el dashboard predictivo.

- Carga perezosa (singleton) de los modelos entrenados.
- predicción completa en < 2 s (H3): normalización N3 → clasificación PLN →
  features híbridas → RUL → SHAP → texto explicativo → log JSONL.
- Acepta datos de una bomba directamente (dict) o un historial de OTs.
"""

import threading
from datetime import date, datetime

import numpy as np

from ml import config
from ml.preprocesamiento import preprocesar
from ml.metrics_logger import CronometroInferencia, log_inferencia
from ml.xai import resumen_shap, texto_explicativo, valores_shap

_lock = threading.Lock()
_estado = {"cargado": False, "vectorizador": None, "clf": None, "encoder": None,
           "rul": None, "explainer": None}


def _precalentar():
    """Warm-up del pipeline completo para que la PRIMERA inferencia real también
    cumpla H3 (< 2 s): importa shap, crea el TreeExplainer y hace una predicción
    dummy durante la carga de modelos (no en producción)."""
    import numpy as np
    import pandas as pd
    dummy = pd.DataFrame([[5.0, 3.0, 90.0, 2.0, 1.0, 0.0] + [0.2] * 6],
                         columns=config.FEATURES_RUL)
    try:
        _estado["rul"].predecir(dummy)
    except Exception:
        pass
    try:
        import shap
        _estado["explainer"] = shap.TreeExplainer(_estado["rul"].modelo)
        _estado["explainer"].shap_values(dummy.values, check_additivity=False)
    except Exception:
        _estado["explainer"] = None
    # Vectorizador + clasificador con un texto de prueba
    _estado["vectorizador"].transform(["prueba de calentamiento"])


def cargar_modelos(forzar: bool = False) -> bool:
    """Carga los artefactos entrenados (lazy singleton, thread-safe) + warm-up H3."""
    with _lock:
        if _estado["cargado"] and not forzar:
            return True
        import joblib
        if not (config.MODELO_CLASIFICADOR.exists() and config.MODELO_RUL.exists()
                and config.VECTORIZADOR_N3.exists() and config.LABEL_ENCODER.exists()):
            return False
        _estado["vectorizador"] = joblib.load(config.VECTORIZADOR_N3)
        _estado["clf"] = joblib.load(config.MODELO_CLASIFICADOR)
        _estado["encoder"] = joblib.load(config.LABEL_ENCODER)
        _estado["rul"] = joblib.load(config.MODELO_RUL)
        _precalentar()
        _estado["cargado"] = True
        return True


def modelos_disponibles() -> bool:
    if not _estado["cargado"]:
        return (config.MODELO_CLASIFICADOR.exists() and config.MODELO_RUL.exists()
                and config.VECTORIZADOR_N3.exists())
    return True


# ------------------------------------------------------------------
# Features estructuradas desde datos crudos (equipos del CMMS)
# ------------------------------------------------------------------
def _edad_desde_fecha(fecha_adquisicion) -> float:
    try:
        if isinstance(fecha_adquisicion, str):
            f = date.fromisoformat(fecha_adquisicion[:10])
        else:
            f = fecha_adquisicion
        return round((date.today() - f).days / 365.25, 2)
    except Exception:
        return 5.0  # valor por defecto prudente si no hay fecha


def construir_datos_bomba(equipo: dict, historial_ots: list, texto_libre: str = None) -> dict:
    """
    Convierte un equipo del CMMS + su historial de OTs en el registro de features.
    historial_ots: lista de dicts {fecha_ot, tipo_mantenimiento, descripcion_falla}
    ordenada ascendente (la más reciente al final).
    """
    texto = texto_libre or (historial_ots[-1]["descripcion_falla"] if historial_ots
                            else "sin descripciones disponibles")
    hoy = date.today()

    # Antigüedad
    edad = _edad_desde_fecha(equipo.get("fecha_adquisicion"))

    # Correctivas previas (12 meses) y reportes de oclusión / deriva
    claves_oclusion = ["oclusion", "obstruc", "tapad", "atasc", "bloque"]
    claves_deriva = ["deriva", "desvi", "fuera de rango", "fuera de tolerancia"]
    num_prev_12m = 0
    num_oclusion = 0
    deriva_prev = 0
    ultima_fecha = None
    for ot in historial_ots:
        f = ot.get("fecha_ot")
        if isinstance(f, str):
            try:
                f = date.fromisoformat(f[:10])
            except Exception:
                f = None
        if isinstance(f, datetime):
            f = f.date()
        if f is None:
            continue
        if ultima_fecha is None or f > ultima_fecha:
            ultima_fecha = f
        texto_norm = preprocesar(ot.get("descripcion_falla", ""), "N3")
        es_correctivo = (ot.get("tipo_mantenimiento") or "").lower() == "correctivo"
        if es_correctivo and (hoy - f).days <= 365:
            num_prev_12m += 1
        if es_correctivo and any(c in texto_norm for c in claves_oclusion):
            num_oclusion += 1
        if any(c in texto_norm for c in claves_deriva):
            deriva_prev = 1

    dias_desde = (hoy - ultima_fecha).days if ultima_fecha else 180
    criticidad = equipo.get("criticidad") or "Media"
    if criticidad not in config.CRITICIDAD_PUNTAJE:
        criticidad = "Media"

    return {
        "texto_libre": texto,
        "edad_anios": edad,
        "criticidad": criticidad,
        "dias_desde_ultima_intervencion": dias_desde,
        "num_ot_previas_12m": num_prev_12m,
        "num_reportes_oclusion_previos": num_oclusion,
        "deriva_calibracion_previa": deriva_prev,
    }


# ------------------------------------------------------------------
# Predicción completa (cronometrada — valida H3)
# ------------------------------------------------------------------
def predecir(datos_bomba: dict, equipo_id=None, numero_serie=None,
             registrar_log: bool = True) -> dict:
    """
    Ejecuta el pipeline completo para una bomba y devuelve:
      RUL + semáforo + tipo de falla + probabilidades + explicación SHAP + tiempo.
    """
    if not cargar_modelos():
        raise RuntimeError("Modelos no entrenados. Ejecutar POST /ia/entrenar o python -m ml.entrenar")

    with CronometroInferencia() as cron:
        texto = datos_bomba["texto_libre"]

        # 1) Clasificación PLN con el vectorizador N3 de producción
        X_txt = _estado["vectorizador"].transform([texto])
        if hasattr(_estado["clf"], "predict_proba"):
            probas = _estado["clf"].predict_proba(X_txt)[0]
        else:
            dec = _estado["clf"].decision_function(X_txt)[0]
            probas = np.exp(dec) / np.exp(dec).sum()
        clases = list(_estado["encoder"].classes_)
        orden = [clases.index(c) for c in config.CATEGORIAS_FALLA if c in clases]
        probas = np.asarray(probas)[orden]
        while probas.shape[0] < len(config.CATEGORIAS_FALLA):
            probas = np.append(probas, 0.0)
        tipo_falla = config.CATEGORIAS_FALLA[int(np.argmax(probas))]
        probas_dict = {c: round(float(p), 4) for c, p in zip(config.CATEGORIAS_FALLA, probas)}

        # 2) Features híbridas (estructuradas + probabilidades PLN)
        feats = {}
        for i, cat in enumerate(config.CATEGORIAS_FALLA):
            feats[f"prob_{cat}"] = float(probas[i])
        feats["edad_anios"] = float(datos_bomba.get("edad_anios", 5.0))
        feats["criticidad_puntaje"] = float(config.CRITICIDAD_PUNTAJE.get(datos_bomba.get("criticidad", "Media"), 2))
        feats["dias_desde_ultima_intervencion"] = float(datos_bomba.get("dias_desde_ultima_intervencion", 180))
        feats["num_ot_previas_12m"] = float(datos_bomba.get("num_ot_previas_12m", 0))
        feats["num_reportes_oclusion_previos"] = float(datos_bomba.get("num_reportes_oclusion_previos", 0))
        feats["deriva_calibracion_previa"] = float(datos_bomba.get("deriva_calibracion_previa", 0))
        X = np.array([[feats[f] for f in config.FEATURES_RUL]])

        # 3) RUL
        rul_dias = float(_estado["rul"].predecir(_X_df(X))[0])

        # 4) SHAP + texto explicativo (usa el explainer precalentado)
        try:
            if _estado.get("explainer") is not None:
                sv = _estado["explainer"].shap_values(X, check_additivity=False)[0]
                if isinstance(sv, list):
                    sv = sv[0]
                sv = np.asarray(sv)
            else:
                sv = valores_shap(_estado["rul"], X)[0]
        except Exception:
            sv = np.zeros(len(config.FEATURES_RUL))
        resumen = resumen_shap(sv, X[0], top_k=5)
        explicacion = texto_explicativo(rul_dias, tipo_falla, resumen, probas_dict)

    semaforo = config.semaforo_para_rul(rul_dias)

    resultado = {
        "equipo_id": equipo_id,
        "numero_serie": numero_serie,
        "rul_dias": round(rul_dias, 1),
        "semaforo": semaforo,
        "tipo_falla_predicho": tipo_falla,
        "probabilidades": probas_dict,
        "explicacion": explicacion,
        "shap_top": resumen,
        "tiempo_ms": cron.tiempo_ms,
        "cumple_h3": cron.cumple_h3(),
        "features_usadas": {f: round(feats[f], 4) for f in config.FEATURES_RUL},
    }

    if registrar_log:
        log_inferencia(equipo_id, numero_serie, rul_dias, tipo_falla,
                       cron.tiempo_ms, resumen)
    return resultado


def _X_df(X: np.ndarray):
    """Envoltorio mínimo tipo DataFrame para reutilizar el código del modelo."""
    import pandas as pd
    return pd.DataFrame(X, columns=config.FEATURES_RUL)


# ------------------------------------------------------------------
# Predicciones para el dashboard (todas las bombas)
# ------------------------------------------------------------------
def predecir_parque(bombas: list, historiales: dict) -> list:
    """
    bombas: lista de dicts de equipos (tipo_equipo == Bomba de Infusión).
    historiales: {equipo_id: [ots...]}
    Devuelve lista con el último estado predictivo de cada bomba (para semáforo).
    """
    salida = []
    for eq in bombas:
        eid = eq.get("id")
        ots = historiales.get(eid, [])
        datos = construir_datos_bomba(eq, ots)
        try:
            r = predecir(datos, equipo_id=eid, numero_serie=eq.get("numero_serie"),
                         registrar_log=False)
        except Exception:
            r = {
                "equipo_id": eid, "numero_serie": eq.get("numero_serie"),
                "rul_dias": None, "semaforo": {"nivel": "sin_datos", "color": "#9ca3af", "etiqueta": "Sin datos"},
                "tipo_falla_predicho": None, "probabilidades": {}, "explicacion": "Modelos no entrenados.",
                "shap_top": [], "tiempo_ms": None, "cumple_h3": None,
            }
        r["nombre_corto"] = eq.get("nombre_corto")
        r["modelo"] = eq.get("modelo")
        r["ubicacion_actual"] = eq.get("ubicacion_actual")
        salida.append(r)
    # Ordenar: más críticas primero
    salida.sort(key=lambda x: (x["rul_dias"] if x["rul_dias"] is not None else 9999))
    return salida
