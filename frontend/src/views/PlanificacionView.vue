<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'

const router = useRouter()

// --- Datos ---
const ordenes = ref([])
const tareasMP = ref([])
const equipos = ref([])
const usuarios = ref([])
const estadosOT = ref([])
const loading = ref(true)

// --- Filtros ---
const filterEquipo = ref('')
const filterUbicacion = ref('')
const filterResponsable = ref('')
const filterTipo = ref('')  // '' = todo, 'ot' = solo OT, 'mp' = solo MP

// --- Calendario ---
const hoy = new Date()
const calAnio = ref(hoy.getFullYear())
const calMes = ref(hoy.getMonth())

const DIAS_SEMANA = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

// --- Modal detalle ---
const showDetalleModal = ref(false)
const detalleEvento = ref(null)

// --- Fetch ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resOrdenes, resMP, resEquipos, resUsers, resEstados] = await Promise.all([
      apiClient.get('/ordenes/'),
      apiClient.get('/preventivo/'),
      apiClient.get('/equipos/'),
      apiClient.get('/users/'),
      apiClient.get('/ordenes/estados/')
    ])
    ordenes.value = resOrdenes.data
    tareasMP.value = resMP.data
    equipos.value = resEquipos.data
    usuarios.value = resUsers.data
    estadosOT.value = resEstados.data
  } catch (error) {
    console.error('Error cargando datos', error)
  } finally {
    loading.value = false
  }
}

// --- Helpers ---
const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.nombre_corto || eq.modelo) : `ID:${id}`
}

const getEquipoUbicacion = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.ubicacion_actual || '') : ''
}

const getUsuarioNombre = (id) => {
  if (!id) return ''
  const u = usuarios.value.find(u => u.id === id)
  return u ? (u.full_name || u.username) : ''
}

const getEstadoOTNombre = (id) => {
  const e = estadosOT.value.find(e => e.id === id)
  return e ? e.nombre_estado : ''
}

const getEstadoOTColor = (id) => {
  const e = estadosOT.value.find(e => e.id === id)
  return e ? e.color : '#95a5a6'
}

// --- Unificar eventos (OTs + MPs) ---
const eventosUnificados = computed(() => {
  let eventos = []

  // Procesar OTs
  if (filterTipo.value !== 'mp') {
    ordenes.value.forEach(ot => {
      // Usar fecha_creacion como fecha del evento (o fecha_vencimiento si existe)
      const fecha = ot.fecha_vencimiento || ot.fecha_creacion
      if (!fecha) return

      eventos.push({
        id: `ot-${ot.id}`,
        tipo: 'ot',
        tipoLabel: 'OT',
        fecha: fecha.substring(0, 10),
        titulo: ot.titulo,
        equipo_id: ot.equipo_id,
        equipo_nombre: getEquipoNombre(ot.equipo_id),
        ubicacion: getEquipoUbicacion(ot.equipo_id),
        responsable_id: ot.tecnico_asignado_id,
        responsable_nombre: getUsuarioNombre(ot.tecnico_asignado_id),
        estado: getEstadoOTNombre(ot.estado_id),
        estado_color: getEstadoOTColor(ot.estado_id),
        estado_id: ot.estado_id,
        descripcion: ot.descripcion_falla,
        ot_id: ot.id,
        prioridad: ot.prioridad
      })
    })
  }

  // Procesar MPs
  if (filterTipo.value !== 'ot') {
    tareasMP.value.forEach(tarea => {
      if (!tarea.proxima_fecha) return

      // Verificar si tiene OT activa
      const tieneOt = ordenes.value.some(ot =>
        ot.orden_preventiva_id === tarea.id &&
        (ot.estado_id === 1 || ot.estado_id === 2 || ot.estado_id === 3)
      )

      let color = '#eab308'  // amarillo por defecto (recordatorio)
      let estadoLabel = 'Recordatorio'
      if (tieneOt) {
        color = '#16a34a'  // verde (programada)
        estadoLabel = 'Programada'
      } else {
        const today = new Date().setHours(0, 0, 0, 0)
        const dueDate = new Date(tarea.proxima_fecha).setHours(0, 0, 0, 0)
        if (dueDate < today) {
          color = '#ef4444'  // rojo (vencida)
          estadoLabel = 'Vencida'
        } else if (dueDate === today) {
          color = '#f97316'  // naranja (hoy)
          estadoLabel = 'Hoy'
        }
      }

      eventos.push({
        id: `mp-${tarea.id}`,
        tipo: 'mp',
        tipoLabel: 'MP',
        fecha: tarea.proxima_fecha.substring(0, 10),
        titulo: tarea.titulo,
        equipo_id: tarea.equipo_id,
        equipo_nombre: getEquipoNombre(tarea.equipo_id),
        ubicacion: getEquipoUbicacion(tarea.equipo_id),
        responsable_id: tarea.responsable_id,
        responsable_nombre: getUsuarioNombre(tarea.responsable_id),
        estado: estadoLabel,
        estado_color: color,
        frecuencia_dias: tarea.frecuencia_dias,
        descripcion: tarea.descripcion,
        mp_id: tarea.id,
        tiene_ot: tieneOt
      })
    })
  }

  return eventos
})

