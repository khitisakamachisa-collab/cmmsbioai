<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
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

// --- Opciones para selects ---
const tiposContrato = [
  'Comodato', 'Mantenimiento Preventivo', 'Mantenimiento Correctivo',
  'Leasing', 'Garantía Extendida', 'Soporte Técnico', 'Servicio Integral', 'Otro'
]
const periodicidades = ['Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual']
const monedas = ['USD', 'EUR', 'BOB', 'MXN', 'ARS', 'CLP', 'COP', 'PEN', 'BRL', 'Otro']

// --- Modal Crear/Editar ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})
const saving = ref(false)

// --- Modal Detalle ---
const showDetailModal = ref(false)
const selectedContrato = ref(null)

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
    moneda: 'USD',
    cobertura_detalle: '',
    tiempo_respuesta: '',
    horario_servicio: '',
    notas: '',
    equipos_ids: []
  }
}

function abrirCrear() {
  resetForm()
  isEditing.value = false
  showModal.value = true
}

function abrirEditar(c) {
  formData.value = {
    proveedor_id: c.proveedor_id,
    tipo_contrato: c.tipo_contrato,
    fecha_inicio: c.fecha_inicio ? String(c.fecha_inicio).slice(0, 10) : '',
    fecha_fin: c.fecha_fin ? String(c.fecha_fin).slice(0, 10) : '',
    costo_total: c.costo_total ?? '',
    costo_periodico: c.costo_periodico ?? '',
    periodicidad_costo: c.periodicidad_costo || 'Único',
    moneda: c.moneda || 'USD',
    cobertura_detalle: c.cobertura_detalle ?? '',
    tiempo_respuesta: c.tiempo_respuesta ?? '',
    horario_servicio: c.horario_servicio ?? '',
    notas: c.notas ?? '',
    equipos_ids: Array.isArray(c.equipos) ? c.equipos.map(e => e.id) : []
  }
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

// --- Init ---
onMounted(async () => {
  await Promise.all([cargarContratos(), cargarAuxiliares()])
})
</script>

<template>
  <div>
    <Navbar />
    <div class="container">
      <div class="page-header">
        <div>
          <h2>Contratos</h2>
          <p class="subtitle">Gestión de contratos de mantenimiento, leasing, comodato y otros (RF12)</p>
        </div>
        <div class="header-actions">
          <button class="btn btn-secondary" @click="exportarExcel" :disabled="!filteredContratos.length">📤 Excel</button>
          <button class="btn btn-secondary" @click="exportarCSV" :disabled="!filteredContratos.length">📄 CSV</button>
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

      <!-- Filtros -->
      <div class="filtros-card">
        <div class="filtros-grid">
          <div class="filtro-item">
            <label>Buscar</label>
            <input v-model="searchQuery" type="text" placeholder="Proveedor, tipo, cobertura..." class="input" />
          </div>
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
            <button v-if="tieneFiltrosActivos" class="btn btn-link" @click="limpiarFiltros">Limpiar</button>
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
              <th>Equipos</th>
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
                  <div class="text-muted">→ {{ formatFecha(c.fecha_fin) }}</div>
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
              <td>
                <span v-if="c.equipos && c.equipos.length" class="equipos-count">
                  {{ c.equipos.length }} equipo(s)
                </span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="acciones-col">
                <button class="btn-icon" title="Ver detalle" @click="verDetalle(c)">👁</button>
                <button class="btn-icon" title="Editar" @click="abrirEditar(c)">✏️</button>
                <button class="btn-icon btn-icon-danger" title="Eliminar" @click="eliminarContrato(c)">🗑</button>
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
              <select v-model="formData.moneda" class="input">
                <option v-for="m in monedas" :key="m" :value="m">{{ m }}</option>
              </select>
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
              <label>Equipos Asociados</label>
              <div class="equipos-checkbox-grid">
                <label v-for="eq in equipos" :key="eq.id" class="checkbox-item">
                  <input type="checkbox" :value="eq.id" v-model="formData.equipos_ids" />
                  <span>{{ eq.nombre_corto || eq.modelo }} <small v-if="eq.numero_serie" class="text-muted">({{ eq.numero_serie }})</small></span>
                </label>
                <p v-if="!equipos.length" class="text-muted">No hay equipos registrados.</p>
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
                  <small v-if="eq.modelo" class="text-muted">— {{ eq.modelo }}</small>
                  <small v-if="eq.numero_serie" class="text-muted">SN: {{ eq.numero_serie }}</small>
                  <small v-if="eq.ubicacion_actual" class="text-muted">📍 {{ eq.ubicacion_actual }}</small>
                </div>
              </div>
              <span v-else class="text-muted">Sin equipos asociados</span>
            </div>
          </div>
        </div>
        <div class="modal-footer">
          <button class="btn btn-danger" @click="eliminarContrato(selectedContrato)">🗑 Eliminar</button>
          <button class="btn btn-primary" @click="abrirEditar(selectedContrato); showDetailModal = false">✏️ Editar</button>
          <button class="btn btn-secondary" @click="showDetailModal = false">Cerrar</button>
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
  padding: 0.45rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  font-size: 0.9rem;
  font-family: inherit;
  background: white;
}

.input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
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

.btn-danger { background: #ef4444; color: white; }
.btn-danger:hover:not(:disabled) { background: #dc2626; }

.btn-link {
  background: transparent;
  color: #3b82f6;
  padding: 0.5rem;
}

.btn-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 1rem;
  padding: 0.2rem 0.35rem;
  border-radius: 4px;
  transition: background 0.15s;
}

.btn-icon:hover { background: #f1f5f9; }
.btn-icon-danger:hover { background: #fee2e2; }

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

textarea.input {
  resize: vertical;
  min-height: 50px;
  font-family: inherit;
}

.equipos-checkbox-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 0.35rem;
  max-height: 180px;
  overflow-y: auto;
  border: 1px solid #e2e8f0;
  border-radius: 4px;
  padding: 0.5rem;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  cursor: pointer;
  padding: 0.2rem;
}

.checkbox-item:hover { background: #f8fafc; border-radius: 3px; }

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

.equipos-lista {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
  margin-top: 0.25rem;
}

.equipo-tag {
  background: #f1f5f9;
  padding: 0.5rem 0.7rem;
  border-radius: 4px;
  font-size: 0.85rem;
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: baseline;
}

@media (max-width: 768px) {
  .form-grid { grid-template-columns: 1fr; }
  .detalle-grid { grid-template-columns: 1fr; }
  .page-header { flex-direction: column; align-items: stretch; }
  .header-actions { justify-content: stretch; }
  .header-actions .btn { flex: 1; justify-content: center; }
}
</style>
