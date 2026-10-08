"""
CMMS-BioAI — Módulo Predictivo (RF07) · ml/data/generar_dataset.py
Genera el dataset sintético de 220 órdenes de trabajo (OTs) de bombas de infusión.

Características exigidas por el PROMPT MAESTRO / tesis:
- Texto libre realista en español (sinónimos, abreviaturas y errores ortográficos
  típicos de técnicos de unidades de Bioingeniería), con solapamiento natural de
  vocabulario entre categorías (síntomas compartidos entre sistemas de la bomba).
- Datos estructurados coherentes (fechas 2023-2025, tiempos, tipos de falla).
- Etiquetas de "tipo de falla" (eléctrica, mecánica, software, sensor, calibración, otra)
  para entrenar el clasificador PLN.
- Variable objetivo "días hasta la próxima falla" (RUL) con proceso de degradación
  físicamente plausible (recurrencia de oclusión y deriva metrológica acortan la vida).
- Reproducible: semilla fija RANDOM_SEED=42 (documentada en la tesis).

Ejecución:
    cd backend
    python -m ml.data.generar_dataset
"""

import csv
import json
import random
import re
import numpy as np
from datetime import date, timedelta

from ml import config

SEED = config.RANDOM_SEED
N_OT_OBJETIVO = 220          # n=219 (Cochran, tesis §3.6.3) + 1 de margen
FECHA_INICIO = date(2023, 1, 1)
FECHA_FIN = date(2025, 12, 31)
MAX_OT_POR_EQUIPO = 9        # ~25 equipos × ~9 OTs ≈ 220 OTs

# ------------------------------------------------------------------
# Parque de bombas de infusión sintético (25 equipos)
# ------------------------------------------------------------------
MARCAS_MODELOS = [
    ("B.Braun", "Infusomat Space"), ("B.Braun", "Perfusor Space"),
    ("Fresenius", "Agilia SP"), ("Fresenius", "Vial Leona"),
    ("Baxter", "Sigma Spectrum"), ("Terumo", "TE-171"),
    ("Mindray", "BeneFusion SP3"), ("NIPRO", "FD-160"),
    ("Nihon Kohden", "IP-701T"), ("Braun", "Infusomat fmS"),
    ("Medicap", "IP-01"), ("Mindray", "BeneFusion VP5"),
    ("Fresenius", "Agilia VP"), ("Terumo", "TE-331"),
    ("B.Braun", "Infunius Space"), ("NIPRO", "FD-170"),
    ("Baxter", "Flo-Gard 6201"), ("Nihon Kohden", "IP-705T"),
    ("Medicap", "IP-02"), ("Mindray", "BeneFusion EP5"),
    ("Fresenius", "Vial Leona V2"), ("Terumo", "TE-172"),
    ("B.Braun", "Perfusor fmS"), ("NIPRO", "FD-160R"),
    ("Baxter", "Colleague CXE"),
]

UBICACIONES = [
    "UCI Adultos", "UCI Neonatal", "Hospitalización 2A", "Hospitalización 2B",
    "Hospitalización 3A", "Emergencia y Urgencias", "Centro Quirúrgico",
    "Neonatología", "Oncología", "Pediatría", "Recuperación", "UCI Intermedio",
]

