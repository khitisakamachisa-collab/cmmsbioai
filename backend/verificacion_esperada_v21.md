# REPORTE DE VERIFICACIÓN ESPERADA — Dataset Demo v2.1

_Generado por `generar_demo_v21.py` el 2026-10-11 16:02:54._
_Ancla temporal: OTs entre **2026-09-26 05:02:54** y **2026-10-11 15:02:54** (fechas relativas a la ejecución)._
_Fecha de adquisición aplicada a los 13 equipos: **2026-09-11** (hoy − 30 días → ventana de 720 h calendario)._

> **NOTA DE PRECISIÓN:** el motor v2.1.2 mide la ventana en **días completos desde
> `fecha_adquisicion` hasta HOY**. Los valores de MTBF/Disponibilidad cuadran
> exacto si la verificación se hace **el mismo día** de la generación/importación.
> Si verificas días después, la ventana crece 24 h por día (MDT, MTTR y los
> contadores n_* NO cambian; solo MTBF y Disponibilidad se desplazan levemente).

## Instrucciones de Uso

1. Ejecutar: `python generar_demo_v21.py` (genera los 3 archivos junto al script)
2. **Ruta recomendada para las OTs:** `python generar_demo_v21.py --importar`
   (importa equipos + OTs 101-115 directamente en `cmms_bioai.db`, genera la
   bitácora nativa y **auto-valida contra el motor v2.1**).
   *Nota: el CMMS v2.1.2 aún no tiene importador Excel de OTs; el Excel
   `demo_ordenes_trabajo_v21.xlsx` queda como formato de referencia/respaldo.*
3. Alternativa por UI para equipos: Configuración → "Limpiar Base de Datos" →
   "Cargar datos TEST" → Equipos → "Importar Excel" con `demo_equipos_v21.xlsx`.
   ⚠ Si los 13 equipos YA existen en tu BD (p. ej. creados antes con series
   `V21-*`), NO importes ese Excel: el importador oficial busca por
   `numero_serie` y crearía duplicados; `--importar` reutiliza por nombre.
   (ojo: el importador oficial de equipos no persiste `tipo_equipo` ni
   `criticidad`; `--importar` sí lo hace).
4. Reiniciar uvicorn y abrir **Reportes → MTBF/MTTR** (o `/reportes/mtbf-mttr`).
5. Comparar con los valores esperados de este reporte.

## Verificaciones por OT

### OT 101 (Bomba de Infusión 1 — Falla en motor)
- **Estado:** Completada
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 1.5 h (brutas 1.50 h)
- **MDT esperado (creación→resolución):** 3.00 h
- **Regla probada:** Línea base
- **Verificar en reporte:** Equipo "Bomba de Infusión 1" debe mostrar n_fallas_correctivas=2, n_fallas_reales=1 (junto a OT 102)

### OT 102 (Bomba de Infusión 1 — Reincidencia falla motor)
- **Estado:** Completada
- **ventana_garantia_reparacion:** True
- **es_reparacion_inefectiva:** True
- **parent_ot_id:** 101
- **failure_sequence:** 2
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 1.5 h (brutas 1.50 h)
- **MDT esperado (creación→resolución):** 3.00 h
- **Regla probada:** Regla 3 (Ventana 72 h)
- **Verificar en reporte:** n_excluidas_garantia=1; MTBF calculado con 1 sola falla real; la reincidencia SÍ aporta al MTTR (1.5 h)

### OT 103 (Monitor Signos Vitales — Monitor no enciende)
- **Estado:** Cancelada
- **mdt_excluido_disponibilidad:** True
- **motivo_cancelacion:** Falsa_Alarma
- **MTTA esperado (creación→asignación):** 0.50 h
- **MTTR_Hombre esperado:** — (OT cancelada sin trabajo registrado)
- **MDT esperado (creación→resolución):** 0.50 h
- **Regla probada:** Regla 4 (Falsa Alarma en Abierta)
- **Verificar en reporte:** Equipo "Monitor Signos Vitales": mdt_excluido_horas total = 1.25 h (0.5 de esta OT + 0.75 de la OT 104); Disponibilidad = 100%

### OT 104 (Monitor Signos Vitales — Alarma de obstrucción)
- **Estado:** Cancelada
- **mdt_excluido_disponibilidad:** True
- **motivo_cancelacion:** Error_Usuario
- **MTTA esperado (creación→asignación):** 0.33 h
- **MTTR_Hombre esperado:** 0.2 h (brutas 0.25 h)
- **MDT esperado (creación→resolución):** 0.75 h
- **Regla probada:** Regla 4 (Error Usuario en Proceso)
- **Verificar en reporte:** mdt_excluido_horas acumulado del Monitor = 1.25 h (0.5 + 0.75); Disponibilidad = 100%

