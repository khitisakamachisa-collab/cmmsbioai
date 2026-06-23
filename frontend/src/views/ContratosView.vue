<script setup>
import { ref, computed, onMounted } from 'vue'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
import { exportToExcelHTML } from '../services/export.js'  // v0.9.3: RF13

// --- Variables Generales ---
const contratos = ref([])
const proveedores = ref([])
const equipos = ref([])
const loading = ref(true)
const errorMsg = ref('')

const PAGE_SIZE = 10
const currentPage = ref(1)
const searchQuery = ref('')

// --- Filtros ---
const filterProveedor = ref('')
const filterVigencia = ref('')

// --- Modal ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})

// --- Constantes ---
const TIPOS_CONTRATO = [
  'Comodato', 'Mantenimiento Preventivo', 'Mantenimiento Correctivo',
  'Leasing', 'Garantía Extendida', 'Soporte Técnico', 'Servicio Integral', 'Otro'
]
const PERIODICIDADES = ['Único', 'Mensual', 'Trimestral', 'Semestral', 'Anual']
const MONEDAS = ['USD', 'EUR', 'BOB', 'MXN', 'ARS', 'CLP', 'COP', 'PEN', 'BRL', 'Otro']

// --- Computados ---
const filteredContratos = computed(() => {
  let result = contratos.value
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    result = result.filter(c =>
      c.tipo_contrato?.toLowerCase().includes(q) ||
      c.proveedor_nombre?.toLowerCase().includes(q)
    )
  }
  if (filterProveedor.value) {
    result = result.filter(c => c.proveedor_id == filterProveedor.value)
  }
  if (filterVigencia.value === 'vigente') {
    result = result.filter(c => c.activo === true)
  } else if (filterVigencia.value === 'vencido') {
    result = result.filter(c => c.activo === false && c.dias_restantes < 0)
  } else if (filterVigencia.value === 'proximo') {
    result = result.filter(c => c.activo === true && c.dias_restantes <= 30)
  }
  return result
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredContratos.value.length / PAGE_SIZE)))

const tieneFiltros = computed(() => searchQuery.value.trim() || filterProveedor.value || filterVigencia.value)

