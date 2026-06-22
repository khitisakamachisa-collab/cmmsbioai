<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'

const router = useRouter()

// --- Variables ---
const tareas = ref([])
const equipos = ref([])
const usuarios = ref([])
const ordenes = ref([])  // v0.9.2: para verificar OTs activas por MP
const loading = ref(true)

const currentPage = ref(1)
const pageSize = ref(10)

// --- Filtros de busqueda ---
const searchQuery = ref('')
const filterEquipo = ref('')
const filterUbicacion = ref('')
const filterUsuario = ref('')
const filterEstado = ref('')

// --- Vista: Tabla o Calendario ---
const vistaActiva = ref('tabla')

// --- Calendario ---
const hoy = new Date()
const calAnio = ref(hoy.getFullYear())
const calMes = ref(hoy.getMonth()) // 0-based

const DIAS_SEMANA = ['Lun', 'Mar', 'Mie', 'Jue', 'Vie', 'Sab', 'Dom']
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

// --- Modal Detalle Calendario ---
const showDetalleModal = ref(false)
const detalleTarea = ref(null)

// --- Modal ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})

// --- Kit de mantenimiento ---
const listaInventario = ref([])
const selectedRepuestoId = ref(null)
const selectedCantidad = ref(1)
const repuestosSeleccionados = ref([])

// --- Modal Generar OT ---
const showGenerarOTModal = ref(false)
const generarOTData = ref({})
const generarOTLoading = ref(false)

const fetchInventario = async () => {
  const res = await apiClient.get('/repuestos/')
  listaInventario.value = res.data
}

// --- Datos ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resTareas, resEquipos, resUsers, resOrdenes] = await Promise.all([
      apiClient.get('/preventivo/'),
      apiClient.get('/equipos/'),
      apiClient.get('/users/'),
      apiClient.get('/ordenes/')  // v0.9.2: para verificar OTs activas por MP
    ])
    tareas.value = resTareas.data
    equipos.value = resEquipos.data
    usuarios.value = resUsers.data
    ordenes.value = resOrdenes.data  // v0.9.2
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// --- Opciones de filtros (derivadas de datos) ---
const ubicacionesUnicas = computed(() => {
  const uds = new Set()
  equipos.value.forEach(eq => {
    if (eq.ubicacion_actual) uds.add(eq.ubicacion_actual)
  })
  return Array.from(uds).sort()
})

// --- Tareas filtradas (afecta tabla + calendario) ---
const filteredTareas = computed(() => {
  let result = tareas.value

  // Filtro texto
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    result = result.filter(t => {
      const titulo = String(t.titulo ?? '').toLowerCase()
      const equipoNombre = getEquipoNombre(t.equipo_id).toLowerCase()
      const usuarioNombre = getUsuarioNombre(t.responsable_id).toLowerCase()
      return titulo.includes(q) || equipoNombre.includes(q) || usuarioNombre.includes(q)
    })
  }

  // Filtro equipo
  if (filterEquipo.value) {
    result = result.filter(t => String(t.equipo_id) === String(filterEquipo.value))
  }

  // Filtro ubicacion (del equipo asociado)
  if (filterUbicacion.value) {
    result = result.filter(t => {
      const eq = equipos.value.find(e => e.id === t.equipo_id)
      return eq && eq.ubicacion_actual === filterUbicacion.value
    })
  }

  // Filtro usuario/responsable
  if (filterUsuario.value) {
    result = result.filter(t => String(t.responsable_id) === String(filterUsuario.value))
  }

  // Filtro estado (v0.9.2: incluye ciclo verde→amarillo→rojo)
  if (filterEstado.value) {
    result = result.filter(t => getStatusClass(t.proxima_fecha, tieneOtActiva(t)) === filterEstado.value)
  }

  return result
})

const tieneFiltrosActivos = computed(() => {
  return searchQuery.value.trim() || filterEquipo.value || filterUbicacion.value || filterUsuario.value || filterEstado.value
})

const limpiarFiltros = () => {
  searchQuery.value = ''
  filterEquipo.value = ''
  filterUbicacion.value = ''
  filterUsuario.value = ''
  filterEstado.value = ''
}

watch([searchQuery, filterEquipo, filterUbicacion, filterUsuario, filterEstado], () => {
  currentPage.value = 1
})

// --- Acciones CRUD ---
const openCreateModal = async () => {
  isEditing.value = false
  formData.value = {
    equipo_id: '',
    responsable_id: null,
    titulo: '',
    frecuencia_dias: 90,
    ultima_fecha: null,
    proxima_fecha: ''  // v0.9.0: fecha REAL programada por el usuario (editable)
  }
  repuestosSeleccionados.value = []
  selectedRepuestoId.value = null
  selectedCantidad.value = 1
  try {
    await fetchInventario()
    showModal.value = true
  } catch (error) {
    console.error(error)
    alert('Error al cargar inventario')
  }
}

const openEditModal = async (tarea) => {
  isEditing.value = true
  selectedRepuestoId.value = null
  selectedCantidad.value = 1
  try {
    const [resTarea] = await Promise.all([
      apiClient.get(`/preventivo/${tarea.id}`),
      fetchInventario()
    ])
    const fullTarea = resTarea.data
    formData.value = { ...fullTarea }
    if (fullTarea.ultima_fecha) {
      formData.value.ultima_fecha = fullTarea.ultima_fecha.substring(0, 10)
    }
    // v0.9.0: formatear proxima_fecha para el date picker
    if (fullTarea.proxima_fecha) {
      formData.value.proxima_fecha = fullTarea.proxima_fecha.substring(0, 10)
    } else {
      formData.value.proxima_fecha = ''
    }
    repuestosSeleccionados.value = (fullTarea.repuestos_detalle || []).map((rep) => ({
      repuesto_id: rep.repuesto_id,
      nombre: rep.nombre_repuesto || `Repuesto #${rep.repuesto_id}`,
      cantidad: rep.cantidad_requerida
    }))
    showModal.value = true
  } catch (error) {
    console.error(error)
    alert('Error al cargar la tarea para editar')
  }
}