### OT 105 (Ecógrafo 4D — Falla tarjeta procesamiento)
- **Estado:** Completada
- **sub_estado_logistica:** En_Aduana
- **horas_espera_repuesto:** 267.5
- **MTTA esperado (creación→asignación):** 2.00 h
- **MTTR_Hombre esperado:** 0.0 h (brutas 267.50 h)
- **MDT esperado (creación→resolución):** 270.00 h
- **Regla probada:** Logística larga
- **Verificar en reporte:** MTTR=0.0 h; Disponibilidad=62.5%; mdt_valido_horas=270.0

### OT 106 (Equipo de Rayos X — Falla en mesa)
- **Estado:** Completada
- **en_pausa_tecnica:** True (motivo=Emergencia_Clinica, tiempo_pausa_acumulado=4.0 h)
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 2.5 h (brutas 6.50 h)
- **MDT esperado (creación→resolución):** 8.00 h
- **Regla probada:** Reglas 11-14 (Pausa por emergencia)
- **Verificar en reporte:** MTTR=2.5 h (no 6.5 h); Disponibilidad=98.9%

### OT 107 (Máquina de Hemodiálisis — Paro durante tratamiento)
- **Estado:** Completada
- **MTTA esperado (creación→asignación):** 0.25 h
- **MTTR_Hombre esperado:** 2.0 h (brutas 2.00 h)
- **MDT esperado (creación→resolución):** 2.50 h
- **Regla probada:** Línea base (emergencia atendida)
- **Verificar en reporte:** MTTR=2.0 h; Disponibilidad=99.7%

### OT 108 (Resonancia Magnética — Falla criogénica)
- **Estado:** Completada
- **cierre_administrativo:** True
- **excluida_de_MTTR:** True
- **MTTA esperado (creación→asignación):** 4.00 h
- **MTTR_Hombre esperado:** 122.0 h (brutas 122.00 h)
- **MDT esperado (creación→resolución):** 128.00 h
- **Regla probada:** Regla 6 (Cierre administrativo)
- **Verificar en reporte:** n_excluidas_mttr=1, n_validas_mttr=0, MTTR=None; mdt_valido_horas=128.0; Disponibilidad=82.2%

### OT 109 (Ventilador Mecánico — Falla de compresión)
- **Estado:** Completada
- **tipo_origen_ot:** Sistema/IA, tipo_impacto=PRECAUTORIO
- **MTTA esperado (creación→asignación):** 2.00 h
- **MTTR_Hombre esperado:** 1.5 h (brutas 1.50 h)
- **MDT esperado (creación→resolución):** 4.00 h
- **Regla probada:** Regla 15 (OT predictiva de IA)
- **Verificar en reporte:** n_programadas=0 (es falla correctiva real aunque origen=IA); MTTR=1.5 h; Disponibilidad=99.4%

### OT 110 (Desfibrilador Zoll — No carga batería)
- **Estado:** Cancelada
- **excluida_de_MTTR:** True
- **motivo_cancelacion:** Baja_Equipo
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 97.5 h (brutas 97.50 h)
- **MDT esperado (creación→resolución):** 99.00 h
- **Regla probada:** Regla 4+5 (Baja de equipo)
- **Verificar en reporte:** mdt_valido_horas=99.0 (SÍ cuenta); Disponibilidad=86.2% (no 100%); MTTR=None

### OT 111 (Centrífuga Eppendorf — Mantenimiento Preventivo)
- **Estado:** Completada
- **tipo_origen_ot:** Programado, tipo_impacto=PROGRAMADO
- **MTTA esperado (creación→asignación):** 0.00 h
- **MTTR_Hombre esperado:** 1.0 h (brutas 1.00 h)
- **MDT esperado (creación→resolución):** 1.50 h
- **Regla probada:** Línea base (MP programado)
- **Verificar en reporte:** n_programadas=1; NO cuenta como falla correctiva, no aporta al MTTR y NO suma MDT (Disponibilidad=100%)

### OT 112 (Autoclave Steris — Falla de puerta)
- **Estado:** Completada
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 1.5 h (brutas 1.50 h)
- **MDT esperado (creación→resolución):** 3.00 h
- **Regla probada:** Línea base (reparación normal)
- **Verificar en reporte:** MTTR=1.5 h; Disponibilidad=99.6%

### OT 113 (Microscopio Olympus — Lámpara fundida)
- **Estado:** Completada
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 0.5 h (brutas 0.50 h)
- **MDT esperado (creación→resolución):** 1.75 h
- **Regla probada:** Línea base (repuesto en stock)
- **Verificar en reporte:** MTTR=0.5 h; Disponibilidad=99.8%

### OT 114 (Balanza Analítica — Desviación de calibración)
- **Estado:** Completada
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 1.5 h (brutas 1.50 h)
- **MDT esperado (creación→resolución):** 3.00 h
- **Regla probada:** Línea base (calibración)
- **Verificar en reporte:** MTTR=1.5 h; Disponibilidad=99.6%

### OT 115 (Electrocardiógrafo GE — Error de software)
- **Estado:** Completada
- **MTTA esperado (creación→asignación):** 1.00 h
- **MTTR_Hombre esperado:** 0.5 h (brutas 0.50 h)
- **MDT esperado (creación→resolución):** 2.00 h
- **Regla probada:** Línea base (software)
- **Verificar en reporte:** MTTR=0.5 h; Disponibilidad=99.7%

