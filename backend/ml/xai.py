"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/xai.py
Explicabilidad diagnóstica (XAI) con SHAP + generación de texto en lenguaje natural.

Tesis: los valores de Shapley cuantifican la contribución marginal de cada
feature (textual y estructurada) a la predicción del RUL, y se traducen a una
explicación auditable estilo: "Falla probable en 15 días. Factores principales:
3 reportes previos de 'oclusión' (+0.35), antigüedad >5 años (+0.22), ...".

Este módulo es la pieza que se evalúa con la escala Likert (Hipótesis H2).
"""

import numpy as np

from ml import config

# Palabras clave → texto diagnóstico en español
_DIAGNOSTICO_FAMILIA = {
    "mecanica": "patrones textuales de falla mecánica (oclusión / obstrucción del sistema)",
    "electrica": "patrones textuales de falla eléctrica (batería / alimentación)",
    "software": "patrones textuales de falla de software (reinicios / alarmas espurias)",
    "sensor": "patrones textuales de falla de sensor (burbujas / presión)",
    "calibracion": "evidencia textual de deriva metrológica",
    "otra": "patrones textuales no críticos (mantenimiento de rutina)",
}


# ------------------------------------------------------------------
# Cálculo de valores SHAP
# ------------------------------------------------------------------
def valores_shap(modelo_rul, X: np.ndarray) -> np.ndarray:
    """
    SHAP values para el modelo RUL (TreeExplainer — RF/XGBoost).
    Devuelve matriz (n_muestras, n_features). Con XGBoost, la suma de SHAP
    incluye el valor base en la posición extra del explainer; se reduce a
    contribuciones por feature.
    """
    import shap
    explainer = shap.TreeExplainer(modelo_rul.modelo)
    sv = explainer.shap_values(X, check_additivity=False)
    if isinstance(sv, list):  # RandomForest multissalida (raro en regresión)
        sv = sv[0]
    return np.array(sv)


def resumen_shap(shap_row: np.ndarray, x_row: np.ndarray, top_k: int = 5) -> list:
    """
    Resume la instancia: lista de {feature, etiqueta, valor, shap, direccion}
    ordenada por |shap| descendente. Se EXCLUYEN features con valor 0 (no aportan
    significado diagnóstico al experto: p.ej. '0 reportes previos').
    """
    candidatos = [i for i in range(len(x_row)) if abs(x_row[i]) > 1e-9]
    # Si todas son 0, devolver las de mayor |shap| igualmente (para trazabilidad)
    if not candidatos:
        candidatos = list(range(len(x_row)))
    candidatos.sort(key=lambda i: -abs(shap_row[i]))
    orden = candidatos[:top_k]
    items = []
    for i in orden:
        f = config.FEATURES_RUL[i]
        items.append({
            "feature": f,
            "etiqueta": config.ETIQUETAS_FEATURES.get(f, f),
            "valor": float(np.round(x_row[i], 3)),
            "shap": float(np.round(shap_row[i], 3)),
            "direccion": "acorta" if shap_row[i] < 0 else "extiende",
        })
    return items


def importancia_global_shap(modelo_rul, X: np.ndarray) -> list:
    """Media de |SHAP| por feature sobre una muestra de referencia (dashboard)."""
    sv = valores_shap(modelo_rul, X)
    media = np.abs(sv).mean(axis=0)
    pares = sorted(zip(config.FEATURES_RUL, media), key=lambda p: -p[1])
    return [
        {"feature": f, "importancia": round(float(v), 4),
         "etiqueta": config.ETIQUETAS_FEATURES.get(f, f)}
        for f, v in pares
    ]


# ------------------------------------------------------------------
# Generación de texto explicativo (español natural, auditable)
# ------------------------------------------------------------------
def _fmt_feature(item: dict) -> str:
    shap = item["shap"]
    signo = "+" if shap >= 0 else ""
    dias = abs(shap) * 1.0  # unidades de días (modelo en días)
    return f"{item['etiqueta']} ({signo}{dias:.2f} d)"


def texto_explicativo(rul_pred: float, tipo_falla: str, resumen: list, probas: dict = None) -> str:
    """
    Convierte la predicción + SHAP en un párrafo diagnóstico en español.
    Ejemplo (tesis): "Falla probable en 15 días. Factores principales:
    3 reportes previos de 'oclusión' (+0.35), antigüedad >5 años (+0.22)..."
    """
    if not resumen:
        return (
            f"Se estima una falla probable en ~{int(round(rul_pred))} días. "
            "Sin factores dominantes identificados (evidencia histórica insuficiente)."
        )

    # Los SHAP del regresor: valores negativos REDUCEN el RUL (acercan la falla)
    acortan = [i for i in resumen if i["shap"] < 0][:3]
    extienden = [i for i in resumen if i["shap"] > 0][:2]

    partes = [f"Falla probable en ~{int(round(rul_pred))} días."]

    if acortan:
        factores = []
        for i in acortan:
            nombre = _nombre_amigable(i)
            contrib = abs(i["shap"])
            factores.append(f"{nombre} (−{contrib:.2f} d)")
        partes.append("Factores que acercan la falla: " + ", ".join(factores) + ".")

    if extienden:
        factores = [f"{_nombre_amigable(i)} (+{i['shap']:.2f} d)" for i in extienden]
        partes.append("Factores que extienden la vida útil: " + ", ".join(factores) + ".")

    partes.append(
        f"Patrón de falla dominante detectado en el texto de las OTs: {_DIAGNOSTICO_FAMILIA.get(tipo_falla, tipo_falla)}."
    )

    if probas:
        mejor = max(probas, key=probas.get)
        if probas[mejor] >= 0.4 and mejor != "otra":
            partes.append(
                f"Clasificador PLN: {int(round(probas[mejor]*100))}% de confianza en falla de tipo {mejor}."
            )

    partes.append("Recomendación: programar intervención preventiva anticipada y verificar repuestos críticos.")
    return " ".join(partes)


def _nombre_amigable(item: dict) -> str:
    """Traduce features a frases de diagnóstico (ej. ejemplo de la tesis)."""
    f = item["feature"]
    v = item["valor"]
    if f == "num_reportes_oclusion_previos":
        return f"{int(v)} reporte(s) previo(s) de 'oclusión'"
    if f == "edad_anios":
        return f"antigüedad {v:.1f} años" + (" (>5 años)" if v > 5 else "")
    if f == "deriva_calibracion_previa":
        return "deriva previa en calibración"
    if f == "num_ot_previas_12m":
        return f"{int(v)} OT(s) correctiva(s) en 12 meses"
    if f == "dias_desde_ultima_intervencion":
        return f"{int(v)} días desde la última intervención"
    if f == "criticidad_puntaje":
        return "criticidad alta" if v >= 3 else "criticidad media"
    if f.startswith("prob_"):
        cat = f.replace("prob_", "")
        return _DIAGNOSTICO_FAMILIA.get(cat, cat)
    return item["etiqueta"]