// --- Filtrar eventos ---
const eventosFiltrados = computed(() => {
  let result = eventosUnificados.value

  if (filterEquipo.value) {
    result = result.filter(e => String(e.equipo_id) === String(filterEquipo.value))
  }
  if (filterUbicacion.value) {
    result = result.filter(e => e.ubicacion === filterUbicacion.value)
  }
  if (filterResponsable.value) {
    result = result.filter(e => String(e.responsable_id) === String(filterResponsable.value))
  }

  return result
})

// --- Ubicaciones únicas para filtro ---
const ubicacionesUnicas = computed(() => {
  const vals = new Set()
  equipos.value.forEach(eq => { if (eq.ubicacion_actual) vals.add(eq.ubicacion_actual) })
  return Array.from(vals).sort()
})

// --- Lógica del calendario ---
const diasDelMes = computed(() => {
  const year = calAnio.value
  const month = calMes.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  // Día de la semana del primer día (0=domingo, ajustar a 0=lunes)
  let firstDayOfWeek = firstDay.getDay() - 1
  if (firstDayOfWeek < 0) firstDayOfWeek = 6  // domingo → 6

  const totalDays = lastDay.getDate()
  const celdas = []

  // Celdas vacías antes del primer día
  for (let i = 0; i < firstDayOfWeek; i++) {
    celdas.push({ dia: null, eventos: [] })
  }

  // Días del mes
  for (let d = 1; d <= totalDays; d++) {
    const fechaStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const eventosDelDia = eventosFiltrados.value.filter(e => e.fecha === fechaStr)
    const esHoy = (d === hoy.getDate() && month === hoy.getMonth() && year === hoy.getFullYear())
    celdas.push({ dia: d, fecha: fechaStr, eventos: eventosDelDia, esHoy })
  }

  // Completar la última semana con celdas vacías
  while (celdas.length % 7 !== 0) {
    celdas.push({ dia: null, eventos: [] })
  }

  return celdas
})

// --- Navegación del calendario ---
const mesAnterior = () => {
  if (calMes.value === 0) {
    calMes.value = 11
    calAnio.value--
  } else {
    calMes.value--
  }
}

const mesSiguiente = () => {
  if (calMes.value === 11) {
    calMes.value = 0
    calAnio.value++
  } else {
    calMes.value++
  }
}

const irHoy = () => {
  calAnio.value = hoy.getFullYear()
  calMes.value = hoy.getMonth()
}

// --- Resumen ---
const resumen = computed(() => {
  const total = eventosFiltrados.value.length
  const ots = eventosFiltrados.value.filter(e => e.tipo === 'ot').length
  const mps = eventosFiltrados.value.filter(e => e.tipo === 'mp').length
  const mpsVencidos = eventosFiltrados.value.filter(e => e.tipo === 'mp' && e.estado === 'Vencida').length
  const mpsProgramados = eventosFiltrados.value.filter(e => e.tipo === 'mp' && e.estado === 'Programada').length
  return { total, ots, mps, mpsVencidos, mpsProgramados }
})

