from typing import Optional
from sqlmodel import Field, SQLModel
from datetime import datetime, date

# --- Tabla de Dominio: Estados de OT ---

class EstadoOT(SQLModel, table=True):
    __tablename__ = "estadoot" # Asegúrate que coincida con tu tabla real
    
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_estado: str
    # AGREGA ESTA LÍNEA:
    color: str = Field(default="#95a5a6") 

# --- Tabla Principal: Ordenes de Trabajo ---

class OrdenTrabajo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id")
    
    # FK a tarea preventiva (si la OT se generó desde preventivo)
    orden_preventiva_id: Optional[int] = Field(default=None, foreign_key="tareapreventiva.id") 
    
    estado_id: int = Field(foreign_key="estadoot.id")
    
    prioridad: str 
    tecnico_asignado_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    
    fecha_creacion: datetime = Field(default_factory=datetime.now)
    fecha_vencimiento: Optional[date] = None
    
    titulo: str
    descripcion_falla: str
    
    # Campos de cierre
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    costo_adicional: Optional[float] = None