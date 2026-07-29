from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from typing import Optional
from datetime import datetime, date, timedelta
from database import get_session
from models.equipos import Equipo
from models.ordenes import OrdenTrabajo, EstadoOT
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
