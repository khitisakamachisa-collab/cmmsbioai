from typing import Optional
from datetime import date as date_type
from sqlmodel import Field, SQLModel

class Repuesto(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_repuesto: str
    numero_serie: Optional[str] = None
    numero_material: Optional[str] = None
    descripcion: Optional[str] = None
    especificaciones_tecnicas: Optional[str] = None
    cantidad_disponible: int = Field(default=0)
    unidad_medida: str = Field(default="unidad")
    ubicacion_almacen: Optional[str] = None
    nivel_stock_minimo: Optional[int] = None
    proveedor_ultimo: Optional[str] = None
    proveedor_ultimo_id: Optional[int] = Field(default=None, foreign_key="proveedor.id")  # v0.9.14
    fecha_ultima_entrada: Optional[date_type] = None
    precio_referencia: Optional[float] = None
    imagen_ruta: Optional[str] = None  # Ruta relativa a imagen (ej: INVENTARIO/I0001_xxx/I0001_xxx.jpg)
    
    # --- Nueva Tabla Intermedia ---

class OtRepuestoUtilizado(SQLModel, table=True):
    """
    Tabla que relaciona Órdenes de Trabajo con Repuestos.
    Registra CUÁNTOS repuestos se usaron en una OT específica.
    """
    orden_trabajo_id: int = Field(foreign_key="ordentrabajo.id", primary_key=True)
    repuesto_id: int = Field(foreign_key="repuesto.id", primary_key=True)
    cantidad_utilizada: int