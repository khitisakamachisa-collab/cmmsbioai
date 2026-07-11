<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'
import DocumentosAdjuntos from '../components/DocumentosAdjuntos.vue'  // v0.9.12
import { exportToExcelHTML, exportToCSV } from '../services/export.js'

// --- Variables generales ---
const contratos = ref([])
const proveedores = ref([])
const equipos = ref([])
const loading = ref(true)
const errorMsg = ref('')

const PAGE_SIZE = 10
const currentPage = ref(1)

// --- Filtros ---
const searchQuery = ref('')
const filterVigencia = ref('')   // '' | 'vigente' | 'vencido' | 'proximo'
const filterTipo = ref('')
const filterProveedor = ref('')

// --- Importación Excel (v0.9.8, mismo patrón que Equipos/Proveedores) ---
const showImportModal = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importDragOver = ref(false)

// --- Buscador interno de equipos en el modal (v0.9.8) ---
const equiposSearchQuery = ref('')

// --- Opciones para selects ---
const tiposContrato = [
  'Comodato', 'Mantenimiento Preventivo', 'Mantenimiento Correctivo',
  'Leasing', 'Garantía Extendida', 'Soporte Técnico', 'Servicio Integral', 'Otro'
]
const periodicidades = ['Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual']
const monedas = ['BOB']  // v0.9.15: solo Bolivianos para todo el proyecto

// --- Modal Crear/Editar ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})
const saving = ref(false)

// --- Modal Detalle ---
const showDetailModal = ref(false)
const selectedContrato = ref(null)

// v0.9.12: Modal Documentos
const showDocsModal = ref(false)
const docsContrato = ref(null)

// --- Helpers ---
const formatFecha = (f) => {
  if (!f) return '—'
  try {
    const d = new Date(f)
    return d.toLocaleDateString('es-BO', { year: 'numeric', month: '2-digit', day: '2-digit' })
  } catch {
    return String(f).slice(0, 10)
  }
}

const formatMoneda = (val, moneda) => {
  if (val === null || val === undefined || val === '') return '—'
  const num = Number(val)
  if (isNaN(num)) return String(val)
  return `${num.toLocaleString('es-BO', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${moneda || ''}`.trim()
}

const getEstadoVigencia = (c) => {
  if (!c) return { label: '—', clase: 'badge-gray' }
  if (c.activo) {
    if (c.dias_restantes !== null && c.dias_restantes <= 30) {
      return { label: `Vence pronto (${c.dias_restantes}d)`, clase: 'badge-yellow' }
    }
    return { label: 'Vigente', clase: 'badge-green' }
  }
  if (c.dias_restantes !== null && c.dias_restantes > 0) {
    return { label: 'Programado', clase: 'badge-blue' }
  }
  return { label: 'Vencido', clase: 'badge-red' }
}

// --- Carga de datos ---
async function cargarContratos() {
  loading.value = true
  errorMsg.value = ''
  try {
    const res = await apiClient.get('/contratos/')
    contratos.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    errorMsg.value = 'Error al cargar contratos: ' + (e.response?.data?.detail || e.message)
  } finally {
    loading.value = false
  }
}

async function cargarAuxiliares() {
  try {
    const [pr, eq] = await Promise.all([
      apiClient.get('/proveedores/'),
      apiClient.get('/equipos/')
    ])
    proveedores.value = Array.isArray(pr.data) ? pr.data : []
    equipos.value = Array.isArray(eq.data) ? (Array.isArray(eq.data) ? eq.data : (eq.data.items || [])) : []
  } catch (e) {
    console.error('Error cargando auxiliares:', e)
  }
}

// --- Filtros computados ---
const tieneFiltrosActivos = computed(() =>
  searchQuery.value.trim() || filterVigencia.value || filterTipo.value || filterProveedor.value
)

const limpiarFiltros = () => {
  searchQuery.value = ''
  filterVigencia.value = ''
  filterTipo.value = ''
  filterProveedor.value = ''
}

const filteredContratos = computed(() => {
  let result = contratos.value
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    result = result.filter(c => {
      const proveedor = String(c.proveedor_nombre ?? '').toLowerCase()
      const tipo = String(c.tipo_contrato ?? '').toLowerCase()
      const cobertura = String(c.cobertura_detalle ?? '').toLowerCase()
      const notas = String(c.notas ?? '').toLowerCase()
      return proveedor.includes(q) || tipo.includes(q) || cobertura.includes(q) || notas.includes(q)
    })
  }
  if (filterTipo.value) {
    result = result.filter(c => c.tipo_contrato === filterTipo.value)
  }
  if (filterProveedor.value) {
    result = result.filter(c => String(c.proveedor_id) === String(filterProveedor.value))
  }
  if (filterVigencia.value === 'vigente') {
    result = result.filter(c => c.activo === true)
  } else if (filterVigencia.value === 'vencido') {
    result = result.filter(c => c.activo === false && (c.dias_restantes === null || c.dias_restantes <= 0))
  } else if (filterVigencia.value === 'proximo') {
    result = result.filter(c => c.activo === true && c.dias_restantes !== null && c.dias_restantes <= 30)
  } else if (filterVigencia.value === 'programado') {
    result = result.filter(c => c.activo === false && c.dias_restantes !== null && c.dias_restantes > 0)
  }
  return result
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredContratos.value.length / PAGE_SIZE))
)

const paginatedContratos = computed(() => {
  const start = (currentPage.value - 1) * PAGE_SIZE
  return filteredContratos.value.slice(start, start + PAGE_SIZE)
})

watch([searchQuery, filterVigencia, filterTipo, filterProveedor], () => {
  currentPage.value = 1
})

// --- Stats ---
const stats = computed(() => {
  const total = contratos.value.length
  const vigentes = contratos.value.filter(c => c.activo).length
  const vencidos = contratos.value.filter(c => !c.activo && (c.dias_restantes === null || c.dias_restantes <= 0)).length
  const proximos = contratos.value.filter(c => c.activo && c.dias_restantes !== null && c.dias_restantes <= 30).length
  return { total, vigentes, vencidos, proximos }
})

// --- Formulario ---
function resetForm() {
  formData.value = {
    proveedor_id: '',
    tipo_contrato: 'Mantenimiento Preventivo',
    fecha_inicio: '',
    fecha_fin: '',
    costo_total: '',
    costo_periodico: '',
    periodicidad_costo: 'Único',
    moneda: 'BOB',  // v0.9.15: solo BOB
    cobertura_detalle: '',
    tiempo_respuesta: '',
    horario_servicio: '',
    notas: '',
    equipos_ids: []
  }
}

