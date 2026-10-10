# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Fábrica de Datos Demo v2.1 (generar_demo_v21.py)
=============================================================
Genera un dataset de demostración con FECHAS RELATIVAS dinámicas para probar
TODAS las reglas de negocio v2.1 del motor de métricas (MTBF/MTTR/MDT/
Disponibilidad), junto con un reporte de verificación esperada.

Archivos que genera (por defecto, junto al script → backend/):
    1. demo_ordenes_trabajo_v21.xlsx   15 OTs de prueba (101-115) con las
                                       banderas v2.1 y relojes que activan
                                       cada regla.
    2. demo_equipos_v21.xlsx           13 equipos de soporte con criticidad,
                                       tipo_equipo y fecha_adquisicion
                                       (hoy − 30 días → ventana de 720 h).
    3. verificacion_esperada_v21.md    Reporte con los valores esperados por
                                       OT y por equipo, para comparar contra
                                       Reportes → MTBF/MTTR del CMMS.

MODO IMPORTACIÓN (recomendado para las OTs):
    python generar_demo_v21.py --importar
    Genera los 3 archivos Y ADEMÁS importa equipos + OTs directamente en
    cmms_bioai.db (bitácora nativa + síntomas/feedback de la OT 109) y
    ejecuta una VALIDACIÓN AUTOMÁTICA contra el motor v2.1 real
    (_calcular_indicadores_v21). Idempotente: reemplaza las OTs 101-115
    (con sus hijos) en cada corrida; nunca toca otras OTs.

DISEÑO TEMPORAL (fechas relativas — funciona cualquier día que se ejecute):
    - Ancla: AHORA. La última OT en cerrar (OT 105) cierra 1 h antes de la
      generación y todo el dataset se extiende ~15.8 días hacia atrás.
    - OT 102 (reincidencia) cierra... se crea EXACTAMENTE 48 h después de la
      resolución de la OT 101 → activa ventana_garantia_reparacion (<72 h).
    - OT 105 (logística): 270 h de MDT, 267.5 h de espera de repuesto (11 días).
    - OT 106 (pausa): 4 h de pausa técnica dentro de 6.5 h de reparación bruta.
    - OT 108 (cierre administrativo): MDT 128 h, MTTR excluido.
    - OT 110 (baja de equipo): MDT 99 h que SÍ cuenta para Disponibilidad.
    - fecha_adquisicion de los 13 equipos = HOY − 30 días → la ventana del
      motor (días completos hasta HOY) da 720 h calendario el MISMO DÍA de la
      generación → los valores del reporte .md cuadran exacto si se verifica
      el mismo día (ver nota en verificacion_esperada_v21.md).

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python generar_demo_v21.py [--importar] [--dir RUTA_SALIDA]
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timedelta, date
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
DB_NAME = "cmms_bioai.db"

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    print("❌ Falta openpyxl. Instálalo con: pip install openpyxl")
    raise SystemExit(1)

FMT_FECHA = "%Y-%m-%d %H:%M:%S"

# Días de observación demo: ventana del motor = (HOY − fecha_adquisicion) días
# completos → 30 días × 24 h = 720 h calendario (verificado el mismo día).
HORIZONTE_DIAS = 30

# Colchón: la última OT en cerrar es la OT 105 (res = +22200 min por su
# logística de 11 días) y resuelve 60 min antes de "ahora"; el ancla (OT 101)
# queda 22800 min (~15.8 días) hacia atrás. TODAS las marcas son relativas.
# [v2.1.3 del parche: antes SPAN=19440 (< 22200) dejaba la resolución de la
#  OT 105 ~45 h en el FUTURO — cosmética corregida, checks relativos intactos]
COLCHON_FIN_MIN = 60
SPAN_TOTAL_MIN = 22200


# ============================================================
# EQUIPOS DE SOPORTE (13) — formato del importador de Excel
# (/equipos/import-excel). Las 2 últimas columnas (tipo_equipo,
# criticidad) son informativas: el importador oficial las ignora
# (usa nombre_corto/modelo/numero_serie/marca obligatorias); el
# modo --importar de ESTE script sí las persiste en la BD.
# ============================================================

def construir_equipos(hoy: date) -> list[dict]:
    """13 equipos demo con fecha_adquisicion relativa (hoy − 30 días)."""
    adq = (hoy - timedelta(days=HORIZONTE_DIAS)).strftime("%Y-%m-%d")
    filas = [
        # nombre_corto, tipo_equipo, criticidad, modelo, marca, ubicacion
        ("Bomba de Infusión 1",    "Bomba de Infusión",    "Alta",    "Alaris GP",     "BD",           "UCI Adultos"),
        ("Monitor Signos Vitales", "Monitor",              "Alta",    "IPM-12",        "Mindray",      "Hospitalización"),
        ("Ecógrafo 4D",            "Ecógrafo",             "Alta",    "Voluson E8",    "GE Healthcare","Ginecología"),
        ("Equipo de Rayos X",      "Rayos X",              "Alta",    "Digital FX-40", "Siemens",      "Imagenología"),
        ("Máquina de Hemodiálisis","Hemodiálisis",         "Crítica", "4008S",         "Fresenius",    "Unidad Renal"),
        ("Resonancia Magnética",   "Resonancia",           "Crítica", "Magnetom 1.5T", "Siemens",      "Imagenología"),
        ("Ventilador Mecánico",    "Ventilador",           "Crítica", "V60",           "Philips",      "UCI Adultos"),
        ("Desfibrilador Zoll",     "Desfibrilador",        "Crítica", "R Series",      "Zoll",         "Emergencia"),
        ("Centrífuga Eppendorf",   "Centrífuga",           "Media",   "5810R",         "Eppendorf",    "Laboratorio"),
        ("Autoclave Steris",       "Autoclave",            "Alta",    "Amsco 3011",    "Steris",       "Esterilización"),
        ("Microscopio Olympus",    "Microscopio",          "Media",   "CX23",          "Olympus",      "Laboratorio"),
        ("Balanza Analítica",      "Balanza",              "Media",   "PA214",         "Ohaus",        "Laboratorio"),
        ("Electrocardiógrafo GE",  "Electrocardiógrafo",   "Alta",    "MAC 2000",      "GE Healthcare","Cardiología"),
    ]
    equipos = []
    for i, (nombre, tipo, crit, modelo, marca, ubic) in enumerate(filas, start=1):
        equipos.append({
            "nombre_corto": nombre,
            "modelo": modelo,
            "numero_serie": f"DEMO-V21-{i:03d}",
            "numero_material": "",
            "marca": marca,
            "fecha_adquisicion": adq,
            "fecha_inicio_garantia": "",
            "fecha_fin_garantia": "",
            "ubicacion_actual": ubic,
            "estado": "Operativo",
            "proveedor_principal": "",
            "condicion_origen": "Compra",
            "descripcion": f"Equipo demo para pruebas v2.1 ({tipo})",
            "observaciones": "Dataset demo generado por generar_demo_v21.py",
            "tipo_equipo": tipo,
            "criticidad": crit,
        })
    return equipos


NOMBRES_EQUIPOS = [
    "Bomba de Infusión 1", "Monitor Signos Vitales", "Ecógrafo 4D",
    "Equipo de Rayos X", "Máquina de Hemodiálisis", "Resonancia Magnética",
    "Ventilador Mecánico", "Desfibrilador Zoll", "Centrífuga Eppendorf",
    "Autoclave Steris", "Microscopio Olympus", "Balanza Analítica",
    "Electrocardiógrafo GE",
]


# ============================================================
# OTS DEMO (15) — offsets en MINUTOS desde el ANCLA:
#   ancla = AHORA − 60 min (colchón) − 370 h (span hasta el cierre de la OT 105)
# Relojes resultantes (alineados al motor v2.1.2):
#   MTTA = creación→asignación | brutas = inicio→resolución
#   activas = brutas − pausa − espera(logística) | MDT = creación→resolución
# ============================================================

