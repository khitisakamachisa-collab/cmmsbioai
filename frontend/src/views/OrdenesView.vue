<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import DocumentosAdjuntos from '../components/DocumentosAdjuntos.vue'

const router = useRouter()

// --- Variables Generales ---
const ordenes = ref([])
const equipos = ref([])
const estadosOT = ref([]) 
const tecnicos = ref([])
const loading = ref(true)

const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

// v0.9.20: filtros adicionales
const filterTipo = ref('')
const filterPrioridad = ref('')
const filterEstado = ref('')
const sortOrder = ref('desc')  // 'desc' = más nuevas primero, 'asc' = más viejas primero

// Tipos de OT para el menú de selección de Título
const tiposOT = [
  'Correctivo',
  'Preventivo',
  'Predictivo',
  'Calibración',
  'Inspección',
  'Actualización',
  'Diagnóstico',
  'Prueba/Validación',
  'Limpieza',
  'Cambio de repuesto',
  'Grasa/Lubricación',
  'Instalación',
  'Retiro/Dado de baja',
  'Transferencia',
  'Auditoría',
  'Otro'
]

const filteredOrdenes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let result = ordenes.value

  // Búsqueda libre
  if (q) {
    result = result.filter((ot) => {
      const titulo = String(ot.titulo ?? '').toLowerCase()
      const falla = String(ot.descripcion_falla ?? '').toLowerCase()
      const id = String(ot.id ?? '')
      const equipo = getEquipoNombre(ot.equipo_id).toLowerCase()
      return titulo.includes(q) || falla.includes(q) || id.includes(q) || equipo.includes(q)
    })
  }

  // v0.9.20: filtros por Tipo, Prioridad, Estado
  if (filterTipo.value) {
    result = result.filter(ot => ot.titulo === filterTipo.value)
  }
  if (filterPrioridad.value) {
    result = result.filter(ot => ot.prioridad === filterPrioridad.value)
  }
  if (filterEstado.value) {
    result = result.filter(ot => String(ot.estado_id) === String(filterEstado.value))
  }

  // v0.9.20: ordenamiento por ID (asc = viejas primero, desc = nuevas primero)
  result = [...result].sort((a, b) => {
    if (sortOrder.value === 'desc') return b.id - a.id
    return a.id - b.id
  })

  return result
})

const paginatedOrdenes = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredOrdenes.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredOrdenes.value.length / pageSize.value))
)

watch(
  () => filteredOrdenes.value.length,
  (len) => {
    const tp = Math.max(1, Math.ceil(len / pageSize.value))
    if (currentPage.value > tp) currentPage.value = tp
  }
)

watch([searchQuery, filterTipo, filterPrioridad, filterEstado, sortOrder], () => {
  currentPage.value = 1
})

const irPaginaAnterior = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}

const irPaginaSiguiente = () => {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

// --- Control de Modales ---
const showModal = ref(false) // Modal Crear
const showEditModal = ref(false) // Modal Editar (Lápiz)
const showViewModal = ref(false) // Modal Ver (Ojo)
const selectedOT = ref({}) // OT seleccionada

// --- Variables Modal Documentos ---
const showDocsModal = ref(false)
const docsOT = ref({})

// --- Variables para Repuestos ---
const listaRepuestos = ref([])
const selectedRepuestoId = ref(null)
const selectedCantidad = ref(1)
const repuestosSeleccionados = ref([])

// v0.9.21: Variables para Costos Adicionales (RF11 - OtCostoAdicional)
const tiposCosto = [
  'Transporte', 'Servicio Externo', 'Repuesto No Inventariado',
  'Herramienta Renta', 'Honorarios / Mano de Obra',
  'Insumos / Materiales', 'Viáticos', 'Otro'
]
const costosAdicionales = ref([])        // lista de costos (para modal crear)
const editCostosAdicionales = ref([])    // lista de costos (para modal editar)
const detalleCostos = ref([])            // lista de costos (para modal ver)
const costoForm = ref({ tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null })
const editCostoForm = ref({ tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null })

const totalCostos = computed(() => costosAdicionales.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))
const totalEditCostos = computed(() => editCostosAdicionales.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))
const totalDetalleCostos = computed(() => detalleCostos.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))

const addCostoToOT = () => {
  if (!costoForm.value.descripcion_costo || !costoForm.value.monto_costo) {
    alert('Complete descripción y monto del costo')
    return
  }
  costosAdicionales.value.push({ ...costoForm.value, monto_costo: Number(costoForm.value.monto_costo) })
  costoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
}

const removeCostoFromOT = (idx) => {
  costosAdicionales.value.splice(idx, 1)
}

const addEditCostoToOT = () => {
  if (!editCostoForm.value.descripcion_costo || !editCostoForm.value.monto_costo) {
    alert('Complete descripción y monto del costo')
    return
  }
  editCostosAdicionales.value.push({ ...editCostoForm.value, monto_costo: Number(editCostoForm.value.monto_costo) })
  editCostoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
}

const removeEditCostoFromOT = (idx) => {
  editCostosAdicionales.value.splice(idx, 1)
}

