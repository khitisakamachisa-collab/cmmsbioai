<script setup>
// ============================================================
// CMMS-BioAI v1.0.0 — RF07 Módulo Predictivo (PLN + RUL + XAI)
// Dashboard predictivo SOLO para Bombas de Infusión (tesis).
// Semáforo RUL · explicación SHAP · ablación N1/N2/N3 · métricas H1/H3.
// ============================================================
import { ref, onMounted, computed, nextTick } from 'vue'
import { Chart, registerables } from 'chart.js'
import apiClient from '../services/api.js'

Chart.register(...registerables)

// ---------- Estado ----------
const cargando = ref(false)
const entrenando = ref(false)
const mensaje = ref('')
const mensajeTipo = ref('info') // info | ok | error
const estadoIA = ref(null)
const metricas = ref(null)
const ablacion = ref(null)
const resumen = ref(null)
const seleccionada = ref(null)
const detalle = ref(null)
const h3 = ref(null)
const detalleCargando = ref(false)

// Gráficos
const chartShap = ref(null)
const chartImportancia = ref(null)
const chartProbs = ref(null)
let instanciaShap = null
let instanciaImportancia = null
let instanciaProbs = null

// ---------- Computed ----------
const hayModelos = computed(() => estadoIA.value?.entrenado === true)

const metricasCards = computed(() => {
  const m = metricas.value
  if (!m) return []
  const cls = m.clasificacion || {}
  const reg = m.regresion || {}
  return [
    { titulo: 'F1-Score (macro)', valor: fmt(cls.f1_macro), sub: 'Clasificación de fallas', color: '#2563eb' },
    { titulo: 'AUC-ROC (OvR)', valor: fmt(cls.auc_roc_ovr), sub: 'Discriminación', color: '#7c3aed' },
    { titulo: 'RMSE RUL', valor: reg.rmse_dias != null ? `${reg.rmse_dias} d` : '—', sub: 'Error cuadrático medio', color: '#d97706' },
    { titulo: 'MAE RUL', valor: reg.mae_dias != null ? `${reg.mae_dias} d` : '—', sub: 'Error absoluto medio', color: '#16a34a' },
  ]
})

const resumenOrdenado = computed(() => resumen.value?.bombas || [])

const conteoSem = computed(() => resumen.value?.conteo_semaforo || { rojo: 0, amarillo: 0, verde: 0, sin_datos: 0 })

const ablacionTabla = computed(() => ablacion.value?.tabla_comparativa || [])
const ablacionPrueba = computed(() => ablacion.value?.prueba_estadistica_n3_vs_n2 || null)

function fmt(v) {
  if (v === null || v === undefined) return '—'
  return typeof v === 'number' ? v.toFixed(4).replace(/0+$/, '').replace(/\.$/, '') : v
}

function fmtMs(v) {
  if (v === null || v === undefined) return '—'
  return v >= 100 ? `${Math.round(v)} ms` : `${v.toFixed(1)} ms`
}

function semaforoColor(b) {
  return b?.semaforo?.color || '#9ca3af'
}

function semaforoEtiqueta(b) {
  return b?.semaforo?.etiqueta || 'Sin datos'
}

// ---------- Carga de datos ----------
async function cargarTodo() {
  cargando.value = true
  mensaje.value = ''
  try {
    const [est, met, abl, res, h3r] = await Promise.allSettled([
      apiClient.get('/ia/estado'),
      apiClient.get('/ia/metricas'),
      apiClient.get('/ia/ablation'),
      apiClient.get('/ia/resumen'),
      apiClient.get('/ia/h3'),
    ])
    if (est.status === 'fulfilled') estadoIA.value = est.value.data
    if (met.status === 'fulfilled') metricas.value = met.value.data
    if (abl.status === 'fulfilled') ablacion.value = abl.value.data
    if (res.status === 'fulfilled') resumen.value = res.value.data
    if (h3r.status === 'fulfilled') h3.value = h3r.value.data
    await nextTick()
    renderImportancia()
    if (resumenOrdenado.value.length && !seleccionada.value) {
      await seleccionarBomba(resumenOrdenado.value[0])
    }
  } catch (e) {
    mensaje.value = 'Error cargando el módulo predictivo: ' + (e?.response?.data?.detail || e.message)
    mensajeTipo.value = 'error'
  } finally {
    cargando.value = false
  }
}