const addRepuesto = () => {
  if (!selectedRepuestoId.value || selectedCantidad.value < 1) return
  const repInfo = listaInventario.value.find((r) => r.id === selectedRepuestoId.value)
  if (!repInfo) return
  if (repuestosSeleccionados.value.some((r) => r.repuesto_id === repInfo.id)) {
    alert('Este repuesto ya esta en el kit')
    return
  }
  repuestosSeleccionados.value.push({
    repuesto_id: repInfo.id,
    nombre: repInfo.nombre_repuesto,
    cantidad: selectedCantidad.value
  })
  selectedRepuestoId.value = null
  selectedCantidad.value = 1
}

const removeRepuesto = (index) => {
  repuestosSeleccionados.value.splice(index, 1)
}

const buildPayload = () => {
  const payload = {
    equipo_id: formData.value.equipo_id,
    responsable_id: formData.value.responsable_id,
    titulo: formData.value.titulo,
    descripcion: formData.value.descripcion || null,
    frecuencia_dias: Number(formData.value.frecuencia_dias),
    ultima_fecha: formData.value.ultima_fecha || null,
    proxima_fecha: formData.value.proxima_fecha || null,  // v0.9.0: fecha REAL programada
    repuestos: repuestosSeleccionados.value.map((r) => ({
      repuesto_id: r.repuesto_id,
      cantidad_requerida: Number(r.cantidad)
    }))
  }
  if (isEditing.value) {
    return {
      titulo: payload.titulo,
      descripcion: payload.descripcion,
      frecuencia_dias: payload.frecuencia_dias,
      responsable_id: payload.responsable_id,
      ultima_fecha: payload.ultima_fecha,
      proxima_fecha: payload.proxima_fecha,  // v0.9.0
      repuestos: payload.repuestos
    }
  }
  return payload
}

// v0.9.0: Sugerir proxima_fecha basada en ultima_fecha + frecuencia_dias
// (el usuario puede modificarla libremente)
const sugerirProximaFecha = () => {
  if (formData.value.ultima_fecha && formData.value.frecuencia_dias) {
    const ultima = new Date(formData.value.ultima_fecha)
    const proxima = new Date(ultima)
    proxima.setDate(proxima.getDate() + Number(formData.value.frecuencia_dias))
    formData.value.proxima_fecha = proxima.toISOString().substring(0, 10)
  }
}

const saveTarea = async () => {
  try {
    const payload = buildPayload()
    if (isEditing.value) {
      await apiClient.put(`/preventivo/${formData.value.id}`, payload)
      alert('Tarea actualizada')
    } else {
      await apiClient.post('/preventivo/', payload)
      alert('Tarea creada')
    }
    showModal.value = false
    fetchData()
  } catch (error) {
    alert('Error al guardar tarea')
    console.error(error)
  }
}

const deleteTarea = async (id) => {
  if (confirm('Eliminar esta tarea preventiva?')) {
    try {
      await apiClient.delete(`/preventivo/${id}`)
      alert('Tarea eliminada')
      fetchData()
    } catch (e) {
      alert('Error al eliminar')
    }
  }
}

// --- Generar OT desde preventivo ---
const openGenerarOTModal = (tarea) => {
  generarOTData.value = {
    tarea_id: tarea.id,
    titulo: tarea.titulo,
    equipo: getEquipoNombre(tarea.equipo_id),
    prioridad: 'Media',
    tecnico_asignado_id: tarea.responsable_id || null,
    fecha_vencimiento: tarea.proxima_fecha ? tarea.proxima_fecha.substring(0, 10) : null
  }
  showGenerarOTModal.value = true
}

const generarOT = async () => {
  generarOTLoading.value = true
  try {
    const payload = {
      prioridad: generarOTData.value.prioridad,
      tecnico_asignado_id: generarOTData.value.tecnico_asignado_id || null,
      fecha_vencimiento: generarOTData.value.fecha_vencimiento || null
    }
    const res = await apiClient.post(`/preventivo/${generarOTData.value.tarea_id}/generar-ot`, payload)
    const otId = res.data.id
    showGenerarOTModal.value = false
    showDetalleModal.value = false
    
    if (confirm(`OT #${otId} creada exitosamente. Desea ir a editarla para agregar repuestos del kit?`)) {
      router.push('/ordenes')
    }
    
    fetchData()
  } catch (error) {
    const msg = error.response?.data?.detail || 'Error al generar OT'
    alert(msg)
    console.error(error)
  } finally {
    generarOTLoading.value = false
  }
}

// --- Helpers Visuales ---
const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.nombre_corto || eq.modelo) : 'N/A'
}
const getEquipoUbicacion = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.ubicacion_actual || 'Sin ubicacion') : 'N/A'
}
const getUsuarioNombre = (id) => {
  const u = usuarios.value.find(u => u.id === id)
  return u ? (u.full_name || u.username) : 'Sin asignar'
}

