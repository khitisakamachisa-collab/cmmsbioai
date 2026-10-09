# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Importador del Dataset de Prueba v2.1
===================================================
Estrategia "Reset Controlado con Seed Enriquecido": importa 15 OTs de prueba
(101-115) que cubren las reglas críticas del flujo v2.1, calcula los relojes
de forma determinista a partir de las fechas, y genera bitácora nativa para
que /reportes/tiempos-etapa funcione sobre el dataset sin cambios de código.

REGLAS DE CÁLCULO (documentadas, deterministas)
-----------------------------------------------
Estados: el CSV usa códigos v2.1 (OPEN, IN_PROGRESS, ...). El mapeo es por
NOMBRE contra el catálogo real (no por ID hardcodeado, porque el spec traía
IDs desplazados respecto al catálogo real del sistema):

    OPEN          → Abierta        (id real 1)
    IN_PROGRESS   → En Proceso     (id real 2)
    WAITING_SPARE → Esp. Repuesto  (id real 3)
    COMPLETED     → Completada     (id real 4)
    CANCELED      → Cancelada      (id real 5)
    MONITORING    → En Monitoreo   (id real 6)

Relojes (alineados a /reportes/tiempos-etapa, que es la fuente viva):
    horas_hasta_asignacion = fecha_asignacion - fecha_creacion
    horas_reaccion         = fecha_inicio_trabajo - fecha_asignacion
    horas_reparacion_brutas= fecha_resolucion - fecha_inicio_trabajo
    MTTA (variante spec)   = fecha_inicio_trabajo - fecha_creacion
                             (= hasta_asignacion + reaccion)
    MDT                    = fecha_resolucion - fecha_creacion
Partición de la ventana de reparación: brutas = activas + pausa + espera.
    - pausa: columna opcional 'tiempo_pausa_acumulado' del CSV; si no viene y
      en_pausa_tecnica=True, se extrae del informe con el patrón "pausó Xh".
    - espera logística: si sub_estado_logistica no es NULL y el CSV no trae
      marcas WAITING_SPARE (no trae), se asume ventana completa - pausa y
      activas = 0 (caso 105). Queda marcado en el reporte.
Regla de exclusión forzada: CANCELED con motivo en
    {Falsa_Alarma, Duplicado, Error_Usuario} → mdt_excluido_disponibilidad=True.

Bitácora: se generan eventos nativos (creada / asignada / iniciada /
pausada / reanudada / resuelta / cancelada) con usuario='sistema', para que
la espera de repuestos y la bitácora exportable funcionen igual que con
datos orgánicos. Convención de anclaje de pausas:
    - logística     → pausada en fecha_inicio_trabajo, reanudada en resolucion
    - pausa técnica → reanudada en resolucion, pausada en resolucion - pausa

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python importar_dataset_v21.py [--csv RUTA] [--reemplazar]