async function seleccionarBomba(bomba) {
  seleccionada.value = bomba
  detalle.value = null
  detalleCargando.value = true
  try {
    const r = await apiClient.get(`/ia/predict/${bomba.equipo_id}`)
    detalle.value = r.data
    await nextTick()
    renderShap(detalle.value)
    renderProbs(detalle.value)
  } catch (e) {
    mensaje.value = e?.response?.data?.detail || 'Error al predecir el equipo'
    mensajeTipo.value = 'error'
  } finally {
    detalleCargando.value = false
  }
}

async function reentrenar() {
  entrenando.value = true
  mensaje.value = 'Entrenando el pipeline PLN + RUL + SHAP (puede tardar ~1 minuto)...'
  mensajeTipo.value = 'info'
  try {
    const r = await apiClient.post('/ia/entrenar?usar_dataset_sintetico=true')
    mensaje.value = `Entrenamiento completado — F1: ${r.data?.clasificacion?.f1_macro} · RMSE: ${r.data?.regresion?.rmse_dias} días`
    mensajeTipo.value = 'ok'
    await cargarTodo()
  } catch (e) {
    mensaje.value = 'Error en el entrenamiento: ' + (e?.response?.data?.detail || e.message)
    mensajeTipo.value = 'error'
  } finally {
    entrenando.value = false
  }
}

function exportarCSV(tipo) {
  window.open(`http://127.0.0.1:8000/ia/exportar/${tipo}?formato=csv`, '_blank')
}