// v0.9.21: Sincronizar costos de una OT con el backend
// - costosNuevos: los que están en el formulario pero no tienen id (crear)
// - costosExistentes: los que tienen id (mantener)
// - costosEliminar: los que están en BD pero no en el formulario (eliminar)
async function sincronizarCostosOT(otId, costosFormulario) {
  // costosFormulario: array de {id?, tipo_costo, descripcion_costo, monto_costo}
  // 1. Obtener costos actuales de la OT desde el backend
  const res = await apiClient.get(`/costos/?orden_trabajo_id=${otId}`)
  const costosBD = res.data
  const idsFormulario = costosFormulario.filter(c => c.id).map(c => c.id)

  // 2. Eliminar los que están en BD pero no en el formulario
  for (const cBD of costosBD) {
    if (!idsFormulario.includes(cBD.id)) {
      await apiClient.delete(`/costos/${cBD.id}`)
    }
  }

  // 3. Crear los nuevos (sin id) y actualizar los existentes (con id)
  for (const c of costosFormulario) {
    if (c.id) {
      // Actualizar existente
      await apiClient.put(`/costos/${c.id}`, {
        tipo_costo: c.tipo_costo,
        descripcion_costo: c.descripcion_costo,
        monto_costo: c.monto_costo
      })
    } else {
      // Crear nuevo
      await apiClient.post('/costos/', {
        orden_trabajo_id: otId,
        tipo_costo: c.tipo_costo,
        descripcion_costo: c.descripcion_costo,
        monto_costo: c.monto_costo
      })
    }
  }
}

// v0.9.23: Helpers datetime-local (DEBEN estar antes de formData por hoisting de const)
const toLocalDatetimeString = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d}T${h}:${min}`
}

const toDatetimeLocal = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return toLocalDatetimeString(d)
}

// Formulario Crear
const formData = ref({
  equipo_id: '',
  estado_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: null,
  unidad_tiempo: 'horas',
  tiempo_real_invertido: null,
  acciones_realizadas: '',
  fecha_creacion: toLocalDatetimeString(new Date())  // v0.9.23: datetime-local default now
})

// Formulario Editar
const editFormData = ref({
  equipo_id: '',
  estado_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: null,
  unidad_tiempo: 'horas',
  tiempo_real_invertido: null,
  acciones_realizadas: '',
  fecha_creacion: ''
})

// --- Funciones de Datos ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resOrdenes, resEquipos, resEstados, resUsers] = await Promise.all([
      apiClient.get('/ordenes/'),
      apiClient.get('/equipos/'),
      apiClient.get('/ordenes/estados/'),
      apiClient.get('/users/')
    ])
    ordenes.value = resOrdenes.data
    equipos.value = resEquipos.data
    estadosOT.value = resEstados.data
    tecnicos.value = resUsers.data
  } catch (error) {
    console.error('Error cargando datos', error)
  } finally {
    loading.value = false
  }
}

// v0.9.18: Abrir modal Crear — cargar repuestos y resetear estado
const openCreateModal = async () => {
  formData.value = { equipo_id: '', estado_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: null, unidad_tiempo: 'horas', tiempo_real_invertido: null, acciones_realizadas: '', fecha_creacion: toLocalDatetimeString(new Date()) }
  repuestosSeleccionados.value = []
  selectedRepuestoId.value = null
  selectedCantidad.value = 1
  // v0.9.21: resetear costos
  costosAdicionales.value = []
  costoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
  // Cargar repuestos para el selector
  try {
    const resRep = await apiClient.get('/repuestos/')
    listaRepuestos.value = resRep.data
  } catch (e) {
    console.error('Error cargando repuestos:', e)
  }
  showModal.value = true
}

const saveOrden = async () => {
  try {
    const payload = { ...formData.value, repuestos_utilizados: repuestosSeleccionados.value }
    if (payload.tiempo_real_invertido === "" || payload.tiempo_real_invertido === null) {
      payload.tiempo_real_invertido = null
    } else {
      payload.tiempo_real_invertido = parseFloat(payload.tiempo_real_invertido)
    }
    const res = await apiClient.post('/ordenes/', payload)
    const nuevaOTId = res.data.id
    // v0.9.21: guardar costos adicionales
    if (costosAdicionales.value.length > 0) {
      await sincronizarCostosOT(nuevaOTId, costosAdicionales.value)
    }
    alert('Orden creada')
    showModal.value = false
    formData.value = { equipo_id: '', estado_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: null, unidad_tiempo: 'horas', tiempo_real_invertido: null, acciones_realizadas: '', fecha_creacion: toLocalDatetimeString(new Date()) }
    repuestosSeleccionados.value = []
    costosAdicionales.value = []
    fetchData() 
  } catch (error) {
    alert('Error al crear OT')
  }
}

// --- NUEVO: Abrir Modal Ver (Solo Lectura) ---
const openViewModal = async (ot) => {
  // Llamamos al detalle para tener datos frescos
  try {
    const res = await apiClient.get(`/ordenes/${ot.id}`)
    selectedOT.value = res.data
    // v0.9.20: cargar lista de repuestos para resolver nombres en el modal Ver
    if (!listaRepuestos.value.length) {
      try {
        const resRep = await apiClient.get('/repuestos/')
        listaRepuestos.value = resRep.data
      } catch (e) {
        console.warn('No se pudieron cargar repuestos para el detalle', e)
      }
    }
    // v0.9.21: cargar costos adicionales de la OT
    try {
      const resCostos = await apiClient.get(`/costos/?orden_trabajo_id=${ot.id}`)
      detalleCostos.value = resCostos.data
    } catch (e) {
      console.warn('No se pudieron cargar costos', e)
      detalleCostos.value = []
    }
    showViewModal.value = true
  } catch (e) {
    alert("Error al cargar detalles")
  }
}

// v0.9.20: helper para obtener el nombre de un repuesto por su ID
const getRepuestoNombre = (id) => {
  if (!id) return ''
  const rep = listaRepuestos.value.find(r => r.id === id)
  return rep ? rep.nombre_repuesto : `Repuesto #${id}`
}

