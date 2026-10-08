from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select, func
from typing import Optional
from datetime import datetime, date, timedelta
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

from fastapi.responses import StreamingResponse
import csv as _csv
import io as _io

_HORA_POR_UNIDAD = {"horas": 1.0, "dias": 24.0}


def _a_horas(tiempo: Optional[float], unidad: Optional[str]) -> float:
    if tiempo is None:
        return 0.0
    factor = _HORA_POR_UNIDAD.get((unidad or "horas").lower(), 1.0)
    return float(tiempo) * factor


@router.get("/mtbf-mttr")
def reporte_mtbf_mttr(
    fecha_desde: Optional[date] = Query(None, description="Inicio del periodo (YYYY-MM-DD)"),
    fecha_hasta: Optional[date] = Query(None, description="Fin del periodo (YYYY-MM-DD)"),
    formato: str = Query("json", description="json | csv (por equipo, para análisis estadístico)"),
    session: Session = Depends(get_session)
):
    """
    Calcula MTBF, MTTR y Disponibilidad por equipo y por tipo de equipo,
    a partir de las OTs correctivas completadas registradas en el sistema.
    Exportable en CSV para el análisis estadístico de la tesis (Capítulo IV).
    """
    hoy = date.today()
    window_end = fecha_hasta or hoy

    equipos = session.exec(select(Equipo)).all()
    ots = session.exec(
        select(OrdenTrabajo).where(OrdenTrabajo.estado_id == 4)  # Completada
    ).all()

    # Solo correctivas (sin orden_preventiva_id)
    correctivas_por_equipo: dict = {}
    for ot in ots:
        if ot.orden_preventiva_id is not None:
            continue
        if ot.fecha_creacion and ot.fecha_creacion.date() > window_end:
            continue
        if fecha_desde and ot.fecha_creacion and ot.fecha_creacion.date() < fecha_desde:
            continue
        correctivas_por_equipo.setdefault(ot.equipo_id, []).append(ot)

    por_equipo = []
    for eq in equipos:
        ots_eq = correctivas_por_equipo.get(eq.id, [])
        n_fallas = len(ots_eq)
        horas_reparacion = sum(_a_horas(ot.tiempo_real_invertido, ot.unidad_tiempo) for ot in ots_eq)
        n_con_tiempo = sum(1 for ot in ots_eq if ot.tiempo_real_invertido is not None and ot.tiempo_real_invertido > 0)

        # Ventana de observación: fecha_desde → fecha_adquisicion → primera correctiva
        fechas = [ot.fecha_creacion.date() for ot in ots_eq if ot.fecha_creacion]
        inicio = fecha_desde or eq.fecha_adquisicion or (min(fechas) if fechas else None)
        if inicio is None:
            continue  # sin forma de definir ventana de observación

        dias_calendario = max((window_end - inicio).days, 0)
        horas_calendario = dias_calendario * 24.0
        horas_operativas = max(horas_calendario - horas_reparacion, 0.0)

        mtbf = round(horas_operativas / n_fallas, 1) if n_fallas > 0 and horas_operativas > 0 else None
        mttr = round(horas_reparacion / n_con_tiempo, 1) if n_con_tiempo > 0 else None
        if mtbf is not None and mttr is not None and (mtbf + mttr) > 0:
            disponibilidad = round(mtbf / (mtbf + mttr) * 100.0, 1)
        elif n_fallas == 0 and horas_operativas > 0:
            disponibilidad = 100.0  # sin fallas registradas en el periodo
        else:
            disponibilidad = None

        por_equipo.append({
            "equipo_id": eq.id,
            "nombre_corto": eq.nombre_corto,
            "modelo": eq.modelo,
            "tipo_equipo": eq.tipo_equipo or "Otro",
            "periodo_inicio": str(inicio),
            "periodo_fin": str(window_end),
            "n_fallas_correctivas": n_fallas,
            "n_con_tiempo_registrado": n_con_tiempo,
            "horas_reparacion": round(horas_reparacion, 1),
            "horas_operativas": round(horas_operativas, 1),
            "mtbf_horas": mtbf,
            "mttr_horas": mttr,
            "disponibilidad_pct": disponibilidad,
        })

    por_equipo.sort(key=lambda x: (-(x["disponibilidad_pct"] or 0), x["nombre_corto"] or ""))

    # Agregación por tipo de equipo (suma de horas y fallas)
    por_tipo = {}
    for r in por_equipo:
        t = por_tipo.setdefault(r["tipo_equipo"], {
            "tipo_equipo": r["tipo_equipo"], "n_equipos": 0, "n_fallas_correctivas": 0,
            "n_con_tiempo_registrado": 0, "horas_reparacion": 0.0, "horas_operativas": 0.0,
        })
        t["n_equipos"] += 1
        t["n_fallas_correctivas"] += r["n_fallas_correctivas"]
        t["n_con_tiempo_registrado"] += r["n_con_tiempo_registrado"]
        t["horas_reparacion"] += r["horas_reparacion"]
        t["horas_operativas"] += r["horas_operativas"]

    por_tipo_out = []
    for t in por_tipo.values():
        t["horas_reparacion"] = round(t["horas_reparacion"], 1)
        t["horas_operativas"] = round(t["horas_operativas"], 1)
        t["mtbf_horas"] = round(t["horas_operativas"] / t["n_fallas_correctivas"], 1) if t["n_fallas_correctivas"] > 0 and t["horas_operativas"] > 0 else None
        t["mttr_horas"] = round(t["horas_reparacion"] / t["n_con_tiempo_registrado"], 1) if t["n_con_tiempo_registrado"] > 0 else None
        if t["mtbf_horas"] is not None and t["mttr_horas"] is not None and (t["mtbf_horas"] + t["mttr_horas"]) > 0:
            t["disponibilidad_pct"] = round(t["mtbf_horas"] / (t["mtbf_horas"] + t["mttr_horas"]) * 100.0, 1)
        elif t["n_fallas_correctivas"] == 0 and t["horas_operativas"] > 0:
            t["disponibilidad_pct"] = 100.0
        else:
            t["disponibilidad_pct"] = None
        por_tipo_out.append(t)

    por_tipo_out.sort(key=lambda x: x["tipo_equipo"])

    resultado = {
        "definiciones": {
            "falla": "OT correctiva completada (sin orden preventiva asociada)",
            "mtbf": "horas operativas del periodo / nº de fallas",
            "mttr": "suma de tiempos de reparación / nº de fallas con tiempo registrado",
            "disponibilidad": "MTBF / (MTBF + MTTR) × 100",
            "unidad_tiempo": "horas",
        },
        "parametros": {"fecha_desde": str(fecha_desde) if fecha_desde else None,
                        "fecha_hasta": str(window_end)},
        "por_equipo": por_equipo,
        "por_tipo_equipo": por_tipo_out,
    }

    if (formato or "json").lower() == "csv":
        buffer = _io.StringIO()
        w = _csv.writer(buffer)
        w.writerow(["equipo_id", "nombre_corto", "modelo", "tipo_equipo",
                    "periodo_inicio", "periodo_fin", "n_fallas_correctivas",
                    "n_con_tiempo_registrado", "horas_reparacion", "horas_operativas",
                    "mtbf_horas", "mttr_horas", "disponibilidad_pct"])
        for r in por_equipo:
            w.writerow([r[c] for c in ["equipo_id", "nombre_corto", "modelo", "tipo_equipo",
                                        "periodo_inicio", "periodo_fin", "n_fallas_correctivas",
                                        "n_con_tiempo_registrado", "horas_reparacion",
                                        "horas_operativas", "mtbf_horas", "mttr_horas",
                                        "disponibilidad_pct"]])
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="cmmsbioai_mtbf_mttr_{hoy}.csv"'},
        )

    return resultado


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
                "parent_ot_id", "failure_sequence"]
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
