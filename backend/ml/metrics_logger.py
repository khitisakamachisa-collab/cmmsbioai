"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/metrics_logger.py
Cronómetro de inferencia y log JSONL (valida la Hipótesis H3 de la tesis).

- Cronómetro: time.perf_counter() alrededor del pipeline COMPLETO
  (entrada de datos → preprocesamiento → clasificación PLN → features → RUL
  → SHAP → texto explicativo).
- Log de cada inferencia: timestamp, equipo, RUL predicho, tipo de falla,
  tiempo_ms y valores SHAP (formato JSONL, una línea por inferencia).
"""

import json
import time
from datetime import datetime

from ml import config


class CronometroInferencia:
    """Context manager que mide el tiempo completo con time.perf_counter()."""

    def __init__(self):
        self.t0 = None
        self.tiempo_s = None

    def __enter__(self):
        self.t0 = time.perf_counter()
        return self

    def __exit__(self, *exc):
        self.tiempo_s = time.perf_counter() - self.t0
        return False

    @property
    def tiempo_ms(self) -> float:
        return round((self.tiempo_s or 0) * 1000.0, 2)

    def cumple_h3(self) -> bool:
        """H3: pipeline completo < 2 s en hardware estándar sin GPU."""
        return self.tiempo_s is not None and self.tiempo_s < config.H3_TIEMPO_MAXIMO_S


def log_inferencia(equipo_id, numero_serie, rul_pred, tipo_falla, tiempo_ms,
                   shap_top: list, umbral_h3_s: float = None) -> dict:
    """Agrega una línea al log JSONL de inferencias (anónima, sin datos sensibles)."""
    registro = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "equipo_id": equipo_id,
        "numero_serie": numero_serie,          # código de activo (no contiene personas)
        "rul_dias": round(float(rul_pred), 1) if rul_pred is not None else None,
        "tipo_falla_predicho": tipo_falla,
        "tiempo_ms": round(float(tiempo_ms), 2),
        "cumple_h3": (tiempo_ms / 1000.0) < (umbral_h3_s or config.H3_TIEMPO_MAXIMO_S),
        "shap_top": [
            {"feature": s["feature"], "etiqueta": s["etiqueta"],
             "shap": s["shap"], "direccion": s["direccion"]}
            for s in (shap_top or [])
        ],
    }
    with open(config.LOG_INFERENCIAS, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def log_entrenamiento(n_ots: int, f1: float, auc: float, rmse: float, mae: float,
                      tiempo_entrenamiento_s: float, dataset: str) -> dict:
    """Registra cada reentrenamiento (trazabilidad científica)."""
    registro = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "evento": "entrenamiento_pipeline",
        "dataset": dataset,
        "n_ots": n_ots,
        "f1_macro": round(float(f1), 4) if f1 is not None else None,
        "auc_roc_ovr": round(float(auc), 4) if auc is not None else None,
        "rmse_dias": round(float(rmse), 2) if rmse is not None else None,
        "mae_dias": round(float(mae), 2) if mae is not None else None,
        "tiempo_entrenamiento_s": round(float(tiempo_entrenamiento_s), 2),
    }
    with open(config.LOG_ENTRENAMIENTOS, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return registro


def leer_logs_inferencias(ultimos: int = 100) -> list:
    """Devuelve las últimas N inferencias registradas (para el dashboard)."""
    if not config.LOG_INFERENCIAS.exists():
        return []
    lineas = config.LOG_INFERENCIAS.read_text(encoding="utf-8").strip().splitlines()
    out = []
    for ln in lineas[-ultimos:]:
        try:
            out.append(json.loads(ln))
        except Exception:
            continue
    return out


def estadisticas_h3() -> dict:
    """Resumen de tiempos de inferencia (H3) a partir del log."""
    logs = leer_logs_inferencias(ultimos=10000)
    tiempos = [l["tiempo_ms"] for l in logs if l.get("tiempo_ms") is not None]
    if not tiempos:
        return {"n_inferencias": 0, "mensaje": "Sin inferencias registradas todavía."}
    import numpy as np
    tiempos_arr = np.array(tiempos)
    return {
        "n_inferencias": len(tiempos_arr),
        "tiempo_ms_media": round(float(tiempos_arr.mean()), 2),
        "tiempo_ms_mediana": round(float(np.median(tiempos_arr)), 2),
        "tiempo_ms_p95": round(float(np.percentile(tiempos_arr, 95)), 2),
        "tiempo_ms_max": round(float(tiempos_arr.max()), 2),
        "umbral_h3_ms": config.H3_TIEMPO_MAXIMO_S * 1000,
        "h3_cumple_media": bool(tiempos_arr.mean() < config.H3_TIEMPO_MAXIMO_S * 1000),
        "h3_cumple_p95": bool(np.percentile(tiempos_arr, 95) < config.H3_TIEMPO_MAXIMO_S * 1000),
    }
