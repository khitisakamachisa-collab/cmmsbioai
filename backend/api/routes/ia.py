"""
CMMS-BioAI — RF07 Módulo Predictivo (IA) · api/routes/ia.py
Endpoints REST que exponen el pipeline PLN + RUL + XAI al frontend y al análisis externo.

Endpoints:
  GET  /ia/estado               → ¿modelos entrenados? + resumen de métricas
  POST /ia/entrenar             → entrena el pipeline completo (dataset o datos del CMMS)
  GET  /ia/resumen              → semáforo RUL de todas las bombas de infusión
  GET  /ia/predict/{equipo_id}  → predicción completa de una bomba (RUL + SHAP + tiempo)
  POST /ia/predict              → predicción manual con datos explícitos (demo/pruebas)
  GET  /ia/metricas             → métricas del entrenamiento + importancia global SHAP
  GET  /ia/ablation             → tabla del estudio de ablación (N1/N2/N3) + prueba N3 vs N2
  GET  /ia/h1                   → contraste de la hipótesis H1 (híbrido vs estructurado)
  GET  /ia/h3                   → estadísticas de tiempos de inferencia (H3)
  GET  /ia/logs                 → últimas inferencias registradas (JSONL)
  GET  /ia/exportar/{tipo}      → descarga CSV/JSON anonimizado (predicciones|matriz|tiempos|shap|ablacion)

Restricción offline: todo el cómputo es local (scikit-learn/XGBoost/SHAP, sin red).
"""

from typing import Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlmodel import Session, select

from database import get_session
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo

router = APIRouter(prefix="/ia", tags=["RF07 — Módulo Predictivo IA"])

TIPO_OBJETIVO = "Bomba de Infusión"


# ------------------------------------------------------------------
# Utilidades internas
# ------------------------------------------------------------------
def _cargar_modelos_o_error():
    from ml import predictor as pred
    if not pred.cargar_modelos():
        raise HTTPException(
            status_code=409,
            detail="Modelos no entrenados. Ejecute POST /ia/entrenar primero.",
        )
    return pred


def _historial_de_equipo(session: Session, equipo_id: int) -> list:
    """Convierte las OTs del CMMS al formato del módulo predictivo (sin fuga de datos)."""
    ots = session.exec(
        select(OrdenTrabajo)
        .where(OrdenTrabajo.equipo_id == equipo_id)
        .order_by(OrdenTrabajo.fecha_creacion)
    ).all()
    historial = []
    for ot in ots:
        tipo = "preventivo" if ot.orden_preventiva_id else "correctivo"
        historial.append({
            "fecha_ot": ot.fecha_creacion.date().isoformat() if ot.fecha_creacion else None,
            "tipo_mantenimiento": tipo,
            "descripcion_falla": ot.descripcion_falla or "",
        })
    return historial


def _equipo_a_dict(eq: Equipo) -> dict:
    return {
        "id": eq.id,
        "nombre_corto": eq.nombre_corto,
        "modelo": eq.modelo,
        "numero_serie": eq.numero_serie,
        "fecha_adquisicion": eq.fecha_adquisicion.isoformat() if eq.fecha_adquisicion else None,
        "criticidad": eq.criticidad or "Media",
        "tipo_equipo": eq.tipo_equipo or "Otro",
        "ubicacion_actual": eq.ubicacion_actual,
    }


# ------------------------------------------------------------------
# Estado y entrenamiento
# ------------------------------------------------------------------
@router.get("/estado")
def estado():
    """Estado del módulo predictivo y métricas del último entrenamiento."""
    from ml import config as mlcfg
    from ml.entrenar import esta_entrenado
    metricas = None
    if mlcfg.METRICAS_ENTRENAMIENTO.exists():
        import json
        with open(mlcfg.METRICAS_ENTRENAMIENTO, encoding="utf-8") as f:
            metricas = json.load(f)
    return {
        "entrenado": esta_entrenado(),
        "tipo_equipo_objetivo": TIPO_OBJETIVO,
        "categorias_falla": ["calibracion", "electrica", "mecanica", "otra", "sensor", "software"],
        "niveles_ablacion": mlcfg.NIVELES_PREPROCESAMIENTO,
        "metricas_entrenamiento": metricas,
    }