// --- Fetch ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resContratos, resProveedores, resEquipos] = await Promise.all([
      apiClient.get('/contratos/'),
      apiClient.get('/proveedores/'),
      apiClient.get('/equipos/')
    ])
    contratos.value = resContratos.data
    proveedores.value = resProveedores.data
    equipos.value = resEquipos.data
  } catch (e) {
    errorMsg.value = 'Error al cargar datos'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// --- Helpers ---
const getProveedorNombre = (id) => {
  const p = proveedores.value.find(p => p.id === id)
  return p ? p.nombre_empresa : 'N/A'
}

const getVigenciaBadge = (contrato) => {
  if (contrato.activo === true) {
    if (contrato.dias_restantes <= 30) return { text: `Por vencer (${contrato.dias_restantes}d)`, class: 'badge-vencer' }
    return { text: 'Vigente', class: 'badge-vigente' }
  }
  if (contrato.dias_restantes < 0) return { text: 'Vencido', class: 'badge-vencido' }
  return { text: 'No iniciado', class: 'badge-no-iniciado' }
}

const formatMoneda = (monto, moneda) => {
  if (monto == null) return '—'
  const simbolos = { USD: '$', EUR: '€', BOB: 'Bs', MXN: '$', ARS: '$', CLP: '$', COP: '$', PEN: 'S/', BRL: 'R$', Otro: '' }
  return `${simbolos[moneda] || ''} ${Number(monto).toFixed(2)}`
}

const formatFecha = (fecha) => {
  if (!fecha) return '—'
  return new Date(fecha).toLocaleDateString('es-BO')
}

// --- CRUD ---
const openCreateModal = () => {
  isEditing.value = false
  formData.value = {
    proveedor_id: '',
    tipo_contrato: 'Mantenimiento Preventivo',
    fecha_inicio: '',
    fecha_fin: '',
    costo_total: null,
    costo_periodico: null,
    periodicidad_costo: 'Único',
    moneda: 'USD',
    cobertura_detalle: '',
    tiempo_respuesta: '',
    horario_servicio: '',
    notas: '',
    equipos_ids: []
  }
  showModal.value = true
}

const openEditModal = async (contrato) => {
  try {
    const res = await apiClient.get(`/contratos/${contrato.id}`)
    const full = res.data
    isEditing.value = true
    formData.value = {
      id: full.id,
      proveedor_id: full.proveedor_id,
      tipo_contrato: full.tipo_contrato,
      fecha_inicio: full.fecha_inicio?.substring(0, 10),
      fecha_fin: full.fecha_fin?.substring(0, 10),
      costo_total: full.costo_total,
      costo_periodico: full.costo_periodico,
      periodicidad_costo: full.periodicidad_costo,
      moneda: full.moneda,
      cobertura_detalle: full.cobertura_detalle || '',
      tiempo_respuesta: full.tiempo_respuesta || '',
      horario_servicio: full.horario_servicio || '',
      notas: full.notas || '',
      equipos_ids: full.equipos?.map(e => e.id) || []
    }
    showModal.value = true
  } catch (e) {
    alert('Error al cargar contrato')
    console.error(e)
  }
}

const saveContrato = async () => {
  try {
    const payload = { ...formData.value }
    if (payload.costo_total === '' || payload.costo_total === null) payload.costo_total = null
    if (payload.costo_periodico === '' || payload.costo_periodico === null) payload.costo_periodico = null
    if (payload.equipos_ids?.length === 0) payload.equipos_ids = null

    if (isEditing.value) {
      await apiClient.put(`/contratos/${payload.id}`, payload)
      alert('Contrato actualizado')
    } else {
      await apiClient.post('/contratos/', payload)
      alert('Contrato creado')
    }
    showModal.value = false
    fetchData()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Error al guardar'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
    console.error(e)
  }
}

const deleteContrato = async (id) => {
  if (!confirm('¿Eliminar este contrato y sus asociaciones con equipos?')) return
  try {
    await apiClient.delete(`/contratos/${id}`)
    alert('Contrato eliminado')
    fetchData()
  } catch (e) {
    alert('Error al eliminar')
    console.error(e)
  }
}

const limpiarFiltros = () => {
  searchQuery.value = ''
  filterProveedor.value = ''
  filterVigencia.value = ''
}

// v0.9.3: Exportar contratos filtrados a Excel (RF13)
const exportarContratos = () => {
  const data = filteredContratos.value.map(c => ({
    ...c,
    proveedor_nombre: c.proveedor_nombre || getProveedorNombre(c.proveedor_id),
    estado_vigencia: c.activo ? 'Vigente' : (c.dias_restantes < 0 ? 'Vencido' : 'No iniciado'),
    equipos_nombres: c.equipos?.map(e => e.nombre_corto).join('; ') || ''
  }))
  const columns = [
    { key: 'id', label: 'ID' },
    { key: 'proveedor_nombre', label: 'Proveedor' },
    { key: 'tipo_contrato', label: 'Tipo' },
    { key: 'fecha_inicio', label: 'Fecha Inicio' },
    { key: 'fecha_fin', label: 'Fecha Fin' },
    { key: 'estado_vigencia', label: 'Vigencia' },
    { key: 'dias_restantes', label: 'Dias Restantes' },
    { key: 'costo_total', label: 'Costo Total' },
    { key: 'moneda', label: 'Moneda' },
    { key: 'periodicidad_costo', label: 'Periodicidad' },
    { key: 'cobertura_detalle', label: 'Cobertura' },
    { key: 'tiempo_respuesta', label: 'Tiempo Respuesta' },
    { key: 'equipos_nombres', label: 'Equipos Cubiertos' },
    { key: 'notas', label: 'Notas' },
  ]
  exportToExcelHTML(data, columns, 'CMMS-BioAI_Contratos')
}

onMounted(() => { fetchData() })
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />
    <main class="content">
      <div class="top-bar">
        <h2>Gestión de Contratos</h2>
        <div class="top-bar-actions">
          <div class="search-wrapper">
            <input v-model="searchQuery" type="search" class="search-input"
              placeholder="Tipo, proveedor..." autocomplete="off" />
          </div>
          <button class="btn-export" @click="exportarContratos" title="Exportar lista filtrada a Excel">📤 Exportar</button>
          <button class="btn-primary" @click="openCreateModal">+ Nuevo Contrato</button>
        </div>
      </div>

      <!-- Filtros -->
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Proveedor:</label>
          <select v-model="filterProveedor" class="filter-select">
            <option value="">Todos</option>
            <option v-for="p in proveedores" :key="p.id" :value="p.id">{{ p.nombre_empresa }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Vigencia:</label>
          <select v-model="filterVigencia" class="filter-select">
            <option value="">Todos</option>
            <option value="vigente">Vigentes</option>
            <option value="vencido">Vencidos</option>
            <option value="proximo">Por vencer (30d)</option>
          </select>
        </div>
        <button v-if="tieneFiltros" class="btn-clear-filters" @click="limpiarFiltros">Limpiar</button>
        <span v-if="tieneFiltros" class="filter-count">{{ filteredContratos.length }} de {{ contratos.length }}</span>
      </div>

      <div v-if="loading">Cargando contratos...</div>
      <div v-if="errorMsg" class="error">{{ errorMsg }}</div>

      <table v-if="!loading && contratos.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Proveedor</th>
            <th>Tipo</th>
            <th>Vigencia</th>
            <th>Estado</th>
            <th>Equipos</th>
            <th>Costo</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredContratos.length">
            <td colspan="8" class="empty-cell">No hay contratos que coincidan.</td>
          </tr>
          <tr v-for="c in filteredContratos.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)" :key="c.id">
            <td>#{{ c.id }}</td>
            <td><strong>{{ c.proveedor_nombre }}</strong></td>
            <td>{{ c.tipo_contrato }}</td>
            <td>{{ formatFecha(c.fecha_inicio) }} - {{ formatFecha(c.fecha_fin) }}</td>
            <td>
              <span :class="getVigenciaBadge(c).class">{{ getVigenciaBadge(c).text }}</span>
            </td>
            <td>{{ c.equipos?.length || 0 }}</td>
            <td>{{ formatMoneda(c.costo_total, c.moneda) }}</td>
            <td class="actions-cell">
              <button class="btn-icon" title="Editar" @click="openEditModal(c)">✏️</button>
              <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteContrato(c.id)">🗑️</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && !contratos.length" class="empty-state">
        No hay contratos registrados. Haga clic en "Nuevo Contrato" para comenzar.
      </div>

      <div v-if="!loading && filteredContratos.length" class="table-pagination">
        <button class="btn-pagination" :disabled="currentPage <= 1" @click="currentPage--">Anterior</button>
        <span>Página {{ currentPage }} de {{ totalPages }}</span>
        <button class="btn-pagination" :disabled="currentPage >= totalPages" @click="currentPage++">Siguiente</button>
      </div>
    </main>

    <!-- Modal Crear/Editar -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal" style="max-width: 650px;">
        <h3>{{ isEditing ? 'Editar Contrato' : 'Nuevo Contrato' }}</h3>
        <form @submit.prevent="saveContrato">
          <div class="form-group">
            <label>Proveedor *</label>
            <select v-model="formData.proveedor_id" required>
              <option value="">— Seleccionar —</option>
              <option v-for="p in proveedores" :key="p.id" :value="p.id">{{ p.nombre_empresa }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Tipo de Contrato *</label>
              <select v-model="formData.tipo_contrato" required>
                <option v-for="t in TIPOS_CONTRATO" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Moneda</label>
              <select v-model="formData.moneda">
                <option v-for="m in MONEDAS" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Fecha Inicio *</label>
              <input v-model="formData.fecha_inicio" type="date" required>
            </div>
            <div class="form-group">
              <label>Fecha Fin *</label>
              <input v-model="formData.fecha_fin" type="date" required>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Costo Total</label>
              <input v-model="formData.costo_total" type="number" step="0.01" min="0" placeholder="0.00">
            </div>
            <div class="form-group">
              <label>Costo Periódico</label>
              <input v-model="formData.costo_periodico" type="number" step="0.01" min="0" placeholder="0.00">
            </div>
            <div class="form-group">
              <label>Periodicidad</label>
              <select v-model="formData.periodicidad_costo">
                <option v-for="p in PERIODICIDADES" :key="p" :value="p">{{ p }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Tiempo de Respuesta</label>
              <input v-model="formData.tiempo_respuesta" type="text" placeholder="Ej: 24 hs, 48 hs">
            </div>
            <div class="form-group">
              <label>Horario de Servicio</label>
              <input v-model="formData.horario_servicio" type="text" placeholder="Ej: Lun-Vie 8-18hs">
            </div>
          </div>
          <div class="form-group">
            <label>Cobertura</label>
            <textarea v-model="formData.cobertura_detalle" rows="2" placeholder="Qué incluye el contrato..."></textarea>
          </div>
          <div class="form-group">
            <label>Equipos Cubiertos</label>
            <div class="equipos-checkbox-grid">
              <label v-for="eq in equipos" :key="eq.id" class="checkbox-label">
                <input type="checkbox" :value="eq.id" v-model="formData.equipos_ids">
                {{ eq.nombre_corto || eq.modelo }} ({{ eq.numero_serie }})
              </label>
            </div>
          </div>
          <div class="form-group">
            <label>Notas</label>
            <textarea v-model="formData.notas" rows="2" placeholder="Observaciones..."></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 0.75rem; margin-bottom: 1rem; }
.top-bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }
.search-input { padding: 0.55rem 0.85rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9rem; min-width: 200px; }
.search-input:focus { outline: none; border-color: #3498db; }

.filter-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; margin-bottom: 1rem; padding: 0.75rem 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.filter-group { display: flex; align-items: center; gap: 0.35rem; }
.filter-label { font-size: 0.82rem; font-weight: 600; color: #64748b; }
.filter-select { padding: 0.35rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.82rem; min-width: 120px; }
.btn-clear-filters { padding: 0.35rem 0.7rem; border: 1px solid #fecaca; border-radius: 6px; background: #fef2f2; color: #dc2626; font-size: 0.78rem; font-weight: 600; cursor: pointer; }
.filter-count { font-size: 0.78rem; font-weight: 600; color: #64748b; background: #f1f5f9; padding: 0.25rem 0.5rem; border-radius: 4px; }

table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; font-size: 0.88rem; }
th { background: #f8f9fa; font-weight: bold; }
.empty-cell { text-align: center; color: #64748b; padding: 1.5rem; }
.empty-state { text-align: center; padding: 2.5rem; color: #64748b; }

.badge-vigente { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #16a34a; }
.badge-vencer { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #1e293b; background: #fbbf24; }
.badge-vencido { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #dc2626; }
.badge-no-iniciado { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #64748b; }

.actions-cell { display: flex; gap: 0.5rem; }
.btn-icon { background: #f0f2f5; border: none; padding: 6px 8px; border-radius: 6px; cursor: pointer; font-size: 1rem; }
.btn-icon:hover { background: #dfe2e6; }
.btn-danger-icon:hover { background: #fee2e2; }

.table-pagination { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-top: 1rem; }
.btn-pagination { background: #3498db; color: white; border: none; padding: 0.5rem 1.1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem; }
.btn-pagination:disabled { opacity: 0.45; cursor: not-allowed; }
.btn-pagination:hover:not(:disabled) { background: #2980b9; }

.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; padding: 1rem; }
.modal { background: white; padding: 1.5rem; border-radius: 8px; width: 100%; max-width: 550px; max-height: 90vh; overflow-y: auto; box-shadow: 0 10px 25px rgba(0,0,0,0.2); }
.modal h3 { margin: 0 0 1rem 0; color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
.form-group { margin-bottom: 0.85rem; }
.form-group label { display: block; margin-bottom: 0.3rem; font-weight: 600; color: #334155; font-size: 0.88rem; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.5rem 0.7rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; font-family: inherit; }
.form-group input:focus, .form-group select:focus, .form-group textarea:focus { outline: none; border-color: #3498db; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
.form-row:has(.form-group:nth-child(3)) { grid-template-columns: 1fr 1fr 1fr; }
@media (max-width: 600px) { .form-row { grid-template-columns: 1fr !important; } }

.equipos-checkbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 0.35rem; max-height: 150px; overflow-y: auto; padding: 0.5rem; border: 1px solid #e2e8f0; border-radius: 6px; background: #f8fafc; }
.checkbox-label { display: flex; align-items: center; gap: 0.35rem; font-size: 0.82rem; color: #334155; cursor: pointer; }
.checkbox-label input { width: auto; }

.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
.btn-primary { background: #3498db; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-primary:hover { background: #2980b9; }
.btn-export { background: #f0fdf4; color: #16a34a; border: 1px solid #86efac; padding: 0.45rem 0.9rem; border-radius: 4px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
.btn-export:hover { background: #dcfce7; }
.btn-secondary { background: #95a5a6; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-secondary:hover { background: #7f8c8d; }

.error { color: #dc2626; background: #fef2f2; padding: 0.75rem; border-radius: 6px; margin: 1rem 0; }
</style>
