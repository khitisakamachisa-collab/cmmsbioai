from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func
from typing import Optional
from datetime import datetime, date, time, timedelta
from database import get_session
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo, EstadoOT, BitacoraOT
from models.repuestos import Repuesto, OtRepuestoUtilizado
from models.preventivo import TareaPreventiva
from models.historial import EventoHistorial
from models.estados import EstadoEquipo
from models.users import Usuario

router = APIRouter(prefix="/reportes", tags=["Reportes"])


# --- 1. Resumen general de mantenimiento por equipo ---
@router.get("/mantenimiento-por-equipo")
def reporte_mantenimiento_por_equipo(
    fecha_desde: Optional[date] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    """
    Retorna un resumen de mantenimiento por cada equipo:
    - Total de eventos (preventivos, correctivos, calibraciones, otros)
    - Tiempo total invertido
    - Costo total
    - Última fecha de mantenimiento
    """
    # Consultar eventos con filtros de fecha
    query = select(EventoHistorial)
    if fecha_desde:
        query = query.where(func.date(EventoHistorial.fecha_evento) >= fecha_desde)
    if fecha_hasta:
        query = query.where(func.date(EventoHistorial.fecha_evento) <= fecha_hasta)

    eventos = session.exec(query).all()

    # Mapear equipos
    equipos_map = {e.id: (e.nombre_corto or "N/A", e.modelo) for e in session.exec(select(Equipo)).all()}

    # Agrupar por equipo en Python
    por_equipo = {}
    for ev in eventos:
        if ev.equipo_id not in por_equipo:
            eq_nombre, eq_modelo = equipos_map.get(ev.equipo_id, ("Desconocido", "N/A"))
            por_equipo[ev.equipo_id] = {
                "equipo_id": ev.equipo_id,
                "equipo_nombre": eq_nombre,
                "equipo_modelo": eq_modelo,
                "total_eventos": 0,
                "preventivos": 0,
                "correctivos": 0,
                "calibraciones": 0,
                "otros": 0,
                "tiempo_total": 0,
                "costo_total": 0,
                "ultima_fecha": None
            }
        d = por_equipo[ev.equipo_id]
        d["total_eventos"] += 1

        tipo = (ev.tipo_evento or "otro").lower()
        if tipo == "preventivo":
            d["preventivos"] += 1
        elif tipo == "correctivo":
            d["correctivos"] += 1
        elif tipo == "calibracion":
            d["calibraciones"] += 1
        else:
            d["otros"] += 1

        d["tiempo_total"] += ev.tiempo_invertido or 0
        d["costo_total"] += ev.costo or 0

        # Actualizar última fecha
        if ev.fecha_evento:
            if d["ultima_fecha"] is None or ev.fecha_evento > d["ultima_fecha"]:
                d["ultima_fecha"] = ev.fecha_evento

    # Redondear y formatear
    datos = []
    for d in por_equipo.values():
        d["tiempo_total"] = round(d["tiempo_total"], 2)
        d["costo_total"] = round(d["costo_total"], 2)
        d["ultima_fecha"] = str(d["ultima_fecha"]) if d["ultima_fecha"] else None
        datos.append(d)

    # Ordenar por total_eventos descendente
    datos.sort(key=lambda x: x["total_eventos"], reverse=True)

    return datos


# --- 2. OTs por período ---
@router.get("/ots-por-periodo")
def reporte_ots_por_periodo(
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    estado_id: Optional[int] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Retorna las OTs filtradas por rango de fechas y/o estado,
    junto con un resumen estadístico.
    """
    query = select(OrdenTrabajo)

    if fecha_desde:
        query = query.where(func.date(OrdenTrabajo.fecha_creacion) >= fecha_desde)
    if fecha_hasta:
        query = query.where(func.date(OrdenTrabajo.fecha_creacion) <= fecha_hasta)
    if estado_id:
        query = query.where(OrdenTrabajo.estado_id == estado_id)

    ordenes = session.exec(query.order_by(OrdenTrabajo.fecha_creacion.desc())).all()

    # Mapear estados
    estados_ot = {e.id: e.nombre_estado for e in session.exec(select(EstadoOT)).all()}

    # Mapear equipos
    equipos_map = {e.id: (e.nombre_corto or e.modelo) for e in session.exec(select(Equipo)).all()}

    # Mapear técnicos
    tecnicos_map = {u.id: (u.full_name or u.username) for u in session.exec(select(Usuario)).all()}

    # Construir resultado
    ots_list = []
    for ot in ordenes:
        ots_list.append({
            "id": ot.id,
            "titulo": ot.titulo,
            "equipo_nombre": equipos_map.get(ot.equipo_id, "Desconocido"),
            "estado_nombre": estados_ot.get(ot.estado_id, "Desconocido"),
            "prioridad": ot.prioridad,
            "tecnico_nombre": tecnicos_map.get(ot.tecnico_asignado_id) if ot.tecnico_asignado_id else None,
            "fecha_creacion": str(ot.fecha_creacion) if ot.fecha_creacion else None,
            "acciones_realizadas": ot.acciones_realizadas,
            "tiempo_real_invertido": ot.tiempo_real_invertido,
            "costo_adicional": ot.costo_adicional,
            "orden_preventiva_id": ot.orden_preventiva_id
        })

    # Resumen estadístico
    total_ots = len(ots_list)
    por_estado = {}
    por_prioridad = {}
    total_costo = 0
    total_tiempo = 0

    for ot in ots_list:
        estado = ot["estado_nombre"]
        por_estado[estado] = por_estado.get(estado, 0) + 1
        prio = ot["prioridad"] or "Sin prioridad"
        por_prioridad[prio] = por_prioridad.get(prio, 0) + 1
        if ot["costo_adicional"]:
            total_costo += ot["costo_adicional"]
        if ot["tiempo_real_invertido"]:
            total_tiempo += ot["tiempo_real_invertido"]

    return {
        "resumen": {
            "total_ots": total_ots,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad,
            "total_costo": round(total_costo, 2),
            "total_tiempo": round(total_tiempo, 2)
        },
        "ordenes": ots_list
    }


# --- 3. Análisis de costos ---
@router.get("/costos")
def reporte_costos(
    fecha_desde: Optional[date] = Query(None),
    fecha_hasta: Optional[date] = Query(None),
    session: Session = Depends(get_session)
):
    """
    Retorna un análisis detallado de costos de mantenimiento:
    - Costos por equipo
    - Costos por tipo de evento
    - Costos totales y promedios
    """
    query = select(EventoHistorial)

    if fecha_desde:
        query = query.where(func.date(EventoHistorial.fecha_evento) >= fecha_desde)
    if fecha_hasta:
        query = query.where(func.date(EventoHistorial.fecha_evento) <= fecha_hasta)

    eventos = session.exec(query).all()

    # Mapear equipos
    equipos_map = {e.id: (e.nombre_corto or e.modelo) for e in session.exec(select(Equipo)).all()}

    # Costos por equipo
    costos_por_equipo = {}
    # Costos por tipo
    costos_por_tipo = {}
    total_general = 0
    total_tiempo = 0
    count = 0

    for ev in eventos:
        eq_nombre = equipos_map.get(ev.equipo_id, "Desconocido")
        costo = ev.costo or 0
        tiempo = ev.tiempo_invertido or 0

        # Por equipo
        if eq_nombre not in costos_por_equipo:
            costos_por_equipo[eq_nombre] = {"costo": 0, "tiempo": 0, "eventos": 0}
        costos_por_equipo[eq_nombre]["costo"] += costo
        costos_por_equipo[eq_nombre]["tiempo"] += tiempo
        costos_por_equipo[eq_nombre]["eventos"] += 1

        # Por tipo
        tipo = ev.tipo_evento or "otro"
        if tipo not in costos_por_tipo:
            costos_por_tipo[tipo] = {"costo": 0, "tiempo": 0, "eventos": 0}
        costos_por_tipo[tipo]["costo"] += costo
        costos_por_tipo[tipo]["tiempo"] += tiempo
        costos_por_tipo[tipo]["eventos"] += 1

        total_general += costo
        total_tiempo += tiempo
        count += 1

    # Redondear
    for eq in costos_por_equipo:
        costos_por_equipo[eq]["costo"] = round(costos_por_equipo[eq]["costo"], 2)
        costos_por_equipo[eq]["tiempo"] = round(costos_por_equipo[eq]["tiempo"], 2)
    for tipo in costos_por_tipo:
        costos_por_tipo[tipo]["costo"] = round(costos_por_tipo[tipo]["costo"], 2)
        costos_por_tipo[tipo]["tiempo"] = round(costos_por_tipo[tipo]["tiempo"], 2)

    # Ordenar por costo descendente
    costos_por_equipo_sorted = dict(
        sorted(costos_por_equipo.items(), key=lambda x: x[1]["costo"], reverse=True)
    )

    return {
        "total_costo": round(total_general, 2),
        "total_tiempo": round(total_tiempo, 2),
        "total_eventos": count,
        "costo_promedio": round(total_general / count, 2) if count > 0 else 0,
        "costos_por_equipo": costos_por_equipo_sorted,
        "costos_por_tipo": costos_por_tipo
    }


# --- 4. Cumplimiento de mantenimiento preventivo ---
@router.get("/preventivo-cumplimiento")
def reporte_preventivo_cumplimiento(session: Session = Depends(get_session)):
    """
    Retorna el estado de cumplimiento de las tareas preventivas:
    - Tareas al día, vencidas y próximas a vencer
    - Detalle por equipo
    """
    hoy = date.today()
    en7dias = hoy + timedelta(days=7)
    en30dias = hoy + timedelta(days=30)

    tareas = session.exec(
        select(TareaPreventiva).where(TareaPreventiva.activa == True)
    ).all()

    equipos_map = {e.id: (e.nombre_corto or e.modelo) for e in session.exec(select(Equipo)).all()}
    tecnicos_map = {u.id: (u.full_name or u.username) for u in session.exec(select(Usuario)).all()}

    al_dia = 0
    vencidas = 0
    proximas_7 = 0
    proximas_30 = 0
    detalle = []

    for t in tareas:
        eq_nombre = equipos_map.get(t.equipo_id, "Desconocido")
        tec_nombre = tecnicos_map.get(t.responsable_id) if t.responsable_id else None

        estado = "al_dia"
        if not t.proxima_fecha:
            estado = "sin_fecha"
        elif t.proxima_fecha < hoy:
            estado = "vencida"
            vencidas += 1
        elif t.proxima_fecha <= en7dias:
            estado = "proxima_7"
            proximas_7 += 1
        elif t.proxima_fecha <= en30dias:
            estado = "proxima_30"
            proximas_30 += 1
        else:
            al_dia += 1

        detalle.append({
            "tarea_id": t.id,
            "titulo": t.titulo,
            "equipo_nombre": eq_nombre,
            "responsable": tec_nombre,
            "frecuencia_dias": t.frecuencia_dias,
            "ultima_fecha": str(t.ultima_fecha) if t.ultima_fecha else None,
            "proxima_fecha": str(t.proxima_fecha) if t.proxima_fecha else None,
            "estado": estado
        })

    # Ordenar: vencidas primero
    orden_estado = {"vencida": 0, "proxima_7": 1, "proxima_30": 2, "al_dia": 3, "sin_fecha": 4}
    detalle.sort(key=lambda x: orden_estado.get(x["estado"], 5))

    total_tareas = len(tareas)
    porcentaje_cumplimiento = round((al_dia / total_tareas) * 100, 1) if total_tareas > 0 else 100

    return {
        "resumen": {
            "total_tareas": total_tareas,
            "al_dia": al_dia,
            "vencidas": vencidas,
            "proximas_7_dias": proximas_7,
            "proximas_30_dias": proximas_30,
            "porcentaje_cumplimiento": porcentaje_cumplimiento
        },
        "detalle": detalle
    }


# --- 5. Disponibilidad de equipos ---
@router.get("/disponibilidad-equipos")
def reporte_disponibilidad_equipos(session: Session = Depends(get_session)):
    """
    Retorna la distribución de equipos por estado de disponibilidad.
    """
    estados = session.exec(select(EstadoEquipo)).all()
    equipos = session.exec(select(Equipo)).all()

    distribucion = {}
    for est in estados:
        distribucion[est.nombre_estado] = {
            "count": 0,
            "color": est.color or "#95a5a6",
            "equipos": []
        }

    for eq in equipos:
        estado = session.get(EstadoEquipo, eq.estado_id)
        if estado and estado.nombre_estado in distribucion:
            distribucion[estado.nombre_estado]["count"] += 1
            distribucion[estado.nombre_estado]["equipos"].append({
                "id": eq.id,
                "nombre": eq.nombre_corto or eq.modelo,
                "marca": eq.marca,
                "ubicacion": eq.ubicacion_actual
            })

    total = len(equipos)
    # Calcular disponibilidad = Operativos / Total
    operativos = distribucion.get("Operativo", {}).get("count", 0)
    porcentaje_disponibilidad = round((operativos / total) * 100, 1) if total > 0 else 0

    return {
        "total_equipos": total,
        "porcentaje_disponibilidad": porcentaje_disponibilidad,
        "distribucion": distribucion
    }


# --- 6. Inventario de repuestos ---
@router.get("/inventario-repuestos")
def reporte_inventario_repuestos(session: Session = Depends(get_session)):
    """
    Retorna el estado del inventario de repuestos:
    - Stock bajo
    - Valor total del inventario
    - Repuestos más utilizados
    """
    repuestos = session.exec(select(Repuesto)).all()

    stock_bajo = []
    stock_normal = []
    total_valor = 0

    for r in repuestos:
        # Para valor del inventario, usamos cantidad_disponible (no tenemos precio unitario, usamos 0)
        es_bajo = False
        if r.nivel_stock_minimo and r.nivel_stock_minimo > 0:
            es_bajo = r.cantidad_disponible <= r.nivel_stock_minimo
        else:
            es_bajo = r.cantidad_disponible <= 5

        item = {
            "id": r.id,
            "nombre": r.nombre_repuesto,
            "numero_material": r.numero_material,
            "cantidad_disponible": r.cantidad_disponible,
            "nivel_minimo": r.nivel_stock_minimo or 5,
            "ubicacion": r.ubicacion_almacen,
            "es_bajo": es_bajo
        }

        if es_bajo:
            stock_bajo.append(item)
        else:
            stock_normal.append(item)

    # Repuestos más utilizados (top 10 por cantidad en OtRepuestoUtilizado)
    uso_query = select(
        OtRepuestoUtilizado.repuesto_id,
        func.sum(OtRepuestoUtilizado.cantidad_utilizada).label("total_usado")
    ).group_by(OtRepuestoUtilizado.repuesto_id).order_by(
        func.sum(OtRepuestoUtilizado.cantidad_utilizada).desc()
    ).limit(10)

    usados = session.exec(uso_query).all()
    mas_utilizados = []
    for u in usados:
        rep = session.get(Repuesto, u.repuesto_id)
        mas_utilizados.append({
            "nombre": rep.nombre_repuesto if rep else f"Repuesto#{u.repuesto_id}",
            "total_usado": u.total_usado,
            "stock_actual": rep.cantidad_disponible if rep else 0
        })

    return {
        "total_repuestos": len(repuestos),
        "stock_bajo_count": len(stock_bajo),
        "stock_normal_count": len(stock_normal),
        "stock_bajo": stock_bajo,
        "mas_utilizados": mas_utilizados
    }


# --- 7. MTBF / MTTR / Disponibilidad (v1.0.2 — indicadores del Cap. IV) ---
# Definiciones operativas (convención del sistema, cf. api/routes/ordenes.py:
# tipo_evento = "preventivo" si orden_preventiva_id, sino "correctivo"):
#   - Falla            = OT correctiva COMPLETADA (estado_id=4, sin orden_preventiva_id)
#   - MTBF             = horas operativas del periodo / nº de fallas
#                        horas operativas = horas calendario del periodo − horas de reparación
#   - MTTR             = suma de tiempos de reparación / nº de fallas con tiempo registrado
#   - Disponibilidad   = MTBF / (MTBF + MTTR) × 100
# Unidad de tiempo: horas (tiempo_real_invertido × 24 si unidad_tiempo="dias")

import csv as _csv
import io as _io

_HORA_POR_UNIDAD = {"horas": 1.0, "dias": 24.0}


def _a_horas(tiempo: Optional[float], unidad: Optional[str]) -> float:
    if tiempo is None:
        return 0.0
    factor = _HORA_POR_UNIDAD.get((unidad or "horas").lower(), 1.0)
    return float(tiempo) * factor


# =================================================================
# v2.1 — Motor de métricas MTBF / MTTR / Disponibilidad
# (Reglas de Negocio v2.1 sobre las banderas del dataset importado)
#
#   Regla 3  → ventana_garantia_reparacion=True: reincidencia dentro
#              de la ventana de garantía (<72h). NO cuenta como falla
#              nueva → sale del denominador del MTBF.
#   Regla 6  → excluida_de_MTTR=True (p.ej. cierre administrativo):
#              sale del promedio de MTTR.
#   Regla 4  → mdt_excluido_disponibilidad=True (Falsa_Alarma,
#              Duplicado, Error_Usuario): su MDT NO se suma a la
#              indisponibilidad. Las canceladas por Baja_Equipo SÍ
#              suman MDT (el equipo sí estuvo fuera de servicio).
#   Reglas 11-14 → el MTTR usa HORAS ACTIVAS: reparación bruta −
#              pausas técnicas (tiempo_pausa_acumulado) − espera de
#              repuestos (bitácora). La logística y las pausas no
#              penalizan la eficiencia del técnico.
#
# Compatibilidad histórica (NO se borra la lógica antigua):
#   - OTs sin sellos de tiempo R5 aportan con tiempo_real_invertido
#     (×24 si unidad_tiempo="dias"), igual que en v1.0.2.
#   - La clave "horas_reparacion" mantiene su significado histórico
#     (suma de tiempo registrado) para trazabilidad.
#   - Preventivas vinculadas (orden_preventiva_id) y OTs
#     tipo_origen_ot='Programado' NO son fallas correctivas.
# =================================================================

def _es_programada(ot) -> bool:
    """True si la OT es preventiva/programada (no es falla correctiva)."""
    if ot.orden_preventiva_id is not None:
        return True
    return (ot.tipo_origen_ot or "Usuario") == "Programado"


def _pausa_total_horas(ot, espera_bitacora: float) -> float:
    """Pausa total a descontar de la reparación bruta (Reglas 11-14).
    La bitácora (pausada→reanudada) ya refleja pausas técnicas y espera
    de repuestos; si la columna tiempo_pausa_acumulado declara más de lo
    que la bitácora registra, se suma el faltante (defensa)."""
    pausa_col = float(ot.tiempo_pausa_acumulado or 0.0)
    if espera_bitacora >= pausa_col:
        return espera_bitacora
    return espera_bitacora + pausa_col


def _horas_ot_v21(ot, espera_bitacora: float) -> Optional[dict]:
    """Horas de reparación BRUTAS y ACTIVAS de una OT cerrada.
    - Con sellos R5: brutas = inicio→resolución; activas = brutas − pausas.
    - Históricas (sin sellos): tiempo_real_invertido registrado
      (compatibilidad v1.0.2); activas = registrado − pausa declarada."""
    brutas_sello = _horas_entre(ot.fecha_inicio_trabajo, ot.fecha_resolucion)
    if brutas_sello is not None:
        activas = max(brutas_sello - _pausa_total_horas(ot, espera_bitacora), 0.0)
        return {"brutas": brutas_sello, "activas": round(activas, 2)}
    registrado = _a_horas(ot.tiempo_real_invertido, ot.unidad_tiempo)
    if registrado > 0:
        pausa = min(float(ot.tiempo_pausa_acumulado or 0.0), registrado)
        return {"brutas": round(registrado, 2), "activas": round(max(registrado - pausa, 0.0), 2)}
    return None


def _mdt_horas(ot) -> Optional[float]:
    """MDT de una OT cerrada: resolución − creación (sellos R5).
    Fallback histórico: tiempo_real_invertido registrado."""
    mdt_sello = _horas_entre(ot.fecha_creacion, ot.fecha_resolucion)
    if mdt_sello is not None:
        return mdt_sello
    registrado = _a_horas(ot.tiempo_real_invertido, ot.unidad_tiempo)
    return round(registrado, 2) if registrado > 0 else None


_ADVERTENCIA_MTBF = "Basado en {n} fallas (mínimo recomendado: 3)"


def _calcular_indicadores_v21(session: Session,
                              fecha_desde: Optional[date],
                              fecha_hasta: Optional[date]) -> dict:
    """Núcleo v2.1 compartido por /mtbf-mttr, /mtbf, /mttr y /disponibilidad."""
    hoy = date.today()
    window_end = fecha_hasta or hoy

    equipos = session.exec(select(Equipo)).all()
    ots_cerradas = session.exec(
        select(OrdenTrabajo).where(OrdenTrabajo.estado_id.in_([4, 5]))  # Completada | Cancelada
    ).all()

    # Espera de repuestos/pausas por OT desde la bitácora (pausada → reanudada).
    # Se agrupa POR OT antes de recorrer: en el orden global por fecha los
    # eventos de otras OTs intercalan y romperían los pares pausada→reanudada.
    espera_por_ot: dict[int, float] = {}
    ids_cerradas = [o.id for o in ots_cerradas]
    if ids_cerradas:
        entradas = session.exec(
            select(BitacoraOT)
            .where(BitacoraOT.orden_trabajo_id.in_(ids_cerradas))
            .order_by(BitacoraOT.fecha.asc(), BitacoraOT.id.asc())
        ).all()
        bitacora_por_ot: dict[int, list] = {}
        for ent in entradas:
            bitacora_por_ot.setdefault(ent.orden_trabajo_id, []).append(ent)
        for ot_id, evs in bitacora_por_ot.items():
            pausa_desde = None
            for ent in evs:
                if ent.accion == "pausada":
                    pausa_desde = ent.fecha
                elif ent.accion == "reanudada" and pausa_desde is not None:
                    d = (ent.fecha - pausa_desde).total_seconds() / 3600.0
                    if d >= 0:
                        espera_por_ot[ot_id] = espera_por_ot.get(ot_id, 0.0) + d
                    pausa_desde = None

    # Clasificación de OTs cerradas dentro de la ventana
    fallas_eq: dict[int, list] = {}      # correctivas COMPLETADAS (MTBF/MTTR)
    canceladas_eq: dict[int, list] = {}  # correctivas CANCELADAS (solo MDT)
    programadas_eq: dict[int, list] = {} # informativo (no son fallas)
    for ot in ots_cerradas:
        if not ot.fecha_creacion:
            continue
        if ot.fecha_creacion.date() > window_end:
            continue
        if fecha_desde and ot.fecha_creacion.date() < fecha_desde:
            continue
        if _es_programada(ot):
            if ot.estado_id == 4:
                programadas_eq.setdefault(ot.equipo_id, []).append(ot)
            continue
        if ot.estado_id == 4:
            fallas_eq.setdefault(ot.equipo_id, []).append(ot)
        else:
            canceladas_eq.setdefault(ot.equipo_id, []).append(ot)

    por_equipo = []
    for eq in equipos:
        fallas_raw = fallas_eq.get(eq.id, [])
        canceladas = canceladas_eq.get(eq.id, [])
        programadas = programadas_eq.get(eq.id, [])

        # Regla 3: reincidencias en ventana de garantía no son fallas nuevas
        excl_garantia = [o for o in fallas_raw if o.ventana_garantia_reparacion]
        fallas_reales = [o for o in fallas_raw if not o.ventana_garantia_reparacion]
        # Regla 6: cierres administrativos fuera del MTTR.
        # Nota: las reincidencias en ventana de garantía (Regla 3) salen del
        # denominador del MTBF, pero SÍ aportan al MTTR (fue una reparación real).
        validas_mttr = [o for o in fallas_raw if not o.excluida_de_MTTR]
        n_excl_mttr = sum(1 for o in fallas_raw if o.excluida_de_MTTR)

        horas_reparacion_legacy = sum(_a_horas(o.tiempo_real_invertido, o.unidad_tiempo) for o in fallas_raw)
        sum_activas = 0.0
        for o in validas_mttr:
            h = _horas_ot_v21(o, espera_por_ot.get(o.id, 0.0))
            if h:
                sum_activas += h["activas"]
        n_con_tiempo = sum(1 for o in fallas_raw
                           if o.tiempo_real_invertido is not None and o.tiempo_real_invertido > 0)

        # Regla 4: MDT válido (completadas + canceladas; excluye banderas)
        candidatos_mdt = fallas_raw + canceladas
        mdt_valido = 0.0
        mdt_excluido = 0.0
        for o in candidatos_mdt:
            m = _mdt_horas(o)
            if m is None:
                continue
            if o.mdt_excluido_disponibilidad:
                mdt_excluido += m
            else:
                mdt_valido += m

        # Ventana de observación (misma convención v1.0.2: días completos).
        # v2.1.2: la fuente de la ventana se reporta (ventana_fuente) y, si la
        # ventana da 0 días (p.ej. equipo sin fecha_adquisicion cuya primera
        # OT es de HOY), se recalcula con PRECISIÓN HORARIA: la disponibilidad
        # deja de congelarse en None y el MDT real (p.ej. una Baja_Equipo)
        # no queda oculto tras un 100% implícito. Las OTs programadas
        # completadas también delimitan la ventana (equipo observado).
        fechas_dt = [o.fecha_creacion for o in (candidatos_mdt + programadas) if o.fecha_creacion]
        fechas = [d.date() for d in fechas_dt]
        if fecha_desde:
            inicio, fuente_ventana = fecha_desde, "fecha_desde"
        elif eq.fecha_adquisicion:
            inicio, fuente_ventana = eq.fecha_adquisicion, "fecha_adquisicion"
        elif fechas:
            inicio, fuente_ventana = min(fechas), "primera_OT"
        else:
            continue  # sin forma de definir ventana de observación

        dias_calendario = max((window_end - inicio).days, 0)
        if dias_calendario > 0:
            horas_calendario = dias_calendario * 24.0
        else:
            # v2.1.2 — precisión horaria para ventanas menores a 24h
            fin_dt = datetime.combine(window_end, time.min) + timedelta(days=1)
            if fuente_ventana == "primera_OT" and fechas_dt:
                inicio_dt = min(fechas_dt)  # conserva la hora real de creación
            elif isinstance(inicio, datetime):
                inicio_dt = inicio
            else:
                inicio_dt = datetime.combine(inicio, time.min)
            horas_calendario = max((fin_dt - inicio_dt).total_seconds() / 3600.0, 0.0)
        horas_operativas = max(horas_calendario - mdt_valido, 0.0)

        n_reales = len(fallas_reales)
        mtbf = round(horas_operativas / n_reales, 1) if n_reales > 0 and horas_operativas > 0 else None
        mttr = round(sum_activas / len(validas_mttr), 1) if validas_mttr else None
        if horas_calendario > 0:
            disponibilidad = round(max(horas_calendario - mdt_valido, 0.0) / horas_calendario * 100.0, 1)
        elif mdt_valido > 0:
            disponibilidad = 0.0  # v2.1.2: hay MDT real; una ventana nula no puede exhibir 100%
        else:
            disponibilidad = None

        advertencia = _ADVERTENCIA_MTBF.format(n=n_reales) if n_reales < 3 else None

        por_equipo.append({
            "equipo_id": eq.id,
            "nombre_corto": eq.nombre_corto,
            "modelo": eq.modelo,
            "tipo_equipo": eq.tipo_equipo or "Otro",
            "periodo_inicio": str(inicio),
            "periodo_fin": str(window_end),
            # v1.0.2 (compatibilidad de claves)
            "n_fallas_correctivas": len(fallas_raw),
            "n_con_tiempo_registrado": n_con_tiempo,
            "horas_reparacion": round(horas_reparacion_legacy, 1),
            "horas_operativas": round(horas_operativas, 1),
            # v2.1
            "n_fallas_reales": n_reales,
            "n_excluidas_garantia": len(excl_garantia),
            "n_excluidas_mttr": n_excl_mttr,
            "n_validas_mttr": len(validas_mttr),
            "n_programadas": len(programadas),
            "horas_reparacion_activas": round(sum_activas, 1),
            "mdt_valido_horas": round(mdt_valido, 1),
            "mdt_excluido_horas": round(mdt_excluido, 1),
            "horas_calendario": round(horas_calendario, 1),
            "ventana_fuente": fuente_ventana,
            "mtbf_horas": mtbf,
            "mttr_horas": mttr,
            "disponibilidad_pct": disponibilidad,
            "advertencia_mtbf": advertencia,
        })

    por_equipo.sort(key=lambda x: (-(x["disponibilidad_pct"] or 0), x["nombre_corto"] or ""))

    # Agregación por tipo de equipo (v2.1)
    claves_suma = ["n_fallas_correctivas", "n_fallas_reales", "n_excluidas_garantia",
                   "n_excluidas_mttr", "n_validas_mttr", "n_programadas",
                   "n_con_tiempo_registrado", "horas_reparacion", "horas_reparacion_activas",
                   "mdt_valido_horas", "mdt_excluido_horas", "horas_calendario", "horas_operativas"]
    por_tipo = {}
    for r in por_equipo:
        t = por_tipo.setdefault(r["tipo_equipo"], {"tipo_equipo": r["tipo_equipo"], "n_equipos": 0})
        t["n_equipos"] += 1
        for k in claves_suma:
            t[k] = t.get(k, 0.0) + (r[k] or 0.0)

    por_tipo_out = []
    for t in por_tipo.values():
        for k in claves_suma:
            t[k] = round(t[k], 1)
        t["mtbf_horas"] = round(t["horas_operativas"] / t["n_fallas_reales"], 1) if t["n_fallas_reales"] > 0 and t["horas_operativas"] > 0 else None
        t["mttr_horas"] = round(t["horas_reparacion_activas"] / t["n_validas_mttr"], 1) if t["n_validas_mttr"] > 0 else None
        t["disponibilidad_pct"] = round(max(t["horas_calendario"] - t["mdt_valido_horas"], 0.0) / t["horas_calendario"] * 100.0, 1) if t["horas_calendario"] > 0 else None
        t["advertencia_mtbf"] = _ADVERTENCIA_MTBF.format(n=int(t["n_fallas_reales"])) if t["n_fallas_reales"] < 3 else None
        por_tipo_out.append(t)

    por_tipo_out.sort(key=lambda x: x["tipo_equipo"])

    return {
        "definiciones": {
            "version_motor": "v2.1.2",
            "falla": "OT correctiva completada (sin orden preventiva asociada; tipo_origen_ot != 'Programado')",
            "fallas_reales": "fallas correctivas menos reincidencias en ventana de garantía (Regla 3: ventana_garantia_reparacion=True no es falla nueva)",
            "mtbf": "horas operativas / fallas reales — horas operativas = horas calendario − MDT válido",
            "mttr": "suma de horas de reparación ACTIVAS / nº de OTs completadas válidas (Regla 6: excluye excluida_de_MTTR=True; Reglas 11-14: activas = brutas − pausas − espera repuestos)",
            "mdt_valido": "suma de (resolución − creación) de OTs con mdt_excluido_disponibilidad=False — incluye canceladas por Baja_Equipo (Regla 4)",
            "disponibilidad": "(horas calendario − MDT válido) / horas calendario × 100",
            "ventana_calendario": "horas entre fecha_adquisicion (o, en su defecto, la primera OT cerrada del equipo) y la fecha de corte; días completos, con precisión horaria si la ventana es menor a 24h (v2.1.2). ventana_fuente indica el origen usado",
            "compatibilidad": "OTs históricas sin sellos de tiempo (R5) aportan con tiempo_real_invertido (horas; días ×24). 'horas_reparacion' conserva su significado histórico (tiempo registrado)",
            "unidad_tiempo": "horas",
        },
        "parametros": {"fecha_desde": str(fecha_desde) if fecha_desde else None,
                        "fecha_hasta": str(window_end)},
        "reglas_v21": {
            "regla_3_garantia": "ventana_garantia_reparacion=True → fuera del denominador MTBF",
            "regla_6_cierre_admin": "excluida_de_MTTR=True → fuera del promedio MTTR",
            "regla_4_mdt": "mdt_excluido_disponibilidad=True → MDT no suma a indisponibilidad; Baja_Equipo SÍ suma",
            "reglas_11_14_horas_activas": "MTTR usa activas: brutas − tiempo_pausa_acumulado − espera de repuestos (bitácora)",
            "excluidas_garantia": sum(r["n_excluidas_garantia"] for r in por_equipo),
            "excluidas_mttr": sum(r["n_excluidas_mttr"] for r in por_equipo),
            "mdt_excluido_horas": round(sum(r["mdt_excluido_horas"] for r in por_equipo), 1),
        },
        "por_equipo": por_equipo,
        "por_tipo_equipo": por_tipo_out,
    }


_COLS_CSV_V21 = ["equipo_id", "nombre_corto", "modelo", "tipo_equipo",
                 "periodo_inicio", "periodo_fin", "n_fallas_correctivas",
                 "n_fallas_reales", "n_excluidas_garantia", "n_excluidas_mttr",
                 "n_validas_mttr", "n_programadas", "n_con_tiempo_registrado",
                 "horas_reparacion", "horas_reparacion_activas", "mdt_valido_horas",
                 "mdt_excluido_horas", "horas_calendario", "horas_operativas",
                 "mtbf_horas", "mttr_horas", "disponibilidad_pct", "advertencia_mtbf",
                 "ventana_fuente"]


@router.get("/mtbf-mttr")
def reporte_mtbf_mttr(
    fecha_desde: Optional[date] = Query(None, description="Inicio del periodo (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fin del periodo (YYYY-MM-DD)"),
    formato: str = Query("json", description="json | csv (por equipo, para análisis estadístico)"),
    session: Session = Depends(get_session)
):
    """
    Calcula MTBF, MTTR y Disponibilidad por equipo y por tipo de equipo
    aplicando las Reglas de Negocio v2.1 (banderas: ventana_garantia_reparacion,
    excluida_de_MTTR, mdt_excluido_disponibilidad, tiempo_pausa_acumulado).
    Exportable en CSV para el análisis estadístico de la tesis (Capítulo IV).
    Payload idéntico disponible en /reportes/mtbf, /reportes/mttr y
    /reportes/disponibilidad.
    """
    resultado = _calcular_indicadores_v21(session, fecha_desde, fecha_hasta)
    hoy = date.today()

    if (formato or "json").lower() == "csv":
        buffer = _io.StringIO()
        w = _csv.writer(buffer)
        w.writerow(_COLS_CSV_V21)
        for r in resultado["por_equipo"]:
            w.writerow([r.get(c) for c in _COLS_CSV_V21])
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cmmsbioai_mtbf_mttr_v21_{hoy}.csv"'},
        )

    return resultado


# --- Aliases v2.1 (mismo payload; consulta directa por indicador) ---
@router.get("/mtbf")
def reporte_mtbf(
    fecha_desde: Optional[date] = Query(None, description="Inicio del periodo (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fin del periodo (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    """Alias de /reportes/mtbf-mttr — foco MTBF (Regla 3: reincidencias en
    ventana de garantía no cuentan como fallas nuevas)."""
    return _calcular_indicadores_v21(session, fecha_desde, fecha_hasta)


@router.get("/mttr")
def reporte_mttr(
    fecha_desde: Optional[date] = Query(None, description="Inicio del periodo (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fin del periodo (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    """Alias de /reportes/mtbf-mttr — foco MTTR (Regla 6: excluye cierres
    administrativos; Reglas 11-14: horas activas)."""
    return _calcular_indicadores_v21(session, fecha_desde, fecha_hasta)


@router.get("/disponibilidad")
def reporte_disponibilidad(
    fecha_desde: Optional[date] = Query(None, description="Inicio del periodo (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fin del periodo (YYYY-MM-DD)"),
    session: Session = Depends(get_session)
):
    """Alias de /reportes/mtbf-mttr — foco Disponibilidad (Regla 4: el MDT de
    falsas alarmas/duplicados/errores de usuario no resta; Baja_Equipo sí)."""
    return _calcular_indicadores_v21(session, fecha_desde, fecha_hasta)


# =================================================================
# v1.1.0 — KPIs del Flujo de Trabajo OT (Propuesta aprobada 03/10)
# Endpoint: GET /reportes/tiempos-etapa  (+ exportación CSV Cap. IV)
#
#   MTTA (Mean Time To Assign) = creación → asignación de técnico
#   Tiempo de reacción         = asignación → inicio de trabajo
#   Reparación bruta           = inicio de trabajo → resolución
#   Espera de repuestos        = suma de intervalos "Esp. Repuesto"
#                                (de la bitácora: pausar → reanudar)
#   Reparación activa          = reparación bruta − espera repuestos
#   Tasa de cancelación        = canceladas / creadas × 100
#   Tasa de reapertura         = OTs reabiertas / completadas × 100
#
# Solo las OTs con sellos de tiempo (creadas bajo el flujo v1.1.0)
# aportan a los promedios; las anteriores aparecen con "—".
# =================================================================

def _horas_entre(inicio: Optional[datetime], fin: Optional[datetime]) -> Optional[float]:
    if inicio is None or fin is None:
        return None
    delta = (fin - inicio).total_seconds() / 3600.0
    if delta < 0:
        return None
    return round(delta, 2)


@router.get("/tiempos-etapa")
def reporte_tiempos_etapa(
    fecha_desde: Optional[date] = Query(None, description="Inicio del periodo (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fin del periodo (YYYY-MM-DD)"),
    formato: str = Query("json", description="json | csv (una fila por OT, Cap. IV)"),
    session: Session = Depends(get_session)
):
    hoy = date.today()
    window_start = fecha_desde or date(hoy.year - 5, 1, 1)
    window_end = fecha_hasta or hoy

    query = select(OrdenTrabajo).where(func.date(OrdenTrabajo.fecha_creacion) >= window_start,
                                       func.date(OrdenTrabajo.fecha_creacion) <= window_end)
    ordenes = session.exec(query).all()

    equipos_map = {e.id: (e.nombre_corto or "N/A", e.tipo_equipo or "N/A")
                   for e in session.exec(select(Equipo)).all()}
    estados_map = {e.id: e.nombre_estado for e in session.exec(select(EstadoOT)).all()}

    # Bitácora completa del periodo, agrupada por OT (para espera de repuestos y reaperturas)
    bitacora_por_ot: dict[int, list[BitacoraOT]] = {}
    if ordenes:
        entradas = session.exec(
            select(BitacoraOT).order_by(BitacoraOT.fecha.asc(), BitacoraOT.id.asc())
        ).all()
        for ent in entradas:
            bitacora_por_ot.setdefault(ent.orden_trabajo_id, []).append(ent)

    ahora = datetime.now()
    por_ot = []
    valores = {"mtta": [], "reaccion": [], "reparacion": [], "espera": [], "activa": []}
    n_completadas = 0
    n_canceladas = 0
    n_reabiertas = 0

    for ot in ordenes:
        equipo_nombre, tipo_equipo = equipos_map.get(ot.equipo_id, ("Desconocido", "N/A"))
        estado_actual = estados_map.get(ot.estado_id, "?")

        h_asig = _horas_entre(ot.fecha_creacion, ot.fecha_asignacion)
        h_reac = _horas_entre(ot.fecha_asignacion, ot.fecha_inicio_trabajo)
        h_rep = _horas_entre(ot.fecha_inicio_trabajo, ot.fecha_resolucion)

        # Espera de repuestos desde la bitácora (R4): intervalos pausada → reanudada
        h_espera = 0.0
        pausa_desde = None
        n_reab_ot = 0
        for ent in bitacora_por_ot.get(ot.id, []):
            if ent.accion == "pausada":
                pausa_desde = ent.fecha
            elif ent.accion == "reanudada" and pausa_desde is not None:
                d = (ent.fecha - pausa_desde).total_seconds() / 3600.0
                if d >= 0:
                    h_espera += d
                pausa_desde = None
            elif ent.accion == "reabierta":
                n_reab_ot += 1
        if estado_actual == "Esp. Repuesto" and pausa_desde is not None:
            d = (ahora - pausa_desde).total_seconds() / 3600.0
            if d >= 0:
                h_espera += d
        h_espera = round(h_espera, 2) if h_rep is not None or h_espera > 0 else 0.0

        h_activa = None
        if h_rep is not None:
            h_activa = round(max(h_rep - h_espera, 0.0), 2)

        if h_asig is not None:
            valores["mtta"].append(h_asig)
        if h_reac is not None:
            valores["reaccion"].append(h_reac)
        if h_rep is not None:
            valores["reparacion"].append(h_rep)
            if h_espera > 0:
                valores["espera"].append(h_espera)
            if h_activa is not None:
                valores["activa"].append(h_activa)
        if estado_actual == "Completada":
            n_completadas += 1
        elif estado_actual == "Cancelada":
            n_canceladas += 1
        if n_reab_ot > 0:
            n_reabiertas += 1

        por_ot.append({
            "ot_id": ot.id,
            "equipo": equipo_nombre,
            "tipo_equipo": tipo_equipo,
            "titulo": ot.titulo,
            "preventiva": bool(ot.orden_preventiva_id),
            "estado_actual": estado_actual,
            "prioridad": ot.prioridad,
            "fecha_creacion": ot.fecha_creacion.isoformat(sep=" ") if ot.fecha_creacion else None,
            "fecha_asignacion": ot.fecha_asignacion.isoformat(sep=" ") if ot.fecha_asignacion else None,
            "fecha_inicio_trabajo": ot.fecha_inicio_trabajo.isoformat(sep=" ") if ot.fecha_inicio_trabajo else None,
            "fecha_resolucion": ot.fecha_resolucion.isoformat(sep=" ") if ot.fecha_resolucion else None,
            "horas_hasta_asignacion": h_asig,
            "horas_reaccion": h_reac,
            "horas_reparacion_brutas": h_rep,
            "horas_espera_repuesto": round(h_espera, 2),
            "horas_reparacion_activas": h_activa,
            "tiempo_invertido_registrado": ot.tiempo_real_invertido,
            "unidad_tiempo": ot.unidad_tiempo or "horas",
            "n_reaperturas": n_reab_ot,
            # v1.1.1: cadena de reincidencias (cierre definitivo + OT nueva vinculada)
            "parent_ot_id": ot.parent_ot_id,
            "failure_sequence": ot.failure_sequence or 1,
            # v2.1: banderas del dataset (informativo para el análisis Cap. IV)
            "tipo_origen_ot": ot.tipo_origen_ot,
            "tipo_impacto": ot.tipo_impacto,
            "ventana_garantia_reparacion": ot.ventana_garantia_reparacion,
            "es_reparacion_inefectiva": ot.es_reparacion_inefectiva,
            "excluida_de_MTTR": ot.excluida_de_MTTR,
            "mdt_excluido_disponibilidad": ot.mdt_excluido_disponibilidad,
            "cierre_administrativo": ot.cierre_administrativo,
            "motivo_cancelacion": ot.motivo_cancelacion,
        })

    def _prom(lista):
        return round(sum(lista) / len(lista), 2) if lista else None

    resumen = {
        "n_ots": len(ordenes),
        "n_completadas": n_completadas,
        "n_canceladas": n_canceladas,
        "n_reabiertas": n_reabiertas,
        "n_reincidencias": sum(1 for ot in ordenes if ot.parent_ot_id),
        "mtta_horas": _prom(valores["mtta"]),
        "tiempo_reaccion_horas": _prom(valores["reaccion"]),
        "reparacion_bruta_horas": _prom(valores["reparacion"]),
        "espera_repuesto_horas": _prom(valores["espera"]),
        "reparacion_activa_horas": _prom(valores["activa"]),
        "tasa_cancelacion_pct": round(n_canceladas * 100.0 / len(ordenes), 1) if ordenes else None,
        "tasa_reapertura_pct": round(n_reabiertas * 100.0 / n_completadas, 1) if n_completadas else None,
        "tasa_reincidencia_pct": round(sum(1 for ot in ordenes if ot.parent_ot_id) * 100.0 / len(ordenes), 1) if ordenes else None,
    }

    resultado = {
        "definiciones": {
            "mtta": "creación de la OT → asignación de técnico (promedio, horas)",
            "tiempo_reaccion": "asignación → inicio del trabajo en sitio (promedio, horas)",
            "reparacion_bruta": "inicio del trabajo → resolución (promedio, horas)",
            "espera_repuesto": "intervalos en estado 'Esp. Repuesto' según bitácora (promedio, horas)",
            "reparacion_activa": "reparación bruta − espera de repuestos (promedio, horas)",
            "tasa_cancelacion": "OTs canceladas / OTs creadas × 100",
            "tasa_reapertura": "OTs reabiertas / OTs completadas × 100 (histórico; desde v1.1.1 la cerrada es inmutable y la re-intervención genera OT nueva vinculada)",
            "tasa_reincidencia": "OTs que nacieron como reincidencia (parent_ot_id) / OTs creadas × 100 — indicador de fallas crónicas",
            "alcance": "solo OTs creadas bajo el flujo v1.1.0 tienen sellos de tiempo completos (R5)",
        },
        "parametros": {"fecha_desde": str(window_start), "fecha_hasta": str(window_end)},
        "resumen": resumen,
        "por_ot": por_ot,
    }

    if (formato or "json").lower() == "csv":
        buffer = _io.StringIO()
        w = _csv.writer(buffer)
        cols = ["ot_id", "equipo", "tipo_equipo", "titulo", "preventiva", "estado_actual",
                "prioridad", "fecha_creacion", "fecha_asignacion", "fecha_inicio_trabajo",
                "fecha_resolucion", "horas_hasta_asignacion", "horas_reaccion",
                "horas_reparacion_brutas", "horas_espera_repuesto", "horas_reparacion_activas",
                "tiempo_invertido_registrado", "unidad_tiempo", "n_reaperturas",
                "parent_ot_id", "failure_sequence",
                "tipo_origen_ot", "tipo_impacto", "ventana_garantia_reparacion",
                "es_reparacion_inefectiva", "excluida_de_MTTR",
                "mdt_excluido_disponibilidad", "cierre_administrativo",
                "motivo_cancelacion"]
        w.writerow(cols)
        for r in por_ot:
            w.writerow([r[c] for c in cols])
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cmmsbioai_tiempos_etapa_{hoy}.csv"'},
        )

    return resultado


# =================================================================
# v1.1.1 — Bitácora exportable (CSV): por OT o por EQUIPO (todas las
# OTs del equipo, en orden cronológico). Responde a la necesidad del
# usuario: "¿se puede exportar como historial de la OT o del equipo?"
# =================================================================
@router.get("/bitacora-csv")
def bitacora_csv(
    ot_id: Optional[int] = Query(None, description="Bitácora de una sola OT"),
    equipo_id: Optional[int] = Query(None, description="Bitácora de TODAS las OTs del equipo"),
    session: Session = Depends(get_session)
):
    if not ot_id and not equipo_id:
        raise HTTPException(status_code=400, detail="Indique ot_id o equipo_id")

    if ot_id:
        if not session.get(OrdenTrabajo, ot_id):
            raise HTTPException(status_code=404, detail=f"OT {ot_id} no encontrada")
        query = select(BitacoraOT).where(BitacoraOT.orden_trabajo_id == ot_id)
        nombre_archivo = f"bitacora_ot_{ot_id}_{date.today()}.csv"
    else:
        ots_ids = [o.id for o in session.exec(
            select(OrdenTrabajo).where(OrdenTrabajo.equipo_id == equipo_id)
        ).all()]
        if not ots_ids:
            raise HTTPException(status_code=404, detail=f"El equipo {equipo_id} no tiene OTs con bitácora")
        query = select(BitacoraOT).where(BitacoraOT.orden_trabajo_id.in_(ots_ids))
        nombre_archivo = f"bitacora_equipo_{equipo_id}_{date.today()}.csv"

    entradas = session.exec(query.order_by(BitacoraOT.fecha.asc(), BitacoraOT.id.asc())).all()

    buffer = _io.StringIO()
    w = _csv.writer(buffer)
    w.writerow(["fecha", "ot_id", "accion", "usuario", "estado_anterior", "estado_nuevo", "comentario"])
    for e in entradas:
        w.writerow([
            e.fecha.isoformat(sep=" ") if e.fecha else "",
            e.orden_trabajo_id,
            e.accion,
            e.usuario or "sistema",
            e.estado_anterior or "",
            e.estado_nuevo or "",
            (e.comentario or "").replace("\n", " "),
        ])
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{nombre_archivo}"'},
    )
