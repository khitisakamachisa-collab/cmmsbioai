# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Modelos v2.1 (Rediseño de flujos / Dataset de Prueba)
===================================================================
Tres tablas nuevas autorizadas por la tarea "Importar Dataset de Prueba v2.1":

  - symptoms            → Síntomas anexados a una OT (usuario o Sistema/IA)
  - feedback_predictivo → Cierre del ciclo predictivo: predicción IA vs resultado real
  - hitos_ciclo_vida    → Eventos de fin de vida del equipo (EOS, RECALL, ...)

NO se modifica ningún router ni endpoint existente (restricción de la tarea).
Estas tablas se crean automáticamente con SQLModel.metadata.create_all()
siempre que este módulo esté importado (ver models/__init__.py).
"""

from typing import Optional
from sqlmodel import Field, SQLModel
from pydantic import NaiveDatetime
from datetime import datetime, date


class SintomaOT(SQLModel, table=True):
    """Tabla 'symptoms' — Síntomas anexados a una OT.

    Un síntoma puede originarse en el Usuario (reporte verbal/escrito) o en
    el Sistema/IA (predicción RUL que abre o anexa evidencia a la OT).
    prediccion_rul guarda JSON como string, p.ej.:
      '{"dias_estimados": 7, "confianza": 0.85}'
    """
    __tablename__ = "symptoms"

    id: Optional[int] = Field(default=None, primary_key=True)
    ot_id: int = Field(foreign_key="ordentrabajo.id", index=True)
    tipo_origen: str                                  # 'Usuario' | 'Sistema/IA'
    texto_sintoma: str                                # Descripción del síntoma
    prediccion_rul: Optional[str] = None              # JSON como string (solo origen IA)
    # NaiveDatetime: almacenamiento naive en SQLite (convención del proyecto, v1.1.0)
    fecha_reporte: NaiveDatetime = Field(default_factory=datetime.now)
    usuario_id: Optional[int] = Field(default=None, foreign_key="usuario.id")
    estado_validacion: str = Field(default="Pendiente")  # 'Pendiente' | 'Confirmado' | 'Falsa_Alarma'


class FeedbackPredictivo(SQLModel, table=True):
    """Tabla 'feedback_predictivo' — Resultado real vs predicción original de la IA.

    Insumo directo para recalibrar el modelo RUL (H2 de la tesis): compara la
    predicción emitida con lo que el técnico efectivamente encontró.
    """
    __tablename__ = "feedback_predictivo"

    id: Optional[int] = Field(default=None, primary_key=True)
    ot_id: int = Field(foreign_key="ordentrabajo.id", index=True)
    symptom_id: Optional[int] = Field(default=None, foreign_key="symptoms.id")
    prediccion_original_ia: str                       # JSON como string
    resultado_real_tecnico: str                       # 'Confirmada' | 'Falsa_Alarma' | 'Parcial'
    variables_sensores_snapshot: Optional[str] = None  # JSON como string (opcional)


class HitoCicloVida(SQLModel, table=True):
    """Tabla 'hitos_ciclo_vida' — Hitos administrativos del ciclo de vida del equipo.

    Eventos como EOS (End of Service), RECALL del fabricante, cambios
    normativos o fin de garantía. Alimentan la planificación de reemplazos
    y las alertas de vencimiento (v2.1).
    """
    __tablename__ = "hitos_ciclo_vida"

    id: Optional[int] = Field(default=None, primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id", index=True)
    tipo_evento: str                                  # 'EOS' | 'RECALL' | 'ACTUALIZACION_NORMATIVA' | 'FIN_GARANTIA'
    fecha_notificacion: Optional[date] = None         # Fecha de la carta
    fecha_limite: Optional[date] = None               # Fecha límite
    impacto_operativo: str = Field(default="MEDIO")   # 'BAJO' | 'MEDIO' | 'ALTO' | 'CRITICO'
    accion_requerida: Optional[str] = None            # Descripción
    estado: str = Field(default="NOTIFICADO")         # 'NOTIFICADO' | 'EN_PLANIFICACION' | 'RESUELTO' | 'VENCIDO'