// --- NUEVO: Abrir Modal Editar (Lápiz) ---
const openEditModal = async (ot) => {
  try {
    // 1. Obtener datos frescos de la orden específica
    const res = await apiClient.get(`/ordenes/${ot.id}`)
    const fullOt = res.data
    
    selectedOT.value = fullOt
    
    // 2. Cargar repuestos para el selector
    const resRep = await apiClient.get('/repuestos/')
    listaRepuestos.value = resRep.data
    
    // 3. Llenar formulario de edición
    editFormData.value = {
      equipo_id: fullOt.equipo_id,
      estado_id: fullOt.estado_id,
      prioridad: fullOt.prioridad || 'Media',
      titulo: fullOt.titulo || '',
      descripcion_falla: fullOt.descripcion_falla || '',
      tecnico_asignado_id: fullOt.tecnico_asignado_id || null,
      unidad_tiempo: fullOt.unidad_tiempo || 'horas',
      tiempo_real_invertido: fullOt.tiempo_real_invertido || null,
      acciones_realizadas: fullOt.acciones_realizadas || '',
      fecha_creacion: toDatetimeLocal(fullOt.fecha_creacion)
    }

    // v0.9.21: cargar costos adicionales existentes
    try {
      const resCostos = await apiClient.get(`/costos/?orden_trabajo_id=${ot.id}`)
      editCostosAdicionales.value = resCostos.data.map(c => ({
        id: c.id,
        tipo_costo: c.tipo_costo,
        descripcion_costo: c.descripcion_costo,
        monto_costo: c.monto_costo
      }))
    } catch (e) {
      editCostosAdicionales.value = []
    }
    editCostoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
    
    // 4. Pre-llenar repuestos existentes de la OT
    repuestosSeleccionados.value = []
    if (fullOt.repuestos_usados && fullOt.repuestos_usados.length > 0) {
      repuestosSeleccionados.value = fullOt.repuestos_usados.map(r => {
        const repInfo = listaRepuestos.value.find(rp => rp.id === r.repuesto_id)
        return {
          repuesto_id: r.repuesto_id,
          nombre: repInfo ? repInfo.nombre_repuesto : `Repuesto #${r.repuesto_id}`,
          cantidad: r.cantidad_utilizada
        }
      })
    }
    
    // 5. Si la OT viene de preventivo y no tiene repuestos, sugerir los del kit
    if (fullOt.orden_preventiva_id && repuestosSeleccionados.value.length === 0) {
      try {
        const resTarea = await apiClient.get(`/preventivo/${fullOt.orden_preventiva_id}`)
        const kitRepuestos = resTarea.data.repuestos_detalle || []
        if (kitRepuestos.length > 0) {
          repuestosSeleccionados.value = kitRepuestos.map(r => {
            const repInfo = listaRepuestos.value.find(rp => rp.id === r.repuesto_id)
            return {
              repuesto_id: r.repuesto_id,
              nombre: repInfo ? repInfo.nombre_repuesto : `Repuesto #${r.repuesto_id}`,
              cantidad: r.cantidad_requerida
            }
          })
        }
      } catch (e) {
        console.warn('No se pudieron cargar repuestos del kit preventivo', e)
      }
    }
    
    showEditModal.value = true
  } catch (e) {
    console.error(e)
    alert("Error al cargar orden para editar")
  }
}

