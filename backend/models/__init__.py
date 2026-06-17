# Este archivo nos permite importar modelos limpiamente en otros archivos
from .users import Usuario
from .equipos import Equipo
from .estados import EstadoEquipo  # <--- AGREGA ESTA LÍNEA (Importamos desde el nuevo archivo)
from .ordenes import OrdenTrabajo, EstadoOT # <--- Agregar esto
from .repuestos import Repuesto, OtRepuestoUtilizado
# AGREGAR ESTAS LÍNEAS:
from .preventivo import TareaPreventiva, TareaRepuesto
from .historial import EventoHistorial
from .documentos import DocumentoAdjunto
from .herramientas import Herramienta
from .proveedores import Proveedor, ContactoProveedor

# Si tienes __all__, agrégalos allí también
__all__ = [
    "Usuario", "Equipo", "EstadoEquipo", 
    "OrdenTrabajo", "EstadoOT", 
    "Repuesto", "OtRepuestoUtilizado",
    "TareaPreventiva", "TareaRepuesto",
    "EventoHistorial",
    "DocumentoAdjunto",
    "Herramienta",
    "Proveedor", "ContactoProveedor"
]
