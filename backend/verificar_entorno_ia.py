# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Verificador de entorno (RF07 / Módulo IA)
=====================================================
Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python verificar_entorno_ia.py

Comprueba, uno por uno, los paquetes que necesita el módulo
predictivo (RF07) e informa qué falta o qué versión tiene.
No instala nada, solo diagnostica.
"""

import importlib
import sys

# (nombre del import, nombre pip, versión mínima razonable)
PAQUETES = [
    ("fastapi",       "fastapi",      "0.100"),
    ("uvicorn",       "uvicorn",      "0.30"),
    ("sqlmodel",      "sqlmodel",     "0.0.47"),   # NaiveDatetime requiere >=0.0.24; 0.0.47 recomendado
    ("pydantic",      "pydantic",     "2.11"),
    ("multipart",     "python-multipart", "0.0.9"),
    ("jose",          "python-jose[cryptography]", "3.3"),
    ("passlib",       "passlib[bcrypt]", "1.7"),
    ("openpyxl",      "openpyxl",     "3.1"),
    ("numpy",         "numpy",        "1.26"),
    ("pandas",        "pandas",       "2.0"),
    ("scipy",         "scipy",        "1.11"),
    ("sklearn",       "scikit-learn", "1.3"),
    ("xgboost",       "xgboost",      "2.0"),
    ("shap",          "shap",         "0.44"),
    ("joblib",        "joblib",       "1.3"),
    ("nltk",          "nltk",         "3.8"),
    ("httpx2",        "httpx2",       "0.1"),      # solo pruebas (TestClient)
]


def version_de(nombre_import: str) -> str:
    try:
        mod = importlib.import_module(nombre_import)
        return getattr(mod, "__version__", "?")
    except Exception:
        return "-"


def main() -> int:
    print("=" * 62)
    print(" CMMS-BioAI - Verificador de entorno del modulo IA (RF07)")
    print("=" * 62)
    print(f" Python: {sys.version.split()[0]}  ({sys.executable})")
    print("-" * 62)

    faltan = []
    ok = 0
    for import_name, pip_name, min_ver in PAQUETES:
        try:
            importlib.import_module(import_name)
            estado = "OK"
            ok += 1
        except Exception as e:
            estado = "FALTA"
            faltan.append(pip_name)
        ver = version_de(import_name)
        print(f" [{estado:>5}] {pip_name:<30} {ver:>10}   (min {min_ver})")

    print("-" * 62)

    # Prueba de carga de modelos entrenados
    try:
        import joblib
        from pathlib import Path
        modelos = sorted(Path("ml/models").glob("*.joblib"))
        if modelos:
            print(f" Modelos entrenados en ml/models/: {len(modelos)} archivo(s)")
            for m in modelos:
                print(f"   - {m.name} ({m.stat().st_size / 1024:.0f} KB)")
        else:
            print(" Aviso: ml/models/ no tiene modelos entrenados.")
            print("        (Se regeneran al entrenar desde el Panel Predictivo)")
    except Exception as e:
        print(f" Aviso: no se pudo inspeccionar ml/models/ ({e})")

    print("-" * 62)
    if faltan:
        print(f" RESULTADO: faltan {len(faltan)} paquete(s). Instalar con:")
        print()
        print("   python -m pip install --only-binary=:all: " + " ".join(faltan))
        print()
        print(" o de una sola vez con:")
        print("   python -m pip install --only-binary=:all: -r requirements.txt")
        return 1
    else:
        print(f" RESULTADO: TODO OK ({ok}/{len(PAQUETES)} paquetes presentes).")
        print(" Puedes levantar el backend y entrenar desde el Panel Predictivo.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
