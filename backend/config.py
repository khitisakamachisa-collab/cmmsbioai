"""
Configuración centralizada del backend CMMS-BioAI.

Lee la configuración desde config.json (en el mismo directorio que este archivo).
Si config.json no existe, lo crea con valores por defecto.

Todos los módulos deben importar las rutas y configuraciones desde aquí:
    from config import UPLOADS_DIR, get_dir

NUNCA calcular rutas con __file__ desde otros módulos.
NUNCA usar rutas relativas tipo Path("uploads").
"""
import json
from pathlib import Path

# ─── Directorio base: donde está este archivo (backend/) ───
BACKEND_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BACKEND_DIR / "config.json"

# ─── Valores por defecto (si no existe config.json) ───
_DEFAULTS = {
    "empresa": {
        "nombre": "CMMS-BioAI",
        "logo_ruta": ""
    },
    "directorios": {
        "uploads_base": "uploads",
        "equipos_imagenes": "uploads/EQUIPOS",
        "equipos_documentos": "uploads/EQUIPOS",
        "ot_documentos": "uploads/OT",
        "inventario_imagenes": "uploads/INVENTARIO",
        "inventario_documentos": "uploads/INVENTARIO",
        "reportes": "uploads/REPORTES"
    },
    "sistema": {
        "idioma": "es",
        "zona_horaria": "America/La_Paz",
        "moneda": "BOB",
        "prefijo_equipos": "E",
        "prefijo_ordenes": "OT",
        "prefijo_inventario": "I"
    }
}


def _load_config() -> dict:
    """Carga config.json. Si no existe, lo crea con defaults y lo devuelve."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"[config.py] ERROR leyendo config.json: {e}")
            print(f"[config.py] Usando valores por defecto")
            return _DEFAULTS
    else:
        # Crear config.json con defaults
        _save_config(_DEFAULTS)
        print(f"[config.py] Creado config.json con valores por defecto")
        return _DEFAULTS


def _save_config(cfg: dict):
    """Guarda la configuración en config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


# ─── Cargar configuración al importar ───
_config = _load_config()


def get_config() -> dict:
    """Devuelve la configuración completa (diccionario)."""
    return _config


def update_config(new_config: dict):
    """Actualiza la configuración completa y la guarda en config.json."""
    global _config
    _config = new_config
    _save_config(_config)


def get_dir(key: str) -> Path:
    """
    Devuelve la ruta absoluta de un directorio configurado.

    Keys disponibles:
        - "uploads_base"          -> backend/uploads/
        - "equipos_imagenes"      -> backend/uploads/EQUIPOS/
        - "equipos_documentos"    -> backend/uploads/EQUIPOS/
        - "ot_documentos"         -> backend/uploads/OT/
        - "inventario_imagenes"   -> backend/uploads/INVENTARIO/
        - "inventario_documentos" -> backend/uploads/INVENTARIO/
        - "reportes"              -> backend/uploads/REPORTES/

    Ejemplo:
        from config import get_dir
        dir_equipos = get_dir("equipos_imagenes")
        # Resultado: <BACKEND_DIR>/uploads/EQUIPOS (ruta absoluta)
    """
    dirs = _config.get("directorios", _DEFAULTS["directorios"])
    relative_path = dirs.get(key)
    if relative_path is None:
        raise KeyError(f"Directorio '{key}' no encontrado en config.json")
    abs_path = BACKEND_DIR / relative_path
    abs_path.mkdir(parents=True, exist_ok=True)
    return abs_path


# ─── Variables de conveniencia (las más usadas) ───
UPLOADS_DIR = get_dir("uploads_base")

# ─── Info de debug (se muestra al iniciar el servidor) ───
print(f"[config.py] BACKEND_DIR = {BACKEND_DIR}")
print(f"[config.py] UPLOADS_DIR  = {UPLOADS_DIR}")
print(f"[config.py] config.json  = {CONFIG_FILE}")
