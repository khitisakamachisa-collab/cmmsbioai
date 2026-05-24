<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'
import { Doughnut, Bar } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const router = useRouter()

// --- Variables ---
const equipos = ref([])
const ordenes = ref([])
const estadosOT = ref([])
const estados = ref([])
const repuestos = ref([])
const tareasPreventivas = ref([])
const loading = ref(true)

// --- Chart refs ---
const estadoChartReady = ref(false)
const prioridadChartReady = ref(false)

// --- Funciones de Datos ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resEquipos, resOrdenes, resEstadosOT, resEstados, resRepuestos, resPreventivo] = await Promise.all([
      apiClient.get('/equipos/'),
      apiClient.get('/ordenes/'),
      apiClient.get('/ordenes/estados/'),
      apiClient.get('/equipos/estados'),
      apiClient.get('/repuestos/'),
      apiClient.get('/preventivo/')
    ])
    equipos.value = resEquipos.data
    ordenes.value = resOrdenes.data
    estadosOT.value = resEstadosOT.data
    estados.value = resEstados.data
    repuestos.value = resRepuestos.data
    tareasPreventivas.value = resPreventivo.data
  } catch (error) {
    console.error('Error cargando datos del dashboard', error)
  } finally {
    loading.value = false
    // Renderizar gráficos después de que el DOM se actualice
    await nextTick()
    estadoChartReady.value = true
    prioridadChartReady.value = true
  }
}

// --- Computados para Tarjetas ---
const totalEquipos = computed(() => equipos.value.length)

const ordenesPendientes = computed(() => {
  const cerrados = new Set(['completada', 'cerrada'])
  return ordenes.value.filter((ot) => {
    const est = estadosOT.value.find((e) => e.id === ot.estado_id)
    if (!est) return true
    const nombre = (est.nombre_estado || '').trim().toLowerCase()
    return !cerrados.has(nombre)
  }).length
})

const equiposMantenimiento = computed(() =>
  equipos.value.filter((eq) => Number(eq.estado_id) === 2).length
)

const stockBajo = computed(() =>
  repuestos.value.filter(r => {
    const min = r.nivel_stock_minimo
    if (min != null && min !== '') return Number(r.cantidad_disponible) <= Number(min)
    return Number(r.cantidad_disponible) <= 5
  }).length
)

const preventivoVencido = computed(() => {
  const today = new Date().setHours(0, 0, 0, 0)
  return tareasPreventivas.value.filter(t => {
    if (!t.proxima_fecha) return false
    return new Date(t.proxima_fecha).setHours(0, 0, 0, 0) < today
  }).length
})

// --- Datos para gráfico Doughnut: Equipos por Estado ---
const estadoDistribucion = computed(() => {
  const dist = {}
  estados.value.forEach(est => {
    dist[est.id] = { nombre: est.nombre_estado, color: est.color || '#95a5a6', count: 0 }
  })
  equipos.value.forEach(eq => {
    if (dist[eq.estado_id]) {
      dist[eq.estado_id].count++
    }
  })
  return Object.values(dist).filter(d => d.count > 0)
})

const estadoChartData = computed(() => ({
  labels: estadoDistribucion.value.map(d => d.nombre),
  datasets: [{
    data: estadoDistribucion.value.map(d => d.count),
    backgroundColor: estadoDistribucion.value.map(d => d.color),
    borderColor: '#ffffff',
    borderWidth: 3,
    hoverBorderWidth: 4,
    hoverOffset: 8
  }]
}))

const estadoChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '55%',
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 16,
        usePointStyle: true,
        pointStyleWidth: 12,
        font: { size: 12, family: "'Segoe UI', sans-serif" }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(30, 41, 59, 0.92)',
      titleFont: { size: 13 },
      bodyFont: { size: 12 },
      padding: 10,
      cornerRadius: 6,
      callbacks: {
        label: function (context) {
          const total = context.dataset.data.reduce((a, b) => a + b, 0)
          const pct = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0
          return ` ${context.label}: ${context.parsed} (${pct}%)`
        }
      }
    }
  }
}

// --- Datos para gráfico Bar: Órdenes por Prioridad ---
const ordenesPorPrioridad = computed(() => {
  const prio = { Urgente: 0, Alta: 0, Media: 0, Baja: 0 }
  ordenes.value.forEach(ot => {
    const p = ot.prioridad || 'Media'
    if (prio[p] !== undefined) prio[p]++
  })
  return prio
})

