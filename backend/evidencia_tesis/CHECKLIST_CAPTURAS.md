# CHECKLIST DE CAPTURAS — Capítulo IV (Evidencia del Motor v2.1)

> Generado automáticamente por `exportar_evidencia_tesis.py` el 2026-10-11 15:49.
> Motor de métricas: **v2.1.3** · Dataset demo: OTs 101–115 · Equipos: 21
> Los valores entre corchetes **[ ]** son los que la BD reporta AHORA: tu captura
> debe mostrar exactamente esos números. Si re-importas el demo
> (`python generar_demo_v21.py --importar`), regenera este checklist.

## 0. Preparación (antes de capturar)

1. Backend activo: `venv\Scripts\activate` → `uvicorn main:app --reload` (puerto 8000).
2. Frontend activo: `cd frontend && npm run dev` (puerto 5173).
3. Recomendado: re-ejecutar `python generar_demo_v21.py --importar` **el mismo día**
   de las capturas → fecha_adquisicion = hoy−30d y los porcentajes de Disponibilidad
   cuadran exactos con `verificacion_esperada_v21.md` (38/38 checks OK).
4. Navegador a ~90% de zoom, tema claro; para anotar: recuadro rojo + leyenda «Figura N».
5. Convención de nombres: `fig_capIV_<n>_<tema>.png`.

## 1. Reporte MTBF / MTTR / Disponibilidad (núcleo del Cap. IV)

Frontend: `http://localhost:5173/reportes` → pestaña **«MTBF / MTTR / Dispon.»**

### Fig. 1 — Tabla completa del reporte (evidencia central)
- **Qué destacar:** la tabla completa; recuadro en la fila **Bomba de Infusión 1**.
- **Valores que debe mostrar:** n_fallas_correctivas=[2] ·
  n_excluidas_garantia=[1] · n_fallas_reales=[1] ·
  MTBF=[762.0] h · MTTR=[1.5] h · advertencia_mtbf visible.
- **Regla v2.1 que demuestra:** Regla 3 (Ventana de Garantía 72 h) — la reincidencia
  (OT 102 a 48 h) NO es falla nueva para MTBF, pero SÍ aporta al MTTR.
- **Anotación sugerida:** «Figura X. Reporte MTBF/MTTR v2.1. La reincidencia dentro de la
  ventana de garantía de 72 h se excluye del denominador del MTBF (n_excluidas_garantia=1)
  mientras sigue aportando al MTTR (1.5 h), según las reglas de negocio implementadas.»

### Fig. 2 — Regla 6: cierre administrativo no infla el MTTR
- **Qué destacar:** fila **Resonancia Magnética**.
- **Valores:** n_excluidas_mttr=[1] · n_validas_mttr=[0] ·
  MTTR=[—] (None = sin OTs válidas) · disponibilidad=[83.3] %.
- **Regla:** Regla 6 (Cierre Administrativo) — las 122 h de la OT 108 quedan fuera del
  promedio de eficiencia técnica y visibles solo como desglose en Tiempos por Etapa.
- **Anotación:** «El cierre administrativo (OT 108) se excluye del MTTR
  (n_excluidas_mttr=1) para no inflar artificialmente la eficiencia del técnico.»

### Fig. 3 — Reglas 11-14: MTTR con horas ACTIVAS
- **Qué destacar:** filas **Ecógrafo 4D** y **Equipo de Rayos X** (juntas, misma captura).
- **Valores:** Ecógrafo MTTR=[0.0] h con MDT=[270.0] h y
  disponibilidad=[64.8] %; Rayos X MTTR=[2.5] h.
- **Regla:** Reglas 11-14 (Pausa por Emergencia + Logística) — la espera logística de
  267.5 h (OT 105) NO infla la eficiencia (MTTR=0) y la pausa técnica de 4 h (OT 106)
  se descuenta del tiempo bruto (MTTR=2.5 h = 6.5−4).
- **Anotación:** «El MTTR usa horas de reparación activas: la espera logística (11 días)
  y la pausa por emergencia clínica se descuentan del tiempo bruto, evitando sobrestimar
  la ineficiencia técnica.»

### Fig. 4 — Regla 4: disponibilidad y MDT excluido
- **Qué destacar:** filas **Monitor Signos Vitales** y **Desfibrilador Zoll** (misma captura).
- **Valores:** Monitor disponibilidad=[100.0] % con
  mdt_excluido_horas=[1.2] h; Desfibrilador
  disponibilidad=[87.1] % con mdt_valido_horas=[99.0] h.