def _ot(ot_id, equipo, tipo_equipo, titulo, origen, impacto, estado, prioridad,
        cre, asig, ini, res, texto, codigo="", causa="", accion="", **flags):
    """Constructor compacto de una OT demo (defaults v2.1 seguros)."""
    d = dict(
        ot_id=ot_id, equipo=equipo, tipo_equipo=tipo_equipo, titulo=titulo,
        tipo_origen_ot=origen, tipo_impacto=impacto, estado_actual=estado,
        sub_estado_logistica=None, prioridad=prioridad,
        parent_ot_id=None, failure_sequence=1,
        ventana_garantia=False, es_reparacion_inefectiva=False,
        en_pausa_tecnica=False, motivo_pausa=None,
        tiempo_pausa_acumulado=0.0, horas_espera_repuesto=0.0,
        n_reaperturas=0, unidad_tiempo="horas",
        creacion=cre, asignacion=asig, inicio_trabajo=ini, resolucion=res,
        codigo_falla=codigo, causa_raiz=causa, accion_tomada=accion,
        motivo_cancelacion=None, cierre_administrativo=False,
        excluida_de_MTTR=False, mdt_excluido_disponibilidad=False,
        texto_libre_informe=texto,
    )
    d.update(flags)
    return d


def construir_ots() -> list[dict]:
    """Las 15 OTs demo. Offsets en minutos desde el ancla (ver docstring)."""
    return [
        # ── Línea base + Regla 3 (ventana de garantía 72 h) ──
        _ot(101, "Bomba de Infusión 1", "Bomba de Infusión", "Falla en motor",
            "Usuario", "REAL", "Completada", "Media",
            0, 60, 90, 180,
            "Reemplazo exitoso de motor. Equipo operativo.",
            codigo="F-101", causa="Desgaste natural", accion="Cambio de motor"),
        _ot(102, "Bomba de Infusión 1", "Bomba de Infusión", "Reincidencia falla motor",
            "Usuario", "REAL", "Completada", "Media",
            3060, 3120, 3150, 3240,
            "Falla 48 h después de la reparación (dentro de la ventana de "
            "garantía de 72 h). Lote de repuestos defectuoso.",
            codigo="F-101", causa="Repuesto defectuoso", accion="Cambio de motor con lote nuevo",
            parent_ot_id=101, failure_sequence=2,
            ventana_garantia=True, es_reparacion_inefectiva=True),

        # ── Regla 4: falsas alarmas / error usuario (MDT excluido) ──
        _ot(103, "Monitor Signos Vitales", "Monitor", "Monitor no enciende",
            "Usuario", "REAL", "Cancelada", "Alta",
            4920, 4950, None, 4950,
            "Enfermera reportó falla, pero era el cable de poder desconectado. "
            "Cancelada en Abierta (0.5 h). MDT excluido de Disponibilidad.",
            motivo_cancelacion="Falsa_Alarma", mdt_excluido_disponibilidad=True),
        _ot(104, "Monitor Signos Vitales", "Monitor", "Alarma de obstrucción",
            "Usuario", "REAL", "Cancelada", "Media",
            4980, 5000, 5010, 5025,
            "Técnico acudió al sitio. Válvula de infusión cerrada por error de "
            "operación. MDT excluido de Disponibilidad.",
            motivo_cancelacion="Error_Usuario", mdt_excluido_disponibilidad=True),

        # ── Logística larga (11 días ≈ 267.5 h de espera de repuesto) ──
        _ot(105, "Ecógrafo 4D", "Ecógrafo", "Falla tarjeta procesamiento",
            "Usuario", "REAL", "Completada", "Alta",
            6000, 6120, 6150, 22200,
            "Repuesto 1 fallido. Repuesto 2 importado (En_Aduana). Logística "
            "acumulada: 11 días (267.5 h de espera). MTTR hombre = 0.0 h.",
            codigo="F-205", causa="Daño eléctrico", accion="Reemplazo de tarjeta",
            sub_estado_logistica="En_Aduana", horas_espera_repuesto=267.5),

        # ── Reglas 11-14: pausa técnica por emergencia clínica ──
        _ot(106, "Equipo de Rayos X", "Rayos X", "Falla en mesa",
            "Usuario", "REAL", "Completada", "Media",
            7440, 7500, 7530, 7920,
            "Técnico pausó 4 h por emergencia en Hemodiálisis (ver OT 107). "
            "MTTR Hombre = 2.5 h, Calendario = 6.5 h.",
            codigo="F-310", causa="Contacto sucio", accion="Limpieza y ajuste",
            en_pausa_tecnica=True, motivo_pausa="Emergencia_Clinica",
            tiempo_pausa_acumulado=4.0),

        # ── Línea base (la emergencia atendida de la OT 106) ──
        _ot(107, "Máquina de Hemodiálisis", "Hemodiálisis", "Paro durante tratamiento",
            "Usuario", "REAL", "Completada", "Crítica",
            7620, 7635, 7650, 7770,
            "Emergencia clínica atendida por el técnico de Rayos X. "
            "Resolución exitosa.",
            codigo="F-401", causa="Desgaste bomba", accion="Cambio de bomba peristáltica"),

        # ── Regla 6: cierre administrativo (MTTR excluido, MDT cuenta) ──
        _ot(108, "Resonancia Magnética", "Resonancia", "Falla criogénica",
            "Usuario", "REAL", "Completada", "Crítica",
            8880, 9120, 9240, 16560,
            "Técnico abandonó el caso. Coordinador forzó el cierre "
            "administrativo. MTTR excluido. MDT (128 h) sí cuenta.",
            codigo="F-501", causa="Diagnostico_Incompleto", accion="Cierre_Administrativo",
            cierre_administrativo=True, excluida_de_MTTR=True),

        # ── Regla 15: OT predictiva generada por IA con síntomas ──
        _ot(109, "Ventilador Mecánico", "Ventilador", "Falla de compresión",
            "Sistema/IA", "PRECAUTORIO", "Completada", "Media",
            10200, 10320, 10350, 10440,
            "OT generada por predicción RUL del sistema. Síntoma de usuario "
            "anexado: 'ruido extraño'. Confirmado por el técnico.",
            codigo="F-601", causa="Contaminación", accion="Limpieza de válvula"),

        # ── Regla 4+5: baja de equipo (MDT SÍ cuenta, MTTR fuera) ──
        _ot(110, "Desfibrilador Zoll", "Desfibrilador", "No carga batería",
            "Usuario", "REAL", "Cancelada", "Alta",
            11820, 11880, 11910, 17760,
            "Comité decidió la baja técnica. Equipo donado. MDT (99 h) SÍ "
            "cuenta para Disponibilidad; MTTR excluido del promedio.",
            motivo_cancelacion="Baja_Equipo", excluida_de_MTTR=True),

        # ── Línea base: MP programado (no es falla correctiva) ──
        _ot(111, "Centrífuga Eppendorf", "Centrífuga", "Mantenimiento Preventivo",
            "Programado", "PROGRAMADO", "Completada", "Baja",
            13140, 13140, 13170, 13230,
            "MP trimestral sin novedades.",
            codigo="P-101", causa="Rutinario", accion="Lubricación y calibración"),

        # ── Líneas base restantes ──
        _ot(112, "Autoclave Steris", "Autoclave", "Falla de puerta",
            "Usuario", "REAL", "Completada", "Alta",
            14760, 14820, 14850, 14940,
            "Reparación correctiva estándar.",
            codigo="F-701", causa="Desgaste mecánico", accion="Ajuste de cerradura"),
        _ot(113, "Microscopio Olympus", "Microscopio", "Lámpara fundida",
            "Usuario", "REAL", "Completada", "Baja",
            16140, 16200, 16215, 16245,
            "Repuesto disponible en stock local.",
            codigo="F-801", causa="Fin de vida útil", accion="Cambio de lámpara halógena"),
        _ot(114, "Balanza Analítica", "Balanza", "Desviación de calibración",
            "Usuario", "REAL", "Completada", "Media",
            17520, 17580, 17610, 17700,
            "Se ajustaron los parámetros internos de calibración.",
            codigo="F-901", causa="Error de calibración", accion="Calibración externa"),
        _ot(115, "Electrocardiógrafo GE", "Electrocardiógrafo", "Error de software",
            "Usuario", "REAL", "Completada", "Media",
            19320, 19380, 19410, 19440,
            "Reinicio y actualización de firmware aplicados.",
            codigo="F-102", causa="Software", accion="Actualización de firmware"),
    ]