const prioridadChartData = computed(() => ({
  labels: ['Urgente', 'Alta', 'Media', 'Baja'],
  datasets: [{
    label: 'Ordenes de Trabajo',
    data: [
      ordenesPorPrioridad.value.Urgente,
      ordenesPorPrioridad.value.Alta,
      ordenesPorPrioridad.value.Media,
      ordenesPorPrioridad.value.Baja
    ],
    backgroundColor: ['#ef4444', '#f97316', '#eab308', '#22c55e'],
    borderColor: ['#dc2626', '#ea580c', '#ca8a04', '#16a34a'],
    borderWidth: 1,
    borderRadius: 6,
    barThickness: 42
  }]
}))

const prioridadChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  indexAxis: 'x',
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: 'rgba(30, 41, 59, 0.92)',
      titleFont: { size: 13 },
      bodyFont: { size: 12 },
      padding: 10,
      cornerRadius: 6
    }
  },
  scales: {
    y: {
      beginAtZero: true,
      ticks: {
        stepSize: 1,
        font: { size: 11 }
      },
      grid: { color: 'rgba(0,0,0,0.06)' }
    },
    x: {
      ticks: { font: { size: 12, weight: '600' } },
      grid: { display: false }
    }
  }
}

// --- Órdenes por Estado (segundo gráfico doughnut) ---
const ordenesPorEstado = computed(() => {
  const dist = {}
  estadosOT.value.forEach(est => {
    dist[est.id] = { nombre: est.nombre_estado, count: 0 }
  })
  ordenes.value.forEach(ot => {
    if (dist[ot.estado_id]) {
      dist[ot.estado_id].count++
    }
  })
  return Object.values(dist).filter(d => d.count > 0)
})

const otEstadoColors = {
  'abierta': '#3b82f6',
  'en proceso': '#f59e0b',
  'completada': '#22c55e',
  'cerrada': '#94a3b8',
  'cancelada': '#ef4444',
  'pendiente': '#8b5cf6'
}

const otEstadoChartData = computed(() => ({
  labels: ordenesPorEstado.value.map(d => d.nombre),
  datasets: [{
    data: ordenesPorEstado.value.map(d => d.count),
    backgroundColor: ordenesPorEstado.value.map(d => {
      const key = (d.nombre || '').trim().toLowerCase()
      return otEstadoColors[key] || '#94a3b8'
    }),
    borderColor: '#ffffff',
    borderWidth: 3,
    hoverBorderWidth: 4,
    hoverOffset: 8
  }]
}))

const otEstadoChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '55%',
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        padding: 16,
        usePointStyle: true,
        pointStyleWidth: 12,
        font: { size: 12, family: "'Segoe UI', sans-serif" }
      }
    },
    tooltip: {
      backgroundColor: 'rgba(30, 41, 59, 0.92)',
      titleFont: { size: 13 },
      bodyFont: { size: 12 },
      padding: 10,
      cornerRadius: 6,
      callbacks: {
        label: function (context) {
          const total = context.dataset.data.reduce((a, b) => a + b, 0)
          const pct = total > 0 ? ((context.parsed / total) * 100).toFixed(1) : 0
          return ` ${context.label}: ${context.parsed} (${pct}%)`
        }
      }
    }
  }
}