- **Regla:** Regla 4 (Falsa Alarma / Error de Usuario no restan) y Regla 4+5 (la Baja de
  Equipo SÍ suma MDT aunque no entra al MTTR).
- **Anotación:** «Las falsas alarmas y errores de usuario se excluyen de la
  indisponibilidad (MDT excluido reportado por transparencia); la baja del desfibrilador
  sí penaliza la disponibilidad del servicio.»

### Fig. 5 — Bloque "reglas_v21" del payload (opcional, nivel API)
- Endpoint directo: `http://127.0.0.1:8000/reportes/mtbf-mttr` (JSON en el navegador).
- **Qué destacar:** el bloque `reglas_v21` (contadores globales de exclusiones) y
  `definiciones.version_motor` = v2.1.3.
- **Uso:** demuestra que las reglas son Trazables y auditables desde la API.

## 2. Tiempos por Etapa (KPIs del flujo v1.1 + desglose v2.1)

Frontend: `http://localhost:5173/reportes` → pestaña **«Tiempos por Etapa»**

### Fig. 6 — Resumen de etapas
- **Qué destacar:** tarjetas/promedios: MTTA=[1.07] h ·
  reacción=[0.52] h · reparación bruta=[36.09] h ·
  espera repuesto=[135.75] h · activa=[16.70] h ·
  tasas de cancelación/reapertura/reincidencia.
- **Regla:** flujo v1.1.0 (MTTA → reacción → reparación bruta → activa) con piso de
  pausa v2.1.3 (sin doble conteo).
- **Anotación:** «KPIs por etapa del flujo de trabajo; la espera de repuestos se mide
  con los pares pausada→reanudada de la bitácora.»

### Fig. 7 — Desglose de OT 105 (logística pura)
- **Qué destacar:** fila **OT 105** en la tabla por OT.
- **Valores:** espera repuesto=[267.5] h ·
  activas=[0.0] h · brutas=[267.5] h.
- **Regla:** Logística larga (11 días) — muestra el cuello de botella de repuestos.
- **Anotación:** «La OT 105 evidencia espera logística de 267.5 h con 0 h de trabajo
  activo: el cuello de botella es el proceso de compras, no el técnico.»

### Fig. 8 — Desglose de OT 106 (pausa por emergencia)
- **Qué destacar:** fila **OT 106**.
- **Valores:** espera (pausa técnica)=[4.0] h ·
  activas=[2.5] h.
- **Regla:** Reglas 11-14 — pausa por emergencia clínica descontada del tiempo activo.
- **Anotación:** «La reparación activa (2.5 h) es la reparación bruta (6.5 h) menos la
  pausa por emergencia (4.0 h).»

### Fig. 9 — Desglose de OT 108 y OT 110 (transparencia de exclusiones)
- **Qué destacar:** filas **OT 108** (activas=[122.0] h,
  cierre administrativo visible) y **OT 110** (Baja_Equipo).
- **Regla:** Regla 6 + Regla 4+5.
- **Anotación:** «Las exclusiones del MTTR permanecen visibles en el desglose por etapa:
  el sistema no oculta la información, solo la clasifica correctamente.»

## 3. Flujo de OTs y ciclo predictivo (RF07 / Regla 15)

### Fig. 10 — Listado de OTs con estados del flujo
- URL: `http://localhost:5173/ordenes`
- **Qué destacar:** OTs 101–115 con estados (Completada / Cancelada / Esp. Repuesto) y
  banderas v2.1 visibles (reincidencia OT 102 vinculada a 101 si el listado lo muestra).
- **Uso:** evidencia del flujo v1.1 operando con el dataset demo.

### Fig. 11 — Detalle OT 109 (predictiva IA): síntomas + feedback
- URL: `http://localhost:5173/ordenes` → abrir el detalle de la **OT 109**.
- **Qué destacar:** síntoma de origen **Sistema/IA** («Predicción RUL: degradación de
  válvula de compresión», con `dias_estimados: 7, confianza: 0.85`) y el
  **feedback predictivo** con resultado real del técnico = Confirmada.
- **Regla:** Regla 15 (OT Predictiva de IA) + ciclo de realimentación H2 (RF07).
- **Anotación:** «La OT generada por la IA anexa evidencia (síntoma con predicción RUL)
  y cierra el ciclo con el veredicto del técnico: insumo directo para recalibrar el modelo.»

### Fig. 12 — Bitácora de la OT 106 (pares pausada→reanudada)
- URL: `http://localhost:5173/ordenes` → detalle OT 106 → bitácora/historial.
- **Qué destacar:** eventos `pausada` (motivo emergencia) y `reanudada` con horarios
  que suman 4.0 h.