// v0.9.2: Helper para calcular estado del ciclo verde→amarillo→rojo
// Necesita saber si hay OT activa para este MP
const getStatusClass = (proximaFecha, tieneOtActiva = false) => {
  // 🟢 Verde: hay OT activa (programada)
  if (tieneOtActiva) return 'status-programada'

  if (!proximaFecha) return 'status-unknown'
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)

  // 🔴 Rojo: vencida (sin OT activa y fecha pasada)
  if (dueDate < today) return 'status-overdue'
  if (dueDate === today) return 'status-due-today'

  // 🟡 Amarillo: recordatorio (sin OT activa pero fecha futura)
  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return 'status-upcoming'

  return 'status-ok'
}

const getStatusLabel = (proximaFecha, tieneOtActiva = false) => {
  if (tieneOtActiva) return '🟢 Programada'
  if (!proximaFecha) return 'Sin fecha'
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)

  if (dueDate < today) return '🔴 Vencida'
  if (dueDate === today) return '🔴 Hoy'

  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return '🟡 Próxima'

  return '🟡 Recordatorio'
}

// v0.9.2: Verificar si una tarea tiene OT activa
const tieneOtActiva = (tarea) => {
  return ordenes.value.some(ot =>
    ot.orden_preventiva_id === tarea.id &&
    (ot.estado_id === 1 || ot.estado_id === 2 || ot.estado_id === 3)  // Abierta, En Proceso, Esp. Repuesto
  )
}

// Color para el calendario (v0.9.2: incluye verde para OT activa)
const getCalEventColor = (proximaFecha, tieneOt = false) => {
  if (tieneOt) return '#16a34a' // 🟢 verde: OT activa (programada)
  if (!proximaFecha) return '#94a3b8' // gris
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)

  if (dueDate < today) return '#ef4444' // 🔴 rojo: vencida
  if (dueDate === today) return '#f97316' // 🔴 naranja: hoy

  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return '#eab308' // 🟡 amarillo: próxima
  
  return '#22c55e' // verde
}

const getCalEventBg = (proximaFecha) => {
  if (!proximaFecha) return '#f1f5f9'
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)
  
  if (dueDate < today) return '#fef2f2'
  if (dueDate === today) return '#fff7ed'
  
  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return '#fefce8'
  
  return '#f0fdf4'
}

// --- Calendario: logica de grilla ---
const calTitulo = computed(() => `${MESES[calMes.value]} ${calAnio.value}`)

// Tareas agrupadas por fecha del mes actual (usando filteredTareas)
const tareasPorDia = computed(() => {
  const map = {}
  filteredTareas.value.forEach(tarea => {
    if (!tarea.proxima_fecha || !tarea.activa) return
    const fecha = new Date(tarea.proxima_fecha)
    if (fecha.getFullYear() === calAnio.value && fecha.getMonth() === calMes.value) {
      const dia = fecha.getDate()
      if (!map[dia]) map[dia] = []
      map[dia].push(tarea)
    }
  })
  return map
})

// Generar la grilla del mes: array de semanas, cada semana = 7 celdas
const calGrilla = computed(() => {
  const primerDia = new Date(calAnio.value, calMes.value, 1)
  const ultimoDia = new Date(calAnio.value, calMes.value + 1, 0)
  const totalDias = ultimoDia.getDate()
  
  // Dia de la semana del primer dia (0=domingo, convertir a lunes=0)
  let inicioSemana = primerDia.getDay() - 1
  if (inicioSemana < 0) inicioSemana = 6
  
  const celdas = []
  
  // Dias del mes anterior (celdas vacias)
  const mesAnteriorUltimoDia = new Date(calAnio.value, calMes.value, 0).getDate()
  for (let i = inicioSemana - 1; i >= 0; i--) {
    celdas.push({ dia: mesAnteriorUltimoDia - i, esMesActual: false, tareas: [] })
  }
  
  // Dias del mes actual
  for (let d = 1; d <= totalDias; d++) {
    celdas.push({ dia: d, esMesActual: true, tareas: tareasPorDia.value[d] || [] })
  }
  
  // Completar ultima semana hasta 7 celdas
  const resto = celdas.length % 7
  if (resto > 0) {
    for (let i = 1; i <= 7 - resto; i++) {
      celdas.push({ dia: i, esMesActual: false, tareas: [] })
    }
  }
  
  // Dividir en semanas
  const semanas = []
  for (let i = 0; i < celdas.length; i += 7) {
    semanas.push(celdas.slice(i, i + 7))
  }
  
  return semanas
})

const esHoy = (dia) => {
  return dia.esMesActual &&
    dia.dia === hoy.getDate() &&
    calMes.value === hoy.getMonth() &&
    calAnio.value === hoy.getFullYear()
}

const calAnterior = () => {
  if (calMes.value === 0) {
    calMes.value = 11
    calAnio.value--
  } else {
    calMes.value--
  }
}

const calSiguiente = () => {
  if (calMes.value === 11) {
    calMes.value = 0
    calAnio.value++
  } else {
    calMes.value++
  }
}

const calHoy = () => {
  calAnio.value = hoy.getFullYear()
  calMes.value = hoy.getMonth()
}

// --- Detalle de tarea desde calendario ---
const openDetalleTarea = (tarea) => {
  detalleTarea.value = tarea
  showDetalleModal.value = true
}

const closeDetalleYGenerarOT = () => {
  showDetalleModal.value = false
  openGenerarOTModal(detalleTarea.value)
}

const closeDetalleYEditar = () => {
  showDetalleModal.value = false
  openEditModal(detalleTarea.value)
}

// --- Paginacion tabla (usando filteredTareas) ---
const paginatedTareas = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredTareas.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredTareas.value.length / pageSize.value))
)

