from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import NaiveDatetime
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
    
    # NaiveDatetime: almacenamiento naive en SQLite (compat sqlmodel>=0.0.22)
    fecha_creacion: NaiveDatetime = Field(default_factory=datetime.now)
    fecha_vencimiento: Optional[date] = None
    
    titulo: str
    descripcion_falla: str
    
    # Campos de cierre
    acciones_realizadas: Optional[str] = None
    tiempo_real_invertido: Optional[float] = None
    unidad_tiempo: Optional[str] = Field(default="horas")  # "horas" o "dias"
    costo_adicional: Optional[float] = None  # Costo general de la OT
    costos_adicionales: Optional[float] = None  # Costos adicionales (externos, transporte, etc.)

    # ==========================================================
    # v1.1.0 — Flujo de Trabajo OT (Propuesta aprobada 03/10/2026)
    # Regla R5: sellos de tiempo, primera escritura inmutable.
    #   fecha_asignacion     → se fija al ASIGNAR técnico (1ra vez)
    #   fecha_inicio_trabajo → se fija al INICIAR trabajo (1ra vez)
    #   fecha_resolucion     → se fija al RESOLVER/completar (1ra vez)
    # Ningún endpoint los sobreescribe una vez establecidos.
    # ==========================================================
    fecha_asignacion: Optional[NaiveDatetime] = None
    fecha_inicio_trabajo: Optional[NaiveDatetime] = None
    fecha_resolucion: Optional[NaiveDatetime] = None

    # ==========================================================
    # v1.1.1 — Cierre definitivo y reincidencias
    # (prompt "Gestión de OTs con Cierre Definitivo y Reapertura")
    #
    # Una OT cerrada (Completada/Cancelada) es INMUTABLE: ya no se
    # reabre. Si la misma falla vuelve a intervenirse, se crea una
    # OT NUEVA vinculada:
    #   parent_ot_id     → OT que originó la reincidencia
    #   failure_sequence → nº de veces que la misma falla en el mismo
    #                      equipo ha generado OTs (1 = primera).
    #                      Sirve para detectar fallas crónicas y para
    #                      no distorsionar MTBF/MTTR/Disponibilidad
    #                      (cada OT individual mantiene su propio
    #                      inicio/cierre).
    # ==========================================================
    parent_ot_id: Optional[int] = Field(default=None, foreign_key="ordentrabajo.id")
    failure_sequence: int = Field(default=1)

    # ==========================================================
    # v2.1 — Dataset de Prueba / Rediseño de flujos (15 campos)
    # Defaults seguros: filas existentes quedan como 'Usuario/REAL'
    # sin pausas ni exclusiones (compatibilidad total).
    # ==========================================================
    tipo_origen_ot: str = Field(default="Usuario")        # Usuario | Sistema/IA | Programado
    tipo_impacto: str = Field(default="REAL")             # REAL | PRECAUTORIO | PROGRAMADO
    sub_estado_logistica: Optional[str] = None            # Esperando_Cotización | En_Proceso_Compra | En_Aduana | En_Transito
    ventana_garantia_reparacion: bool = Field(default=False)   # True si falla en <72h de OT anterior
    es_reparacion_inefectiva: bool = Field(default=False)      # True si falla infantil / repuesto defectuoso
    en_pausa_tecnica: bool = Field(default=False)              # True si pausada por emergencia
    motivo_pausa: Optional[str] = None                         # Emergencia_Clinica | Reasignacion_Coordinador | ...
    tiempo_pausa_acumulado: float = Field(default=0.0)         # Horas totales en pausa
    cierre_administrativo: bool = Field(default=False)         # True si fue forzado por Coordinador
    excluida_de_MTTR: bool = Field(default=False)              # True si no cuenta para eficiencia técnica
    mdt_excluido_disponibilidad: bool = Field(default=False)   # True si MDT no se suma a Disponibilidad
    codigo_falla: Optional[str] = None                         # Código estructurado de falla (F-101, ...)
    causa_raiz: Optional[str] = None                           # Código estructurado de causa
    accion_tomada: Optional[str] = None                        # Código estructurado de acción
    motivo_cancelacion: Optional[str] = None                   # Falsa_Alarma | Duplicado | Error_Usuario | Baja_Equipo | No_Reparable | Riesgo_Aceptado


# ==============================================================
# v1.1.0 — Bitácora de transiciones (Regla R4)
# Cada acción del flujo OT (asignar, iniciar, pausar, reanudar,
# resolver, cancelar, reabrir, editar) queda registrada aquí con
# usuario, comentario y estados anterior/nuevo. Es la evidencia
# de trazabilidad para auditoría y para el cálculo del tiempo
# en "Esp. Repuesto" del reporte /reportes/tiempos-etapa.
# ==============================================================

class BitacoraOT(SQLModel, table=True):
    __tablename__ = "bitacora_ot"

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_trabajo_id: int = Field(foreign_key="ordentrabajo.id", index=True)

    fecha: NaiveDatetime = Field(default_factory=datetime.now)

    # Acción del flujo: creada / asignada / iniciada / pausada /
    # reanudada / resuelta / cancelada / reabierta / editada
    accion: str

    # Usuario que ejecutó (username) o "sistema"
    usuario: Optional[str] = None

    estado_anterior: Optional[str] = None
    estado_nuevo: Optional[str] = None
    comentario: Optional[str] = None