async function exportarJSON(tipo) {
  try {
    const r = await apiClient.get(`/ia/exportar/${tipo}?formato=json`)
    const blob = new Blob([JSON.stringify(r.data, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `cmmsbioai_${tipo}_anonimizado.json`
    a.click()
    URL.revokeObjectURL(url)
  } catch (e) {
    mensaje.value = e?.response?.data?.detail || 'Reporte no disponible todavía'
    mensajeTipo.value = 'error'
  }
}

// ---------- Gráficos ----------
function renderShap(d) {
  if (!chartShap.value || !d?.shap_top?.length) return
  if (instanciaShap) instanciaShap.destroy()
  const items = [...d.shap_top].sort((a, b) => Math.abs(b.shap) - Math.abs(a.shap))
  instanciaShap = new Chart(chartShap.value, {
    type: 'bar',
    data: {
      labels: items.map(s => shortLabel(s.etiqueta)),
      datasets: [{
        label: 'Contribución SHAP (días)',
        data: items.map(s => s.shap),
        backgroundColor: items.map(s => (s.shap < 0 ? '#ef4444' : '#16a34a')),
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const it = items[ctx.dataIndex]
              return `${it.shap < 0 ? 'Acerca la falla' : 'Extiende la vida'}: ${Math.abs(it.shap).toFixed(2)} días`
            },
          },
        },
      },
      scales: {
        x: { grid: { color: '#e5e7eb' } },
        y: { ticks: { font: { size: 11 } } },
      },
    },
  })
}

function shortLabel(etq) {
  const mapa = {
    "Antigüedad del equipo (años)": 'Antigüedad (años)',
    "Criticidad del equipo (1-3)": 'Criticidad',
    "Días desde la última intervención": 'Días desde últ. interv.',
    "N.º de OTs correctivas previas (12 meses)": 'OTs previas (12m)',
    "N.º de reportes previos de 'oclusión'": "Rep. previos 'oclusión'",
    "Deriva previa en calibración": 'Deriva previa calib.',
  }
  return mapa[etq] || etq.replace(' (PLN)', '')
}

function renderImportancia() {
  if (!chartImportancia.value || !metricas.value?.importancia_global_shap?.length) return
  if (instanciaImportancia) instanciaImportancia.destroy()
  const imp = metricas.value.importancia_global_shap
  instanciaImportancia = new Chart(chartImportancia.value, {
    type: 'bar',
    data: {
      labels: imp.map(i => shortLabel(i.etiqueta)),
      datasets: [{
        label: 'Importancia (|SHAP| medio)',
        data: imp.map(i => i.importancia),
        backgroundColor: '#2563eb',
        borderRadius: 4,
      }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { grid: { color: '#e5e7eb' } } },
    },
  })
}

function renderProbs(d) {
  if (!chartProbs.value || !d?.probabilidades) return
  if (instanciaProbs) instanciaProbs.destroy()
  const cats = Object.keys(d.probabilidades)
  const vals = cats.map(c => (d.probabilidades[c] * 100).toFixed(1))
  const colores = cats.map(c => (c === d.tipo_falla_predicho ? '#2563eb' : '#cbd5e1'))
  instanciaProbs = new Chart(chartProbs.value, {
    type: 'bar',
    data: {
      labels: cats.map(c => c.charAt(0).toUpperCase() + c.slice(1)),
      datasets: [{ label: 'Probabilidad (%)', data: vals, backgroundColor: colores, borderRadius: 4 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, max: 100, grid: { color: '#e5e7eb' } } },
    },
  })
}

onMounted(cargarTodo)
</script>

<template>
  <div class="predictivo-view">
    <!-- ================= Header ================= -->
    <header class="pred-header">
      <div>
        <h1 class="pred-titulo">🧠 Módulo Predictivo — Bombas de Infusión</h1>
        <p class="pred-subtitulo">
          Modelo híbrido interpretable (PLN + RUL + XAI/SHAP) · arquitectura offline-first · RF07
        </p>
      </div>
      <div class="pred-acciones">
        <button class="btn btn-sec" :disabled="entrenando" @click="reentrenar">
          {{ entrenando ? '⏳ Entrenando…' : '🔄 Reentrenar' }}
        </button>
        <button class="btn btn-sec" @click="exportarCSV('predicciones')">📤 CSV RUL</button>
        <button class="btn btn-sec" @click="exportarCSV('tiempos')">📤 CSV H3</button>
        <button class="btn btn-sec" @click="exportarJSON('shap')">📤 JSON SHAP</button>
      </div>
    </header>

    <div v-if="mensaje" class="pred-mensaje" :class="`pred-mensaje--${mensajeTipo}`">
      {{ mensaje }}
    </div>

    <!-- ================= Sin modelos ================= -->
    <div v-if="!hayModelos && !cargando" class="pred-vacio">
      <p>No hay modelos entrenados todavía.</p>
      <button class="btn btn-primario" :disabled="entrenando" @click="reentrenar">
        🚀 Entrenar pipeline (dataset de 220 OTs)
      </button>
    </div>

    <!-- ================= Contenido ================= -->
    <div v-else class="pred-contenido">
      <!-- Métricas del modelo -->
      <section class="pred-metricas" v-if="metricasCards.length">
        <div v-for="m in metricasCards" :key="m.titulo" class="metrica-card">
          <span class="metrica-valor" :style="{ color: m.color }">{{ m.valor }}</span>
          <span class="metrica-titulo">{{ m.titulo }}</span>
          <span class="metrica-sub">{{ m.sub }}</span>
        </div>
        <div class="metrica-card" v-if="h3 && h3.n_inferencias">
          <span class="metrica-valor" :style="{ color: h3.h3_cumple_p95 ? '#16a34a' : '#ef4444' }">
            {{ fmtMs(h3.tiempo_ms_p95) }}
          </span>
          <span class="metrica-titulo">Tiempo inferencia (p95)</span>
          <span class="metrica-sub">
            {{ h3.h3_cumple_p95 ? '✅ H3 cumplida (< 2 s)' : '❌ H3 no cumplida' }} · {{ h3.n_inferencias }} inferencias
          </span>
        </div>
      </section>

      <!-- Ablación -->
      <section class="pred-ablacion" v-if="ablacionTabla.length">
        <h2 class="pred-seccion-titulo">Estudio de Ablación — 3 niveles de preprocesamiento</h2>
        <table class="tabla-ablacion">
          <thead>
            <tr>
              <th>Nivel</th>
              <th>F1-Score macro</th>
              <th>AUC-ROC (OvR)</th>
              <th>RMSE (días)</th>
              <th>MAE (días)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="f in ablacionTabla" :key="f.nivel" :class="{ 'fila-ganadora': f.nivel === 'N3' }">
              <td>
                <strong>{{ f.nivel }}</strong>
                <span class="nivel-desc">{{ f.descripcion }}</span>
              </td>
              <td>{{ f.f1_macro_media }}</td>
              <td>{{ f.auc_roc_ovr_media ?? '—' }}</td>
              <td>{{ f.rmse_dias_media }}</td>
              <td>{{ f.mae_dias_media }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="ablacionPrueba && ablacionPrueba.conclusion" class="ablacion-prueba">
          <strong>Prueba estadística N3 vs N2:</strong>
          {{ ablacionPrueba.prueba_aplicada || 'pareada' }} ·
          p = {{ ablacionPrueba.p_valor_primario ?? ablacionPrueba.p_valor }} ·
          {{ ablacionPrueba.conclusion }}
        </p>
      </section>

      <!-- Parque + detalle -->
      <section class="pred-grid">
        <!-- Lista de bombas -->
        <div class="pred-parque">
          <div class="parque-header">
            <h2 class="pred-seccion-titulo">Parque de bombas ({{ resumen?.total ?? 0 }})</h2>
            <div class="sem-leyenda">
              <span class="sem-chip"><i class="dot" style="background:#ef4444"></i>{{ conteoSem.rojo }} críticas</span>
              <span class="sem-chip"><i class="dot" style="background:#eab308"></i>{{ conteoSem.amarillo }} atención</span>
              <span class="sem-chip"><i class="dot" style="background:#16a34a"></i>{{ conteoSem.verde }} estables</span>
            </div>
          </div>

          <div v-if="!resumenOrdenado.length" class="parque-vacio">
            {{ resumen?.mensaje || 'Sin bombas registradas.' }}
            <br /><small>Registre equipos con tipo «Bomba de Infusión» en el inventario (RF01).</small>
          </div>

          <button
            v-for="b in resumenOrdenado"
            :key="b.equipo_id"
            class="bomba-item"
            :class="{ 'bomba-item--activa': seleccionada?.equipo_id === b.equipo_id }"
            @click="seleccionarBomba(b)"
          >
            <span class="bomba-dot" :style="{ background: semaforoColor(b) }"></span>
            <span class="bomba-info">
              <strong>{{ b.nombre_corto || `Equipo #${b.equipo_id}` }}</strong>
              <small>{{ b.modelo }} · {{ b.ubicacion_actual || 'Sin ubicación' }}</small>
            </span>
            <span class="bomba-rul" v-if="b.rul_dias !== null">
              <strong>{{ Math.round(b.rul_dias) }} d</strong>
              <small>{{ semaforoEtiqueta(b) }}</small>
            </span>
            <span class="bomba-rul" v-else><small>Sin datos</small></span>
          </button>
        </div>

        <!-- Detalle SHAP -->
        <div class="pred-detalle">
          <template v-if="detalleCargando">
            <div class="detalle-vacio">⏳ Calculando predicción + SHAP…</div>
          </template>
          <template v-else-if="detalle">
            <div class="detalle-cabecera">
              <div>
                <h2 class="detalle-titulo">{{ detalle.nombre_corto || `Equipo #${detalle.equipo_id}` }}</h2>
                <small class="detalle-sub">N.º serie: {{ detalle.numero_serie }} · {{ detalle.n_ots_historial }} OT(s) en historial</small>
              </div>
              <div class="detalle-rul" :style="{ borderColor: detalle.semaforo?.color }">
                <span class="rul-numero">{{ Math.round(detalle.rul_dias) }}</span>
                <span class="rul-unidad">días<br />RUL estimado</span>
              </div>
            </div>

            <div class="detalle-explicacion" v-if="detalle.explicacion">
              <h3>💬 Explicación diagnóstica (XAI/SHAP)</h3>
              <p>{{ detalle.explicacion }}</p>
              <small class="detalle-tiempo">
                ⏱ Inferencia completa: {{ fmtMs(detalle.tiempo_ms) }}
                {{ detalle.cumple_h3 ? '· ✅ cumple H3 (< 2 s)' : '· ⚠️ excede el umbral H3' }}
              </small>
            </div>

            <div class="detalle-graficos">
              <div class="grafico-caja">
                <h3>Contribución SHAP (esta predicción)</h3>
                <canvas ref="chartShap"></canvas>
              </div>
              <div class="grafico-caja">
                <h3>Probabilidad por tipo de falla (PLN)</h3>
                <canvas ref="chartProbs"></canvas>
              </div>
            </div>
          </template>
          <template v-else>
            <div class="detalle-vacio">Seleccione una bomba de la lista para ver su predicción.</div>
          </template>
        </div>
      </section>

      <!-- Importancia global -->
      <section class="pred-importancia" v-if="metricas?.importancia_global_shap?.length">
        <h2 class="pred-seccion-titulo">Importancia global de variables (|SHAP| medio)</h2>
        <div class="grafico-caja grafico-anch">
          <canvas ref="chartImportancia"></canvas>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.predictivo-view { padding: 1.5rem 2rem; max-width: 1400px; margin: 0 auto; }

.pred-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 1rem; flex-wrap: wrap; margin-bottom: 1rem; }
.pred-titulo { font-size: 1.45rem; margin: 0; color: #1e293b; }
.pred-subtitulo { margin: 0.25rem 0 0; color: #64748b; font-size: 0.88rem; }
.pred-acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; }

.btn { border: none; border-radius: 8px; padding: 0.55rem 0.9rem; font-size: 0.85rem; cursor: pointer; transition: all .15s ease; }
.btn:disabled { opacity: 0.55; cursor: not-allowed; }
.btn-sec { background: #fff; border: 1px solid #cbd5e1; color: #334155; }
.btn-sec:hover:not(:disabled) { background: #f1f5f9; }
.btn-primario { background: #2563eb; color: #fff; padding: 0.7rem 1.2rem; font-size: 0.95rem; }
.btn-primario:hover:not(:disabled) { background: #1d4ed8; }

.pred-mensaje { padding: 0.7rem 1rem; border-radius: 8px; font-size: 0.88rem; margin-bottom: 1rem; }
.pred-mensaje--info { background: #eff6ff; color: #1d4ed8; }
.pred-mensaje--ok { background: #f0fdf4; color: #15803d; }
.pred-mensaje--error { background: #fef2f2; color: #b91c1c; }

.pred-vacio { text-align: center; padding: 3rem; background: #f8fafc; border-radius: 12px; color: #475569; }

/* Métricas */
.pred-metricas { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 0.9rem; margin-bottom: 1.5rem; }
.metrica-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.1rem; display: flex; flex-direction: column; gap: 0.15rem; }
.metrica-valor { font-size: 1.55rem; font-weight: 700; }
.metrica-titulo { font-size: 0.82rem; color: #334155; font-weight: 600; }
.metrica-sub { font-size: 0.74rem; color: #94a3b8; }

/* Ablación */
.pred-ablacion { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.1rem 1.3rem; margin-bottom: 1.5rem; }
.pred-seccion-titulo { font-size: 1.02rem; margin: 0 0 0.8rem; color: #1e293b; }
.tabla-ablacion { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.tabla-ablacion th { text-align: left; padding: 0.5rem 0.6rem; background: #f1f5f9; color: #475569; font-weight: 600; }
.tabla-ablacion td { padding: 0.55rem 0.6rem; border-top: 1px solid #e2e8f0; }
.fila-ganadora { background: #f0fdf4; }
.nivel-desc { display: block; font-size: 0.72rem; color: #94a3b8; }
.ablacion-prueba { margin: 0.8rem 0 0; font-size: 0.82rem; color: #475569; background: #f8fafc; padding: 0.6rem 0.8rem; border-radius: 8px; }

/* Parque + detalle */
.pred-grid { display: grid; grid-template-columns: 380px 1fr; gap: 1.2rem; margin-bottom: 1.5rem; }
@media (max-width: 1000px) { .pred-grid { grid-template-columns: 1fr; } }

.pred-parque { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1rem 1.1rem; }
.parque-header { display: flex; justify-content: space-between; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.sem-leyenda { display: flex; gap: 0.4rem; flex-wrap: wrap; }
.sem-chip { display: inline-flex; align-items: center; gap: 0.3rem; font-size: 0.72rem; color: #475569; }
.dot { width: 9px; height: 9px; border-radius: 50%; display: inline-block; }
.parque-vacio { padding: 1.5rem 0.5rem; color: #64748b; font-size: 0.88rem; text-align: center; }

.bomba-item { display: flex; align-items: center; gap: 0.7rem; width: 100%; text-align: left; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.65rem 0.8rem; margin-top: 0.55rem; cursor: pointer; transition: all .12s ease; }
.bomba-item:hover { border-color: #94a3b8; background: #f8fafc; }
.bomba-item--activa { border-color: #2563eb; background: #eff6ff; }
.bomba-dot { width: 14px; height: 14px; border-radius: 50%; flex-shrink: 0; box-shadow: 0 0 0 3px rgba(0,0,0,0.06); }
.bomba-info { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.bomba-info strong { font-size: 0.88rem; color: #1e293b; }
.bomba-info small { color: #94a3b8; font-size: 0.73rem; }
.bomba-rul { text-align: right; display: flex; flex-direction: column; }
.bomba-rul strong { font-size: 0.95rem; color: #1e293b; }
.bomba-rul small { color: #94a3b8; font-size: 0.72rem; }

.pred-detalle { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.1rem 1.3rem; }
.detalle-vacio { color: #94a3b8; text-align: center; padding: 3rem 1rem; }
.detalle-cabecera { display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; }
.detalle-titulo { margin: 0; font-size: 1.12rem; color: #1e293b; }
.detalle-sub { color: #94a3b8; }
.detalle-rul { display: flex; align-items: center; gap: 0.5rem; border: 2px solid; border-radius: 12px; padding: 0.5rem 0.9rem; }
.rul-numero { font-size: 2rem; font-weight: 800; color: #1e293b; }
.rul-unidad { font-size: 0.7rem; color: #64748b; line-height: 1.15; }

.detalle-explicacion { margin-top: 1rem; background: #f8fafc; border-left: 4px solid #2563eb; border-radius: 0 8px 8px 0; padding: 0.8rem 1rem; }
.detalle-explicacion h3 { margin: 0 0 0.4rem; font-size: 0.88rem; color: #1e293b; }
.detalle-explicacion p { margin: 0; font-size: 0.9rem; color: #334155; line-height: 1.5; }
.detalle-tiempo { display: block; margin-top: 0.5rem; color: #64748b; }

.detalle-graficos { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem; }
@media (max-width: 800px) { .detalle-graficos { grid-template-columns: 1fr; } }
.grafico-caja { border: 1px solid #e2e8f0; border-radius: 10px; padding: 0.8rem; }
.grafico-caja h3 { margin: 0 0 0.5rem; font-size: 0.82rem; color: #475569; }
.grafico-caja canvas { max-height: 240px; }

.pred-importancia { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.1rem 1.3rem; }
.grafico-anch canvas { max-height: 300px; }
</style>