@router.post("/entrenar")
def entrenar(usar_dataset_sintetico: bool = True):
    """
    Entrena el pipeline PLN + RUL + XAI.
    usar_dataset_sintetico=True → usa ml/data/dataset_ot_bombas.csv (220 OTs, tesis).
    Con datos reales del CMMS: generar un CSV normalizado con la misma estructura
    y pasar usar_dataset_sintetico=false apuntando la ruta en ml/config.py.
    """
    from ml.entrenar import entrenar_todo
    try:
        return entrenar_todo(guardar=True)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=f"Dataset no encontrado: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en el entrenamiento: {e}")


# ------------------------------------------------------------------
# Predicción
# ------------------------------------------------------------------
@router.get("/resumen")
def resumen_parque(session: Session = Depends(get_session)):
    """Semáforo predictivo de todas las bombas de infusión (dashboard)."""
    pred = _cargar_modelos_o_error()
    bombas = session.exec(
        select(Equipo).where(Equipo.tipo_equipo == TIPO_OBJETIVO)
    ).all()
    if not bombas:
        return {
            "bombas": [],
            "mensaje": f"No hay equipos con tipo_equipo='{TIPO_OBJETIVO}'. "
                       f"Registre bombas de infusión en el inventario (RF01) para activar el módulo.",
        }
    historiales = {eq.id: _historial_de_equipo(session, eq.id) for eq in bombas}
    filas = pred.predecir_parque([_equipo_a_dict(eq) for eq in bombas], historiales)

    conteo = {"rojo": 0, "amarillo": 0, "verde": 0, "sin_datos": 0}
    for f in filas:
        nivel = (f.get("semaforo") or {}).get("nivel", "sin_datos")
        conteo[nivel] = conteo.get(nivel, 0) + 1
    return {"total": len(filas), "conteo_semaforo": conteo, "bombas": filas}


@router.get("/predict/{equipo_id}")
def predecir_equipo(equipo_id: int, session: Session = Depends(get_session)):
    """Predicción completa de una bomba: RUL + semáforo + SHAP + explicación + tiempo (H3)."""
    pred = _cargar_modelos_o_error()
    eq = session.get(Equipo, equipo_id)
    if not eq:
        raise HTTPException(status_code=404, detail=f"Equipo {equipo_id} no existe")
    if (eq.tipo_equipo or "") != TIPO_OBJETIVO:
        raise HTTPException(
            status_code=400,
            detail=f"El módulo predictivo solo aplica a '{TIPO_OBJETIVO}' "
                   f"(delimitación de la tesis). Este equipo es '{eq.tipo_equipo}'.",
        )
    historial = _historial_de_equipo(session, eq.id)
    datos = pred.construir_datos_bomba(_equipo_a_dict(eq), historial)
    resultado = pred.predecir(datos, equipo_id=eq.id, numero_serie=eq.numero_serie)
    resultado["n_ots_historial"] = len(historial)
    resultado["nombre_corto"] = eq.nombre_corto
    resultado["modelo"] = eq.modelo
    resultado["ubicacion_actual"] = eq.ubicacion_actual
    return resultado


class PrediccionManual(BaseModel):
    """Cuerpo para predicciones manuales (demo / evaluación con expertos H2)."""
    texto_libre: str
    edad_anios: float = 5.0
    criticidad: str = "Alta"
    dias_desde_ultima_intervencion: int = 180
    num_ot_previas_12m: int = 0
    num_reportes_oclusion_previos: int = 0
    deriva_calibracion_previa: int = 0
    equipo_id: Optional[int] = None
    numero_serie: Optional[str] = None


@router.post("/predict")
def predecir_manual(datos: PrediccionManual):
    """Predicción con datos explícitos (útil para la evaluación Likert de la tesis)."""
    pred = _cargar_modelos_o_error()
    registro = {
        "texto_libre": datos.texto_libre,
        "edad_anios": datos.edad_anios,
        "criticidad": datos.criticidad,
        "dias_desde_ultima_intervencion": datos.dias_desde_ultima_intervencion,
        "num_ot_previas_12m": datos.num_ot_previas_12m,
        "num_reportes_oclusion_previos": datos.num_reportes_oclusion_previos,
        "deriva_calibracion_previa": datos.deriva_calibracion_previa,
    }
    return pred.predecir(registro, equipo_id=datos.equipo_id, numero_serie=datos.numero_serie)