const addRepuestoToOT = () => {
  if (!selectedRepuestoId.value || selectedCantidad.value < 1) return
  const repInfo = listaRepuestos.value.find(r => r.id === selectedRepuestoId.value)
  if (!repInfo) return
  if (selectedCantidad.value > repInfo.cantidad_disponible) {
    alert("No hay suficiente stock")
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

const updateOrden = async () => {
  try {
    const payload = { 
      ...editFormData.value,
      repuestos_utilizados: repuestosSeleccionados.value
    };
    
    if (payload.tiempo_real_invertido === "" || payload.tiempo_real_invertido === null) {
      payload.tiempo_real_invertido = null;
    } else {
      payload.tiempo_real_invertido = parseFloat(payload.tiempo_real_invertido);
    }

    await apiClient.put(`/ordenes/${selectedOT.value.id}`, payload)
    // v0.9.21: sincronizar costos adicionales
    await sincronizarCostosOT(selectedOT.value.id, editCostosAdicionales.value)
    alert('Orden actualizada')
    showEditModal.value = false
    fetchData() 
  } catch (error) {
    console.error(error)
    alert('Error al actualizar')
  }
}

const deleteOrden = async (id) => {
  if (confirm("¿Eliminar esta orden?")) {
    try {
      await apiClient.delete(`/ordenes/${id}`)
      alert('Orden eliminada')
      fetchData()
    } catch (error) {
      alert('Error al eliminar')
    }
  }
}

// --- Helpers ---
const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? `${eq.nombre_corto || eq.modelo}` : `ID: ${id}`
}

const getTecnicoNombre = (id) => {
  if (!id) return 'Sin Asignar'
  const t = tecnicos.value.find(u => u.id === id)
  return t ? (t.full_name || t.username) : 'Desconocido'
}

const prioridadClass = (prio) => {
  if (prio === 'Urgente') return 'urgente'
  if (prio === 'Alta') return 'alta'
  return 'media'
}

// Helper para obtener color del estado
const getEstadoColor = (id) => {
  const state = estadosOT.value.find(e => e.id === id)
  return state && state.color ? state.color : '#95a5a6'
}

// v0.9.23: Icono de origen (opción B: icono en título)
const getOrigenIcon = (ot) => {
  if (ot.orden_preventiva_id) return '🛡️'
  return ''
}
const getOrigenTitle = (ot) => {
  if (ot.orden_preventiva_id) return `Preventivo #${ot.orden_preventiva_id}`
  return 'Correctivo manual'
}

// v0.9.23: Formatear fecha y hora de creación para la tabla
const formatFechaHora = (ot) => {
  if (!ot.fecha_creacion) return 'N/A'
  const d = new Date(ot.fecha_creacion)
  const fecha = d.toLocaleDateString('es-BO')
  const hora = d.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' })
  return `${fecha} ${hora}`
}

// --- Función para abrir Modal Documentos ---
const openDocsModal = (ot) => {
  docsOT.value = ot
  showDocsModal.value = true
}

onMounted(() => {
  fetchData()
})
</script>

<template>
  <div class="dashboard-container">

    <main class="content">
      <div class="top-bar">
        <h2>Listado de Órdenes de Trabajo</h2>
        <div class="top-bar-actions">
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input v-model="searchQuery" type="search" class="search-input" placeholder="Titulo, equipo, ID..." autocomplete="off">
          </div>
          <button class="btn-primary btn-icon-only" @click="openCreateModal" title="Nueva Orden">+</button>
        </div>
      </div>

      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Tipo:</label>
          <select v-model="filterTipo" class="filter-select"><option value="">Todos</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Prioridad:</label>
          <select v-model="filterPrioridad" class="filter-select"><option value="">Todas</option><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Estado:</label>
          <select v-model="filterEstado" class="filter-select"><option value="">Todos</option><option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option></select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Orden:</label>
          <select v-model="sortOrder" class="filter-select"><option value="desc">↓ Nuevas primero</option><option value="asc">↑ Viejas primero</option></select>
        </div>
        <button v-if="filterTipo || filterPrioridad || filterEstado" class="btn-clear-filters" @click="filterTipo = ''; filterPrioridad = ''; filterEstado = ''">Limpiar filtros</button>
      </div>

      <div v-if="loading">Cargando...</div>

      <table v-if="!loading && ordenes.length">
        <thead><tr><th>ID</th><th>Equipo</th><th>Título</th><th>Prioridad</th><th>Estado</th><th>Fecha / Hora</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr v-for="ot in paginatedOrdenes" :key="ot.id">
            <td>#{{ ot.id }}</td>
            <td>{{ getEquipoNombre(ot.equipo_id) }}</td>
            <td><strong>{{ getOrigenIcon(ot) }} {{ ot.titulo }}</strong><br><small>{{ ot.descripcion_falla.substring(0, 30) }}...</small></td>
            <td><span class="badge" :class="prioridadClass(ot.prioridad)">{{ ot.prioridad }}</span></td>
            <td><span class="badge" :style="{ backgroundColor: getEstadoColor(ot.estado_id) }">{{ estadosOT.find(e => e.id === ot.estado_id)?.nombre_estado || 'N/A' }}</span></td>
            <td><small>{{ formatFechaHora(ot) }}</small></td>
            <td class="actions-cell">
              <button class="btn-icon btn-view" title="Ver Detalles" @click="openViewModal(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/></svg></button>
              <button class="btn-icon btn-edit" title="Editar" @click="openEditModal(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/></svg></button>
              <button class="btn-icon btn-delete" title="Eliminar" @click="deleteOrden(ot.id)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg></button>
              <button class="btn-icon btn-doc" title="Documentos Adjuntos" @click="openDocsModal(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1z"/></svg></button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && ordenes.length" class="table-pagination" role="navigation" aria-label="Paginación del listado de órdenes">
        <button type="button" class="btn-pagination" :disabled="currentPage <= 1" @click="irPaginaAnterior">Anterior</button>
        <span class="table-pagination-meta">Página {{ currentPage }} de {{ totalPages }}</span>
        <button type="button" class="btn-pagination" :disabled="currentPage >= totalPages" @click="irPaginaSiguiente">Siguiente</button>
      </div>
    </main>

    <!-- ==================== Modal Crear OT ==================== -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal modal-wide modal-xl">
        <h3>Nueva Orden de Trabajo</h3>
        <form @submit.prevent="saveOrden">
          <div class="detail-tables">
            <div class="detail-table-block">
              <h4>Asignación</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Equipo Afectado *</td><td><select v-model="formData.equipo_id" class="detail-field" required><option value="" disabled>Seleccione...</option><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}{{ eq.numero_serie ? ' — ' + eq.numero_serie : '' }}</option></select></td></tr>
                <tr><td class="detail-label">Estado *</td><td><select v-model="formData.estado_id" class="detail-field" required><option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option></select></td></tr>
                <tr><td class="detail-label">Prioridad</td><td><select v-model="formData.prioridad" class="detail-field"><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select></td></tr>
                <tr><td class="detail-label">Técnico Asignado</td><td><select v-model="formData.tecnico_asignado_id" class="detail-field"><option :value="null">-- Sin Asignar --</option><option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">{{ tec.full_name || tec.username }}</option></select></td></tr>
              </tbody></table>
            </div>
            <div class="detail-table-block">
              <h4>Tipo y Tiempos</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Título / Tipo *</td><td><select v-model="formData.titulo" class="detail-field" required><option value="" disabled>Seleccione tipo...</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select></td></tr>
                <tr><td class="detail-label">Fecha / Hora</td><td><input v-model="formData.fecha_creacion" type="datetime-local" class="detail-field"></td></tr>
                <tr><td class="detail-label">Tiempo Invertido</td><td><div class="field-inline"><input v-model="formData.tiempo_real_invertido" type="number" step="0.5" min="0" class="detail-field" placeholder="Ej: 1.5"><select v-model="formData.unidad_tiempo" class="detail-field" style="width: 100px;"><option value="horas">Horas</option><option value="dias">Días</option></select></div></td></tr>
              </tbody></table>
            </div>
          </div>
          <div class="detail-descriptions">
            <div class="desc-col"><strong>Descripción / Falla *</strong><textarea v-model="formData.descripcion_falla" required rows="3" class="detail-field detail-textarea" placeholder="Describa la falla reportada..."></textarea></div>
            <div class="desc-col"><strong>Acciones Realizadas</strong><textarea v-model="formData.acciones_realizadas" rows="3" class="detail-field detail-textarea" placeholder="Describa la reparación..."></textarea></div>
          </div>
          <div class="costos-repuestos-row">
            <div class="cr-col">
              <div class="costos-section">
                <div class="costo-form-inline">
                  <div class="cr-field" style="flex: 3;"><label>Costos Adicionales</label><input v-model="costoForm.descripcion_costo" type="text" class="detail-field" placeholder="Descripción del costo"></div>
                  <div class="cr-field"><label>Tipo</label><select v-model="costoForm.tipo_costo" class="detail-field"><option v-for="t in tiposCosto" :key="t" :value="t">{{ t }}</option></select></div>
                  <div class="cr-field" style="flex: 0.5;"><label>Monto</label><input v-model="costoForm.monto_costo" type="number" step="0.01" min="0" class="detail-field" placeholder="0.00"></div>
                  <div class="cr-field" style="flex: 0 0 25%;"><button type="button" class="btn-add-costo" @click="addCostoToOT">+ Agregar</button></div>
                </div>
                <ul class="costo-lista" v-if="costosAdicionales.length">
                  <li v-for="(c, idx) in costosAdicionales" :key="idx"><span class="costo-tipo">{{ c.tipo_costo }}</span><span class="costo-desc">{{ c.descripcion_costo }}</span><span class="costo-monto">Bs. {{ Number(c.monto_costo).toFixed(2) }}</span><button type="button" class="costo-remove" @click="removeCostoFromOT(idx)" title="Quitar costo">×</button></li>
                  <li class="costo-total"><span>Total:</span><span class="costo-monto-total">Bs. {{ totalCostos.toFixed(2) }}</span></li>
                </ul>
                <p v-else class="costo-empty">No hay costos agregados.</p>
              </div>
            </div>
            <div class="cr-col">
              <h4 class="section-title">Repuestos Utilizados</h4>
              <div class="repuestos-section">
                <div class="repuesto-selector">
                  <select v-model="selectedRepuestoId" class="detail-field"><option :value="null">Seleccionar...</option><option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">{{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})</option></select>
                  <input type="number" v-model="selectedCantidad" min="1" class="detail-field" style="width: 80px;">
                  <button type="button" class="btn-add-repuesto" @click="addRepuestoToOT">Agregar</button>
                </div>
                <ul class="repuesto-lista" v-if="repuestosSeleccionados.length"><li v-for="(item, idx) in repuestosSeleccionados" :key="idx">{{ item.cantidad }} x {{ item.nombre }}</li></ul>
                <p v-else class="repuesto-empty">No hay repuestos agregados.</p>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn-primary">Crear</button>
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ==================== MODAL VER ==================== -->
    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal modal-wide">
        <h3>Detalle de Orden #{{ selectedOT.id }}</h3>
        <div class="detail-tables">
          <div class="detail-table-block">
            <h4>Información General</h4>
            <table class="detail-table"><tbody>
              <tr><td class="detail-label">Equipo</td><td>{{ getEquipoNombre(selectedOT.equipo_id) }}</td></tr>
              <tr><td class="detail-label">Título / Tipo</td><td>{{ selectedOT.titulo }}</td></tr>
              <tr><td class="detail-label">Prioridad</td><td><span class="badge" :class="prioridadClass(selectedOT.prioridad)">{{ selectedOT.prioridad }}</span></td></tr>
              <tr><td class="detail-label">Estado</td><td><span class="badge" :style="{ backgroundColor: getEstadoColor(selectedOT.estado_id) }">{{ estadosOT.find(e => e.id === selectedOT.estado_id)?.nombre_estado }}</span></td></tr>
              <tr v-if="selectedOT.orden_preventiva_id"><td class="detail-label">Origen</td><td><span class="badge badge-preventivo">Preventivo #{{ selectedOT.orden_preventiva_id }}</span></td></tr>
            </tbody></table>
          </div>
          <div class="detail-table-block">
            <h4>Asignación y Tiempos</h4>
            <table class="detail-table"><tbody>
              <tr><td class="detail-label">Técnico</td><td>{{ getTecnicoNombre(selectedOT.tecnico_asignado_id) }}</td></tr>
              <tr><td class="detail-label">Fecha Creación</td><td>{{ selectedOT.fecha_creacion ? formatFechaHora(selectedOT) : 'N/A' }}</td></tr>
              <tr><td class="detail-label">Tiempo Invertido</td><td>{{ selectedOT.tiempo_real_invertido || 0 }} {{ selectedOT.unidad_tiempo === 'dias' ? 'días' : 'horas' }}</td></tr>
            </tbody></table>
          </div>
        </div>
        <div class="detail-descriptions">
          <div class="desc-col"><strong>Descripción de Falla</strong><div class="description-box">{{ selectedOT.descripcion_falla }}</div></div>
          <div v-if="selectedOT.acciones_realizadas" class="desc-col"><strong>Acciones Realizadas</strong><div class="description-box">{{ selectedOT.acciones_realizadas }}</div></div>
        </div>
        <div class="detail-section-title">Costos Adicionales ({{ detalleCostos.length }})</div>
        <div v-if="!detalleCostos.length" class="empty-section">Sin costos registrados.</div>
        <table v-else class="detail-table detail-table-full">
          <thead><tr><th class="detail-th">Tipo</th><th class="detail-th">Descripción</th><th class="detail-th">Monto</th></tr></thead>
          <tbody>
            <tr v-for="c in detalleCostos" :key="c.id"><td><span class="badge" style="background: #7c3aed; font-size: 0.72rem; padding: 1px 8px; border-radius: 10px;">{{ c.tipo_costo }}</span></td><td>{{ c.descripcion_costo }}</td><td style="font-weight: 700; color: #5b21b6; white-space: nowrap;">Bs. {{ Number(c.monto_costo).toFixed(2) }}</td></tr>
            <tr style="background: #ede9fe; border-top: 2px solid #7c3aed;"><td colspan="2" style="font-weight: 700; text-align: right; padding: 0.4rem 0.6rem;">Total:</td><td style="font-weight: 700; color: #5b21b6; font-size: 1rem; padding: 0.4rem 0.6rem;">Bs. {{ totalDetalleCostos.toFixed(2) }}</td></tr>
          </tbody>
        </table>
        <div class="detail-section-title">Repuestos Utilizados</div>
        <div v-if="!selectedOT.repuestos_usados || !selectedOT.repuestos_usados.length" class="empty-section">Sin repuestos registrados.</div>
        <table v-else class="detail-table detail-table-full">
          <thead><tr><th class="detail-th">Cantidad</th><th class="detail-th">Repuesto</th></tr></thead>
          <tbody><tr v-for="rep in selectedOT.repuestos_usados" :key="rep.repuesto_id"><td>{{ rep.cantidad_utilizada }} x</td><td>{{ getRepuestoNombre(rep.repuesto_id) }}</td></tr></tbody>
        </table>
        <div class="modal-actions"><button class="btn-secondary" @click="showViewModal = false">Cerrar</button></div>
      </div>
    </div>

    <!-- ==================== MODAL EDITAR ==================== -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal modal-wide modal-xl">
        <h3>Editar / Cerrar OT #{{ selectedOT.id }}</h3>
        <form @submit.prevent="updateOrden">
          <div class="detail-tables">
            <div class="detail-table-block">
              <h4>Asignación</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Equipo Afectado *</td><td><select v-model="editFormData.equipo_id" class="detail-field" required><option value="" disabled>Seleccione...</option><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}{{ eq.numero_serie ? ' — ' + eq.numero_serie : '' }}</option></select></td></tr>
                <tr><td class="detail-label">Nuevo Estado *</td><td><select v-model="editFormData.estado_id" class="detail-field" required><option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option></select></td></tr>
                <tr><td class="detail-label">Prioridad</td><td><select v-model="editFormData.prioridad" class="detail-field"><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select></td></tr>
                <tr><td class="detail-label">Técnico Asignado</td><td><select v-model="editFormData.tecnico_asignado_id" class="detail-field"><option :value="null">-- Sin Asignar --</option><option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">{{ tec.full_name || tec.username }}</option></select></td></tr>
              </tbody></table>
            </div>
            <div class="detail-table-block">
              <h4>Tipo y Tiempos</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Título / Tipo</td><td><select v-if="selectedOT.orden_preventiva_id" disabled class="detail-field" style="background: #f8fafc; color: #64748b; cursor: not-allowed;"><option value="Preventivo" selected>Preventivo</option></select><select v-else v-model="editFormData.titulo" class="detail-field" required><option value="" disabled>Seleccione tipo...</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select></td></tr>
                <tr><td class="detail-label">Fecha / Hora</td><td><input v-model="editFormData.fecha_creacion" type="datetime-local" class="detail-field"></td></tr>
                <tr><td class="detail-label">Tiempo Invertido</td><td><div class="field-inline"><input v-model="editFormData.tiempo_real_invertido" type="number" step="0.5" min="0" class="detail-field" placeholder="Ej: 1.5"><select v-model="editFormData.unidad_tiempo" class="detail-field" style="width: 100px;"><option value="horas">Horas</option><option value="dias">Días</option></select></div></td></tr>
              </tbody></table>
            </div>
          </div>
          <div class="detail-descriptions">
            <div class="desc-col"><strong>Descripción / Falla *</strong><textarea v-model="editFormData.descripcion_falla" required rows="3" class="detail-field detail-textarea" placeholder="Describa la falla..."></textarea></div>
            <div class="desc-col"><strong>Acciones Realizadas</strong><textarea v-model="editFormData.acciones_realizadas" rows="3" class="detail-field detail-textarea" placeholder="Describa la reparación..."></textarea></div>
          </div>
          <div class="costos-repuestos-row">
            <div class="cr-col">
              <div class="costos-section">
                <div class="costo-form-inline">
                  <div class="cr-field" style="flex: 3;"><label>Costos Adicionales</label><input v-model="editCostoForm.descripcion_costo" type="text" class="detail-field" placeholder="Descripción del costo"></div>
                  <div class="cr-field"><label>Tipo</label><select v-model="editCostoForm.tipo_costo" class="detail-field"><option v-for="t in tiposCosto" :key="t" :value="t">{{ t }}</option></select></div>
                  <div class="cr-field" style="flex: 0.5;"><label>Monto</label><input v-model="editCostoForm.monto_costo" type="number" step="0.01" min="0" class="detail-field" placeholder="0.00"></div>
                  <div class="cr-field" style="flex: 0 0 25%;"><button type="button" class="btn-add-costo" @click="addEditCostoToOT">+ Agregar</button></div>
                </div>
                <ul class="costo-lista" v-if="editCostosAdicionales.length">
                  <li v-for="(c, idx) in editCostosAdicionales" :key="idx"><span class="costo-tipo">{{ c.tipo_costo }}</span><span class="costo-desc">{{ c.descripcion_costo }}</span><span class="costo-monto">Bs. {{ Number(c.monto_costo).toFixed(2) }}</span><button type="button" class="costo-remove" @click="removeEditCostoFromOT(idx)" title="Quitar costo">×</button></li>
                  <li class="costo-total"><span>Total:</span><span class="costo-monto-total">Bs. {{ totalEditCostos.toFixed(2) }}</span></li>
                </ul>
                <p v-else class="costo-empty">No hay costos agregados.</p>
              </div>
            </div>
            <div class="cr-col">
              <h4 class="section-title">Repuestos Utilizados</h4>
              <div class="repuestos-section">
                <div class="repuesto-selector">
                  <select v-model="selectedRepuestoId" class="detail-field"><option :value="null">Seleccionar...</option><option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">{{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})</option></select>
                  <input type="number" v-model="selectedCantidad" min="1" class="detail-field" style="width: 80px;">
                  <button type="button" class="btn-add-repuesto" @click="addRepuestoToOT">Agregar</button>
                </div>
                <ul class="repuesto-lista" v-if="repuestosSeleccionados.length"><li v-for="(item, idx) in repuestosSeleccionados" :key="idx">{{ item.cantidad }} x {{ item.nombre }}</li></ul>
                <p v-else class="repuesto-empty">No hay repuestos agregados.</p>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn-primary">Guardar Cambios</button>
            <button type="button" class="btn-secondary" @click="showEditModal = false">Cancelar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Documentos Adjuntos -->
    <div v-if="showDocsModal" class="modal-overlay" @click.self="showDocsModal = false">
      <div class="modal modal-docs">
        <h3>Documentos - OT #{{ docsOT.id }} ({{ docsOT.titulo }})</h3>
        <DocumentosAdjuntos v-if="docsOT.id" :ordenTrabajoId="docsOT.id" />
        <div class="modal-actions"><button class="btn-secondary" @click="showDocsModal = false">Cerrar</button></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* === Layout General === */
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

