# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Prueba de la limpieza v1.1.2 (bloque C: I6 + coherencia)
=====================================================================
Verifica sobre una BD TEMPORAL (no toca cmms_bioai.db):
  1. GET  /users/            -> NO expone hashed_password (I6)
  2. POST /users/ con schema -> acepta payload del frontend
     {nombre_completo, email, password, rol} y mapea rol -> role (I6)
  3. POST /users/ duplicado  -> 400
  4. La app importa sin los módulos muertos eliminados (A1/A3/A4/A5)

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python prueba_v112_limpieza.py

Salida esperada: verificaciones "[OK]" y al final "OK ✓".
"""

import os
import sys
import tempfile

# --- BD temporal ANTES de importar la app (mismo patrón que prueba_flujo_v111) ---
_TMP = tempfile.mkdtemp(prefix="cmms_v112_")
os.chdir(_TMP)
sys.path.insert(0, _BACKEND := os.path.join(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # por si se corre desde otro cwd

from fastapi.testclient import TestClient  # noqa: E402
import main as app_main  # noqa: E402

# Mismo orden que el lifespan de main.py: migraciones + seed
app_main.create_db_and_tables()
app_main.seed_database()
client = TestClient(app_main.app)

_resultados = []


def check(nombre, condicion):
    _resultados.append(bool(condicion))
    print(f"[{'OK' if condicion else 'FALLO'}] {nombre}")


def main():
    # --- 1. GET /users/ sin hashed_password ---
    r = client.get("/users/")
    check("GET /users/ -> 200", r.status_code == 200)
    usuarios = r.json()
    check("GET /users/ devuelve la lista seed (admin/tech/user)", len(usuarios) >= 3)
    check("I6: NINGÚN usuario expone hashed_password",
          all("hashed_password" not in u for u in usuarios))
    check("Campos útiles presentes (id/username/role/full_name)",
          all(k in usuarios[0] for k in ("id", "username", "role", "full_name")))

    # --- 2. POST /users/ con el payload exacto de UsuariosView.vue ---
    payload = {"nombre_completo": "Tecnico Prueba v112",
               "email": "tecnico112@biolab.com",
               "password": "clave112", "rol": "tecnico"}
    r = client.post("/users/", json=payload)
    check("POST /users/ payload frontend -> 200", r.status_code == 200)
    creado = r.json()
    check("rol del frontend mapeado a role", creado.get("role") == "tecnico")
    check("nombre_completo mapeado a full_name",
          creado.get("full_name") == "Tecnico Prueba v112")
    check("I6: respuesta del POST tampoco expone hashed_password",
          "hashed_password" not in creado)

    # --- 3. Email duplicado -> 400 ---
    r = client.post("/users/", json=payload)
    check("POST /users/ duplicado -> 400", r.status_code == 400)

    # --- 4. Login con el usuario creado (bcrypt intacto) ---
    r = client.post("/token", data={"username": "tecnico112@biolab.com",
                                    "password": "clave112"})
    check("POST /token con usuario creado -> 200 (hash verificado)",
          r.status_code == 200 and "access_token" in r.json())

    print("=" * 60)
    if all(_resultados):
        print(f"RESULTADO: {len(_resultados)}/{len(_resultados)} verificaciones OK")
        print("OK ✓ — limpieza v1.1.2 validada (I6 users sin hash + rol mapeado)")
    else:
        fallidos = len(_resultados) - sum(_resultados)
        print(f"RESULTADO: {sum(_resultados)}/{len(_resultados)} OK — {fallidos} FALLOS")
        sys.exit(1)


if __name__ == "__main__":
    main()