El script corre SIEMPRE contra cmms_bioai.db del directorio backend/.
Sin --reemplazar: si una OT del CSV ya existe, se OMITE (idempotente).
"""

import argparse
import csv
import os
import re
import sys
from datetime import datetime
from itertools import combinations

# ── La BD es relativa al backend/ (database.py usa ruta relativa) ──
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlmodel import Session, select  # noqa: E402
from database import create_db_and_tables, seed_database, engine  # noqa: E402
from models import Equipo, EstadoOT, OrdenTrabajo, BitacoraOT  # noqa: E402
from models.v21 import SintomaOT, FeedbackPredictivo, HitoCicloVida  # noqa: E402

# ============================================================
# Constantes de mapeo
# ============================================================

MAPEO_ESTADOS_V21 = {
    "OPEN": "Abierta",
    "IN_PROGRESS": "En Proceso",
    "WAITING_SPARE": "Esp. Repuesto",
    "COMPLETED": "Completada",
    "CANCELED": "Cancelada",
    "MONITORING": "En Monitoreo",
}

# Motivos de cancelación que EXCLUYEN el MDT de la Disponibilidad (spec v2.1)
MOTIVOS_EXCLUYEN_MDT = {"Falsa_Alarma", "Duplicado", "Error_Usuario"}

OT_ID_FEEDBACK = 109  # OT predictiva con síntomas anexados + feedback


# ============================================================
# Helpers de parsing
# ============================================================

def _limpiar(valor):
    """'' → None; str strip."""
    if valor is None:
        return None
    valor = valor.strip()
    return valor if valor else None


def _parse_bool(valor, defecto=False):
    if valor is None:
        return defecto
    v = str(valor).strip().lower()
    if v in ("true", "1", "si", "sí", "yes", "y", "x"):
        return True
    if v in ("false", "0", "no", "n", ""):
        return False
    raise ValueError(f"Booleano no reconocido: {valor!r}")


def _parse_dt(valor):
    """'2026-10-01 08:00:00' → datetime naive. '' → None."""
    valor = _limpiar(valor)
    if valor is None:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(valor, fmt)
        except ValueError:
            continue
    raise ValueError(f"Fecha no reconocida: {valor!r} (formatos: YYYY-MM-DD [HH:MM:SS])")


def _horas_entre(inicio, fin):
    """Horas decimales entre dos datetimes; None si falta alguno."""
    if inicio is None or fin is None:
        return None
    return round((fin - inicio).total_seconds() / 3600.0, 2)


_PATRON_PAUSA = re.compile(r"paus[óo]\s+(?:por\s+)?(?:~)?(\d+(?:[.,]\d+)?)\s*h", re.IGNORECASE)


def _extraer_pausa_del_informe(texto):
    """Extrae horas de pausa declaradas en el informe ('pausó 4h').
    Heurística documentada SOLO para el dataset de prueba (fallback)."""
    if not texto:
        return None
    m = _PATRON_PAUSA.search(texto)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))


# ============================================================
# Reparación de filas CSV malformadas (comas de más)
# ============================================================
# El dataset de prueba trae filas con comas de más: (a) coma estructural
# extra (fila 103) y (b) comas SIN entrecomillar dentro del texto del
# informe ("...MTTR Hombre = 3h, Calendario = 6.5h."). El reparador prueba
# quitar comas vacías (de derecha a izquierda) y re-une el sobrante en la
# última columna; valida estrictamente antes de aceptar.

_BOOLS_OK = {"true", "false", ""}


def _fila_valida(c, n_header, vocab_motivos):
    """Valida una fila realineada: booleanos, motivo, fecha y estado."""
    if len(c) != n_header:
        return False
    bools_idx = (11, 12, 13, 23, 24, 25)  # ventana, inefec, pausa, cierre, exclMTTR, exclMDT
    if any(c[i].lower() not in _BOOLS_OK for i in bools_idx):
        return False
    if c[22] != "" and c[22] not in vocab_motivos:  # motivo_cancelacion
        return False
    try:
        _parse_dt(c[15])  # fecha_creacion
    except Exception:
        return False
    if c[6].upper() not in MAPEO_ESTADOS_V21:
        return False
    if re.match(r"^(True|False)\b", c[26] or ""):  # texto no debe arrancar como booleano
        return False
    return True


def _reparar_fila(campos, n_header, vocab_motivos):
    """Devuelve la fila reparada (27 campos) o None si no logra validarla.
    Estrategia: quitar s vacíos (derecha→izquierda) + re-uniir el sobrante
    en la última columna (texto del informe)."""
    extras = len(campos) - n_header
    if extras <= 0:
        return None
    vacios = [i for i in range(11, min(23, len(campos))) if campos[i] == ""]
    vacios_desc = sorted(vacios, reverse=True)
    for s in range(0, extras + 1):
        if s > len(vacios_desc):
            break
        for quitar in combinations(vacios_desc, s):
            quitar_set = set(quitar)
            nueva = [c for i, c in enumerate(campos) if i not in quitar_set]
            if len(nueva) < n_header:
                continue
            if len(nueva) > n_header:  # re-uniir sobrante en la última columna
                nueva = nueva[:n_header - 1] + [", ".join(x.strip() for x in nueva[n_header - 1:])]
            if _fila_valida(nueva, n_header, vocab_motivos):
                return nueva
    return None


# ============================================================
# Resolución de catálogos (por NOMBRE, no por ID)
# ============================================================

def resolver_estados_sistema(session):
    """Mapa nombre_estado → EstadoOT (catálogo real de la BD)."""
    return {e.nombre_estado: e for e in session.exec(select(EstadoOT)).all()}


def resolver_equipo(session, nombre, tipo_equipo, cache, creados):
    """Upsert de equipo por nombre_corto. Los 13 equipos del dataset pueden
    no existir: 'Seed Enriquecido' los crea con datos mínimos N/D.
    Devuelve (equipo, fue_creado_ahora)."""
    if nombre in cache:
        return cache[nombre], False
    equipo = session.exec(select(Equipo).where(Equipo.nombre_corto == nombre)).first()
    fue_creado = False
    if equipo is None:
        serie = "V21-" + re.sub(r"[^A-Za-z0-9]+", "", nombre).upper()[:40]
        equipo = Equipo(
            nombre_corto=nombre,
            modelo="N/D",
            numero_serie=serie,
            marca="N/D",
            tipo_equipo=tipo_equipo or "Otro",
            criticidad="Media",
            estado_id=1,  # Operativo (seed id=1)
        )
        session.add(equipo)
        session.flush()  # asigna id sin commit (FKs posteriores)
        creados.append(nombre)
        fue_creado = True
    cache[nombre] = equipo
    return equipo, fue_creado


# ============================================================
# Construcción de la OT + bitácora
# ============================================================

def construir_ot(fila, equipo_id, estado_id, fuentes):
    """Convierte una fila del CSV en OrdenTrabajo (+ lista de notas).
    fuente_pausa indica de dónde salió tiempo_pausa_acumulado."""
    fechas = {k: _parse_dt(fila.get(k)) for k in
              ("fecha_creacion", "fecha_asignacion", "fecha_inicio_trabajo", "fecha_resolucion")}

    en_pausa = _parse_bool(fila.get("en_pausa_tecnica"))
    # --- tiempo_pausa_acumulado: columna explícita > informe (si en_pausa) > 0.0 ---
    pausa_csv = _limpiar(fila.get("tiempo_pausa_acumulado"))
    if pausa_csv is not None:
        pausa_h = float(pausa_csv.replace(",", "."))
        fuente_pausa = "columna CSV"
    elif en_pausa:
        pausa_h = _extraer_pausa_del_informe(fila.get("texto_libre_informe") or "")
        fuente_pausa = "extraída del informe (patrón 'pausó Xh')" if pausa_h is not None else "no declarada → 0.0"
        pausa_h = pausa_h or 0.0
    else:
        pausa_h = 0.0
        fuente_pausa = "sin pausa"

    estado_v21 = fila["estado_actual"].strip().upper()
    cancelada = estado_v21 == "CANCELED"
    completada = estado_v21 == "COMPLETED"

    # Regla forzada de exclusión de MDT (spec PASO 3.3)
    motivo = _limpiar(fila.get("motivo_cancelacion"))
    mdt_excluido = _parse_bool(fila.get("mdt_excluido_disponibilidad"))
    if cancelada and motivo in MOTIVOS_EXCLUYEN_MDT and not mdt_excluido:
        mdt_excluido = True
        fuentes.append(f"OT {fila['ot_id']}: mdt_excluido_disponibilidad forzado a True "
                       f"(regla v2.1: cancelada por {motivo})")

    parent_id = _limpiar(fila.get("parent_ot_id"))
    seq = _limpiar(fila.get("failure_sequence"))

    ot = OrdenTrabajo(
        id=int(fila["ot_id"]),
        equipo_id=equipo_id,
        estado_id=estado_id,
        prioridad=(fila.get("prioridad") or "Media").strip(),
        fecha_creacion=fechas["fecha_creacion"],
        fecha_asignacion=fechas["fecha_asignacion"],
        fecha_inicio_trabajo=fechas["fecha_inicio_trabajo"],
        fecha_resolucion=fechas["fecha_resolucion"],
        titulo=fila["titulo"].strip(),
        # texto_libre_informe → descripcion_falla (narrativa rica para PLN);
        # accion_tomada (CSV) → acciones_realizadas (qué se hizo, semántica exacta)
        descripcion_falla=fila["texto_libre_informe"].strip(),
        acciones_realizadas=_limpiar(fila.get("accion_tomada")),
        parent_ot_id=int(parent_id) if parent_id else None,
        failure_sequence=int(seq) if seq else 1,
        # --- 15 campos v2.1 ---
        tipo_origen_ot=fila.get("tipo_origen_ot", "Usuario").strip() or "Usuario",
        tipo_impacto=fila.get("tipo_impacto", "REAL").strip() or "REAL",
        sub_estado_logistica=_limpiar(fila.get("sub_estado_logistica")),
        ventana_garantia_reparacion=_parse_bool(fila.get("ventana_garantia")),
        es_reparacion_inefectiva=_parse_bool(fila.get("es_reparacion_inefectiva")),
        en_pausa_tecnica=en_pausa,
        motivo_pausa=_limpiar(fila.get("motivo_pausa")),
        tiempo_pausa_acumulado=pausa_h,
        cierre_administrativo=_parse_bool(fila.get("cierre_administrativo")),
        excluida_de_MTTR=_parse_bool(fila.get("excluida_de_MTTR")),
        mdt_excluido_disponibilidad=mdt_excluido,
        codigo_falla=_limpiar(fila.get("codigo_falla")),
        causa_raiz=_limpiar(fila.get("causa_raiz")),
        accion_tomada=_limpiar(fila.get("accion_tomada")),
        motivo_cancelacion=motivo,
    )
    return ot, fechas, pausa_h, fuente_pausa, cancelada, completada


def generar_bitacora(ot, fechas, pausa_h, logistica, nombres_estados, sub_estado):
    """Eventos nativos espejo del flujo real (R4), para que reportes/bitácora
    funcionen sobre el dataset. Nombres de estado reales del catálogo."""
    abierta = nombres_estados["Abierta"].nombre_estado
    en_proceso = nombres_estados["En Proceso"].nombre_estado
    esp_repuesto = nombres_estados["Esp. Repuesto"].nombre_estado
    cancelada_nombre = nombres_estados["Cancelada"].nombre_estado
    completada_nombre = nombres_estados["Completada"].nombre_estado
    usr = "sistema"
    eventos = [
        BitacoraOT(orden_trabajo_id=ot.id, fecha=fechas["fecha_creacion"], accion="creada",
                   usuario=usr, estado_anterior=None, estado_nuevo=abierta,
                   comentario=f"Import dataset v2.1 (ot_id {ot.id})"),
    ]
    if fechas["fecha_asignacion"]:
        eventos.append(BitacoraOT(orden_trabajo_id=ot.id, fecha=fechas["fecha_asignacion"],
                                  accion="asignada", usuario=usr, estado_anterior=abierta,
                                  estado_nuevo=abierta, comentario="Asignación importada (dataset v2.1)"))
    if fechas["fecha_inicio_trabajo"]:
        eventos.append(BitacoraOT(orden_trabajo_id=ot.id, fecha=fechas["fecha_inicio_trabajo"],
                                  accion="iniciada", usuario=usr, estado_anterior=abierta,
                                  estado_nuevo=en_proceso, comentario="Inicio de trabajo importado"))
    if logistica and fechas["fecha_inicio_trabajo"] and fechas["fecha_resolucion"]:
        eventos.append(BitacoraOT(orden_trabajo_id=ot.id, fecha=fechas["fecha_inicio_trabajo"],
                                  accion="pausada", usuario=usr, estado_anterior=en_proceso,
                                  estado_nuevo=esp_repuesto,
                                  comentario=f"Esp. repuesto/logística ({sub_estado}) — import v2.1"))
        eventos.append(BitacoraOT(orden_trabajo_id=ot.id, fecha=fechas["fecha_resolucion"],
                                  accion="reanudada", usuario=usr, estado_anterior=esp_repuesto,
                                  estado_nuevo=en_proceso, comentario="Reanudada tras logística — import v2.1"))
    elif ot.en_pausa_tecnica and pausa_h > 0 and fechas["fecha_resolucion"]:
        desde = datetime.fromtimestamp(fechas["fecha_resolucion"].timestamp() - pausa_h * 3600)
        eventos.append(BitacoraOT(orden_trabajo_id=ot.id, fecha=desde, accion="pausada",
                                  usuario=usr, estado_anterior=en_proceso, estado_nuevo=esp_repuesto,
                                  comentario=f"Pausa técnica ({ot.motivo_pausa}) — import v2.1"))
        eventos.append(BitacoraOT(orden_trabajo_id=ot.id, fecha=fechas["fecha_resolucion"],
                                  accion="reanudada", usuario=usr, estado_anterior=esp_repuesto,
                                  estado_nuevo=en_proceso, comentario="Reanudada tras pausa técnica — import v2.1"))
    es_cancelada = ot.estado_id == nombres_estados["Cancelada"].id
    if fechas["fecha_resolucion"]:
        if es_cancelada:
            eventos.append(BitacoraOT(
                orden_trabajo_id=ot.id, fecha=fechas["fecha_resolucion"], accion="cancelada",
                usuario=usr, estado_anterior=en_proceso, estado_nuevo=cancelada_nombre,
                comentario=f"Cancelada ({ot.motivo_cancelacion or 'n/d'}) — import v2.1"))
        else:
            eventos.append(BitacoraOT(
                orden_trabajo_id=ot.id, fecha=fechas["fecha_resolucion"], accion="resuelta",
                usuario=usr, estado_anterior=en_proceso, estado_nuevo=completada_nombre,
                comentario="Resolución importada (dataset v2.1)"))
    elif es_cancelada:
        # 103: cancelada sin fecha de resolución → se usa la última marca conocida
        fin = fechas["fecha_inicio_trabajo"] or fechas["fecha_asignacion"] or fechas["fecha_creacion"]
        eventos.append(BitacoraOT(
            orden_trabajo_id=ot.id, fecha=fin, accion="cancelada",
            usuario=usr, estado_anterior=abierta, estado_nuevo=cancelada_nombre,
            comentario=f"Cancelada sin resolución ({ot.motivo_cancelacion or 'n/d'}) — import v2.1"))
    return eventos


# ============================================================
# Relojes (alineados a /reportes/tiempos-etapa)
# ============================================================

def calcular_relojes(ot, fechas, pausa_h, logistica):
    h_asig = _horas_entre(fechas["fecha_creacion"], fechas["fecha_asignacion"])
    h_reac = _horas_entre(fechas["fecha_asignacion"], fechas["fecha_inicio_trabajo"])
    h_rep = _horas_entre(fechas["fecha_inicio_trabajo"], fechas["fecha_resolucion"])
    mtta_spec = _horas_entre(fechas["fecha_creacion"], fechas["fecha_inicio_trabajo"])
    mdt = _horas_entre(fechas["fecha_creacion"], fechas["fecha_resolucion"])
    if h_rep is None:
        h_espera, h_activa = None, None
    elif logistica:
        # Sin marcas WAITING_SPARE en el CSV: ventana completa − pausa = logística,
        # trabajo activo desconocido → 0.0 (queda marcado en el reporte).
        h_espera = round(max(h_rep - pausa_h, 0.0), 2)
        h_activa = 0.0
    else:
        h_espera = 0.0
        h_activa = round(max(h_rep - pausa_h, 0.0), 2)
    return {
        "ot_id": ot.id, "estado": None, "equipo": None,
        "h_asig": h_asig, "h_reac": h_reac, "mtta_spec": mtta_spec,
        "h_rep": h_rep, "pausa": pausa_h if h_rep is not None else None,
        "h_espera": h_espera, "h_activa": h_activa, "mdt": mdt,
        "ot": ot,
    }


# ============================================================
# Síntomas + feedback predictivo (OT 109)
# ============================================================

def relojes_desde_bd(ot):
    """Recalcula los relojes desde una OT cargada de BD (para checks e
    idempotencia: funciona igual en primera importación y re-corridas)."""
    fechas = {"fecha_creacion": ot.fecha_creacion, "fecha_asignacion": ot.fecha_asignacion,
              "fecha_inicio_trabajo": ot.fecha_inicio_trabajo, "fecha_resolucion": ot.fecha_resolucion}
    return calcular_relojes(ot, fechas, ot.tiempo_pausa_acumulado or 0.0,
                            bool(ot.sub_estado_logistica))


def insertar_sintomas_feedback(session, ot109):
    """2 síntomas + 1 feedback según spec PASO 3.5/3.6. Idempotente."""
    ya = session.exec(select(SintomaOT).where(SintomaOT.ot_id == OT_ID_FEEDBACK)).all()
    if ya:
        n_fb = len(session.exec(
            select(FeedbackPredictivo).where(FeedbackPredictivo.ot_id == OT_ID_FEEDBACK)).all())
        return len(ya), n_fb, False
    s1 = SintomaOT(
        ot_id=OT_ID_FEEDBACK, tipo_origen="Sistema/IA",
        texto_sintoma="Predicción RUL: degradación de válvula de compresión",
        prediccion_rul='{"dias_estimados": 7, "confianza": 0.85}',
        fecha_reporte=ot109.fecha_creacion, usuario_id=None, estado_validacion="Confirmado",
    )
    s2 = SintomaOT(
        ot_id=OT_ID_FEEDBACK, tipo_origen="Usuario",
        texto_sintoma="Ruido extraño en compresor",
        prediccion_rul=None,
        fecha_reporte=ot109.fecha_creacion, usuario_id=None, estado_validacion="Confirmado",
    )
    session.add(s1)
    session.add(s2)
    session.flush()
    fb = FeedbackPredictivo(
        ot_id=OT_ID_FEEDBACK, symptom_id=s1.id,
        prediccion_original_ia='{"dias_estimados": 7, "confianza": 0.85, "variables": {"presion": 0.7, "vibracion": 0.6}}',
        resultado_real_tecnico="Confirmada",
        variables_sensores_snapshot=None,
    )
    session.add(fb)
    session.commit()
    return 2, 1, True


# ============================================================
# Reporte de validación
# ============================================================

def _fmt(h):
    return "—" if h is None else f"{h:.2f}"


def _flags(ot):
    f = []
    if ot.tipo_origen_ot == "Sistema/IA":
        f.append("IA")
    if ot.tipo_origen_ot == "Programado":
        f.append("PROG")
    if ot.tipo_impacto == "PRECAUTORIO":
        f.append("PRECAU")
    if ot.sub_estado_logistica:
        f.append("LOG")
    if ot.en_pausa_tecnica:
        f.append("PAUSA")
    if ot.ventana_garantia_reparacion:
        f.append("GAR<72h")
    if ot.es_reparacion_inefectiva:
        f.append("INEFEC")
    if ot.cierre_administrativo:
        f.append("ADMIN")
    if ot.excluida_de_MTTR:
        f.append("EXCL-MTTR")
    if ot.mdt_excluido_disponibilidad:
        f.append("EXCL-MDT")
    return ",".join(f) or "—"


def imprimir_reporte(filas, stats, discrepancias, fuentes, estados_usados, checks):
    L = []
    a = L.append
    a("")
    a("=" * 78)
    a("REPORTE DE VALIDACIÓN — IMPORTACIÓN DATASET DE PRUEBA v2.1")
    a("=" * 78)
    a("[1] RESUMEN")
    for k, v in stats.items():
        if k.startswith("_"):
            continue
        a(f"    {k:<42} {v}")
    a("")
    a("[2] MAPEO DE ESTADOS v2.1 → CATÁLOGO REAL (por nombre, no por ID)")
    for code, (nombre, eid) in estados_usados.items():
        a(f"    {code:<14} → {nombre:<14} (id={eid})")
    a("")
    a("[3] RELOJES POR OT (horas — alineados a /reportes/tiempos-etapa)")
    a("    " + f"{'OT':<5}{'EST':<6}{'asig':>7}{'reacc':>7}{'MTTA*':>7}{'brutas':>8}{'pausa':>7}{'espera':>8}{'activas':>8}{'MDT':>8}  {'FLAGS'}")
    a("    " + "-" * 84)
    for r in filas:
        a("    " + f"{r['ot_id']:<5}{r['estado']:<6}{_fmt(r['h_asig']):>7}{_fmt(r['h_reac']):>7}"
             f"{_fmt(r['mtta_spec']):>7}{_fmt(r['h_rep']):>8}{_fmt(r['pausa']):>7}"
             f"{_fmt(r['h_espera']):>8}{_fmt(r['h_activa']):>8}{_fmt(r['mdt']):>8}  {r.get('flags', '—')}")
    a("    " + "-" * 84)
    a("    EST: CPL=Completada CAN=Cancelada | MTTA* = variante del spec")
    a("         (creación→inicio; = asig + reacc). asig/reacc = semántica del reporte vivo.")
    if not filas:
        a("    (Ninguna fila importada en esta corrida — todas ya existían; usa --reemplazar)")
    a("")
    a("[4] REGLAS v2.1 APLICADAS")
    for f in fuentes:
        a(f"    • {f}")
    a("")
    a("[5] DISCREPANCIAS DETECTADAS (no bloquean la importación)")
    for d in discrepancias:
        a(f"    ⚠ {d}")
    a("")
    a("[6] AGREGADOS DEL DATASET (horas)")
    for k, v in stats.get("_agregados", []):
        a(f"    {k:<58} {v}")
    a("")
    a("[7] CRITERIOS DE ÉXITO")
    ok_all = True
    for nombre, ok in checks:
        ok_all &= ok
        a(f"    [{'✅' if ok else '❌'}] {nombre}")
    a("=" * 78)
    a(f"RESULTADO FINAL: {'OK ✓ — dataset v2.1 importado y validado' if ok_all else 'FALLO ✗ — revisar checks ❌'}")
    a("=" * 78)
    print("\n".join(L))
    return ok_all


# ============================================================
# Main
# ============================================================

def main():
    ap = argparse.ArgumentParser(description="Importa dataset_prueba_v21.csv (15 OTs) al CMMS.")
    ap.add_argument("--csv", default=None, help="Ruta al CSV (por defecto: junto al script o ../)")
    ap.add_argument("--reemplazar", action="store_true",
                    help="Borra las OTs del CSV que ya existan (con bitácora/síntomas/feedback) y reimporta")
    args = ap.parse_args()

    candidatos = []
    if args.csv:
        candidatos.append(args.csv)
    candidatos += ["dataset_prueba_v21.csv", os.path.join("..", "dataset_prueba_v21.csv")]
    ruta_csv = next((c for c in candidatos if c and os.path.exists(c)), None)
    if ruta_csv is None:
        print("❌ No se encontró dataset_prueba_v21.csv. Usa: python importar_dataset_v21.py --csv RUTA")
        return 1

    print(f"=== Importador Dataset v2.1 — CSV: {ruta_csv} ===")
    create_db_and_tables()
    seed_database()

    discrepancias, fuentes = [], []

    with open(ruta_csv, newline="", encoding="utf-8-sig") as f:
        lector = list(csv.reader(f))
    if not lector:
        print("❌ CSV vacío.")
        return 1
    header = [h.strip() for h in lector[0]]
    vocab_motivos = {"Falsa_Alarma", "Duplicado", "Error_Usuario",
                     "Baja_Equipo", "No_Reparable", "Riesgo_Aceptado"}
    filas_csv, reparadas = [], []
    for n_raw, campos in enumerate(lector[1:], start=2):
        if not campos or all(c.strip() == "" for c in campos):
            continue
        campos = [c.strip() for c in campos]
        extras = len(campos) - len(header)
        if extras > 0:
            campos2 = _reparar_fila(campos, len(header), vocab_motivos)
            if campos2 is None:
                print(f"❌ Fila {n_raw} (OT {campos[0]}): {extras} campo(s) de más y no se pudo reparar.")
                print(f"   Contenido: {campos}")
                return 1
            reparadas.append((int(campos[0]), extras))
            campos = campos2
        elif extras < 0:
            print(f"❌ Fila {n_raw} (OT {campos[0]}): faltan {-extras} campo(s).")
            return 1
        filas_csv.append(dict(zip(header, campos)))
    for oid_rep, extras in reparadas:
        discrepancias.append(
            f"OT {oid_rep}: fila del CSV con {extras} campo(s) de más (coma extra / comas sin "
            f"entrecomillar en el texto del informe) — reparada automáticamente. Corregir el CSV fuente.")
    if not filas_csv:
        print("❌ CSV sin filas de datos.")
        return 1
    requeridas = {"ot_id", "equipo", "tipo_equipo", "titulo", "estado_actual", "fecha_creacion",
                  "fecha_asignacion", "fecha_inicio_trabajo", "fecha_resolucion", "texto_libre_informe"}
    faltan = requeridas - set(filas_csv[0].keys())
    if faltan:
        print(f"❌ CSV sin columnas obligatorias: {sorted(faltan)}")
        return 1
    filas_csv.sort(key=lambda r: int(r["ot_id"]))

    stats = {"OTs en CSV": len(filas_csv), "Importadas": 0, "Omitidas (ya existían)": 0,
             "Equipos creados (seed enriquecido)": 0, "Equipos reutilizados": 0,
             "Síntomas insertados (OT 109)": 0, "Feedback insertado (OT 109)": 0,
             "Bitácora generada (eventos)": 0}

    with Session(engine) as session:
        nombres_estados = resolver_estados_sistema(session)
        faltan_estados = {n for n in MAPEO_ESTADOS_V21.values()} - set(nombres_estados)
        if faltan_estados:
            print(f"❌ El catálogo no tiene los estados: {sorted(faltan_estados)}. Corre el backend una vez (seed).")
            return 1

        ids_csv = [int(r["ot_id"]) for r in filas_csv]
        existentes = [oid for oid in ids_csv
                      if session.exec(select(OrdenTrabajo).where(OrdenTrabajo.id == oid)).first()]

        if existentes and not args.reemplazar:
            print(f"⚠ {len(existentes)} OTs ya existen ({existentes}). Se OMiten. Usa --reemplazar para reimportar.")
        if existentes and args.reemplazar:
            for oid in sorted(existentes, reverse=True):
                for ent in session.exec(select(BitacoraOT).where(BitacoraOT.orden_trabajo_id == oid)).all():
                    session.delete(ent)
                for fb in session.exec(select(FeedbackPredictivo).where(FeedbackPredictivo.ot_id == oid)).all():
                    session.delete(fb)
                for sy in session.exec(select(SintomaOT).where(SintomaOT.ot_id == oid)).all():
                    session.delete(sy)
                ot_del = session.get(OrdenTrabajo, oid)
                session.delete(ot_del)
            session.commit()
            print(f"🔄 --reemplazar: {len(existentes)} OTs borradas con sus hijos. Reimportando...")

        cache_equipos, creados = {}, []
        filas, mapa_usado = [], {}
        for fila in filas_csv:
            oid = int(fila["ot_id"])
            if oid in existentes and not args.reemplazar:
                stats["Omitidas (ya existían)"] += 1
                continue
            code = fila["estado_actual"].strip().upper()
            if code not in MAPEO_ESTADOS_V21:
                print(f"❌ OT {oid}: estado '{code}' no reconocido. Válidos: {sorted(MAPEO_ESTADOS_V21)}")
                return 1
            nombre_estado = MAPEO_ESTADOS_V21[code]
            estado = nombres_estados[nombre_estado]
            mapa_usado[code] = (nombre_estado, estado.id)

            equipo, fue_creado = resolver_equipo(session, fila["equipo"].strip(), fila.get("tipo_equipo"), cache_equipos, creados)
            if fue_creado:
                if fila["equipo"].strip() not in stats.get("_equipos_creados_nombres", set()):
                    stats["Equipos creados (seed enriquecido)"] += 1
                    stats.setdefault("_equipos_creados_nombres", set()).add(fila["equipo"].strip())
            else:
                stats["Equipos reutilizados"] += 1

            ot, fechas, pausa_h, fuente_pausa, cancelada, completada = construir_ot(
                fila, equipo.id, estado.id, fuentes)
            if fuente_pausa.startswith("extraída"):
                fuentes.append(f"OT {oid}: tiempo_pausa_acumulado={pausa_h}h {fuente_pausa}")
            session.add(ot)
            eventos = generar_bitacora(ot, fechas, pausa_h, bool(ot.sub_estado_logistica),
                                       nombres_estados, ot.sub_estado_logistica)
            for ev in eventos:
                session.add(ev)
            stats["Bitácora generada (eventos)"] += len(eventos)

            r = calcular_relojes(ot, fechas, pausa_h, bool(ot.sub_estado_logistica))
            r["estado"] = "CPL" if completada else ("CAN" if cancelada else code[:3])
            r["equipo"] = equipo.nombre_corto
            r["flags"] = _flags(ot)  # precalculado DENTRO de sesión (evita DetachedInstance)
            filas.append(r)
            stats["Importadas"] += 1

        # Verificación de regla ventana_garantia (<72h) en reincidencias del dataset
        por_id = {r["ot_id"]: r for r in filas}
        for r in filas:
            ot = r["ot"]
            if ot.ventana_garantia_reparacion and ot.parent_ot_id in por_id:
                madre = por_id[ot.parent_ot_id]["ot"]
                if madre.fecha_resolucion and ot.fecha_creacion:
                    gap = (ot.fecha_creacion - madre.fecha_resolucion).total_seconds() / 3600.0
                    fuentes.append(f"OT {ot.id}: ventana_garantia=True verificada — reincidencia a "
                                   f"{gap:.1f}h de la OT {madre.id} (<72h)")
                    if gap >= 72:
                        discrepancias.append(
                            f"OT {ot.id}: ventana_garantia=True pero la reincidencia ocurrió a {gap:.1f}h (>=72h)")

        session.commit()

        # Síntomas + feedback (OT 109)
        ot109 = session.get(OrdenTrabajo, OT_ID_FEEDBACK)
        if ot109:
            n_s, n_fb, nuevo = insertar_sintomas_feedback(session, ot109)
            if nuevo:
                stats["Síntomas insertados (OT 109)"] = n_s
                stats["Feedback insertado (OT 109)"] = n_fb
            else:
                fuentes.append(f"OT {OT_ID_FEEDBACK}: síntomas/feedback ya existían — no duplicados")
                stats["Síntomas insertados (OT 109)"] = n_s
                stats["Feedback insertado (OT 109)"] = n_fb
        else:
            discrepancias.append(f"OT {OT_ID_FEEDBACK} no existe — síntomas/feedback NO insertados")

        # === Discrepancias analíticas sobre lo importado ===
        r106 = por_id.get(106)
        if r106 and r106["ot"].en_pausa_tecnica and r106["h_activa"] is not None:
            if "3h" in (r106["ot"].descripcion_falla or "") and abs(r106["h_activa"] - 3.0) > 0.01:
                discrepancias.append(
                    f"OT 106: el informe declara 'MTTR Hombre = 3h' pero las activas calculadas son "
                    f"{r106['h_activa']}h (brutas 6.5h − pausa declarada 4.0h). La pausa implícita por 3h sería 3.5h. "
                    f"Corregir CSV (pausa 3.5h) o aceptar 2.5h.")
        r110 = por_id.get(110)
        if r110 and not r110["ot"].excluida_de_MTTR and "MTTR excluido" in (r110["ot"].descripcion_falla or ""):
            discrepancias.append(
                f"OT 110: CSV dice excluida_de_MTTR=False pero su informe declara 'MTTR excluido'. "
                f"Se importó FIEL AL CSV; corregir la columna en el CSV si el informe manda.")
        r105 = por_id.get(105)
        if r105 and r105["ot"].sub_estado_logistica:
            discrepancias.append(
                f"OT 105: el CSV no trae marcas de entrada/salida de WAITING_SPARE → se asumió ventana "
                f"completa = logística ({r105['h_espera']}h ≈ '11 días' del informe) con activas=0.0. "
                f"Si quieres el split fino, agrega columnas espera_inicio/espera_fin al CSV.")
        discrepancias.append(
            "Spec vs sistema: (a) IDs de estado del spec estaban desplazados (decía COMPLETED→5 / "
            "CANCELED→6; el catálogo real es Completada=4 / Cancelada=5) → se mapeó POR NOMBRE; "
            "(b) los campos horas_* NO son columnas de la BD: son métricas que calcula "
            "/reportes/tiempos-etapa desde las fechas — fuente de verdad = sellos de tiempo R5.")

        # === Agregados ===
        comp = [r for r in filas if r["estado"] == "CPL"]
        with_data = [r for r in comp if r["h_rep"] is not None]
        agregados = []
        if with_data:
            mttr_b = round(sum(r["h_rep"] for r in with_data) / len(with_data), 2)
            agregados.append((f"MTTR brutas prom ({len(with_data)} completadas)", f"{mttr_b} h"))
            no_excl = [r for r in with_data if not r["ot"].excluida_de_MTTR]
            excl = [r for r in with_data if r["ot"].excluida_de_MTTR]
            if no_excl:
                mttr_a = round(sum(r["h_activa"] for r in no_excl) / len(no_excl), 2)
                agregados.append((f"MTTR activas prom ({len(no_excl)} completadas, "
                                  f"{len(excl)} excluidas v2.1)", f"{mttr_a} h"))
        mdt_cuenta = [r for r in filas if r["mdt"] is not None and not r["ot"].mdt_excluido_disponibilidad]
        mdt_excl = [r for r in filas if r["mdt"] is not None and r["ot"].mdt_excluido_disponibilidad]
        if mdt_cuenta:
            agregados.append((f"MDT suma a Disponibilidad ({len(mdt_cuenta)} OTs)",
                              f"{round(sum(r['mdt'] for r in mdt_cuenta), 2)} h"))
        if mdt_excl:
            agregados.append((f"MDT EXCLUIDO de Disponibilidad ({len(mdt_excl)} OTs)",
                              f"{round(sum(r['mdt'] for r in mdt_excl), 2)} h"))
        stats["_agregados"] = agregados

    # === Checklist de criterios de éxito (todo recalculado desde BD) ===
    import sqlite3
    con = sqlite3.connect("cmms_bioai.db")
    cols = {row[1] for row in con.execute("PRAGMA table_info(ordentrabajo)")}
    n_tablas = {t for (t,) in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    con.close()

    db_flags, db_relojes = {}, {}
    with Session(engine) as s2:
        ids_csv = [int(r["ot_id"]) for r in filas_csv]
        n_ots = len(s2.exec(select(OrdenTrabajo).where(OrdenTrabajo.id.in_(ids_csv))).all())
        n_sym = len(s2.exec(select(SintomaOT).where(SintomaOT.ot_id == OT_ID_FEEDBACK)).all())
        n_fb = len(s2.exec(select(FeedbackPredictivo).where(FeedbackPredictivo.ot_id == OT_ID_FEEDBACK)).all())
        n_bit = len(s2.exec(select(BitacoraOT).where(BitacoraOT.orden_trabajo_id.in_(ids_csv))).all())
        for oid in (103, 104, 105, 106, 108, 110):
            ot_db = s2.get(OrdenTrabajo, oid)
            if ot_db:
                db_flags[oid] = {"excl_mttr": ot_db.excluida_de_MTTR,
                                 "excl_mdt": ot_db.mdt_excluido_disponibilidad,
                                 "admin": ot_db.cierre_administrativo}
                db_relojes[oid] = relojes_desde_bd(ot_db)
    r105, r106, r110 = db_relojes.get(105), db_relojes.get(106), db_relojes.get(110)
    nuevas_cols = {"tipo_origen_ot", "tipo_impacto", "sub_estado_logistica", "ventana_garantia_reparacion",
                   "es_reparacion_inefectiva", "en_pausa_tecnica", "motivo_pausa", "tiempo_pausa_acumulado",
                   "cierre_administrativo", "excluida_de_MTTR", "mdt_excluido_disponibilidad",
                   "codigo_falla", "causa_raiz", "accion_tomada", "motivo_cancelacion"}
    checks = [
        ("15 campos nuevos presentes en tabla ordentrabajo", nuevas_cols.issubset(cols)),
        ("3 tablas nuevas creadas (symptoms, feedback_predictivo, hitos_ciclo_vida)",
         {"symptoms", "feedback_predictivo", "hitos_ciclo_vida"}.issubset(n_tablas)),
        (f"OTs del CSV en BD: {n_ots}/{len(filas_csv)}", n_ots == len(filas_csv)),
        (f"Síntomas OT 109 insertados: {n_sym}/2", n_sym == 2),
        (f"Feedback predictivo OT 109: {n_fb}/1", n_fb == 1),
        ("Relojes calculados (105 logística=267.5h, 106 activas=2.5h, 110 MDT=99.0h)",
         bool(r105 and abs((r105["h_espera"] or 0) - 267.5) < 0.01
              and r106 and abs((r106["h_activa"] or 0) - 2.5) < 0.01
              and r110 and abs((r110["mdt"] or 0) - 99.0) < 0.01)),
        ("Exclusiones v2.1: 103/104 EXCL-MDT, 108 EXCL-MTTR+ADMIN",
         bool(db_flags.get(103, {}).get("excl_mdt") and db_flags.get(104, {}).get("excl_mdt")
              and db_flags.get(108, {}).get("excl_mttr") and db_flags.get(108, {}).get("admin"))),
        ("Bitácora nativa en BD (espera repuestos computable por /reportes)", n_bit > 0),
    ]
    stats["OTs en BD tras import"] = f"{n_ots}/{len(filas_csv)}"
    stats["Bitácora en BD (eventos del dataset)"] = n_bit
    return 0 if imprimir_reporte(filas, stats, discrepancias, fuentes, mapa_usado, checks) else 1


if __name__ == "__main__":
    sys.exit(main())
