<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'

const router = useRouter()

// --- Variables ---
const tareas = ref([])
const equipos = ref([])
const usuarios = ref([])
const loading = ref(true)

const currentPage = ref(1)
const pageSize = ref(10)

// --- Filtros de busqueda ---
const searchQuery = ref('')
const filterEquipo = ref('')
const filterUbicacion = ref('')
const filterUsuario = ref('')
const filterEstado = ref('')

// --- Modal ---

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
    const [resTareas, resEquipos, resUsers] = await Promise.all([
      apiClient.get('/preventivo/'),
      apiClient.get('/equipos/'),
      apiClient.get('/users/')
    ])
    tareas.value = resTareas.data
    equipos.value = resEquipos.data
    usuarios.value = resUsers.data
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

// --- Tareas filtradas ---
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

  // Filtro estado
  if (filterEstado.value) {
    result = result.filter(t => getStatusClass(t.proxima_fecha) === filterEstado.value)
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
  // v0.9.23: Título siempre es "Preventivo" (bloqueado), frecuencia default 90
  const ahora = new Date()
  const fechaSistema = `${ahora.getFullYear()}-${String(ahora.getMonth() + 1).padStart(2, '0')}-${String(ahora.getDate()).padStart(2, '0')}`
  formData.value = {
    equipo_id: '',
    responsable_id: null,
    titulo: 'Preventivo',
    frecuencia_dias: 90,
    ultima_fecha: fechaSistema,  // fecha del sistema por defecto (date)
    proxima_fecha: ''  // se calculará automáticamente
  }
  // v0.9.23: calcular próxima fecha automáticamente: ultima_fecha + frecuencia
  calcularProximaFecha()
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
    formData.value = { ...fullTarea, titulo: 'Preventivo' }  // v0.9.23: título bloqueado
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
    titulo: 'Preventivo',  // v0.9.23: siempre "Preventivo", no se envía desde formulario
    descripcion: formData.value.descripcion || null,
    frecuencia_dias: Number(formData.value.frecuencia_dias),
    ultima_fecha: formData.value.ultima_fecha ? formData.value.ultima_fecha.substring(0, 10) : null,
    proxima_fecha: formData.value.proxima_fecha || null,
    repuestos: repuestosSeleccionados.value.map((r) => ({
      repuesto_id: r.repuesto_id,
      cantidad_requerida: Number(r.cantidad)
    }))
  }
  if (isEditing.value) {
    return {
      titulo: 'Preventivo',  // v0.9.23: siempre "Preventivo"
      descripcion: payload.descripcion,
      frecuencia_dias: payload.frecuencia_dias,
      responsable_id: payload.responsable_id,
      ultima_fecha: payload.ultima_fecha,
      proxima_fecha: payload.proxima_fecha,
      repuestos: payload.repuestos
    }
  }
  return payload
}

// v0.9.23: Eliminado sugerirProximaFecha. Ahora se usa watch para calcular automáticamente.
// La lógica es: si cambia ultima_fecha o frecuencia_dias → recalcular proxima_fecha
// Si cambia proxima_fecha manualmente → recalcular frecuencia_dias
let recalculandoDesdeFrecuencia = false
let recalculandoDesdeProxima = false

const calcularProximaFecha = () => {
  if (formData.value.ultima_fecha && formData.value.frecuencia_dias) {
    recalculandoDesdeFrecuencia = true
    const ultima = new Date(formData.value.ultima_fecha)
    const proxima = new Date(ultima)
    proxima.setDate(proxima.getDate() + Number(formData.value.frecuencia_dias))
    formData.value.proxima_fecha = proxima.toISOString().substring(0, 10)
    setTimeout(() => { recalculandoDesdeFrecuencia = false }, 0)
  }
}

const calcularFrecuenciaDesdeProxima = () => {
  if (formData.value.ultima_fecha && formData.value.proxima_fecha) {
    recalculandoDesdeProxima = true
    const ultima = new Date(formData.value.ultima_fecha)
    const proxima = new Date(formData.value.proxima_fecha)
    const diffDias = Math.round((proxima - ultima) / (1000 * 60 * 60 * 24))
    if (diffDias > 0) {
      formData.value.frecuencia_dias = diffDias
    }
    setTimeout(() => { recalculandoDesdeProxima = false }, 0)
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
    numero_serie: getEquipoNumeroSerie(tarea.equipo_id),
    prioridad: 'Media',
    tecnico_asignado_id: tarea.responsable_id || null,
    // v0.9.23: usar fecha_creacion (proxima_fecha) en vez de fecha_vencimiento
    fecha_creacion: tarea.proxima_fecha ? toDatetimeLocalMP(tarea.proxima_fecha) : null
  }
  showGenerarOTModal.value = true
}

const generarOT = async () => {
  generarOTLoading.value = true
  try {
    const payload = {
      prioridad: generarOTData.value.prioridad,
      tecnico_asignado_id: generarOTData.value.tecnico_asignado_id || null,
      fecha_creacion: generarOTData.value.fecha_creacion || null
    }
    const res = await apiClient.post(`/preventivo/${generarOTData.value.tarea_id}/generar-ot`, payload)
    const otId = res.data.id
    showGenerarOTModal.value = false
    
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

const getEquipoNumeroSerie = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.numero_serie || '') : ''
}

const getEquipoModelo = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.modelo || '') : ''
}

// Formato equipo: nombre_corto - modelo - numero_serie
const getEquipoFullLabel = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  if (!eq) return 'N/A'
  const parts = [eq.nombre_corto || eq.modelo]
  if (eq.modelo) parts.push(eq.modelo)
  if (eq.numero_serie) parts.push(eq.numero_serie)
  return parts.join(' - ')
}

