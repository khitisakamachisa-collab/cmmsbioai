"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/preprocesamiento.py
Preprocesamiento de texto libre en español con 3 NIVELES (estudio de ablación).

N1 — Texto crudo: minúsculas + tokenización básica (conserva todo).
N2 — Limpieza genérica agresiva: minúsculas, sin puntuación, stop words en español
     + stemming Snowball (señal léxica comprimida; puede degradar términos técnicos).
N3 — Limpieza consciente del dominio: normalización con el diccionario de sinónimos
     biomédicos (ocluido/obstrucción/tapado → oclusion), eliminación de stop words
     y de relleno administrativo, SIN stemming (los términos técnicos quedan íntegros
     y son interpretables en SHAP).

100% offline: no requiere descargas de NLTK ni modelos externos.
"""

import json
import re
import unicodedata
from functools import lru_cache

from ml import config

# ------------------------------------------------------------------
# Stop words en español (lista compacta embebida — offline, sin descargas)
# ------------------------------------------------------------------
STOP_WORDS_ES = frozenset("""
a al algo algunas algunos ante antes aquella aquellas aquello aquellos asi aun
aunque bajo bien cada casi como con contra cual cuales cuando cuanto de del desde
donde dos e el ella ellas ello ellos en entre era eran eras es esa esas ese eso
esos esta estaba estamos estan estar estas este esto estos estuve fue fueron fui
ha habia han hasta hay la las le les lo los mas me mi mis mucho muy nada ni no
nos nosotros o os otra otras otro otros para pero poco por porque pese que quien
quienes se sea segun ser si sin sobre solo son su sus tal tambien tanto te tuvo
tiene tienen toda todas todo todos tras tu tus un una unas uno unos usted ustedes
ver y ya yo
""".split())

# Palabras de relleno administrativo típicas de las OTs (ruido sin valor diagnóstico)
FILLER_DOMINIO = frozenset("""
reportado reporta reportan indicado indica segun tecnico tecnica servicio turno
enfermeria enfermeriaa usuario usaria trajo momento noche manana tarde quedo
queda realizo realiza realizado realizados operativa operativo funcional reviso
revisar chequeo cumpio cumplio
""".split())

# ------------------------------------------------------------------
# Utilidades de normalización
# ------------------------------------------------------------------
_TOKEN_RE = re.compile(r"[a-z0-9áéíóúñü]+")


def _quitar_acentos(texto: str) -> str:
    """Elimina diacríticos (oclusión → oclusion) — permite mapeo tolerante a acentos."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def _tokenizar(texto: str) -> list:
    return _TOKEN_RE.findall(texto.lower())


# ------------------------------------------------------------------
# Diccionario de sinónimos → mapa de normalización (N3)
# ------------------------------------------------------------------
@lru_cache(maxsize=1)
def _mapa_sinonimos() -> tuple:
    """
    Devuelve (mapa_tokens, mapa_frases) donde:
      - mapa_tokens: {variante_sin_acentos: termino_canonico} (una palabra)
      - mapa_frases: [(regex_frase_normalizada, termino_canonico)] (2+ palabras)
    """
    with open(config.SINONIMOS_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)
    mapa_tokens: dict = {}
    mapa_frases: list = []
    for canonico, variantes in raw.items():
        if canonico.startswith("_"):
            continue
        canonico_norm = _quitar_acentos(canonico.lower())
        mapa_tokens[canonico_norm] = canonico_norm
        for v in variantes:
            v_norm = _quitar_acentos(v.lower().strip())
            if not v_norm:
                continue
            if " " in v_norm:
                # Frase: patrón con espacios flexibles y bordes de palabra
                patron = r"\b" + r"\s+".join(re.escape(p) for p in v_norm.split()) + r"\b"
                mapa_frases.append((patron, canonico_norm))
            else:
                mapa_tokens[v_norm] = canonico_norm
    # Frases más largas primero (evita reemplazos parciales)
    mapa_frases.sort(key=lambda x: -len(x[0]))
    return mapa_tokens, mapa_frases


# ------------------------------------------------------------------
# NIVELES DE PREPROCESAMIENTO (ablación)
# ------------------------------------------------------------------
def nivel1(texto: str) -> str:
    """N1 — Texto crudo: minúsculas y tokenización básica (sin más limpieza)."""
    return " ".join(_tokenizar(texto))


def nivel2(texto: str) -> str:
    """N2 — Limpieza genérica agresiva: stop words + stemming Snowball español."""
    try:
        from nltk.stem.snowball import SnowballStemmer
        stemmer = SnowballStemmer("spanish")
        _stem = stemmer.stem
    except Exception:  # NLTK no disponible → truncamiento simple (fallback offline)
        def _stem(p: str) -> str:
            return p[:-2] if len(p) > 4 else p

    tokens = [t for t in _tokenizar(texto) if t not in STOP_WORDS_ES]
    return " ".join(_stem(t) for t in tokens)


def nivel3(texto: str) -> str:
    """
    N3 — Limpieza consciente del dominio:
      1) quita acentos y minúsculas (tolerancia a errores de digitación),
      2) normaliza sinónimos/frases del diccionario biomédico → término canónico,
      3) elimina stop words y relleno administrativo,
      4) SIN stemming: los términos técnicos quedan íntegros (interpretables en SHAP).
    """
    mapa_tokens, mapa_frases = _mapa_sinonimos()
    texto_norm = _quitar_acentos(texto.lower())
    for patron, canonico in mapa_frases:
        texto_norm = re.sub(patron, f" {canonico} ", texto_norm)
    tokens = _tokenizar(texto_norm)
    limpios = []
    for t in tokens:
        if t in STOP_WORDS_ES or t in FILLER_DOMINIO:
            continue
        limpios.append(mapa_tokens.get(t, t))
    return " ".join(limpios)


PREPROCESADORES = {"N1": nivel1, "N2": nivel2, "N3": nivel3}


def preprocesar(texto: str, nivel: str = "N3") -> str:
    """Punto de entrada único: preprocesar('texto', 'N1'|'N2'|'N3')."""
    func = PREPROCESADORES.get(nivel)
    if func is None:
        raise ValueError(f"Nivel de preprocesamiento inválido: {nivel}")
    return func(texto or "")


# ------------------------------------------------------------------
# Detección de señales de dominio (usada por el generador de features RUL)
# ------------------------------------------------------------------
def contiene_sena(texto: str, claves: list) -> bool:
    """True si el texto (normalizado N3) contiene alguna clave canónica."""
    t = " " + nivel3(texto) + " "
    return any(_quitar_acentos(c.lower()) in t for c in claves)