// --- Limpiar filtros ---
const tieneFiltros = computed(() => filterEquipo.value || filterUbicacion.value || filterResponsable.value || filterTipo.value)

const limpiarFiltros = () => {
  filterEquipo.value = ''
  filterUbicacion.value = ''
  filterResponsable.value = ''
  filterTipo.value = ''
}

// --- Detalle de evento ---
const openDetalle = (evento) => {
  detalleEvento.value = evento
  showDetalleModal.value = true
}

const irAOrden = (otId) => {
  showDetalleModal.value = false
  router.push('/ordenes')
}

const irAPreventivo = () => {
  showDetalleModal.value = false
  router.push('/preventivo')
}

// --- Color del evento ---
const getEventoColor = (evento) => {
  return evento.estado_color || '#95a5a6'
}

const getEventoBorder = (evento) => {
  return `3px solid ${getEventoColor(evento)}`
}

onMounted(() => { fetchData() })
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>📅 Planificación de Mantenimiento</h2>
        <div class="top-bar-actions">
          <button class="btn-hoy" @click="irHoy">Hoy</button>
        </div>
      </div>

      <!-- Resumen rápido -->
      <div class="resumen-bar">
        <div class="resumen-item">
          <span class="resumen-num">{{ resumen.total }}</span>
          <span class="resumen-label">Total eventos</span>
        </div>
        <div class="resumen-item resumen-ot">
          <span class="resumen-num">{{ resumen.ots }}</span>
          <span class="resumen-label">OTs</span>
        </div>
        <div class="resumen-item resumen-mp">
          <span class="resumen-num">{{ resumen.mps }}</span>
          <span class="resumen-label">MPs</span>
        </div>
        <div class="resumen-item resumen-vencido" v-if="resumen.mpsVencidos > 0">
          <span class="resumen-num">{{ resumen.mpsVencidos }}</span>
          <span class="resumen-label">🔴 Vencidos</span>
        </div>
        <div class="resumen-item resumen-programado" v-if="resumen.mpsProgramados > 0">
          <span class="resumen-num">{{ resumen.mpsProgramados }}</span>
          <span class="resumen-label">🟢 Programados</span>
        </div>
      </div>

      <!-- Filtros -->
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Tipo:</label>
          <select v-model="filterTipo" class="filter-select">
            <option value="">Todo</option>
            <option value="ot">Solo OT</option>
            <option value="mp">Solo MP</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Equipo:</label>
          <select v-model="filterEquipo" class="filter-select">
            <option value="">Todos</option>
            <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Ubicación:</label>
          <select v-model="filterUbicacion" class="filter-select">
            <option value="">Todas</option>
            <option v-for="u in ubicacionesUnicas" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Responsable:</label>
          <select v-model="filterResponsable" class="filter-select">
            <option value="">Todos</option>
            <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.full_name || u.username }}</option>
          </select>
        </div>
        <button v-if="tieneFiltros" class="btn-clear-filters" @click="limpiarFiltros">Limpiar</button>
      </div>

      <!-- Navegación del calendario -->
      <div class="cal-nav">
        <button class="cal-nav-btn" @click="mesAnterior">← Anterior</button>
        <h3 class="cal-title">{{ MESES[calMes] }} {{ calAnio }}</h3>
        <button class="cal-nav-btn" @click="mesSiguiente">Siguiente →</button>
      </div>

      <!-- Calendario -->
      <div v-if="loading" class="loading-msg">Cargando calendario...</div>

      <div v-else class="cal-grid">
        <!-- Encabezados -->
        <div v-for="dia in DIAS_SEMANA" :key="dia" class="cal-header">{{ dia }}</div>

        <!-- Días -->
        <div
          v-for="(celda, idx) in diasDelMes"
          :key="idx"
          class="cal-cell"
          :class="{ 'cal-cell--empty': !celda.dia, 'cal-cell--today': celda.esHoy }"
        >
          <div v-if="celda.dia" class="cal-day-number">{{ celda.dia }}</div>
          <div v-if="celda.dia && celda.eventos.length > 0" class="cal-events">
            <div
              v-for="evento in celda.eventos.slice(0, 4)"
              :key="evento.id"
              class="cal-event"
              :style="{ borderLeft: getEventoBorder(evento) }"
              :class="'cal-event--' + evento.tipo"
              @click="openDetalle(evento)"
              :title="`${evento.tipoLabel}: ${evento.titulo} — ${evento.equipo_nombre}`"
            >
              <span class="cal-event-badge">{{ evento.tipoLabel }}</span>
              <span class="cal-event-title">{{ evento.titulo }}</span>
            </div>
            <div v-if="celda.eventos.length > 4" class="cal-event-more">
              +{{ celda.eventos.length - 4 }} más...
            </div>
          </div>
        </div>
      </div>

      <!-- Leyenda -->
      <div class="cal-legend">
        <div class="legend-item">
          <span class="legend-dot" style="background: #16a34a;"></span> 🟢 MP Programada (OT activa)
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #eab308;"></span> 🟡 MP Recordatorio (próxima)
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #ef4444;"></span> 🔴 MP Vencida
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #3b82f6;"></span> 🔵 OT Abierta
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #f39c12;"></span> 🟠 OT En Proceso
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #27ae60;"></span> ✅ OT Completada
        </div>
      </div>
    </main>

    <!-- Modal Detalle de Evento -->
    <div v-if="showDetalleModal && detalleEvento" class="modal-overlay" @click.self="showDetalleModal = false">
      <div class="modal" style="max-width: 550px;">
        <h3>
          <span class="detalle-tipo-badge" :class="'badge-' + detalleEvento.tipo">
            {{ detalleEvento.tipoLabel }}
          </span>
          {{ detalleEvento.titulo }}
        </h3>

        <div class="detalle-grid">
          <div class="detalle-col">
            <p><strong>Equipo:</strong> {{ detalleEvento.equipo_nombre }}</p>
            <p v-if="detalleEvento.ubicacion"><strong>Ubicación:</strong> {{ detalleEvento.ubicacion }}</p>
            <p><strong>Fecha:</strong> {{ detalleEvento.fecha }}</p>
            <p><strong>Estado:</strong>
              <span class="badge-estado" :style="{ backgroundColor: detalleEvento.estado_color }">
                {{ detalleEvento.estado }}
              </span>
            </p>
          </div>
          <div class="detalle-col">
            <p v-if="detalleEvento.responsable_nombre"><strong>Responsable:</strong> {{ detalleEvento.responsable_nombre }}</p>
            <p v-if="detalleEvento.prioridad"><strong>Prioridad:</strong> {{ detalleEvento.prioridad }}</p>
            <p v-if="detalleEvento.frecuencia_dias"><strong>Frecuencia:</strong> Cada {{ detalleEvento.frecuencia_dias }} días</p>
            <p v-if="detalleEvento.tiene_ot !== undefined">
              <strong>OT activa:</strong> {{ detalleEvento.tiene_ot ? '✅ Sí' : '❌ No' }}
            </p>
          </div>
        </div>

        <div v-if="detalleEvento.descripcion" class="detalle-desc">
          <strong>Descripción:</strong>
          <p>{{ detalleEvento.descripcion }}</p>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetalleModal = false">Cerrar</button>
          <button v-if="detalleEvento.tipo === 'ot'" class="btn-primary" @click="irAOrden(detalleEvento.ot_id)">
            Ir a Órdenes
          </button>
          <button v-if="detalleEvento.tipo === 'mp'" class="btn-primary" @click="irAPreventivo">
            Ir a Preventivo
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.top-bar h2 { margin: 0; }
.top-bar-actions { display: flex; gap: 0.5rem; align-items: center; }

