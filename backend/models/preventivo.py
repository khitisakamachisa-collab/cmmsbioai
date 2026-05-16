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
    """
    __tablename__ = "tareapreventiva"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Conexiones principales
    equipo_id: int = Field(foreign_key="equipo.id")
    responsable_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    
    # Detalles de la actividad
    titulo: str # Ej: "Calibración Anual", "Limpieza Mensual"
    descripcion: Optional[str] = None
    frecuencia_dias: int # Ej: 30 (mensual), 365 (anual)
    
    # Gestión de Fechas
    ultima_fecha: Optional[date] = None # Última vez que se realizó
    proxima_fecha: Optional[date] = None # Próxima fecha programada
    
    activa: bool = Field(default=True)