/* === Top Bar === */
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; margin-bottom: 1rem; gap: 0.75rem; }
.top-bar h2 { margin: 0; }
.top-bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }
.search-wrapper { position: relative; display: flex; align-items: center; min-width: 200px; flex: 1 1 180px; max-width: 320px; }
.search-icon { position: absolute; left: 10px; color: #94a3b8; pointer-events: none; z-index: 1; }
.search-input { width: 100%; padding: 0.55rem 0.85rem 0.55rem 2.2rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; background: #fff; }
.search-input::placeholder { color: #94a3b8; }
.search-input:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }

/* === Barra de Filtros === */
.filter-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; margin-bottom: 1rem; padding: 0.75rem 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.filter-group { display: flex; align-items: center; gap: 0.35rem; }
.filter-label { font-size: 0.82rem; font-weight: 600; color: #64748b; white-space: nowrap; }
.filter-select { padding: 0.35rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.82rem; background: #fff; color: #334155; min-width: 130px; max-width: 200px; }
.filter-select:focus { outline: none; border-color: #3498db; }
.btn-clear-filters { display: flex; align-items: center; gap: 0.3rem; padding: 0.35rem 0.7rem; border: 1px solid #fecaca; border-radius: 6px; background: #fef2f2; color: #dc2626; font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-clear-filters:hover { background: #fee2e2; }

/* === Tabla Principal === */
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }

/* === Paginación === */
.table-pagination { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 1rem; margin-top: 1rem; padding: 0.75rem 0; }
.table-pagination-meta { font-size: 0.9rem; color: #475569; text-align: center; }
.btn-pagination { background-color: #3498db; color: white; border: none; padding: 0.5rem 1.1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: background-color 0.2s ease, opacity 0.2s ease; }
.btn-pagination:hover:not(:disabled) { background-color: #2980b9; }
.btn-pagination:disabled { opacity: 0.45; cursor: not-allowed; }

/* === Botones === */
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 1rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
.btn-icon-only { width: 42px; height: 42px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 1.2rem; line-height: 1; }

/* === Badges === */
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; font-weight: bold; }
.urgente { background-color: #e74c3c; }
.alta { background-color: #e67e22; }
.media { background-color: #f1c40f; color: #333; }
.badge-preventivo { background-color: #8b5cf6; color: white; font-size: 0.7rem; }

/* === Iconos de Acción === */
.actions-cell { display: flex; gap: 0.5rem; align-items: center; }
.btn-icon { background: #f0f2f5; color: #555; border: none; padding: 8px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.btn-view:hover { background: #16a34a; color: #ffffff; }
.btn-edit:hover { background: #2563eb; color: #ffffff; }
.btn-delete:hover { background: #dc2626; color: #ffffff; }
.btn-doc:hover { background: #0891b2; color: #ffffff; }

/* === Modales === */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 1.2rem 1.25rem; border-radius: 8px; width: 500px; max-width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.modal-wide { width: min(980px, 96vw); }
.modal-xl { width: min(1040px, 96vw); }
.modal-docs { width: 650px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

/* === Detail Table (nuevo layout para modales crear/editar) === */
.detail-tables { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }
.detail-table-block { flex: 1; }
.detail-table-block h4 { margin-bottom: 0.6rem; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.3rem; font-size: 0.95rem; }
.detail-table { width: 100%; border-collapse: collapse; }
.detail-table td { padding: 0.35rem 0.6rem; font-size: 0.88rem; border-bottom: 1px solid #eee; vertical-align: middle; }
.detail-table tr:last-child td { border-bottom: none; }
.detail-label { color: #666; font-weight: 600; width: 35%; white-space: nowrap; font-size: 0.8rem; padding-right: 0.35rem; }
.detail-field { width: 100%; padding: 0.45rem 0.55rem; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; background: #fff; font-size: 0.85rem; color: #334155; }
.detail-field:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.16); }
.detail-textarea { min-height: 84px; resize: vertical; font-family: inherit; }
.field-inline { display: flex; gap: 0.4rem; align-items: stretch; }
.field-inline .detail-field { flex: 1; }

/* === Descripciones === */
.detail-descriptions { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
.desc-col { flex: 1; }
.desc-col strong { display: block; margin-bottom: 0.25rem; color: #2c3e50; font-size: 0.85rem; }
.description-box { background: white; border: 1px solid #e0e0e0; border-radius: 4px; padding: 0.6rem; font-size: 0.85rem; color: #444; min-height: 50px; line-height: 1.5; word-break: break-word; overflow-y: auto; max-height: 150px; white-space: pre-wrap; }

/* === Sub-tablas en modal Ver === */
.detail-table-full { margin-bottom: 0.5rem; }
.detail-th { font-size: 0.78rem; color: #666; font-weight: 600; padding: 0.3rem 0.6rem; text-align: left; background: #f5f7fa; border-bottom: 1px solid #dde; }
.detail-section-title { font-size: 0.95rem; font-weight: 600; color: #2c3e50; margin-bottom: 0.5rem; margin-top: 0.8rem; }
.empty-section { text-align: center; padding: 1rem; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; color: #64748b; font-size: 0.88rem; margin-bottom: 0.5rem; }

/* === Sección de Título === */
.section-title { margin: 1rem 0 0.5rem 0; padding: 0; font-size: 1rem; font-weight: 700; color: #1e293b; border: none; background: none; }

/* === Costos + Repuestos en la misma fila === */
.costos-repuestos-row { display: flex; gap: 1.25rem; }
.cr-col { flex: 1; min-width: 0; }
@media (max-width: 768px) { .costos-repuestos-row { flex-direction: column; } .detail-tables { flex-direction: column; } }

/* === Costos Adicionales === */
.costos-section { padding: 0; margin-top: 0.5rem; }
.costo-form-inline { display: flex; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.75rem; flex-wrap: wrap; }
.cr-field { min-width: 100px; }
.cr-field label { display: block; font-size: 0.78rem; font-weight: 600; color: #64748b; margin-bottom: 0.2rem; }
.btn-add-costo { background: #7c3aed; color: white; border: none; padding: 0.55rem 0.8rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; white-space: nowrap; transition: background 0.2s; margin-top: 0.25rem; }
.btn-add-costo:hover { background: #6d28d9; }
.costo-lista { list-style: none; padding: 0; margin: 0; }
.costo-lista li { display: flex; align-items: center; gap: 0.5rem; padding: 6px 10px; background: #faf5ff; border-left: 3px solid #7c3aed; border-radius: 4px; margin-bottom: 4px; font-size: 0.85rem; color: #1e293b; flex-wrap: wrap; }
.costo-tipo { background: #7c3aed; color: white; padding: 1px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }
.costo-desc { flex: 1; min-width: 100px; }
.costo-monto { font-weight: 700; color: #5b21b6; white-space: nowrap; }
.costo-remove { background: #a78bfa; color: white; border: none; cursor: pointer; font-size: 0.85rem; line-height: 1; width: 20px; height: 20px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; padding: 0; transition: all 0.15s; flex-shrink: 0; }
.costo-remove:hover { background: #7c3aed; }
.costo-total { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px !important; background: #ede9fe !important; border-left: 3px solid #7c3aed !important; font-weight: 700; margin-top: 6px !important; }
.costo-monto-total { color: #5b21b6; font-size: 1rem !important; }
.costo-empty { color: #78716c; font-style: italic; font-size: 0.85rem; margin: 0.5rem 0 0 0; }

/* === Repuestos === */
.repuestos-section { padding: 0; margin-top: 0.5rem; }
.repuesto-selector { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 10px; }
.repuesto-selector select { flex: 1; }
.btn-add-repuesto { background: #d97706; color: white; border: none; padding: 0.55rem 0.8rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; white-space: nowrap; transition: background 0.2s; }
.btn-add-repuesto:hover { background: #b45309; }
.repuesto-lista { list-style: none; padding: 0; margin-top: 8px; }
.repuesto-lista li { padding: 8px 12px; background: #fffbf0; border-left: 3px solid #d97706; border-bottom: 1px solid #fef3c7; font-size: 0.9rem; color: #1e293b; font-weight: 500; }
.repuesto-lista li:last-child { border-bottom: none; }
.repuesto-empty { color: #78716c; font-style: italic; font-size: 0.85rem; margin: 0.5rem 0 0 0; }
</style>