def _ancla() -> datetime:
    """Datetime base del dataset: AHORA − colchón − span. Microsegundos en 0."""
    ahora = datetime.now().replace(microsecond=0)
    return ahora - timedelta(minutes=COLCHON_FIN_MIN + SPAN_TOTAL_MIN)


def _fechas_ot(ot: dict, ancla: datetime) -> dict:
    """Offsets en minutos → datetimes reales."""
    def f(minutos):
        return None if minutos is None else ancla + timedelta(minutes=minutos)
    return {
        "fecha_creacion": f(ot["creacion"]),
        "fecha_asignacion": f(ot["asignacion"]),
        "fecha_inicio_trabajo": f(ot["inicio_trabajo"]),
        "fecha_resolucion": f(ot["resolucion"]),
    }


# ============================================================
# Writers Excel
# ============================================================

_ESTILO_HDR = Font(bold=True, color="FFFFFF")
_RELLENO_HDR = PatternFill("solid", fgColor="1F4E79")
_ANCHO_OT = {
    "ot_id": 8, "equipo": 22, "tipo_equipo": 18, "titulo": 26,
    "tipo_origen_ot": 13, "tipo_impacto": 13, "estado_actual": 12,
    "sub_estado_logistica": 16, "prioridad": 10, "parent_ot_id": 11,
    "failure_sequence": 11, "ventana_garantia": 12, "es_reparacion_inefectiva": 13,
    "en_pausa_tecnica": 12, "motivo_pausa": 18, "tiempo_pausa_acumulado": 12,
    "horas_espera_repuesto": 12, "n_reaperturas": 11, "unidad_tiempo": 11,
    "fecha_creacion": 19, "fecha_asignacion": 19, "fecha_inicio_trabajo": 19,
    "fecha_resolucion": 19, "codigo_falla": 11, "causa_raiz": 20,
    "accion_tomada": 26, "motivo_cancelacion": 16, "cierre_administrativo": 12,
    "excluida_de_MTTR": 12, "mdt_excluido_disponibilidad": 14,
    "texto_libre_informe": 70,
}


def _escribir_xlsx(ruta: Path, columnas: list[str], filas: list[list],
                   anchos: dict | None = None, hoja: str = "Datos"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = hoja
    ws.append(columnas)
    for c in ws[1]:
        c.font = _ESTILO_HDR
        c.fill = _RELLENO_HDR
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    for fila in filas:
        ws.append(fila)
    anchos = anchos or {}
    for i, col in enumerate(columnas, start=1):
        ws.column_dimensions[get_column_letter(i)].width = anchos.get(col, 16)
    ws.freeze_panes = "A2"
    wb.save(ruta)


COLS_OT = [
    "ot_id", "equipo", "tipo_equipo", "titulo", "tipo_origen_ot", "tipo_impacto",
    "estado_actual", "sub_estado_logistica", "prioridad", "parent_ot_id",
    "failure_sequence", "ventana_garantia", "es_reparacion_inefectiva",
    "en_pausa_tecnica", "motivo_pausa", "tiempo_pausa_acumulado",
    "horas_espera_repuesto", "n_reaperturas", "unidad_tiempo",
    "fecha_creacion", "fecha_asignacion", "fecha_inicio_trabajo",
    "fecha_resolucion", "codigo_falla", "causa_raiz", "accion_tomada",
    "motivo_cancelacion", "cierre_administrativo", "excluida_de_MTTR",
    "mdt_excluido_disponibilidad", "texto_libre_informe",
]

COLS_EQUIPOS = [
    "nombre_corto", "modelo", "numero_serie", "numero_material", "marca",
    "fecha_adquisicion", "fecha_inicio_garantia", "fecha_fin_garantia",
    "ubicacion_actual", "estado", "proveedor_principal", "condicion_origen",
    "descripcion", "observaciones", "tipo_equipo", "criticidad",
]


def _celda(v):
    """None → '' ; bool → 'True'/'False' ; datetime → string estándar."""
    if v is None:
        return ""
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, datetime):
        return v.strftime(FMT_FECHA)
    return v


def generar_excel_ots(ruta: Path, ots: list[dict], ancla: datetime):
    filas = []
    for ot in ots:
        fechas = _fechas_ot(ot, ancla)
        fila = []
        for col in COLS_OT:
            if col == "fecha_creacion":
                fila.append(_celda(fechas["fecha_creacion"]))
            elif col == "fecha_asignacion":
                fila.append(_celda(fechas["fecha_asignacion"]))
            elif col == "fecha_inicio_trabajo":
                fila.append(_celda(fechas["fecha_inicio_trabajo"]))
            elif col == "fecha_resolucion":
                fila.append(_celda(fechas["fecha_resolucion"]))
            else:
                fila.append(_celda(ot.get(col)))
        filas.append(fila)
    _escribir_xlsx(ruta, COLS_OT, filas, anchos=_ANCHO_OT, hoja="OTs Demo v2.1")


def generar_excel_equipos(ruta: Path, equipos: list[dict]):
    filas = [[_celda(eq.get(c)) for c in COLS_EQUIPOS] for eq in equipos]
    anchos = {"nombre_corto": 24, "modelo": 16, "numero_serie": 14, "marca": 14,
              "fecha_adquisicion": 16, "ubicacion_actual": 16, "estado": 12,
              "condicion_origen": 14, "descripcion": 38, "observaciones": 40,
              "tipo_equipo": 18, "criticidad": 11}
    _escribir_xlsx(ruta, COLS_EQUIPOS, filas, anchos=anchos, hoja="Equipos Demo v2.1")


# ============================================================
# Reporte de verificación esperada (.md)
# ============================================================

