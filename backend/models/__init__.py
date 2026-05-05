# Este archivo nos permite importar modelos limpiamente en otros archivos
from .users import Usuario
from .equipos import Equipo
from .estados import EstadoEquipo  # <--- AGREGA ESTA LÍNEA (Importamos desde el nuevo archivo)
from .ordenes import OrdenTrabajo, EstadoOT # <--- Agregar esto
#from .repuestos import Repuesto, OtRepuestoUtilizado # <--- Agregar import

# También asegúrate de exportarlo en la lista si existe __all__
__all__ = ["Usuario", "Equipo", "EstadoEquipo", "OrdenTrabajo", "EstadoOT"]