watch(
  () => filteredTareas.value.length,
  (len) => {
    const tp = Math.max(1, Math.ceil(len / pageSize.value))
    if (currentPage.value > tp) currentPage.value = tp
  }
)

const irPaginaAnterior = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}

const irPaginaSiguiente = () => {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

// --- Resumen rapido para el calendario (usando filteredTareas) ---
const resumenCalendario = computed(() => {
  const activas = filteredTareas.value.filter(t => t.activa)
  const total = activas.length
  const vencidas = activas.filter(t => getStatusClass(t.proxima_fecha, tieneOtActiva(t)) === 'status-overdue').length
  const hoyCount = activas.filter(t => getStatusClass(t.proxima_fecha, tieneOtActiva(t)) === 'status-due-today').length
  const proximas = activas.filter(t => getStatusClass(t.proxima_fecha, tieneOtActiva(t)) === 'status-upcoming').length
  const programadas = activas.filter(t => getStatusClass(t.proxima_fecha, tieneOtActiva(t)) === 'status-programada').length
  return { total, vencidas, hoy: hoyCount, proximas }
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Mantenimiento Preventivo</h2>
        <div class="top-bar-actions">
          <!-- Busqueda texto -->
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="Titulo, equipo, responsable..."
              autocomplete="off"
              aria-label="Buscar tareas preventivas"
            >
          </div>
          <!-- Toggle vista -->
          <div class="vista-toggle">
            <button 
              class="vista-btn" 
              :class="{ 'vista-btn--active': vistaActiva === 'tabla' }"
              @click="vistaActiva = 'tabla'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M0 2a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V2zm1 9v2a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2H1zm0-1h14V2a1 1 0 0 0-1-1H2a1 1 0 0 0-1 1v8zm7-4a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1H8zm0 2a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1H8zM2 5.5a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5zm0 2a.5.5 0 0 1 .5-.5h3a.5.5 0 0 1 0 1h-3a.5.5 0 0 1-.5-.5z"/>
              </svg>
              Tabla
            </button>
            <button 
              class="vista-btn" 
              :class="{ 'vista-btn--active': vistaActiva === 'calendario' }"
              @click="vistaActiva = 'calendario'"
            >
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"/>
              </svg>
              Calendario
            </button>
          </div>
          <button class="btn-primary" @click="openCreateModal">+ Nueva Tarea</button>
        </div>
      </div>

      <!-- Barra de filtros -->
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Equipo:</label>
          <select v-model="filterEquipo" class="filter-select">
            <option value="">Todos</option>
            <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Ubicacion:</label>
          <select v-model="filterUbicacion" class="filter-select">
            <option value="">Todas</option>
            <option v-for="ub in ubicacionesUnicas" :key="ub" :value="ub">{{ ub }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Responsable:</label>
          <select v-model="filterUsuario" class="filter-select">
            <option value="">Todos</option>
            <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.full_name || u.username }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Estado:</label>
          <select v-model="filterEstado" class="filter-select">
            <option value="">Todos</option>
            <option value="status-programada">🟢 Programada</option>
            <option value="status-overdue">🔴 Vencida</option>
            <option value="status-due-today">🔴 Hoy</option>
            <option value="status-upcoming">🟡 Próxima</option>
            <option value="status-ok">🟡 Recordatorio</option>
            <option value="status-unknown">Sin fecha</option>
          </select>
        </div>
        <button v-if="tieneFiltrosActivos" class="btn-clear-filters" @click="limpiarFiltros" title="Limpiar todos los filtros">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
          </svg>
          Limpiar
        </button>
        <span v-if="tieneFiltrosActivos" class="filter-count">{{ filteredTareas.length }} de {{ tareas.length }}</span>
      </div>

      <div v-if="loading">Cargando...</div>

      <!-- ==================== VISTA TABLA ==================== -->
      <template v-if="!loading && vistaActiva === 'tabla'">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Equipo</th>
              <th>Ubicacion</th>
              <th>Titulo</th>
              <th>Frecuencia</th>
              <th>Proxima Fecha</th>
              <th>Responsable</th>
              <th>Estado</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredTareas.length">
              <td class="table-empty-cell" colspan="9">
                {{ tieneFiltrosActivos ? 'No hay tareas que coincidan con los filtros.' : 'No hay tareas preventivas registradas.' }}
              </td>
            </tr>
            <tr v-for="tarea in paginatedTareas" :key="tarea.id">
              <td>#{{ tarea.id }}</td>
              <td>{{ getEquipoNombre(tarea.equipo_id) }}</td>
              <td>{{ getEquipoUbicacion(tarea.equipo_id) }}</td>
              <td><strong>{{ tarea.titulo }}</strong></td>
              <td>Cada {{ tarea.frecuencia_dias }} dias</td>
              <td>{{ tarea.proxima_fecha || 'Pendiente' }}</td>
              <td>{{ getUsuarioNombre(tarea.responsable_id) }}</td>
              <td>
                <span class="badge" :class="getStatusClass(tarea.proxima_fecha, tieneOtActiva(tarea))">
                  {{ getStatusLabel(tarea.proxima_fecha, tieneOtActiva(tarea)) }}
                </span>
              </td>
              <td class="actions-cell">
                <button class="btn-icon btn-generate-icon" title="Generar OT" @click="openGenerarOTModal(tarea)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M9.5 13a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0zm0-5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
                  </svg>
                </button>
                <button class="btn-icon" title="Editar" @click="openEditModal(tarea)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                     <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10z"/>
                  </svg>
                </button>
                <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteTarea(tarea.id)">
                   <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>

        <div
          v-if="filteredTareas.length"
          class="table-pagination"
          role="navigation"
          aria-label="Paginacion de tareas preventivas"
        >
          <button
            type="button"
            class="btn-pagination"
            :disabled="currentPage <= 1"
            @click="irPaginaAnterior"
          >
            Anterior
          </button>
          <span class="table-pagination-meta">
            Pagina {{ currentPage }} de {{ totalPages }}
          </span>
          <button
            type="button"
            class="btn-pagination"
            :disabled="currentPage >= totalPages"
            @click="irPaginaSiguiente"
          >
            Siguiente
          </button>
        </div>
      </template>

      <div v-if="!loading && vistaActiva === 'tabla' && !filteredTareas.length && tieneFiltrosActivos" class="empty-state">
        No hay tareas que coincidan con los filtros seleccionados.
      </div>

      <!-- ==================== VISTA CALENDARIO ==================== -->
      <template v-if="!loading && vistaActiva === 'calendario'">
        <!-- Leyenda de colores -->
        <div class="cal-legend">
          <span class="cal-legend-item"><span class="cal-legend-dot" style="background:#ef4444"></span> Vencida</span>
          <span class="cal-legend-item"><span class="cal-legend-dot" style="background:#f97316"></span> Hoy</span>
          <span class="cal-legend-item"><span class="cal-legend-dot" style="background:#eab308"></span> Proxima</span>
          <span class="cal-legend-item"><span class="cal-legend-dot" style="background:#22c55e"></span> OK</span>
          <span class="cal-legend-item"><span class="cal-legend-dot" style="background:#94a3b8"></span> Sin fecha</span>
        </div>

        <!-- Resumen rapido -->
        <div class="cal-summary">
          <div class="cal-summary-card cal-summary--total">
            <span class="cal-summary-num">{{ resumenCalendario.total }}</span>
            <span class="cal-summary-label">Tareas Activas</span>
          </div>
          <div class="cal-summary-card cal-summary--overdue">
            <span class="cal-summary-num">{{ resumenCalendario.vencidas }}</span>
            <span class="cal-summary-label">Vencidas</span>
          </div>
          <div class="cal-summary-card cal-summary--today">
            <span class="cal-summary-num">{{ resumenCalendario.hoy }}</span>
            <span class="cal-summary-label">Hoy</span>
          </div>
          <div class="cal-summary-card cal-summary--upcoming">
            <span class="cal-summary-num">{{ resumenCalendario.proximas }}</span>
            <span class="cal-summary-label">Proximas (7d)</span>
          </div>
        </div>

        <!-- Navegacion del calendario -->
        <div class="cal-nav">
          <button class="cal-nav-btn" @click="calAnterior">&larr; Anterior</button>
          <div class="cal-nav-center">
            <h3 class="cal-title">{{ calTitulo }}</h3>
            <button class="cal-hoy-btn" @click="calHoy">Hoy</button>
          </div>
          <button class="cal-nav-btn" @click="calSiguiente">Siguiente &rarr;</button>
        </div>

        <!-- Grilla del calendario -->
        <div class="cal-grid">
          <!-- Encabezado dias -->
          <div class="cal-header" v-for="dia in DIAS_SEMANA" :key="dia">{{ dia }}</div>
          
          <!-- Celdas -->
          <div 
            v-for="(celda, idx) in calGrilla.flat()" 
            :key="idx"
            class="cal-cell"
            :class="{ 
              'cal-cell--other': !celda.esMesActual, 
              'cal-cell--today': esHoy(celda),
              'cal-cell--has-tasks': celda.tareas.length > 0
            }"
          >
            <div class="cal-cell-header">
              <span class="cal-day-num">{{ celda.dia }}</span>
              <span v-if="celda.tareas.length > 1" class="cal-task-count">{{ celda.tareas.length }}</span>
            </div>
            <div class="cal-cell-events">
              <div 
                v-for="tarea in celda.tareas.slice(0, 3)" 
                :key="tarea.id"
                class="cal-event"
                :style="{
                  borderLeftColor: getCalEventColor(tarea.proxima_fecha, tieneOtActiva(tarea)),
                  backgroundColor: getCalEventBg(tarea.proxima_fecha)
                }"
                @click="openDetalleTarea(tarea)"
              >
                <span class="cal-event-title">{{ tarea.titulo }}</span>
                <span class="cal-event-equipo">{{ getEquipoNombre(tarea.equipo_id) }}</span>
              </div>
              <div v-if="celda.tareas.length > 3" class="cal-event-more" @click="vistaActiva = 'tabla'">
                +{{ celda.tareas.length - 3 }} mas
              </div>
            </div>
          </div>
        </div>
      </template>
    </main>

    <!-- ==================== Modal Detalle (Calendario) ==================== -->
    <div v-if="showDetalleModal" class="modal-overlay" @click.self="showDetalleModal = false">
      <div class="modal" style="width: 520px;">
        <h3>Detalle de Tarea Preventiva</h3>
        <div v-if="detalleTarea" class="detalle-content">
          <div class="detalle-row">
            <span class="detalle-label">ID:</span>
            <span>#{{ detalleTarea.id }}</span>
          </div>
          <div class="detalle-row">
            <span class="detalle-label">Titulo:</span>
            <span><strong>{{ detalleTarea.titulo }}</strong></span>
          </div>
          <div class="detalle-row">
            <span class="detalle-label">Equipo:</span>
            <span>{{ getEquipoNombre(detalleTarea.equipo_id) }}</span>
          </div>
          <div class="detalle-row">
            <span class="detalle-label">Frecuencia:</span>
            <span>Cada {{ detalleTarea.frecuencia_dias }} dias</span>
          </div>
          <div class="detalle-row">
            <span class="detalle-label">Proxima Fecha:</span>
            <span>
              <span class="badge" :class="getStatusClass(detalleTarea.proxima_fecha)">
                {{ detalleTarea.proxima_fecha || 'Sin fecha' }} - {{ getStatusLabel(detalleTarea.proxima_fecha) }}
              </span>
            </span>
          </div>
          <div class="detalle-row">
            <span class="detalle-label">Responsable:</span>
            <span>{{ getUsuarioNombre(detalleTarea.responsable_id) }}</span>
          </div>
          <div class="detalle-row" v-if="detalleTarea.descripcion">
            <span class="detalle-label">Descripcion:</span>
            <span>{{ detalleTarea.descripcion }}</span>
          </div>
          <div v-if="detalleTarea.repuestos_detalle && detalleTarea.repuestos_detalle.length" class="detalle-kit">
            <h4>Kit de Repuestos</h4>
            <ul>
              <li v-for="rep in detalleTarea.repuestos_detalle" :key="rep.repuesto_id">
                {{ rep.cantidad_requerida }} x {{ rep.nombre_repuesto || 'Repuesto #' + rep.repuesto_id }}
              </li>
            </ul>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetalleModal = false">Cerrar</button>
          <button class="btn-edit-modal" @click="closeDetalleYEditar">Editar</button>
          <button class="btn-primary" @click="closeDetalleYGenerarOT">Generar OT</button>
        </div>
      </div>
    </div>

    <!-- ==================== Modal Crear/Editar ==================== -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Tarea Preventiva' : 'Nueva Tarea Preventiva' }}</h3>
        <form @submit.prevent="saveTarea">
          
          <div class="form-group">
            <label>Equipo *</label>
            <select v-model="formData.equipo_id" required>
              <option value="" disabled>Seleccione...</option>
              <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Titulo de la Tarea *</label>
            <input v-model="formData.titulo" placeholder="Ej: Calibracion Anual" required>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Frecuencia (dias) <span class="hint">sugerencia</span></label>
              <input v-model="formData.frecuencia_dias" type="number" min="1" required>
            </div>
            <div class="form-group">
              <label>Ultima Fecha Realizada</label>
              <input v-model="formData.ultima_fecha" type="date" @change="sugerirProximaFecha">
            </div>
          </div>

          <!-- v0.9.0: proxima_fecha editable (fecha REAL programada, no auto-calculada) -->
          <div class="form-row">
            <div class="form-group">
              <label>Próxima Fecha Programada <span class="hint">fecha real para el calendario</span></label>
              <input v-model="formData.proxima_fecha" type="date">
              <small class="form-help">Esta es la fecha que aparece en el calendario. La frecuencia es solo una sugerencia.</small>
            </div>
            <div class="form-group">
              <button type="button" class="btn-sugerir" @click="sugerirProximaFecha" title="Calcular sugerencia basada en última fecha + frecuencia">
                📅 Sugerir fecha
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>Responsable</label>
            <select v-model="formData.responsable_id">
              <option :value="null">-- Sin Asignar --</option>
              <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.full_name || u.username }}</option>
            </select>
          </div>

          <div class="form-group kit-section">
            <h4>Kit de Mantenimiento</h4>
            <p class="kit-hint">Repuestos necesarios para ejecutar esta tarea preventiva.</p>
            <div class="repuesto-selector">
              <select v-model="selectedRepuestoId">
                <option :value="null">Seleccionar repuesto...</option>
                <option
                  v-for="rep in listaInventario"
                  :key="rep.id"
                  :value="rep.id"
                >
                  {{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})
                </option>
              </select>
              <input
                v-model.number="selectedCantidad"
                type="number"
                min="1"
                class="cantidad-input"
                placeholder="Cant."
              >
              <button type="button" class="btn-sm" @click="addRepuesto">Agregar</button>
            </div>
            <ul v-if="repuestosSeleccionados.length" class="repuesto-lista">
              <li v-for="(item, idx) in repuestosSeleccionados" :key="item.repuesto_id">
                <span>{{ item.cantidad }} x {{ item.nombre }}</span>
                <button
                  type="button"
                  class="btn-remove-repuesto"
                  title="Quitar"
                  @click="removeRepuesto(idx)"
                >
                  X
                </button>
              </li>
            </ul>
            <p v-else class="kit-empty">No hay repuestos en el kit.</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ==================== Modal Generar OT ==================== -->
    <div v-if="showGenerarOTModal" class="modal-overlay" @click.self="showGenerarOTModal = false">
      <div class="modal" style="width: 480px;">
        <h3>Generar Orden de Trabajo</h3>
        <div class="generar-ot-info">
          <p><strong>Tarea:</strong> {{ generarOTData.titulo }}</p>
          <p><strong>Equipo:</strong> {{ generarOTData.equipo }}</p>
        </div>
        
        <form @submit.prevent="generarOT">
          <div class="form-group">
            <label>Prioridad</label>
            <select v-model="generarOTData.prioridad">
              <option>Urgente</option>
              <option>Alta</option>
              <option>Media</option>
              <option>Baja</option>
            </select>
          </div>

          <div class="form-group">
            <label>Tecnico Asignado</label>
            <select v-model="generarOTData.tecnico_asignado_id">
              <option :value="null">-- Sin Asignar --</option>
              <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.full_name || u.username }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Fecha de Vencimiento</label>
            <input v-model="generarOTData.fecha_vencimiento" type="date">
          </div>

          <div class="generar-ot-hint">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
            <span>Se creara una OT vinculada a esta tarea preventiva. Los repuestos del kit se sugeriran al editar la OT.</span>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showGenerarOTModal = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="generarOTLoading">
              {{ generarOTLoading ? 'Generando...' : 'Generar OT' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Reutilizamos estilos de DashboardView */
.dashboard-container { padding: 0; }
.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid #ddd; font-size: 0.88rem; }
th { background-color: #f8f9fa; font-weight: bold; }
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.75rem 1rem; margin-bottom: 1rem; }
.top-bar h2 { margin: 0; }
.top-bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }

/* Busqueda */
.search-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  min-width: 200px;
  flex: 1 1 180px;
  max-width: 320px;
}
.search-icon {
  position: absolute;
  left: 10px;
  color: #94a3b8;
  pointer-events: none;
  z-index: 1;
}
.search-input {
  width: 100%;
  padding: 0.55rem 0.85rem 0.55rem 2.2rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  box-sizing: border-box;
  background: #fff;
}
.search-input::placeholder { color: #94a3b8; }
.search-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}

