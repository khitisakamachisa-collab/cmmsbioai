"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/entrenar.py
Entrenamiento del pipeline de producción (N3) sobre el dataset disponible.

Flujo:
  1) Carga dataset (CSV sintético 220 OTs o datos reales normalizados).
  2) Entrena ClasificadorPLN (TF-IDF N3 + SVM calibrado) → tipo de falla.
  3) Construye features híbridas y entrena ModeloRUL (XGBoost/RF) → días.
  4) Evalúa con partición estratificada train/test (métricas H1/H3 base).
  5) Guarda modelos joblib + metricas_entrenamiento.json + log de entrenamiento.

Ejecución:
    cd backend
    python -m ml.entrenar
"""

import json
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from ml import config
from ml.pln import ClasificadorPLN, metricas_clasificacion
from ml.rul import ModeloRUL, construir_features, metricas_regresion
from ml.xai import importancia_global_shap
from ml.metrics_logger import log_entrenamiento


def cargar_dataset(ruta_csv=None) -> pd.DataFrame:
    """Carga el dataset de OTs de bombas de infusión (sintético o real normalizado)."""
    ruta = ruta_csv or config.DATASET_CSV
    df = pd.read_csv(ruta, encoding="utf-8-sig")
    cols_requeridas = [
        "texto_libre", "tipo_falla", "equipo_id", "edad_anios", "criticidad",
        "dias_desde_ultima_intervencion", "num_ot_previas_12m",
        "num_reportes_oclusion_previos", "deriva_calibracion_previa",
        "dias_hasta_proxima_falla",
    ]
    faltan = [c for c in cols_requeridas if c not in df.columns]
    if faltan:
        raise ValueError(f"Dataset sin columnas requeridas: {faltan}")
    return df


def entrenar_todo(df: pd.DataFrame = None, guardar: bool = True) -> dict:
    """Entrena el pipeline completo de producción con nivel N3."""
    t_inicio = time.perf_counter()

    if df is None:
        df = cargar_dataset()

    # ------------------------------------------------------------------
    # 1) Partición estratificada train/test (75/25)
    # ------------------------------------------------------------------
    df_tr, df_te = train_test_split(
        df, test_size=0.25, random_state=config.RANDOM_SEED, stratify=df["tipo_falla"]
    )

    # ------------------------------------------------------------------
    # 2) Clasificador PLN (N3 = producción)
    # ------------------------------------------------------------------
    pln = ClasificadorPLN("N3").entrenar(
        df_tr["texto_libre"].tolist(), df_tr["tipo_falla"].tolist()
    )
    y_pred = pln.predecir(df_te["texto_libre"].tolist())
    probas_te = pln.probabilidades(df_te["texto_libre"].tolist())
    m_cls = metricas_clasificacion(df_te["tipo_falla"].tolist(), y_pred, probas_te)

    # ------------------------------------------------------------------
    # 3) Modelo RUL (features híbridas)
    # ------------------------------------------------------------------
    probas_tr = pln.probabilidades(df_tr["texto_libre"].tolist())
    X_tr = construir_features(df_tr, probas_tr)
    X_te = construir_features(df_te, probas_te)
    rul = ModeloRUL().entrenar(X_tr, df_tr["dias_hasta_proxima_falla"])
    y_rul = rul.predecir(X_te)
    m_rul = metricas_regresion(df_te["dias_hasta_proxima_falla"], y_rul)

    # ------------------------------------------------------------------
    # 4) Importancia global de SHAP (sobre muestra de referencia = test)
    # ------------------------------------------------------------------
    try:
        imp_global = importancia_global_shap(rul, X_te.values)
    except Exception:
        imp_global = rul.importancia_global()

    # ------------------------------------------------------------------
    # 5) Persistencia de modelos y métricas
    # ------------------------------------------------------------------
    if guardar:
        import joblib
        joblib.dump(pln.vectorizador, config.VECTORIZADOR_N3)
        joblib.dump(pln.clf, config.MODELO_CLASIFICADOR)
        joblib.dump(pln.encoder, config.LABEL_ENCODER)
        joblib.dump(rul, config.MODELO_RUL)

        metricas = {
            "nivel_produccion": "N3",
            "clasificador": f"TF-IDF({config.TFIDF_MAX_FEATURES}) + {config.CLASIFICADOR_PLN} calibrado",
            "rul": config.RUL_ALGORITMO,
            "n_total": int(len(df)),
            "n_train": int(len(df_tr)),
            "n_test": int(len(df_te)),
            "clasificacion": m_cls,
            "regresion": m_rul,
            "importancia_global_shap": imp_global[:8],
            "categorias": config.CATEGORIAS_FALLA,
            "features_rul": config.FEATURES_RUL,
        }
        with open(config.METRICAS_ENTRENAMIENTO, "w", encoding="utf-8") as f:
            json.dump(metricas, f, ensure_ascii=False, indent=2)

        log_entrenamiento(
            n_ots=len(df), f1=m_cls["f1_macro"], auc=m_cls.get("auc_roc_ovr"),
            rmse=m_rul["rmse_dias"], mae=m_rul["mae_dias"],
            tiempo_entrenamiento_s=time.perf_counter() - t_inicio,
            dataset=str(config.DATASET_CSV.name),
        )

    resumen = {
        "ok": True,
        "n_ots": int(len(df)),
        "clasificacion": m_cls,
        "regresion": m_rul,
        "tiempo_entrenamiento_s": round(time.perf_counter() - t_inicio, 2),
        "modelos_guardados_en": str(config.MODELS_DIR),
    }
    return resumen


def esta_entrenado() -> bool:
    """True si ya existen los artefactos de producción."""
    return config.MODELO_CLASIFICADOR.exists() and config.MODELO_RUL.exists() and config.VECTORIZADOR_N3.exists()


if __name__ == "__main__":
    resultado = entrenar_todo()
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
