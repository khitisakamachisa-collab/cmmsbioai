# Este archivo nos permite importar modelos limpiamente en otros archivos
from .users import Usuario
from .equipos import Equipo
from .estados import EstadoEquipo  # <--- AGREGA ESTA LÍNEA (Importamos desde el nuevo archivo)
from .ordenes import OrdenTrabajo, EstadoOT # <--- Agregar esto
#from .repuestos import Repuesto, OtRepuestoUtilizado # <--- Agregar import
from .repuestos import Repuesto
# AGREGAR ESTAS LÍNEAS:
from .preventivo import TareaPreventiva, TareaRepuesto
from .historial import EventoHistorial

# Si tienes __all__, agrégalos allí también
__all__ = [
    "Usuario", "Equipo", "EstadoEquipo", 
    "OrdenTrabajo", "EstadoOT", 
    "Repuesto", 
    "TareaPreventiva", "TareaRepuesto",
    "EventoHistorial"
]
