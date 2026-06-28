<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
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
  if (!q) return ordenes.value
  return ordenes.value.filter((ot) => {
    const titulo = String(ot.titulo ?? '').toLowerCase()
    const falla = String(ot.descripcion_falla ?? '').toLowerCase()
    const id = String(ot.id ?? '')
    const equipo = getEquipoNombre(ot.equipo_id).toLowerCase()
    return titulo.includes(q) || falla.includes(q) || id.includes(q) || equipo.includes(q)
  })
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

watch(searchQuery, () => {
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

// Formulario Crear
const formData = ref({
  equipo_id: '',
  estado_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: null,
  unidad_tiempo: 'horas'
})

// Formulario Editar
const editFormData = ref({
  estado_id: '',
  prioridad: 'Media',
  acciones_realizadas: '',
  tiempo_real_invertido: null,
  unidad_tiempo: 'horas',
  tecnico_asignado_id: null,
  costo_adicional: null,
  costos_adicionales: null
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

const saveOrden = async () => {
  try {
    await apiClient.post('/ordenes/', formData.value)
    alert('Orden creada')
    showModal.value = false
    formData.value = { equipo_id: '', estado_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: null, unidad_tiempo: 'horas' }
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
    showViewModal.value = true
  } catch (e) {
    alert("Error al cargar detalles")
  }
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
      estado_id: fullOt.estado_id,
      prioridad: fullOt.prioridad || 'Media',
      acciones_realizadas: fullOt.acciones_realizadas || '',
      tiempo_real_invertido: fullOt.tiempo_real_invertido || null,
      unidad_tiempo: fullOt.unidad_tiempo || 'horas',
      tecnico_asignado_id: fullOt.tecnico_asignado_id || null,
      costo_adicional: fullOt.costo_adicional || null,
      costos_adicionales: fullOt.costos_adicionales || null
    }
    
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
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Listado de Órdenes de Trabajo</h2>
        <div class="top-bar-actions">
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="Titulo, equipo, ID..."
              autocomplete="off"
            >
          </div>
          <button class="btn-primary" @click="showModal = true">+ Nueva Orden</button>
        </div>
      </div>

      <div v-if="loading">Cargando...</div>

      <table v-if="!loading && ordenes.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Equipo</th>
            <th>Título</th>
            <th>Prioridad</th>
            <th>Estado</th>
            <th>Origen</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ot in paginatedOrdenes" :key="ot.id">
            <td>#{{ ot.id }}</td>
            <td>{{ getEquipoNombre(ot.equipo_id) }}</td>
            <td>
              <strong>{{ ot.titulo }}</strong><br>
              <small>{{ ot.descripcion_falla.substring(0, 30) }}...</small>
            </td>
            <td>
              <span class="badge" :class="prioridadClass(ot.prioridad)">{{ ot.prioridad }}</span>
            </td>
            <td>
               <span class="badge" :style="{ backgroundColor: getEstadoColor(ot.estado_id) }">
                 {{ estadosOT.find(e => e.id === ot.estado_id)?.nombre_estado || 'N/A' }}
               </span>
            </td>
            <td>
              <span v-if="ot.orden_preventiva_id" class="badge badge-preventivo" title="Generada desde tarea preventiva">
                Preventivo #{{ ot.orden_preventiva_id }}
              </span>
              <span v-else class="badge badge-correctivo">Correctivo</span>
            </td>
            <td class="actions-cell">
              <!-- Ojo: Ver Detalle -->
              <button class="btn-icon" title="Ver Detalles" @click="openViewModal(ot)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                </svg>
              </button>
              
              <!-- Lápiz: Editar -->
              <button class="btn-icon btn-edit-icon" title="Editar / Cerrar" @click="openEditModal(ot)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10z"/>
                </svg>
              </button>

              <!-- Papelera: Eliminar -->
              <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteOrden(ot.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                  <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
              </button>

              <!-- Cuaderno: Documentos -->
              <button class="btn-icon btn-doc-icon" title="Documentos Adjuntos" @click="openDocsModal(ot)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1z"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="!loading && ordenes.length"
        class="table-pagination"
        role="navigation"
        aria-label="Paginación del listado de órdenes"
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
          Página {{ currentPage }} de {{ totalPages }}
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
    </main>

    <!-- Modal Crear OT -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>Nueva Orden de Trabajo</h3>
        <form @submit.prevent="saveOrden">
          <div class="form-group"><label>Equipo Afectado *</label><select v-model="formData.equipo_id" required><option value="" disabled>Seleccione...</option><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}</option></select></div>
          <div class="form-row">
            <div class="form-group"><label>Estado *</label><select v-model="formData.estado_id" required><option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option></select></div>
            <div class="form-group"><label>Prioridad</label><select v-model="formData.prioridad"><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select></div>
          </div>
          <div class="form-group"><label>Técnico Asignado</label><select v-model="formData.tecnico_asignado_id"><option :value="null">-- Sin Asignar --</option><option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">{{ tec.full_name || tec.username }}</option></select></div>
          <div class="form-group"><label>Título / Tipo de OT *</label><select v-model="formData.titulo" required><option value="" disabled>Seleccione tipo...</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select></div>
          <div class="form-group"><label>Descripción</label><textarea v-model="formData.descripcion_falla" required></textarea></div>
          <div class="modal-actions"><button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button><button type="submit" class="btn-primary">Crear</button></div>
        </form>
      </div>
    </div>

    <!-- MODAL VER (Solo Lectura) -->
    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal" style="width: 700px;">
        <h3>Detalle de Orden #{{ selectedOT.id }}</h3>
        <div class="detail-grid-view">
          <div class="detail-column">
            <h4>Información General</h4>
            <p><strong>Equipo:</strong> {{ getEquipoNombre(selectedOT.equipo_id) }}</p>
            <p><strong>Título / Tipo:</strong> {{ selectedOT.titulo }}</p>
            <p><strong>Prioridad:</strong> 
              <span class="badge" :class="prioridadClass(selectedOT.prioridad)">{{ selectedOT.prioridad }}</span>
            </p>
            <p><strong>Estado:</strong> 
              <span class="badge" :style="{ backgroundColor: getEstadoColor(selectedOT.estado_id) }">
                {{ estadosOT.find(e => e.id === selectedOT.estado_id)?.nombre_estado }}
              </span>
            </p>
            <p v-if="selectedOT.orden_preventiva_id"><strong>Origen:</strong> 
              <span class="badge badge-preventivo">Preventivo #{{ selectedOT.orden_preventiva_id }}</span>
            </p>
          </div>
          <div class="detail-column">
            <h4>Asignación y Tiempos</h4>
            <p><strong>Técnico:</strong> {{ getTecnicoNombre(selectedOT.tecnico_asignado_id) }}</p>
            <p><strong>Fecha Creación:</strong> {{ selectedOT.fecha_creacion ? new Date(selectedOT.fecha_creacion).toLocaleDateString('es-BO') : 'N/A' }}</p>
            <p><strong>Tiempo Invertido:</strong> {{ selectedOT.tiempo_real_invertido || 0 }} {{ selectedOT.unidad_tiempo === 'dias' ? 'días' : 'horas' }}</p>
            <p><strong>Costo General:</strong> {{ selectedOT.costo_adicional ? 'Bs. ' + Number(selectedOT.costo_adicional).toFixed(2) : '-' }}</p>
            <p><strong>Costos Adicionales:</strong> {{ selectedOT.costos_adicionales ? 'Bs. ' + Number(selectedOT.costos_adicionales).toFixed(2) : '-' }}</p>
          </div>
        </div>
        <div class="detail-full-view">
          <h4>Descripción de Falla</h4>
          <div class="description-box">{{ selectedOT.descripcion_falla }}</div>
        </div>
        <div class="detail-full-view" v-if="selectedOT.acciones_realizadas">
          <h4>Acciones Realizadas</h4>
          <div class="description-box" style="color: #27ae60;">{{ selectedOT.acciones_realizadas }}</div>
        </div>
        <div class="detail-full-view">
          <h4>Repuestos Utilizados</h4>
          <ul v-if="selectedOT.repuestos_usados && selectedOT.repuestos_usados.length" class="repuesto-detail-list">
            <li v-for="rep in selectedOT.repuestos_usados" :key="rep.repuesto_id">
              {{ rep.cantidad_utilizada }} x Repuesto #{{ rep.repuesto_id }}
            </li>
          </ul>
          <p v-else style="color: #888;"><em>Sin repuestos registrados.</em></p>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showViewModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- MODAL EDITAR (Formulario) -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal" style="width: 700px;">
        <h3>Editar / Cerrar OT #{{ selectedOT.id }}</h3>
        
        <!-- Información de la OT (solo lectura) -->
        <div class="ot-details">
          <p><strong>Equipo:</strong> {{ getEquipoNombre(selectedOT.equipo_id) }}</p>
          <p><strong>Título:</strong> {{ selectedOT.titulo }}</p>
          <p><strong>Falla:</strong> {{ selectedOT.descripcion_falla }}</p>
        </div>

        <form @submit.prevent="updateOrden">
          <!-- Estado y Prioridad lado a lado -->
          <div class="form-row">
            <div class="form-group">
              <label>Nuevo Estado *</label>
              <select v-model="editFormData.estado_id" required>
                <option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Prioridad</label>
              <select v-model="editFormData.prioridad">
                <option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option>
              </select>
            </div>
          </div>

          <!-- Técnico y Tiempo lado a lado (con unidad_tiempo) -->
          <div class="form-row">
            <div class="form-group">
              <label>Técnico Asignado</label>
              <select v-model="editFormData.tecnico_asignado_id">
                <option :value="null">-- Sin Asignar --</option>
                <option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">
                  {{ tec.full_name || tec.username }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Tiempo Invertido</label>
              <div style="display: flex; gap: 8px;">
                <input v-model="editFormData.tiempo_real_invertido" type="number" step="0.5" min="0" placeholder="Ej: 1.5" style="flex: 1;">
                <select v-model="editFormData.unidad_tiempo" style="width: 100px;">
                  <option value="horas">Horas</option>
                  <option value="dias">Días</option>
                </select>
              </div>
            </div>
          </div>

          <!-- Acciones Realizadas -->
          <div class="form-group">
            <label>Acciones Realizadas</label>
            <textarea v-model="editFormData.acciones_realizadas" rows="3" placeholder="Describa la reparación..."></textarea>
          </div>

          <!-- Costos lado a lado -->
          <div class="form-row">
            <div class="form-group">
              <label>Costo General (Bs.)</label>
              <input v-model="editFormData.costo_adicional" type="number" step="0.01" min="0" placeholder="Costos directos de la OT">
            </div>
            <div class="form-group">
              <label>Costos Adicionales (Bs.)</label>
              <input v-model="editFormData.costos_adicionales" type="number" step="0.01" min="0" placeholder="Externos, transporte, etc.">
            </div>
          </div>

          <hr>
          <h4>Repuestos Utilizados</h4>
          <div class="repuesto-selector">
            <select v-model="selectedRepuestoId"><option :value="null">Seleccionar...</option><option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">{{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})</option></select>
            <input type="number" v-model="selectedCantidad" min="1" style="width: 60px">
            <button type="button" class="btn-sm" @click="addRepuestoToOT">Agregar</button>
          </div>
          <ul class="repuesto-lista" v-if="repuestosSeleccionados.length">
            <li v-for="(item, idx) in repuestosSeleccionados" :key="idx">{{ item.cantidad }} x {{ item.nombre }}</li>
          </ul>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showEditModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar Cambios</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Documentos Adjuntos -->
    <div v-if="showDocsModal" class="modal-overlay" @click.self="showDocsModal = false">
      <div class="modal modal-docs">
        <h3>Documentos - OT #{{ docsOT.id }} ({{ docsOT.titulo }})</h3>
        <DocumentosAdjuntos v-if="docsOT.id" :ordenTrabajoId="docsOT.id" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDocsModal = false">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Estilo para que el texto largo no se salga y tenga scroll */
.detail-box, .ot-details {
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 4px;
  margin-bottom: 1rem;
  
  /* Magia CSS para texto largo */
  word-wrap: break-word;      /* Rompe palabras largas */
  white-space: pre-wrap;      /* Respeta enters del usuario */
  max-height: 200px;          /* Altura máxima antes de scroll */
  overflow-y: auto;           /* Activa scroll vertical si es necesario */
}

.detail-box p {
  margin: 0.5rem 0;
}

/* Estilos */
.dashboard-container { padding: 0; }
.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; }
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; margin-bottom: 1rem; gap: 0.75rem; }
.top-bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }
.search-wrapper {
  position: relative; display: flex; align-items: center;
  min-width: 200px; flex: 1 1 180px; max-width: 320px;
}
.search-icon { position: absolute; left: 10px; color: #94a3b8; pointer-events: none; z-index: 1; }
.search-input {
  width: 100%; padding: 0.55rem 0.85rem 0.55rem 2.2rem;
  border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9rem;
  box-sizing: border-box; background: #fff;
}
.search-input::placeholder { color: #94a3b8; }
.search-input:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; font-weight: bold; }
.urgente { background-color: #e74c3c; }
.alta { background-color: #e67e22; }
.media { background-color: #f1c40f; color: #333; }
.badge-preventivo { background-color: #8b5cf6; color: white; font-size: 0.7rem; }
.badge-correctivo { background-color: #6b7280; color: white; font-size: 0.7rem; }

/* Detail grid for View modal */
.detail-grid-view { display: flex; gap: 2rem; margin-bottom: 1.5rem; }
.detail-column { flex: 1; }
.detail-column h4 { margin-bottom: 0.8rem; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.3rem; }
.detail-column p { margin: 0 0 0.5rem 0; font-size: 0.9rem; color: #555; }
.detail-full-view { width: 100%; background: #f8f9fa; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }
.detail-full-view h4 { margin-top: 0; margin-bottom: 0.5rem; color: #2c3e50; }
.description-box {
  background: white; padding: 0.8rem; border: 1px solid #e0e0e0; border-radius: 4px;
  min-height: 40px; color: #444; font-size: 0.9rem;
  word-break: break-word; overflow-y: auto; max-height: 150px; white-space: pre-wrap;
}
.repuesto-detail-list { list-style: none; padding: 0; margin: 0; }
.repuesto-detail-list li { padding: 4px 0; font-size: 0.9rem; color: #555; border-bottom: 1px solid #eee; }

/* Iconos */
.actions-cell { display: flex; gap: 0.5rem; }
.btn-icon { background: #f0f2f5; border: none; padding: 8px; border-radius: 6px; cursor: pointer; color: #555; }
.btn-icon:hover { background: #dfe2e6; }
.btn-edit-icon:hover { background: #fff3cd; color: #856404; }
.btn-danger-icon:hover { background: #fee2e2; color: #c0392b; }
.btn-doc-icon:hover { background: #e8f4fd; color: #2563eb; }

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 600px; max-width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.modal-docs { width: 650px; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
.detail-box { background: #f8f9fa; padding: 1rem; border-radius: 4px; }
.detail-box p { margin: 0.5rem 0; }
.ot-details { background: #f8f9fa; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
.repuesto-selector { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.repuesto-lista { list-style: none; padding: 0; background: #f9f9f9; border: 1px solid #eee; }
.repuesto-lista li { padding: 8px; border-bottom: 1px solid #eee; font-size: 0.9rem; }

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
</style>