_MD_PLANTILLA = """# REPORTE DE VERIFICACIÓN ESPERADA — Dataset Demo v2.1

_Generado por `generar_demo_v21.py` el {generado}._
_Ancla temporal: OTs entre **{f_min}** y **{f_max}** (fechas relativas a la ejecución)._
_Fecha de adquisición aplicada a los 13 equipos: **{fecha_adq}** (hoy − {horizonte} días → ventana de {hc} h calendario)._

> **NOTA DE PRECISIÓN:** el motor v2.1.2 mide la ventana en **días completos desde
> `fecha_adquisicion` hasta HOY**. Los valores de MTBF/Disponibilidad cuadran
> exacto si la verificación se hace **el mismo día** de la generación/importación.
> Si verificas días después, la ventana crece 24 h por día (MDT, MTTR y los
> contadores n_* NO cambian; solo MTBF y Disponibilidad se desplazan levemente).

## Instrucciones de Uso

1. Ejecutar: `python generar_demo_v21.py` (genera los 3 archivos junto al script)
2. **Ruta recomendada para las OTs:** `python generar_demo_v21.py --importar`
   (importa equipos + OTs 101-115 directamente en `cmms_bioai.db`, genera la
   bitácora nativa y **auto-valida contra el motor v2.1**).
   *Nota: el CMMS v2.1.2 aún no tiene importador Excel de OTs; el Excel
   `demo_ordenes_trabajo_v21.xlsx` queda como formato de referencia/respaldo.*
3. Alternativa por UI para equipos: Configuración → "Limpiar Base de Datos" →
   "Cargar datos TEST" → Equipos → "Importar Excel" con `demo_equipos_v21.xlsx`.
   ⚠ Si los 13 equipos YA existen en tu BD (p. ej. creados antes con series
   `V21-*`), NO importes ese Excel: el importador oficial busca por
   `numero_serie` y crearía duplicados; `--importar` reutiliza por nombre.
   (ojo: el importador oficial de equipos no persiste `tipo_equipo` ni
   `criticidad`; `--importar` sí lo hace).
4. Reiniciar uvicorn y abrir **Reportes → MTBF/MTTR** (o `/reportes/mtbf-mttr`).
5. Comparar con los valores esperados de este reporte.

## Verificaciones por OT

{por_ot}

## Verificaciones Globales (Reportes → MTBF/MTTR)

### MTBF
- **Bomba de Infusión 1:** n_fallas_correctivas=2, n_fallas_reales=1,
  n_excluidas_garantia=1 (OT 102 sale del denominador por Regla 3).
- **MTBF esperado:** {mtbf_bomba} h = ({hc} h calendario − 6.0 h MDT) / 1 falla real.
- **Advertencia esperada:** "Basado en 1 fallas (mínimo recomendado: 3)".

### MTTR (horas ACTIVAS: brutas − pausas − espera de repuestos)
| Equipo | MTTR esperado | Detalle |
|---|---|---|
| Bomba de Infusión 1 | {mttr_bomba} h | (1.5 + 1.5) / 2 — la reincidencia SÍ aporta a MTTR (Regla 3) |
| Monitor Signos Vitales | — (None) | sin fallas completadas (103/104 canceladas) |
| Ecógrafo 4D | 0.0 h | 267.5 h brutas − 267.5 h logística = 0 |
| Equipo de Rayos X | 2.5 h | 6.5 h brutas − 4.0 h pausa (Reglas 11-14) |
| Máquina de Hemodiálisis | 2.0 h | reparación directa |
| Resonancia Magnética | — (None) | n_validas_mttr=0 (OT 108 excluida, Regla 6); n_excluidas_mttr=1 |
| Ventilador Mecánico | 1.5 h | OT de IA (Sistema/IA sí es falla real) |
| Desfibrilador Zoll | — (None) | cancelada (Baja_Equipo) |
| Centrífuga Eppendorf | — (None) | n_programadas=1 (MP no es falla) |
| Autoclave Steris | 1.5 h | reparación directa |
| Microscopio Olympus | 0.5 h | reparación directa |
| Balanza Analítica | 1.5 h | calibración correctiva |
| Electrocardiógrafo GE | 0.5 h | reparación directa |

- **Referencia global (manual):** suma activas 13.0 h / 10 OTs válidas = **1.30 h**.
  ⚠ La spec original sumaba 11 términos (incl. OT 111 = 1.0 h) → 1.27 h; el motor
  v2.1 **excluye las OTs `Programado` del MTTR** (no son fallas correctivas), por
  lo que la cifra correcta contra la que muestra el CMMS es **1.30 h**. El promedio
  oficial es POR EQUIPO (tabla anterior), no global.

### Disponibilidad = (horas calendario − MDT válido) / horas calendario
| Equipo | Disponibilidad esperada | Motivo |
|---|---|---|
| Monitor Signos Vitales | **100.0 %** | único MDT (0.5 + 0.75 h) excluido por Regla 4 |
| Centrífuga Eppendorf | **100.0 %** | MP programado: no es falla → no suma MDT |
| Desfibrilador Zoll | **86.2 %** | MDT de la baja (99.0 h) SÍ cuenta (Regla 4+5) |
| Ecógrafo 4D | **62.5 %** | logística larga: MDT 270.0 h de 720 h |
| Resonancia Magnética | 82.2 % | MDT 128.0 h (cierre administrativo SÍ cuenta) |
| Ventilador Mecánico | 99.4 % | MDT 4.0 h |
| Bomba de Infusión 1 | 99.2 % | MDT 6.0 h (2 fallas × 3 h) |
| Equipo de Rayos X | 98.9 % | MDT 8.0 h |
| Autoclave Steris | 99.6 % | MDT 3.0 h |
| Balanza Analítica | 99.6 % | MDT 3.0 h |
| Electrocardiógrafo GE | 99.7 % | MDT 2.0 h |
| Máquina de Hemodiálisis | 99.7 % | MDT 2.5 h |
| Microscopio Olympus | 99.8 % | MDT 1.75 h |

- **MDT excluido global (Regla 4):** 0.5 h (OT 103) + 0.75 h (OT 104) = 1.25 h
  (el reporte lo muestra como **1.2** por redondeo a 1 decimal).

## Checklist de Verificación
- [ ] OT 102 tiene ventana_garantia=True y se creó a 48 h de la resolución de la OT 101
- [ ] OT 103/104 tienen mdt_excluido_disponibilidad=True
- [ ] OT 105 tiene horas_espera_repuesto=267.5 y MTTR=0.0
- [ ] OT 106 tiene tiempo_pausa_acumulado=4.0 y MTTR=2.5 (no 6.5)
- [ ] OT 108 tiene cierre_administrativo=True y el equipo muestra MTTR=None
- [ ] OT 110 tiene mdt_excluido_disponibilidad=False (el MDT de 99 h SÍ cuenta)
- [ ] Bomba de Infusión 1 muestra la advertencia de MTBF con n<3
- [ ] Centrífuga Eppendorf muestra n_programadas=1 y no afecta MTTR
- [ ] Ventilador Mecánico es tipo_origen=Sistema/IA y SÍ cuenta como falla real
"""


def _fmt_h(h):
    return "—" if h is None else f"{h:.1f}"


