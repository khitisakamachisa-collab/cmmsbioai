"""Diagnóstico rápido: por qué AUC es null y por qué el RUL no aprende."""
import numpy as np
import pandas as pd
from ml.entrenar import cargar_dataset
from ml import config

df = cargar_dataset()
print("Distribución target RUL:")
print(df["dias_hasta_proxima_falla"].describe())

# Correlaciones feature-target
X_num = df[["edad_anios", "dias_desde_ultima_intervencion", "num_ot_previas_12m",
            "num_reportes_oclusion_previos", "deriva_calibracion_previa",
            "dias_hasta_proxima_falla"]].copy()
X_num["criticidad_puntaje"] = df["criticidad"].map(config.CRITICIDAD_PUNTAJE)
print("\nCorrelaciones con dias_hasta_proxima_falla:")
print(X_num.corr()["dias_hasta_proxima_falla"].sort_values())

# ¿El texto predice el RUL? Media de RUL por tipo de falla
print("\nRUL medio por tipo de falla:")
print(df.groupby("tipo_falla")["dias_hasta_proxima_falla"].agg(["mean", "std", "count"]))

# RUL por equipo problemático (num_ot_previas_12m alto)
df["problematico_aprox"] = (df["num_ot_previas_12m"] >= 3).astype(int)
print("\nRUL medio por 'problemático aproximado':")
print(df.groupby("problematico_aprox")["dias_hasta_proxima_falla"].agg(["mean", "std", "count"]))

# Diagnóstico del AUC: clases presentes en test
from sklearn.model_selection import train_test_split
from ml.pln import ClasificadorPLN
from sklearn.metrics import roc_auc_score

df_tr, df_te = train_test_split(df, test_size=0.25, random_state=42, stratify=df["tipo_falla"])
pln = ClasificadorPLN("N3").entrenar(df_tr["texto_libre"].tolist(), df_tr["tipo_falla"].tolist())
probas = pln.probabilidades(df_te["texto_libre"].tolist())
y_te = df_te["tipo_falla"].tolist()
print("\nClases en test:", sorted(set(y_te)))
print("Clases del encoder:", list(pln.encoder.classes_))
try:
    auc = roc_auc_score(y_te, probas, labels=config.CATEGORIAS_FALLA, multi_class="ovr", average="macro")
    print("AUC OK:", auc)
except Exception as e:
    print("Error AUC:", repr(e))