.btn-hoy { background: #3498db; color: white; border: none; padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.btn-hoy:hover { background: #2980b9; }

/* Resumen */
.resumen-bar { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
.resumen-item { display: flex; flex-direction: column; align-items: center; padding: 0.5rem 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; min-width: 90px; }
.resumen-num { font-size: 1.4rem; font-weight: 700; color: #1e293b; }
.resumen-label { font-size: 0.72rem; color: #64748b; }
.resumen-ot .resumen-num { color: #2563eb; }
.resumen-mp .resumen-num { color: #f59e0b; }
.resumen-vencido .resumen-num { color: #dc2626; }
.resumen-programado .resumen-num { color: #16a34a; }

/* Filtros */
.filter-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; margin-bottom: 1rem; padding: 0.75rem 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.filter-group { display: flex; align-items: center; gap: 0.35rem; }
.filter-label { font-size: 0.82rem; font-weight: 600; color: #64748b; white-space: nowrap; }
.filter-select { padding: 0.35rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.82rem; min-width: 100px; }
.btn-clear-filters { padding: 0.35rem 0.7rem; border: 1px solid #fecaca; border-radius: 6px; background: #fef2f2; color: #dc2626; font-size: 0.78rem; font-weight: 600; cursor: pointer; }

/* Calendario */
.cal-nav { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.cal-nav-btn { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; color: #334155; }
.cal-nav-btn:hover { background: #e2e8f0; }
.cal-title { margin: 0; font-size: 1.2rem; color: #1e293b; }

.cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 2px; background: #e2e8f0; border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.cal-header { background: #2c3e50; color: white; text-align: center; padding: 0.5rem; font-weight: 700; font-size: 0.85rem; }
.cal-cell { background: white; min-height: 90px; padding: 0.3rem; display: flex; flex-direction: column; gap: 2px; }
.cal-cell--empty { background: #f8fafc; }
.cal-cell--today { background: #fef3c7; }
.cal-day-number { font-weight: 700; font-size: 0.85rem; color: #334155; }
.cal-cell--today .cal-day-number { color: #d97706; }

.cal-events { display: flex; flex-direction: column; gap: 2px; overflow: hidden; }
.cal-event { padding: 2px 5px; border-radius: 4px; font-size: 0.72rem; cursor: pointer; display: flex; align-items: center; gap: 3px; transition: transform 0.1s; overflow: hidden; white-space: nowrap; }
.cal-event:hover { transform: scale(1.02); }
.cal-event-badge { font-weight: 700; font-size: 0.65rem; padding: 1px 4px; border-radius: 3px; flex-shrink: 0; }
.cal-event--ot .cal-event-badge { background: #3b82f6; color: white; }
.cal-event--mp .cal-event-badge { background: #f59e0b; color: white; }
.cal-event-title { overflow: hidden; text-overflow: ellipsis; color: #334155; }
.cal-event-more { font-size: 0.68rem; color: #64748b; padding: 1px 5px; font-style: italic; }

/* Leyenda */
.cal-legend { display: flex; flex-wrap: wrap; gap: 1rem; margin-top: 1rem; padding: 0.75rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.legend-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; color: #475569; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
.modal { background: white; padding: 1.5rem; border-radius: 8px; width: 100%; max-width: 550px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal h3 { margin: 0 0 1rem 0; color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; }

.detalle-tipo-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; }
.badge-ot { background: #3b82f6; color: white; }
.badge-mp { background: #f59e0b; color: white; }

.detalle-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.detalle-col p { margin: 0.3rem 0; font-size: 0.88rem; color: #334155; }
.detalle-desc { margin-bottom: 1rem; padding: 0.75rem; background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; }
.detalle-desc p { margin: 0.3rem 0 0 0; font-size: 0.85rem; color: #475569; }

.badge-estado { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: white; }

.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
.btn-primary { background: #3498db; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-primary:hover { background: #2980b9; }
.btn-secondary { background: #95a5a6; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-secondary:hover { background: #7f8c8d; }

.loading-msg { text-align: center; padding: 2rem; color: #64748b; }

@media (max-width: 768px) {
  .cal-grid { grid-template-columns: repeat(7, minmax(60px, 1fr)); overflow-x: auto; }
  .cal-cell { min-height: 70px; }
  .detalle-grid { grid-template-columns: 1fr; }
}
</style>