def generar_md(ruta: Path, ots: list[dict], ancla: datetime, equipos: list[dict]):
    fechas_min = min(_fechas_ot(o, ancla)["fecha_creacion"] for o in ots)
    fechas_max = max(_fechas_ot(o, ancla)["fecha_resolucion"] for o in ots
                     if _fechas_ot(o, ancla)["fecha_resolucion"])
    fecha_adq = equipos[0]["fecha_adquisicion"]

    bloques = []
    detalle = {
        101: ("Línea base", "Equipo \"Bomba de Infusión 1\" debe mostrar "
              "n_fallas_correctivas=2, n_fallas_reales=1 (junto a OT 102)"),
        102: ("Regla 3 (Ventana 72 h)", "n_excluidas_garantia=1; MTBF calculado "
              "con 1 sola falla real; la reincidencia SÍ aporta al MTTR (1.5 h)"),
        103: ("Regla 4 (Falsa Alarma en Abierta)", "Equipo \"Monitor Signos "
              "Vitales\": mdt_excluido_horas total = 1.25 h (0.5 de esta OT + "
              "0.75 de la OT 104); Disponibilidad = 100%"),
        104: ("Regla 4 (Error Usuario en Proceso)", "mdt_excluido_horas "
              "acumulado del Monitor = 1.25 h (0.5 + 0.75); Disponibilidad = 100%"),
        105: ("Logística larga", "MTTR=0.0 h; Disponibilidad=62.5%; "
              "mdt_valido_horas=270.0"),
        106: ("Reglas 11-14 (Pausa por emergencia)", "MTTR=2.5 h (no 6.5 h); "
              "Disponibilidad=98.9%"),
        107: ("Línea base (emergencia atendida)", "MTTR=2.0 h; "
              "Disponibilidad=99.7%"),
        108: ("Regla 6 (Cierre administrativo)", "n_excluidas_mttr=1, "
              "n_validas_mttr=0, MTTR=None; mdt_valido_horas=128.0; "
              "Disponibilidad=82.2%"),
        109: ("Regla 15 (OT predictiva de IA)", "n_programadas=0 (es falla "
              "correctiva real aunque origen=IA); MTTR=1.5 h; Disponibilidad=99.4%"),
        110: ("Regla 4+5 (Baja de equipo)", "mdt_valido_horas=99.0 (SÍ cuenta); "
              "Disponibilidad=86.2% (no 100%); MTTR=None"),
        111: ("Línea base (MP programado)", "n_programadas=1; NO cuenta como "
              "falla correctiva, no aporta al MTTR y NO suma MDT "
              "(Disponibilidad=100%)"),
        112: ("Línea base (reparación normal)", "MTTR=1.5 h; Disponibilidad=99.6%"),
        113: ("Línea base (repuesto en stock)", "MTTR=0.5 h; Disponibilidad=99.8%"),
        114: ("Línea base (calibración)", "MTTR=1.5 h; Disponibilidad=99.6%"),
        115: ("Línea base (software)", "MTTR=0.5 h; Disponibilidad=99.7%"),
    }
    for ot in ots:
        fechas = _fechas_ot(ot, ancla)
        mtta = (fechas["fecha_asignacion"] - fechas["fecha_creacion"])
        brutas = None
        if fechas["fecha_inicio_trabajo"] and fechas["fecha_resolucion"]:
            brutas = fechas["fecha_resolucion"] - fechas["fecha_inicio_trabajo"]
        mdt = None
        if fechas["fecha_resolucion"]:
            mdt = fechas["fecha_resolucion"] - fechas["fecha_creacion"]
        activas = None
        if brutas is not None:
            activas = max(brutas.total_seconds() / 3600
                          - ot["tiempo_pausa_acumulado"]
                          - (ot["horas_espera_repuesto"] if ot["sub_estado_logistica"] else 0.0),
                          0.0)
        regla, verificar = detalle[ot["ot_id"]]
        flags = []
        if ot["ventana_garantia"]:
            flags.append("ventana_garantia_reparacion=True")
        if ot["es_reparacion_inefectiva"]:
            flags.append("es_reparacion_inefectiva=True")
        if ot["parent_ot_id"]:
            flags.append(f"parent_ot_id={ot['parent_ot_id']}")
        if ot["failure_sequence"] != 1:
            flags.append(f"failure_sequence={ot['failure_sequence']}")
        if ot["sub_estado_logistica"]:
            flags.append(f"sub_estado_logistica={ot['sub_estado_logistica']}")
        if ot["horas_espera_repuesto"]:
            flags.append(f"horas_espera_repuesto={ot['horas_espera_repuesto']}")
        if ot["en_pausa_tecnica"]:
            flags.append(f"en_pausa_tecnica=True (motivo={ot['motivo_pausa']}, "
                         f"tiempo_pausa_acumulado={ot['tiempo_pausa_acumulado']} h)")
        if ot["cierre_administrativo"]:
            flags.append("cierre_administrativo=True")
        if ot["excluida_de_MTTR"]:
            flags.append("excluida_de_MTTR=True")
        if ot["mdt_excluido_disponibilidad"]:
            flags.append("mdt_excluido_disponibilidad=True")
        if ot["motivo_cancelacion"]:
            flags.append(f"motivo_cancelacion={ot['motivo_cancelacion']}")
        if ot["tipo_origen_ot"] != "Usuario":
            flags.append(f"tipo_origen_ot={ot['tipo_origen_ot']}, tipo_impacto={ot['tipo_impacto']}")
        bloque = [
            f"### OT {ot['ot_id']} ({ot['equipo']} — {ot['titulo']})",
            f"- **Estado:** {ot['estado_actual']}",
        ]
        for fl in flags:
            bloque.append(f"- **{fl.split('=')[0]}:** {fl.split('=', 1)[1] if '=' in fl else 'True'}")
        bloque.append(f"- **MTTA esperado (creación→asignación):** {mtta.total_seconds() / 3600:.2f} h")
        if brutas is not None:
            bloque.append(f"- **MTTR_Hombre esperado:** {_fmt_h(activas)} h "
                          f"(brutas {brutas.total_seconds() / 3600:.2f} h)")
        else:
            bloque.append("- **MTTR_Hombre esperado:** — (OT cancelada sin trabajo registrado)")
        if mdt is not None:
            bloque.append(f"- **MDT esperado (creación→resolución):** {mdt.total_seconds() / 3600:.2f} h")
        bloque.append(f"- **Regla probada:** {regla}")
        bloque.append(f"- **Verificar en reporte:** {verificar}")
        bloques.append("\n".join(bloque))

    contenido = _MD_PLANTILLA.format(
        generado=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        f_min=fechas_min.strftime(FMT_FECHA),
        f_max=fechas_max.strftime(FMT_FECHA),
        fecha_adq=fecha_adq,
        horizonte=HORIZONTE_DIAS,
        hc=HORIZONTE_DIAS * 24,
        por_ot="\n\n".join(bloques),
        mtbf_bomba=f"{(HORIZONTE_DIAS * 24 - 6.0) / 1:.1f}",
        mttr_bomba="1.5",
    )
    ruta.write_text(contenido, encoding="utf-8")


# ============================================================
# Verificación de equipos en la BD (solo lectura, stdlib)
# ============================================================

def verificar_equipos_bd() -> dict:
    """Best-effort: consulta cmms_bioai.db y reporta qué equipos demo existen.
    Nunca falla: si la BD no existe o no es legible, devuelve estado 'sin_bd'."""
    res = {"estado": "sin_bd", "existentes": [], "faltantes": list(NOMBRES_EQUIPOS)}
    ruta_db = BACKEND_DIR / DB_NAME
    if not ruta_db.exists():
        return res
    try:
        con = sqlite3.connect(str(ruta_db))
        con.row_factory = sqlite3.Row
        tablas = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        if "equipo" not in tablas:
            con.close()
            return res
        filas = con.execute("SELECT nombre_corto, numero_serie FROM equipo").fetchall()
        con.close()
        nombres_bd = {r["nombre_corto"].strip() for r in filas if r["nombre_corto"]}
        series_bd = {r["numero_serie"].strip() for r in filas if r["numero_serie"]}
        existentes, faltantes = [], []
        for nombre in NOMBRES_EQUIPOS:
            if nombre in nombres_bd:
                existentes.append(nombre)
            else:
                faltantes.append(nombre)
        res.update(estado="ok", existentes=existentes, faltantes=faltantes,
                   series_demo=len([s for s in series_bd if s.startswith("DEMO-V21")]))
        return res
    except Exception as e:  # pragma: no cover
        res["estado"] = f"error: {e}"
        return res


# ============================================================
# MODO --importar: carga directa a cmms_bioai.db + validación
# ============================================================

# Aliases de estado por si el Excel llega con códigos v2.1 o variantes
ALIAS_ESTADOS = {
    "Completada": "Completada", "COMPLETED": "Completada",
    "Cancelada": "Cancelada", "CANCELED": "Cancelada",
}
MOTIVOS_EXCLUYEN_MDT = {"Falsa_Alarma", "Duplicado", "Error_Usuario"}
OT_ID_FEEDBACK = 109

