from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from datetime import date, datetime

# --- Tablas de Dominio (Catálogos) ---
# ELIMINAMOS LA CLASE EstadoEquipo DE AQUÍ. Ahora está en models/estados.py

# --- Modelo Principal ---

class Equipo(SQLModel, table=True):
    """
    Tabla Equipos.
    Registro principal de activos médicos.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_corto: Optional[str] = None
    modelo: str
    numero_serie: str = Field(unique=True, index=True)
    numero_material: Optional[str] = None  # Número de material (variante del modelo)
    marca: str
    fecha_adquisicion: date
    fecha_fin_garantia: Optional[date] = None  # Fecha fin de garantía
    registro_sanitario_bolivia: Optional[str] = None
    ubicacion_actual: Optional[str] = None
    proveedor_principal: Optional[str] = None
    descripcion: Optional[str] = None
    imagen_ruta: Optional[str] = None
    calibracion_proxima: Optional[date] = None

    # Claves Foráneas
    responsable_tecnico_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    estado_id: Optional[int] = Field(default=None, foreign_key="estadoequipo.id")