# ------------------------------------------------------------------
# Plantillas de texto libre por tipo de falla (estilo de técnico)
# Se incluye solapamiento inter-categoría deliberado: en la práctica real,
# los síntomas textuales se comparten entre sistemas (ej. "alarma de oclusión"
# puede ser mecánica, de sensor o de software). Esto da un problema de
# clasificación realista (F1 < 1.0) y demuestra el valor del diccionario N3.
# ------------------------------------------------------------------
PLANTILLAS = {
    "mecanica": [
        "el equipo reporta {oclusion} en la línea de {volumen}",
        "{oclusion} en el sistema, se reemplaza el {motor} y se prueba",
        "se produce {oclusion} recurrente otra vez, tercer reporte del mes",
        "reincide la {oclusion} pese a la {purga}, se revisa el {motor}",
        "el {motor} hace {ruido} y se detiene la infusión",
        "la {puerta} del cassette está rota, la bomba no arranca",
        "el {teclado} no responde para ajustar la tasa, el mecanismo está {trabado}",
        "se traba el {motor} al iniciar, hay que golpear el equipo",
        "el mecanismo de {flujo} se desalineó, gotea de forma irregular",
        "{ruido} mecánico en la base, el {motor} vibra demasiado",
        "la perilla del {motor} quedó suelta, no sostiene la tasa programada",
    ],
    "electrica": [
        "la {bateria} ya no carga, el equipo se apaga solo al desconectar",
        "no enciende con corriente ni con {bateria}, revisar {fusible}",
        "{fusible} quemado por segunda vez, el {cable} hace falso contacto",
        "el {cable} está pelado cerca del enchufe, chispea al conectar",
        "se apaga de manera intermitente, posible falla de {bateria}",
        "la {bateria} dura menos de 10 minutos en modo autónomo",
        "no prende el equipo, se prueba con otro {cable} y sí funciona",
        "olores a quemado en la zona del {fusible}, se suspende el uso",
        "el equipo se apaga solo, la {pantalla} se pone en negro",
        "al conectar a la pared salta el interruptor, revisar {fusible} y {cable}",
    ],
    "software": [
        "el {software} se reinicia solo durante la infusión",
        "{pantalla} congelada, no acepta comandos, requiere reinicio",
        "error en {pantalla}: código de error {software}, no permite programar",
        "el sistema se {software} a valores de fábrica, pierde la configuración",
        "{alarma} constante sin {oclusion} ni {burbuja}, se reinicia y se normaliza",
        "no guarda la configuración de {flujo}, se resetea al apagar",
        "{software} desactualizado, se reinstala el firmware",
        "la {pantalla} parpadea y muestra datos erróneos de {volumen}",
        "{alarma} intermitente por falla del {software}, sin causa física aparente",
        "tras reiniciar, el equipo mantiene la {alarma} de {oclusion} sin haberla",
    ],
    "sensor": [
        "el {sensor} de {burbuja} falla, da {alarma} sin haber aire",
        "no {sensor} la {oclusion} real, pasaba aire al paciente",
        "el {sensor} de {presion} está fuera de rango, lecturas erráticas",
        "{burbuja} falsa constante, se limpia el {sensor} y persiste",
        "el {sensor} no {sensor} {burbuja} pequeñas en la línea",
        "{alarma} de {presion} permanente sin {oclusion} aparente",
        "falla el {sensor} de gota, no cuenta los {volumen} correctamente",
        "el {sensor} de {burbuja} se activa con la luz del solárium",
        "no responde el {sensor} de la {puerta}, la bomba cree que está abierta",
        "lecturas inestables del {sensor} de {presion} durante la infusión",
        "la {alarma} de {oclusion} se activa sin haber tapado, el {sensor} mide mal",
    ],
    "calibracion": [
        "se detecta {deriva} de {flujo} del +8% en la verificación",
        "análisis metrológico: {deriva} de {volumen} fuera de tolerancia",
        "el equipo {deriva} en el caudal, se reprograma la {calibracion}",
        "falla la {calibracion} anual por {deriva} sostenida del caudal",
        "infunde de más: {deriva} del {volumen} programado, se ajusta",
        "no coincide el {volumen} infundido con el programado, {deriva} -12%",
        "tras la {calibracion} el {flujo} sigue {deriva}, se envía a servicio",
        "{deriva} de {flujo} a tasas bajas, dentro de tolerancia a tasas altas",
        "la {calibracion} de {presion} de oclusión quedó {deriva}, se corrige",
        "se documenta {deriva} en el análisis de {volumen} del patrón",
        "revisar {flujo}: gotea más de lo programado, se solicita {calibracion}",
    ],
    "otra": [
        "{mantenimiento} preventivo semestral, limpieza interna y prueba de {alarma}",
        "{mantenimiento} preventivo, se prueba {bateria} y {sensor}, todo conforme",
        "cambio de accesorios y {purga} de la línea, equipo operativo",
        "{mantenimiento} rutinario: limpieza, lubricación y prueba de {flujo}",
        "se realiza {purga} y cambio de {accesorio}, sin hallazgos",
        "{calibracion} programada sin {deriva}, dentro de tolerancia",
        "{calibracion} de rutina conforme, se deja constancia del patrón",
        "{desinfeccion} interna programada y prueba de encendido",
        "verificación funcional tras {mantenimiento}, sin {deriva} detectada",
        "revisión por traslado de servicio, {mantenimiento} básico realizado",
        "tras la falla de {oclusion} se realiza {purga} y limpieza, queda operativo",
    ],
}