# ------------------------------------------------------------------
# Métricas científicas
# ------------------------------------------------------------------
@router.get("/metricas")
def metricas():
    """Métricas del último entrenamiento + importancia global de SHAP (dashboard)."""
    from ml import config as mlcfg
    import json
    if not mlcfg.METRICAS_ENTRENAMIENTO.exists():
        raise HTTPException(status_code=409, detail="Sin entrenamiento previo. Ejecute POST /ia/entrenar.")
    with open(mlcfg.METRICAS_ENTRENAMIENTO, encoding="utf-8") as f:
        return json.load(f)


@router.get("/ablation")
def ablation(ejecutar: bool = False):
    """
    Estudio de ablación (3 niveles de preprocesamiento).
    ejecutar=false → lee el reporte guardado (ml/reports/ablacion_resultados.json).
    ejecutar=true  → vuelve a ejecutar el estudio completo (CV k=5, ~1-2 min).
    """
    from ml import config as mlcfg
    import json
    if ejecutar or not mlcfg.REPORTE_ABLACION_JSON.exists():
        from ml.entrenar import cargar_dataset
        from ml.ablation import ejecutar_ablacion
        resultado = ejecutar_ablacion(cargar_dataset())
        return resultado
    with open(mlcfg.REPORTE_ABLACION_JSON, encoding="utf-8") as f:
        return json.load(f)


@router.get("/h1")
def hipotesis_h1(ejecutar: bool = False):
    """Contraste H1: F1 híbrido vs F1 estructurado (≥15% con α=0.05)."""
    from ml import config as mlcfg
    import json
    if ejecutar or not mlcfg.REPORTE_H1_JSON.exists():
        from ml.entrenar import cargar_dataset
        from ml.validacion import validar_h1
        return validar_h1(cargar_dataset())
    with open(mlcfg.REPORTE_H1_JSON, encoding="utf-8") as f:
        return json.load(f)


@router.get("/h3")
def hipotesis_h3():
    """Estadísticas de tiempos de inferencia (umbral < 2 s, sin GPU)."""
    from ml.metrics_logger import estadisticas_h3
    return estadisticas_h3()


@router.get("/logs")
def logs(ultimos: int = 50):
    """Últimas inferencias registradas (trazabilidad + evidencia H3)."""
    from ml.metrics_logger import leer_logs_inferencias
    return {"inferencias": leer_logs_inferencias(ultimos=ultimos)}


# ------------------------------------------------------------------
# Exportación científica anonimizada
# ------------------------------------------------------------------
@router.get("/exportar/{tipo}")
def exportar(tipo: str, formato: str = "csv"):
    """
    Descarga los reportes científicos anonimizados:
    tipo ∈ {predicciones, matriz, tiempos, shap, ablacion} — formato csv|json.
    """
    from ml import config as mlcfg

    mapas = {
        "predicciones": (mlcfg.REPORTE_PREDICCIONES_CSV, "predicciones_vs_realidad"),
        "matriz": (mlcfg.REPORTE_MATRIZ_CONFUSION_CSV, "matriz_confusion"),
        "tiempos": (mlcfg.REPORTE_TIEMPOS_CSV, "tiempos_inferencia"),
        "shap": (mlcfg.REPORTE_SHAP_CSV, "valores_shap"),
        "ablacion": (mlcfg.REPORTE_ABLACION_CSV, "ablacion_resultados"),
    }
    if tipo not in mapas:
        raise HTTPException(status_code=404, detail=f"Tipo '{tipo}' no válido. Use: {list(mapas)}")

    ruta_csv, nombre = mapas[tipo]
    if formato == "json":
        if not ruta_csv.exists():
            raise HTTPException(status_code=409, detail="Reporte no generado aún. Ejecute el estudio (POST /ia/entrenar + ablación).")
        import csv as _csv
        with open(ruta_csv, encoding="utf-8-sig") as f:
            lector = _csv.DictReader(f)
            data = list(lector)
        return {"tipo": tipo, "filas": data}

    if not ruta_csv.exists():
        raise HTTPException(status_code=409, detail="Reporte no generado aún. Ejecute el estudio primero.")
    return FileResponse(
        path=str(ruta_csv), media_type="text/csv",
        filename=f"cmmsbioai_{nombre}_anonimizado.csv",
    )
