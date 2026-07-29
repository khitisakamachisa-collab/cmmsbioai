from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import date

# --- MODELO INTERMEDIO: Conecta Tareas con Repuestos ---
class TareaRepuesto(SQLModel, table=True):
    """
    Define qué repuestos y en qué cantidad se necesitan para una tarea preventiva.
    Ejemplo: Para la tarea 'Limpieza Ecógrafo' se necesitan 2 unidades de 'Gel Ecográfico'.
    """
    __tablename__ = "tarea_repuesto"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Conexiones (Foreign Keys)
    tarea_preventiva_id: int = Field(foreign_key="tareapreventiva.id")
    repuesto_id: int = Field(foreign_key="repuesto.id")

    # Cantidad necesaria para ejecutar la tarea
    cantidad_requerida: int = Field(default=1)


# --- MODELO PRINCIPAL: Tarea Preventiva ---
class TareaPreventiva(SQLModel, table=True):
    """
    Define una actividad de mantenimiento programada.

    v0.9.0 - Cambio conceptual importante:
    - `proxima_fecha` es la FECHA REAL programada por el usuario (seteada con date picker).
      NO se calcula automáticamente. Es la fecha que aparece en el calendario.
    - `frecuencia_dias` es solo una SUGERENCIA/RECORDATORIO de cada cuánto hacer el MP.
      Se usa para sugerir la próxima fecha al completar una OT de MP, pero el usuario
      puede modificarla libremente.

    Flujo:
    1. Usuario crea MP: setea `proxima_fecha` con la fecha real que quiere.
       El sistema puede sugerir `hoy + frecuencia_dias` pero el usuario puede cambiarla.
    2. Calendario de Planificación: muestra `proxima_fecha` (la fecha REAL).
    3. Al completar el MP (generar OT y marcarla como completada):
       - `ultima_fecha = fecha de completado`
       - El sistema sugiere `proxima_fecha = ultima_fecha + frecuencia_dias`, pero
         el usuario puede modificarla.
    4. HOME (dashboard): widget "MPs próximos a vencer" basado en `proxima_fecha` vs hoy.
    """
    __tablename__ = "tareapreventiva"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Conexiones principales
    equipo_id: int = Field(foreign_key="equipo.id")
    responsable_id: Optional[int] = Field(default=None, foreign_key="usuario.id")

    # Detalles de la actividad
    titulo: str  # Ej: "Calibración Anual", "Limpieza Mensual"
    descripcion: Optional[str] = None
    frecuencia_dias: int  # Ej: 30 (mensual), 365 (anual) - solo recordatorio/sugerencia

    # Gestión de Fechas
    ultima_fecha: Optional[date] = None  # Última vez que se realizó realmente
    proxima_fecha: Optional[date] = None  # FECHA REAL programada por el usuario (NO auto-calculada)

    activa: bool = Field(default=True)
