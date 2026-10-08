"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/ablation.py
Estudio de ABLACIÓN del preprocesamiento en 3 niveles (tesis, Fase 2).

Entrena y evalúa el pipeline completo bajo las 3 configuraciones:
  N1 texto crudo → N2 limpieza genérica agresiva → N3 limpieza consciente del dominio
y genera la tabla comparativa F1-Score, AUC-ROC, RMSE y MAE por nivel,
incluyendo la prueba estadística pareada N3 vs N2 (Wilcoxon sobre pliegues
de la validación cruzada estratificada por equipo).
"""

import json
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon, ttest_rel

from ml import config
from ml.pln import ClasificadorPLN, metricas_clasificacion
from ml.rul import ModeloRUL, construir_features, metricas_regresion
from ml.validacion import pliegues_estratificados_por_equipo


def _evaluar_nivel_en_fold(df_tr, df_te, nivel: str) -> dict:
    """Entrena PLN+RUL en el pliegue de entrenamiento y evalúa en el de prueba."""
    pln = ClasificadorPLN(nivel).entrenar(df_tr["texto_libre"].tolist(), df_tr["tipo_falla"].tolist())
    y_pred = pln.predecir(df_te["texto_libre"].tolist())
    probas = pln.probabilidades(df_te["texto_libre"].tolist())

    m_cls = metricas_clasificacion(df_te["tipo_falla"].tolist(), y_pred, probas)

    # RUL con probabilidades del PLN de este nivel
    X_te = construir_features(df_te, probas)
    X_tr = construir_features(df_tr, pln.probabilidades(df_tr["texto_libre"].tolist()))
    rul = ModeloRUL().entrenar(X_tr, df_tr["dias_hasta_proxima_falla"])
    y_rul_pred = rul.predecir(X_te)
    m_rul = metricas_regresion(df_te["dias_hasta_proxima_falla"], y_rul_pred)

    return {
        "f1_macro": m_cls["f1_macro"],
        "auc_roc_ovr": m_cls.get("auc_roc_ovr"),
        "rmse_dias": m_rul["rmse_dias"],
        "mae_dias": m_rul["mae_dias"],
        "_probas": probas,
        "_pln": pln,
        "_rul": rul,
        "_y_pred": y_pred,
    }


def ejecutar_ablacion(df: pd.DataFrame, guardar: bool = True) -> dict:
    """
    Ejecuta el estudio de ablación completo con CV estratificada por equipo (k=5).
    Devuelve tabla comparativa + prueba estadística N3 vs N2.
    """
    pliegues = pliegues_estratificados_por_equipo(df, k=config.CV_FOLDS)
    niveles = ["N1", "N2", "N3"]

    # Métricas por pliegue y nivel (para IC y prueba pareada)
    fold_metrics = {n: {"f1_macro": [], "auc_roc_ovr": [], "rmse_dias": [], "mae_dias": []}
                    for n in niveles}
    ultimo_estado = {}

    for nombre_nivel in niveles:
        for i, (df_tr, df_te) in enumerate(pliegues):
            r = _evaluar_nivel_en_fold(df_tr, df_te, nombre_nivel)
            for k in fold_metrics[nombre_nivel]:
                v = r[k]
                if v is not None:
                    fold_metrics[nombre_nivel][k].append(float(v))
            ultimo_estado[nombre_nivel] = r

    # ------------------------------------------------------------------
    # Tabla comparativa (media ± desviación estándar)
    # ------------------------------------------------------------------
    tabla = []
    for n in niveles:
        fila = {"nivel": n, "descripcion": config.NIVELES_PREPROCESAMIENTO[n]}
        for k, valores in fold_metrics[n].items():
            if valores:
                fila[f"{k}_media"] = round(float(np.mean(valores)), 4)
                fila[f"{k}_std"] = round(float(np.std(valores)), 4)
            else:
                fila[f"{k}_media"], fila[f"{k}_std"] = None, None
        tabla.append(fila)

    # ------------------------------------------------------------------
    # Prueba estadística pareada UNILATERAL N3 > N2 (protocolo de la tesis §3.10):
    #   1) Shapiro-Wilk sobre las diferencias por pliegue (α=0.05)
    #   2) Si normalidad → t de Student pareada (unilateral); si no → Wilcoxon
    # La hipótesis de la tesis es direccional (N3 superior) → alternative='greater'.
    # ------------------------------------------------------------------
    from scipy.stats import shapiro
    f1_n3 = fold_metrics["N3"]["f1_macro"]
    f1_n2 = fold_metrics["N2"]["f1_macro"]
    diffs = np.array(f1_n3) - np.array(f1_n2)
    prueba = {"comparacion": "N3 vs N2 (F1-Score macro, pareado por pliegue, unilateral N3>N2)",
              "alpha": config.ALPHA_ESTADISTICO, "n_pliegues": len(f1_n3),
              "diferencias_por_pliegue": [round(float(d), 4) for d in diffs]}
    try:
        _, p_shapiro = shapiro(diffs)
        prueba["shapiro_wilk_p_diferencias"] = round(float(p_shapiro), 4)
    except Exception:
        p_shapiro = 1.0
        prueba["shapiro_wilk_p_diferencias"] = None

    if p_shapiro is not None and p_shapiro >= config.ALPHA_ESTADISTICO:
        stat_t, p_t = ttest_rel(f1_n3, f1_n2, alternative="greater")
        prueba["prueba_aplicada"] = "t de Student pareada (unilateral) — diferencias normales (Shapiro p ≥ α)"
        prueba["estadistico"] = round(float(stat_t), 4)
        prueba["p_valor"] = round(float(p_t), 6)
        prueba["p_valor_primario"] = round(float(p_t), 6)
        try:  # Wilcoxon como referencia complementaria
            stat_w, p_w = wilcoxon(f1_n3, f1_n2, alternative="greater", method="exact")
            prueba["wilcoxon_p_referencial"] = round(float(p_w), 6)
        except Exception:
            pass
    else:
        try:
            stat_w, p_w = wilcoxon(f1_n3, f1_n2, alternative="greater", method="exact")
            prueba["prueba_aplicada"] = "Wilcoxon exacta pareada (unilateral) — diferencias no normales (Shapiro p < α)"
            prueba["estadistico"] = round(float(stat_w), 4)
            prueba["p_valor"] = round(float(p_w), 6)
            prueba["p_valor_primario"] = round(float(p_w), 6)
        except Exception as e:
            prueba["p_valor_primario"] = None
            prueba["error_wilcoxon"] = str(e)

    p_primario = prueba.get("p_valor_primario")
    if p_primario is not None:
        prueba["conclusion"] = (
            "N3 superior a N2 con significancia estadística unilateral (p < α) — valida la propuesta de la tesis."
            if p_primario < config.ALPHA_ESTADISTICO
            else "No se alcanza significancia estadística unilateral entre N3 y N2 en esta muestra."
        )

    resultado = {
        "tabla_comparativa": tabla,
        "prueba_estadistica_n3_vs_n2": prueba,
        "metricas_por_pliegue": fold_metrics,
        "cv_folds": config.CV_FOLDS,
        "estratificacion": "equipo (StratifiedGroupKFold sobre tipo de falla)",
    }

    if guardar:
        # CSV
        df_tab = pd.DataFrame(tabla)
        df_tab.to_csv(config.REPORTE_ABLACION_CSV, index=False, encoding="utf-8-sig")
        # JSON (sin objetos no serializables)
        resultado_limpio = {k: v for k, v in resultado.items() if k != "metricas_por_pliegue"}
        resultado_limpio["metricas_por_pliegue"] = fold_metrics
        with open(config.REPORTE_ABLACION_JSON, "w", encoding="utf-8") as f:
            json.dump(resultado_limpio, f, ensure_ascii=False, indent=2)

    return resultado