# Valores esperados del motor v2.1 para los 13 equipos demo (misma jornada)
ESPERADO_EQUIPOS = {
    "Bomba de Infusión 1":     dict(mtbf_horas=714.0, mttr_horas=1.5, disponibilidad_pct=99.2,
                                    n_fallas_correctivas=2, n_fallas_reales=1,
                                    n_excluidas_garantia=1, mdt_valido_horas=6.0),
    "Monitor Signos Vitales":  dict(mttr_horas=None, disponibilidad_pct=100.0,
                                    mdt_excluido_horas=1.2),
    "Ecógrafo 4D":             dict(mttr_horas=0.0, disponibilidad_pct=62.5,
                                    mdt_valido_horas=270.0),
    "Equipo de Rayos X":       dict(mttr_horas=2.5, disponibilidad_pct=98.9),
    "Máquina de Hemodiálisis": dict(mttr_horas=2.0, disponibilidad_pct=99.7),
    "Resonancia Magnética":    dict(mttr_horas=None, disponibilidad_pct=82.2,
                                    n_excluidas_mttr=1, n_validas_mttr=0),
    "Ventilador Mecánico":     dict(mttr_horas=1.5, disponibilidad_pct=99.4,
                                    n_programadas=0),
    "Desfibrilador Zoll":      dict(mttr_horas=None, disponibilidad_pct=86.2,
                                    mdt_valido_horas=99.0),
    "Centrífuga Eppendorf":    dict(mttr_horas=None, disponibilidad_pct=100.0,
                                    n_programadas=1),
    "Autoclave Steris":        dict(mttr_horas=1.5, disponibilidad_pct=99.6),
    "Microscopio Olympus":     dict(mttr_horas=0.5, disponibilidad_pct=99.8),
    "Balanza Analítica":       dict(mttr_horas=1.5, disponibilidad_pct=99.6),
    "Electrocardiógrafo GE":   dict(mttr_horas=0.5, disponibilidad_pct=99.7),
}