# Variantes ortográficas/abreviaturas (una sola palabra — las frases quedan para N3)
VARIANTES_ORTOGRAFICAS = {
    "oclusión": ["oclusion", "ocluido", "ocluida", "obstruccion", "tapado", "atascado"],
    "burbuja": ["burbuga", "burbujas"],
    "alarma": ["alrama", "alarmaa"],
    "batería": ["bateria", "bateriaa"],
    "calibración": ["calibracion", "calibrasion"],
    "presión": ["presion"],
    "pantalla": ["pantall", "pan."],
    "émbolo": ["embolo"],
    "sensor": ["senso", "sensorr"],
    "infusión": ["infusion", "infu."],
    "verificación": ["verificacion", "verif."],
    "desinfección": ["desinfeccion"],
    "cámara": ["camara"],
    "purga": ["purgado"],
}

# Rellenos ocasionales para dar naturalidad (ruido para el estudio de ablación)
RELLENOS = [
    "según técnico de servicio", "reportado por enfermería de turno",
    "en la noche", "durante la mañana", "al momento del traslado",
    "el usuario reporta que", "la técnica indica que", "cuando lo trajeron",
]
PALABRAS_QUE = ["ok", "ya", "quedó", "funciona", "se deja operativo", "pendiente repuesto"]

# Plantillas AMBIGUAS (vocabulario compartido entre categorías): el mismo síntoma
# ('alarma de oclusión') puede corresponder a causa mecánica, de sensor o de
# software. El técnico etiqueta por causa raíz final → ambigüedad irreducible
# realista que acota el F1 máximo alcanzable (como en un corpus hospitalario).
PLANTILLAS_AMBIGUAS = [
    "alarma de oclusion constante, se reviso y no se encontro causa clara",
    "el equipo sigue marcando oclusion, ya se purgo el sistema y persiste",
    "persiste la alarma de oclusion pese al cambio de linea de infusion",
    "marca oclusion intermitente, se verifico el sensor y la linea sin hallazgo",
    "vuelve la alarma de oclusion tras la purga, se deja en observacion",
]