function abrirCrear() {
  resetForm()
  equiposSearchQuery.value = ''
  isEditing.value = false
  showModal.value = true
}

function abrirEditar(c) {
  // v0.9.10: guardar referencia al contrato que se edita para que guardarContrato() pueda obtener su id
  selectedContrato.value = c
  formData.value = {
    proveedor_id: c.proveedor_id,
    tipo_contrato: c.tipo_contrato,
    fecha_inicio: c.fecha_inicio ? String(c.fecha_inicio).slice(0, 10) : '',
    fecha_fin: c.fecha_fin ? String(c.fecha_fin).slice(0, 10) : '',
    costo_total: c.costo_total ?? '',
    costo_periodico: c.costo_periodico ?? '',
    periodicidad_costo: c.periodicidad_costo || 'Único',
    moneda: 'BOB',  // v0.9.15: forzar BOB al editar (ignorar valor anterior)
    cobertura_detalle: c.cobertura_detalle ?? '',
    tiempo_respuesta: c.tiempo_respuesta ?? '',
    horario_servicio: c.horario_servicio ?? '',
    notas: c.notas ?? '',
    equipos_ids: Array.isArray(c.equipos) ? c.equipos.map(e => e.id) : []
  }
  equiposSearchQuery.value = ''
  isEditing.value = true
  showModal.value = true
}

function cerrarModal() {
  showModal.value = false
}

async function guardarContrato() {
  // Validaciones
  if (!formData.value.proveedor_id) {
    alert('Seleccione un proveedor')
    return
  }
  if (!formData.value.fecha_inicio || !formData.value.fecha_fin) {
    alert('Ingrese fechas de inicio y fin')
    return
  }
  if (formData.value.fecha_fin < formData.value.fecha_inicio) {
    alert('La fecha fin debe ser mayor o igual a la fecha inicio')
    return
  }

  saving.value = true
  try {
    const payload = { ...formData.value }
    // Convertir números vacíos a null
    if (payload.costo_total === '') payload.costo_total = null
    if (payload.costo_periodico === '') payload.costo_periodico = null
    payload.proveedor_id = parseInt(payload.proveedor_id)
    if (!payload.equipos_ids || payload.equipos_ids.length === 0) {
      payload.equipos_ids = null
    }

    if (isEditing.value) {
      const id = selectedContrato.value?.id
      await apiClient.put(`/contratos/${id}`, payload)
    } else {
      await apiClient.post('/contratos/', payload)
    }
    showModal.value = false
    await cargarContratos()
  } catch (e) {
    const detail = e.response?.data?.detail || e.message
    alert('Error al guardar contrato: ' + (typeof detail === 'string' ? detail : JSON.stringify(detail)))
  } finally {
    saving.value = false
  }
}

// --- Detalle ---
function verDetalle(c) {
  selectedContrato.value = c
  showDetailModal.value = true
}

// v0.9.12: Abrir modal de documentos del contrato
function abrirDocs(c) {
  docsContrato.value = c
  showDocsModal.value = true
}

// --- Eliminar ---
async function eliminarContrato(c) {
  if (!confirm(`¿Eliminar contrato #${c.id} (${c.tipo_contrato} - ${c.proveedor_nombre})?\nEsta acción no se puede deshacer.`)) return
  try {
    await apiClient.delete(`/contratos/${c.id}`)
    await cargarContratos()
    if (selectedContrato.value?.id === c.id) {
      showDetailModal.value = false
      selectedContrato.value = null
    }
  } catch (e) {
    alert('Error al eliminar: ' + (e.response?.data?.detail || e.message))
  }
}

// --- Exportar ---
function exportarExcel() {
  const rows = filteredContratos.value.map(c => ({
    ID: c.id,
    Proveedor: c.proveedor_nombre || '',
    Tipo: c.tipo_contrato || '',
    'Fecha Inicio': c.fecha_inicio ? String(c.fecha_inicio).slice(0, 10) : '',
    'Fecha Fin': c.fecha_fin ? String(c.fecha_fin).slice(0, 10) : '',
    Estado: getEstadoVigencia(c).label,
    'Días Restantes': c.dias_restantes ?? '',
    'Costo Total': c.costo_total ?? '',
    'Costo Periódico': c.costo_periodico ?? '',
    Periodicidad: c.periodicidad_costo || '',
    Moneda: c.moneda || '',
    'Tiempo Respuesta': c.tiempo_respuesta || '',
    'Horario Servicio': c.horario_servicio || '',
    'Cobertura': c.cobertura_detalle || '',
    'Equipos Asociados': Array.isArray(c.equipos) ? c.equipos.map(e => e.nombre_corto).join('; ') : '',
    Notas: c.notas || ''
  }))
  exportToExcelHTML(rows, `Contratos_${new Date().toISOString().slice(0, 10)}`)
}

function exportarCSV() {
  const rows = filteredContratos.value.map(c => ({
    id: c.id,
    proveedor: c.proveedor_nombre || '',
    tipo: c.tipo_contrato || '',
    fecha_inicio: c.fecha_inicio ? String(c.fecha_inicio).slice(0, 10) : '',
    fecha_fin: c.fecha_fin ? String(c.fecha_fin).slice(0, 10) : '',
    estado: getEstadoVigencia(c).label,
    dias_restantes: c.dias_restantes ?? '',
    costo_total: c.costo_total ?? '',
    costo_periodico: c.costo_periodico ?? '',
    periodicidad: c.periodicidad_costo || '',
    moneda: c.moneda || '',
    equipos: Array.isArray(c.equipos) ? c.equipos.map(e => e.nombre_corto).join('; ') : ''
  }))
  exportToCSV(rows, `Contratos_${new Date().toISOString().slice(0, 10)}`)
}

// --- Importación Excel (v0.9.8, mismo patrón que Equipos/Proveedores) ---
function openImportModal() {
  importFile.value = null
  importResult.value = null
  importing.value = false
  importDragOver.value = false
  showImportModal.value = true
}

function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    importFile.value = file
    importResult.value = null
  }
}

function handleDragOver(e) {
  e.preventDefault()
  importDragOver.value = true
}

function handleDragLeave(e) {
  e.preventDefault()
  importDragOver.value = false
}

function handleDrop(e) {
  e.preventDefault()
  importDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    importFile.value = file
    importResult.value = null
  }
}

