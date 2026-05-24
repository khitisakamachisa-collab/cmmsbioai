from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from database import get_session
from models.equipos import Equipo
from models.estados import EstadoEquipo
from models.users import Usuario # Asegúrate de que esta ruta sea correcta
from schemas.equipo import EquipoCreate, EquipoRead, EquipoUpdate
from datetime import date, datetime
from io import BytesIO
import openpyxl

router = APIRouter(prefix="/equipos", tags=["Equipos"])

# NUEVO: Endpoint para listar técnicos (usuarios)
@router.get("/tecnicos")
def listar_tecnicos(session: Session = Depends(get_session)):
    tecnicos = session.exec(select(Usuario)).all()
    # Devolvemos solo lo necesario para el selector
    return [{"id": t.id, "username": t.username} for t in tecnicos]

@router.post("/", response_model=EquipoRead)
def crear_equipo(equipo: EquipoCreate, session: Session = Depends(get_session)):
    existe = session.exec(select(Equipo).where(Equipo.numero_serie == equipo.numero_serie)).first()
    if existe:
        raise HTTPException(status_code=400, detail="El número de serie ya está registrado")
    
    db_equipo = Equipo(**equipo.model_dump())
    session.add(db_equipo)
    session.commit()
    session.refresh(db_equipo)
    return db_equipo

@router.get("/", response_model=list[EquipoRead])
def listar_equipos(session: Session = Depends(get_session)):
    equipos = session.exec(select(Equipo)).all()
    return equipos

@router.put("/{equipo_id}", response_model=EquipoRead)
def actualizar_equipo(equipo_id: int, equipo_data: EquipoUpdate, session: Session = Depends(get_session)):
    db_equipo = session.get(Equipo, equipo_id)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    equipo_data_dict = equipo_data.model_dump(exclude_unset=True)
    for key, value in equipo_data_dict.items():
        setattr(db_equipo, key, value)
    
    session.add(db_equipo)
    session.commit()
    session.refresh(db_equipo)
    return db_equipo

@router.delete("/{equipo_id}")
def eliminar_equipo(equipo_id: int, session: Session = Depends(get_session)):
    db_equipo = session.get(Equipo, equipo_id)
    if not db_equipo:
        raise HTTPException(status_code=404, detail="Equipo no encontrado")
    
    session.delete(db_equipo)
    session.commit()
    return {"ok": True, "message": "Equipo eliminado"}

# ---------------------------------------------------------
# ENDPOINT CORREGIDO: LEE DE LA BASE DE DATOS
# ---------------------------------------------------------
@router.get("/estados")
def listar_estados(session: Session = Depends(get_session)):
    # Usa EstadoEquipo aquí
    estados = session.exec(select(EstadoEquipo)).all()
    return estados

# ... imports existentes ...

# Endpoint para CREAR un nuevo estado (Solo para administración inicial)
@router.post("/estados")
def crear_estado(nombre_estado: str, session: Session = Depends(get_session)):
    # Verificar si ya existe
    existe = session.exec(select(EstadoEquipo).where(EstadoEquipo.nombre_estado == nombre_estado)).first()
    if existe:
        raise HTTPException(status_code=400, detail="El estado ya existe")
    # Usar el modelo correcto: EstadoEquipo (no Estado que no existe)
    nuevo_estado = EstadoEquipo(nombre_estado=nombre_estado)
    session.add(nuevo_estado)
    session.commit()
    session.refresh(nuevo_estado)
    return nuevo_estado


