# -*- coding: utf-8 -*-
"""
CMMS-BioAI — Generador de Dataset Sintético Ampliado (~220 OTs) para RF07
=========================================================================
Genera `dataset_sintetico_220_ot.xlsx` — historial sintético de ~6 meses con
distribución controlada de las banderas v2.1 — para alimentar los
experimentos de RF07 (PLN de descripciones de falla, RUL, XAI/SHAP).

Hojas del Excel:
    1. OTs Dataset v2.1     → MISMO formato de columnas que
                              demo_ordenes_trabajo_v21.xlsx (COLS_OT, 31 col)
    2. Equipos Dataset      → mismo formato que demo_equipos_v21.xlsx (16 col)
    3. Bitacora             → eventos creada/asignada/iniciada/pausada/
                              reanudada/resuelta/cancelada por OT
    4. Sintomas             → tabla 'symptoms' (origen Sistema/IA o Usuario)
    5. FeedbackPredictivo   → tabla 'feedback_predictivo' (ciclo H2)
    6. RepuestosOT          → repuestos por OT (Instalado / Instalado_Fallido)
    7. TextosPLN            → corpus etiquetado para el clasificador PLN

Restricciones respetadas:
  - NO modifica el motor de métricas ni duplica su lógica: solo genera datos
    coherentes con las REGLAS v2.1 (reincidencias <72 h REALES en las fechas,
    pausa declarada = espera de bitácora, exclusiones según clase).
  - NO importa a la BD: únicamente genera el Excel + reporte de verificación.
  - Determinista: semilla fija (RANDOM_SEED) → dataset reproducible.

Uso (Windows):
    cd D:\\cmmsbioai\\backend
    venv\\Scripts\\activate
    python generar_dataset_sintetico_220.py

Salidas (junto al script):
    dataset_sintetico_220_ot.xlsx
    verificacion_dataset_220.md
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
except ImportError:  # pragma: no cover
    print("❌ Falta openpyxl. Instálalo con: pip install openpyxl")
    raise SystemExit(1)

FMT_FECHA = "%Y-%m-%d %H:%M:%S"
RANDOM_SEED = 20261
rng = random.Random(RANDOM_SEED)

N_TOTAL = 220
SPAN_MESES = 6.0
COLCHON_FIN_MIN = 60          # la última OT resuelve ≥1 h antes de "ahora"

# ------------------------------------------------------------------
# Cuotas de CLASE (partición disjunta que suma exactamente 220)
# ------------------------------------------------------------------
CUOTAS = {
    "A_correctiva":   107,   # Usuario correctiva normal (104 completadas + 3 abiertas)
    "B_reincidencia": 11,    # ventana_garantia=True (5%)
    "C_sistema_ia":   22,    # tipo_origen_ot='Sistema/IA' (10%)
    "D_programado":   33,    # preventivos 'Programado' (15%)
    "E_cierre_admin": 11,    # cierre_administrativo=True (5%)
    "F_falsa_alarma": 18,    # cancelada Falsa_Alarma (8%)
    "G_error_usuario": 11,   # cancelada Error_Usuario (5%)
    "H_baja_equipo":   7,    # cancelada Baja_Equipo (3%)
}
N_PAUSA_TECNICA = 22          # en_pausa_tecnica=True (10%)
N_LOGISTICA = 33              # sub_estado_logistica en alguna variante (15%)
N_REPUESTOS = 42              # ~30% de las 140 correctivas (A+B+C)
N_REPUESTOS_FALLIDOS = 3      # ~5% de esos repuestos (reparación inefectiva)
FB_LABELS = ["Confirmada"] * 15 + ["Falsa_Alarma"] * 5 + ["Parcial"] * 2  # ~70/20/10

SUB_ESTADOS_LOGISTICA = ["Esperando_Cotización", "En_Proceso_Compra",
                         "En_Aduana", "En_Transito"]
HORAS_LOGISTICA = {"Esperando_Cotización": (24, 72), "En_Proceso_Compra": (48, 120),
                   "En_Aduana": (96, 200), "En_Transito": (72, 260)}
TECNICOS = ["M. Fernández", "C. Quisbert", "R. Salazar",
            "J. Cárdenas", "L. Villarroel", "S. Mendoza"]
COORDINADOR = "Coordinación CMMS"

# Columnas oficiales (idénticas a generar_demo_v21.py — formato importador)
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

# ============================================================
# EQUIPOS — 13 del seed enriquecido + 10 adicionales = 23
# peso = propensión relativa de fallas (equipos con alta frecuencia
# de fallas vs equipos con pocas fallas)
# ============================================================
EQUIPOS = [
    # nombre, tipo_equipo, criticidad, modelo, marca, ubicación, peso
    ("Bomba de Infusión 1",     "Bomba de Infusión",   "Alta",    "Alaris GP",      "BD",            "UCI Adultos",        1.5),
    ("Monitor Signos Vitales",  "Monitor",             "Alta",    "IPM-12",         "Mindray",       "Hospitalización",    1.0),
    ("Ecógrafo 4D",             "Ecógrafo",            "Alta",    "Voluson E8",     "GE Healthcare", "Ginecología",        1.0),
    ("Equipo de Rayos X",       "Rayos X",             "Alta",    "Digital FX-40",  "Siemens",       "Imagenología",       1.0),
    ("Máquina de Hemodiálisis", "Hemodiálisis",        "Crítica", "4008S",          "Fresenius",     "Unidad Renal",       1.5),
    ("Resonancia Magnética",    "Resonancia",          "Crítica", "Magnetom 1.5T",  "Siemens",       "Imagenología",       0.55),
    ("Ventilador Mecánico",     "Ventilador",          "Crítica", "V60",            "Philips",       "UCI Adultos",        1.5),
    ("Desfibrilador Zoll",      "Desfibrilador",       "Crítica", "R Series",       "Zoll",          "Emergencia",         1.0),
    ("Centrífuga Eppendorf",    "Centrífuga",          "Media",   "5810R",          "Eppendorf",     "Laboratorio",        0.55),
    ("Autoclave Steris",        "Autoclave",           "Alta",    "Amsco 3011",     "Steris",        "Esterilización",     1.0),
    ("Microscopio Olympus",     "Microscopio",         "Media",   "CX23",           "Olympus",       "Laboratorio",        0.55),
    ("Balanza Analítica",       "Balanza",             "Media",   "PA214",          "Ohaus",         "Laboratorio",        0.3),
    ("Electrocardiógrafo GE",   "Electrocardiógrafo",  "Alta",    "MAC 2000",       "GE Healthcare", "Cardiología",        1.0),
    # --- 10 equipos adicionales (variedad de frecuencia y criticidad) ---
    ("Ventilador Neonatal",        "Ventilador",          "Crítica", "VN500",         "Dräger",    "UCI Neonatal",       1.5),
    ("Bomba de Infusión 2",        "Bomba de Infusión",   "Alta",    "Alaris GP",     "BD",        "Pediatría",          1.5),
    ("Monitor Signos Vitales 2",   "Monitor",             "Alta",    "IPM-9800",      "Mindray",   "Quirófano 2",        1.0),
    ("Ultrasonido Portátil",       "Ecógrafo",            "Media",   "SiteScan A6",   "Mindray",   "Emergencia",         1.0),
    ("Lámpara Cielítica",          "Lámpara Quirúrgica",  "Alta",    "Polarem 700",   "Dr. Mach",  "Quirófano 1",        1.0),
    ("Electrobisturí",             "Electroquirúrgico",   "Crítica", "Force FX",      "Valleylab", "Quirófano 1",        1.0),
    ("Aspirador de Secreciones",   "Aspirador",           "Alta",    "Accuvac AD-1",  "ATMOS",     "UCI Adultos",        1.5),
    ("Estimulador Nervioso",       "Estimulador",         "Media",   "StimUp NS-2",   "Bistos",    "Rehabilitación",     0.55),
    ("Bomba de Nutrición Enteral", "Bomba de Nutrición",  "Media",   "Flocare 800",   "Nutricia",  "Hospitalización",    1.5),
    ("Cama Hospitalaria Eléctrica","Cama Hospitalaria",   "Baja",    "Multicare 200", "Linet",     "Hospitalización",    0.3),
]

CATALOGO_REPUESTOS = [
    ("Motor DC 12V", 85.0), ("Placa madre controladora", 210.0),
    ("Batería recargable 7.4V", 45.0), ("Kit de sellos/empaques", 18.0),
    ("Manguera de silicona", 12.5), ("Válvula solenoide", 38.0),
    ("Sensor de presión", 62.0), ("Pantalla LCD de reemplazo", 95.0),
    ("Fuente de poder interna", 70.0), ("Rodamiento SKF-6001", 9.0),
    ("Filtro HEPA compacto", 26.0), ("Transductor ultrasónico", 340.0),
    ("Cable paciente ECG", 22.0), ("Cuchilla de electrobisturí", 15.0),
    ("Turbina de aspiración", 120.0), ("Cámara de compresión", 180.0),
]

# ============================================================
# CORPUS DE TEXTOS PARA PLN — familias con sinónimos, variantes
# técnicas/no técnicas y errores de tipeo comunes (realistas)
# ============================================================
FAMILIAS = {
    "no_enciende": {
        "codigo": "F-101", "componente": "fuente de poder",
        "sintomas": ["El equipo no enciende", "no prende al presionar el botón de encendido",
                     "no da señales de encendido", "queda muerto, no ensiende",
                     "el interruptor principal no responde", "sin energía, no arranca"],
        "causa": ["Variación eléctrica", "Fuente de poder defectuosa",
                  "Desgaste del interruptor"], "accion": "Cambio de fuente de poder",
        "repuestos": [8, 6]},
    "sin_imagen": {
        "codigo": "F-102", "componente": "tarjeta de display",
        "sintomas": ["No hay imagen en el monitor", "pantalla sin señal",
                     "el display no muestra nada", "monitor en negro",
                     "no aparece la imagen del paciente"],
        "causa": ["Tarjeta de video dañada", "Cable de señal flojo",
                  "Panel de display agotado"], "accion": "Reemplazo de pantalla LCD",
        "repuestos": [7]},
    "ruido": {
        "codigo": "F-103", "componente": "compresor",
        "sintomas": ["ruido extraño en el compresor", "zumbido anormal al operar",
                     "vibración excesiva en el chasis", "chirrido intermitente en la bomba",
                     "hace un ruido raro al iniciar"],
        "causa": ["Desgaste mecánico", "Rodamiento dañado", "Falta de lubricación"],
        "accion": "Cambio de rodamiento y lubricación", "repuestos": [9, 15]},
    "fuga": {
        "codigo": "F-104", "componente": "circuito de fluido",
        "sintomas": ["fuga de liquido en la manguera", "pérdida de fluido por el conector",
                     "gotea por la válvula de salida", "fuga en el circuito hidráulico",
                     "moja la base, hay goteo constante"],
        "causa": ["Sello desgastado", "Manguera perforada", "Conector flojo por fatiga"],
        "accion": "Kit de sellos y manguera nueva", "repuestos": [3, 4]},
    "alarma": {
        "codigo": "F-105", "componente": "sensor de presión",
        "sintomas": ["alarma continua que no se silencia", "alarma intermitente sin código",
                     "suena la alarma de alta presión sin causa aparente",
                     "alerta sonora constante que molesta al paciente"],
        "causa": ["Sensor de presión descalibrado", "Falsa condición de alarma",
                  "Configuración de umbrales alterada"], "accion": "Recalibración de sensores",
        "repuestos": [6]},
    "error_codigo": {
        "codigo": "F-106", "componente": "tarjeta controladora",
        "sintomas": ["aparece el código de error E-04", "error 0x2F en pantalla y se bloquea",
                     "mensaje de falla del sistema al encender", "código F31 y reinicia solo"],
        "causa": ["Firmware desactualizado", "Memoria corrupta",
                  "Placa controladora defectuosa"], "accion": "Actualización de firmware y prueba",
        "repuestos": [1]},
    "no_calibra": {
        "codigo": "F-107", "componente": "sensor de medición",
        "sintomas": ["no calibra desde el último traslado", "se descalibra sola cada semana",
                     "lecturas fuera de rango", "no pasa la calibración inicial"],
        "causa": ["Deriva del sensor", "Uso sin verificación periódica",
                  "Componente de medición vencido"], "accion": "Calibración con patrón de verificación",
        "repuestos": [6]},
    "bateria": {
        "codigo": "F-108", "componente": "batería",
        "sintomas": ["la batería no carga", "no retiene la carga conectado a red",
                     "autonomía de batería muy corta", "batería dura menos de 10 minutos"],
        "causa": ["Batería agotada por ciclos", "Cargador interno dañado"],
        "accion": "Reemplazo de batería recargable", "repuestos": [2]},
    "calor": {
        "codigo": "F-109", "componente": "sistema de ventilación",
        "sintomas": ["se sobrecalienta después de 1 hora", "temperatura elevada en el transformador",
                     "se calienta mucho el motor", "sobrecalentamiento del compresor"],
        "causa": ["Ventilación obstruida", "Filtro saturado de polvo",
                  "Carga térmica excesiva"], "accion": "Limpieza interna y cambio de filtro",
        "repuestos": [10]},
    "rendimiento": {
        "codigo": "F-110", "componente": "bomba hidráulica",
        "sintomas": ["bajo rendimiento en modo continuo", "no alcanza la presión nominal",
                     "flujo menor al esperado", "rendimiento degradado, tarda el doble",
                     "trabaja lento y se detiene"],
        "causa": ["Desgaste natural", "Obstrucción parcial del circuito",
                  "Componente hidráulico desgastado"], "accion": "Ajuste y reemplazo de componentes",
        "repuestos": [0, 5]},
    "intermitente": {
        "codigo": "F-111", "componente": "conector de potencia",
        "sintomas": ["falla intermitente difícil de reproducir", "se apaga solo a los minutos",
                     "se reinicia aleatoriamente", "corta la operación sin motivo aparente"],
        "causa": ["Conector fatigado", "Falla eléctrica intermitente",
                  "Sobrecarga del circuito"], "accion": "Reparación de conector y prueba de carga",
        "repuestos": [8]},
    "conexion": {
        "codigo": "F-112", "componente": "tarjeta de red",
        "sintomas": ["no conecta a la red del hospital", "falla la conectividad al sistema central",
                     "no transmite datos al servidor", "pierde la conexión cada pocos minutos"],
        "causa": ["Tarjeta de red dañada", "Configuración de red alterada"],
        "accion": "Reconfiguración y cambio de tarjeta", "repuestos": [1]},
    "obstruccion": {
        "codigo": "F-113", "componente": "línea de fluido",
        "sintomas": ["obstrucción en la línea de aspiración", "tubo tapado con residuos",
                     "no aspira con suficiente fuerza", "válvula atascada"],
        "causa": ["Residuos acumulados", "Falta de limpieza periódica"],
        "accion": "Desobstrucción y cambio de tubería", "repuestos": [4]},
    "mecanico": {
        "codigo": "F-114", "componente": "ensamblaje mecánico",
        "sintomas": ["la puerta no cierra bien", "bisagra floja en el panel lateral",
                     "pieza suelta dentro del gabinete", "rueda delantera dañada"],
        "causa": ["Desgaste mecánico", "Manejo inadecuado"],
        "accion": "Ajuste mecánico y reemplazo de pieza", "repuestos": [9]},
}

SUFIJOS = [" desde ayer", " en modo operativo", " durante la noche",
           " tras el corte de energía", ", afecta la atención del paciente",
           " de manera constante", " al iniciar el turno", ""]
PREFIJOS = ["", "Se reporta que ", "El personal indica: ",
            "Personal de enfermería reporta: ", "Usuario refiere que "]
TIPOS = ["Falla en ", "Falla de ", "Reparación de ", "Diagnóstico de "]

ACCIONES_CIERRE = [
    "Se realizó prueba funcional por 2 h sin novedades. Equipo operativo.",
    "Reparación completada y verificada con simulador. Equipo devuelto al servicio.",
    "Se documentó la intervención; seguimiento en el próximo preventivo.",
    "Funcionamiento verificado según especificación del fabricante.",
]
ACCIONES_CAPACITACION = [
    "Se capacitó al usuario en el procedimiento correcto de operación.",
    "Refuerzo de capacitación brindado; instructivo dejado junto al equipo.",
]
ACCIONES_VERIFICACION = [
    "Inspección completa sin hallazgos; funcionamiento normal.",
    "Verificado en sitio: no se reproduce la condición reportada.",
]


def texto_descripcion(fam_key: str) -> str:
    """Descripción de falla con variación (sinónimos + prefijo/sufijo)."""
    base = rng.choice(FAMILIAS[fam_key]["sintomas"])
    return rng.choice(PREFIJOS) + base + rng.choice(SUFIJOS)


def texto_titulo(fam_key: str, equipo: str) -> str:
    return f"{rng.choice(TIPOS)}{fam_key.replace('_', ' ')} — {equipo}"


def _h(a: float) -> timedelta:
    return timedelta(hours=a)


# ============================================================
# DISTRIBUCIÓN POR EQUIPO (mayor resto, determinista)
# ============================================================
def repartir(cuota: int, pesos, minimo: int = 0, maximo: int = 10**9):
    total_p = sum(pesos)
    base = [max(minimo, int(cuota * p / total_p)) for p in pesos]
    resto = cuota - sum(base)
    orden = sorted(range(len(pesos)),
                   key=lambda i: (cuota * pesos[i] / total_p) - base[i],
                   reverse=True)
    i = 0
    while resto > 0:
        if base[orden[i % len(orden)]] < maximo:
            base[orden[i % len(orden)]] += 1
            resto -= 1
        i += 1
    while resto < 0:
        j = max(range(len(base)), key=lambda k: base[k])
        if base[j] > minimo:
            base[j] -= 1
            resto += 1
        else:
            break
    return base


def construir_planes() -> tuple[list, dict]:
    """Devuelve (equipos, planes): planes[nombre] = lista cronológica de
    clases. Clases: A correctiva, B reincidencia, C Sistema/IA, D preventivo,
    E cierre admin, F falsa alarma, G error usuario, H baja, AO1-AO3 abiertas."""
    pesos = [e[6] for e in EQUIPOS]
    # 209 base − 3 OTs abiertas AO (que se agregan aparte) → 220 exactos
    n_por_eq = repartir(N_TOTAL - CUOTAS["B_reincidencia"] - 3, pesos, minimo=3)
    d_base = repartir(CUOTAS["D_programado"], pesos, minimo=1, maximo=4)

    # Equipos con baja (H): ≤1, con historia ≥5 OTs
    elegibles = [i for i, n in enumerate(n_por_eq) if n >= 5]
    rng.shuffle(elegibles)
    idx_baja = set(elegibles[:CUOTAS["H_baja_equipo"]])

    # A: 104 completadas (las 3 abiertas AO van aparte en equipos grandes)
    rep_a = repartir(CUOTAS["A_correctiva"] - 3, pesos)
    rep_c = repartir(CUOTAS["C_sistema_ia"], pesos, maximo=3)
    rep_f = repartir(CUOTAS["F_falsa_alarma"], pesos, maximo=2)
    rep_g = repartir(CUOTAS["G_error_usuario"], pesos, maximo=2)
    rep_e = repartir(CUOTAS["E_cierre_admin"], pesos, maximo=2)

    planes = {}
    for i, eq in enumerate(EQUIPOS):
        nombre = eq[0]
        n = n_por_eq[i]
        n_otras = n - d_base[i] - (1 if i in idx_baja else 0)
        mix = (["A"] * rep_a[i] + ["C"] * rep_c[i] + ["F"] * rep_f[i]
               + ["G"] * rep_g[i] + ["E"] * rep_e[i])
        while len(mix) > n_otras:
            mix.remove("A" if "A" in mix else mix[0])
        while len(mix) < n_otras:
            mix.append("A")
        rng.shuffle(mix)
        lista = mix + ["D"] * d_base[i]
        rng.shuffle(lista)
        if i in idx_baja:
            lista.append("H")
        planes[nombre] = lista

    # OTs abiertas (AO1 Abierta, AO2 En Proceso, AO3 Esp. Repuesto): al final
    # de equipos SIN baja, de mayor peso (OTs recientes realistas)
    idx_grandes = sorted([i for i in range(len(EQUIPOS)) if i not in idx_baja],
                         key=lambda k: -EQUIPOS[k][6])[:3]
    for k, i in enumerate(idx_grandes):
        planes[EQUIPOS[i][0]].append(f"AO{k + 1}")

    # Reincidencias (B): insertar justo después de un padre A/C completado
    puestos_b = 0
    guardia = 0
    while puestos_b < CUOTAS["B_reincidencia"] and guardia < 500:
        guardia += 1
        i = rng.randrange(len(EQUIPOS))
        nombre = EQUIPOS[i][0]
        lista = planes[nombre]
        for pos, cls in enumerate(lista[:-1]):
            if cls in ("A", "C") and lista[pos + 1] not in ("B", "H",
                                                            "AO1", "AO2", "AO3"):
                lista.insert(pos + 1, "B")
                puestos_b += 1
                break

    # Pre-asignación EXACTA de pausa técnica y logística sobre A/C (posiciones)
    candidatos = [(nombre, pos)
                  for nombre, lista in planes.items()
                  for pos, cls in enumerate(lista) if cls in ("A", "C")]
    rng.shuffle(candidatos)
    set_pausa = set(candidatos[:N_PAUSA_TECNICA])
    set_logi = set(candidatos[N_PAUSA_TECNICA:N_PAUSA_TECNICA + N_LOGISTICA])
    return EQUIPOS, planes, set_pausa, set_logi


# ============================================================
# TIMELINE — construcción hacia ADELANTE por equipo
# ============================================================
def construir_timeline(equipos, planes, set_pausa, set_logi):
    ahora = datetime.now().replace(second=0, microsecond=0)
    fin = ahora - timedelta(minutes=COLCHON_FIN_MIN)
    ots, bitacora, repuestos = [], [], []
    fb_pool = FB_LABELS[:]          # se baraja; se consume por cada C
    rng.shuffle(fb_pool)

    for eq in equipos:
        nombre, tipo = eq[0], eq[1]
        lista = planes[nombre]
        n = len(lista)
        span_d = max(40.0, min(185.0, 185.0 * n / 16.0)) * rng.uniform(0.9, 1.05)
        fin_eq = fin - timedelta(days=rng.uniform(0, 10))
        # 0.82: reserva ~18% del span para las duraciones de las OTs
        gap_base_h = span_d * 24.0 / max(n, 1) * 0.82
        t = fin_eq - timedelta(days=span_d)
        padre = None                 # última correctiva completada (para B)
        es_ultimo = False

        for pos, cls in enumerate(lista):
            es_ultimo = (pos == n - 1)
            f = {c: None for c in COLS_OT}
            f["equipo"] = nombre
            f["tipo_equipo"] = tipo
            f["tipo_origen_ot"] = "Usuario"
            f["tipo_impacto"] = "REAL"
            f["estado_actual"] = "Completada"
            f["prioridad"] = rng.choices(["Alta", "Media", "Baja"],
                                         weights=[25, 55, 20])[0]
            f["failure_sequence"] = 1
            f["n_reaperturas"] = 0
            f["unidad_tiempo"] = "horas"
            f["_pares"] = []         # pares pausada→reanudada (h, sub)
            fam_key = rng.choice(list(FAMILIAS.keys()))
            fam = FAMILIAS[fam_key]
            cre = t

            if cls in ("AO1", "AO2", "AO3"):
                f["descripcion_falla"] = texto_descripcion(fam_key)
                f["titulo"] = texto_titulo(fam_key, nombre)
                f["codigo_falla"] = fam["codigo"]
                f["causa_raiz"] = rng.choice(fam["causa"])
                f["accion_tomada"] = fam["accion"]
                f["texto_libre_informe"] = (
                    f"Intervención sobre {nombre}: {f['descripcion_falla']} "
                    f"Acción: {f['accion_tomada']}.")
                f["estado_actual"] = {"AO1": "Abierta", "AO2": "En Proceso",
                                      "AO3": "Esp. Repuesto"}[cls]
                asig = cre + _h(rng.uniform(0.5, 4.0))
                f["_cre"], f["_asig"] = cre, asig
                f["_ini"], f["_res"] = None, None
                f["_mtta"] = (asig - cre).total_seconds() / 3600.0
                if cls in ("AO2", "AO3"):
                    ini = asig + _h(rng.uniform(0.5, 6.0))
                    f["_ini"] = ini
                    if cls == "AO3":
                        pausa_at = ini + _h(rng.uniform(1.0, 6.0))
                        f["_pares"] = [(pausa_at, None)]   # pausa abierta
                ots.append(f)
                t = cre + _h(gap_base_h * rng.uniform(0.4, 1.2))
                continue

            if cls == "B":
                assert padre is not None, "B sin padre (plan malformado)"
                fam_key = padre["_fam_key"]          # la reincidencia hereda
                fam = FAMILIAS[fam_key]              # la familia del padre
                p_fam = fam
                f["ventana_garantia"] = True
                f["prioridad"] = "Alta"
                f["titulo"] = f"Reincidencia {p_fam['codigo']} — {nombre}"
                f["descripcion_falla"] = "Falla repetida: " + \
                    texto_descripcion(padre["_fam_key"])
                f["codigo_falla"] = p_fam["codigo"]
                f["causa_raiz"] = "Falla infantil / reparación previa inefectiva"
                f["accion_tomada"] = "Reintervención y verificación extendida"
                activas = rng.uniform(0.5, 4.0)
                f["_padre"] = padre
            elif cls == "C":
                f["tipo_origen_ot"] = "Sistema/IA"
                f["titulo"] = f"Predictiva IA: degradación de {fam['componente']} — {nombre}"
                fb = fb_pool.pop() if fb_pool else "Confirmada"
                dias, conf = rng.randint(3, 21), round(rng.uniform(0.70, 0.97), 2)
                f["_pred_json"] = (f'{{"dias_estimados": {dias}, '
                                   f'"confianza": {conf}, '
                                   f'"componente": "{fam["componente"]}"}}')
                f["_fb"], f["_dias"], f["_conf"] = fb, dias, conf
                f["_fam_key"] = fam_key
                if fb == "Falsa_Alarma":
                    f["descripcion_falla"] = (f"Predicción IA de degradación de "
                                              f"{fam['componente']} con confianza "
                                              f"{conf}; "
                                              + rng.choice(ACCIONES_VERIFICACION).lower())
                    f["codigo_falla"] = ""
                    f["causa_raiz"] = "Sin hallazgos (predicción no confirmada)"
                    f["accion_tomada"] = "Inspección preventiva"
                    activas = rng.uniform(0.3, 1.2)
                elif fb == "Parcial":
                    f["descripcion_falla"] = texto_descripcion(fam_key)
                    f["codigo_falla"] = fam["codigo"]
                    f["causa_raiz"] = "Degradación incipiente confirmada"
                    f["accion_tomada"] = "Ajuste preventivo y monitoreo"
                    activas = rng.uniform(0.8, 3.0)
                else:
                    f["descripcion_falla"] = texto_descripcion(fam_key)
                    f["codigo_falla"] = fam["codigo"]
                    f["causa_raiz"] = rng.choice(fam["causa"])
                    f["accion_tomada"] = fam["accion"]
                    activas = rng.uniform(0.8, 6.0)
            elif cls == "D":
                f["tipo_origen_ot"] = "Programado"
                f["tipo_impacto"] = "PROGRAMADO"
                f["titulo"] = rng.choice([
                    "Mantenimiento preventivo trimestral", "Preventivo semestral",
                    "Preventivo con calibración", "Chequeo programado + limpieza interna"])
                f["descripcion_falla"] = ("Preventivo programado según plan: "
                                          "inspección, limpieza y pruebas de seguridad.")
                f["codigo_falla"] = ""
                f["causa_raiz"] = ""
                f["accion_tomada"] = "Checklist preventivo completado"
                f["prioridad"] = "Media"
                activas = rng.uniform(1.0, 4.0)
            elif cls == "E":
                f["cierre_administrativo"] = True
                f["excluida_de_MTTR"] = True
                f["titulo"] = f"Espera de decisión administrativa — {nombre}"
                f["descripcion_falla"] = (texto_descripcion(fam_key)
                                          + " Pendiente presupuesto/aprobación de repuesto importado.")
                f["codigo_falla"] = fam["codigo"]
                f["causa_raiz"] = rng.choice(fam["causa"])
                f["accion_tomada"] = "Cierre administrativo por Coordinación"
                f["prioridad"] = "Baja"
                activas = rng.uniform(90.0, 130.0)   # activas altas, sin pausas
            elif cls in ("F", "G"):
                f["estado_actual"] = "Cancelada"
                f["motivo_cancelacion"] = "Falsa_Alarma" if cls == "F" else "Error_Usuario"
                f["mdt_excluido_disponibilidad"] = True
                if cls == "F":
                    f["titulo"] = f"Alarma / reporte sin falla real — {nombre}"
                    f["descripcion_falla"] = rng.choice([
                        "Usuario reporta el equipo 'dañado'; verificado y funciona.",
                        "Alarma reportada; condición no reproducible en sitio.",
                        "Reporte por indicador del panel mal interpretado.",
                        "El equipo 'se apagó solo'; era pantalla en reposo.",
                        "Se reportó humo; resultó ser vapor del entorno clínico.",
                        "Falsa activación de alarma por puerta mal cerrada."])
                    f["causa_raiz"] = "Sin falla real"
                    f["accion_tomada"] = "Verificación sin intervención"
                else:
                    f["titulo"] = f"Error de operación del usuario — {nombre}"
                    f["descripcion_falla"] = rng.choice([
                        "El equipo 'no funciona'; el usuario omitió un paso del procedimiento.",
                        "Configuración alterada por el usuario; no es falla de equipo.",
                        "Mal uso de accesorios provocó el reporte.",
                        "El usuario no conectó el cable de paciente; reporte infundado.",
                        "Parámetros de alarma ajustados incorrectamente por el operador.",
                        "Cartucho/consumible mal instalado por el personal nuevo."])
                    f["causa_raiz"] = "Error de usuario"
                    f["accion_tomada"] = rng.choice(ACCIONES_CAPACITACION)
                f["codigo_falla"] = ""
                dur = rng.uniform(0.5, 2.5)
                res = cre + _h(dur)
                asig = cre + _h(min(rng.uniform(0.2, 1.0), dur * 0.6))
                f["_cre"], f["_asig"], f["_ini"], f["_res"] = cre, asig, None, res
                f["_mtta"] = (asig - cre).total_seconds() / 3600.0
                f["tiempo_real_invertido"] = 0.0
                f["texto_libre_informe"] = (f"Reporte sobre {nombre}: "
                                            + f["descripcion_falla"] + " "
                                            + f["accion_tomada"] + ".")
                padre = None
                ots.append(f)
                t = res + _h(gap_base_h * rng.uniform(0.4, 1.6))
                continue
            elif cls == "H":
                f["estado_actual"] = "Cancelada"
                f["motivo_cancelacion"] = "Baja_Equipo"
                f["excluida_de_MTTR"] = True
                f["mdt_excluido_disponibilidad"] = False
                f["prioridad"] = "Alta"
                f["titulo"] = f"Evaluación final y baja del equipo — {nombre}"
                f["descripcion_falla"] = rng.choice([
                    "Falla mayor: reparación no viable económicamente.",
                    "Fuera de soporte del fabricante (EOS) y sin repuestos en mercado.",
                    "Daño estructural severo; se recomienda reemplazo.",
                    "Falla recurrente del componente principal; costo de reparación > 60% del valor de reposición.",
                    "Equipo con más de 3 reincidencias en 6 meses; se autoriza baja técnica."])
                f["causa_raiz"] = "Fin de vida útil / no reparable"
                f["accion_tomada"] = "Evaluación técnica y trámite de baja"
                f["codigo_falla"] = fam["codigo"]
                activas = rng.uniform(24.0, 120.0)
            else:  # A
                f["titulo"] = texto_titulo(fam_key, nombre)
                f["descripcion_falla"] = texto_descripcion(fam_key)
                f["codigo_falla"] = fam["codigo"]
                f["causa_raiz"] = rng.choice(fam["causa"])
                f["accion_tomada"] = fam["accion"]
                activas = rng.uniform(0.5, 10.0)

            # Pauses solapadas (solo A/C; cuotas pre-asignadas por posición)
            espera = 0.0
            if cls in ("A", "C"):
                if (nombre, pos) in set_pausa:
                    espera = rng.uniform(0.5, 6.0)
                    f["en_pausa_tecnica"] = True
                    f["motivo_pausa"] = rng.choice(
                        ["Emergencia_Clinica", "Reasignacion_Coordinador"])
                elif (nombre, pos) in set_logi:
                    sub = rng.choice(SUB_ESTADOS_LOGISTICA)
                    espera = rng.uniform(*HORAS_LOGISTICA[sub])
                    f["sub_estado_logistica"] = sub
                    f["horas_espera_repuesto"] = round(espera, 2)
            if cls == "B":
                espera = 0.0

            mtta = rng.uniform(0.2, 6.0)
            reaccion = rng.uniform(0.3, 8.0)
            brutas = activas + espera
            asig = cre + _h(mtta)
            ini = asig + _h(reaccion)
            res = ini + _h(brutas)
            f["_cre"], f["_asig"], f["_ini"], f["_res"] = cre, asig, ini, res
            f["_mtta"], f["_reaccion"] = mtta, reaccion
            f["_activas"], f["_espera"] = round(activas, 2), round(espera, 2)
            f["tiempo_real_invertido"] = round(activas, 1)
            f["tiempo_pausa_acumulado"] = round(espera, 2)
            if espera > 0:
                f["horas_espera_repuesto"] = round(espera, 2)
            f["texto_libre_informe"] = (
                f"Intervención sobre {nombre}: {f['descripcion_falla']} "
                f"Acción: {f['accion_tomada']}. " + rng.choice(ACCIONES_CIERRE))
            f["_fam_key"] = fam_key

            # Repuesto (~30% de correctivas A/C; la asignación de fallidos va
            # en el post-proceso, ligada a reincidencias reales)
            if cls in ("A", "C") and len(repuestos) < N_REPUESTOS \
                    and f.get("_fb") != "Falsa_Alarma" and rng.random() < 0.42:
                nom_r, pre_r = CATALOGO_REPUESTOS[rng.choice(fam["repuestos"])]
                repuestos.append({"ot_ref": f, "repuesto_nombre": nom_r,
                                  "cantidad_utilizada": rng.randint(1, 2),
                                  "estado_instalacion": "Instalado",
                                  "precio_referencia": pre_r})
                f["_repuesto_row"] = repuestos[-1]

            if cls in ("A", "C"):
                padre = f   # candidato a padre de reincidencia
            ots.append(f)

            # Siguiente OT: si es B → nace 24-48 h después de ESTA resolución
            if pos + 1 < n and lista[pos + 1] == "B":
                t = res + _h(rng.uniform(24.0, 48.0))
            else:
                t = res + _h(gap_base_h * rng.uniform(0.4, 1.6))

        # Ajuste: si el equipo se pasó de la ventana, desplazar TODAS sus
        # fechas (preserva duraciones, gaps y deltas de reincidencia <72 h)
        last_res = max((o["_res"] for o in ots if o["_res"] and o["equipo"] == nombre),
                       default=None)
        if last_res and last_res > fin_eq:
            d = last_res - fin_eq
            for o in ots:
                if o["equipo"] == nombre:
                    for k in ("_cre", "_asig", "_ini", "_res"):
                        if o[k] is not None:
                            o[k] = o[k] - d
                    o["_pares"] = [(p0 - d if p0 is not None else None,
                                    p1 - d if p1 is not None else None)
                                   for p0, p1 in o["_pares"]]

    return ots, bitacora, repuestos, fb_pool


# ============================================================
# POST-PROCESO: ids, enlaces padre/hijo, repuestos fallidos
# ============================================================
def post_procesar(ots, repuestos):
    """Ordena cronológicamente, asigna ot_id (500+), resuelve parent_ot_id y
    marca exactamente N_REPUESTOS_FALLIDOS repuestos como Instalado_Fallido
    ligados a reincidencias reales (es_reparacion_inefectiva=True)."""
    ots.sort(key=lambda o: o["_cre"])
    for i, o in enumerate(ots):
        o["ot_id"] = 500 + i
    for o in ots:
        if o.get("_padre") is not None:
            p = o["_padre"]
            o["parent_ot_id"] = p["ot_id"]
            o["failure_sequence"] = (p.get("failure_sequence") or 1) + 1
    # Repuestos defectuosos: el repuesto del padre falló → reincidencia
    fallidos = 0
    for b in [o for o in ots if o["ventana_garantia"]]:
        if fallidos >= N_REPUESTOS_FALLIDOS:
            break
        p = b["_padre"]
        row = p.get("_repuesto_row")
        if row is None:  # el padre no tenía repuesto: se le asigna uno
            nom_r, pre_r = CATALOGO_REPUESTOS[
                rng.choice(FAMILIAS[p["_fam_key"]]["repuestos"])]
            row = {"ot_ref": p, "repuesto_nombre": nom_r, "cantidad_utilizada": 1,
                   "estado_instalacion": "Instalado", "precio_referencia": pre_r}
            repuestos.append(row)
            p["_repuesto_row"] = row
        if row["estado_instalacion"] == "Instalado":
            row["estado_instalacion"] = "Instalado_Fallido"
            b["es_reparacion_inefectiva"] = True
            fallidos += 1
    for r in repuestos:
        r["ot_id"] = r["ot_ref"]["ot_id"]
    return fallidos


def _diversificar_textos(ots):
    """Pasada de unicidad: para descripciones duplicadas (clases con pools de
    variantes fijas) añade un calificador contextual realista y determinista
    hasta lograr >= 90% de textos únicos (evita overfitting trivial del PLN)."""
    calificadores = [
        "según reporte del turno nocturno", "confirmado en ronda de la mañana",
        "observado durante la ronda de la tarde", "según comunicación del área",
        "reportado por personal de enfermería", "documentado por el técnico de guardia",
        "reiteración del reporte del servicio", "segundo aviso del mismo servicio",
        "con detalles adicionales del usuario", "hallado en inspección de rutina"]
    vistos = {}
    for o in ots:
        d = o["descripcion_falla"]
        if d in vistos:
            k = vistos[d]
            nuevo = d + f" ({calificadores[k % len(calificadores)]})"
            o["descripcion_falla"] = nuevo
            # coherencia: el informe libre contiene la descripción
            if o.get("texto_libre_informe") and d in o["texto_libre_informe"]:
                o["texto_libre_informe"] = \
                    o["texto_libre_informe"].replace(d, nuevo, 1)
            vistos[d] = k + 1
        else:
            vistos[d] = 0
    # segunda pasada por si aún persisten duplicados (pools muy usados)
    vistos = {}
    for o in ots:
        d = o["descripcion_falla"]
        if d in vistos:
            nuevo = d + f" [caso {o['ot_id']}, {o['equipo']}]"
            o["descripcion_falla"] = nuevo
            if o.get("texto_libre_informe") and d in o["texto_libre_informe"]:
                o["texto_libre_informe"] = \
                    o["texto_libre_informe"].replace(d, nuevo, 1)
        else:
            vistos[d] = True


def clase_de(o):
    """Etiqueta de clase dataset derivable de las banderas (para TextosPLN)."""
    if o["ventana_garantia"]:
        return "B_reincidencia"
    if o["tipo_origen_ot"] == "Sistema/IA":
        return "C_sistema_ia"
    if o["tipo_origen_ot"] == "Programado":
        return "D_programado"
    if o["cierre_administrativo"]:
        return "E_cierre_admin"
    if o["motivo_cancelacion"] == "Falsa_Alarma":
        return "F_falsa_alarma"
    if o["motivo_cancelacion"] == "Error_Usuario":
        return "G_error_usuario"
    if o["motivo_cancelacion"] == "Baja_Equipo":
        return "H_baja_equipo"
    if o["estado_actual"] in ("Abierta", "En Proceso", "Esp. Repuesto"):
        return "AO_abierta"
    return "A_correctiva"


# ============================================================
# BITÁCORA coherente con los relojes de cada OT
# ============================================================
def construir_bitacora(ots):
    evs = []
    for o in ots:
        ot = o["ot_id"]
        crea_us = "Sistema/IA (RF07)" if o["tipo_origen_ot"] == "Sistema/IA" \
            else "sistema"
        evs.append([o["_cre"], ot, "creada", crea_us, "", "Abierta",
                    f"OT creada ({o['tipo_origen_ot']}): {o['titulo']}"])
        if o["_asig"]:
            evs.append([o["_asig"], ot, "asignada", rng.choice(TECNICOS),
                        "Abierta", "En Proceso",
                        "Asignación según carga de trabajo y criticidad del equipo"])
        if o["_ini"]:
            evs.append([o["_ini"], ot, "iniciada", rng.choice(TECNICOS),
                        "En Proceso", "En Proceso", "Inicio de intervención en el equipo"])
        if o.get("en_pausa_tecnica") and o["_ini"] is not None:
            esp = o["tiempo_pausa_acumulado"]
            evs.append([o["_ini"], ot, "pausada", rng.choice(TECNICOS),
                        "En Proceso", "En Proceso",
                        f"Pausa técnica ({o['motivo_pausa']}): equipo detenido en sitio"])
            evs.append([o["_ini"] + _h(esp), ot, "reanudada", rng.choice(TECNICOS),
                        "En Proceso", "En Proceso",
                        "Reanudación del trabajo tras atender la emergencia"])
        elif o.get("sub_estado_logistica") and o["_ini"] is not None:
            esp = o["horas_espera_repuesto"]
            evs.append([o["_ini"], ot, "pausada", rng.choice(TECNICOS),
                        "En Proceso", "Esp. Repuesto",
                        f"Espera de repuesto ({o['sub_estado_logistica']})"])
            evs.append([o["_ini"] + _h(esp), ot, "reanudada", rng.choice(TECNICOS),
                        "Esp. Repuesto", "En Proceso",
                        "Repuesto recibido; se reanuda la reparación"])
        for (p0, p1) in o["_pares"]:  # pausa abierta (OT en Esp. Repuesto)
            evs.append([p0, ot, "pausada", rng.choice(TECNICOS),
                        "En Proceso", "Esp. Repuesto",
                        "Esperando confirmación de repuesto (OT abierta)"])
        if o["_res"]:
            if o["estado_actual"] == "Completada":
                evs.append([o["_res"], ot, "resuelta", rng.choice(TECNICOS),
                            "En Proceso", "Completada",
                            o["accion_tomada"] + (" Cierre administrativo." if
                                                  o["cierre_administrativo"] else "")])
            else:
                evs.append([o["_res"], ot, "cancelada", COORDINADOR,
                            "En Proceso", "Cancelada",
                            f"Cancelada ({o['motivo_cancelacion']}): "
                            f"{o['accion_tomada']}."])
    evs.sort(key=lambda e: (e[0], e[1]))
    return evs


# ============================================================
# SÍNTOMAS + FEEDBACK PREDICTIVO (ciclo H2 de las OTs Sistema/IA)
# ============================================================
def construir_sintomas_feedback(ots):
    sintomas, feedback = [], []
    for o in ots:
        if o["tipo_origen_ot"] != "Sistema/IA":
            continue
        label = o["_fb"]
        sid = len(sintomas) + 1
        estado_val = {"Confirmada": "Confirmado", "Falsa_Alarma": "Falsa_Alarma",
                      "Parcial": "Pendiente"}[label]
        sintomas.append({
            "symptom_id": sid, "ot_id": o["ot_id"], "tipo_origen": "Sistema/IA",
            "texto_sintoma": ("Predicción RUL: degradación de "
                              f"{FAMILIAS[o['_fam_key']]['componente']} "
                              "(sensor + historial de fallas)"),
            "prediccion_rul": o["_pred_json"], "fecha_reporte": o["_cre"],
            "estado_validacion": estado_val})
        if rng.random() < 0.6:  # síntoma del usuario corroborante
            sintomas.append({
                "symptom_id": len(sintomas) + 1, "ot_id": o["ot_id"],
                "tipo_origen": "Usuario", "texto_sintoma": o["descripcion_falla"],
                "prediccion_rul": None,
                "fecha_reporte": o["_cre"] + _h(rng.uniform(0.1, 2.0)),
                "estado_validacion": "Confirmado" if label == "Confirmada"
                else "Pendiente"})
        feedback.append({
            "ot_id": o["ot_id"], "symptom_id": sid,
            "prediccion_original_ia": o["_pred_json"],
            "resultado_real_tecnico": label,
            "variables_sensores_snapshot": None, "fecha_cierre": o["_res"]})
    return sintomas, feedback


# ============================================================
# EXCEL (mismo estilo que generar_demo_v21.py)
# ============================================================
def _celda(v):
    if v is None:
        return ""
    if isinstance(v, bool):
        return "True" if v else "False"
    if isinstance(v, datetime):
        return v.strftime(FMT_FECHA)
    return v


def _hoja(wb, titulo, columnas, filas, anchos=None, primera=False):
    ws = wb.active if primera else wb.create_sheet(titulo)
    if primera:
        ws.title = titulo
    ws.append(columnas)
    for c in range(1, len(columnas) + 1):
        cell = ws.cell(row=1, column=c)
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="2F5496")
    for fila in filas:
        ws.append([_celda(v) for v in fila])
    for i, col in enumerate(columnas, start=1):
        ws.column_dimensions[get_column_letter(i)].width = \
            (anchos or {}).get(col, 16)
    ws.freeze_panes = "A2"
    return ws


MAP_FECHAS = {"fecha_creacion": "_cre", "fecha_asignacion": "_asig",
              "fecha_inicio_trabajo": "_ini", "fecha_resolucion": "_res"}


def generar_excel(ruta, ots, equipos_estado, bitacora, sintomas, feedback,
                  repuestos):
    wb = openpyxl.Workbook()
    # 1. OTs — formato EXACTO de demo_ordenes_trabajo_v21.xlsx
    filas_ot = []
    for o in ots:
        fila = []
        for c in COLS_OT:
            if c in MAP_FECHAS:
                fila.append(_celda(o.get(MAP_FECHAS[c])))
            else:
                fila.append(_celda(o.get(c)))
        filas_ot.append(fila)
    anchos_ot = {"titulo": 34, "equipo": 22, "texto_libre_informe": 46,
                 "descripcion_falla": 40, "tipo_equipo": 17}
    _hoja(wb, "OTs Dataset v2.1", COLS_OT, filas_ot, anchos_ot, primera=True)

    # 2. Equipos — formato EXACTO de demo_equipos_v21.xlsx
    hoy = datetime.now().date()
    filas_eq = []
    for i, (nombre, tipo, crit, modelo, marca, ubic, _p) in enumerate(EQUIPOS, 1):
        estado = "Retirado/Baja" if nombre in equipos_estado else "Operativo"
        filas_eq.append([
            nombre, modelo, f"SINT-220-{i:03d}", "", marca,
            (hoy - timedelta(days=365 * rng.uniform(2, 6))).isoformat(),
            "", "", ubic, estado, "", "Compra",
            f"Equipo sintético para entrenamiento RF07 ({tipo})",
            "Generado por generar_dataset_sintetico_220.py",
            tipo, crit])
    _hoja(wb, "Equipos Dataset", COLS_EQUIPOS, filas_eq,
          {"nombre_corto": 24, "descripcion": 38, "observaciones": 38})

    # 3. Bitácora
    _hoja(wb, "Bitacora",
          ["fecha", "ot_id", "accion", "usuario", "estado_anterior",
           "estado_nuevo", "comentario"],
          [[e[0], e[1], e[2], e[3], e[4] or "", e[5] or "", e[6]] for e in bitacora],
          {"comentario": 52})

    # 4. Síntomas / 5. Feedback / 6. Repuestos
    _hoja(wb, "Sintomas",
          ["symptom_id", "ot_id", "tipo_origen", "texto_sintoma",
           "prediccion_rul", "fecha_reporte", "estado_validacion"],
          [[s["symptom_id"], s["ot_id"], s["tipo_origen"], s["texto_sintoma"],
            s["prediccion_rul"], s["fecha_reporte"], s["estado_validacion"]]
           for s in sintomas], {"texto_sintoma": 46, "prediccion_rul": 34})
    _hoja(wb, "FeedbackPredictivo",
          ["ot_id", "symptom_id", "prediccion_original_ia",
           "resultado_real_tecnico", "variables_sensores_snapshot",
           "fecha_cierre"],
          [[f["ot_id"], f["symptom_id"], f["prediccion_original_ia"],
            f["resultado_real_tecnico"], "", f["fecha_cierre"]]
           for f in feedback], {"prediccion_original_ia": 34})
    _hoja(wb, "RepuestosOT",
          ["ot_id", "repuesto_nombre", "cantidad_utilizada",
           "estado_instalacion", "precio_referencia"],
          [[r["ot_id"], r["repuesto_nombre"], r["cantidad_utilizada"],
            r["estado_instalacion"], r["precio_referencia"]] for r in repuestos],
          {"repuesto_nombre": 26})

    # 7. TextosPLN — corpus etiquetado para el clasificador
    filas_tx = []
    for o in ots:
        cls = clase_de(o)
        fam = o.get("_fam_key")
        filas_tx.append([
            o["ot_id"], o["equipo"], cls,
            fam or ("preventivo" if cls == "D_programado" else
                    "sin_falla_real" if cls == "F_falsa_alarma" else
                    "error_usuario" if cls == "G_error_usuario" else "n/d"),
            o["codigo_falla"] or "", o["descripcion_falla"],
            o["accion_tomada"], o["texto_libre_informe"]])
    _hoja(wb, "TextosPLN",
          ["ot_id", "equipo", "clase_dataset", "familia_falla", "codigo_falla",
           "descripcion_falla", "acciones_realizadas", "texto_libre_informe"],
          filas_tx, {"descripcion_falla": 44, "texto_libre_informe": 48,
                     "acciones_realizadas": 34, "equipo": 22})
    wb.save(ruta)


# ============================================================
# VALIDACIÓN + REPORTE verificacion_dataset_220.md
# ============================================================
def validar_y_reportar(ruta_md, ots, repuestos, sintomas, feedback, bitacora,
                       n_fallidos):
    ahora = datetime.now()
    checks = []

    def chk(nombre, ok, detalle=""):
        checks.append((nombre, bool(ok), detalle))
        print(f"  [{'✅' if ok else '❌'}] {nombre}"
              + (f" → {detalle}" if detalle and not ok else ""))

    cnt = {
        "ventana_garantia": sum(1 for o in ots if o["ventana_garantia"]),
        "en_pausa_tecnica": sum(1 for o in ots if o["en_pausa_tecnica"]),
        "cierre_administrativo": sum(1 for o in ots if o["cierre_administrativo"]),
        "Falsa_Alarma": sum(1 for o in ots if o["motivo_cancelacion"] == "Falsa_Alarma"),
        "Error_Usuario": sum(1 for o in ots if o["motivo_cancelacion"] == "Error_Usuario"),
        "Baja_Equipo": sum(1 for o in ots if o["motivo_cancelacion"] == "Baja_Equipo"),
        "Sistema/IA": sum(1 for o in ots if o["tipo_origen_ot"] == "Sistema/IA"),
        "Programado": sum(1 for o in ots if o["tipo_origen_ot"] == "Programado"),
        "Usuario": sum(1 for o in ots if o["tipo_origen_ot"] == "Usuario"),
        "logistica": sum(1 for o in ots if o["sub_estado_logistica"]),
        "mdt_excluido": sum(1 for o in ots if o["mdt_excluido_disponibilidad"]),
        "excluida_MTTR": sum(1 for o in ots if o["excluida_de_MTTR"]),
    }
    print("-" * 66)
    print("[DISTRIBUCIÓN] banderas v2.1 vs objetivo (tolerancia ±5% de 220 = ±11):")
    filas_flags = [
        ("ventana_garantia_reparacion=True", cnt["ventana_garantia"], 11, "5%"),
        ("en_pausa_tecnica=True", cnt["en_pausa_tecnica"], 22, "10%"),
        ("cierre_administrativo=True", cnt["cierre_administrativo"], 11, "5%"),
        ("motivo_cancelacion=Falsa_Alarma", cnt["Falsa_Alarma"], 18, "8%"),
        ("motivo_cancelacion=Error_Usuario", cnt["Error_Usuario"], 11, "5%"),
        ("motivo_cancelacion=Baja_Equipo", cnt["Baja_Equipo"], 7, "3%"),
        ("tipo_origen_ot=Sistema/IA", cnt["Sistema/IA"], 22, "10%"),
        ("tipo_origen_ot=Programado", cnt["Programado"], 33, "15%"),
        ("sub_estado_logistica (variante)", cnt["logistica"], 33, "15%"),
        ("mdt_excluido_disponibilidad=True", cnt["mdt_excluido"], 29, "13%"),
        ("excluida_de_MTTR=True", cnt["excluida_MTTR"], 18, "8%"),
    ]
    for nombre, real, objetivo, pct in filas_flags:
        ok = abs(real - objetivo) <= 11
        chk(f"{nombre}: {real} (objetivo {objetivo} = {pct})", ok)

    # Consistencia de reincidencias <72 h con las FECHAS
    por_id = {o["ot_id"]: o for o in ots}
    mal_delta = []
    for o in ots:
        if o["ventana_garantia"] and o["parent_ot_id"]:
            p = por_id.get(o["parent_ot_id"])
            if p is None or p["_res"] is None:
                mal_delta.append((o["ot_id"], "padre inválido"))
            else:
                delta = (o["_cre"] - p["_res"]).total_seconds() / 3600.0
                if not (0 < delta < 72):
                    mal_delta.append((o["ot_id"], f"Δ={delta:.1f}h"))
    chk("Reincidencias: nacimiento 0<Δ<72 h tras resolución del padre "
        f"({cnt['ventana_garantia']} OTs)", not mal_delta, str(mal_delta[:4]))

    # Bitácora coherente: los pares pausada→reanudada REALES (eventos, por OT
    # — mismo criterio del motor v2.1.3) suman la pausa declarada
    incoherentes = []
    ev_por_ot = {}
    for ev in bitacora:
        ev_por_ot.setdefault(ev[1], []).append(ev)
    for o in ots:
        declarada = float(o["tiempo_pausa_acumulado"] or 0)
        suma, pausa_desde = 0.0, None
        for ev in sorted(ev_por_ot.get(o["ot_id"], []), key=lambda e: e[0]):
            if ev[2] == "pausada":
                pausa_desde = ev[0]
            elif ev[2] == "reanudada" and pausa_desde is not None:
                d = (ev[0] - pausa_desde).total_seconds() / 3600.0
                suma += max(d, 0.0)
                pausa_desde = None
        if abs(round(suma, 2) - declarada) > 0.05:
            incoherentes.append((o["ot_id"], round(suma, 2), declarada))
    chk("Bitácora: pares pausada→reanudada = pausa declarada (sin doble conteo)",
        not incoherentes, str(incoherentes[:5]))

    # Fechas: sin futuro y span ~6 meses
    max_res = max((o["_res"] for o in ots if o["_res"]), default=None)
    min_cre = min((o["_cre"] for o in ots), default=None)
    span_dias = (max_res - min_cre).total_seconds() / 86400.0 if max_res else 0
    chk("Sin fechas futuras (última resolución ≤ ahora−1h)",
        max_res is not None and max_res <= ahora - timedelta(minutes=59),
        str(max_res))
    chk(f"Historia amplia para RUL: span={span_dias:.0f} días (objetivo ~180)",
        150 <= span_dias <= 200)

    # Ciclo predictivo
    fb_cnt = {"Confirmada": 0, "Falsa_Alarma": 0, "Parcial": 0}
    for f in feedback:
        fb_cnt[f["resultado_real_tecnico"]] = fb_cnt.get(
            f["resultado_real_tecnico"], 0) + 1
    chk(f"Feedback predictivo completo: {len(feedback)} de {cnt['Sistema/IA']} IA",
        len(feedback) == cnt["Sistema/IA"])
    chk(f"Distribución feedback ~70/20/10: {fb_cnt}",
        fb_cnt["Confirmada"] >= 13 and fb_cnt["Falsa_Alarma"] >= 4)

    # Repuestos
    ots_con_rep = len({r["ot_id"] for r in repuestos})
    chk(f"Repuestos: {len(repuestos)} filas en {ots_con_rep} correctivas "
        f"(objetivo ~30% de 140 = 42)", abs(ots_con_rep - 42) <= 11)
    chk(f"Repuestos Instalado_Fallido = {n_fallidos} (objetivo ~3, "
        "ligados a es_reparacion_inefectiva)", n_fallidos == N_REPUESTOS_FALLIDOS)

    # Textos únicos para PLN
    descs = [o["descripcion_falla"] for o in ots]
    unicos = len(set(descs))
    pct_unicos = unicos * 100.0 / max(len(descs), 1)
    chk(f"Textos no repetitivos: {unicos}/{len(descs)} únicos ({pct_unicos:.0f}%)",
        pct_unicos >= 85)

    # Estados finales
    est_cnt = {}
    for o in ots:
        est_cnt[o["estado_actual"]] = est_cnt.get(o["estado_actual"], 0) + 1

    # Por equipo
    por_eq = {}
    for o in ots:
        por_eq[o["equipo"]] = por_eq.get(o["equipo"], 0) + 1

    # Muestras de texto
    muestras = []
    vistos = set()
    for o in ots:
        d = o["descripcion_falla"]
        if d not in vistos and len(muestras) < 8:
            muestras.append((o["ot_id"], clase_de(o), d))
            vistos.add(d)

    # ── verificacion_dataset_220.md ──
    linea = lambda ok: "✅" if ok else "❌"
    md = [f"# Verificación del Dataset Sintético 220 OTs (RF07)",
          "",
          f"> Generado por `generar_dataset_sintetico_220.py` el "
          f"{ahora.strftime('%Y-%m-%d %H:%M')} · semilla determinista "
          f"RANDOM_SEED={RANDOM_SEED} (corridas reproducibles)",
          f"> Rango real de fechas: **{min_cre.strftime('%Y-%m-%d')} → "
          f"{max_res.strftime('%Y-%m-%d')}** ({span_dias:.0f} días ≈ "
          f"{span_dias/30.4:.1f} meses) · {len(ots)} OTs · "
          f"{len(por_eq)} equipos",
          "",
          "## 1. Distribución de banderas v2.1",
          "",
          "| Flag v2.1 | Objetivo (tabla tesis) | Generado | Estado (±5% = ±11) |",
          "|-----------|:---:|:---:|:---:|"]
    for nombre, real, objetivo, pct in filas_flags:
        ok = abs(real - objetivo) <= 11
        md.append(f"| {nombre} | {objetivo} ({pct}) | {real} | {linea(ok)} |")
    md += ["",
           f"**Nota sobre `tipo_origen_ot='Usuario'`:** el total bruto es "
           f"{cnt['Usuario']} OTs ({cnt['Usuario']*100/len(ots):.0f}%) porque "
           "INCLUYE reincidencias (11), cierres administrativos (11) y "
           "canceladas de origen usuario (36). La fila «Usuario 57% ≈ 125» "
           "de la tabla de la tesis refiere a las **correctivas normales** "
           f"(clase A = {cnt['Usuario'] - 11 - 11 - 36} completadas + 3 abiertas), "
           "cuya suma con el resto de clases cierra exactamente 220.",
           "",
           "## 2. Distribución de estados finales",
           "",
           "| Estado | OTs | % |",
           "|--------|:---:|:---:|"]
    for est, n in sorted(est_cnt.items(), key=lambda x: -x[1]):
        md.append(f"| {est} | {n} | {n*100.0/len(ots):.1f}% |")
    md += ["", "## 3. OTs por equipo (diversidad de frecuencia)",
           "",
           "| Equipo | Criticidad | OTs |",
           "|--------|:---:|:---:|"]
    crit_map = {e[0]: e[2] for e in EQUIPOS}
    for nombre, n in sorted(por_eq.items(), key=lambda x: -x[1]):
        md.append(f"| {nombre} | {crit_map[nombre]} | {n} |")
    md += ["",
           "## 4. Ciclo predictivo (OTs Sistema/IA → síntomas → feedback)",
           "",
           f"- OTs predictivas: **{cnt['Sistema/IA']}** · síntomas generados: "
           f"**{len(sintomas)}** · feedbacks: **{len(feedback)}**",
           f"- Resultado real del técnico: Confirmada={fb_cnt['Confirmada']}, "
           f"Falsa_Alarma={fb_cnt['Falsa_Alarma']}, Parcial={fb_cnt['Parcial']} "
           "(objetivo ~70/20/10%)",
           "- Cada feedback referencia su `symptom_id` y guarda la predicción "
           "RUL original (JSON: dias_estimados, confianza, componente).",
           "",
           "## 5. Repuestos",
           "",
           f"- Filas de repuestos: **{len(repuestos)}** en {ots_con_rep} OTs "
           "correctivas (~30%)",
           f"- **{n_fallidos} Instalado_Fallido** → sus OTs de reincidencia "
           "llevan `es_reparacion_inefectiva=True` (cadena repuesto defectuoso "
           "→ falla infantil, entrenable por PLN y por reglas).",
           "",
           "## 6. Consistencias verificadas",
           ""]
    for nombre, ok, detalle in checks:
        md.append(f"- {linea(ok)} {nombre}"
                  + (f" — ⚠ {detalle}" if not ok and detalle else ""))
    md += ["",
           "## 7. Muestras de textos libres generados (para PLN)",
           ""]
    for ot_id, cls, d in muestras:
        md.append(f"- `OT {ot_id}` ({cls}): «{d}»")
    md += ["",
           "## 8. Cómo consumirlo en los experimentos RF07",
           "",
           "```python",
           "import pandas as pd",
           "df  = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='OTs Dataset v2.1')",
           "tx  = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='TextosPLN')",
           "snt = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='Sintomas')",
           "fb  = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='FeedbackPredictivo')",
           "# PLN:  tx.descripcion_falla → X; tx.clase_dataset / familia_falla → y",
           "# RUL:  fechas + tiempo_pausa_acumulado + horizonte por equipo",
           "# XAI:  variables de la OT + feedback como etiqueta de realimentación",
           "```",
           ""]
    ruta_md.write_text("\n".join(md), encoding="utf-8")

    n_ok = sum(1 for _, ok, _ in checks if ok)
    return n_ok, len(checks)


# ============================================================
# MAIN
# ============================================================
def main():
    print("=" * 66)
    print("GENERADOR DE DATASET SINTÉTICO 220 OTs — RF07 (PLN/RUL/XAI)")
    print(f"Semilla determinista: {RANDOM_SEED} · ventana objetivo ~{SPAN_MESES:.0f} meses")
    print("=" * 66)
    equipos, planes, set_pausa, set_logi = construir_planes()
    ots, _, repuestos, fb_pool = construir_timeline(equipos, planes,
                                                    set_pausa, set_logi)
    print(f"[1/5] Timeline construido: {len(ots)} OTs en {len(EQUIPOS)} equipos")
    n_fallidos = post_procesar(ots, repuestos)
    _diversificar_textos(ots)
    print(f"[2/5] Post-proceso: ids 500+ · parent_ot_id resuelto · "
          f"{n_fallidos} repuestos Instalado_Fallido · textos diversificados")
    bitacora = construir_bitacora(ots)
    print(f"[3/5] Bitácora coherente: {len(bitacora)} eventos")
    sintomas, feedback = construir_sintomas_feedback(ots)
    print(f"[4/5] Ciclo predictivo: {len(sintomas)} síntomas · "
          f"{len(feedback)} feedbacks (~70/20/10)")

    equipos_baja = {o["equipo"] for o in ots if o["motivo_cancelacion"] == "Baja_Equipo"}
    ruta_xlsx = BACKEND_DIR / "dataset_sintetico_220_ot.xlsx"
    generar_excel(ruta_xlsx, ots, equipos_baja, bitacora, sintomas, feedback,
                  repuestos)
    print(f"[5/5] Excel generado: {ruta_xlsx.name} (7 hojas)")

    wb = openpyxl.load_workbook(ruta_xlsx)
    print("-" * 66)
    print("[VERIFICACIÓN] hojas del Excel (filas de datos):")
    for ws in wb.worksheets:
        print(f"    · {ws.title:<20} {ws.max_row - 1} filas × {ws.max_column} cols")
    print("-" * 66)
    n_ok, n_tot = validar_y_reportar(
        BACKEND_DIR / "verificacion_dataset_220.md", ots, repuestos,
        sintomas, feedback, bitacora, n_fallidos)
    print("=" * 66)
    print(f"RESULTADO: {n_ok}/{n_tot} verificaciones OK")
    if n_ok == n_tot:
        print("OK ✓ — dataset listo para los experimentos RF07 (PLN/RUL/XAI)")
        print(f"Archivos: {ruta_xlsx.name} + verificacion_dataset_220.md")
        print("Nota: NO se importó nada a la BD (solo generación de archivos).")
        sys.exit(0)
    print("✗ Hay verificaciones fallidas — revisar arriba")
    sys.exit(1)


if __name__ == "__main__":
    main()



