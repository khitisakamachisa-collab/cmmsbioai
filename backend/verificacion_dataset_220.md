# Verificación del Dataset Sintético 220 OTs (RF07)

> Generado por `generar_dataset_sintetico_220.py` el 2026-10-11 15:52 · semilla determinista RANDOM_SEED=20261 (corridas reproducibles)
> Rango real de fechas: **2026-04-17 → 2026-10-05** (171 días ≈ 5.6 meses) · 220 OTs · 23 equipos

## 1. Distribución de banderas v2.1

| Flag v2.1 | Objetivo (tabla tesis) | Generado | Estado (±5% = ±11) |
|-----------|:---:|:---:|:---:|
| ventana_garantia_reparacion=True | 11 (5%) | 11 | ✅ |
| en_pausa_tecnica=True | 22 (10%) | 22 | ✅ |
| cierre_administrativo=True | 11 (5%) | 11 | ✅ |
| motivo_cancelacion=Falsa_Alarma | 18 (8%) | 18 | ✅ |
| motivo_cancelacion=Error_Usuario | 11 (5%) | 11 | ✅ |
| motivo_cancelacion=Baja_Equipo | 7 (3%) | 7 | ✅ |
| tipo_origen_ot=Sistema/IA | 22 (10%) | 22 | ✅ |
| tipo_origen_ot=Programado | 33 (15%) | 33 | ✅ |
| sub_estado_logistica (variante) | 33 (15%) | 33 | ✅ |
| mdt_excluido_disponibilidad=True | 29 (13%) | 29 | ✅ |
| excluida_de_MTTR=True | 18 (8%) | 18 | ✅ |

**Nota sobre `tipo_origen_ot='Usuario'`:** el total bruto es 165 OTs (75%) porque INCLUYE reincidencias (11), cierres administrativos (11) y canceladas de origen usuario (36). La fila «Usuario 57% ≈ 125» de la tabla de la tesis refiere a las **correctivas normales** (clase A = 107 completadas + 3 abiertas), cuya suma con el resto de clases cierra exactamente 220.

## 2. Distribución de estados finales

| Estado | OTs | % |
|--------|:---:|:---:|
| Completada | 181 | 82.3% |
| Cancelada | 36 | 16.4% |
| En Proceso | 1 | 0.5% |
| Abierta | 1 | 0.5% |
| Esp. Repuesto | 1 | 0.5% |

## 3. OTs por equipo (diversidad de frecuencia)

| Equipo | Criticidad | OTs |
|--------|:---:|:---:|
| Máquina de Hemodiálisis | Crítica | 14 |
| Bomba de Infusión 2 | Alta | 14 |
| Ventilador Neonatal | Crítica | 14 |
| Aspirador de Secreciones | Alta | 14 |
| Ventilador Mecánico | Crítica | 13 |
| Bomba de Nutrición Enteral | Media | 13 |
| Bomba de Infusión 1 | Alta | 13 |
| Electrocardiógrafo GE | Alta | 11 |
| Desfibrilador Zoll | Crítica | 10 |
| Ecógrafo 4D | Alta | 10 |
| Equipo de Rayos X | Alta | 10 |
| Ultrasonido Portátil | Media | 10 |
| Monitor Signos Vitales | Alta | 9 |
| Electrobisturí | Crítica | 9 |
| Monitor Signos Vitales 2 | Alta | 9 |
| Autoclave Steris | Alta | 9 |
| Lámpara Cielítica | Alta | 9 |
| Estimulador Nervioso | Media | 7 |
| Microscopio Olympus | Media | 6 |
| Resonancia Magnética | Crítica | 5 |
| Centrífuga Eppendorf | Media | 5 |
| Cama Hospitalaria Eléctrica | Baja | 3 |
| Balanza Analítica | Media | 3 |

## 4. Ciclo predictivo (OTs Sistema/IA → síntomas → feedback)