/* Barra de filtros */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.filter-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}
.filter-select {
  padding: 0.35rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.82rem;
  background: #fff;
  color: #334155;
  min-width: 120px;
  max-width: 180px;
}
.filter-select:focus {
  outline: none;
  border-color: #3498db;
}
.btn-clear-filters {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.7rem;
  border: 1px solid #fecaca;
  border-radius: 6px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-clear-filters:hover {
  background: #fee2e2;
}
.filter-count {
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

/* Tabla vacia */
.table-empty-cell { text-align: center; color: #64748b; padding: 1.5rem 12px; font-size: 0.95rem; }
.empty-state { text-align: center; padding: 2.5rem 1rem; color: #64748b; font-size: 0.95rem; }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.btn-edit-modal { background-color: #f59e0b; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-weight: bold; }

/* Iconos */
.actions-cell { display: flex; gap: 0.5rem; }
.btn-icon { background: #f0f2f5; border: none; padding: 8px; border-radius: 6px; cursor: pointer; color: #555; }
.btn-icon:hover { background: #dfe2e6; }
.btn-danger-icon:hover { background: #fee2e2; color: #c0392b; }
.btn-generate-icon:hover { background: #dbeafe; color: #2563eb; }

/* Badges de Estado Preventivo */
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
.status-ok { background-color: #d4edda; color: #155724; }
.status-upcoming { background-color: #fff3cd; color: #856404; }
.status-overdue { background-color: #f8d7da; color: #721c24; }
.status-due-today { background-color: #ffeaa7; color: #856404; }
.status-unknown { background-color: #e2e3e5; color: #383d41; }
.status-programada { background-color: #d1ecf1; color: #0c5460; }  /* v0.9.2: verde-azulado para OT activa */

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; max-width: 90%; max-height: 90vh; overflow-y: auto; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

.table-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
  padding: 0.75rem 0;
}
.table-pagination-meta {
  font-size: 0.9rem;
  color: #475569;
}
.btn-pagination {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
}
.btn-pagination:hover:not(:disabled) {
  background-color: #2980b9;
}
.btn-pagination:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.kit-section h4 {
  margin: 0 0 0.35rem 0;
  color: #2c3e50;
  font-size: 1rem;
}
.kit-hint {
  margin: 0 0 0.75rem 0;
  font-size: 0.85rem;
  color: #64748b;
}
.kit-empty {
  margin: 0;
  font-size: 0.85rem;
  color: #94a3b8;
  font-style: italic;
}
.repuesto-selector {
  display: flex;
  gap: 10px;
  align-items: center;
  margin-bottom: 10px;
}
.repuesto-selector select {
  flex: 1;
  min-width: 0;
}
.cantidad-input {
  width: 80px;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
}
.btn-sm {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 0.9rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  white-space: nowrap;
}
.btn-sm:hover {
  background-color: #2980b9;
}
.repuesto-lista {
  list-style: none;
  padding: 0;
  margin: 0;
  background: #f9f9f9;
  border: 1px solid #eee;
  border-radius: 4px;
}
.repuesto-lista li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 10px;
  border-bottom: 1px solid #eee;
  font-size: 0.9rem;
}
.repuesto-lista li:last-child {
  border-bottom: none;
}
.btn-remove-repuesto {
  background: #fee2e2;
  color: #c0392b;
  border: none;
  width: 28px;
  height: 28px;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  line-height: 1;
}
.btn-remove-repuesto:hover {
  background: #fecaca;
}

/* Generar OT */
.generar-ot-info {
  background: #f0f7ff;
  padding: 0.75rem 1rem;
  border-radius: 6px;
  border-left: 4px solid #3b82f6;
  margin-bottom: 1rem;
}
.generar-ot-info p {
  margin: 0.25rem 0;
  font-size: 0.9rem;
  color: #1e3a5f;
}
.generar-ot-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 6px;
  padding: 0.75rem;
  margin-bottom: 0.5rem;
  font-size: 0.82rem;
  color: #78350f;
  line-height: 1.4;
}
.generar-ot-hint svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: #d97706;
}

/* ==================== TOGGLE VISTA ==================== */
.vista-toggle {
  display: flex;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.vista-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 1rem;
  border: none;
  background: white;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  color: #64748b;
  transition: all 0.2s;
}
.vista-btn:first-child {
  border-right: 1px solid #e2e8f0;
}
.vista-btn:hover {
  background: #f1f5f9;
  color: #334155;
}
.vista-btn--active {
  background: #3b82f6;
  color: white;
}
.vista-btn--active:hover {
  background: #2563eb;
  color: white;
}

/* ==================== CALENDARIO ==================== */
.cal-legend {
  display: flex;
  gap: 1.25rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  flex-wrap: wrap;
}
.cal-legend-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.82rem;
  color: #475569;
  font-weight: 500;
}
.cal-legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

/* Resumen rapido */
.cal-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
@media (max-width: 700px) {
  .cal-summary { grid-template-columns: repeat(2, 1fr); }
}
.cal-summary-card {
  background: white;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  text-align: center;
  border: 1px solid #e2e8f0;
}
.cal-summary-num {
  display: block;
  font-size: 1.6rem;
  font-weight: 800;
  line-height: 1.2;
}
.cal-summary-label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.cal-summary--total .cal-summary-num { color: #3b82f6; }
.cal-summary--overdue .cal-summary-num { color: #ef4444; }
.cal-summary--today .cal-summary-num { color: #f97316; }
.cal-summary--upcoming .cal-summary-num { color: #eab308; }

/* Navegacion */
.cal-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  background: white;
  padding: 0.75rem 1rem;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.cal-nav-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  color: #334155;
  transition: all 0.2s;
}
.cal-nav-btn:hover {
  background: #e2e8f0;
}
.cal-nav-center {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.cal-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  color: #1e293b;
}
.cal-hoy-btn {
  background: #3b82f6;
  color: white;
  border: none;
  padding: 0.3rem 0.75rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.78rem;
  font-weight: 600;
}
.cal-hoy-btn:hover {
  background: #2563eb;
}

/* Grilla del calendario */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  background: white;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  overflow: hidden;
  box-shadow: 0 1px 6px rgba(15,23,42,0.07);
}
.cal-header {
  padding: 0.6rem 0.5rem;
  text-align: center;
  font-weight: 700;
  font-size: 0.8rem;
  color: #64748b;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.cal-cell {
  min-height: 90px;
  border-right: 1px solid #f1f5f9;
  border-bottom: 1px solid #f1f5f9;
  padding: 0.35rem;
  position: relative;
  transition: background 0.15s;
}
.cal-cell:nth-child(7n) {
  border-right: none;
}
.cal-cell--other {
  background: #fafbfc;
}
.cal-cell--other .cal-day-num {
  color: #c0c7d0;
}
.cal-cell--today {
  background: #eff6ff;
}
.cal-cell--today .cal-day-num {
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
}
.cal-cell:hover {
  background: #f8fafc;
}
.cal-cell--today:hover {
  background: #dbeafe;
}

.cal-cell-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.25rem;
}
.cal-day-num {
  font-size: 0.82rem;
  font-weight: 600;
  color: #334155;
}
.cal-task-count {
  font-size: 0.65rem;
  font-weight: 700;
  background: #3b82f6;
  color: white;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.cal-cell-events {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.cal-event {
  padding: 0.2rem 0.4rem;
  border-left: 3px solid;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s;
  overflow: hidden;
}
.cal-event:hover {
  filter: brightness(0.95);
  transform: translateX(1px);
}
.cal-event-title {
  display: block;
  font-size: 0.72rem;
  font-weight: 600;
  color: #1e293b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cal-event-equipo {
  display: block;
  font-size: 0.65rem;
  color: #64748b;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cal-event-more {
  font-size: 0.68rem;
  color: #3b82f6;
  font-weight: 600;
  cursor: pointer;
  padding: 0.1rem 0.4rem;
}
.cal-event-more:hover {
  text-decoration: underline;
}

/* Detalle modal */
.detalle-content {
  margin: 1rem 0;
}
.detalle-row {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid #f1f5f9;
  font-size: 0.9rem;
  color: #334155;
}
.detalle-label {
  font-weight: 700;
  color: #64748b;
  min-width: 120px;
  flex-shrink: 0;
}
.detalle-kit {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 6px;
  border: 1px solid #e2e8f0;
}
.detalle-kit h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.88rem;
  color: #1e293b;
}
.detalle-kit ul {
  margin: 0;
  padding-left: 1.2rem;
  font-size: 0.85rem;
  color: #475569;
}
.detalle-kit li {
  padding: 0.15rem 0;
}

/* Responsive calendario */
@media (max-width: 900px) {
  .cal-cell {
    min-height: 70px;
    padding: 0.2rem;
  }
  .cal-event-title {
    font-size: 0.65rem;
  }
  .cal-event-equipo {
    display: none;
  }
}
@media (max-width: 600px) {
  .cal-grid {
    font-size: 0.8rem;
  }
  .cal-cell {
    min-height: 55px;
  }
  .cal-event {
    padding: 0.1rem 0.2rem;
  }
  .cal-event-equipo {
    display: none;
  }
  .top-bar {
    flex-direction: column;
    gap: 0.75rem;
    align-items: flex-start;
  }
  .top-bar-actions {
    width: 100%;
    justify-content: space-between;
  }
}

/* v0.9.0: Estilos para proxima_fecha editable */
.hint {
  font-size: 0.72rem;
  color: #94a3b8;
  font-weight: 400;
  font-style: italic;
}
.form-help {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.25rem;
}
.btn-sugerir {
  background: #eff6ff;
  color: #2563eb;
  border: 1px solid #bfdbfe;
  padding: 0.5rem 0.85rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.82rem;
  white-space: nowrap;
  transition: all 0.2s;
  margin-top: 1.5rem;
}
.btn-sugerir:hover {
  background: #dbeafe;
  border-color: #93c5fd;
}
</style>
