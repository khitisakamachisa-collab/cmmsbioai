"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/validacion.py
Validación cruzada estratificada k=5 POR EQUIPO y contraste de la Hipótesis H1.

- StratifiedGroupKFold: estratifica por tipo de falla (y) agrupando por equipo_id
  (groups) para mitigar la correlación intraclase — exactamente lo que exige la
  tesis §3.10 ("estratificación por equipo").
- H1: el modelo híbrido (texto PLN + estructuradas) debe superar en ≥15% el
  F1-Score del modelo solo estructurado (α=0.05), con prueba pareada por pliegue
  (t de Student o Wilcoxon si no hay normalidad).
"""

import json
import numpy as np
import pandas as pd
from scipy.stats import shapiro, ttest_rel, wilcoxon
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import f1_score, roc_auc_score
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ml import config
from ml.preprocesamiento import preprocesar

# Features estructuradas del clasificador (sin probabilidades PLN, para evitar fuga)
FEATURES_CLS = [
    "edad_anios", "criticidad_puntaje", "dias_desde_ultima_intervencion",
    "num_ot_previas_12m", "num_reportes_oclusion_previos", "deriva_calibracion_previa",
    "es_mantenimiento_programado",
]


def pliegues_estratificados_por_equipo(df: pd.DataFrame, k: int = 5) -> list:
    """Devuelve lista de (df_train, df_test) estratificados por equipo."""
    sgkf = StratifiedGroupKFold(n_splits=k, shuffle=True, random_state=config.RANDOM_SEED)
    pliegues = []
    for tr_idx, te_idx in sgkf.split(df, df["tipo_falla"], groups=df["equipo_id"]):
        pliegues.append((df.iloc[tr_idx].reset_index(drop=True),
                         df.iloc[te_idx].reset_index(drop=True)))
    return pliegues


def _df_con_criticidad(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["criticidad_puntaje"] = df["criticidad"].map(config.CRITICIDAD_PUNTAJE).fillna(2)
    # Feature estructurada legítima disponible al momento de clasificar la OT:
    # las OTs programadas (preventivo/calibración) casi siempre son clase 'otra'
    df["es_mantenimiento_programado"] = (
        ~df["tipo_mantenimiento"].astype(str).str.lower().eq("correctivo")
    ).astype(int)
    return df


def _clasificador(tipo: str) -> Pipeline:
    """
    tipo='híbrido': TF-IDF(texto) + estructuradas → RandomForest
    tipo='estructurado': solo estructuradas → RandomForest (misma familia/algoritmo
    para un contraste justo, siguiendo el protocolo de la tesis).
    """
    if tipo == "hibrido":
        pre = ColumnTransformer([
            ("texto", TfidfVectorizer(max_features=config.TFIDF_MAX_FEATURES,
                                      preprocessor=lambda t: preprocesar(t, "N3")), "texto_libre"),
            ("num", StandardScaler(), FEATURES_CLS),
        ])
    else:
        pre = ColumnTransformer([
            ("num", StandardScaler(), FEATURES_CLS),
        ])
    clf = RandomForestClassifier(
        n_estimators=300, max_depth=8, random_state=config.RANDOM_SEED, n_jobs=-1
    )
    return Pipeline([("pre", pre), ("clf", clf)])


def _evaluar_clasificador(pipe: Pipeline, df_tr: pd.DataFrame, df_te: pd.DataFrame) -> dict:
    X_tr = df_tr[["texto_libre"] + FEATURES_CLS]
    X_te = df_te[["texto_libre"] + FEATURES_CLS]
    pipe.fit(X_tr, df_tr["tipo_falla"])
    y_pred = pipe.predict(X_te)
    metricas = {"f1_macro": float(f1_score(df_te["tipo_falla"], y_pred,
                                           labels=config.CATEGORIAS_FALLA, average="macro",
                                           zero_division=0))}
    try:
        probas = pipe.predict_proba(X_te)
        metricas["auc_roc_ovr"] = float(roc_auc_score(
            df_te["tipo_falla"], probas, labels=config.CATEGORIAS_FALLA, multi_class="ovr", average="macro"
        ))
    except Exception:
        metricas["auc_roc_ovr"] = None
    return metricas


def validar_h1(df: pd.DataFrame, guardar: bool = True) -> dict:
    """
    Contraste completo de H1 con CV estratificada por equipo:
    F1(híbrido) vs F1(estructurado) pareado por pliegue.
    """
    df = _df_con_criticidad(df)
    pliegues = pliegues_estratificados_por_equipo(df, k=config.CV_FOLDS)

    f1_hibrido, f1_estructurado, auc_hibrido, auc_estructurado = [], [], [], []
    detalle_pliegues = []

    for i, (tr, te) in enumerate(pliegues, start=1):
        m_h = _evaluar_clasificador(_clasificador("hibrido"), tr, te)
        m_e = _evaluar_clasificador(_clasificador("estructurado"), tr, te)
        f1_hibrido.append(m_h["f1_macro"])
        f1_estructurado.append(m_e["f1_macro"])
        if m_h.get("auc_roc_ovr") is not None:
            auc_hibrido.append(m_h["auc_roc_ovr"])
        if m_e.get("auc_roc_ovr") is not None:
            auc_estructurado.append(m_e["auc_roc_ovr"])
        detalle_pliegues.append({
            "pliegue": i,
            "n_train": int(len(tr)), "n_test": int(len(te)),
            "f1_hibrido": round(m_h["f1_macro"], 4),
            "f1_estructurado": round(m_e["f1_macro"], 4),
            "auc_hibrido": round(m_h["auc_roc_ovr"], 4) if m_h.get("auc_roc_ovr") else None,
            "auc_estructurado": round(m_e["auc_roc_ovr"], 4) if m_e.get("auc_roc_ovr") else None,
        })

    f1_h = np.array(f1_hibrido)
    f1_e = np.array(f1_estructurado)
    mejora = (f1_h - f1_e) / np.where(f1_e > 0, f1_e, 1e-9)

    # Normalidad de las diferencias (para elegir t de Student vs Wilcoxon)
    diffs = f1_h - f1_e
    try:
        _, p_norm = shapiro(diffs) if len(diffs) >= 3 else (None, 1.0)
    except Exception:
        p_norm = 1.0

    if p_norm is not None and p_norm >= config.ALPHA_ESTADISTICO:
        stat, p_valor = ttest_rel(f1_h, f1_e, alternative="greater")
        prueba_usada = "t de Student pareada (unilateral, híbrido > estructurado)"
    else:
        try:
            stat, p_valor = wilcoxon(f1_h, f1_e, alternative="greater", method="exact")
        except Exception:
            stat, p_valor = None, None
        prueba_usada = "Wilcoxon pareado (unilateral, rangos con signo)"

    mejora_media = float(np.mean(mejora))
    h1_cumple = (
        p_valor is not None
        and p_valor < config.ALPHA_ESTADISTICO
        and mejora_media >= config.H1_MEJORA_MINIMA
    )

    resultado = {
        "hipotesis": "H1: el modelo híbrido (PLN+RUL) supera en ≥15% el F1 del modelo solo estructurado",
        "alpha": config.ALPHA_ESTADISTICO,
        "cv_folds": config.CV_FOLDS,
        "estratificacion": "por equipo (StratifiedGroupKFold)",
        "f1_hibrido_media": round(float(f1_h.mean()), 4),
        "f1_hibrido_std": round(float(f1_h.std()), 4),
        "f1_estructurado_media": round(float(f1_e.mean()), 4),
        "f1_estructurado_std": round(float(f1_e.std()), 4),
        "mejora_relativa_media": round(mejora_media, 4),
        "mejora_minima_requerida": config.H1_MEJORA_MINIMA,
        "auc_hibrido_media": round(float(np.mean(auc_hibrido)), 4) if auc_hibrido else None,
        "auc_estructurado_media": round(float(np.mean(auc_estructurado)), 4) if auc_estructurado else None,
        "prueba_estadistica": prueba_usada,
        "estadistico": round(float(stat), 4) if stat is not None else None,
        "p_valor": round(float(p_valor), 6) if p_valor is not None else None,
        "shapiro_p_diferencias": round(float(p_norm), 4) if p_norm is not None else None,
        "h1_cumple": bool(h1_cumple),
        "conclusion": (
            "SE CUMPLE H1: mejora relativa ≥ 15% con significancia estadística (p < α)."
            if h1_cumple else
            "H1 NO SE CUMPLE en esta muestra sintética: revisar mejora relativa/p-valor."
        ),
        "detalle_por_pliegue": detalle_pliegues,
    }

    if guardar:
        with open(config.REPORTE_H1_JSON, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)

    return resultado
