<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
import { Chart as ChartJS, ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'
import { Doughnut, Bar } from 'vue-chartjs'

ChartJS.register(ArcElement, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

// --- Estado general ---
const activeTab = ref('mantenimiento')
const loading = ref(false)
const error_msg = ref('')

// --- Filtros de fecha ---
const hoy = new Date()
const hace30 = new Date(hoy.getTime() - 30 * 24 * 60 * 60 * 1000)
const fechaDesde = ref(hace30.toISOString().substring(0, 10))
const fechaHasta = ref(hoy.toISOString().substring(0, 10))

// --- Datos de reportes ---
const mantenimientoData = ref([])
const otsData = ref({ resumen: {}, ordenes: [] })
const costosData = ref({})
const preventivoData = ref({ resumen: {}, detalle: [] })
const disponibilidadData = ref({})
const inventarioData = ref({})

// --- Tabs ---
const tabs = [
  { key: 'mantenimiento', label: 'Mantenimiento por Equipo' },
  { key: 'ots', label: 'OTs por Período' },
  { key: 'costos', label: 'Análisis de Costos' },
  { key: 'preventivo', label: 'Cumplimiento Preventivo' },
  { key: 'disponibilidad', label: 'Disponibilidad Equipos' },
  { key: 'inventario', label: 'Inventario Repuestos' }
]

// --- Fetch functions ---
const fetchMantenimiento = async () => {
  try {
    loading.value = true
    const params = {}
    if (fechaDesde.value) params.fecha_desde = fechaDesde.value
    if (fechaHasta.value) params.fecha_hasta = fechaHasta.value
    const res = await apiClient.get('/reportes/mantenimiento-por-equipo', { params })
    mantenimientoData.value = res.data
  } catch (error) {
    error_msg.value = 'Error al cargar reporte de mantenimiento'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchOTs = async () => {
  try {
    loading.value = true
    const params = {}
    if (fechaDesde.value) params.fecha_desde = fechaDesde.value
    if (fechaHasta.value) params.fecha_hasta = fechaHasta.value
    const res = await apiClient.get('/reportes/ots-por-periodo', { params })
    otsData.value = res.data
  } catch (error) {
    error_msg.value = 'Error al cargar reporte de OTs'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchCostos = async () => {
  try {
    loading.value = true
    const params = {}
    if (fechaDesde.value) params.fecha_desde = fechaDesde.value
    if (fechaHasta.value) params.fecha_hasta = fechaHasta.value
    const res = await apiClient.get('/reportes/costos', { params })
    costosData.value = res.data
  } catch (error) {
    error_msg.value = 'Error al cargar reporte de costos'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchPreventivo = async () => {
  try {
    loading.value = true
    const res = await apiClient.get('/reportes/preventivo-cumplimiento')
    preventivoData.value = res.data
  } catch (error) {
    error_msg.value = 'Error al cargar reporte preventivo'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchDisponibilidad = async () => {
  try {
    loading.value = true
    const res = await apiClient.get('/reportes/disponibilidad-equipos')
    disponibilidadData.value = res.data
  } catch (error) {
    error_msg.value = 'Error al cargar reporte de disponibilidad'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchInventario = async () => {
  try {
    loading.value = true
    const res = await apiClient.get('/reportes/inventario-repuestos')
    inventarioData.value = res.data
  } catch (error) {
    error_msg.value = 'Error al cargar reporte de inventario'
    console.error(error)
  } finally {
    loading.value = false
  }
}

// --- Cargar datos según tab activo ---
const loadActiveReport = () => {
  error_msg.value = ''
  switch (activeTab.value) {
    case 'mantenimiento': fetchMantenimiento(); break
    case 'ots': fetchOTs(); break
    case 'costos': fetchCostos(); break
    case 'preventivo': fetchPreventivo(); break
    case 'disponibilidad': fetchDisponibilidad(); break
    case 'inventario': fetchInventario(); break
  }
}

// --- Chart data computados ---

// Mantenimiento: eventos por equipo (barras)
const mantenimientoChartData = computed(() => {
  if (!mantenimientoData.value.length) return null
  const top = mantenimientoData.value.slice(0, 10)
  return {
    labels: top.map(d => d.equipo_nombre),
    datasets: [
      { label: 'Preventivos', data: top.map(d => d.preventivos), backgroundColor: '#27ae60' },
      { label: 'Correctivos', data: top.map(d => d.correctivos), backgroundColor: '#e74c3c' },
      { label: 'Calibración', data: top.map(d => d.calibraciones), backgroundColor: '#3498db' },
      { label: 'Otro', data: top.map(d => d.otros), backgroundColor: '#9b59b6' }
    ]
  }
})

const mantenimientoChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { position: 'top' } },
  scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } }
}

// OTs por estado (doughnut)
const otsEstadoChartData = computed(() => {
  const porEstado = otsData.value.resumen?.por_estado || {}
  const labels = Object.keys(porEstado)
  const data = Object.values(porEstado)
  const colors = {
    'Abierta': '#3b82f6', 'En Proceso': '#f59e0b', 'Bloqueada': '#8b5cf6',
    'Completada': '#22c55e', 'Cancelada': '#ef4444'
  }
  return {
    labels,
    datasets: [{
      data,
      backgroundColor: labels.map(l => colors[l] || '#94a3b8'),
      borderWidth: 2,
      borderColor: '#fff'
    }]
  }
})

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: false,
  cutout: '50%',
  plugins: {
    legend: { position: 'bottom', labels: { padding: 12, usePointStyle: true } }
  }
}

// Costos por tipo (barras)
const costosTipoChartData = computed(() => {
  const porTipo = costosData.value.costos_por_tipo || {}
  const labels = Object.keys(porTipo)
  return {
    labels: labels.map(l => l.charAt(0).toUpperCase() + l.slice(1)),
    datasets: [
      { label: 'Costo (Bs)', data: labels.map(l => porTipo[l].costo), backgroundColor: ['#27ae60', '#e74c3c', '#3498db', '#9b59b6'].slice(0, labels.length) },
      { label: 'Tiempo (h)', data: labels.map(l => porTipo[l].tiempo), backgroundColor: ['#2ecc71', '#c0392b', '#2980b9', '#8e44ad'].slice(0, labels.length) }
    ]
  }
})

const costosEquipoChartData = computed(() => {
  const porEquipo = costosData.value.costos_por_equipo || {}
  const labels = Object.keys(porEquipo).slice(0, 10)
  return {
    labels,
    datasets: [{
      label: 'Costo (Bs)',
      data: labels.map(l => porEquipo[l].costo),
      backgroundColor: '#3498db',
      borderRadius: 4
    }]
  }
})

const barOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true } }
}

// Preventivo: cumplimiento (doughnut)
const preventivoChartData = computed(() => {
  const resumen = preventivoData.value.resumen || {}
  return {
    labels: ['Al día', 'Vencidas', 'Próximas 7d', 'Próximas 30d'],
    datasets: [{
      data: [resumen.al_dia || 0, resumen.vencidas || 0, resumen.proximas_7_dias || 0, resumen.proximas_30_dias || 0],
      backgroundColor: ['#22c55e', '#ef4444', '#f59e0b', '#3b82f6'],
      borderWidth: 2,
      borderColor: '#fff'
    }]
  }
})

// Disponibilidad (doughnut)
const disponibilidadChartData = computed(() => {
  const dist = disponibilidadData.value.distribucion || {}
  const labels = Object.keys(dist)
  return {
    labels,
    datasets: [{
      data: labels.map(l => dist[l].count),
      backgroundColor: labels.map(l => dist[l].color),
      borderWidth: 2,
      borderColor: '#fff'
    }]
  }
})

// --- Helpers ---
const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  return new Date(dateStr).toLocaleDateString('es-BO', { year: 'numeric', month: 'short', day: 'numeric' })
}

const estadoPreventivoClass = (estado) => {
  const classes = {
    vencida: 'badge-danger',
    proxima_7: 'badge-warning',
    proxima_30: 'badge-info',
    al_dia: 'badge-success',
    sin_fecha: 'badge-neutral'
  }
  return classes[estado] || 'badge-neutral'
}

const estadoPreventivoLabel = (estado) => {
  const labels = {
    vencida: 'Vencida',
    proxima_7: 'Próxima (7d)',
    proxima_30: 'Próxima (30d)',
    al_dia: 'Al día',
    sin_fecha: 'Sin fecha'
  }
  return labels[estado] || estado
}

// --- Watchers ---
watch(activeTab, () => { loadActiveReport() })

onMounted(() => {
  loadActiveReport()
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Reportes y Estadísticas</h2>
        <div class="top-bar-actions">
          <label class="filter-label">Desde:</label>
          <input v-model="fechaDesde" type="date" class="filter-date" @change="loadActiveReport()">
          <label class="filter-label">Hasta:</label>
          <input v-model="fechaHasta" type="date" class="filter-date" @change="loadActiveReport()">
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ 'tab-active': activeTab === tab.key }"
          @click="activeTab = tab.key"
        >
          {{ tab.label }}
        </button>
      </div>

      <div v-if="loading" class="loading-state">Cargando reporte...</div>
      <div v-if="error_msg" class="error">{{ error_msg }}</div>

      <!-- ============ TAB: MANTENIMIENTO POR EQUIPO ============ -->
      <div v-if="!loading && activeTab === 'mantenimiento'" class="report-section">
        <div v-if="mantenimientoData.length" class="chart-row">
          <div class="chart-panel chart-panel--wide">
            <h3 class="panel-title">Eventos de Mantenimiento por Equipo (Top 10)</h3>
            <div class="chart-container">
              <Bar v-if="mantenimientoChartData" :data="mantenimientoChartData" :options="mantenimientoChartOptions" />
            </div>
          </div>
        </div>

        <div class="report-summary-cards" v-if="mantenimientoData.length">
          <div class="summary-card">
            <span class="summary-value">{{ mantenimientoData.reduce((s, d) => s + d.total_eventos, 0) }}</span>
            <span class="summary-label">Total Eventos</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ mantenimientoData.reduce((s, d) => s + d.preventivos, 0) }}</span>
            <span class="summary-label">Preventivos</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ mantenimientoData.reduce((s, d) => s + d.correctivos, 0) }}</span>
            <span class="summary-label">Correctivos</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ mantenimientoData.reduce((s, d) => s + d.tiempo_total, 0).toFixed(1) }} h</span>
            <span class="summary-label">Tiempo Total</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">Bs {{ mantenimientoData.reduce((s, d) => s + d.costo_total, 0).toFixed(2) }}</span>
            <span class="summary-label">Costo Total</span>
          </div>
        </div>

        <table v-if="mantenimientoData.length" class="report-table">
          <thead>
            <tr>
              <th>Equipo</th>
              <th>Modelo</th>
              <th>Prev.</th>
              <th>Corr.</th>
              <th>Calib.</th>
              <th>Otro</th>
              <th>Total</th>
              <th>Tiempo (h)</th>
              <th>Costo (Bs)</th>
              <th>Último Mant.</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in mantenimientoData" :key="item.equipo_id">
              <td><strong>{{ item.equipo_nombre }}</strong></td>
              <td>{{ item.equipo_modelo }}</td>
              <td><span class="num-badge num-green">{{ item.preventivos }}</span></td>
              <td><span class="num-badge num-red">{{ item.correctivos }}</span></td>
              <td><span class="num-badge num-blue">{{ item.calibraciones }}</span></td>
              <td><span class="num-badge num-purple">{{ item.otros }}</span></td>
              <td><strong>{{ item.total_eventos }}</strong></td>
              <td>{{ item.tiempo_total }}</td>
              <td>{{ item.costo_total }}</td>
              <td>{{ item.ultima_fecha ? formatDate(item.ultima_fecha) : 'N/A' }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="!mantenimientoData.length" class="empty-state">
          No hay datos de mantenimiento para el período seleccionado. Los eventos se registran automáticamente al completar una Orden de Trabajo.
        </div>
      </div>

      <!-- ============ TAB: OTs POR PERÍODO ============ -->
      <div v-if="!loading && activeTab === 'ots'" class="report-section">
        <div class="report-summary-cards" v-if="otsData.resumen && otsData.resumen.total_ots">
          <div class="summary-card">
            <span class="summary-value">{{ otsData.resumen.total_ots }}</span>
            <span class="summary-label">Total OTs</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">Bs {{ otsData.resumen.total_costo }}</span>
            <span class="summary-label">Costo Total</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ otsData.resumen.total_tiempo }} h</span>
            <span class="summary-label">Tiempo Total</span>
          </div>
        </div>

        <div class="chart-row" v-if="otsData.resumen && otsData.resumen.por_estado">
          <div class="chart-panel">
            <h3 class="panel-title">OTs por Estado</h3>
            <div class="chart-container-small">
              <Doughnut v-if="otsEstadoChartData" :data="otsEstadoChartData" :options="doughnutOptions" />
            </div>
          </div>
        </div>

        <table v-if="otsData.ordenes && otsData.ordenes.length" class="report-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Título</th>
              <th>Equipo</th>
              <th>Estado</th>
              <th>Prioridad</th>
              <th>Técnico</th>
              <th>Fecha Creación</th>
              <th>Tiempo (h)</th>
              <th>Costo (Bs)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ot in otsData.ordenes" :key="ot.id">
              <td>{{ ot.id }}</td>
              <td><strong>{{ ot.titulo }}</strong></td>
              <td>{{ ot.equipo_nombre }}</td>
              <td><span class="ot-estado-badge">{{ ot.estado_nombre }}</span></td>
              <td>{{ ot.prioridad }}</td>
              <td>{{ ot.tecnico_nombre || 'Sin asignar' }}</td>
              <td>{{ formatDate(ot.fecha_creacion) }}</td>
              <td>{{ ot.tiempo_real_invertido || '-' }}</td>
              <td>{{ ot.costo_adicional ? 'Bs ' + ot.costo_adicional : '-' }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="otsData.ordenes && !otsData.ordenes.length" class="empty-state">
          No hay órdenes de trabajo para el período seleccionado.
        </div>
      </div>

      <!-- ============ TAB: ANÁLISIS DE COSTOS ============ -->
      <div v-if="!loading && activeTab === 'costos'" class="report-section">
        <div class="report-summary-cards" v-if="costosData.total_eventos">
          <div class="summary-card">
            <span class="summary-value">Bs {{ costosData.total_costo }}</span>
            <span class="summary-label">Costo Total</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ costosData.total_tiempo }} h</span>
            <span class="summary-label">Tiempo Total</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ costosData.total_eventos }}</span>
            <span class="summary-label">Total Eventos</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">Bs {{ costosData.costo_promedio }}</span>
            <span class="summary-label">Costo Promedio/Evento</span>
          </div>
        </div>

        <div class="chart-row" v-if="costosData.costos_por_tipo">
          <div class="chart-panel">
            <h3 class="panel-title">Costos por Tipo de Mantenimiento</h3>
            <div class="chart-container-small">
              <Bar v-if="costosTipoChartData" :data="costosTipoChartData" :options="barOptions" />
            </div>
          </div>
          <div class="chart-panel">
            <h3 class="panel-title">Costos por Equipo (Top 10)</h3>
            <div class="chart-container-small">
              <Bar v-if="costosEquipoChartData" :data="costosEquipoChartData" :options="barOptions" />
            </div>
          </div>
        </div>

        <!-- Tabla de costos por equipo -->
        <h3 class="section-title" v-if="costosData.costos_por_equipo && Object.keys(costosData.costos_por_equipo).length">Detalle de Costos por Equipo</h3>
        <table v-if="costosData.costos_por_equipo && Object.keys(costosData.costos_por_equipo).length" class="report-table">
          <thead>
            <tr>
              <th>Equipo</th>
              <th>Eventos</th>
              <th>Tiempo (h)</th>
              <th>Costo (Bs)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(data, nombre) in costosData.costos_por_equipo" :key="nombre">
              <td><strong>{{ nombre }}</strong></td>
              <td>{{ data.eventos }}</td>
              <td>{{ data.tiempo }}</td>
              <td>{{ data.costo }}</td>
            </tr>
          </tbody>
        </table>

        <div v-if="!costosData.total_eventos" class="empty-state">
          No hay datos de costos para el período seleccionado.
        </div>
      </div>

      <!-- ============ TAB: CUMPLIMIENTO PREVENTIVO ============ -->
      <div v-if="!loading && activeTab === 'preventivo'" class="report-section">
        <div class="report-summary-cards" v-if="preventivoData.resumen && preventivoData.resumen.total_tareas">
          <div class="summary-card">
            <span class="summary-value">{{ preventivoData.resumen.porcentaje_cumplimiento }}%</span>
            <span class="summary-label">Cumplimiento</span>
          </div>
          <div class="summary-card">
            <span class="summary-value">{{ preventivoData.resumen.total_tareas }}</span>
            <span class="summary-label">Total Tareas</span>
          </div>
          <div class="summary-card summary-green">
            <span class="summary-value">{{ preventivoData.resumen.al_dia }}</span>
            <span class="summary-label">Al Día</span>
          </div>
          <div class="summary-card summary-red">
            <span class="summary-value">{{ preventivoData.resumen.vencidas }}</span>
            <span class="summary-label">Vencidas</span>
          </div>
          <div class="summary-card summary-yellow">
            <span class="summary-value">{{ preventivoData.resumen.proximas_7_dias }}</span>
            <span class="summary-label">Próximas 7d</span>
          </div>
        </div>

        <div class="chart-row" v-if="preventivoData.resumen && preventivoData.resumen.total_tareas">
          <div class="chart-panel">
            <h3 class="panel-title">Estado del Preventivo</h3>
            <div class="chart-container-small">
              <Doughnut v-if="preventivoChartData" :data="preventivoChartData" :options="doughnutOptions" />
            </div>
          </div>
        </div>

        <table v-if="preventivoData.detalle && preventivoData.detalle.length" class="report-table">
          <thead>
            <tr>
              <th>Tarea</th>
              <th>Equipo</th>
              <th>Responsable</th>
              <th>Frecuencia</th>
              <th>Última</th>
              <th>Próxima</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in preventivoData.detalle" :key="t.tarea_id">
              <td><strong>{{ t.titulo }}</strong></td>
              <td>{{ t.equipo_nombre }}</td>
              <td>{{ t.responsable || 'Sin asignar' }}</td>
              <td>{{ t.frecuencia_dias }} días</td>
              <td>{{ t.ultima_fecha ? formatDate(t.ultima_fecha) : 'N/A' }}</td>
              <td>{{ t.proxima_fecha ? formatDate(t.proxima_fecha) : 'N/A' }}</td>
              <td>
                <span class="prev-badge" :class="estadoPreventivoClass(t.estado)">
                  {{ estadoPreventivoLabel(t.estado) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="preventivoData.detalle && !preventivoData.detalle.length" class="empty-state">
          No hay tareas preventivas activas registradas.
        </div>
      </div>

      <!-- ============ TAB: DISPONIBILIDAD EQUIPOS ============ -->
      <div v-if="!loading && activeTab === 'disponibilidad'" class="report-section">
        <div class="report-summary-cards" v-if="disponibilidadData.total_equipos">
          <div class="summary-card">
            <span class="summary-value">{{ disponibilidadData.total_equipos }}</span>
            <span class="summary-label">Total Equipos</span>
          </div>
          <div class="summary-card summary-green">
            <span class="summary-value">{{ disponibilidadData.porcentaje_disponibilidad }}%</span>
            <span class="summary-label">Disponibilidad</span>
          </div>
        </div>

        <div class="chart-row" v-if="disponibilidadData.distribucion">
          <div class="chart-panel">
            <h3 class="panel-title">Distribución por Estado</h3>
            <div class="chart-container-small">
              <Doughnut v-if="disponibilidadChartData" :data="disponibilidadChartData" :options="doughnutOptions" />
            </div>
          </div>
        </div>

        <div v-if="disponibilidadData.distribucion" class="disponibilidad-grid">
          <div
            v-for="(data, estado) in disponibilidadData.distribucion"
            :key="estado"
            class="disp-card"
          >
            <div class="disp-card-header" :style="{ borderColor: data.color }">
              <span class="disp-count" :style="{ color: data.color }">{{ data.count }}</span>
              <span class="disp-label">{{ estado }}</span>
            </div>
            <div class="disp-equipos" v-if="data.equipos && data.equipos.length">
              <span v-for="eq in data.equipos" :key="eq.id" class="disp-equipo-chip">
                {{ eq.nombre }}
              </span>
            </div>
          </div>
        </div>

        <div v-if="!disponibilidadData.total_equipos" class="empty-state">
          No hay equipos registrados en el sistema.
        </div>
      </div>

      <!-- ============ TAB: INVENTARIO REPUESTOS ============ -->
      <div v-if="!loading && activeTab === 'inventario'" class="report-section">
        <div class="report-summary-cards" v-if="inventarioData.total_repuestos">
          <div class="summary-card">
            <span class="summary-value">{{ inventarioData.total_repuestos }}</span>
            <span class="summary-label">Total Repuestos</span>
          </div>
          <div class="summary-card summary-red">
            <span class="summary-value">{{ inventarioData.stock_bajo_count }}</span>
            <span class="summary-label">Stock Bajo</span>
          </div>
          <div class="summary-card summary-green">
            <span class="summary-value">{{ inventarioData.stock_normal_count }}</span>
            <span class="summary-label">Stock Normal</span>
          </div>
        </div>

        <div class="report-cols" v-if="inventarioData.mas_utilizados && inventarioData.mas_utilizados.length">
          <div class="report-col">
            <h3 class="section-title">Repuestos Más Utilizados</h3>
            <table class="report-table">
              <thead>
                <tr>
                  <th>Repuesto</th>
                  <th>Total Usado</th>
                  <th>Stock Actual</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in inventarioData.mas_utilizados" :key="r.nombre">
                  <td><strong>{{ r.nombre }}</strong></td>
                  <td>{{ r.total_usado }}</td>
                  <td :class="{ 'stock-bajo': r.stock_actual <= 5 }">{{ r.stock_actual }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="report-col">
            <h3 class="section-title">Repuestos con Stock Bajo</h3>
            <table v-if="inventarioData.stock_bajo && inventarioData.stock_bajo.length" class="report-table">
              <thead>
                <tr>
                  <th>Repuesto</th>
                  <th>Disponible</th>
                  <th>Mínimo</th>
                  <th>Ubicación</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in inventarioData.stock_bajo" :key="r.id">
                  <td><strong>{{ r.nombre }}</strong></td>
                  <td class="stock-bajo">{{ r.cantidad_disponible }}</td>
                  <td>{{ r.nivel_minimo }}</td>
                  <td>{{ r.ubicacion || 'N/A' }}</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="empty-state-small">No hay repuestos con stock bajo.</div>
          </div>
        </div>

        <div v-if="!inventarioData.total_repuestos" class="empty-state">
          No hay repuestos registrados en el inventario.
        </div>
      </div>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

.top-bar {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  align-items: center;
  gap: 0.75rem 1rem;
  margin-bottom: 1rem;
}
.top-bar h2 { margin: 0; }
.top-bar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
}
.filter-label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #475569;
}
.filter-date {
  padding: 0.4rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.88rem;
}
.filter-date:focus {
  outline: none;
  border-color: #3498db;
}

/* === Tabs === */
.tabs-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin-bottom: 1.25rem;
  border-bottom: 2px solid #e2e8f0;
  padding-bottom: 0;
}
.tab-btn {
  padding: 0.55rem 1rem;
  border: none;
  background: transparent;
  color: #64748b;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  border-bottom: 3px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}
.tab-btn:hover { color: #1e293b; background: #f1f5f9; border-radius: 6px 6px 0 0; }
.tab-active { color: #1e293b; border-bottom-color: #3498db; background: #f0f7ff; border-radius: 6px 6px 0 0; }

/* === Summary Cards === */
.report-summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 0.75rem;
  margin-bottom: 1.25rem;
}
.summary-card {
  background: white;
  border-radius: 10px;
  padding: 1rem;
  text-align: center;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
}
.summary-value {
  display: block;
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  margin-bottom: 0.15rem;
}
.summary-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.summary-green .summary-value { color: #16a34a; }
.summary-red .summary-value { color: #dc2626; }
.summary-yellow .summary-value { color: #ca8a04; }

/* === Charts === */
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-bottom: 1.25rem;
}
.chart-row:has(.chart-panel--wide) {
  grid-template-columns: 1fr;
}
.chart-panel {
  background: white;
  border-radius: 10px;
  padding: 1.15rem;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
}
.chart-container { height: 320px; position: relative; }
.chart-container-small { height: 260px; position: relative; }
.panel-title {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  font-weight: 700;
  color: #2c3e50;
}

/* === Tables === */
.report-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  box-shadow: 0 1px 3px rgba(0,0,0,0.07);
  border-radius: 8px;
  overflow: hidden;
  font-size: 0.88rem;
}
.report-table th {
  background: #f1f5f9;
  font-weight: 700;
  color: #475569;
  padding: 0.65rem 0.75rem;
  text-align: left;
  border-bottom: 2px solid #e2e8f0;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.report-table td {
  padding: 0.55rem 0.75rem;
  border-bottom: 1px solid #f1f5f9;
  color: #334155;
}
.report-table tbody tr:hover { background: #f8fafc; }

.num-badge {
  display: inline-block;
  min-width: 22px;
  text-align: center;
  padding: 1px 6px;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 700;
}
.num-green { background: #dcfce7; color: #166534; }
.num-red { background: #fee2e2; color: #991b1b; }
.num-blue { background: #dbeafe; color: #1e3a8a; }
.num-purple { background: #f3e8ff; color: #581c87; }

.ot-estado-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 700;
  background: #e2e8f0;
  color: #334155;
}

.prev-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 700;
  color: white;
}
.badge-success { background: #22c55e; }
.badge-danger { background: #ef4444; }
.badge-warning { background: #f59e0b; }
.badge-info { background: #3b82f6; }
.badge-neutral { background: #94a3b8; }

/* === Disponibilidad grid === */
.disponibilidad-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 0.75rem;
  margin-top: 1rem;
}
.disp-card {
  background: white;
  border-radius: 8px;
  padding: 1rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  border: 1px solid #e2e8f0;
}
.disp-card-header {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-bottom: 0.6rem;
  padding-bottom: 0.5rem;
  border-bottom: 3px solid;
}
.disp-count { font-size: 1.4rem; font-weight: 700; }
.disp-label { font-size: 0.9rem; font-weight: 600; color: #475569; }
.disp-equipos {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  max-height: 120px;
  overflow-y: auto;
}
.disp-equipo-chip {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 0.75rem;
  background: #f1f5f9;
  color: #334155;
  font-weight: 500;
}

/* === Report columns === */
.report-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 900px) {
  .report-cols { grid-template-columns: 1fr; }
  .chart-row { grid-template-columns: 1fr; }
}

.section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #2c3e50;
  margin: 1.25rem 0 0.5rem 0;
}

.stock-bajo {
  color: #dc2626;
  font-weight: 700;
}

/* === States === */
.loading-state { text-align: center; padding: 2rem; color: #64748b; }
.empty-state { text-align: center; padding: 2.5rem 1rem; color: #64748b; font-size: 0.95rem; }
.empty-state-small { text-align: center; padding: 1rem; color: #94a3b8; font-size: 0.88rem; }
.error { color: #e74c3c; font-weight: bold; margin-bottom: 1rem; }
</style>