def modo_importar(ots: list[dict], equipos: list[dict], ancla: datetime) -> bool:
    """Importa equipos + OTs 101-115 en cmms_bioai.db (idempotente) y valida
    contra el motor v2.1 real. Devuelve True si todos los checks pasan."""
    os.chdir(str(BACKEND_DIR))
    if str(BACKEND_DIR) not in sys.path:
        sys.path.insert(0, str(BACKEND_DIR))

    from sqlmodel import Session, select  # noqa: E402
    from database import create_db_and_tables, seed_database, engine  # noqa: E402
    from models import Equipo, EstadoOT, OrdenTrabajo, BitacoraOT  # noqa: E402
    from models.v21 import SintomaOT, FeedbackPredictivo  # noqa: E402

    print("\n[IMPORT] Preparando BD (tablas + seed catálogos)...")
    create_db_and_tables()
    seed_database()

    stats = {"equipos_creados": 0, "equipos_actualizados": 0,
             "ots_borradas": 0, "ots_importadas": 0, "eventos_bitacora": 0}

    with Session(engine) as session:
        # ── 1. Estados por NOMBRE ──
        estados_bd = {e.nombre_estado: e for e in session.exec(select(EstadoOT)).all()}
        estado_res = {}
        for ot in ots:
            nombre = ALIAS_ESTADOS.get(ot["estado_actual"].strip(), ot["estado_actual"].strip())
            if nombre not in estados_bd:
                print(f"❌ El catálogo no tiene el estado '{nombre}'. Corre el backend (seed) e reintenta.")
                return False
            estado_res[ot["ot_id"]] = estados_bd[nombre]

        # ── 2. Equipos: upsert por numero_serie → nombre_corto → crear ──
        mapa_equipo: dict[str, Equipo] = {}
        fecha_adq = date.fromisoformat(equipos[0]["fecha_adquisicion"])
        for eq in equipos:
            obj = session.exec(select(Equipo).where(
                Equipo.numero_serie == eq["numero_serie"])).first()
            if obj is None:
                obj = session.exec(select(Equipo).where(
                    Equipo.nombre_corto == eq["nombre_corto"])).first()
            if obj is None:
                obj = Equipo(
                    nombre_corto=eq["nombre_corto"], modelo=eq["modelo"],
                    numero_serie=eq["numero_serie"], numero_material=eq["numero_material"] or None,
                    marca=eq["marca"], tipo_equipo=eq["tipo_equipo"],
                    criticidad=eq["criticidad"], fecha_adquisicion=fecha_adq,
                    ubicacion_actual=eq["ubicacion_actual"], estado_id=1,
                    condicion_origen=eq["condicion_origen"],
                    descripcion=eq["descripcion"], observaciones=eq["observaciones"],
                )
                stats["equipos_creados"] += 1
            else:
                # Demo: completa metadatos clave SIN tocar historial
                obj.nombre_corto = eq["nombre_corto"]
                obj.tipo_equipo = eq["tipo_equipo"]
                obj.criticidad = eq["criticidad"]
                obj.fecha_adquisicion = fecha_adq
                stats["equipos_actualizados"] += 1
            session.add(obj)
            session.flush()
            mapa_equipo[eq["nombre_corto"]] = obj

        # ── 3. Borrar OTs 101-115 previas + TODA bitácora/síntoma/feedback
        #      del rango demo (PURGA INCONDICIONAL — v2.1.3) ──
        # Antes solo se borraban los hijos de OTs EXISTENTES: filas huérfanas
        # (de OTs borradas a mano) o remanentes de corridas anteriores
        # contaminaban los pares pausada→reanudada que alimentan la espera/
        # pausas del motor (dos generaciones de eventos ⇒ espera = esperado
        # − Δt entre corridas). Ahora se purga por rango de ids, exista o no
        # la OT padre.
        ids = [ot["ot_id"] for ot in ots]
        n_huerfanos = 0
        for ev in session.exec(select(BitacoraOT).where(
                BitacoraOT.orden_trabajo_id.in_(ids))).all():
            session.delete(ev)
            n_huerfanos += 1
        for fb in session.exec(select(FeedbackPredictivo).where(
                FeedbackPredictivo.ot_id.in_(ids))).all():
            session.delete(fb)
            n_huerfanos += 1
        for sy in session.exec(select(SintomaOT).where(
                SintomaOT.ot_id.in_(ids))).all():
            session.delete(sy)
            n_huerfanos += 1
        previas = session.exec(select(OrdenTrabajo).where(OrdenTrabajo.id.in_(ids))).all()
        for ot_prev in previas:
            session.delete(ot_prev)
            stats["ots_borradas"] += 1
        session.commit()
        if n_huerfanos:
            print(f"[IMPORT] 🧹 Purga incondicional: {n_huerfanos} filas hijo "
                  f"(bitácora/síntomas/feedback) eliminadas en el rango demo 101-115 "
                  f"(incluye huérfanas/heredadas).")
        if stats["ots_borradas"]:
            print(f"[IMPORT] 🔄 {stats['ots_borradas']} OTs demo previas reemplazadas "
                  f"(con bitácora/síntomas/feedback). Otras OTs NO se tocaron.")

        # ── 4. Insertar OTs + bitácora nativa ──
        for ot in ots:
            fechas = _fechas_ot(ot, ancla)
            equipo = mapa_equipo[ot["equipo"]]
            motivo = ot["motivo_cancelacion"]
            mdt_excl = ot["mdt_excluido_disponibilidad"]
            if (ot["estado_actual"] == "Cancelada" and motivo in MOTIVOS_EXCLUYEN_MDT
                    and not mdt_excl):
                mdt_excl = True  # regla v2.1 forzosa (defensa)
            nueva = OrdenTrabajo(
                id=ot["ot_id"], equipo_id=equipo.id, estado_id=estado_res[ot["ot_id"]].id,
                prioridad=ot["prioridad"], unidad_tiempo=ot["unidad_tiempo"],
                fecha_creacion=fechas["fecha_creacion"],
                fecha_asignacion=fechas["fecha_asignacion"],
                fecha_inicio_trabajo=fechas["fecha_inicio_trabajo"],
                fecha_resolucion=fechas["fecha_resolucion"],
                titulo=ot["titulo"], descripcion_falla=ot["texto_libre_informe"],
                acciones_realizadas=ot["accion_tomada"] or None,
                parent_ot_id=ot["parent_ot_id"], failure_sequence=ot["failure_sequence"],
                tipo_origen_ot=ot["tipo_origen_ot"], tipo_impacto=ot["tipo_impacto"],
                sub_estado_logistica=ot["sub_estado_logistica"],
                ventana_garantia_reparacion=ot["ventana_garantia"],
                es_reparacion_inefectiva=ot["es_reparacion_inefectiva"],
                en_pausa_tecnica=ot["en_pausa_tecnica"], motivo_pausa=ot["motivo_pausa"],
                tiempo_pausa_acumulado=ot["tiempo_pausa_acumulado"],
                cierre_administrativo=ot["cierre_administrativo"],
                excluida_de_MTTR=ot["excluida_de_MTTR"],
                mdt_excluido_disponibilidad=mdt_excl,
                codigo_falla=ot["codigo_falla"] or None,
                causa_raiz=ot["causa_raiz"] or None,
                accion_tomada=ot["accion_tomada"] or None,
                motivo_cancelacion=motivo,
            )
            session.add(nueva)

            # Bitácora espejo del flujo real (R4) — alimenta espera de
            # repuestos/pausas del motor (pausada→reanudada).
            abierta = estados_bd["Abierta"].nombre_estado
            en_proceso = estados_bd["En Proceso"].nombre_estado
            esp_rep = estados_bd["Esp. Repuesto"].nombre_estado
            cancelada_n = estados_bd["Cancelada"].nombre_estado
            completada_n = estados_bd["Completada"].nombre_estado
            eventos = [BitacoraOT(orden_trabajo_id=nueva.id, fecha=fechas["fecha_creacion"],
                                  accion="creada", usuario="sistema", estado_anterior=None,
                                  estado_nuevo=abierta,
                                  comentario=f"Dataset demo v2.1 (OT {nueva.id})")]
            if fechas["fecha_asignacion"]:
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=fechas["fecha_asignacion"],
                    accion="asignada", usuario="sistema", estado_anterior=abierta,
                    estado_nuevo=abierta, comentario="Asignación demo v2.1"))
            if fechas["fecha_inicio_trabajo"]:
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=fechas["fecha_inicio_trabajo"],
                    accion="iniciada", usuario="sistema", estado_anterior=abierta,
                    estado_nuevo=en_proceso, comentario="Inicio de trabajo demo v2.1"))
            es_cancelada = ot["estado_actual"] == "Cancelada"
            if ot["sub_estado_logistica"] and fechas["fecha_inicio_trabajo"] and fechas["fecha_resolucion"]:
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=fechas["fecha_inicio_trabajo"],
                    accion="pausada", usuario="sistema", estado_anterior=en_proceso,
                    estado_nuevo=esp_rep,
                    comentario=f"Esp. repuesto/logística ({ot['sub_estado_logistica']}) — demo v2.1"))
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=fechas["fecha_resolucion"],
                    accion="reanudada", usuario="sistema", estado_anterior=esp_rep,
                    estado_nuevo=en_proceso, comentario="Reanudada tras logística — demo v2.1"))
            elif ot["en_pausa_tecnica"] and ot["tiempo_pausa_acumulado"] > 0 and fechas["fecha_resolucion"]:
                desde = fechas["fecha_resolucion"] - timedelta(hours=ot["tiempo_pausa_acumulado"])
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=desde, accion="pausada",
                    usuario="sistema", estado_anterior=en_proceso, estado_nuevo=esp_rep,
                    comentario=f"Pausa técnica ({ot['motivo_pausa']}) — demo v2.1"))
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=fechas["fecha_resolucion"],
                    accion="reanudada", usuario="sistema", estado_anterior=esp_rep,
                    estado_nuevo=en_proceso, comentario="Reanudada tras pausa técnica — demo v2.1"))
            if fechas["fecha_resolucion"]:
                anterior = en_proceso if fechas["fecha_inicio_trabajo"] else abierta
                eventos.append(BitacoraOT(
                    orden_trabajo_id=nueva.id, fecha=fechas["fecha_resolucion"],
                    accion="cancelada" if es_cancelada else "resuelta",
                    usuario="sistema", estado_anterior=anterior,
                    estado_nuevo=cancelada_n if es_cancelada else completada_n,
                    comentario=(f"Cancelada ({motivo or 'n/d'}) — demo v2.1" if es_cancelada
                                else "Resolución demo v2.1")))
            for ev in eventos:
                session.add(ev)
            stats["eventos_bitacora"] += len(eventos)
            stats["ots_importadas"] += 1
        session.commit()

        # ── 5. Síntomas + feedback predictivo (Regla 15, OT 109) ──
        ot109 = session.get(OrdenTrabajo, OT_ID_FEEDBACK)
        if ot109 and not session.exec(select(SintomaOT).where(
                SintomaOT.ot_id == OT_ID_FEEDBACK)).first():
            s1 = SintomaOT(ot_id=OT_ID_FEEDBACK, tipo_origen="Sistema/IA",
                           texto_sintoma="Predicción RUL: degradación de válvula de compresión",
                           prediccion_rul='{"dias_estimados": 7, "confianza": 0.85}',
                           fecha_reporte=ot109.fecha_creacion, usuario_id=None,
                           estado_validacion="Confirmado")
            s2 = SintomaOT(ot_id=OT_ID_FEEDBACK, tipo_origen="Usuario",
                           texto_sintoma="Ruido extraño en compresor", prediccion_rul=None,
                           fecha_reporte=ot109.fecha_creacion, usuario_id=None,
                           estado_validacion="Confirmado")
            session.add(s1)
            session.add(s2)
            session.flush()
            session.add(FeedbackPredictivo(
                ot_id=OT_ID_FEEDBACK, symptom_id=s1.id,
                prediccion_original_ia='{"dias_estimados": 7, "confianza": 0.85, '
                                       '"variables": {"presion": 0.7, "vibracion": 0.6}}',
                resultado_real_tecnico="Confirmada", variables_sensores_snapshot=None))
            session.commit()
            print("[IMPORT] Síntomas (2) + feedback predictivo (1) de la OT 109 insertados")

    print(f"[IMPORT] Equipos: {stats['equipos_creados']} creados / "
          f"{stats['equipos_actualizados']} actualizados · "
          f"OTs: {stats['ots_importadas']} importadas · "
          f"Bitácora: {stats['eventos_bitacora']} eventos")

    # ── 6. Validación automática contra el MOTOR v2.1 real ──
    print("\n[VALIDACIÓN] Ejecutando el motor v2.1 real (_calcular_indicadores_v21)...")
    try:
        from api.routes.reportes import _calcular_indicadores_v21
    except Exception as e:
        print(f"⚠ No se pudo importar el motor ({e}). Revisa los valores manualmente.")
        return True
    with Session(engine) as session:
        resultado = _calcular_indicadores_v21(session, None, None)
    por_equipo = {r["nombre_corto"]: r for r in resultado["por_equipo"]}

    checks = []
    for nombre, esperado in ESPERADO_EQUIPOS.items():
        real = por_equipo.get(nombre)
        if real is None:
            checks.append((f"{nombre}: equipo en reporte", False))
            continue
        for campo, valor_esp in esperado.items():
            valor_real = real.get(campo)
            if valor_esp is None:
                ok = valor_real is None
            else:
                ok = valor_real is not None and abs(float(valor_real) - float(valor_esp)) < 0.051
            checks.append((f"{nombre} → {campo}={valor_esp} (real: {valor_real})", ok))

    print()
    ok_all = True
    for nombre, ok in checks:
        ok_all &= ok
        print(f"    [{'✅' if ok else '❌'}] {nombre}")
    n_ok = sum(1 for _, ok in checks if ok)
    print(f"\n    RESULTADO VALIDACIÓN: {n_ok}/{len(checks)} checks OK — "
          f"{'Motor v2.1 calcula EXACTO lo esperado' if ok_all else 'revisar ❌ (¿otras OTs del mismo equipo en tu BD? usa Limpiar BD)'}")

    # ── Auditoría de bitácora (v2.1.3): los pares pausada→reanudada de la
    #    bitácora alimentan la espera/pausa del motor. Si en el rango demo
    #    quedaran eventos ajenos a ESTA corrida (huérfanos o de otra
    #    generación), aquí se evidencia con el detalle completo. ──
    print("\n[AUDITORÍA BITÁCORA] pares pausada→reanudada de las OTs con espera/pausa:")
    ESPERA_ESPERADA = {105: 267.5, 106: 4.0}
    auditoria_ok = True
    with Session(engine) as session:
        for ot_id, esperado in ESPERA_ESPERADA.items():
            evs = session.exec(select(BitacoraOT).where(
                BitacoraOT.orden_trabajo_id == ot_id).order_by(
                BitacoraOT.fecha.asc(), BitacoraOT.id.asc())).all()
            total, desde = 0.0, None
            for e in evs:
                if e.accion == "pausada":
                    desde = e.fecha
                elif e.accion == "reanudada" and desde is not None:
                    total += (e.fecha - desde).total_seconds() / 3600.0
                    desde = None
            if abs(total - esperado) < 0.005:
                print(f"    [✅] OT {ot_id}: espera/pausa bitácora = {total:.2f} h (esperado {esperado})")
            else:
                auditoria_ok = False
                print(f"    [❌] OT {ot_id}: espera/pausa bitácora = {total:.2f} h ≠ esperado {esperado} "
                      f"→ {len(evs)} eventos detectados:")
                for e in evs:
                    print(f"        id={e.id} {e.fecha} {e.accion:9s} | {(e.comentario or '')[:60]}")
    if auditoria_ok:
        print("    Bitácora limpia: solo eventos de esta corrida en el rango demo.")
    else:
        print("    ⚠ Eventos ajenos detectados. La versión actual del script los purga en la")
        print("      próxima corrida; si el aviso persiste, comparte esta salida completa.")
    return ok_all


