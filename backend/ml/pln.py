"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/pln.py
Pipeline de PLN: TF-IDF (vocabulario acotado) + clasificador Naive Bayes/SVM lineal.

Salida: tipo de falla clasificado entre 6 categorías de la tesis
(eléctrica, mecánica, software, sensor, calibración, otra).

Para el modelo RUL se necesitan probabilidades por categoría, por lo que el SVM
lineal se calibra con CalibratedClassifierCV (sigmoide) manteniendo el núcleo
"TF-IDF + SVM lineal" exigido por la tesis. 100% offline, sin GPU.
"""

import numpy as np
from functools import partial
from sklearn.calibration import CalibratedClassifierCV
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.preprocessing import LabelEncoder
from sklearn.svm import LinearSVC

from ml import config
from ml.preprocesamiento import nivel1, nivel2, nivel3

# Funciones con nombre (picklables — el lambda no lo es)
_PREPROCESADORES = {"N1": nivel1, "N2": nivel2, "N3": nivel3}


# ------------------------------------------------------------------
# Vectorización TF-IDF (vocabulario acotado 1000-2000 términos)
# ------------------------------------------------------------------
def construir_vectorizador(nivel: str = "N3") -> TfidfVectorizer:
    """TF-IDF con preprocesador integrado según el nivel de ablación (picklable)."""
    func = _PREPROCESADORES[nivel]
    return TfidfVectorizer(
        max_features=config.TFIDF_MAX_FEATURES,
        preprocessor=partial(func),
        ngram_range=(1, 1),
        sublinear_tf=True,
    )


# ------------------------------------------------------------------
# Clasificador PLN
# ------------------------------------------------------------------
def _construir_clasificador_base():
    if config.CLASIFICADOR_PLN == "NB":
        return MultinomialNB(alpha=config.NB_ALPHA)
    # SVM lineal calibrado (necesita predict_proba para las features del RUL)
    svc = LinearSVC(C=config.SVM_C, random_state=config.RANDOM_SEED)
    return CalibratedClassifierCV(svc, method="sigmoid", cv=3)


class ClasificadorPLN:
    """Envoltorio del pipeline TF-IDF + clasificador con codificación de etiquetas."""

    def __init__(self, nivel: str = "N3"):
        self.nivel = nivel
        self.vectorizador = construir_vectorizador(nivel)
        self.clf = _construir_clasificador_base()
        self.encoder = LabelEncoder()

    def entrenar(self, textos: list, etiquetas: list):
        y = self.encoder.fit_transform(etiquetas)
        X = self.vectorizador.fit_transform(textos)
        self.clf.fit(X, y)
        return self

    def predecir(self, textos: list) -> list:
        X = self.vectorizador.transform(textos)
        return self.encoder.inverse_transform(self.clf.predict(X))

    def probabilidades(self, textos: list) -> np.ndarray:
        """Matriz (n_muestras, n_clases) con columnas en orden de CATEGORIAS_FALLA."""
        X = self.vectorizador.transform(textos)
        if hasattr(self.clf, "predict_proba"):
            probas = self.clf.predict_proba(X)
        else:  # respaldo: softmax sobre decision_function
            dec = self.clf.decision_function(X)
            probas = np.exp(dec) / np.exp(dec).sum(axis=1, keepdims=True)
        # Reordenar columnas al orden canónico de CATEGORIAS_FALLA
        clases = list(self.encoder.classes_)
        idx = [clases.index(c) for c in config.CATEGORIAS_FALLA if c in clases]
        probas = probas[:, idx]
        # Asegurar 6 columnas (si una categoría no aparece en el entrenamiento)
        while probas.shape[1] < len(config.CATEGORIAS_FALLA):
            probas = np.hstack([probas, np.zeros((probas.shape[0], 1))])
        return probas

    def guardar(self):
        """Persiste vectorizador + clasificador + encoder en joblib."""
        import joblib
        joblib.dump(self.vectorizador, config.MODELS_DIR / f"tfidf_{self.nivel.lower()}.joblib")
        joblib.dump(self.clf, config.MODELO_CLASIFICADOR)
        joblib.dump(self.encoder, config.LABEL_ENCODER)


# ------------------------------------------------------------------
# Métricas de clasificación (F1, AUC-ROC)
# ------------------------------------------------------------------
def metricas_clasificacion(y_true, y_pred, y_proba=None) -> dict:
    """F1-Score macro, precisión, sensibilidad y AUC-ROC OvR macro (tesis H1)."""
    labels = [c for c in config.CATEGORIAS_FALLA]
    resultado = {
        "f1_macro": round(float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
        "precision_macro": round(float(precision_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)), 4),
    }
    if y_proba is not None:
        try:
            resultado["auc_roc_ovr"] = round(
                float(roc_auc_score(y_true, y_proba, labels=labels, multi_class="ovr", average="macro")), 4
            )
        except Exception:
            resultado["auc_roc_ovr"] = None
    return resultado


def matriz_confusion(y_true, y_pred) -> list:
    """Matriz de confusión como lista de listas (para exportación científica)."""
    labels = config.CATEGORIAS_FALLA
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    return cm.tolist()


# ------------------------------------------------------------------
# Entrenamiento/evaluación con partición train-test (uso general)
# ------------------------------------------------------------------
def entrenar_y_evaluar(df, nivel: str = "N3", test_size: float = 0.25) -> dict:
    """
    Entrena el clasificador PLN con el nivel dado y devuelve métricas en test.
    df requiere columnas: texto_libre, tipo_falla.
    """
    X_tr, X_te, y_tr, y_te = train_test_split(
        df["texto_libre"].tolist(),
        df["tipo_falla"].tolist(),
        test_size=test_size,
        random_state=config.RANDOM_SEED,
        stratify=df["tipo_falla"],
    )
    pln = ClasificadorPLN(nivel).entrenar(X_tr, y_tr)
    y_pred = pln.predecir(X_te)
    probas = pln.probabilidades(X_te)
    m = metricas_clasificacion(y_te, y_pred, probas)

    # Ejemplo de inferencia puntual (para el registro de la tesis)
    m["n_train"], m["n_test"] = len(X_tr), len(X_te)
    m["nivel"] = nivel
    return m
