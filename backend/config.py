"""
Configuración centralizada del backend CMMS-BioAI.

Lee la configuración desde config.json (en el mismo directorio que este archivo).
Si config.json no existe, lo crea con valores por defecto.

Todos los módulos deben importar las rutas y configuraciones desde aquí:
    from config import UPLOADS_DIR, get_dir

NUNCA calcular rutas con __file__ desde otros módulos.
NUNCA usar rutas relativas tipo Path("uploads").

ARQUITECTURA DE DIRECTORIOS:
    - uploads_base: puede ser relativa a backend/ o absoluta (ej: D:/uploads)
    - Las sub-carpetas (EQUIPOS, REPUESTOS, etc.) son RELATIVAS a uploads_base
    - Al cambiar uploads_base, TODAS las sub-carpetas siguen automáticamente
"""
import json
from pathlib import Path

# ─── Directorio base: donde está este archivo (backend/) ───
BACKEND_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BACKEND_DIR / "config.json"

# ─── Valores por defecto (si no existe config.json) ───
_DEFAULTS = {
    "empresa": {
        "nombre": "CMMS-BioAI"
    },
    "directorios": {
        "uploads_base": "uploads",
        "equipos_imagenes": "EQUIPOS",
        "equipos_documentos": "EQUIPOS",
        "ot_documentos": "OT",
        "repuestos_imagenes": "REPUESTOS",
        "repuestos_documentos": "REPUESTOS",
        "herramientas_imagenes": "HERRAMIENTAS",
        "herramientas_documentos": "HERRAMIENTAS",
        "reportes": "REPORTES"
    },
    "sistema": {
        "idioma": "es",
        "zona_horaria": "America/La_Paz",
        "moneda": "BOB",
        "prefijo_equipos": "E",
        "prefijo_ordenes": "OT",
        "prefijo_inventario": "R"
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
    global _config, UPLOADS_DIR
    _config = new_config
    _save_config(_config)
    UPLOADS_DIR = get_dir("uploads_base")


def _resolve_uploads_base() -> Path:
    """
    Resuelve la ruta absoluta de uploads_base.
    - Si es absoluta (ej: D:/uploads, /mnt/datos/uploads), la usa directamente
    - Si es relativa (ej: "uploads"), la resuelve relativa a BACKEND_DIR
    """
    dirs = _config.get("directorios", _DEFAULTS["directorios"])
    uploads_base_str = dirs.get("uploads_base", "uploads")
    base_path = Path(uploads_base_str)
    if base_path.is_absolute():
        return base_path.resolve()
    else:
        return (BACKEND_DIR / base_path).resolve()


def get_dir(key: str) -> Path:
    """
    Devuelve la ruta absoluta de un directorio configurado.

    ARQUITECTURA:
        - "uploads_base" → ruta absoluta (relativa a backend/ o absoluta)
        - Cualquier otra key → relativa a uploads_base

    Keys disponibles:
        - "uploads_base"            → <base>/uploads/  (o D:/uploads/ si es absoluta)
        - "equipos_imagenes"        → <uploads_base>/EQUIPOS/
        - "equipos_documentos"      → <uploads_base>/EQUIPOS/
        - "ot_documentos"           → <uploads_base>/OT/
        - "repuestos_imagenes"      → <uploads_base>/REPUESTOS/
        - "repuestos_documentos"    → <uploads_base>/REPUESTOS/
        - "herramientas_imagenes"   → <uploads_base>/HERRAMIENTAS/
        - "herramientas_documentos" → <uploads_base>/HERRAMIENTAS/
        - "reportes"                → <uploads_base>/REPORTES/

    Ejemplo con uploads_base = "uploads" (relativa):
        get_dir("equipos_imagenes") → /ruta/backend/uploads/EQUIPOS

    Ejemplo con uploads_base = "D:/uploads" (absoluta):
        get_dir("equipos_imagenes") → D:/uploads/EQUIPOS

    Al cambiar uploads_base, TODAS las sub-carpetas se reubican automáticamente.
    """
    dirs = _config.get("directorios", _DEFAULTS["directorios"])
    relative_path = dirs.get(key)
    if relative_path is None:
        raise KeyError(f"Directorio '{key}' no encontrado en config.json")

    if key == "uploads_base":
        abs_path = _resolve_uploads_base()
    else:
        # Las sub-carpetas son relativas a uploads_base
        uploads_base = _resolve_uploads_base()
        abs_path = uploads_base / relative_path

    abs_path.mkdir(parents=True, exist_ok=True)
    return abs_path


# ─── Variables de conveniencia (las más usadas) ───
UPLOADS_DIR = get_dir("uploads_base")


def sanitize_filename(text: str, default: str = "SN") -> str:
    """
    Sanitiza texto para usar en nombres de carpeta/archivo.

    Solo permite caracteres ASCII alfanumericos, guiones y guiones bajos.
    Los caracteres no ASCII (acentos, eñes, etc.) se reemplazan por '_'.
    Esto evita problemas de codificacion en diferentes sistemas operativos.

    Ejemplo:
        sanitize_filename("Inspección") -> "Inspecci_n"
        sanitize_filename("MIC-OLY-001") -> "MIC-OLY-001"
        sanitize_filename("") -> "SN"
    """
    if not text:
        return default
    result = "".join(c if c.isascii() and (c.isalnum() or c in "-_") else "_" for c in text)
    # Eliminar múltiples guiones bajos consecutivos
    while "__" in result:
        result = result.replace("__", "_")
    # Eliminar guiones bajos al inicio/final
    result = result.strip("_")
    return result if result else default

# ─── Info de debug (se muestra al iniciar el servidor) ───
print(f"[config.py] BACKEND_DIR = {BACKEND_DIR}")
print(f"[config.py] UPLOADS_DIR  = {UPLOADS_DIR}")
print(f"[config.py] config.json  = {CONFIG_FILE}")