- **Regla:** Reglas 11-14 — la pausa técnica queda trazada en bitácora (fuente de la
  verdad del motor).
- **Anotación:** «La duración de la pausa se reconstruye de la bitácora: trazabilidad
  completa del tiempo no productivo.»

## 4. Contexto del sistema (capítulo de implementación)

### Fig. 13 — Dashboard general
- URL: `http://localhost:5173/inicio`
- **Uso:** vista general del CMMS operando (OTs, equipos, alertas).

### Fig. 14 — Equipos con criticidad y tipo (enriquecimiento v2.1)
- URL: `http://localhost:5173/equipos`
- **Qué destacar:** columna de criticidad (Crítica/Alta/Media) y tipo_equipo de los
  13 equipos demo.
- **Uso:** muestra el modelo de datos enriquecido que usa el motor (tipo_equipo para
  agregación por tipo).

### Fig. 15 — Panel Predictivo RF07
- URL: `http://localhost:5173/predictivo`
- **Qué destacar:** cabecera «Modelo híbrido interpretable (PLN + RUL + XAI/SHAP)»,
  tarjetas de métricas y estudio de ablación (si hay entrenamiento previo; si no,
  captura del panel vacío indicándolo).
- **Uso:** sección RF07 del Cap. IV (alimentará con dataset_sintetico_220_ot.xlsx).

## 5. Evidencia de exportación (CSV para análisis estadístico)

### Fig. 16 — CSV exportado desde la UI
- Botón de exportación de la pestaña «MTBF / MTTR / Dispon.» (abre
  `http://127.0.0.1:8000/reportes/mtbf-mttr?formato=csv`) y del reporte
  «Tiempos por Etapa» (`.../reportes/tiempos-etapa?formato=csv`).
- **Qué destacar:** el CSV abierto en Excel con las 24 columnas del motor
  (una fila por equipo).
- **Anotación:** «El sistema exporta el reporte con las métricas por equipo para el
  análisis estadístico del Cap. IV (los archivos de esta misma carpeta evidencia_tesis/
  provienen de esos mismos endpoints).»

## 6. Tabla resumen

| # | URL / pestaña | Elemento a destacar | Regla v2.1 |
|---|---------------|---------------------|------------|
| 1 | /reportes → «MTBF / MTTR / Dispon.» | Bomba (exclusión garantía) | Regla 3 |
| 2 | idem | Resonancia (excluida de MTTR) | Regla 6 |
| 3 | idem | Ecógrafo + Rayos X (activas) | Reglas 11-14 |
| 4 | idem | Monitor + Desfibrilador (MDT) | Regla 4 / 4+5 |
| 5 | /reportes/mtbf-mttr (API JSON) | bloque reglas_v21 | Trazabilidad |
| 6 | /reportes → «Tiempos por Etapa» | tarjetas resumen | Flujo v1.1 |
| 7 | idem | OT 105 (espera 267.5 h) | Logística |
| 8 | idem | OT 106 (pausa 4 h) | Reglas 11-14 |
| 9 | idem | OT 108 / OT 110 | Regla 6 / 4+5 |
| 10 | /ordenes | estados del flujo | Flujo v1.1 |
| 11 | /ordenes → OT 109 | síntomas + feedback IA | Regla 15 / RF07 |
| 12 | /ordenes → OT 106 bitácora | pausada→reanudada | Reglas 11-14 |
| 13 | /inicio | dashboard general | Contexto |
| 14 | /equipos | criticidad + tipo_equipo | Modelo v2.1 |
| 15 | /predictivo | panel RF07 | RF07 |
| 16 | exportación CSV | 24 columnas motor | Análisis Cap. IV |

## 7. Notas de estabilidad numérica (importante para redactar)

- **Estables** (no cambian con el día): MDT válido, MTTR, MTBF y todos los desgloses
  por etapa (son diferencias de fechas fijas de las OTs).
- **Dependen del día** (ventana calendario desde fecha_adquisicion): `disponibilidad_pct`
  y `horas_calendario`. Suben ~0.1–2 pp por día transcurrido tras la importación.
  Por eso: **re-importa y captura el mismo día** (ver §0.3).
- La coherencia entre `/reportes/mtbf-mttr`, `/reportes/mtbf`, `/reportes/mttr` y
  `/reportes/disponibilidad` está verificada (mismo payload del motor v2.1.3).
- CSVs de esta carpeta: salida EXACTA de esos endpoints (sin post-proceso), aptos
  como anexo digital de la tesis.
