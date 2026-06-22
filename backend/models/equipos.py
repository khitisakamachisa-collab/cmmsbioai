from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import date

# --- Tablas de Dominio (Catálogos) ---
# ELIMINAMOS LA CLASE EstadoEquipo DE AQUÍ. Ahora está en models/estados.py

# --- Modelo Principal ---

class Equipo(SQLModel, table=True):
    """
    Tabla Equipos - RF01 v0.9.0 (Universal, sin contexto Bolivia).

    Cambios vs v0.8.3:
    - ELIMINADOS: registro_sanitario_bolivia, calibracion_proxima, responsable_tecnico_id, proveedor_principal (texto)
    - AÑADIDOS: observaciones, fecha_inicio_garantia, condicion_origen, proveedor_principal_id (FK)
    - CAMBIO OBLIGATORIEDAD: nombre_corto ahora es NOT NULL, fecha_adquisicion ahora es opcional
    - RESTRICCIONES: modelo, marca, numero_serie NO modificables después de creado (validación en backend + frontend)
    """
    id: Optional[int] = Field(default=None, primary_key=True)

    # === Identificación ===
    nombre_corto: str                                          # NOT NULL (era opcional)
    modelo: str                                                # NOT NULL (no editable después de creado)
    numero_serie: str = Field(unique=True, index=True)         # NOT NULL, unique (no editable después)
    numero_material: Optional[str] = None
    marca: str                                                 # NOT NULL (no editable después de creado)

    # === Fechas ===
    fecha_adquisicion: Optional[date] = None                   # Opcional (era obligatorio)
    fecha_inicio_garantia: Optional[date] = None               # NUEVO
    fecha_fin_garantia: Optional[date] = None                  # Mantenido

    # === Ubicación y estado ===
    ubicacion_actual: Optional[str] = None
    estado_id: Optional[int] = Field(default=None, foreign_key="estadoequipo.id")

    # === Proveedor (FK en vez de texto libre) ===
    proveedor_principal_id: Optional[int] = Field(
        default=None, foreign_key="proveedor.id"
    )                                                          # NUEVO (reemplaza proveedor_principal texto)

    # === Origen ===
    condicion_origen: Optional[str] = None                     # NUEVO (enum: Compra/Donación/Préstamo/...)

    # === Descripción ===
    descripcion: Optional[str] = None                          # Técnica (¿qué es?)
    observaciones: Optional[str] = None                        # NUEVO: Operativas (¿cómo está?)

    # === Imagen ===
    imagen_ruta: Optional[str] = None

    # NOTA: Los campos eliminados (registro_sanitario_bolivia, calibracion_proxima,
    #       responsable_tecnico_id, proveedor_principal) NO se incluyen en el modelo.
    #       Si la tabla SQLite los tiene (de una versión anterior), SQLModel los ignora.
    #       Para una BD nueva (v0.9.0), estos campos simplemente no existen.
