"""
Endpoints CRUD para Contratos - RF12 v0.9.2
v0.9.24: agregado POST /import-excel
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import Session, select
from datetime import datetime, date
from pathlib import Path
from io import BytesIO, StringIO
import csv
from database import get_session
from models.contratos import Contrato, ContratoEquipo
from models.proveedores import Proveedor
from models.equipos import Equipo
from schemas.contrato import ContratoCreate, ContratoUpdate, ContratoRead, TIPOS_CONTRATO, PERIODICIDADES, MONEDAS

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
    return ['BOB']  # v0.9.15: solo Bolivianos para todo el proyecto


@router.get("/periodicidades/lista")
def listar_periodicidades():
    return ['Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual']


@router.post("/import-excel")
async def importar_contratos_excel(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    Importa contratos desde Excel (.xlsx) o CSV - v0.9.24.

    Columnas esperadas (encabezado en fila 1):
      proveedor_nombre, tipo_contrato, fecha_inicio, fecha_fin,
      costo_total, costo_periodico, periodicidad_costo, moneda,
      tiempo_respuesta, horario_servicio, cobertura_detalle, notas,
      equipos_series

    Reglas:
    - proveedor_nombre: se busca por nombre exacto (debe existir)
    - equipos_series: series separadas por ; (punto y coma)
    - moneda: forzado a BOB
    - tipo_contrato y periodicidad_costo: validados contra catálogos
    """
    try:
        import openpyxl
    except ImportError:
        raise HTTPException(status_code=500, detail="openpyxl no está instalado en el servidor")

    ext = Path(file.filename).suffix.lower() if file.filename else ''
    if ext not in ('.xlsx', '.csv'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx o .csv")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no debe superar 5MB")

    # Leer filas
    if ext == '.csv':
        try:
            text = contents.decode('utf-8-sig')
        except UnicodeDecodeError:
            text = contents.decode('latin-1')
        try:
            dialect = csv.Sniffer().sniff(text[:2048], delimiters=',;\t')
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(StringIO(text), dialect)
        filas = list(reader)
    else:
        wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
        ws = wb.active
        filas = []
        for row in ws.iter_rows(values_only=True):
            filas.append([str(c).strip() if c is not None else '' for c in row])

    if len(filas) < 2:
        raise HTTPException(status_code=400, detail="El archivo está vacío o solo tiene encabezados")

    encabezado = [c.strip().lower() for c in filas[0]]
    COLUMNAS = [
        'proveedor_nombre', 'tipo_contrato', 'fecha_inicio', 'fecha_fin',
        'costo_total', 'costo_periodico', 'periodicidad_costo', 'moneda',
        'tiempo_respuesta', 'horario_servicio', 'cobertura_detalle', 'notas',
        'equipos_series'
    ]
    col_map = {}
    for i, h in enumerate(encabezado):
        if h in COLUMNAS:
            col_map[h] = i

    # Validar columnas obligatorias
    for req in ('proveedor_nombre', 'tipo_contrato', 'fecha_inicio', 'fecha_fin'):
        if req not in col_map:
            raise HTTPException(status_code=400, detail=f"Falta columna obligatoria: {req}")

    creados = 0
    errores = []
    proveedores_cache = {}

    for row_idx, row in enumerate(filas[1:], start=2):
        if not row or all(c.strip() == '' for c in row):
            continue

        try:
            prov_nombre = row[col_map['proveedor_nombre']].strip()
            if not prov_nombre:
                errores.append(f"Fila {row_idx}: proveedor_nombre vacío")
                continue

            # Buscar proveedor
            if prov_nombre not in proveedores_cache:
                prov = session.exec(select(Proveedor).where(Proveedor.nombre_empresa == prov_nombre)).first()
                proveedores_cache[prov_nombre] = prov
            prov = proveedores_cache[prov_nombre]
            if not prov:
                errores.append(f"Fila {row_idx}: proveedor '{prov_nombre}' no encontrado")
                continue

            tipo = row[col_map['tipo_contrato']].strip()
            if tipo not in TIPOS_CONTRATO:
                errores.append(f"Fila {row_idx}: tipo_contrato '{tipo}' inválido")
                continue

            # Fechas
            fi_str = row[col_map['fecha_inicio']].strip()
            ff_str = row[col_map['fecha_fin']].strip()
            try:
                f_inicio = datetime.strptime(fi_str, '%Y-%m-%d').date()
            except ValueError:
                errores.append(f"Fila {row_idx}: fecha_inicio formato inválido (YYYY-MM-DD)")
                continue
            try:
                f_fin = datetime.strptime(ff_str, '%Y-%m-%d').date()
            except ValueError:
                errores.append(f"Fila {row_idx}: fecha_fin formato inválido (YYYY-MM-DD)")
                continue

            if f_fin < f_inicio:
                errores.append(f"Fila {row_idx}: fecha_fin anterior a fecha_inicio")
                continue

            # Opcionales
            costo_total = None
            if 'costo_total' in col_map and row[col_map['costo_total']].strip():
                try:
                    costo_total = float(row[col_map['costo_total']].strip())
                except ValueError:
                    pass

            costo_periodico = None
            if 'costo_periodico' in col_map and row[col_map['costo_periodico']].strip():
                try:
                    costo_periodico = float(row[col_map['costo_periodico']].strip())
                except ValueError:
                    pass

            periodicidad = 'Único'
            if 'periodicidad_costo' in col_map and row[col_map['periodicidad_costo']].strip():
                p = row[col_map['periodicidad_costo']].strip()
                if p in PERIODICIDADES:
                    periodicidad = p

            # Equipos por series
            equipos_ids = []
            if 'equipos_series' in col_map and row[col_map['equipos_series']].strip():
                series = [s.strip() for s in row[col_map['equipos_series']].split(';') if s.strip()]
                for serie in series:
                    eq = session.exec(select(Equipo).where(Equipo.numero_serie == serie)).first()
                    if eq:
                        equipos_ids.append(eq.id)

            nuevo = Contrato(
                proveedor_id=prov.id,
                tipo_contrato=tipo,
                fecha_inicio=datetime.combine(f_inicio, datetime.min.time()),
                fecha_fin=datetime.combine(f_fin, datetime.min.time()),
                costo_total=costo_total,
                costo_periodico=costo_periodico,
                periodicidad_costo=periodicidad,
                moneda='BOB',
                tiempo_respuesta=row[col_map['tiempo_respuesta']].strip() if 'tiempo_respuesta' in col_map else None,
                horario_servicio=row[col_map['horario_servicio']].strip() if 'horario_servicio' in col_map else None,
                cobertura_detalle=row[col_map['cobertura_detalle']].strip() if 'cobertura_detalle' in col_map else None,
                notas=row[col_map['notas']].strip() if 'notas' in col_map else None,
            )
            session.add(nuevo)
            session.flush()
            for eq_id in equipos_ids:
                session.add(ContratoEquipo(contrato_id=nuevo.id, equipo_id=eq_id))
            creados += 1

        except Exception as e:
            errores.append(f"Fila {row_idx}: {str(e)}")

    session.commit()

    return {
        "mensaje": f"Importación completada: {creados} contratos creados",
        "creados": creados,
        "errores": errores,
        "total_filas": len(filas) - 1
    }