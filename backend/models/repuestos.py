from typing import Optional
from sqlmodel import Field, SQLModel

class Repuesto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_repuesto: str
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    cantidad_disponible: int = Field(default=0)
    unidad_medida: str = Field(default="unidad")
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None
    imagen: Optional[str] = None # Ruta a imagen opcional
    
    # --- Nueva Tabla Intermedia ---

class OtRepuestoUtilizado(SQLModel, table=True):
    """
    Tabla que relaciona Órdenes de Trabajo con Repuestos.
    Registra CUÁNTOS repuestos se usaron en una OT específica.
    """
    orden_trabajo_id: int = Field(foreign_key="ordentrabajo.id", primary_key=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", primary_key=True)
    cantidad_utilizada: int