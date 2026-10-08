"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/main_pipeline.py
Runner standalone del estudio científico (Fase 2 del PROMPT MAESTRO).

Uso (desde la carpeta backend/):
    python -m ml.main_pipeline dataset    # regenera el dataset sintético
    python -m ml.main_pipeline entrenar   # entrena el pipeline de producción (N3)
    python -m ml.main_pipeline ablacion   # estudio de ablación 3 niveles
    python -m ml.main_pipeline h1         # contraste H1 híbrido vs estructurado
    python -m ml.main_pipeline todo       # ejecuta todo y muestra el resumen
"""

import json
import sys


def _imprimir(titulo: str, datos: dict):
    print(f"\n{'=' * 70}\n{titulo}\n{'=' * 70}")
    print(json.dumps(datos, ensure_ascii=False, indent=2, default=str))


def paso_dataset():
    from ml.data.generar_dataset import main as generar
    generar()
    return {"ok": True, "paso": "dataset"}


def paso_entrenar():
    from ml.entrenar import entrenar_todo
    return entrenar_todo()


def paso_ablacion():
    from ml.entrenar import cargar_dataset
    from ml.ablation import ejecutar_ablacion
    df = cargar_dataset()
    resultado = ejecutar_ablacion(df)
    tabla = resultado["tabla_comparativa"]
    print("\n--- TABLA COMPARATIVA DE ABLACIÓN ---")
    print(f"{'Nivel':6} {'F1 macro':>10} {'AUC OvR':>10} {'RMSE (d)':>10} {'MAE (d)':>10}")
    for f in tabla:
        print(f"{f['nivel']:6} {f.get('f1_macro_media'):>10} {f.get('auc_roc_ovr_media'):>10} "
              f"{f.get('rmse_dias_media'):>10} {f.get('mae_dias_media'):>10}")
    _imprimir("PRUEBA ESTADÍSTICA N3 vs N2", resultado["prueba_estadistica_n3_vs_n2"])
    return {"ok": True, "tabla": tabla, "prueba": resultado["prueba_estadistica_n3_vs_n2"]}


def paso_h1():
    from ml.entrenar import cargar_dataset
    from ml.validacion import validar_h1
    df = cargar_dataset()
    resultado = validar_h1(df)
    _imprimir("HIPÓTESIS H1 — HÍBRIDO VS ESTRUCTURADO", resultado)
    return resultado


def paso_exportar():
    from ml.entrenar import cargar_dataset
    from ml.exportar import exportar_todo
    df = cargar_dataset()
    return exportar_todo(df)


def paso_todo():
    r1 = paso_dataset()
    r2 = paso_entrenar()
    r3 = paso_ablacion()
    r4 = paso_h1()
    r5 = paso_exportar()

    from ml.metrics_logger import estadisticas_h3
    h3 = estadisticas_h3()

    print(f"\n{'=' * 70}\nRESUMEN CIENTÍFICO (tesis CMMS-BioAI)\n{'=' * 70}")
    print(f"Dataset sintético regenerado:      {'OK' if r1.get('ok') else 'FALLO'}")
    print(f"F1-Score producción (N3):          {r2['clasificacion']['f1_macro']}")
    print(f"AUC-ROC OvR producción:            {r2['clasificacion'].get('auc_roc_ovr')}")
    print(f"RMSE RUL:                          {r2['regresion']['rmse_dias']} días")
    print(f"MAE RUL:                           {r2['regresion']['mae_dias']} días")
    print(f"H1 (mejora híbrido vs estructurado): {r4['mejora_relativa_media']} — {r4['conclusion']}")
    print(f"H3 (tiempos de inferencia):        {h3}")
    print("\nReportes generados en ml/reports/ y modelos en ml/models/")
    return {"dataset": r1, "entrenamiento": r2, "ablacion": r3, "h1": r4,
            "exportacion": r5, "h3": h3}


if __name__ == "__main__":
    comando = sys.argv[1] if len(sys.argv) > 1 else "todo"
    acciones = {
        "dataset": paso_dataset,
        "entrenar": paso_entrenar,
        "ablacion": paso_ablacion,
        "h1": paso_h1,
        "todo": paso_todo,
    }
    if comando not in acciones:
        print(__doc__)
        sys.exit(1)
    acciones[comando]()