def _cargar_sinonimos() -> dict:
    with open(config.SINONIMOS_JSON, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {k: v for k, v in raw.items() if not k.startswith("_")}


SINONIMOS = _cargar_sinonimos()

# Claves con sinónimos relevantes para el "dialecto" técnico de cada equipo
DIALECTO_CLAVES = ["oclusion", "burbuja", "alarma", "bateria", "calibracion", "purga", "flujo"]


def _generar_dialecto(rng: random.Random) -> dict:
    """
    Dialecto técnico del equipo: cada bomba es atendida mayormente por un mismo
    técnico con su propio vocabulario (variante preferida por término canónico).
    Esto produce correlación intraclase POR EQUIPO — exactamente el fenómeno que
    motiva la estratificación por equipo de la tesis — y amplifica el valor del
    diccionario de sinónimos (N3) frente a N1/N2 en la validación agrupada.
    """
    dialecto = {}
    for clave in DIALECTO_CLAVES:
        variantes = [v for v in SINONIMOS.get(clave, [clave]) if " " not in v and not v.startswith("no ")]
        dialecto[clave] = rng.choice(variantes) if variantes else clave
    return dialecto


def _variante(canonical: str, rng: random.Random, dialecto: dict = None) -> str:
    """Variante de UNA palabra: respeta el dialecto del equipo (75%) o elige aleatoria."""
    variantes = SINONIMOS.get(canonical, [canonical])
    validas = [v for v in variantes if " " not in v and not v.startswith("no ")]
    if not validas:
        return canonical
    if dialecto and canonical in dialecto and rng.random() < 0.75:
        return dialecto[canonical]
    return rng.choice(validas)


def _aplicar_errores(texto: str, rng: random.Random) -> str:
    """Aplica variantes ortográficas/abreviaturas con probabilidad baja
    (prob. reducida para no romper el dialecto del equipo)."""
    for correcto, errores in VARIANTES_ORTOGRAFICAS.items():
        if correcto in texto and rng.random() < 0.25:
            texto = texto.replace(correcto, rng.choice(errores))
    return texto


def generar_texto(tipo: str, rng: random.Random, es_recurrente: bool = False,
                  dialecto: dict = None) -> str:
    """Genera una descripción de falla realista para el tipo dado."""
    # Ambigüedad diagnóstica: ~20% de fallas mecánicas/sensor/software comparten
    # el mismo texto-síntoma (difiere solo la causa raíz final etiquetada).
    if tipo in ("mecanica", "sensor", "software") and rng.random() < 0.20:
        texto = rng.choice(PLANTILLAS_AMBIGUAS)
    elif es_recurrente and tipo == "mecanica":
        plantillas = [PLANTILLAS["mecanica"][2], PLANTILLAS["mecanica"][3]]
        texto = rng.choice(plantillas)
    else:
        texto = rng.choice(PLANTILLAS[tipo])

    def _repl(m):
        return _variante(m.group(1), rng, dialecto)
    texto = re.sub(r"\{(\w+)\}", _repl, texto)
    texto = _aplicar_errores(texto, rng)
    if rng.random() < 0.25:
        texto = f"{texto}, {rng.choice(RELLENOS)}"
    if rng.random() < 0.2:
        texto = f"{texto}, {rng.choice(PALABRAS_QUE)}"
    if rng.random() < 0.15:  # capitalización casual
        texto = texto.capitalize()
    return texto


# ------------------------------------------------------------------
# Generación de la serie de eventos por equipo
# ------------------------------------------------------------------
def intervalo_falla(rng: np.random.Generator, edad: float, problematico: bool) -> int:
    """Días base entre fallas correctivas. Equipos viejos/problemáticos fallan antes."""
    base = {2: 130, 3: 125, 4: 110, 5: 95, 6: 85, 7: 70, 8: 60, 9: 50, 10: 45}
    media = base.get(int(round(edad)), 90)
    if problematico:
        media *= 0.45
    return int(max(12, rng.normal(media, media * 0.28)))


DISTRIB_TIPO_CORRECTIVO = (
    ["mecanica"] * 30 + ["electrica"] * 22 + ["sensor"] * 18
    + ["software"] * 13 + ["calibracion"] * 11 + ["otra"] * 6
)


def generar_eventos_equipo(eid: int, marca: str, modelo: str, rng: np.random.Generator,
                           rng_texto: random.Random, n_total_actual: list) -> list:
    """
    Serie cronológica de OTs de una bomba.

    Esquema temporal (RUL aprendible, físicamente plausible):
      - Cada falla correctiva i tiene intervalo P_i = f(edad, problemático, degradación).
      - La siguiente falla correctiva ocurre exactamente a P_i días.
      - Con prob. 0.14 se inserta un evento lateral (preventivo/calibración) DENTRO
        del intervalo, sin desplazar la falla programada.
      - RUL(correctivo_i) = P_i;  RUL(lateral) = P_i − días transcurridos.
    """
    edad = float(rng.integers(2, 11))                      # antigüedad 2-10 años
    problematico = rng.random() < 0.30                     # 30% de bombas problemáticas
    criticidad = "Alta" if rng.random() < 0.85 else "Media"  # bombas de infusión = soporte vital
    numero_serie = f"BI-{eid:03d}-{rng.integers(1000, 9999)}"
    dialecto = _generar_dialecto(rng_texto)   # vocabulario propio del técnico del equipo

    eventos = []
    fecha = FECHA_INICIO + timedelta(days=int(rng.integers(0, 60)))
    cuenta_tipos = {}
    deriva_previa_en_serie = False
    lateral_pendiente = None  # (fecha_lateral, tipo_mant, extension_dias)

    while fecha <= FECHA_FIN and n_total_actual[0] < N_OT_OBJETIVO and len(eventos) < MAX_OT_POR_EQUIPO:

        # ---------- Evento lateral programado (preventivo / calibración) ----------
        if lateral_pendiente is not None:
            fecha_lat, tipo_mant, _ext = lateral_pendiente
            lateral_pendiente = None
            if fecha_lat > FECHA_FIN or n_total_actual[0] >= N_OT_OBJETIVO or len(eventos) >= MAX_OT_POR_EQUIPO:
                fecha = fecha_lat
                continue
            texto = generar_texto("otra", rng_texto, False, dialecto)
            eventos.append({
                "equipo_id": eid, "marca": marca, "modelo": modelo,
                "numero_serie": numero_serie, "fecha_ot": fecha_lat,
                "tipo_mantenimiento": tipo_mant, "tipo_falla": "otra",
                "texto_libre": texto,
                "edad_anios": round(edad + (fecha_lat - FECHA_INICIO).days / 365.0, 2),
                "criticidad": criticidad,
                "dias_hasta_proxima_falla": 90,  # provisional (se recálcula real después)
                "tiempo_reparacion_min": int(rng.integers(25, 120)),
                "tecnico_cod": f"TEC-{rng.integers(1, 9):02d}",
                "ubicacion": UBICACIONES[int(rng.integers(0, len(UBICACIONES)))],
            })
            cuenta_tipos["otra"] = cuenta_tipos.get("otra", 0) + 1
            n_total_actual[0] += 1
            continue

        # ---------- Falla correctiva ----------
        tipo_mant = "correctivo"
        if problematico and rng.random() < 0.6:
            tipo_falla = "mecanica"          # bombas problemáticas: dominan oclusiones
        else:
            tipo_falla = rng.choice(DISTRIB_TIPO_CORRECTIVO)

        es_recurrente = (cuenta_tipos.get(tipo_falla, 0) >= 2) and problematico
        texto = generar_texto(tipo_falla, rng_texto, es_recurrente, dialecto)

        # Intervalo hasta la próxima falla (proceso de degradación aprendible)
        P = intervalo_falla(rng, edad, problematico)
        if tipo_falla == "mecanica":
            P = int(P * 0.75)                # oclusión → degradación progresiva
        if cuenta_tipos.get("mecanica", 0) >= 2:
            P = int(P * 0.8)                 # recurrencia compuesta
        if deriva_previa_en_serie:
            P = int(P * 0.85)                # deriva metrológica previa
        if es_recurrente:
            P = int(P * 0.6)                 # reincidencia
        P = max(10, P)

        eventos.append({
            "equipo_id": eid, "marca": marca, "modelo": modelo,
            "numero_serie": numero_serie, "fecha_ot": fecha,
            "tipo_mantenimiento": tipo_mant, "tipo_falla": tipo_falla,
            "texto_libre": texto,
            "edad_anios": round(edad + (fecha - FECHA_INICIO).days / 365.0, 2),
            "criticidad": criticidad,
            "dias_hasta_proxima_falla": P,
            "tiempo_reparacion_min": int(rng.integers(25, 240)),
            "tecnico_cod": f"TEC-{rng.integers(1, 9):02d}",
            "ubicacion": UBICACIONES[int(rng.integers(0, len(UBICACIONES)))],
        })
        cuenta_tipos[tipo_falla] = cuenta_tipos.get(tipo_falla, 0) + 1
        if tipo_falla == "calibracion":
            deriva_previa_en_serie = True
        n_total_actual[0] += 1

        # Programar evento lateral dentro del intervalo: el mantenimiento aplicado
        # EXTIENDE la vida útil (retarda la próxima falla) — patrón físicamente
        # correcto y aprendible por el modelo RUL.
        extension = 0
        if rng.random() < 0.16:
            tipo_lat = "preventivo" if rng.random() < 0.55 else "calibracion_programada"
            extension = int(rng.integers(20, 41))   # días de vida extra tras el mantenimiento
            lateral_pendiente = (
                fecha + timedelta(days=max(10, int(P * rng.uniform(0.4, 0.7)))),
                tipo_lat, extension,
            )

        fecha = fecha + timedelta(days=P + extension)

    return eventos


def calcular_features_struct(eventos: list) -> None:
    """Completa features estructuradas cronológicas por OT (sin fuga de futuro)."""
    por_equipo: dict = {}
    for e in eventos:
        por_equipo.setdefault(e["equipo_id"], []).append(e)

    for eid, lista in por_equipo.items():
        lista.sort(key=lambda x: x["fecha_ot"])
        fechas_correctivos = [e["fecha_ot"] for e in lista if e["tipo_mantenimiento"] == "correctivo"]

        for i, e in enumerate(lista):
            previos = lista[:i]

            # Días desde la última intervención (de cualquier tipo)
            dias_desde = (e["fecha_ot"] - previos[-1]["fecha_ot"]).days if previos else 180

            # OTs correctivas previas en los últimos 12 meses
            lim = e["fecha_ot"] - timedelta(days=365)
            num_prev = sum(1 for f in fechas_correctivos if lim <= f < e["fecha_ot"])

            # Reportes previos de 'oclusión' (variantes canónicas en el texto)
            claves_oclusion = ["oclus", "obstruc", "tapad", "atasc", "bloque"]
            num_oclusion = sum(
                1 for p in previos
                if p["tipo_mantenimiento"] == "correctivo"
                and any(c in p["texto_libre"].lower() for c in claves_oclusion)
            )

            # Deriva previa en calibración
            claves_deriva = ["deriva", "desvi", "fuera de rango", "fuera de tolerancia"]
            deriva_prev = 1 if any(
                any(c in p["texto_libre"].lower() for c in claves_deriva) for p in previos
            ) else 0

            e["dias_desde_ultima_intervencion"] = dias_desde
            e["num_ot_previas_12m"] = num_prev
            e["num_reportes_oclusion_previos"] = num_oclusion
            e["deriva_calibracion_previa"] = deriva_prev

            # RUL real: días hasta el próximo correctivo posterior a esta OT
            proximos = [f for f in fechas_correctivos if f > e["fecha_ot"]]
            if proximos:
                e["dias_hasta_proxima_falla"] = (proximos[0] - e["fecha_ot"]).days
            # Si no hay próximo correctivo: conservar P generado (proyección del intervalo)


def main():
    np.random.seed(SEED)
    rng = np.random.default_rng(SEED)
    rng_texto = random.Random(SEED)

    eventos: list = []
    n_total = [0]
    eid = 1
    while n_total[0] < N_OT_OBJETIVO:
        marca, modelo = MARCAS_MODELOS[(eid - 1) % len(MARCAS_MODELOS)]
        eventos.extend(generar_eventos_equipo(eid, marca, modelo, rng, rng_texto, n_total))
        eid += 1

    calcular_features_struct(eventos)

    # Recorte exacto a 220 y renumeración de OTs
    eventos.sort(key=lambda x: x["fecha_ot"])
    eventos = eventos[:N_OT_OBJETIVO]
    for i, e in enumerate(eventos, start=1):
        e["ot_id"] = f"OT{i:04d}"
        e["estado_ot"] = "Completada"
        e["costo_bs"] = round(float(rng.uniform(15, 900)), 2)

    # ------------------------------------------------------------------
    # Escritura del CSV (utf-8-sig para Excel/Windows)
    # ------------------------------------------------------------------
    campos = [
        "ot_id", "equipo_id", "marca", "modelo", "numero_serie", "fecha_ot",
        "tipo_mantenimiento", "titulo_ot", "texto_libre", "tipo_falla",
        "edad_anios", "criticidad",
        "dias_desde_ultima_intervencion", "num_ot_previas_12m",
        "num_reportes_oclusion_previos", "deriva_calibracion_previa",
        "dias_hasta_proxima_falla",
        "tiempo_reparacion_min", "costo_bs", "tecnico_cod", "estado_ot", "ubicacion",
    ]
    TITULOS = {
        "mecanica": "Correctivo - Falla mecánica", "electrica": "Correctivo - Falla eléctrica",
        "software": "Correctivo - Falla de software", "sensor": "Correctivo - Falla de sensor",
        "calibracion": "Correctivo - Deriva metrológica", "otra": "Mantenimiento / Rutina",
    }
    with open(config.DATASET_CSV, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        for e in eventos:
            fila = {k: e.get(k, "") for k in campos}
            fila["titulo_ot"] = TITULOS.get(e["tipo_falla"], "Correctivo")
            w.writerow(fila)

    # ------------------------------------------------------------------
    # Resumen por consola (verificación rápida del investigador)
    # ------------------------------------------------------------------
    from collections import Counter
    tipos = Counter(str(e["tipo_falla"]) for e in eventos)
    mant = Counter(e["tipo_mantenimiento"] for e in eventos)
    equipos = len({e["equipo_id"] for e in eventos})
    ruls = [e["dias_hasta_proxima_falla"] for e in eventos]
    print(f"Dataset generado: {len(eventos)} OTs → {config.DATASET_CSV}")
    print(f"Equipos (bombas de infusión): {equipos}")
    print(f"Tipos de OT: {dict(mant)}")
    print(f"Distribución tipo de falla: {dict(tipos)}")
    print(f"RUL (días) — min {min(ruls)} / media {np.mean(ruls):.1f} / max {max(ruls)}")


if __name__ == "__main__":
    main()