# ---------------------------------------------------------
# ENDPOINT: IMPORTAR EQUIPOS DESDE EXCEL
# ---------------------------------------------------------
@router.post("/import-excel")
async def importar_equipos_excel(file: UploadFile = File(...), session: Session = Depends(get_session)):
    """
    Importa equipos desde un archivo Excel (.xlsx).
    Columnas esperadas (encabezado en fila 1):
      nombre_corto, modelo, numero_serie, marca, fecha_adquisicion,
      ubicacion_actual, estado, proveedor_principal, registro_sanitario_bolivia,
      descripcion, calibracion_proxima, responsable_username
    
    - Los campos marcados con * son obligatorios: modelo, numero_serie, marca, fecha_adquisicion
    - Si numero_serie ya existe, se ACTUALIZA el registro (upsert)
    - El campo 'estado' se resuelve por nombre (debe existir en EstadoEquipo)
    - 'responsable_username' se resuelve por username del usuario
    """
    # Validar extensión
    if not file.filename or not file.filename.lower().endswith('.xlsx'):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos .xlsx")
    
    # Leer el archivo
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:  # 5MB límite
        raise HTTPException(status_code=400, detail="El archivo no debe superar 5MB")
    
    try:
        wb = openpyxl.load_workbook(BytesIO(contents), read_only=True, data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error al leer el archivo Excel: {str(e)}")
    
    # Obtener estados y usuarios para resolver nombres
    estados_db = session.exec(select(EstadoEquipo)).all()
    estado_map = {e.nombre_estado.strip().lower(): e for e in estados_db}
    
    usuarios_db = session.exec(select(Usuario)).all()
    usuario_map = {u.username.strip().lower(): u for u in usuarios_db}
    
    # Columnas esperadas (en orden)
    COLUMNAS = [
        'nombre_corto', 'modelo', 'numero_serie', 'marca', 'fecha_adquisicion',
        'ubicacion_actual', 'estado', 'proveedor_principal', 'registro_sanitario_bolivia',
        'descripcion', 'calibracion_proxima', 'responsable_username'
    ]
    OBLIGATORIAS = {'modelo', 'numero_serie', 'marca', 'fecha_adquisicion'}
    
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
    
    # Leer encabezados (fila 1)
    filas = list(ws.iter_rows(values_only=True))
    if len(filas) < 2:
        raise HTTPException(status_code=400, detail="El archivo está vacío o solo tiene encabezados")
    
    encabezados_leidos = [str(c).strip().lower() if c else '' for c in filas[0]]
    
    # Mapear columnas leídas a nuestras columnas esperadas
    col_index = {}
    for i, h in enumerate(encabezados_leidos):
        if h in COLUMNAS:
            col_index[h] = i
    
    # Verificar que las obligatorias estén presentes
    faltantes = OBLIGATORIAS - set(col_index.keys())
    if faltantes:
        raise HTTPException(
            status_code=400, 
            detail=f"Faltan columnas obligatorias: {', '.join(faltantes)}. Encabezados encontrados: {', '.join(encabezados_leidos)}"
        )
    
    # Procesar filas
    exitosos = 0
    actualizados = 0
    fallidos = []
    
    for fila_num, fila in enumerate(filas[1:], start=2):  # fila 2 en adelante
        try:
            # Extraer valores de la fila
            def get_val(col_name):
                idx = col_index.get(col_name)
                if idx is None or idx >= len(fila):
                    return None
                val = fila[idx]
                return str(val).strip() if val is not None else None
            
            # Validar obligatorios
            errores_fila = []
            for col in OBLIGATORIAS:
                val = get_val(col)
                if not val:
                    errores_fila.append(f"'{col}' es obligatorio")
            
            if errores_fila:
                fallidos.append({
                    "fila": fila_num,
                    "numero_serie": get_val('numero_serie') or 'N/A',
                    "errores": errores_fila
                })
                continue
            
            # Parsear fecha_adquisicion
            fecha_adq_str = get_val('fecha_adquisicion')
            try:
                fecha_adq = _parse_date(fecha_adq_str)
            except ValueError:
                fallidos.append({
                    "fila": fila_num,
                    "numero_serie": get_val('numero_serie') or 'N/A',
                    "errores": [f"fecha_adquisicion inválida: '{fecha_adq_str}'. Use formato YYYY-MM-DD"]
                })
                continue
            
            # Parsear calibracion_proxima (opcional)
            cal_str = get_val('calibracion_proxima')
            fecha_cal = None
            if cal_str:
                try:
                    fecha_cal = _parse_date(cal_str)
                except ValueError:
                    # No es fatal, solo se ignora
                    pass
            
            # Resolver estado_id
            estado_id = 1  # Default
            estado_str = get_val('estado')
            if estado_str:
                estado_key = estado_str.strip().lower()
                if estado_key in estado_map:
                    estado_id = estado_map[estado_key].id
                else:
                    # No crear automáticamente, usar default y advertir
                    errores_fila.append(f"Estado '{estado_str}' no encontrado, se usará el estado por defecto")
            
            # Resolver responsable_tecnico_id
            responsable_id = None
            resp_str = get_val('responsable_username')
            if resp_str:
                resp_key = resp_str.strip().lower()
                if resp_key in usuario_map:
                    responsable_id = usuario_map[resp_key].id
                else:
                    errores_fila.append(f"Usuario '{resp_str}' no encontrado, se asignará sin responsable")
            
            # Verificar si ya existe (por numero_serie)
            num_serie = get_val('numero_serie')
            equipo_existente = session.exec(
                select(Equipo).where(Equipo.numero_serie == num_serie)
            ).first()
            
            if equipo_existente:
                # ACTUALIZAR (upsert)
                equipo_existente.nombre_corto = get_val('nombre_corto') or equipo_existente.nombre_corto
                equipo_existente.modelo = get_val('modelo') or equipo_existente.modelo
                equipo_existente.marca = get_val('marca') or equipo_existente.marca
                equipo_existente.fecha_adquisicion = fecha_adq
                equipo_existente.ubicacion_actual = get_val('ubicacion_actual') or equipo_existente.ubicacion_actual
                equipo_existente.estado_id = estado_id
                equipo_existente.proveedor_principal = get_val('proveedor_principal') or equipo_existente.proveedor_principal
                equipo_existente.registro_sanitario_bolivia = get_val('registro_sanitario_bolivia') or equipo_existente.registro_sanitario_bolivia
                equipo_existente.descripcion = get_val('descripcion') or equipo_existente.descripcion
                equipo_existente.calibracion_proxima = fecha_cal or equipo_existente.calibracion_proxima
                equipo_existente.responsable_tecnico_id = responsable_id or equipo_existente.responsable_tecnico_id
                session.add(equipo_existente)
                actualizados += 1
            else:
                # CREAR nuevo
                nuevo = Equipo(
                    nombre_corto=get_val('nombre_corto'),
                    modelo=get_val('modelo'),
                    numero_serie=num_serie,
                    marca=get_val('marca'),
                    fecha_adquisicion=fecha_adq,
                    ubicacion_actual=get_val('ubicacion_actual'),
                    estado_id=estado_id,
                    proveedor_principal=get_val('proveedor_principal'),
                    registro_sanitario_bolivia=get_val('registro_sanitario_bolivia'),
                    descripcion=get_val('descripcion'),
                    calibracion_proxima=fecha_cal,
                    responsable_tecnico_id=responsable_id
                )
                session.add(nuevo)
                exitosos += 1
            
            # Si hubo advertencias pero se procesó, las reportamos
            if errores_fila and not equipo_existente:
                # Para registros nuevos con advertencias, igual se contaron como exitosos
                pass
                
        except Exception as e:
            fallidos.append({
                "fila": fila_num,
                "numero_serie": get_val('numero_serie') if 'num_serie' in dir() else 'N/A',
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


def _parse_date(val: str) -> date:
    """Parsea una fecha en formato YYYY-MM-DD o DD/MM/YYYY"""
    val = val.strip()
    # Intentar YYYY-MM-DD
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%Y/%m/%d', '%d-%m-%Y'):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"No se pudo parsear la fecha: '{val}'")


# ---------------------------------------------------------
# ENDPOINT: DESCARGAR PLANTILLA EXCEL DEMO
# ---------------------------------------------------------
@router.get("/plantilla-excel")
def descargar_plantilla_excel(session: Session = Depends(get_session)):
    """
    Genera y descarga un archivo Excel plantilla con datos de ejemplo
    de un biolaboratorio, listo para ser importado.
    """
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Equipos CMMS-BioAI"
    
    # Encabezados
    encabezados = [
        'nombre_corto', 'modelo', 'numero_serie', 'marca', 'fecha_adquisicion',
        'ubicacion_actual', 'estado', 'proveedor_principal', 'registro_sanitario_bolivia',
        'descripcion', 'calibracion_proxima', 'responsable_username'
    ]
    ws.append(encabezados)
    
    # Estilo para encabezados
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
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
    
    # Datos de ejemplo - Equipos de biolaboratorio
    datos_demo = [
        ["Microscopio Olympus CX23", "CX23", "MIC-OLY-001", "Olympus", "2023-03-15",
         "Lab. Microbiología", "Operativo", "Olympus Bolivia", "RS-BOL-2023-001",
         "Microscopio binocular para microbiología clínica", "2025-03-15", ""],
        
        ["Centrífuga Eppendorf 5424", "5424", "CEN-EPP-002", "Eppendorf", "2022-07-20",
         "Lab. Hematología", "Operativo", "Eppendorf Latam", "RS-BOL-2022-045",
         "Centrífuga de mesa 24 tubos, rotor FA-45-24-11", "2024-07-20", ""],
        
        ["Autoclave Steris Amsco 3043", "3043", "AUT-STR-003", "Steris", "2021-01-10",
         "Central de Esterilización", "Operativo", "Steris Corporation", "",
         "Autoclave hospitalaria vertical, 400L capacidad", "2025-01-10", ""],
        
        ["Analizador Bioquímico Cobas c311", "c311", "ANA-ROC-004", "Roche", "2023-06-01",
         "Lab. Bioquímica", "Operativo", "Roche Diagnostics Bolivia", "RS-BOL-2023-089",
         "Analizador bioquímico automatizado, 120 pruebas/h", "2025-06-01", ""],
        
        ["Monitor de Signos Vitales Mindray", "uMEC10", "MON-MIN-005", "Mindray", "2022-11-05",
         "UCI Box 3", "En Mantenimiento", "Mindray Bolivia", "RS-BOL-2022-112",
         "Monitor multiparámetro con SpO2, ECG, NIBP, Temp", "2024-11-05", ""],
        
        ["Electrocardiógrafo GE MAC 2000", "MAC 2000", "ELE-GEE-006", "GE Healthcare", "2020-09-15",
         "Cardiología", "Operativo", "GE Healthcare Latam", "RS-BOL-2020-034",
         "ECG 12 derivaciones con interpretación", "2024-09-15", ""],
        
        ["Espectrofotómetro Thermo Genesys 30", "Genesys 30", "ESP-THM-007", "Thermo Fisher", "2023-02-28",
         "Lab. Investigación", "Operativo", "Thermo Fisher Scientific", "",
         "Espectrofotómetro visible, rango 325-1100nm", "2025-02-28", ""],
        
        ["Balanza Analítica Sartorius", "Quintix 224", "BAL-SAR-008", "Sartorius", "2021-08-12",
         "Lab. Control Calidad", "Operativo", "Sartorius Bolivia", "",
         "Balanza analítica 220g / 0.1mg, calibración interna", "2024-08-12", ""],
        
        ["Desfibrilador Zoll R Series", "R Series", "DES-ZOL-009", "Zoll", "2022-04-18",
         "Emergencias", "Operativo", "Zoll Medical", "RS-BOL-2022-078",
         "Desfibrilador biphasic con monitor y marcapasos", "2025-04-18", ""],
        
        ["Incubadora CO2 Thermo Heracell", "Heracell VIOS 160i", "INC-THM-010", "Thermo Fisher", "2023-09-01",
         "Lab. Cultivo Celular", "Fuera de Servicio", "Thermo Fisher Scientific", "",
         "Incubadora CO2 con control de O2, 170L", "2025-09-01", ""],
        
        ["Bomba de Infusión B. Braun", "Infusomat Space", "BOM-BRA-011", "B. Braun", "2022-12-10",
         "UCI Box 1", "Operativo", "B. Braun Bolivia", "RS-BOL-2022-156",
         "Bomba de infusión volumétrica con modo PCA", "2024-12-10", ""],
        
        ["Termociclador Bio-Rad T100", "T100", "TER-BIO-012", "Bio-Rad", "2021-05-22",
         "Lab. Biología Molecular", "Operativo", "Bio-Rad Latam", "",
         "Termociclador PCR 96 pocillos, gradiente", "2025-05-22", ""],
        
        ["Respirador Dräger Evita V500", "Evita V500", "RES-DRA-013", "Dräger", "2023-01-15",
         "UCI Box 5", "En Mantenimiento", "Dräger Bolivia", "RS-BOL-2023-003",
         "Ventilador de UCI con modos avanzados", "2025-01-15", ""],
        
        ["Pipeta Automática Hamilton", "Microlab STARlet", "PIP-HAM-014", "Hamilton", "2022-03-08",
         "Lab. Automatización", "Operativo", "Hamilton Company", "",
         "Pipeta automatizada 8 canales, 1-1000μL", "2025-03-08", ""],
        
        ["Cámara de Flujo Laminar Esco", "A2 Class", "CAM-ESC-015", "Esco", "2020-06-25",
         "Lab. Microbiología", "Operativo", "Esco Technologies", "",
         "Cabina de seguridad biológica Clase II Tipo A2", "2024-06-25", ""],
    ]
    
    # Estilo para datos
    data_align = Alignment(vertical="center", wrap_text=True)
    
    for fila_data in datos_demo:
        ws.append(fila_data)
    
    # Aplicar bordes y alineación a datos
    for row in ws.iter_rows(min_row=2, max_row=ws.max_row, min_col=1, max_col=len(encabezados)):
        for cell in row:
            cell.border = thin_border
            cell.alignment = data_align
    
    # Ajustar anchos de columna
    anchos = [28, 18, 18, 18, 18, 24, 18, 24, 24, 40, 18, 22]
    for i, ancho in enumerate(anchos, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = ancho
    
    # Crear segunda hoja con instrucciones
    ws2 = wb.create_sheet("Instrucciones")
    instrucciones = [
        ["INSTRUCCIONES PARA IMPORTAR EQUIPOS"],
        [""],
        ["1. Los campos marcados como obligatorios (*) no pueden estar vacíos:"],
        ["   - modelo *", "modelo del equipo"],
        ["   - numero_serie *", "debe ser único, si ya existe se ACTUALIZARÁ el registro"],
        ["   - marca *", "fabricante del equipo"],
        ["   - fecha_adquisicion *", "formato: YYYY-MM-DD o DD/MM/YYYY"],
        [""],
        ["2. Campo 'estado': debe coincidir con un estado existente en el sistema."],
        ["   Estados típicos: Operativo, En Mantenimiento, Fuera de Servicio"],
        ["   Si no coincide, se usará el estado por defecto."],
        [""],
        ["3. Campo 'responsable_username': username del usuario registrado en el sistema."],
        ["   Si no coincide, se asignará sin responsable."],
        [""],
        ["4. Campo 'calibracion_proxima': fecha en formato YYYY-MM-DD (opcional)."],
        [""],
        ["5. Límite de archivo: 5MB (~1000 equipos). Solo archivos .xlsx."],
        [""],
        ["6. Si un 'numero_serie' ya existe, el equipo se ACTUALIZARÁ con los nuevos datos."],
        [""],
        ["7. Puede eliminar los datos de ejemplo y usar sus propios datos."],
        ["   Mantenga los encabezados de columna en la fila 1."],
    ]
    for row in instrucciones:
        ws2.append(row)
    ws2.column_dimensions['A'].width = 55
    ws2.column_dimensions['B'].width = 45
    
    # Guardar en memoria y retornar
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    wb.close()
    
    from datetime import datetime as dt
    filename = f"CMMS-BioAI_Plantilla_Equipos_{dt.now().strftime('%Y%m%d')}.xlsx"
    
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )