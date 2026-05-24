from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from database import get_session
from models.repuestos import Repuesto
from schemas.repuesto import RepuestoCreate, RepuestoRead, RepuestoUpdate
from io import BytesIO
from datetime import datetime as dt
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

router = APIRouter(prefix="/repuestos", tags=["Inventario"])

# ============================================================
# RUTAS ESTÁTICAS (deben ir ANTES de /{rep_id})
# ============================================================

@router.post("/", response_model=RepuestoRead)
def crear_repuesto(repuesto: RepuestoCreate, session: Session = Depends(get_session)):
    db_rep = Repuesto(**repuesto.model_dump())
    session.add(db_rep)
    session.commit()
    session.refresh(db_rep)
    return db_rep

@router.get("/", response_model=list[RepuestoRead])
def listar_repuestos(session: Session = Depends(get_session)):
    repuestos = session.exec(select(Repuesto)).all()
    return repuestos


# ---------------------------------------------------------
# ENDPOINT: DESCARGAR PLANTILLA EXCEL DEMO
# ---------------------------------------------------------
@router.get("/plantilla-excel")
def descargar_plantilla_excel(session: Session = Depends(get_session)):
    """
    Genera y descarga un archivo Excel plantilla con datos de ejemplo
    de repuestos para biolaboratorio.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Repuestos CMMS-BioAI"
    
    encabezados = [
        'nombre_repuesto', 'numero_material', 'descripcion',
        'cantidad_disponible', 'unidad_medida', 'ubicacion_almacen', 'nivel_stock_minimo'
    ]
    ws.append(encabezados)
    
    # Estilo para encabezados
    header_font = Font(bold=True, color="FFFFFF", size=11)
    header_fill = PatternFill(start_color="2C3E50", end_color="2C3E50", fill_type="solid")
    header_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    thin_border = Border(
        left=Side(style='thin'), right=Side(style='thin'),
        top=Side(style='thin'), bottom=Side(style='thin')
    )
    
    for col_num, _ in enumerate(encabezados, 1):
        cell = ws.cell(row=1, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border
    
    # Datos de ejemplo - Repuestos de biolaboratorio
    datos_demo = [
        ["Filtro HEPA para cabina de flujo", "FLT-HEP-001", "Filtro HEPA 99.97% 0.3μm para cabina Esco A2", 3, "unidad", "Almacén B - Estante 1", 2],
        ["Lámpara UV para autoclave", "LMP-UV-002", "Lámpara germicida UV 254nm Steris", 5, "unidad", "Almacén B - Estante 1", 2],
        ["Electrodo pH recalculado", "ELC-PH-003", "Electrodo de pH combinado para analizadores", 4, "unidad", "Lab. Bioquímica", 2],
        ["Tubos de ensayo 16x100mm", "TUB-16004", "Tubos de vidrio borosilicato, paquete x100", 25, "paquete", "Almacén A - Estante 3", 10],
        ["Reactivos panel bioquímico", "RCT-BIO-005", "Kit de reactivos Cobas c311 panel completo", 2, "kit", "Refrigerador Lab 2°C-8°C", 1],
        ["Filtro de aire compresor", "FLT-AIR-006", "Filtro de línea para compresor dental/medico", 6, "unidad", "Almacén B - Estante 2", 3],
        ["Cable ECG 12 derivaciones", "CBL-ECG-007", "Cable paciente 12-lead para GE MAC 2000", 3, "unidad", "Almacén C - Gabinete 1", 2],
        ["Sensor SpO2 dedo", "SNR-SPO-008", "Sensor pulsioximetría dedo adulto Mindray", 4, "unidad", "UCI - Armario suministros", 2],
        ["Papel térmico monitor", "PPL-TRM-009", "Papel térmico 112mm para monitor de signos vitales", 8, "rollo", "Almacén A - Estante 5", 3],
        ["Batería interna desfibrilador", "BAT-DEF-010", "Batería recargable Zoll R Series 14.4V", 2, "unidad", "Emergencias - Armario", 1],
        ["Goma/pistón pipeta", "GOM-PIP-011", "Pistón de goma para pipeta Hamilton 100-1000μL", 10, "unidad", "Lab. Automatización", 5],
        ["Sellador de tapa incubadora", "SLR-INC-012", "Junta de goma puerta incubadora Thermo Heracell", 2, "unidad", "Almacén B - Estante 4", 1],
        ["Fluorescente microscopio", "LMP-MIC-013", "Lámpara halógena 6V 30W para Olympus CX23", 3, "unidad", "Almacén B - Estante 1", 2],
        ["Reactivos hematología", "RCT-HEM-014", "Kit diluyente/limpiador analizador hematológico", 3, "kit", "Refrigerador Lab 2°C-8°C", 1],
        ["Filtro CO2 incubadora", "FLT-CO2-015", "Filtro HEPA para incubadora CO2 Thermo", 2, "unidad", "Almacén B - Estante 3", 1],
        ["Aceite bomba vacío", "ACE-VAC-016", "Aceite para bomba de vacío Autoclave Steris 1L", 4, "litro", "Almacén A - Estante 2", 2],
        ["Manguera silicona", "MNG-SIL-017", "Tubo silicona 8mm ID para bombas de infusión", 5, "metro", "Almacén C - Estante 1", 3],
        ["Electrodo ECG desechable", "ELC-ECG-018", "Electrodos Ag/Cl adulto paquete x50", 20, "paquete", "UCI - Armario suministros", 10],
        ["Papel filtro centrífuga", "PPL-CEN-019", "Filtro de carbón para Eppendorf 5424", 6, "unidad", "Lab. Hematología", 3],
        ["Solución calibración pH", "SLC-PH-020", "Solución buffer pH 4.01 / 7.00 / 10.01 set", 5, "kit", "Lab. Control Calidad", 2],
    ]
    
    data_align = Alignment(vertical="center", wrap_text=True)
    
    for fila_data in datos_demo:
        ws.append(fila_data)
    
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(encabezados)):
        for cell in row:
            cell.border = thin_border
            cell.alignment = data_align
    
    anchos = [35, 18, 50, 20, 14, 28, 20]
    for i, ancho in enumerate(anchos, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = ancho
    
    # Hoja de instrucciones
    ws2 = wb.create_sheet("Instrucciones")
    instrucciones = [
        ["INSTRUCCIONES PARA IMPORTAR REPUESTOS"],
        [""],
        ["1. Los campos marcados como obligatorios (*) no pueden estar vacíos:"],
        ["   - nombre_repuesto *", "nombre del repuesto o insumo"],
        ["   - cantidad_disponible *", "número entero (ej: 5)"],
        [""],
        ["2. Campo 'numero_material': código del repuesto. Si ya existe, se ACTUALIZARÁ."],
        ["   Si no existe numero_material, se busca por nombre_repuesto."],
        [""],
        ["3. Campo 'nivel_stock_minimo': entero. Cantidad mínima antes de alerta."],
        ["   Si no se especifica, no se generará alerta de stock bajo."],
        [""],
        ["4. Campo 'unidad_medida': unidad, par, metro, litro, kit, paquete, rollo, etc."],
        ["   Si se deja vacío, se usará 'unidad' por defecto."],
        [""],
        ["5. Límite de archivo: 5MB. Solo archivos .xlsx."],
        [""],
        ["6. Puede eliminar los datos de ejemplo y usar sus propios datos."],
        ["   Mantenga los encabezados de columna en la fila 1."],
    ]
    for row in instrucciones:
        ws2.append(row)
    ws2.column_dimensions['A'].width = 55
    ws2.column_dimensions['B'].width = 45
    
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    wb.close()
    
    filename = f"CMMS-BioAI_Plantilla_Repuestos_{dt.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


# ---------------------------------------------------------
# ENDPOINT: IMPORTAR REPUESTOS DESDE EXCEL
# ---------------------------------------------------------
@router.post("/import-excel")
async def importar_repuestos_excel(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    Importa repuestos desde un archivo Excel (.xlsx).
    Columnas esperadas (encabezado en fila 1):
      nombre_repuesto *, numero_material, descripcion,
      cantidad_disponible *, unidad_medida, ubicacion_almacen, nivel_stock_minimo
    
    - Campo obligatorio: nombre_repuesto, cantidad_disponible
    - Si numero_material ya existe, se ACTUALIZA el registro (upsert)
    """
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx")
    
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="El archivo no debe superar 5MB")
    
    try:
        wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo Excel: {str(e)}")
    
    COLUMNAS = [
        'nombre_repuesto', 'numero_material', 'descripcion',
        'cantidad_disponible', 'unidad_medida', 'ubicacion_almacen', 'nivel_stock_minimo'
    ]
    OBLIGATORIAS = {'nombre_repuesto', 'cantidad_disponible'}
    
    # Buscar la hoja que contiene los encabezados esperados
    # (si el usuario abrió el archivo en Excel, la hoja activa puede ser "Instrucciones")
    ws = None
    for sheet in wb.worksheets:
        filas_tmp = list(sheet.iter_rows(values_only=True))
        if filas_tmp:
            enc_tmp = [str(c).strip().lower() if c else '' for c in filas_tmp[0]]
            if OBLIGATORIAS.issubset(set(enc_tmp)):
                ws = sheet
                break
    
    if ws is None:
        # Fallback: usar la primera hoja
        ws = wb.worksheets[0]
    
    filas = list(ws.iter_rows(values_only=True))
    if len(filas) < 2:
        raise HTTPException(status_code=400, detail="El archivo está vacío o solo tiene encabezados")
    
    encabezados_leidos = [str(c).strip().lower() if c else '' for c in filas[0]]
    
    col_index = {}
    for i, h in enumerate(encabezados_leidos):
        if h in COLUMNAS:
            col_index[h] = i
    
    faltantes = OBLIGATORIAS - set(col_index.keys())
    if faltantes:
        raise HTTPException(
            status_code=400,
            detail=f"Faltan columnas obligatorias: {', '.join(faltantes)}. Encabezados encontrados: {', '.join(encabezados_leidos)}"
        )
    
    exitosos = 0
    actualizados = 0
    fallidos = []
    
    for fila_num, fila in enumerate(filas[1:], start=2):
        try:
            def get_val(col_name):
                idx = col_index.get(col_name)
                if idx is None or idx >= len(fila):
                    return None
                val = fila[idx]
                return str(val).strip() if val is not None else None
            
            errores_fila = []
            for col in OBLIGATORIAS:
                val = get_val(col)
                if not val:
                    errores_fila.append(f"'{col}' es obligatorio")
            
            if errores_fila:
                fallidos.append({
                    "fila": fila_num,
                    "nombre": get_val('nombre_repuesto') or 'N/A',
                    "errores": errores_fila
                })
                continue
            
            # Parsear cantidad_disponible
            try:
                cantidad = int(float(get_val('cantidad_disponible')))
                if cantidad < 0:
                    raise ValueError()
            except (ValueError, TypeError):
                fallidos.append({
                    "fila": fila_num,
                    "nombre": get_val('nombre_repuesto') or 'N/A',
                    "errores": ["cantidad_disponible debe ser un número entero positivo"]
                })
                continue
            
            # Parsear nivel_stock_minimo (opcional)
            stock_min = None
            stock_str = get_val('nivel_stock_minimo')
            if stock_str:
                try:
                    stock_min = int(float(stock_str))
                except (ValueError, TypeError):
                    pass  # No es fatal, se ignora
            
            unidad = get_val('unidad_medida') or 'unidad'
            
            # Verificar si ya existe (por numero_material o nombre)
            num_mat = get_val('numero_material')
            rep_existente = None
            
            if num_mat:
                rep_existente = session.exec(
                    select(Repuesto).where(Repuesto.numero_material == num_mat)
                ).first()
            
            if not rep_existente:
                # También buscar por nombre como fallback
                nombre = get_val('nombre_repuesto')
                rep_existente = session.exec(
                    select(Repuesto).where(Repuesto.nombre_repuesto == nombre)
                ).first()
            
            if rep_existente:
                # ACTUALIZAR
                rep_existente.nombre_repuesto = get_val('nombre_repuesto') or rep_existente.nombre_repuesto
                rep_existente.numero_material = num_mat or rep_existente.numero_material
                rep_existente.descripcion = get_val('descripcion') or rep_existente.descripcion
                rep_existente.cantidad_disponible = cantidad
                rep_existente.unidad_medida = unidad
                rep_existente.ubicacion_almacen = get_val('ubicacion_almacen') or rep_existente.ubicacion_almacen
                rep_existente.nivel_stock_minimo = stock_min if stock_min is not None else rep_existente.nivel_stock_minimo
                session.add(rep_existente)
                actualizados += 1
            else:
                # CREAR nuevo
                nuevo = Repuesto(
                    nombre_repuesto=get_val('nombre_repuesto'),
                    numero_material=num_mat,
                    descripcion=get_val('descripcion'),
                    cantidad_disponible=cantidad,
                    unidad_medida=unidad,
                    ubicacion_almacen=get_val('ubicacion_almacen'),
                    nivel_stock_minimo=stock_min
                )
                session.add(nuevo)
                exitosos += 1
                
        except Exception as e:
            fallidos.append({
                "fila": fila_num,
                "nombre": get_val('nombre_repuesto') if col_index.get('nombre_repuesto') is not None else 'N/A',
                "errores": [str(e)]
            })
    
    session.commit()
    wb.close()
    
    return {
        "exitosos": exitosos,
        "actualizados": actualizados,
        "fallidos": len(fallidos),
        "total_procesados": exitosos + actualizados + len(fallidos),
        "errores": fallidos
    }


# ============================================================
# RUTAS DINÁMICAS (van DESPUÉS de las estáticas)
# ============================================================

@router.get("/{rep_id}", response_model=RepuestoRead)
def obtener_repuesto(rep_id: int, session: Session = Depends(get_session)):
    db_rep = session.get(Repuesto, rep_id)
    if not db_rep:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    return db_rep


@router.put("/{rep_id}", response_model=RepuestoRead)
def actualizar_repuesto(
    rep_id: int,
    datos: RepuestoUpdate,
    session: Session = Depends(get_session),
):
    db_rep = session.get(Repuesto, rep_id)
    if not db_rep:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    for key, value in datos.model_dump(exclude_unset=True).items():
        setattr(db_rep, key, value)
    session.add(db_rep)
    session.commit()
    session.refresh(db_rep)
    return db_rep


@router.delete("/{rep_id}")
def eliminar_repuesto(rep_id: int, session: Session = Depends(get_session)):
    db_rep = session.get(Repuesto, rep_id)
    if not db_rep:
        raise HTTPException(status_code=404, detail="Repuesto no encontrado")
    session.delete(db_rep)
    session.commit()
    return {"ok": True, "message": "Repuesto eliminado"}