// --- Sugerencias IA (basadas en reglas) ---
const sugerencias = computed(() => {
  const lista = []

  // Sugerencia: equipos sin preventivo
  const equiposConPreventivo = new Set(tareasPreventivas.value.map(t => t.equipo_id))
  const sinPreventivo = equipos.value.filter(eq => !equiposConPreventivo.has(eq.id))
  if (sinPreventivo.length > 0) {
    lista.push({
      tipo: 'warning',
      titulo: 'Equipos sin mantenimiento preventivo',
      descripcion: `${sinPreventivo.length} equipo(s) no tienen tareas preventivas asignadas. Esto incrementa el riesgo de fallas inesperadas.`,
      accion: 'Ir a Preventivo',
      ruta: '/preventivo'
    })
  }

  // Sugerencia: stock bajo
  if (stockBajo.value > 0) {
    lista.push({
      tipo: 'danger',
      titulo: 'Repuestos con stock bajo',
      descripcion: `${stockBajo.value} repuesto(s) están por debajo del nivel mínimo. Reponer a tiempo evita retrasos en reparaciones.`,
      accion: 'Ver Inventario',
      ruta: '/inventario'
    })
  }

  // Sugerencia: preventivo vencido
  if (preventivoVencido.value > 0) {
    lista.push({
      tipo: 'danger',
      titulo: 'Tareas preventivas vencidas',
      descripcion: `${preventivoVencido.value} tarea(s) preventiva(s) tienen fecha vencida. Se recomienda atenderlas de inmediato.`,
      accion: 'Ver Preventivo',
      ruta: '/preventivo'
    })
  }

  // Sugerencia: OTs pendientes
  if (ordenesPendientes.value > 3) {
    lista.push({
      tipo: 'info',
      titulo: 'Ordenes de trabajo pendientes',
      descripcion: `Hay ${ordenesPendientes.value} ordenes pendientes. Considere priorizar las urgentes para mantener el equipo operativo.`,
      accion: 'Ver Ordenes',
      ruta: '/ordenes'
    })
  }

  // Sugerencia: calibracion proxima
  const hoy = new Date()
  const en30Dias = new Date(hoy.getTime() + 30 * 24 * 60 * 60 * 1000)
  const calibracionProxima = equipos.value.filter(eq => {
    if (!eq.calibracion_proxima) return false
    const fecha = new Date(eq.calibracion_proxima)
    return fecha >= hoy && fecha <= en30Dias
  })
  if (calibracionProxima.length > 0) {
    lista.push({
      tipo: 'info',
      titulo: 'Calibraciones proximas',
      descripcion: `${calibracionProxima.length} equipo(s) requieren calibracion en los proximos 30 dias.`,
      accion: 'Ver Equipos',
      ruta: '/equipos'
    })
  }

  if (lista.length === 0) {
    lista.push({
      tipo: 'success',
      titulo: 'Todo en orden',
      descripcion: 'No hay alertas activas en este momento. Todos los equipos estan bajo control.',
      accion: null,
      ruta: null
    })
  }

  return lista
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="home-header">
        <h2>Panel de Control</h2>
        <p class="home-subtitle">Resumen general del sistema CMMS-BioAI</p>
      </div>

      <div v-if="loading" class="loading-state">Cargando datos...</div>

      <template v-if="!loading">
        <!-- Tarjetas de metricas -->
        <section class="stats-grid" aria-label="Metricas principales">
          <article class="stat-card stat-card--neutral">
            <div class="stat-card-header">
              <span class="stat-card-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M11 2a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v12h.5a.5.5 0 0 1 0 1H.5a.5.5 0 0 1 0-1H1v-3a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v3h1V7h1v8h1V2z"/>
                </svg>
              </span>
              <span class="stat-card-label">Total Equipos</span>
            </div>
            <p class="stat-card-value">{{ totalEquipos }}</p>
          </article>

          <article class="stat-card stat-card--blue">
            <div class="stat-card-header">
              <span class="stat-card-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M14 1a1 1 0 0 1 1 1v8a1 1 0 0 1-1 1H4.414A2 2 0 0 0 3 11.586l-2 2V2a1 1 0 0 1 1-1h12zM2 0a2 2 0 0 0-2 2v12.793a.5.5 0 0 0 .854.353l2.853-2.853A1 1 0 0 1 4.414 12H14a2 2 0 0 0 2-2V2a2 2 0 0 0-2-2H2z"/>
                  <path d="M5 6a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm4 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0zm4 0a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/>
                </svg>
              </span>
              <span class="stat-card-label">OT Pendientes</span>
            </div>
            <p class="stat-card-value">{{ ordenesPendientes }}</p>
          </article>

          <article class="stat-card stat-card--orange">
            <div class="stat-card-header">
              <span class="stat-card-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 4.754a3.246 3.246 0 1 0 0 6.492 3.246 3.246 0 0 0 0-6.492zM5.754 8a2.246 2.246 0 1 1 4.492 0 2.246 2.246 0 0 1-4.492 0z"/>
                  <path d="M9.796 1.343c-.527-1.79-3.065-1.79-3.592 0l-.094.319a.873.873 0 0 1-1.255.52l-.292-.16c-1.64-.892-3.433.902-2.54 2.541l.159.292a.873.873 0 0 1-.52 1.255l-.319.094c-1.79.527-1.79 3.065 0 3.592l.319.094a.873.873 0 0 1 .52 1.255l-.16.292c-.892 1.64.901 3.434 2.541 2.54l.292-.159a.873.873 0 0 1 1.255.52l.094.319c.527 1.79 3.065 1.79 3.592 0l.094-.319a.873.873 0 0 1 1.255-.52l.292.16c1.64.893 3.434-.902 2.54-2.541l-.159-.292a.873.873 0 0 1 .52-1.255l.319-.094c1.79-.527 1.79-3.065 0-3.592l-.319-.094a.873.873 0 0 1-.52-1.255l.16-.292c.893-1.64-.902-3.433-2.541-2.54l-.292.159a.873.873 0 0 1-1.255-.52l-.094-.319z"/>
                </svg>
              </span>
              <span class="stat-card-label">En Mantenimiento</span>
            </div>
            <p class="stat-card-value">{{ equiposMantenimiento }}</p>
          </article>

          <article class="stat-card stat-card--red">
            <div class="stat-card-header">
              <span class="stat-card-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/>
                  <path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/>
                </svg>
              </span>
              <span class="stat-card-label">Stock Bajo</span>
            </div>
            <p class="stat-card-value">{{ stockBajo }}</p>
          </article>

          <article class="stat-card stat-card--purple">
            <div class="stat-card-header">
              <span class="stat-card-icon">
                <svg xmlns="http://www.w3.org/2000/svg" width="22" height="22" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
                  <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
                </svg>
              </span>
              <span class="stat-card-label">Preventivo Vencido</span>
            </div>
            <p class="stat-card-value">{{ preventivoVencido }}</p>
          </article>
        </section>

        <!-- Graficos: 3 columnas -->
        <div class="charts-row">
          <section class="chart-panel">
            <h3 class="panel-title">Equipos por Estado</h3>
            <div class="chart-container">
              <Doughnut v-if="estadoChartReady && estadoDistribucion.length > 0" :data="estadoChartData" :options="estadoChartOptions" />
              <div v-else class="chart-empty">No hay equipos registrados.</div>
            </div>
          </section>

          <section class="chart-panel">
            <h3 class="panel-title">Ordenes por Prioridad</h3>
            <div class="chart-container">
              <Bar v-if="prioridadChartReady" :data="prioridadChartData" :options="prioridadChartOptions" />
            </div>
          </section>

          <section class="chart-panel">
            <h3 class="panel-title">Ordenes por Estado</h3>
            <div class="chart-container">
              <Doughnut v-if="estadoChartReady && ordenesPorEstado.length > 0" :data="otEstadoChartData" :options="otEstadoChartOptions" />
              <div v-else class="chart-empty">No hay ordenes registradas.</div>
            </div>
          </section>
        </div>

        <!-- Seccion de Sugerencias -->
        <section class="home-panel sugerencias-panel">
          <h3 class="panel-title">
            <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: text-bottom; margin-right: 6px;">
              <path d="M8 1a2 2 0 0 1 2 2v4H6V3a2 2 0 0 1 2-2zm3 6V3a3 3 0 0 0-6 0v4a2 2 0 0 0-2 2v5a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/>
            </svg>
            Sugerencias del Sistema
          </h3>
          <div class="sugerencias-grid">
            <div
              v-for="(sug, idx) in sugerencias"
              :key="idx"
              class="sugerencia-card"
              :class="'sugerencia--' + sug.tipo"
            >
              <div class="sugerencia-header">
                <span class="sugerencia-icon">
                  <svg v-if="sug.tipo === 'danger'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="M7.002 11a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 4.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 4.995z"/></svg>
                  <svg v-else-if="sug.tipo === 'warning'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M7.938 2.016A.13.13 0 0 1 8.002 2a.13.13 0 0 1 .063.016.146.146 0 0 1 .054.057l6.857 11.667c.036.06.035.124.002.183a.163.163 0 0 1-.054.06.116.116 0 0 1-.066.017H1.146a.115.115 0 0 1-.066-.017.163.163 0 0 1-.054-.06.176.176 0 0 1 .002-.183L7.884 2.073a.147.147 0 0 1 .054-.057zm1.044-.45a1.13 1.13 0 0 0-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566z"/><path d="M7.002 12a1 1 0 1 1 2 0 1 1 0 0 1-2 0zM7.1 5.995a.905.905 0 1 1 1.8 0l-.35 3.507a.552.552 0 0 1-1.1 0L7.1 5.995z"/></svg>
                  <svg v-else-if="sug.tipo === 'info'" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M8 15A7 7 0 1 1 8 1a7 7 0 0 1 0 14zm0 1A8 8 0 1 0 8 0a8 8 0 0 0 0 16z"/><path d="m8.93 6.588-2.29.287-.082.38.45.083c.294.07.352.176.288.469l-.738 3.468c-.194.897.105 1.319.808 1.319.545 0 1.178-.252 1.465-.598l.088-.416c-.2.176-.492.246-.686.246-.275 0-.375-.193-.304-.533L8.93 6.588zM9 4.5a1 1 0 1 1-2 0 1 1 0 0 1 2 0z"/></svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.07.03L7.5 8.844 5.38 6.22a.75.75 0 0 0-1.17.937l2.73 3.39a.75.75 0 0 0 1.12.025l4-4.5a.75.75 0 0 0-.03-1.07z"/></svg>
                </span>
                <strong>{{ sug.titulo }}</strong>
              </div>
              <p class="sugerencia-desc">{{ sug.descripcion }}</p>
              <router-link v-if="sug.ruta" :to="sug.ruta" class="sugerencia-accion">
                {{ sug.accion }} &rarr;
              </router-link>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

.home-header {
  margin-bottom: 1.5rem;
}
.home-header h2 {
  margin: 0 0 0.25rem 0;
  color: #1e293b;
  font-size: 1.5rem;
}
.home-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

/* === Tarjetas de metricas === */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.85rem;
  margin-bottom: 1.5rem;
}
@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 700px) {
  .stats-grid { grid-template-columns: 1fr; }
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 0.65rem 0.95rem;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.06);
  transition: box-shadow 0.2s ease, transform 0.2s ease;
}
.stat-card:hover {
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.1);
  transform: translateY(-1px);
}
.stat-card--neutral { background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%); }
.stat-card--blue { background: linear-gradient(145deg, #eef6ff 0%, #e3f0fc 100%); border-color: rgba(52, 152, 219, 0.2); }
.stat-card--orange { background: linear-gradient(145deg, #fff8f0 0%, #ffedd5 100%); border-color: rgba(230, 126, 34, 0.25); }
.stat-card--red { background: linear-gradient(145deg, #fef2f2 0%, #fee2e2 100%); border-color: rgba(231, 76, 60, 0.25); }
.stat-card--purple { background: linear-gradient(145deg, #f5f3ff 0%, #ede9fe 100%); border-color: rgba(139, 92, 246, 0.25); }

.stat-card-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}
.stat-card-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(44, 62, 80, 0.08);
  color: #2c3e50;
  flex-shrink: 0;
}
.stat-card-icon svg { width: 17px; height: 17px; }
.stat-card--blue .stat-card-icon { background: rgba(52, 152, 219, 0.15); color: #2874a6; }
.stat-card--orange .stat-card-icon { background: rgba(230, 126, 34, 0.18); color: #c26d1a; }
.stat-card--red .stat-card-icon { background: rgba(231, 76, 60, 0.15); color: #c0392b; }
.stat-card--purple .stat-card-icon { background: rgba(139, 92, 246, 0.15); color: #7c3aed; }

.stat-card-label {
  font-size: 0.7rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  line-height: 1.25;
}
.stat-card-value {
  margin: 0;
  font-size: 1.6rem;
  font-weight: 700;
  line-height: 1.15;
  color: #1e293b;
  letter-spacing: -0.02em;
}
.stat-card--blue .stat-card-value { color: #1a5276; }
.stat-card--orange .stat-card-value { color: #9a3412; }
.stat-card--red .stat-card-value { color: #991b1b; }
.stat-card--purple .stat-card-value { color: #6d28d9; }

/* === Fila de graficos === */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}
@media (max-width: 1100px) {
  .charts-row { grid-template-columns: 1fr 1fr; }
}
@media (max-width: 700px) {
  .charts-row { grid-template-columns: 1fr; }
}

.chart-panel {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.chart-container {
  position: relative;
  height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-empty {
  text-align: center;
  color: #94a3b8;
  font-size: 0.9rem;
}

.panel-title {
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #2c3e50;
}

/* === Panel sugerencias === */
.sugerencias-panel {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.06);
}

.sugerencias-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

.sugerencia-card {
  padding: 0.85rem;
  border-radius: 8px;
  border-left: 4px solid;
}
.sugerencia--danger { background: #fef2f2; border-color: #ef4444; }
.sugerencia--warning { background: #fffbeb; border-color: #f59e0b; }
.sugerencia--info { background: #eff6ff; border-color: #3b82f6; }
.sugerencia--success { background: #f0fdf4; border-color: #22c55e; }

.sugerencia-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.3rem;
}
.sugerencia--danger .sugerencia-icon { color: #ef4444; }
.sugerencia--warning .sugerencia-icon { color: #f59e0b; }
.sugerencia--info .sugerencia-icon { color: #3b82f6; }
.sugerencia--success .sugerencia-icon { color: #22c55e; }

.sugerencia-desc {
  margin: 0;
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.4;
}
.sugerencia-accion {
  display: inline-block;
  margin-top: 0.5rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #3498db;
  text-decoration: none;
}
.sugerencia-accion:hover {
  text-decoration: underline;
}
</style>