function descargarPlantillaExcel() {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_contratos.xlsx`
  link.download = 'CMMS-BioAI_Plantilla_Contratos.xlsx'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

function descargarPlantillaCSV() {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_contratos.csv`
  link.download = 'CMMS-BioAI_Plantilla_Contratos.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

async function submitImport() {
  if (!importFile.value) {
    alert('Seleccione un archivo primero')
    return
  }
  const ext = importFile.value.name.toLowerCase()
  if (!ext.endsWith('.xlsx') && !ext.endsWith('.csv')) {
    alert('Solo se aceptan archivos .xlsx o .csv')
    return
  }
  try {
    importing.value = true
    importResult.value = null
    const fd = new FormData()
    fd.append('file', importFile.value)
    const res = await apiClient.post('/contratos/import-excel', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    importResult.value = res.data
    await cargarContratos()
    await cargarAuxiliares()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Error al importar'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
    console.error(e)
  } finally {
    importing.value = false
  }
}

function resetImport() {
  importFile.value = null
  importResult.value = null
}

// --- Filtrado de equipos dentro del modal (v0.9.8) ---
const equiposFiltrados = computed(() => {
  const q = equiposSearchQuery.value.trim().toLowerCase()
  if (!q) return equipos.value
  return equipos.value.filter(eq => {
    const nombre = String(eq.nombre_corto ?? '').toLowerCase()
    const modelo = String(eq.modelo ?? '').toLowerCase()
    const serie = String(eq.numero_serie ?? '').toLowerCase()
    const marca = String(eq.marca ?? '').toLowerCase()
    return nombre.includes(q) || modelo.includes(q) || serie.includes(q) || marca.includes(q)
  })
})

// Contador de equipos seleccionados para mostrar en el label
const equiposSeleccionadosCount = computed(() => {
  return Array.isArray(formData.value.equipos_ids) ? formData.value.equipos_ids.length : 0
})

// v0.9.9: Opción B — chips/tags para Equipos Asociados
// Lista de objetos equipo ya seleccionados (para mostrar como chips)
const equiposSeleccionados = computed(() => {
  if (!Array.isArray(formData.value.equipos_ids)) return []
  return formData.value.equipos_ids
    .map(id => equipos.value.find(e => e.id === id))
    .filter(Boolean)
})

// Resultados de búsqueda EXCLUYENDO los ya seleccionados (para no duplicar)
const equiposResultadosBusqueda = computed(() => {
  return equiposFiltrados.value.filter(eq =>
    !(formData.value.equipos_ids || []).includes(eq.id)
  )
})

function agregarEquipo(eq) {
  if (!Array.isArray(formData.value.equipos_ids)) {
    formData.value.equipos_ids = []
  }
  if (!formData.value.equipos_ids.includes(eq.id)) {
    formData.value.equipos_ids.push(eq.id)
  }
  // Limpiar búsqueda para que la lista de resultados se oculte
  equiposSearchQuery.value = ''
}

function quitarEquipo(id) {
  if (Array.isArray(formData.value.equipos_ids)) {
    formData.value.equipos_ids = formData.value.equipos_ids.filter(i => i !== id)
  }
}

function limpiarSeleccionEquipos() {
  formData.value.equipos_ids = []
}

// --- Init ---
onMounted(async () => {
  await Promise.all([cargarContratos(), cargarAuxiliares()])
})
</script>

<template>
  <div>
    <div class="container">
      <div class="page-header">
        <div>
          <h2>Contratos</h2>
        </div>
        <div class="header-actions">
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="Proveedor, tipo, cobertura, notas..."
              autocomplete="off"
              aria-label="Buscar contratos"
            >
          </div>
          <button class="btn-import" @click="openImportModal" title="Cargar contratos desde Excel">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
            </svg>
            Cargar Excel
          </button>
          <button class="btn btn-export-excel" @click="exportarExcel" :disabled="!filteredContratos.length" title="Exportar tabla actual a Excel">📤 Excel</button>
          <button class="btn btn-export-csv" @click="exportarCSV" :disabled="!filteredContratos.length" title="Exportar tabla actual a CSV">📄 CSV</button>
          <button class="btn btn-primary" @click="abrirCrear">+ Nuevo Contrato</button>
        </div>
      </div>

      <!-- Stats -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total</div>
          <div class="stat-value">{{ stats.total }}</div>
        </div>
        <div class="stat-card stat-green">
          <div class="stat-label">Vigentes</div>
          <div class="stat-value">{{ stats.vigentes }}</div>
        </div>
        <div class="stat-card stat-yellow">
          <div class="stat-label">Vencen ≤30d</div>
          <div class="stat-value">{{ stats.proximos }}</div>
        </div>
        <div class="stat-card stat-red">
          <div class="stat-label">Vencidos</div>
          <div class="stat-value">{{ stats.vencidos }}</div>
        </div>
      </div>

      <!-- Filtros (sin buscador, igual a Equipos/Proveedores) -->
      <div class="filtros-card">
        <div class="filtros-grid">
          <div class="filtro-item">
            <label>Vigencia</label>
            <select v-model="filterVigencia" class="input">
              <option value="">Todos</option>
              <option value="vigente">Vigentes</option>
              <option value="proximo">Vencen ≤30d</option>
              <option value="programado">Programados</option>
              <option value="vencido">Vencidos</option>
            </select>
          </div>
          <div class="filtro-item">
            <label>Tipo</label>
            <select v-model="filterTipo" class="input">
              <option value="">Todos</option>
              <option v-for="t in tiposContrato" :key="t" :value="t">{{ t }}</option>
            </select>
          </div>
          <div class="filtro-item">
            <label>Proveedor</label>
            <select v-model="filterProveedor" class="input">
              <option value="">Todos</option>
              <option v-for="p in proveedores" :key="p.id" :value="p.id">{{ p.nombre_empresa }}</option>
            </select>
          </div>
          <div class="filtro-actions">
            <button v-if="tieneFiltrosActivos" class="btn-clear-filters" @click="limpiarFiltros" title="Limpiar filtros">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
              </svg>
              Limpiar
            </button>
            <span v-if="tieneFiltrosActivos" class="filter-count">{{ filteredContratos.length }} de {{ contratos.length }}</span>
          </div>
        </div>
      </div>

      <!-- Mensaje de error -->
      <div v-if="errorMsg" class="alert alert-error">{{ errorMsg }}</div>

      <!-- Tabla -->
      <div class="table-card">
        <div v-if="loading" class="loading">Cargando contratos...</div>
        <table v-else-if="paginatedContratos.length" class="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Proveedor</th>
              <th>Tipo</th>
              <th>Vigencia</th>
              <th>Estado</th>
              <th>Costo</th>
              <th class="acciones-col">Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in paginatedContratos" :key="c.id">
              <td>#{{ c.id }}</td>
              <td>{{ c.proveedor_nombre || '—' }}</td>
              <td>{{ c.tipo_contrato }}</td>
              <td>
                <div class="vigencia-cell">
                  <div>{{ formatFecha(c.fecha_inicio) }}</div>
                  <div class="vigencia-fin">→ {{ formatFecha(c.fecha_fin) }}</div>
                </div>
              </td>
              <td>
                <span class="badge" :class="getEstadoVigencia(c).clase">{{ getEstadoVigencia(c).label }}</span>
              </td>
              <td>
                <div v-if="c.costo_total !== null && c.costo_total !== undefined">
                  {{ formatMoneda(c.costo_total, c.moneda) }}
                </div>
                <div v-else-if="c.costo_periodico !== null && c.costo_periodico !== undefined" class="text-muted">
                  {{ formatMoneda(c.costo_periodico, c.moneda) }} / {{ c.periodicidad_costo }}
                </div>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="acciones-col actions-cell">
                <button class="btn-icon btn-view" title="Ver detalle" @click="verDetalle(c)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                  </svg>
                </button>
                <button class="btn-icon btn-edit" title="Editar" @click="abrirEditar(c)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5z"/>
                  </svg>
                </button>
                <button class="btn-icon btn-doc" title="Documentos Adjuntos" @click="abrirDocs(c)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1z"/>
                  </svg>
                </button>
                <button class="btn-icon btn-delete" title="Eliminar" @click="eliminarContrato(c)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                  </svg>
                </button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="empty">
          <p>No hay contratos registrados.</p>
          <button class="btn btn-primary" @click="abrirCrear">+ Crear primer contrato</button>
        </div>

        <!-- Paginación -->
        <div v-if="filteredContratos.length > PAGE_SIZE" class="paginacion">
          <button class="btn btn-secondary" :disabled="currentPage === 1" @click="currentPage--">← Anterior</button>
          <span>Página {{ currentPage }} de {{ totalPages }} ({{ filteredContratos.length }} contratos)</span>
          <button class="btn btn-secondary" :disabled="currentPage >= totalPages" @click="currentPage++">Siguiente →</button>
        </div>
      </div>
    </div>

    <!-- Modal Crear/Editar -->
    <div v-if="showModal" class="modal-overlay" @click.self="cerrarModal">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>{{ isEditing ? 'Editar Contrato' : 'Nuevo Contrato' }}</h3>
          <button class="btn-close" @click="cerrarModal">×</button>
        </div>
        <div class="modal-body">
          <div class="form-grid">
            <div class="form-group">
              <label>Proveedor <span class="req">*</span></label>
              <select v-model="formData.proveedor_id" class="input">
                <option value="">— Seleccionar —</option>
                <option v-for="p in proveedores" :key="p.id" :value="p.id">{{ p.nombre_empresa }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Tipo de Contrato <span class="req">*</span></label>
              <select v-model="formData.tipo_contrato" class="input">
                <option v-for="t in tiposContrato" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Fecha Inicio <span class="req">*</span></label>
              <input v-model="formData.fecha_inicio" type="date" class="input" />
            </div>
            <div class="form-group">
              <label>Fecha Fin <span class="req">*</span></label>
              <input v-model="formData.fecha_fin" type="date" class="input" />
            </div>
            <div class="form-group">
              <label>Costo Total</label>
              <input v-model="formData.costo_total" type="number" step="0.01" class="input" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label>Costo Periódico</label>
              <input v-model="formData.costo_periodico" type="number" step="0.01" class="input" placeholder="0.00" />
            </div>
            <div class="form-group">
              <label>Periodicidad Costo</label>
              <select v-model="formData.periodicidad_costo" class="input">
                <option v-for="p in periodicidades" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Moneda</label>
              <input v-model="formData.moneda" type="text" class="input input-readonly" readonly title="El sistema opera únicamente en Bolivianos (BOB)" />
            </div>
            <div class="form-group">
              <label>Tiempo de Respuesta</label>
              <input v-model="formData.tiempo_respuesta" type="text" class="input" placeholder="ej: 24h hábil" />
            </div>
            <div class="form-group">
              <label>Horario de Servicio</label>
              <input v-model="formData.horario_servicio" type="text" class="input" placeholder="ej: L-V 8:00-18:00" />
            </div>
            <div class="form-group form-group-full">
              <label>Cobertura (detalle)</label>
              <textarea v-model="formData.cobertura_detalle" class="input" rows="2" placeholder="Servicios incluidos en el contrato..."></textarea>
            </div>
            <div class="form-group form-group-full">
              <label>Notas</label>
              <textarea v-model="formData.notas" class="input" rows="2"></textarea>
            </div>
            <div class="form-group form-group-full">
              <label>
                Equipos Asociados
                <span class="equipos-counter">({{ equiposSeleccionadosCount }} seleccionado{{ equiposSeleccionadosCount === 1 ? '' : 's' }} de {{ equipos.length }})</span>
                <button v-if="equiposSeleccionadosCount > 0" type="button" class="btn-limpiar-seleccion" @click="limpiarSeleccionEquipos" title="Quitar todos">Limpiar selección</button>
              </label>
              <div class="equipos-selector">
                <!-- v0.9.9: Opción B — chips/tags de equipos seleccionados -->
                <div v-if="equiposSeleccionados.length" class="chips-container">
                  <span v-for="eq in equiposSeleccionados" :key="eq.id" class="chip">
                    <span class="chip-text">
                      <strong>{{ eq.nombre_corto || eq.modelo }}</strong>
                      <strong v-if="eq.marca" class="chip-sub-bold">{{ eq.marca }}</strong>
                      <strong v-if="eq.numero_serie" class="chip-sub-bold">SN: {{ eq.numero_serie }}</strong>
                    </span>
                    <button type="button" class="chip-remove" @click="quitarEquipo(eq.id)" title="Quitar equipo">×</button>
                  </span>
                </div>
                <div v-else class="chips-empty">
                  No hay equipos seleccionados. Use el buscador para agregar.
                </div>

                <!-- Buscador -->
                <div class="equipos-search-wrapper">
                  <svg class="equipos-search-icon" xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
                  </svg>
                  <input
                    v-model="equiposSearchQuery"
                    type="search"
                    class="equipos-search-input"
                    placeholder="Buscar equipo por nombre, modelo, serie o marca para agregar..."
                    autocomplete="off"
                  >
                  <button v-if="equiposSearchQuery" type="button" class="equipos-search-clear" @click="equiposSearchQuery = ''" title="Limpiar búsqueda">×</button>
                </div>

                <!-- Resultados de búsqueda (excluyendo ya seleccionados) -->
                <div v-if="equiposSearchQuery" class="equipos-resultados">
                  <p v-if="!equipos.length" class="text-muted equipos-empty">No hay equipos registrados.</p>
                  <p v-else-if="!equiposResultadosBusqueda.length" class="text-muted equipos-empty">No se encontraron equipos con "{{ equiposSearchQuery }}" o ya están todos seleccionados.</p>
                  <div v-else class="equipos-resultados-list">
                    <div v-for="eq in equiposResultadosBusqueda" :key="eq.id" class="equipo-item" @click="agregarEquipo(eq)">
                      <div class="equipo-item-info">
                        <strong>{{ eq.nombre_corto || eq.modelo }}</strong>
                        <strong v-if="eq.marca" class="equipo-item-bold">{{ eq.marca }}</strong>
                        <strong v-if="eq.numero_serie" class="equipo-item-bold">SN: {{ eq.numero_serie }}</strong>
                      </div>
                      <span class="equipo-item-add" title="Agregar">+ Agregar</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="cerrarModal" :disabled="saving">Cancelar</button>
          <button class="btn btn-primary" @click="guardarContrato" :disabled="saving">
            {{ saving ? 'Guardando...' : (isEditing ? 'Actualizar' : 'Crear') }}
          </button>
        </div>
      </div>
    </div>

    <!-- Modal Detalle -->
    <div v-if="showDetailModal && selectedContrato" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>Contrato #{{ selectedContrato.id }} — {{ selectedContrato.tipo_contrato }}</h3>
          <button class="btn-close" @click="showDetailModal = false">×</button>
        </div>
        <div class="modal-body">
          <div class="detalle-grid">
            <div class="detalle-item">
              <span class="detalle-label">Proveedor</span>
              <span class="detalle-value">{{ selectedContrato.proveedor_nombre || '—' }}</span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Estado</span>
              <span class="badge" :class="getEstadoVigencia(selectedContrato).clase">{{ getEstadoVigencia(selectedContrato).label }}</span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Fecha Inicio</span>
              <span class="detalle-value">{{ formatFecha(selectedContrato.fecha_inicio) }}</span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Fecha Fin</span>
              <span class="detalle-value">{{ formatFecha(selectedContrato.fecha_fin) }}</span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Días Restantes</span>
              <span class="detalle-value">{{ selectedContrato.dias_restantes ?? '—' }}</span>
            </div>
            <!-- v0.9.11: Precio del contrato destacado -->
            <div class="detalle-item detalle-precio">
              <span class="detalle-label">Precio del Contrato</span>
              <span class="detalle-value detalle-precio-value">
                <span v-if="selectedContrato.costo_total !== null && selectedContrato.costo_total !== undefined">
                  {{ formatMoneda(selectedContrato.costo_total, selectedContrato.moneda) }}
                  <small class="detalle-precio-tipo">Costo total</small>
                </span>
                <span v-else-if="selectedContrato.costo_periodico !== null && selectedContrato.costo_periodico !== undefined">
                  {{ formatMoneda(selectedContrato.costo_periodico, selectedContrato.moneda) }}
                  <small class="detalle-precio-tipo">Costo {{ selectedContrato.periodicidad_costo.toLowerCase() }}</small>
                </span>
                <span v-else class="text-muted">—</span>
              </span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Costo Total</span>
              <span class="detalle-value">{{ formatMoneda(selectedContrato.costo_total, selectedContrato.moneda) }}</span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Costo Periódico</span>
              <span class="detalle-value">
                {{ formatMoneda(selectedContrato.costo_periodico, selectedContrato.moneda) }}
                <small v-if="selectedContrato.costo_periodico !== null && selectedContrato.costo_periodico !== undefined" class="text-muted">/ {{ selectedContrato.periodicidad_costo }}</small>
              </span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Tiempo de Respuesta</span>
              <span class="detalle-value">{{ selectedContrato.tiempo_respuesta || '—' }}</span>
            </div>
            <div class="detalle-item">
              <span class="detalle-label">Horario de Servicio</span>
              <span class="detalle-value">{{ selectedContrato.horario_servicio || '—' }}</span>
            </div>
            <div class="detalle-item detalle-full">
              <span class="detalle-label">Cobertura</span>
              <span class="detalle-value">{{ selectedContrato.cobertura_detalle || '—' }}</span>
            </div>
            <div class="detalle-item detalle-full">
              <span class="detalle-label">Notas</span>
              <span class="detalle-value">{{ selectedContrato.notas || '—' }}</span>
            </div>
            <div class="detalle-item detalle-full">
              <span class="detalle-label">Equipos Asociados ({{ selectedContrato.equipos?.length || 0 }})</span>
              <div v-if="selectedContrato.equipos && selectedContrato.equipos.length" class="equipos-lista">
                <div v-for="eq in selectedContrato.equipos" :key="eq.id" class="equipo-tag">
                  <strong>{{ eq.nombre_corto }}</strong>
                  <strong v-if="eq.modelo" class="equipo-tag-detalle">— {{ eq.modelo }}</strong>
                  <strong v-if="eq.numero_serie" class="equipo-tag-detalle">SN: {{ eq.numero_serie }}</strong>
                  <strong v-if="eq.ubicacion_actual" class="equipo-tag-detalle">📍 {{ eq.ubicacion_actual }}</strong>
                </div>
              </div>
              <span v-else class="text-muted">Sin equipos asociados</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDetailModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ==================== Modal Importar Excel (v0.9.8) ==================== -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>Importar Contratos desde Excel</h3>
          <button class="btn-close" @click="showImportModal = false">×</button>
        </div>
        <div class="modal-body">
          <!-- Paso 1: Selección de archivo -->
          <div v-if="!importResult && !importing">
            <div
              class="drop-zone"
              :class="{ 'drop-zone--active': importDragOver, 'drop-zone--has-file': importFile }"
              @dragover="handleDragOver"
              @dragleave="handleDragLeave"
              @drop="handleDrop"
              @click="$refs.fileInput.click()"
            >
              <div v-if="!importFile" class="drop-zone-content">
                <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" viewBox="0 0 16 16" style="color: #94a3b8;">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
                </svg>
                <p class="drop-zone-text">Arrastre su archivo Excel o CSV aquí</p>
                <p class="drop-zone-subtext">o haga clic para seleccionar</p>
              </div>
              <div v-else class="drop-zone-content">
                <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" viewBox="0 0 16 16" style="color: #27ae60;">
                  <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1zm-3.5 8l-1.5-1.5L5 10l1 1 3-3 .5.5-3.5 3.5z"/>
                </svg>
                <p class="drop-zone-filename">{{ importFile.name }}</p>
                <p class="drop-zone-subtext">{{ (importFile.size / 1024).toFixed(1) }} KB</p>
              </div>
            </div>
            <input ref="fileInput" type="file" accept=".xlsx,.csv" style="display: none;" @change="handleFileSelect">

            <div class="import-info">
              <p><strong>Formato:</strong> Archivo .xlsx o .csv con encabezados en la primera fila.</p>
              <p><strong>Columna obligatoria:</strong> proveedor_nombre, tipo_contrato, fecha_inicio, fecha_fin</p>
              <p><strong>Equipos:</strong> en columna <code>equipos_series</code>, lista de número de serie separados por <code>;</code></p>
              <p>Si el proveedor no existe, se <strong>crea automáticamente</strong>. Si ya existe un contrato con mismo proveedor+tipo+fecha_inicio, se <strong>actualiza</strong> (upsert).</p>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="showImportModal = false">Cancelar</button>
              <button type="button" class="btn-outline" @click="descargarPlantillaExcel" title="Descargar plantilla Excel con datos de ejemplo">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                </svg>
                Plantilla Excel
              </button>
              <button type="button" class="btn-outline" @click="descargarPlantillaCSV" title="Descargar plantilla CSV">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;">
                  <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                  <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
                </svg>
                Plantilla CSV
              </button>
              <button type="button" class="btn btn-primary" :disabled="!importFile" @click="submitImport">
                Importar
              </button>
            </div>
          </div>

          <!-- Paso 2: Procesando -->
          <div v-if="importing" class="import-progress">
            <div class="spinner"></div>
            <p style="text-align: center; color: #475569;">Importando contratos...</p>
          </div>

          <!-- Paso 3: Resultados -->
          <div v-if="importResult && !importing">
            <div class="result-summary">
              <div class="result-item result-success">
                <span class="result-number">{{ importResult.exitosos }}</span>
                <span class="result-label">Nuevos</span>
              </div>
              <div class="result-item result-updated">
                <span class="result-number">{{ importResult.actualizados }}</span>
                <span class="result-label">Actualizados</span>
              </div>
              <div class="result-item result-failed">
                <span class="result-number">{{ importResult.fallidos }}</span>
                <span class="result-label">Fallidos</span>
              </div>
              <div class="result-item result-total">
                <span class="result-number">{{ importResult.total_procesados }}</span>
                <span class="result-label">Total</span>
              </div>
            </div>

            <div v-if="importResult.errores && importResult.errores.length > 0" class="import-errors">
              <h4>Detalle de errores / advertencias</h4>
              <div class="error-list">
                <div v-for="(err, idx) in importResult.errores" :key="idx" class="error-item">
                  <span class="error-fila">Fila {{ err.fila }}</span>
                  <span class="error-nombre">(Contrato: {{ err.nombre }})</span>
                  <span class="error-msg">{{ err.errores.join(', ') }}</span>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" @click="resetImport">Importar otro archivo</button>
              <button type="button" class="btn btn-primary" @click="showImportModal = false">Cerrar</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ==================== Modal Documentos (v0.9.12) ==================== -->
    <div v-if="showDocsModal && docsContrato" class="modal-overlay" @click.self="showDocsModal = false">
      <div class="modal modal-lg">
        <div class="modal-header">
          <h3>Documentos — Contrato #{{ docsContrato.id }} ({{ docsContrato.tipo_contrato }})</h3>
          <button class="btn-close" @click="showDocsModal = false">×</button>
        </div>
        <div class="modal-body">
          <DocumentosAdjuntos :contrato-id="docsContrato.id" />
        </div>
        <div class="modal-footer">
          <button class="btn btn-secondary" @click="showDocsModal = false">Cerrar</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 1.5rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.page-header h2 {
  margin: 0 0 0.25rem 0;
  font-size: 1.6rem;
  color: #1e293b;
}

.subtitle {
  margin: 0;
  color: #64748b;
  font-size: 0.9rem;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  border-left: 4px solid #64748b;
}

.stat-green { border-left-color: #10b981; }
.stat-yellow { border-left-color: #f59e0b; }
.stat-red { border-left-color: #ef4444; }

.stat-label {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.stat-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: #1e293b;
  margin-top: 0.25rem;
}

.filtros-card {
  background: white;
  padding: 1rem;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  margin-bottom: 1rem;
}

.filtros-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 0.75rem;
  align-items: end;
}

.filtro-item label {
  display: block;
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.filtro-actions {
  display: flex;
  align-items: end;
}

.input {
  width: 100%;
  padding: 0.5rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
  background: white;
  box-sizing: border-box;
  min-height: 38px;
  line-height: 1.4;
  color: #1e293b;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* v0.9.15: Normalizar altura de selects, dates y numbers para que coincidan */
select.input {
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 16 16'%3e%3cpath fill='none' stroke='%23475569' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='m2 5 6 6 6-6'/%3e%3c/svg%3e");
  background-repeat: no-repeat;
  background-position: right 0.6rem center;
  background-size: 14px;
  padding-right: 2rem;
}

input.input[type="date"],
input.input[type="number"],
input.input[type="text"],
input.input[type="email"],
input.input[type="search"] {
  height: 38px;
}

input.input[type="date"]::-webkit-calendar-picker-indicator {
  cursor: pointer;
}

textarea.input {
  min-height: 60px;
  height: auto;
  resize: vertical;
}

/* v0.9.15: input de solo lectura (ej: Moneda fija en BOB) */
.input-readonly {
  background: #f1f5f9 !important;
  color: #475569 !important;
  cursor: not-allowed;
  font-weight: 600;
}

.table-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  overflow: hidden;
}

.loading, .empty {
  padding: 3rem 1rem;
  text-align: center;
  color: #64748b;
}

.empty p {
  margin-bottom: 1rem;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

.table thead {
  background: #f1f5f9;
}

.table th {
  padding: 0.7rem 0.6rem;
  text-align: left;
  font-weight: 600;
  color: #475569;
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  border-bottom: 2px solid #e2e8f0;
}

.table td {
  padding: 0.6rem;
  border-bottom: 1px solid #f1f5f9;
  vertical-align: top;
}

.table tbody tr:hover {
  background: #f8fafc;
}

.acciones-col {
  white-space: nowrap;
  text-align: right;
}

.vigencia-cell {
  font-size: 0.82rem;
  line-height: 1.3;
}

.vigencia-fin {
  font-weight: 600;
  color: #1e293b;
}

.text-muted {
  color: #94a3b8;
  font-size: 0.78rem;
}

.equipos-count {
  display: inline-block;
  background: #e0e7ff;
  color: #4338ca;
  padding: 0.15rem 0.5rem;
  border-radius: 10px;
  font-size: 0.78rem;
  font-weight: 600;
}

.badge {
  display: inline-block;
  padding: 0.2rem 0.55rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
}

.badge-green { background: #dcfce7; color: #166534; }
.badge-yellow { background: #fef3c7; color: #92400e; }
.badge-red { background: #fee2e2; color: #991b1b; }
.badge-blue { background: #dbeafe; color: #1e40af; }
.badge-gray { background: #e2e8f0; color: #475569; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 0.9rem;
  border: none;
  border-radius: 4px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;
}

.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-primary { background: #3b82f6; color: white; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }

.btn-secondary { background: #e2e8f0; color: #475569; }
.btn-secondary:hover:not(:disabled) { background: #cbd5e1; }

/* v0.9.9: Botones de exportar con color sólido armónico con Importar (verde) y + Nuevo (azul) */
.btn-export-excel { background: #f59e0b; color: white; }
.btn-export-excel:hover:not(:disabled) { background: #d97706; }

.btn-export-csv { background: #0891b2; color: white; }
.btn-export-csv:hover:not(:disabled) { background: #0e7490; }

.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover:not(:disabled) { background: #dc2626; }

.btn-link {
  background: transparent;
  color: #3b82f6;
  padding: 0.5rem;
}

/* v0.9.8: Iconos SVG estilo Proveedores v0.9.7 — gris por defecto, color en hover */
.actions-cell { display: flex; gap: 0.5rem; align-items: center; }
.btn-icon {
  background: #f0f2f5; color: #555;
  border: none; padding: 8px; border-radius: 6px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.btn-view:hover { background: #16a34a; color: #ffffff; }
.btn-edit:hover { background: #2563eb; color: #ffffff; }
.btn-doc:hover { background: #0891b2; color: #ffffff; }  /* v0.9.12 */
.btn-delete:hover { background: #dc2626; color: #ffffff; }

/* Buscador superior (estilo Equipos/Proveedores) */
.search-wrapper {
  position: relative; display: flex; align-items: center;
  min-width: 200px; flex: 1 1 220px; max-width: 360px;
}
.search-icon {
  position: absolute; left: 10px; color: #94a3b8; pointer-events: none; z-index: 1;
}
.search-input {
  width: 100%; padding: 0.55rem 0.85rem 0.55rem 2.2rem;
  border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.9rem; box-sizing: border-box; background: #fff;
}
.search-input::placeholder { color: #94a3b8; }
.search-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }

/* Botón "Cargar Excel" (estilo Equipos/Proveedores) */
.btn-import {
  background-color: #27ae60; color: white; border: none; padding: 0.6rem 1.1rem;
  border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem;
  display: flex; align-items: center; gap: 0.4rem; transition: background-color 0.2s;
}
.btn-import:hover { background-color: #219a52; }
.btn-import svg { flex-shrink: 0; }

/* Botón outline para plantillas dentro del modal */
.btn-outline {
  background-color: transparent; color: #3b82f6; border: 1.5px solid #3b82f6;
  padding: 0.45rem 0.9rem; border-radius: 4px; cursor: pointer; font-weight: 600;
  font-size: 0.85rem; transition: all 0.2s; display: flex; align-items: center;
}
.btn-outline:hover { background-color: #ebf5ff; }

/* Botón limpiar filtros */
.btn-clear-filters {
  display: flex; align-items: center; gap: 0.3rem;
  padding: 0.35rem 0.7rem; border: 1px solid #fecaca; border-radius: 6px;
  background: #fef2f2; color: #dc2626;
  font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-clear-filters:hover { background: #fee2e2; }
.filter-count {
  font-size: 0.78rem; font-weight: 600; color: #64748b;
  background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 4px;
}

/* Drop-zone y spinner (estilo Equipos) */
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 10px; padding: 2rem 1.5rem;
  text-align: center; cursor: pointer; transition: all 0.25s ease;
  margin-bottom: 1rem; background: #f8fafc;
}
.drop-zone:hover { border-color: #3b82f6; background: #f0f7ff; }
.drop-zone--active { border-color: #3b82f6; background: #e8f4fd; border-style: solid; }
.drop-zone--has-file { border-color: #27ae60; border-style: solid; background: #f0fdf4; }
.drop-zone-content { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; }
.drop-zone-text { font-size: 1rem; font-weight: 600; color: #475569; margin: 0; }
.drop-zone-subtext { font-size: 0.85rem; color: #94a3b8; margin: 0; }
.drop-zone-filename { font-size: 0.95rem; font-weight: 600; color: #27ae60; margin: 0; word-break: break-all; }

.import-info {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.85rem; color: #475569;
}
.import-info p { margin: 0.2rem 0; }
.import-info code {
  background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 4px;
  font-size: 0.82rem; color: #7c3aed;
}

.import-progress {
  padding: 2rem; display: flex; flex-direction: column; align-items: center; gap: 1rem;
}
.spinner {
  width: 40px; height: 40px; border: 4px solid #e2e8f0;
  border-top-color: #3b82f6; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.result-summary {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem;
}
.result-item { text-align: center; padding: 0.75rem; border-radius: 8px; }
.result-number { display: block; font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
.result-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; color: #64748b; }
.result-success { background: #f0fdf4; }
.result-success .result-number { color: #16a34a; }
.result-updated { background: #eff6ff; }
.result-updated .result-number { color: #2563eb; }
.result-failed { background: #fef2f2; }
.result-failed .result-number { color: #dc2626; }
.result-total { background: #f8fafc; border: 1px solid #e2e8f0; }
.result-total .result-number { color: #1e293b; }

.import-errors {
  background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 0.75rem;
}
.import-errors h4 { margin: 0 0 0.5rem 0; color: #991b1b; font-size: 0.9rem; }
.error-list { max-height: 200px; overflow-y: auto; }
.error-item {
  padding: 0.35rem 0; font-size: 0.83rem; color: #7f1d1d;
  border-bottom: 1px solid #fecaca;
}
.error-item:last-child { border-bottom: none; }
.error-fila { font-weight: 700; margin-right: 0.5rem; }
.error-nombre { color: #991b1b; font-size: 0.8rem; margin-right: 0.5rem; }
.error-msg { color: #b91c1c; }

/* v0.9.8: Selector de equipos con buscador interno */
.equipos-counter {
  font-size: 0.75rem; font-weight: 500; color: #64748b;
  background: #f1f5f9; padding: 0.1rem 0.4rem; border-radius: 4px; margin-left: 0.5rem;
}
.btn-limpiar-seleccion {
  background: transparent; border: none; color: #dc2626; cursor: pointer;
  font-size: 0.75rem; font-weight: 600; text-decoration: underline;
  margin-left: 0.5rem; padding: 0;
}
.btn-limpiar-seleccion:hover { color: #b91c1c; }
.equipos-selector {
  display: flex; flex-direction: column; gap: 0.6rem;
}

/* v0.9.9: Chips/tags de equipos seleccionados */
.chips-container {
  display: flex; flex-wrap: wrap; gap: 0.4rem;
  padding: 0.5rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  min-height: 42px;
  max-height: 120px;
  overflow-y: auto;
}
.chips-empty {
  padding: 0.75rem;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 0.85rem;
  text-align: center;
}
.chip {
  display: inline-flex; align-items: center; gap: 0.35rem;
  background: #fde68a; color: #000000;
  border: 1px solid #f59e0b;
  padding: 0.3rem 0.4rem 0.3rem 0.65rem;
  border-radius: 14px;
  font-size: 0.82rem;
  font-weight: 600;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(245, 158, 11, 0.25);
}
.chip:hover { background: #fcd34d; border-color: #d97706; }
.chip-text {
  display: inline-flex; flex-direction: column; line-height: 1.2;
}
.chip-sub-bold {
  font-size: 0.72rem; font-weight: 600; color: #000000; margin-top: 2px;
}
.chip-remove {
  background: rgba(0, 0, 0, 0.15); border: none; color: #000000;
  cursor: pointer; font-size: 1rem; line-height: 1;
  width: 18px; height: 18px; border-radius: 50%;
  display: inline-flex; align-items: center; justify-content: center;
  padding: 0; transition: all 0.15s;
}
.chip-remove:hover { background: #000000; color: #ffffff; }

/* Buscador */
.equipos-search-wrapper {
  position: relative; display: flex; align-items: center;
}
.equipos-search-icon {
  position: absolute; left: 10px; color: #94a3b8; pointer-events: none; z-index: 1;
}
.equipos-search-input {
  width: 100%; padding: 0.5rem 2rem 0.5rem 2rem;
  border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.88rem; box-sizing: border-box; background: #fff;
}
.equipos-search-input::placeholder { color: #94a3b8; }
.equipos-search-input:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }
.equipos-search-clear {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  background: transparent; border: none; color: #94a3b8; cursor: pointer;
  font-size: 1.3rem; line-height: 1; padding: 0.2rem 0.4rem; border-radius: 4px;
}
.equipos-search-clear:hover { background: #f1f5f9; color: #475569; }

/* Resultados de búsqueda (lista desplegable) */
.equipos-resultados {
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  background: white;
  max-height: 220px;
  overflow-y: auto;
}
.equipos-resultados-list {
  display: flex; flex-direction: column;
}
.equipo-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  border-bottom: 1px solid #f1f5f9;
  transition: background 0.15s;
}
.equipo-item:last-child { border-bottom: none; }
.equipo-item:hover { background: #f0f7ff; }
.equipo-item-info {
  display: flex; flex-direction: column; gap: 0.1rem; line-height: 1.3;
}
.equipo-item-info strong:first-child { font-size: 0.92rem; }
.equipo-item-bold {
  font-size: 0.76rem; font-weight: 600; color: #334155;
}
.equipo-item-add {
  font-size: 0.78rem; font-weight: 700; color: #16a34a;
  background: #dcfce7; padding: 0.2rem 0.55rem; border-radius: 12px;
  flex-shrink: 0; transition: all 0.15s;
}
.equipo-item:hover .equipo-item-add {
  background: #16a34a; color: white;
}
.equipos-empty { padding: 1rem; text-align: center; }

.paginacion {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  color: #64748b;
  border-top: 1px solid #f1f5f9;
}

.alert {
  padding: 0.75rem 1rem;
  border-radius: 6px;
  margin-bottom: 1rem;
  font-size: 0.88rem;
}

.alert-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fecaca;
}

/* Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: 2rem 1rem;
  z-index: 1000;
  overflow-y: auto;
}

.modal {
  background: white;
  border-radius: 8px;
  width: 100%;
  max-width: 600px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.2);
}

.modal-lg { max-width: 800px; }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
}

.modal-header h3 {
  margin: 0;
  font-size: 1.15rem;
  color: #1e293b;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #64748b;
  padding: 0;
  width: 28px;
  height: 28px;
  border-radius: 4px;
}

.btn-close:hover { background: #f1f5f9; }

.modal-body {
  padding: 1.25rem;
  max-height: 70vh;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #e2e8f0;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
}

.form-group { display: flex; flex-direction: column; gap: 0.25rem; }
.form-group-full { grid-column: 1 / -1; }

.form-group label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
}

.req { color: #ef4444; }

/* Detalle */
.detalle-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.85rem 1.25rem;
}

.detalle-item {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.detalle-full { grid-column: 1 / -1; }

.detalle-label {
  font-size: 0.74rem;
  font-weight: 600;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.detalle-value {
  font-size: 0.92rem;
  color: #1e293b;
}

/* v0.9.11: Precio del contrato destacado en el modal "ojo" */
.detalle-precio {
  grid-column: 1 / -1;
  background: #fef3c7;
  border: 1px solid #fcd34d;
  border-radius: 8px;
  padding: 0.75rem 1rem;
}
.detalle-precio .detalle-label {
  color: #92400e;
  font-size: 0.78rem;
}
.detalle-precio-value {
  font-size: 1.4rem !important;
  font-weight: 700;
  color: #92400e;
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  flex-wrap: wrap;
}
.detalle-precio-tipo {
  font-size: 0.72rem !important;
  font-weight: 500;
  color: #b45309;
  text-transform: lowercase;
  letter-spacing: 0.02em;
}

.equipos-lista {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.25rem;
}

.equipo-tag {
  background: #fef3c7;
  border: 1px solid #fcd34d;
  padding: 0.5rem 0.7rem;
  border-radius: 6px;
  font-size: 0.85rem;
  color: #000000;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: baseline;
}
.equipo-tag strong { color: #000000; }
.equipo-tag-detalle {
  font-weight: 600;
  color: #000000;
  font-size: 0.78rem;
}

@media (max-width: 768px) {
  .form-grid { grid-template-columns: 1fr; }
  .detalle-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: stretch; }
  .header-actions { justify-content: stretch; }
  .header-actions .btn { flex: 1; justify-content: center; }
}
</style>
