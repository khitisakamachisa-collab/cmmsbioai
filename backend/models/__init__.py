# Este archivo nos permite importar modelos limpiamente en otros archivos
from .users import Usuario
from .equipos import Equipo
from .estados import EstadoEquipo
from .ordenes import OrdenTrabajo, EstadoOT
from .repuestos import Repuesto, OtRepuestoUtilizado
from .preventivo import TareaPreventiva, TareaRepuesto
from .historial import EventoHistorial
from .documentos import DocumentoAdjunto
from .herramientas import Herramienta
from .proveedores import Proveedor, ContactoProveedor
from .costos import OtCostoAdicional  # v0.9.1: RF11

__all__ = [
    "Usuario", "Equipo", "EstadoEquipo",
    "OrdenTrabajo", "EstadoOT",
    "Repuesto", "OtRepuestoUtilizado",
    "TareaPreventiva", "TareaRepuesto",
    "EventoHistorial",
    "DocumentoAdjunto",
    "Herramienta",
    "Proveedor", "ContactoProveedor",
    "OtCostoAdicional",  # v0.9.1: RF11
]