# ============================================================
# Banner + main
# ============================================================

def imprimir_banner(dir_salida: Path, chk_bd: dict, ancla: datetime, importado: bool):
    print()
    print("=" * 78)
    print("FÁBRICA DE DATOS DEMO v2.1 — GENERACIÓN COMPLETA")
    print("=" * 78)
    print("Archivos generados:")
    print(f"  ✅ demo_ordenes_trabajo_v21.xlsx (15 OTs con fechas relativas)")
    print(f"  ✅ demo_equipos_v21.xlsx (13 equipos con criticidad)")
    print(f"  ✅ verificacion_esperada_v21.md (reporte de verificación)")
    print(f"Carpeta: {dir_salida}")
    print(f"Ancla temporal: última OT cierra {ancla + timedelta(minutes=SPAN_TOTAL_MIN):%Y-%m-%d %H:%M} "
          f"(1 h antes de la generación); dataset abarca ~15.8 días")
    if chk_bd["estado"] == "ok":
        print(f"Equipos en BD: {len(chk_bd['existentes'])}/13 presentes · "
              f"faltantes: {len(chk_bd['faltantes'])}"
              + (f" → {', '.join(chk_bd['faltantes'])}" if chk_bd["faltantes"] else ""))
        print("  → demo_equipos_v21.xlsx generado igualmente (por si prefieres recrearlos)")
    elif chk_bd["estado"] == "sin_bd":
        print("Equipos en BD: no se encontró cmms_bioai.db junto al script (BD nueva)")
    else:
        print(f"Equipos en BD: no verificado ({chk_bd['estado']})")
    if not importado:
        print("\nPróximos pasos:")
        print("  1. En el CMMS: Configuración → 'Limpiar Base de Datos' (opcional, BD limpia)")
        print("  2. En el CMMS: Configuración → 'Cargar datos TEST'")
        print("  3. Importar demo_equipos_v21.xlsx en Equipos → Importar Excel (SOLO si faltan; si ya existen, no lo importes para no duplicar)")
        print("  4. OTs → 'python generar_demo_v21.py --importar' (el CMMS aún no importa OTs vía Excel)")
        print("  5. Ir a Reportes → MTBF/MTTR")
        print("  6. Comparar con verificacion_esperada_v21.md (mismo día = valores exactos)")
    print("\nReglas v2.1 cubiertas:")
    print("  ✅ Regla 3: Ventana de Garantía 72h (OT 102, reincidencia a 48h)")
    print("  ✅ Regla 4: Falsas Alarmas / Error Usuario (OT 103, 104)")
    print("  ✅ Regla 4+5: Baja de Equipo (OT 110, MDT sí cuenta)")
    print("  ✅ Regla 6: Cierre Administrativo (OT 108)")
    print("  ✅ Reglas 11-14: Pausa por Emergencia (OT 106)")
    print("  ✅ Regla 15: OT Predictiva de IA (OT 109, con síntomas + feedback)")
    print("  ✅ Logística Larga (OT 105, 11 días)")
    print("=" * 78)


def main():
    ap = argparse.ArgumentParser(
        description="Fábrica de Datos Demo v2.1 — genera Excel/CSV de OTs con "
                    "fechas relativas + verificación esperada (+ --importar)")
    ap.add_argument("--importar", action="store_true",
                    help="Importa equipos+OTs en cmms_bioai.db y valida contra el motor v2.1")
    ap.add_argument("--dir", default=None,
                    help="Carpeta de salida (por defecto: junto al script, backend/)")
    args = ap.parse_args()

    dir_salida = Path(args.dir).resolve() if args.dir else BACKEND_DIR
    dir_salida.mkdir(parents=True, exist_ok=True)

    ancla = _ancla()
    hoy = date.today()
    equipos = construir_equipos(hoy)
    ots = construir_ots()

    # Sanidad del diseño temporal (siempre activa: protege el dataset)
    f = {ot["ot_id"]: _fechas_ot(ot, ancla) for ot in ots}
    gap102 = (f[102]["fecha_creacion"] - f[101]["fecha_resolucion"]).total_seconds() / 3600
    mdt105 = (f[105]["fecha_resolucion"] - f[105]["fecha_creacion"]).total_seconds() / 3600
    mdt110 = (f[110]["fecha_resolucion"] - f[110]["fecha_creacion"]).total_seconds() / 3600
    assert abs(gap102 - 48.0) < 1e-6, f"OT 102 debe distar 48 h de la resolución de la OT 101 (hay {gap102})"
    assert abs(mdt105 - 270.0) < 1e-6, f"MDT OT 105 debe ser 270 h (hay {mdt105})"
    assert abs(mdt110 - 99.0) < 1e-6, f"MDT OT 110 debe ser 99 h (hay {mdt110})"

    # 1-2. Excel
    ruta_ots = dir_salida / "demo_ordenes_trabajo_v21.xlsx"
    ruta_eq = dir_salida / "demo_equipos_v21.xlsx"
    generar_excel_ots(ruta_ots, ots, ancla)
    generar_excel_equipos(ruta_eq, equipos)
    # 3. Verificación esperada
    generar_md(dir_salida / "verificacion_esperada_v21.md", ots, ancla, equipos)

    # 4. Estado de equipos en la BD (solo lectura)
    chk_bd = verificar_equipos_bd()

    # 5. Importación + validación (opcional)
    ok_import = True
    if args.importar:
        ok_import = modo_importar(ots, equipos, ancla)

    imprimir_banner(dir_salida, chk_bd, ancla, importado=args.importar)
    return 0 if ok_import else 1


if __name__ == "__main__":
    sys.exit(main())