## Verificaciones Globales (Reportes → MTBF/MTTR)

### MTBF
- **Bomba de Infusión 1:** n_fallas_correctivas=2, n_fallas_reales=1,
  n_excluidas_garantia=1 (OT 102 sale del denominador por Regla 3).
- **MTBF esperado:** 714.0 h = (720 h calendario − 6.0 h MDT) / 1 falla real.
- **Advertencia esperada:** "Basado en 1 fallas (mínimo recomendado: 3)".

### MTTR (horas ACTIVAS: brutas − pausas − espera de repuestos)
| Equipo | MTTR esperado | Detalle |
|---|---|---|
| Bomba de Infusión 1 | 1.5 h | (1.5 + 1.5) / 2 — la reincidencia SÍ aporta a MTTR (Regla 3) |
| Monitor Signos Vitales | — (None) | sin fallas completadas (103/104 canceladas) |
| Ecógrafo 4D | 0.0 h | 267.5 h brutas − 267.5 h logística = 0 |
| Equipo de Rayos X | 2.5 h | 6.5 h brutas − 4.0 h pausa (Reglas 11-14) |
| Máquina de Hemodiálisis | 2.0 h | reparación directa |
| Resonancia Magnética | — (None) | n_validas_mttr=0 (OT 108 excluida, Regla 6); n_excluidas_mttr=1 |
| Ventilador Mecánico | 1.5 h | OT de IA (Sistema/IA sí es falla real) |
| Desfibrilador Zoll | — (None) | cancelada (Baja_Equipo) |
| Centrífuga Eppendorf | — (None) | n_programadas=1 (MP no es falla) |
| Autoclave Steris | 1.5 h | reparación directa |
| Microscopio Olympus | 0.5 h | reparación directa |
| Balanza Analítica | 1.5 h | calibración correctiva |
| Electrocardiógrafo GE | 0.5 h | reparación directa |

- **Referencia global (manual):** suma activas 13.0 h / 10 OTs válidas = **1.30 h**.
  ⚠ La spec original sumaba 11 términos (incl. OT 111 = 1.0 h) → 1.27 h; el motor
  v2.1 **excluye las OTs `Programado` del MTTR** (no son fallas correctivas), por
  lo que la cifra correcta contra la que muestra el CMMS es **1.30 h**. El promedio
  oficial es POR EQUIPO (tabla anterior), no global.

### Disponibilidad = (horas calendario − MDT válido) / horas calendario
| Equipo | Disponibilidad esperada | Motivo |
|---|---|---|
| Monitor Signos Vitales | **100.0 %** | único MDT (0.5 + 0.75 h) excluido por Regla 4 |
| Centrífuga Eppendorf | **100.0 %** | MP programado: no es falla → no suma MDT |
| Desfibrilador Zoll | **86.2 %** | MDT de la baja (99.0 h) SÍ cuenta (Regla 4+5) |
| Ecógrafo 4D | **62.5 %** | logística larga: MDT 270.0 h de 720 h |
| Resonancia Magnética | 82.2 % | MDT 128.0 h (cierre administrativo SÍ cuenta) |
| Ventilador Mecánico | 99.4 % | MDT 4.0 h |
| Bomba de Infusión 1 | 99.2 % | MDT 6.0 h (2 fallas × 3 h) |
| Equipo de Rayos X | 98.9 % | MDT 8.0 h |
| Autoclave Steris | 99.6 % | MDT 3.0 h |
| Balanza Analítica | 99.6 % | MDT 3.0 h |
| Electrocardiógrafo GE | 99.7 % | MDT 2.0 h |
| Máquina de Hemodiálisis | 99.7 % | MDT 2.5 h |
| Microscopio Olympus | 99.8 % | MDT 1.75 h |

- **MDT excluido global (Regla 4):** 0.5 h (OT 103) + 0.75 h (OT 104) = 1.25 h
  (el reporte lo muestra como **1.2** por redondeo a 1 decimal).

## Checklist de Verificación
- [ ] OT 102 tiene ventana_garantia=True y se creó a 48 h de la resolución de la OT 101
- [ ] OT 103/104 tienen mdt_excluido_disponibilidad=True
- [ ] OT 105 tiene horas_espera_repuesto=267.5 y MTTR=0.0
- [ ] OT 106 tiene tiempo_pausa_acumulado=4.0 y MTTR=2.5 (no 6.5)
- [ ] OT 108 tiene cierre_administrativo=True y el equipo muestra MTTR=None
- [ ] OT 110 tiene mdt_excluido_disponibilidad=False (el MDT de 99 h SÍ cuenta)
- [ ] Bomba de Infusión 1 muestra la advertencia de MTBF con n<3
- [ ] Centrífuga Eppendorf muestra n_programadas=1 y no afecta MTTR
- [ ] Ventilador Mecánico es tipo_origen=Sistema/IA y SÍ cuenta como falla real
