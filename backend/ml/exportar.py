"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/exportar.py
Exportación científica ANONIMIZADA (restricción 6 del PROMPT MAESTRO y Ley 164).

Genera los archivos para el análisis externo (Python/R) y para las tablas
de la tesis:
  - predicciones_vs_realidad.csv     → RMSE/MAE del RUL
  - matriz_confusion.csv             → F1-Score del clasificador
  - tiempos_inferencia.csv           → validación H3
  - valores_shap.csv                 → evaluación Likert con expertos (H2)

Anonimización aplicada: sin nombres de técnicos, pacientes ni instituciones;
el equipo se identifica con su código de activo (EQ-XX) y la OT con OT-XXXX.
"""

import csv
import json
import time

import numpy as np
import pandas as pd

from ml import config
from ml.pln import ClasificadorPLN, matriz_confusion
from ml.rul import ModeloRUL, construir_features
from ml.preprocesamiento import preprocesar
from ml.xai import valores_shap
from ml.validacion import _df_con_criticidad, pliegues_estratificados_por_equipo
from sklearn.model_selection import train_test_split


def _escribir_csv(ruta, encabezados, filas):
    with open(ruta, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(encabezados)
        w.writerows(filas)
    return str(ruta)


def exportar_predicciones_vs_realidad(df: pd.DataFrame) -> str:
    """RUL real vs predicho por OT (predicciones out-of-fold, sin fuga de datos)."""
    df = _df_con_criticidad(df)
    pliegues = pliegues_estratificados_por_equipo(df, k=config.CV_FOLDS)
    filas = []
    for df_tr, df_te in pliegues:
        pln = ClasificadorPLN("N3").entrenar(df_tr["texto_libre"].tolist(),
                                             df_tr["tipo_falla"].tolist())
        X_tr = construir_features(df_tr, pln.probabilidades(df_tr["texto_libre"].tolist()))
        X_te = construir_features(df_te, pln.probabilidades(df_te["texto_libre"].tolist()))
        rul = ModeloRUL().entrenar(X_tr, df_tr["dias_hasta_proxima_falla"])
        pred = rul.predecir(X_te)
        for (_, fila), p in zip(df_te.iterrows(), pred):
            filas.append([
                f"OT-{int(fila.name) + 1:04d}" if isinstance(fila.name, int) else str(fila.get("ot_id", "")),
                f"EQ-{int(fila['equipo_id']):02d}",
                round(float(fila["dias_hasta_proxima_falla"]), 1),
                round(float(p), 1),
                round(float(p - fila["dias_hasta_proxima_falla"]), 1),
                fila["tipo_falla"],
            ])
    return _escribir_csv(
        config.REPORTE_PREDICCIONES_CSV,
        ["ot_anon", "equipo_anon", "rul_real_dias", "rul_predicho_dias", "error_dias", "tipo_falla"],
        filas,
    )


def exportar_matriz_confusion(df: pd.DataFrame) -> str:
    """Matriz de confusión out-of-fold del clasificador N3 (para F1 de la tesis)."""
    df = _df_con_criticidad(df)
    pliegues = pliegues_estratificados_por_equipo(df, k=config.CV_FOLDS)
    y_true, y_pred = [], []
    for df_tr, df_te in pliegues:
        pln = ClasificadorPLN("N3").entrenar(df_tr["texto_libre"].tolist(),
                                             df_tr["tipo_falla"].tolist())
        y_true.extend(df_te["tipo_falla"].tolist())
        y_pred.extend(pln.predecir(df_te["texto_libre"].tolist()))
    cm = matriz_confusion(y_true, y_pred)
    return _escribir_csv(
        config.REPORTE_MATRIZ_CONFUSION_CSV,
        ["clase_real\\predicha"] + config.CATEGORIAS_FALLA,
        [[cat] + fila for cat, fila in zip(config.CATEGORIAS_FALLA, cm)],
    )


def exportar_tiempos_inferencia(df: pd.DataFrame, n_muestras: int = 60) -> str:
    """Cronometra el pipeline completo de inferencia (H3) sobre n muestras."""
    from ml.predictor import cargar_modelos, construir_datos_bomba, predecir
    cargar_modelos(forzar=True)

    df_muestra = df.sample(n=min(n_muestras, len(df)), random_state=config.RANDOM_SEED)
    filas = []
    for _, fila in df_muestra.iterrows():
        equipo = {
            "id": int(fila["equipo_id"]),
            "numero_serie": f"EQ-{int(fila['equipo_id']):02d}",
            "fecha_adquisicion": None,
            "criticidad": fila["criticidad"],
        }
        datos = construir_datos_bomba(equipo, [], texto_libre=fila["texto_libre"])
        r = predecir(datos, equipo_id=equipo["id"], numero_serie=equipo["numero_serie"],
                     registrar_log=True)  # cada medición queda en el log JSONL (evidencia H3)
        filas.append([
            str(fila.get("ot_id", "")), f"EQ-{int(fila['equipo_id']):02d}",
            r["rul_dias"], r["tipo_falla_predicho"], r["tiempo_ms"], r["cumple_h3"],
        ])
    return _escribir_csv(
        config.REPORTE_TIEMPOS_CSV,
        ["ot_anon", "equipo_anon", "rul_dias", "tipo_falla", "tiempo_ms", "cumple_h3"],
        filas,
    )


def exportar_valores_shap(df: pd.DataFrame) -> str:
    """SHAP por muestra del conjunto de prueba (insumo del cuestionario Likert H2)."""
    df = _df_con_criticidad(df)
    df_tr, df_te = train_test_split(df, test_size=0.25,
                                    random_state=config.RANDOM_SEED,
                                    stratify=df["tipo_falla"])
    pln = ClasificadorPLN("N3").entrenar(df_tr["texto_libre"].tolist(),
                                         df_tr["tipo_falla"].tolist())
    X_te = construir_features(df_te, pln.probabilidades(df_te["texto_libre"].tolist()))
    X_tr = construir_features(df_tr, pln.probabilidades(df_tr["texto_libre"].tolist()))
    rul = ModeloRUL().entrenar(X_tr, df_tr["dias_hasta_proxima_falla"])
    sv = valores_shap(rul, X_te.values)

    filas = []
    for idx, (pos, (_, fila)) in enumerate(zip(range(len(X_te)), df_te.iterrows())):
        for j, feat in enumerate(config.FEATURES_RUL):
            filas.append([
                str(fila.get("ot_id", f"F{idx}")),
                f"EQ-{int(fila['equipo_id']):02d}", feat,
                round(float(X_te.values[pos, j]), 4),
                round(float(sv[pos, j]), 4),
            ])
    return _escribir_csv(
        config.REPORTE_SHAP_CSV,
        ["ot_anon", "equipo_anon", "feature", "valor_feature", "valor_shap"],
        filas,
    )


def exportar_todo(df: pd.DataFrame = None) -> dict:
    """Genera todos los reportes científicos anonimizados."""
    from ml.entrenar import cargar_dataset
    if df is None:
        df = cargar_dataset()
    resultado = {
        "predicciones_vs_realidad": exportar_predicciones_vs_realidad(df),
        "matriz_confusion": exportar_matriz_confusion(df),
        "tiempos_inferencia": exportar_tiempos_inferencia(df),
        "valores_shap": exportar_valores_shap(df),
    }
    with open(config.REPORTS_DIR / "exportacion_index.json", "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)
    return resultado