// Helper para calcular estado visual (Vencido, Proximo, OK)
const getStatusClass = (proximaFecha) => {
  if (!proximaFecha) return 'status-unknown'
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)
  
  if (dueDate < today) return 'status-overdue'
  if (dueDate === today) return 'status-due-today'
  
  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return 'status-upcoming'
  
  return 'status-ok'
}

const getStatusLabel = (proximaFecha) => {
  if (!proximaFecha) return 'Sin fecha'
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)
  
  if (dueDate < today) return 'Vencida'
  if (dueDate === today) return 'Hoy'
  
  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return 'Proxima'
  
  return 'OK'
}

// --- Paginacion tabla (usando filteredTareas) ---

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

// --- Paginacion tabla ---

// v0.9.23: Helper para convertir fecha string a datetime-local
const toDatetimeLocalMP = (fechaStr) => {
  if (!fechaStr) return ''
  const d = new Date(fechaStr)
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${day}T${h}:${min}`
}

// v0.9.23: Watchers para enlazar frecuencia_dias <-> proxima_fecha
watch(() => formData.value.ultima_fecha, () => {
  if (!recalculandoDesdeProxima) calcularProximaFecha()
})
watch(() => formData.value.frecuencia_dias, () => {
  if (!recalculandoDesdeProxima) calcularProximaFecha()
})
watch(() => formData.value.proxima_fecha, () => {
  if (!recalculandoDesdeFrecuencia && formData.value.ultima_fecha) {
    calcularFrecuenciaDesdeProxima()
  }
})

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="dashboard-container">

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
            <option value="status-overdue">Vencida</option>
            <option value="status-due-today">Hoy</option>
            <option value="status-upcoming">Proxima</option>
            <option value="status-ok">OK</option>
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
      <template v-if="!loading">
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
                <span class="badge" :class="getStatusClass(tarea.proxima_fecha)">
                  {{ getStatusLabel(tarea.proxima_fecha) }}
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

      <div v-if="!loading && !filteredTareas.length && tieneFiltrosActivos" class="empty-state">
        No hay tareas que coincidan con los filtros seleccionados.
      </div>
    </main>

    <!-- ==================== Modal Crear/Editar ==================== -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Tarea Preventiva' : 'Nueva Tarea Preventiva' }}</h3>
        <form @submit.prevent="saveTarea">
          
          <div class="form-group">
            <label>Equipo *</label>
            <select v-model="formData.equipo_id" required>
              <option value="" disabled>Seleccione...</option>
              <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ getEquipoFullLabel(eq.id) }}</option>
            </select>
          </div>

          <!-- Fila: Título de la Tarea + Frecuencia (días) -->
          <div class="form-row">
            <div class="form-group">
              <label>Titulo de la Tarea</label>
              <input value="Preventivo" disabled style="background: #f1f5f9; color: #64748b; cursor: not-allowed;">
              <small class="form-help">Mantenimiento preventivo.</small>
            </div>
            <div class="form-group">
              <label>Frecuencia (dias)</label>
              <input v-model.number="formData.frecuencia_dias" type="number" min="1" required>
            </div>
          </div>

          <!-- Fila: Última Fecha Realizada + Próxima Fecha Programada -->
          <div class="form-row">
            <div class="form-group">
              <label>Ultima Fecha Realizada</label>
              <input v-model="formData.ultima_fecha" type="date">
            </div>
            <div class="form-group">
              <label>Proxima Fecha Programada</label>
              <input v-model="formData.proxima_fecha" type="date">
              <small class="form-help">Ultima Fecha + Frecuencia (dias).</small>
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
              <button type="button" class="btn-add-repuesto" @click="addRepuesto">Agregar</button>
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
          <p v-if="generarOTData.numero_serie"><strong>N. Serie:</strong> {{ generarOTData.numero_serie }}</p>
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
            <label>Fecha y Hora Programada</label>
            <input v-model="generarOTData.fecha_creacion" type="datetime-local">
          </div>

          <div class="generar-ot-hint">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM8 4a.905.905 0 0 0-.9.995l.35 3.507a.552.552 0 0 0 1.1 0l.35-3.507A.905.905 0 0 0 8 4zm.002 6a1 1 0 1 0 0 2 1 1 0 0 0 0-2z"/>
            </svg>
            <span>Se creara una OT tipo "Preventivo" vinculada a esta tarea. El Responsable pasa como Tecnico Asignado.</span>
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

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; max-width: 90%; max-height: 90vh; overflow-y: auto; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 0.9rem; }
.form-row { display: flex; gap: 0.75rem; }
.form-row .form-group { flex: 1; min-width: 0; }
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
  width: auto !important;
}
.cantidad-input {
  width: 85px !important;
  flex: none !important;
  padding: 0.6rem 0.3rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  text-align: center;
}
.btn-add-repuesto {
  background-color: #d97706;
  color: white;
  border: none;
  padding: 0.6rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 600;
  white-space: nowrap;
  width: 85px;
  flex: none;
}
.btn-add-repuesto:hover {
  background-color: #b45309;
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
  background: #fef3c7;
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
  font-size: 0.88rem;
  color: #1e3a5f;
}

/* Modal Generar OT: igualar anchos de inputs */
.generar-ot-info + form .form-group input,
.generar-ot-info + form .form-group select {
  width: 100%;
  box-sizing: border-box;
  font-size: 0.9rem;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
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

/* Responsive */
@media (max-width: 600px) {
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
</style>
