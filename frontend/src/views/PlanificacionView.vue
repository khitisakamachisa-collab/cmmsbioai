<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'

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

// --- Calendario: vista y navegación ---
const hoy = new Date()
const calAnio = ref(hoy.getFullYear())
const calMes = ref(hoy.getMonth())
const calVista = ref('mes')       // 'mes' | 'semana' | 'dia'
const calSemanaIdx = ref(0)       // índice de la semana seleccionada (solo modo semana)
const incluirFinesDeSemana = ref(true)

const DIAS_COMPLETO = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
const DIAS_LABORAL = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie']
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

// Horario de trabajo para vista día
const HORA_INICIO = 6
const HORA_FIN = 22
const HORAS = []
for (let h = HORA_INICIO; h <= HORA_FIN; h++) {
  HORAS.push(h)
}

// Días visibles según toggle
const diasVisibles = computed(() => {
  return incluirFinesDeSemana.value ? DIAS_COMPLETO : DIAS_LABORAL
})
const numColumnas = computed(() => diasVisibles.value.length)

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
      const fecha = ot.fecha_creacion
      if (!fecha) return

      // Intentar extraer hora del datetime
      let hora = null
      if (fecha.length > 10) {
        const timePart = fecha.substring(11, 16)
        if (timePart) hora = timePart
      }

      eventos.push({
        id: `ot-${ot.id}`,
        tipo: 'ot',
        tipoLabel: 'OT',
        fecha: fecha.substring(0, 10),
        hora: hora,
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

  // Procesar MPs: dos eventos por tarea (ultima_fecha y proxima_fecha)
  if (filterTipo.value !== 'ot') {
    tareasMP.value.forEach(tarea => {
      const tieneOt = ordenes.value.some(ot =>
        ot.orden_preventiva_id === tarea.id &&
        (ot.estado_id === 1 || ot.estado_id === 2 || ot.estado_id === 3)
      )

      // --- Evento 1: Última Fecha Realizada ---
      if (tarea.ultima_fecha) {
        eventos.push({
          id: `mp-ult-${tarea.id}`,
          tipo: 'mp',
          tipoLabel: 'MP',
          fecha: tarea.ultima_fecha.substring(0, 10),
          hora: null,
          titulo: tarea.titulo,
          equipo_id: tarea.equipo_id,
          equipo_nombre: getEquipoNombre(tarea.equipo_id),
          ubicacion: getEquipoUbicacion(tarea.equipo_id),
          responsable_id: tarea.responsable_id,
          responsable_nombre: getUsuarioNombre(tarea.responsable_id),
          estado: tieneOt ? 'Realizado' : 'No Realizado',
          estado_color: tieneOt ? '#16a34a' : '#6366f1',
          frecuencia_dias: tarea.frecuencia_dias,
          descripcion: tarea.descripcion,
          mp_id: tarea.id,
          tiene_ot: tieneOt,
          mp_fecha_tipo: 'ultima'
        })
      }

      // --- Evento 2: Próxima Fecha Programada ---
      if (tarea.proxima_fecha) {
        let color = '#eab308'
        let estadoLabel = 'Programado'
        if (tieneOt) {
          color = '#16a34a'
          estadoLabel = 'Con OT'
        } else {
          const today = new Date().setHours(0, 0, 0, 0)
          const dueDate = new Date(tarea.proxima_fecha).setHours(0, 0, 0, 0)
          if (dueDate < today) {
            color = '#ef4444'
            estadoLabel = 'Vencido'
          } else if (dueDate === today) {
            color = '#f97316'
            estadoLabel = 'Hoy'
          }
        }

        eventos.push({
          id: `mp-prox-${tarea.id}`,
          tipo: 'mp',
          tipoLabel: 'MP',
          fecha: tarea.proxima_fecha.substring(0, 10),
          hora: null,
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
          tiene_ot: tieneOt,
          mp_fecha_tipo: 'proxima'
        })
      }
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

// --- Eventos agrupados por fecha ---
const eventosPorFecha = computed(() => {
  const map = {}
  eventosFiltrados.value.forEach(e => {
    if (!map[e.fecha]) map[e.fecha] = []
    map[e.fecha].push(e)
  })
  return map
})

// --- Obtener día de la semana (0=Lun ... 6=Dom) ---
const getDiaSemana = (fechaStr) => {
  const d = new Date(fechaStr + 'T00:00:00')
  let dow = d.getDay() - 1  // 0=dom -> -1
  if (dow < 0) dow = 6
  return dow
}

// ============================
// LÓGICA: VISTA MES
// ============================
const diasDelMes = computed(() => {
  const year = calAnio.value
  const month = calMes.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)

  let firstDayOfWeek = firstDay.getDay() - 1
  if (firstDayOfWeek < 0) firstDayOfWeek = 6

  const totalDays = lastDay.getDate()
  const cols = numColumnas.value
  const celdas = []

  // Si solo laborales, ajustar el offset (sab=5, dom=6 se saltan)
  for (let i = 0; i < firstDayOfWeek; i++) {
    const dayIndex = i  // 0=Lun..6=Dom
    if (!incluirFinesDeSemana.value && (dayIndex === 5 || dayIndex === 6)) continue
    celdas.push({ dia: null, fecha: null, eventos: [], esHoy: false, esFinSemana: false })
  }

  for (let d = 1; d <= totalDays; d++) {
    const fechaStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const dow = getDiaSemana(fechaStr)
    const esFinSemana = dow >= 5

    // Si solo laborales y es finde, no agregar celda
    if (!incluirFinesDeSemana.value && esFinSemana) continue

    const eventosDelDia = eventosPorFecha.value[fechaStr] || []
    const esHoy = (d === hoy.getDate() && month === hoy.getMonth() && year === hoy.getFullYear())
    celdas.push({ dia: d, fecha: fechaStr, eventos: eventosDelDia, esHoy, esFinSemana })
  }

  // Completar última fila
  while (celdas.length % cols !== 0) {
    celdas.push({ dia: null, fecha: null, eventos: [], esHoy: false, esFinSemana: false })
  }

  return celdas
})

// ============================
// LÓGICA: VISTA SEMANA
// ============================
const semanasDelMes = computed(() => {
  const year = calAnio.value
  const month = calMes.value
  const firstDay = new Date(year, month, 1)
  const lastDay = new Date(year, month + 1, 0)
  const totalDays = lastDay.getDate()

  let firstDayOfWeek = firstDay.getDay() - 1
  if (firstDayOfWeek < 0) firstDayOfWeek = 6

  const semanas = []
  let semanaActual = []

  // Agregar celdas vacías antes del primer día
  for (let i = 0; i < firstDayOfWeek; i++) {
    const dayIndex = i
    if (!incluirFinesDeSemana.value && (dayIndex === 5 || dayIndex === 6)) continue
    semanaActual.push({ dia: null, fecha: null, eventos: [], esHoy: false, esFinSemana: false })
  }

  for (let d = 1; d <= totalDays; d++) {
    const fechaStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`
    const dow = getDiaSemana(fechaStr)
    const esFinSemana = dow >= 5

    if (!incluirFinesDeSemana.value && esFinSemana) continue

    const eventosDelDia = eventosPorFecha.value[fechaStr] || []
    const esHoy = (d === hoy.getDate() && month === hoy.getMonth() && year === hoy.getFullYear())
    semanaActual.push({ dia: d, fecha: fechaStr, eventos: eventosDelDia, esHoy, esFinSemana })

    // Cuando llegamos al último día visible de la semana
    const lastVisibleDow = incluirFinesDeSemana.value ? 6 : 4
    if (dow === lastVisibleDow) {
      semanas.push(semanaActual)
      semanaActual = []
    }
  }

  // Agregar la última semana si tiene contenido
  if (semanaActual.length > 0) {
    // Completar con celdas vacías
    const cols = numColumnas.value
    while (semanaActual.length % cols !== 0) {
      semanaActual.push({ dia: null, fecha: null, eventos: [], esHoy: false, esFinSemana: false })
    }
    semanas.push(semanaActual)
  }

  return semanas
})

// Ajustar semanaIdx cuando cambian semanas
watch(semanasDelMes, (semanas) => {
  if (calSemanaIdx.value >= semanas.length) {
    calSemanaIdx.value = Math.max(0, semanas.length - 1)
  }
})

const semanaActual = computed(() => {
  const semanas = semanasDelMes.value
  if (!semanas.length) return []
  return semanas[calSemanaIdx.value] || semanas[0]
})

const semanaLabel = computed(() => {
  const dias = semanaActual.value.filter(d => d.dia !== null)
  if (dias.length === 0) return ''
  const primerDia = dias[0]
  const ultimoDia = dias[dias.length - 1]
  if (primerDia.dia === ultimoDia.dia) {
    return `${primerDia.dia} de ${MESES[calMes.value]}`
  }
  return `${primerDia.dia} - ${ultimoDia.dia} de ${MESES[calMes.value]}`
})

// ============================
// LÓGICA: VISTA DÍA
// ============================

// Navegación por día (cambia la fecha seleccionada dentro del mes)
const diaNavOffset = ref(0)
const diaActualFecha = computed(() => {
  const base = new Date(calAnio.value, calMes.value, 1)
  base.setDate(base.getDate() + diaNavOffset.value)
  const y = base.getFullYear()
  const m = String(base.getMonth() + 1).padStart(2, '0')
  const d = String(base.getDate()).padStart(2, '0')
  return `${y}-${m}-${d}`
})

const diaActualEventos = computed(() => {
  return eventosPorFecha.value[diaActualFecha.value] || []
})

const diaActualLabel = computed(() => {
  const d = new Date(diaActualFecha.value + 'T00:00:00')
  const diasNombres = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado']
  return `${diasNombres[d.getDay()]}, ${d.getDate()} de ${MESES[d.getMonth()]} de ${d.getFullYear()}`
})

// Eventos por hora para la vista día
const eventosPorHora = computed(() => {
  const map = {}
  HORAS.forEach(h => { map[h] = [] })
  diaActualEventos.value.forEach(ev => {
    const h = ev.hora ? parseInt(ev.hora.substring(0, 2)) : null
    if (h !== null && h >= HORA_INICIO && h <= HORA_FIN) {
      map[h].push(ev)
    } else {
      // Sin hora: poner en hora 8 por defecto
      map[8].push(ev)
    }
  })
  return map
})

// --- Navegación del calendario ---
const irAtras = () => {
  if (calVista.value === 'dia') {
    // Navegar un día atrás, cruzando meses si es necesario
    const actual = new Date(diaActualFecha.value + 'T12:00:00')
    actual.setDate(actual.getDate() - 1)
    calAnio.value = actual.getFullYear()
    calMes.value = actual.getMonth()
    diaNavOffset.value--
  } else if (calVista.value === 'semana') {
    if (calSemanaIdx.value > 0) {
      calSemanaIdx.value--
    }
  } else {
    if (calMes.value === 0) {
      calMes.value = 11
      calAnio.value--
    } else {
      calMes.value--
    }
  }
}

const irAdelante = () => {
  if (calVista.value === 'dia') {
    // Navegar un día adelante, cruzando meses si es necesario
    const actual = new Date(diaActualFecha.value + 'T12:00:00')
    actual.setDate(actual.getDate() + 1)
    calAnio.value = actual.getFullYear()
    calMes.value = actual.getMonth()
    diaNavOffset.value++
  } else if (calVista.value === 'semana') {
    if (calSemanaIdx.value < semanasDelMes.value.length - 1) {
      calSemanaIdx.value++
    }
  } else {
    if (calMes.value === 11) {
      calMes.value = 0
      calAnio.value++
    } else {
      calMes.value++
    }
  }
}

const irHoy = () => {
  calAnio.value = hoy.getFullYear()
  calMes.value = hoy.getMonth()
  diaNavOffset.value = 0
  calSemanaIdx.value = 0
  // En vista semana, ir a la semana que contiene hoy
  const hoyDow = getDiaSemana(
    `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`
  )
  const lastVisibleDow = incluirFinesDeSemana.value ? 6 : 4
  let semanaDeHoy = 0
  if (semanasDelMes.value.length > 0) {
    for (let i = 0; i < semanasDelMes.value.length; i++) {
      const semana = semanasDelMes.value[i]
      if (semana.some(c => c.fecha === `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, '0')}-${String(hoy.getDate()).padStart(2, '0')}`)) {
        semanaDeHoy = i
        break
      }
    }
  }
  calSemanaIdx.value = semanaDeHoy
}

// Reset semanaIdx al cambiar mes o toggle fines de semana
watch([calMes, calAnio, incluirFinesDeSemana], () => {
  calSemanaIdx.value = 0
  diaNavOffset.value = 0
})

// Título de la navegación
const navTitle = computed(() => {
  if (calVista.value === 'mes') {
    return `${MESES[calMes.value]} ${calAnio.value}`
  } else if (calVista.value === 'semana') {
    return semanaLabel.value
  } else {
    return diaActualLabel.value
  }
})

// --- Resumen ---
const resumen = computed(() => {
  const total = eventosFiltrados.value.length
  const ots = eventosFiltrados.value.filter(e => e.tipo === 'ot').length
  const mps = eventosFiltrados.value.filter(e => e.tipo === 'mp').length
  const mpsNoRealizado = eventosFiltrados.value.filter(e => e.tipo === 'mp' && e.mp_fecha_tipo === 'ultima' && e.estado === 'No Realizado').length
  const mpsVencidos = eventosFiltrados.value.filter(e => e.tipo === 'mp' && e.mp_fecha_tipo === 'proxima' && e.estado === 'Vencido').length
  const mpsProgramados = eventosFiltrados.value.filter(e => e.tipo === 'mp' && e.mp_fecha_tipo === 'proxima' && (e.estado === 'Programado' || e.estado === 'Con OT')).length
  return { total, ots, mps, mpsNoRealizado, mpsVencidos, mpsProgramados }
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

// --- Hora actual para vista día ---
const horaLabel = (h) => String(h).padStart(2, '0') + ':00'

const isCurrentHour = (hora) => {
  const now = new Date()
  return now.getHours() === hora &&
    calAnio.value === now.getFullYear() &&
    calMes.value === now.getMonth() &&
    diaActualFecha.value === `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
}

// --- Color del evento ---
const getEventoBorder = (evento) => {
  return `3px solid ${evento.estado_color || '#95a5a6'}`
}

onMounted(() => { fetchData() })
</script>

<template>
  <div class="dashboard-container">

    <main class="content">
      <div class="top-bar">
        <h2>Planificación de Mantenimiento</h2>
        <div class="top-bar-actions">
          <button class="btn-hoy" @click="irHoy">Hoy</button>
        </div>
      </div>

      <!-- Resumen rápido (centrado) -->
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
        <div class="resumen-item resumen-no-realizado" v-if="resumen.mpsNoRealizado > 0">
          <span class="resumen-num">{{ resumen.mpsNoRealizado }}</span>
          <span class="resumen-label">No Realizados</span>
        </div>
        <div class="resumen-item resumen-vencido" v-if="resumen.mpsVencidos > 0">
          <span class="resumen-num">{{ resumen.mpsVencidos }}</span>
          <span class="resumen-label">Vencidos</span>
        </div>
        <div class="resumen-item resumen-programado" v-if="resumen.mpsProgramados > 0">
          <span class="resumen-num">{{ resumen.mpsProgramados }}</span>
          <span class="resumen-label">Programados</span>
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

      <!-- Controles de vista + navegación -->
      <div class="cal-controls">
        <div class="cal-controls-left">
          <!-- Toggle vista: Mes / Semana / Día -->
          <div class="vista-toggle">
            <button
              class="vista-btn"
              :class="{ 'vista-btn--active': calVista === 'mes' }"
              @click="calVista = 'mes'"
            >Mes</button>
            <button
              class="vista-btn"
              :class="{ 'vista-btn--active': calVista === 'semana' }"
              @click="calVista = 'semana'"
            >Semana</button>
            <button
              class="vista-btn"
              :class="{ 'vista-btn--active': calVista === 'dia' }"
              @click="calVista = 'dia'; diaNavOffset = 0"
            >Día</button>
          </div>
          <!-- Toggle fines de semana -->
          <label class="toggle-finsemana" :class="{ 'toggle-finsemana--off': !incluirFinesDeSemana }">
            <input type="checkbox" v-model="incluirFinesDeSemana">
            <span class="toggle-slider"></span>
            <span class="toggle-text">{{ incluirFinesDeSemana ? 'Lun-Dom' : 'Lun-Vie' }}</span>
          </label>
        </div>

        <div class="cal-nav">
          <button class="cal-nav-btn" @click="irAtras">&larr; Anterior</button>
          <h3 class="cal-title">{{ navTitle }}</h3>
          <button class="cal-nav-btn" @click="irAdelante">Siguiente &rarr;</button>
        </div>
      </div>

      <!-- Calendario -->
      <div v-if="loading" class="loading-msg">Cargando calendario...</div>

      <!-- ==================== VISTA MES ==================== -->
      <div v-else-if="calVista === 'mes'" class="cal-grid" :style="{ gridTemplateColumns: `repeat(${numColumnas}, 1fr)` }">
        <div v-for="dia in diasVisibles" :key="dia" class="cal-header">{{ dia }}</div>
        <div
          v-for="(celda, idx) in diasDelMes"
          :key="idx"
          class="cal-cell"
          :class="{
            'cal-cell--empty': !celda.dia,
            'cal-cell--today': celda.esHoy,
            'cal-cell--weekend': celda.esFinSemana
          }"
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
              <span class="cal-event-badge">{{ evento.tipoLabel }}{{ evento.mp_fecha_tipo === 'ultima' ? ' Ult.' : '' }}</span>
              <span class="cal-event-title">{{ evento.titulo }}</span>
            </div>
            <div v-if="celda.eventos.length > 4" class="cal-event-more">
              +{{ celda.eventos.length - 4 }} más...
            </div>
          </div>
        </div>
      </div>

      <!-- ==================== VISTA SEMANA ==================== -->
      <div v-else-if="calVista === 'semana'" class="cal-grid cal-grid--semana" :style="{ gridTemplateColumns: `repeat(${numColumnas}, 1fr)` }">
        <div v-for="dia in diasVisibles" :key="dia" class="cal-header">{{ dia }}</div>
        <div
          v-for="(celda, idx) in semanaActual"
          :key="idx"
          class="cal-cell cal-cell--semana"
          :class="{
            'cal-cell--empty': !celda.dia,
            'cal-cell--today': celda.esHoy,
            'cal-cell--weekend': celda.esFinSemana
          }"
        >
          <div v-if="celda.dia" class="cal-day-number">{{ celda.dia }}</div>
          <div v-if="celda.dia && celda.eventos.length > 0" class="cal-events">
            <div
              v-for="evento in celda.eventos"
              :key="evento.id"
              class="cal-event"
              :style="{ borderLeft: getEventoBorder(evento) }"
              :class="'cal-event--' + evento.tipo"
              @click="openDetalle(evento)"
              :title="`${evento.tipoLabel}: ${evento.titulo} — ${evento.equipo_nombre}`"
            >
              <span class="cal-event-badge">{{ evento.tipoLabel }}{{ evento.mp_fecha_tipo === 'ultima' ? ' Ult.' : '' }}</span>
              <span class="cal-event-title">{{ evento.titulo }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Selector de semana (solo en vista semana si hay más de 1) -->
      <div v-if="calVista === 'semana' && semanasDelMes.length > 1" class="semana-selector">
        <button
          v-for="(sem, idx) in semanasDelMes"
          :key="idx"
          class="semana-btn"
          :class="{ 'semana-btn--active': idx === calSemanaIdx }"
          @click="calSemanaIdx = idx"
        >
          Sem {{ idx + 1 }}
        </button>
      </div>

      <!-- ==================== VISTA DÍA ==================== -->
      <div v-else-if="calVista === 'dia'" class="dia-view">
        <div class="dia-timeline">
          <div
            v-for="hora in HORAS"
            :key="hora"
            class="dia-hour-row"
            :class="{ 'dia-hour-row--now': isCurrentHour(hora) }"
          >
            <div class="dia-hour-label">{{ horaLabel(hora) }}</div>
            <div class="dia-hour-content">
              <div
                v-for="evento in (eventosPorHora[hora] || [])"
                :key="evento.id"
                class="dia-event"
                :style="{ borderLeft: getEventoBorder(evento) }"
                :class="'cal-event--' + evento.tipo"
                @click="openDetalle(evento)"
              >
                <div class="dia-event-header">
                  <span class="cal-event-badge">{{ evento.tipoLabel }}{{ evento.mp_fecha_tipo === 'ultima' ? ' Ult.' : '' }}</span>
                  <span v-if="evento.hora" class="dia-event-hora">{{ evento.hora }}</span>
                </div>
                <span class="dia-event-title">{{ evento.titulo }}</span>
                <span class="dia-event-equipo">{{ evento.equipo_nombre }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Leyenda -->
      <div class="cal-legend">
        <div class="legend-item">
          <span class="legend-dot" style="background: #6366f1;"></span> MP No Realizado (Ult. Fecha)
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #16a34a;"></span> MP Realizado / Con OT
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #eab308;"></span> MP Programado (Prox. Fecha)
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #ef4444;"></span> MP Vencido
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #3b82f6;"></span> OT Abierta
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #f39c12;"></span> OT En Proceso
        </div>
        <div class="legend-item">
          <span class="legend-dot" style="background: #27ae60;"></span> OT Completada
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
            <p><strong>Fecha:</strong> {{ detalleEvento.fecha }} <span v-if="detalleEvento.mp_fecha_tipo === 'ultima'" class="badge-tipo-fecha">Ult. Realizada</span><span v-else-if="detalleEvento.mp_fecha_tipo === 'proxima'" class="badge-tipo-fecha badge-tipo-proxima">Prox. Programada</span></p>
            <p v-if="detalleEvento.hora"><strong>Hora:</strong> {{ detalleEvento.hora }}</p>
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
              <strong>OT activa:</strong> {{ detalleEvento.tiene_ot ? 'Sí' : 'No' }}
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
.content { padding: 2rem; max-width: 1400px; margin: 0 auto; }
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.top-bar h2 { margin: 0; font-size: 1.3rem; color: #1e293b; }
.top-bar-actions { display: flex; gap: 0.5rem; align-items: center; }

.btn-hoy { background: #3498db; color: white; border: none; padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.btn-hoy:hover { background: #2980b9; }

/* ===== Resumen (centrado) ===== */
.resumen-bar {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
  justify-content: center;
}
.resumen-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 1.25rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  min-width: 95px;
}
.resumen-num { font-size: 1.4rem; font-weight: 700; color: #1e293b; }
.resumen-label { font-size: 0.72rem; color: #64748b; font-weight: 500; }
.resumen-ot .resumen-num { color: #2563eb; }
.resumen-mp .resumen-num { color: #f59e0b; }
.resumen-no-realizado .resumen-num { color: #6366f1; }
.resumen-vencido .resumen-num { color: #dc2626; }
.resumen-programado .resumen-num { color: #16a34a; }

/* ===== Filtros ===== */
.filter-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; margin-bottom: 1rem; padding: 0.75rem 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.filter-group { display: flex; align-items: center; gap: 0.35rem; }
.filter-label { font-size: 0.82rem; font-weight: 600; color: #64748b; white-space: nowrap; }
.filter-select { padding: 0.35rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.82rem; min-width: 100px; }
.btn-clear-filters { padding: 0.35rem 0.7rem; border: 1px solid #fecaca; border-radius: 6px; background: #fef2f2; color: #dc2626; font-size: 0.78rem; font-weight: 600; cursor: pointer; }

/* ===== Controles de vista + navegación ===== */
.cal-controls {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.cal-controls-left {
  display: flex;
  align-items: center;
  gap: 1rem;
}

/* Toggle vista */
.vista-toggle {
  display: flex;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.vista-btn {
  padding: 0.4rem 1rem;
  border: none;
  background: white;
  cursor: pointer;
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  transition: all 0.2s;
}
.vista-btn + .vista-btn { border-left: 1px solid #e2e8f0; }
.vista-btn:hover { background: #f1f5f9; color: #334155; }
.vista-btn--active { background: #3b82f6; color: white; }
.vista-btn--active:hover { background: #2563eb; color: white; }

/* Toggle fines de semana */
.toggle-finsemana {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  user-select: none;
}
.toggle-finsemana input { display: none; }
.toggle-slider {
  width: 36px;
  height: 20px;
  background: #94a3b8;
  border-radius: 10px;
  position: relative;
  transition: background 0.2s;
}
.toggle-slider::after {
  content: '';
  position: absolute;
  top: 2px;
  left: 2px;
  width: 16px;
  height: 16px;
  background: white;
  border-radius: 50%;
  transition: transform 0.2s;
}
.toggle-finsemana input:checked + .toggle-slider { background: #3b82f6; }
.toggle-finsemana input:checked + .toggle-slider::after { transform: translateX(16px); }
.toggle-text {
  font-size: 0.78rem;
  font-weight: 600;
  color: #475569;
  min-width: 52px;
}

/* Navegación */
.cal-nav { display: flex; align-items: center; gap: 0.75rem; }
.cal-nav-btn { background: #f1f5f9; border: 1px solid #cbd5e1; padding: 0.4rem 1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; color: #334155; white-space: nowrap; }
.cal-nav-btn:hover { background: #e2e8f0; }
.cal-title { margin: 0; font-size: 1.15rem; color: #1e293b; white-space: nowrap; }

/* ===== Calendario (mes y semana) ===== */
.cal-grid {
  display: grid;
  gap: 2px;
  background: #e2e8f0;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.cal-grid--semana .cal-cell { min-height: 200px; }
.cal-header { background: #2c3e50; color: white; text-align: center; padding: 0.5rem; font-weight: 700; font-size: 0.85rem; }
.cal-cell { background: white; min-height: 90px; padding: 0.3rem; display: flex; flex-direction: column; gap: 2px; }
.cal-cell--empty { background: #f8fafc; }
.cal-cell--today { background: #fef3c7; }
.cal-cell--weekend { background: #f8fafc; }
.cal-cell--weekend.cal-cell--today { background: #fef3c7; }
.cal-day-number { font-weight: 700; font-size: 0.85rem; color: #334155; }
.cal-cell--today .cal-day-number { color: #d97706; background: #fbbf24; width: 24px; height: 24px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; }

.cal-events { display: flex; flex-direction: column; gap: 2px; overflow: hidden; flex: 1; }
.cal-event {
  padding: 2px 5px;
  border-radius: 4px;
  font-size: 0.72rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 3px;
  transition: transform 0.1s;
  overflow: hidden;
  white-space: nowrap;
  background: #f8fafc;
}
.cal-event:hover { transform: scale(1.02); background: #f1f5f9; }
.cal-event-badge { font-weight: 700; font-size: 0.65rem; padding: 1px 4px; border-radius: 3px; flex-shrink: 0; }
.cal-event--ot .cal-event-badge { background: #3b82f6; color: white; }
.cal-event--mp .cal-event-badge { background: #f59e0b; color: white; }
.cal-event-title { overflow: hidden; text-overflow: ellipsis; color: #334155; }
.cal-event-more { font-size: 0.68rem; color: #64748b; padding: 1px 5px; font-style: italic; }

/* Selector de semana */
.semana-selector {
  display: flex;
  gap: 0.4rem;
  margin-top: 0.5rem;
  justify-content: center;
  flex-wrap: wrap;
}
.semana-btn {
  padding: 0.3rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  background: white;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
  color: #475569;
  transition: all 0.15s;
}
.semana-btn:hover { background: #f1f5f9; }
.semana-btn--active { background: #3b82f6; color: white; border-color: #3b82f6; }

/* ===== Vista Día ===== */
.dia-view {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.dia-timeline { max-height: 75vh; overflow-y: auto; }
.dia-hour-row {
  display: flex;
  border-bottom: 1px solid #f1f5f9;
  min-height: 52px;
}
.dia-hour-row--now { background: #fffbeb; }
.dia-hour-label {
  width: 65px;
  flex-shrink: 0;
  padding: 0.4rem 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748b;
  text-align: right;
  border-right: 1px solid #e2e8f0;
}
.dia-hour-content {
  flex: 1;
  padding: 0.25rem 0.4rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}
.dia-event {
  padding: 0.4rem 0.6rem;
  border-radius: 5px;
  cursor: pointer;
  background: #f8fafc;
  transition: all 0.15s;
}
.dia-event:hover { background: #f1f5f9; transform: translateX(2px); }
.dia-event-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.15rem;
}
.dia-event-hora {
  font-size: 0.68rem;
  font-weight: 600;
  color: #64748b;
}
.dia-event-title {
  display: block;
  font-size: 0.82rem;
  font-weight: 600;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dia-event-equipo {
  display: block;
  font-size: 0.72rem;
  color: #64748b;
}

/* ===== Leyenda ===== */
.cal-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-top: 1rem;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.legend-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.78rem; color: #475569; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex-shrink: 0; }

/* ===== Modal ===== */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
.modal { background: white; padding: 1.5rem; border-radius: 8px; width: 100%; max-width: 550px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal h3 { margin: 0 0 1rem 0; color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; display: flex; align-items: center; gap: 0.5rem; font-size: 1rem; }

.detalle-tipo-badge { padding: 2px 8px; border-radius: 4px; font-size: 0.78rem; font-weight: 700; }
.badge-ot { background: #3b82f6; color: white; }
.badge-mp { background: #f59e0b; color: white; }

.detalle-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; margin-bottom: 1rem; }
.detalle-col p { margin: 0.3rem 0; font-size: 0.88rem; color: #334155; }
.detalle-desc { margin-bottom: 1rem; padding: 0.75rem; background: #f8fafc; border-radius: 6px; border: 1px solid #e2e8f0; }
.detalle-desc p { margin: 0.3rem 0 0 0; font-size: 0.85rem; color: #475569; }

.badge-estado { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: white; }
.badge-tipo-fecha { display: inline-block; padding: 1px 6px; border-radius: 8px; font-size: 0.68rem; font-weight: 700; background: #6366f1; color: white; margin-left: 0.35rem; vertical-align: middle; }
.badge-tipo-proxima { background: #eab308; }

.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
.btn-primary { background: #3498db; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-primary:hover { background: #2980b9; }
.btn-secondary { background: #95a5a6; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-secondary:hover { background: #7f8c8d; }

.loading-msg { text-align: center; padding: 2rem; color: #64748b; }

/* ===== Responsive ===== */
@media (max-width: 768px) {
  .cal-grid { grid-template-columns: repeat(7, minmax(55px, 1fr)) !important; overflow-x: auto; }
  .cal-cell { min-height: 70px; }
  .cal-grid--semana .cal-cell { min-height: 150px; }
  .cal-controls { flex-direction: column; align-items: stretch; }
  .cal-controls-left { justify-content: space-between; }
  .cal-nav { justify-content: center; }
  .detalle-grid { grid-template-columns: 1fr; }
  .dia-hour-label { width: 50px; font-size: 0.72rem; }
}
</style>