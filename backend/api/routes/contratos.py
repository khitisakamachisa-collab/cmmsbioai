"""
Endpoints CRUD para Contratos - RF12 v0.9.2
v0.9.8: agregado endpoint /import-excel para importar contratos desde .xlsx/.csv
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime, date
from database import get_session
from models.contratos import Contrato, ContratoEquipo
from models.proveedores import Proveedor
from models.equipos import Equipo
from schemas.contrato import ContratoCreate, ContratoUpdate, ContratoRead
from schemas.contrato import TIPOS_CONTRATO, PERIODICIDADES, MONEDAS
from pathlib import Path
from io import BytesIO, StringIO
import csv
import openpyxl

router = APIRouter(prefix="/contratos", tags=["Contratos"])


def _calcular_estado(fecha_inicio, fecha_fin):
    hoy = date.today()
    activo = False
    dias_restantes = None
    if isinstance(fecha_inicio, datetime):
        fecha_inicio = fecha_inicio.date()
    if isinstance(fecha_fin, datetime):
        fecha_fin = fecha_fin.date()
    if fecha_inicio and fecha_fin:
        if fecha_inicio <= hoy <= fecha_fin:
            activo = True
            dias_restantes = (fecha_fin - hoy).days
        elif fecha_fin < hoy:
            activo = False
            dias_restantes = (fecha_fin - hoy).days
        else:
            activo = False
            dias_restantes = (fecha_inicio - hoy).days
    return activo, dias_restantes


def _enriquecer_contrato(session, contrato):
    data = contrato.model_dump()
    activo, dias_restantes = _calcular_estado(contrato.fecha_inicio, contrato.fecha_fin)
    data['activo'] = activo
    data['dias_restantes'] = dias_restantes
    proveedor = session.get(Proveedor, contrato.proveedor_id)
    data['proveedor_nombre'] = proveedor.nombre_empresa if proveedor else 'N/A'
    asociaciones = session.exec(
        select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato.id)
    ).all()
    equipos = []
    for a in asociaciones:
        eq = session.get(Equipo, a.equipo_id)
        if eq:
            equipos.append({'id': eq.id, 'nombre_corto': eq.nombre_corto, 'modelo': eq.modelo,
                           'numero_serie': eq.numero_serie, 'ubicacion_actual': eq.ubicacion_actual})
    data['equipos'] = equipos
    return data


@router.post("/", response_model=ContratoRead, status_code=201)
def crear_contrato(payload: ContratoCreate, session: Session = Depends(get_session)):
    proveedor = session.get(Proveedor, payload.proveedor_id)
    if not proveedor:
        raise HTTPException(status_code=400, detail=f"Proveedor ID {payload.proveedor_id} no existe")
    if payload.fecha_fin < payload.fecha_inicio:
        raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")
    datos = payload.model_dump(exclude={'equipos_ids'})
    datos['fecha_inicio'] = datetime.combine(datos['fecha_inicio'], datetime.min.time())
    datos['fecha_fin'] = datetime.combine(datos['fecha_fin'], datetime.min.time())
    nuevo = Contrato(**datos)
    session.add(nuevo)
    session.flush()
    if payload.equipos_ids:
        for eq_id in payload.equipos_ids:
            eq = session.get(Equipo, eq_id)
            if eq:
                session.add(ContratoEquipo(contrato_id=nuevo.id, equipo_id=eq_id))
    session.commit()
    session.refresh(nuevo)
    return _enriquecer_contrato(session, nuevo)


@router.get("/", response_model=list[ContratoRead])
def listar_contratos(proveedor_id: int = None, equipo_id: int = None, vigente: bool = None, session: Session = Depends(get_session)):
    query = select(Contrato)
    if proveedor_id:
        query = query.where(Contrato.proveedor_id == proveedor_id)
    if equipo_id:
        contrato_ids = select(ContratoEquipo.contrato_id).where(ContratoEquipo.equipo_id == equipo_id)
        query = query.where(Contrato.id.in_(contrato_ids))
    contratos = session.exec(query.order_by(Contrato.fecha_fin.desc())).all()
    resultado = []
    for c in contratos:
        data = _enriquecer_contrato(session, c)
        if vigente is True and not data['activo']:
            continue
        if vigente is False and data['activo']:
            continue
        resultado.append(data)
    return resultado


@router.get("/{contrato_id}", response_model=ContratoRead)
def obtener_contrato(contrato_id: int, session: Session = Depends(get_session)):
    contrato = session.get(Contrato, contrato_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    return _enriquecer_contrato(session, contrato)


@router.put("/{contrato_id}", response_model=ContratoRead)
def actualizar_contrato(contrato_id: int, payload: ContratoUpdate, session: Session = Depends(get_session)):
    db_contrato = session.get(Contrato, contrato_id)
    if not db_contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    datos = payload.model_dump(exclude_unset=True)
    equipos_ids = datos.pop('equipos_ids', None)
    for key, value in datos.items():
        if key in ('fecha_inicio', 'fecha_fin') and value:
            value = datetime.combine(value, datetime.min.time())
        setattr(db_contrato, key, value)
    if db_contrato.fecha_fin < db_contrato.fecha_inicio:
        raise HTTPException(status_code=400, detail="fecha_fin debe ser mayor o igual a fecha_inicio")
    session.add(db_contrato)
    if equipos_ids is not None:
        existing = session.exec(select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato_id)).all()
        for e in existing:
            session.delete(e)
        session.flush()
        for eq_id in equipos_ids:
            eq = session.get(Equipo, eq_id)
            if eq:
                session.add(ContratoEquipo(contrato_id=contrato_id, equipo_id=eq_id))
    session.commit()
    session.refresh(db_contrato)
    return _enriquecer_contrato(session, db_contrato)


@router.delete("/{contrato_id}")
def eliminar_contrato(contrato_id: int, session: Session = Depends(get_session)):
    db_contrato = session.get(Contrato, contrato_id)
    if not db_contrato:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    asociaciones = session.exec(select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato_id)).all()
    for a in asociaciones:
        session.delete(a)
    session.delete(db_contrato)
    session.commit()
    return {"ok": True, "message": "Contrato eliminado"}


@router.get("/tipos/lista")
def listar_tipos_contrato():
    return ['Comodato', 'Mantenimiento Preventivo', 'Mantenimiento Correctivo',
            'Leasing', 'Garantía Extendida', 'Soporte Técnico', 'Servicio Integral', 'Otro']


@router.get("/monedas/lista")
def listar_monedas():
    return ['USD', 'EUR', 'BOB', 'MXN', 'ARS', 'CLP', 'COP', 'PEN', 'BRL', 'Otro']


@router.get("/periodicidades/lista")
def listar_periodicidades():
    return ['Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual']


# ============================================================
# v0.9.8 — Importación desde Excel/CSV
# ============================================================

@router.post("/import-excel")
async def importar_contratos_excel(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    Importa contratos desde un archivo .xlsx o .csv.

    Columnas esperadas (encabezado en fila 1):
      proveedor_nombre*, tipo_contrato*, fecha_inicio*, fecha_fin*,
      costo_total, costo_periodico, periodicidad_costo, moneda,
      tiempo_respuesta, horario_servicio, cobertura_detalle, notas,
      equipos_series

    - proveedor_nombre: si no existe, se CREA automáticamente el proveedor.
    - tipo_contrato: debe ser uno de TIPOS_CONTRATO (default 'Otro').
    - periodicidad_costo: debe ser uno de PERIODICIDADES (default 'Único').
    - moneda: debe ser una de MONEDAS (default 'USD').
    - equipos_series: lista de numero_serie separados por ';' — se asocian
      los equipos cuyo numero_serie coincida. Los que no existan se ignoran
      (pero se reportan en errores).
    - Si ya existe un contrato con mismo proveedor_id + tipo_contrato + fecha_inicio,
      se ACTUALIZA (upsert).

    Retorna: { exitosos, actualizados, fallidos, total_procesados, errores[] }
    """
    ext = Path(file.filename).suffix.lower() if file.filename else ''
    if ext not in ('.xlsx', '.csv'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx o .csv")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no debe superar 5MB")

    is_csv = ext == '.csv'
    filas = []

    if is_csv:
        try:
            text = contents.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                text = contents.decode('latin-1')
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Error al decodificar CSV: {e}")
        try:
            sniffer_sample = text[:2048]
            try:
                dialect = csv.Sniffer().sniff(sniffer_sample, delimiters=',;\t')
            except csv.Error:
                dialect = csv.excel
            reader = csv.reader(StringIO(text), dialect)
            filas = list(reader)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al leer CSV: {e}")
    else:
        try:
            wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Error al leer Excel: {e}")
        # Tomar la primera hoja con encabezados válidos
        for sheet in wb.worksheets:
            filas_tmp = list(sheet.iter_rows(values_only=True))
            if filas_tmp:
                enc = [str(c).strip().lower() if c else '' for c in filas_tmp[0]]
                if 'proveedor_nombre' in enc and 'tipo_contrato' in enc:
                    filas = [list(r) for r in filas_tmp]
                    break
        if not filas and wb.worksheets:
            filas = [list(r) for r in wb.worksheets[0].iter_rows(values_only=True)]

    if len(filas) < 2:
        raise HTTPException(status_code=400, detail="El archivo está vacío o solo tiene encabezados")

    # Mapear encabezados a índices
    encabezados = [str(c).strip().lower() if c else '' for c in filas[0]]
    col_map = {h: i for i, h in enumerate(encabezados)}

    def get_cell(row, key, default=''):
        idx = col_map.get(key.lower())
        if idx is None or idx >= len(row):
            return default
        val = row[idx]
        if val is None:
            return default
        return str(val).strip()

    def get_float(row, key):
        s = get_cell(row, key, '')
        if not s:
            return None
        try:
            return float(s)
        except ValueError:
            return None

    # Precargar todos los equipos en memoria para mapeo por numero_serie
    all_equipos = session.exec(select(Equipo)).all()
    equipos_by_serie = {}
    for eq in all_equipos:
        if eq.numero_serie:
            equipos_by_serie[str(eq.numero_serie).strip()] = eq

    exitosos = 0
    actualizados = 0
    fallidos = 0
    errores = []

    for fila_idx, row in enumerate(filas[1:], start=2):
        # Saltar filas completamente vacías
        if not row or all(c is None or str(c).strip() == '' for c in row):
            continue

        try:
            proveedor_nombre = get_cell(row, 'proveedor_nombre')
            tipo_contrato = get_cell(row, 'tipo_contrato') or 'Otro'
            fecha_inicio_str = get_cell(row, 'fecha_inicio')
            fecha_fin_str = get_cell(row, 'fecha_fin')

            # Validar obligatorios
            if not proveedor_nombre:
                raise ValueError("proveedor_nombre es obligatorio")
            if not fecha_inicio_str or not fecha_fin_str:
                raise ValueError("fecha_inicio y fecha_fin son obligatorios")

            # Parsear fechas (acepta YYYY-MM-DD o DD/MM/YYYY)
            def parse_fecha(s):
                s = s.strip()
                for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%Y/%m/%d'):
                    try:
                        return datetime.strptime(s, fmt).date()
                    except ValueError:
                        continue
                raise ValueError(f"Formato de fecha no válido: {s}")

            f_inicio = parse_fecha(fecha_inicio_str)
            f_fin = parse_fecha(fecha_fin_str)
            if f_fin < f_inicio:
                raise ValueError("fecha_fin debe ser mayor o igual a fecha_inicio")

            # Validar enums (default si vacío)
            if tipo_contrato not in TIPOS_CONTRATO:
                tipo_contrato = 'Otro'

            periodicidad = get_cell(row, 'periodicidad_costo', 'Único') or 'Único'
            if periodicidad not in PERIODICIDADES:
                periodicidad = 'Único'

            moneda = get_cell(row, 'moneda', 'USD') or 'USD'
            if moneda not in MONEDAS:
                moneda = 'USD'

            costo_total = get_float(row, 'costo_total')
            costo_periodico = get_float(row, 'costo_periodico')

            # Resolver o crear proveedor
            proveedor = session.exec(
                select(Proveedor).where(Proveedor.nombre_empresa == proveedor_nombre)
            ).first()
            if not proveedor:
                proveedor = Proveedor(nombre_empresa=proveedor_nombre)
                session.add(proveedor)
                session.flush()
                session.refresh(proveedor)

            # Upsert: buscar contrato existente con mismo proveedor+tipo+fecha_inicio
            existente = session.exec(
                select(Contrato).where(
                    Contrato.proveedor_id == proveedor.id,
                    Contrato.tipo_contrato == tipo_contrato,
                    Contrato.fecha_inicio == datetime.combine(f_inicio, datetime.min.time())
                )
            ).first()

            # Datos del contrato
            datos = {
                'proveedor_id': proveedor.id,
                'tipo_contrato': tipo_contrato,
                'fecha_inicio': datetime.combine(f_inicio, datetime.min.time()),
                'fecha_fin': datetime.combine(f_fin, datetime.min.time()),
                'costo_total': costo_total,
                'costo_periodico': costo_periodico,
                'periodicidad_costo': periodicidad,
                'moneda': moneda,
                'cobertura_detalle': get_cell(row, 'cobertura_detalle') or None,
                'tiempo_respuesta': get_cell(row, 'tiempo_respuesta') or None,
                'horario_servicio': get_cell(row, 'horario_servicio') or None,
                'notas': get_cell(row, 'notas') or None,
            }

            # Equipos: separar por ';' y resolver por numero_serie
            equipos_series_str = get_cell(row, 'equipos_series')
            equipos_ids = []
            equipos_no_encontrados = []
            if equipos_series_str:
                for serie in [s.strip() for s in equipos_series_str.split(';') if s.strip()]:
                    eq = equipos_by_serie.get(serie)
                    if eq:
                        equipos_ids.append(eq.id)
                    else:
                        equipos_no_encontrados.append(serie)

            if existente:
                # Actualizar
                for k, v in datos.items():
                    setattr(existente, k, v)
                session.add(existente)
                session.flush()
                contrato_id = existente.id
                # Reasociar equipos: borrar y volver a crear
                session.exec(
                    select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato_id)
                ).all()  # selección solo para sincronizar
                # Eliminar asociaciones previas
                for ce in session.exec(select(ContratoEquipo).where(ContratoEquipo.contrato_id == contrato_id)).all():
                    session.delete(ce)
                session.flush()
                for eq_id in equipos_ids:
                    session.add(ContratoEquipo(contrato_id=contrato_id, equipo_id=eq_id))
                actualizados += 1
            else:
                # Crear nuevo
                nuevo = Contrato(**datos)
                session.add(nuevo)
                session.flush()
                for eq_id in equipos_ids:
                    session.add(ContratoEquipo(contrato_id=nuevo.id, equipo_id=eq_id))
                exitosos += 1

            session.commit()

            # Reportar series no encontradas como advertencia (no falla la fila)
            if equipos_no_encontrados:
                errores.append({
                    'fila': fila_idx,
                    'nombre': f"{proveedor_nombre} - {tipo_contrato}",
                    'errores': [f"Series no encontradas (ignoradas): {', '.join(equipos_no_encontrados)}"]
                })

        except Exception as e:
            fallidos += 1
            errores.append({
                'fila': fila_idx,
                'nombre': get_cell(row, 'proveedor_nombre') or f'fila {fila_idx}',
                'errores': [str(e)]
            })
            session.rollback()

    return {
        'exitosos': exitosos,
        'actualizados': actualizados,
        'fallidos': fallidos,
        'total_procesados': exitosos + actualizados + fallidos,
        'errores': errores
    }