- OTs predictivas: **22** · síntomas generados: **36** · feedbacks: **22**
- Resultado real del técnico: Confirmada=15, Falsa_Alarma=5, Parcial=2 (objetivo ~70/20/10%)
- Cada feedback referencia su `symptom_id` y guarda la predicción RUL original (JSON: dias_estimados, confianza, componente).

## 5. Repuestos

- Filas de repuestos: **45** en 45 OTs correctivas (~30%)
- **3 Instalado_Fallido** → sus OTs de reincidencia llevan `es_reparacion_inefectiva=True` (cadena repuesto defectuoso → falla infantil, entrenable por PLN y por reglas).

## 6. Consistencias verificadas

- ✅ ventana_garantia_reparacion=True: 11 (objetivo 11 = 5%)
- ✅ en_pausa_tecnica=True: 22 (objetivo 22 = 10%)
- ✅ cierre_administrativo=True: 11 (objetivo 11 = 5%)
- ✅ motivo_cancelacion=Falsa_Alarma: 18 (objetivo 18 = 8%)
- ✅ motivo_cancelacion=Error_Usuario: 11 (objetivo 11 = 5%)
- ✅ motivo_cancelacion=Baja_Equipo: 7 (objetivo 7 = 3%)
- ✅ tipo_origen_ot=Sistema/IA: 22 (objetivo 22 = 10%)
- ✅ tipo_origen_ot=Programado: 33 (objetivo 33 = 15%)
- ✅ sub_estado_logistica (variante): 33 (objetivo 33 = 15%)
- ✅ mdt_excluido_disponibilidad=True: 29 (objetivo 29 = 13%)
- ✅ excluida_de_MTTR=True: 18 (objetivo 18 = 8%)
- ✅ Reincidencias: nacimiento 0<Δ<72 h tras resolución del padre (11 OTs)
- ✅ Bitácora: pares pausada→reanudada = pausa declarada (sin doble conteo)
- ✅ Sin fechas futuras (última resolución ≤ ahora−1h)
- ✅ Historia amplia para RUL: span=171 días (objetivo ~180)
- ✅ Feedback predictivo completo: 22 de 22 IA
- ✅ Distribución feedback ~70/20/10: {'Confirmada': 15, 'Falsa_Alarma': 5, 'Parcial': 2}
- ✅ Repuestos: 45 filas en 45 correctivas (objetivo ~30% de 140 = 42)
- ✅ Repuestos Instalado_Fallido = 3 (objetivo ~3, ligados a es_reparacion_inefectiva)
- ✅ Textos no repetitivos: 220/220 únicos (100%)

## 7. Muestras de textos libres generados (para PLN)

- `OT 500` (D_programado): «Preventivo programado según plan: inspección, limpieza y pruebas de seguridad.»
- `OT 501` (A_correctiva): «El personal indica: error 0x2F en pantalla y se bloquea tras el corte de energía»
- `OT 502` (A_correctiva): «Se reporta que no conecta a la red del hospital»
- `OT 503` (A_correctiva): «El personal indica: bisagra floja en el panel lateral»
- `OT 504` (A_correctiva): «El personal indica: el interruptor principal no responde desde ayer»
- `OT 505` (B_reincidencia): «Falla repetida: Usuario refiere que pieza suelta dentro del gabinete tras el corte de energía»
- `OT 506` (G_error_usuario): «El usuario no conectó el cable de paciente; reporte infundado.»
- `OT 507` (F_falsa_alarma): «Usuario reporta el equipo 'dañado'; verificado y funciona.»

## 8. Cómo consumirlo en los experimentos RF07

```python
import pandas as pd
df  = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='OTs Dataset v2.1')
tx  = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='TextosPLN')
snt = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='Sintomas')
fb  = pd.read_excel('dataset_sintetico_220_ot.xlsx', sheet_name='FeedbackPredictivo')
# PLN:  tx.descripcion_falla → X; tx.clase_dataset / familia_falla → y
# RUL:  fechas + tiempo_pausa_acumulado + horizonte por equipo
# XAI:  variables de la OT + feedback como etiqueta de realimentación
```
