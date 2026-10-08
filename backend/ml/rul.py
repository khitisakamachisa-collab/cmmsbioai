"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/rul.py
Modelo de Vida Útil Remanente (RUL): Random Forest / XGBoost Regressor.

Entrada: features del PLN (probabilidades por tipo de falla derivadas del texto
libre) + datos estructurados (antigüedad, criticidad, días desde la última
intervención, nº de OTs correctivas previas, reportes previos de oclusión,
deriva previa en calibración).

Salida: días estimados hasta la próxima falla (RUL).
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from ml import config


# ------------------------------------------------------------------
# Construcción del vector de features (orden estable de config.FEATURES_RUL)
# ------------------------------------------------------------------
def construir_features(df: pd.DataFrame, probas_pln: np.ndarray) -> pd.DataFrame:
    """
    df requiere las columnas estructuradas de la tesis;
    probas_pln: matriz (n, 6) en el orden de config.CATEGORIAS_FALLA.
    Devuelve DataFrame con columnas = config.FEATURES_RUL.
    """
    X = pd.DataFrame(index=df.index)
    X["edad_anios"] = pd.to_numeric(df["edad_anios"], errors="coerce")
    X["criticidad_puntaje"] = df["criticidad"].map(config.CRITICIDAD_PUNTAJE).fillna(2)
    X["dias_desde_ultima_intervencion"] = pd.to_numeric(
        df["dias_desde_ultima_intervencion"], errors="coerce"
    ).fillna(180)
    X["num_ot_previas_12m"] = pd.to_numeric(df["num_ot_previas_12m"], errors="coerce").fillna(0)
    X["num_reportes_oclusion_previos"] = pd.to_numeric(
        df["num_reportes_oclusion_previos"], errors="coerce"
    ).fillna(0)
    X["deriva_calibracion_previa"] = pd.to_numeric(
        df["deriva_calibracion_previa"], errors="coerce"
    ).fillna(0)

    for i, cat in enumerate(config.CATEGORIAS_FALLA):
        X[f"prob_{cat}"] = probas_pln[:, i] if probas_pln is not None else 0.0

    return X[config.FEATURES_RUL].fillna(0.0)


def construir_features_estructuradas(df: pd.DataFrame) -> pd.DataFrame:
    """Versión SOLO estructurada (línea base para la hipótesis H1 de la tesis)."""
    probs_cero = np.zeros((len(df), len(config.CATEGORIAS_FALLA)))
    return construir_features(df, probs_cero)


# ------------------------------------------------------------------
# Modelos de regresión
# ------------------------------------------------------------------
def _construir_regressor():
    if config.RUL_ALGORITMO == "RandomForest":
        return RandomForestRegressor(
            n_estimators=config.RUL_N_ESTIMATORS,
            max_depth=config.RUL_MAX_DEPTH,
            random_state=config.RANDOM_SEED,
            n_jobs=-1,
        )
    from xgboost import XGBRegressor
    return XGBRegressor(
        n_estimators=config.RUL_N_ESTIMATORS,
        max_depth=config.RUL_MAX_DEPTH,
        learning_rate=config.RUL_LEARNING_RATE,
        subsample=config.RUL_SUBSAMPLE,
        colsample_bytree=config.RUL_COLSAMPLE,
        reg_lambda=1.0,
        random_state=config.RANDOM_SEED,
        objective="reg:squarederror",
        tree_method="hist",
        verbosity=0,
    )


class ModeloRUL:
    """Regresor de días hasta la próxima falla con features híbridas."""

    def __init__(self):
        self.modelo = _construir_regressor()

    def entrenar(self, X: pd.DataFrame, y: pd.Series):
        self.modelo.fit(X.values, y.values)
        return self

    def predecir(self, X: pd.DataFrame) -> np.ndarray:
        pred = self.modelo.predict(X.values)
        return np.clip(pred, 3, 540)  # límites físicos razonables (3-540 días)

    def importancia_global(self) -> list:
        """Importancia media de features (respaldo interpretable de SHAP)."""
        importancias = getattr(self.modelo, "feature_importances_", None)
        if importancias is None:
            return []
        pares = sorted(
            zip(config.FEATURES_RUL, importancias), key=lambda p: -p[1]
        )
        return [
            {"feature": f, "importancia": round(float(v), 4),
             "etiqueta": config.ETIQUETAS_FEATURES.get(f, f)}
            for f, v in pares
        ]


# ------------------------------------------------------------------
# Métricas de regresión (RMSE, MAE — tesis H1)
# ------------------------------------------------------------------
def metricas_regresion(y_true, y_pred) -> dict:
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    return {
        "rmse_dias": round(rmse, 2),
        "mae_dias": round(float(mean_absolute_error(y_true, y_pred)), 2),
        "r2": round(float(r2_score(y_true, y_pred)), 4),
    }
