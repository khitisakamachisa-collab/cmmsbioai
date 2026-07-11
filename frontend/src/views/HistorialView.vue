<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'

// --- Variables Generales ---
const eventos = ref([])
const equipos = ref([])
const tecnicos = ref([])
const loading = ref(true)
const error_msg = ref('')

const PAGE_SIZE = 12
const currentPage = ref(1)
const searchQuery = ref('')
const filtroEquipo = ref('')
const filtroTipo = ref('')

// --- Variables Modal Detalle ---
const showDetailModal = ref(false)
const selectedEvento = ref({})

// --- Variables Modal Crear Evento Manual ---
const showCreateModal = ref(false)
const formData = ref({})

// --- Funciones de Datos ---
const fetchEventos = async () => {
  try {
    loading.value = true
    const params = {}
    if (filtroEquipo.value) params.equipo_id = filtroEquipo.value
    const response = await apiClient.get('/historial/', { params })
    eventos.value = response.data
  } catch (error) {
    error_msg.value = 'Error al cargar historial'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchEquipos = async () => {
  try {
    const response = await apiClient.get('/equipos/')
    equipos.value = response.data
  } catch (error) {
    console.error('Error al cargar equipos', error)
  }
}

const fetchTecnicos = async () => {
  try {
    const response = await apiClient.get('/users/')
    tecnicos.value = response.data
  } catch (error) {
    console.error('Error al cargar técnicos', error)
  }
}

// --- Filtros y Paginación ---
const filteredEventos = computed(() => {
  let result = eventos.value

  if (filtroTipo.value) {
    result = result.filter(e => e.tipo_evento === filtroTipo.value)
  }

  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    result = result.filter(e => {
      const desc = String(e.descripcion ?? '').toLowerCase()
      const equipo = String(e.equipo_nombre ?? '').toLowerCase()
      const tecnico = String(e.tecnico_nombre ?? '').toLowerCase()
      const repuestos = String(e.repuestos_utilizados ?? '').toLowerCase()
      const acciones = String(e.acciones_realizadas ?? '').toLowerCase()
      return desc.includes(q) || equipo.includes(q) || tecnico.includes(q) || repuestos.includes(q) || acciones.includes(q)
    })
  }

  return result
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredEventos.value.length / PAGE_SIZE))
)

watch(() => filteredEventos.value.length, (len) => {
  const tp = Math.max(1, Math.ceil(len / PAGE_SIZE))
  if (currentPage.value > tp) currentPage.value = tp
})

watch(searchQuery, () => { currentPage.value = 1 })

const irPaginaAnterior = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}

const irPaginaSiguiente = () => {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

// --- Helpers ---
const tipoEventoColor = (tipo) => {
  const colors = {
    preventivo: '#27ae60',
    correctivo: '#e74c3c',
    calibracion: '#3498db',
    otro: '#9b59b6'
  }
  return colors[tipo] || '#95a5a6'
}

const tipoEventoIcon = (tipo) => {
  const icons = {
    preventivo: '🔧',
    correctivo: '⚡',
    calibracion: '🎯',
    otro: '📝'
  }
  return icons[tipo] || '📋'
}

const formatDate = (dateStr) => {
  if (!dateStr) return 'N/A'
  const d = new Date(dateStr)
  return d.toLocaleDateString('es-BO', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.nombre_corto || eq.modelo) : 'Desconocido'
}

// --- Modal Detalle ---
const openDetailModal = (evento) => {
  selectedEvento.value = evento
  showDetailModal.value = true
}

// --- Modal Crear Evento Manual ---
const openCreateModal = () => {
  formData.value = {
    equipo_id: '',
    tipo_evento: 'correctivo',
    descripcion: '',
    tecnico_id: null,
    acciones_realizadas: '',
    tiempo_invertido: null,
    costo: null
  }
  showCreateModal.value = true
}

const saveEvento = async () => {
  try {
    const payload = { ...formData.value }
    if (!payload.equipo_id) { alert('Seleccione un equipo'); return }
    if (!payload.descripcion) { alert('Ingrese una descripción'); return }
    if (payload.tecnico_id === '') payload.tecnico_id = null
    if (payload.tiempo_invertido === '' || payload.tiempo_invertido === null) payload.tiempo_invertido = null
    if (payload.costo === '' || payload.costo === null) payload.costo = null

    await apiClient.post('/historial/', payload)
    alert('Evento registrado correctamente')
    showCreateModal.value = false
    fetchEventos()
  } catch (error) {
    console.error(error)
    if (error.response?.data?.detail) {
      alert('Error: ' + error.response.data.detail)
    } else {
      alert('Error al registrar el evento')
    }
  }
}

const deleteEvento = async (id) => {
  if (confirm('¿Está seguro de eliminar este evento del historial?')) {
    try {
      await apiClient.delete(`/historial/${id}`)
      alert('Evento eliminado')
      fetchEventos()
    } catch (error) {
      alert('Error al eliminar')
    }
  }
}

// --- Recargar al cambiar filtro de equipo ---
watch(filtroEquipo, () => {
  currentPage.value = 1
  fetchEventos()
})

onMounted(() => {
  fetchEquipos()
  fetchTecnicos()
  fetchEventos()
})
</script>

<template>
  <div class="dashboard-container">

    <main class="content">
      <div class="top-bar">
        <h2>Historial de Mantenimiento</h2>
        <div class="top-bar-actions">
          <input
            v-model="searchQuery"
            type="search"
            class="search-input"
            placeholder="Buscar en historial..."
            autocomplete="off"
          >
          <select v-model="filtroEquipo" class="filter-select">
            <option value="">Todos los equipos</option>
            <option v-for="eq in equipos" :key="eq.id" :value="eq.id">
              {{ eq.nombre_corto || eq.modelo }}
            </option>
          </select>
          <select v-model="filtroTipo" class="filter-select">
            <option value="">Todos los tipos</option>
            <option value="preventivo">Preventivo</option>
            <option value="correctivo">Correctivo</option>
            <option value="calibracion">Calibración</option>
            <option value="otro">Otro</option>
          </select>
          <button class="btn-primary" @click="openCreateModal">+ Registro Manual</button>
        </div>
      </div>

      <div v-if="loading">Cargando historial...</div>
      <div v-if="error_msg" class="error">{{ error_msg }}</div>

      <!-- Vista Timeline -->
      <div v-if="!loading && filteredEventos.length" class="timeline">
        <div
          v-for="evento in filteredEventos.slice(
            (currentPage - 1) * PAGE_SIZE,
            currentPage * PAGE_SIZE
          )"
          :key="evento.id"
          class="timeline-item"
          :class="'timeline-' + evento.tipo_evento"
        >
          <div class="timeline-marker">
            <span class="timeline-icon">{{ tipoEventoIcon(evento.tipo_evento) }}</span>
          </div>
          <div class="timeline-content">
            <div class="timeline-header">
              <div class="timeline-title-row">
                <span class="timeline-type-badge" :style="{ backgroundColor: tipoEventoColor(evento.tipo_evento) }">
                  {{ evento.tipo_evento.toUpperCase() }}
                </span>
                <span class="timeline-equipo">{{ evento.equipo_nombre || getEquipoNombre(evento.equipo_id) }}</span>
                <span class="timeline-date">{{ formatDate(evento.fecha_evento) }}</span>
              </div>
              <h4 class="timeline-title">{{ evento.descripcion }}</h4>
            </div>
            <div class="timeline-body">
              <div class="timeline-details">
                <div v-if="evento.tecnico_nombre" class="detail-item">
                  <span class="detail-label">Técnico:</span>
                  <span>{{ evento.tecnico_nombre }}</span>
                </div>
                <div v-if="evento.acciones_realizadas" class="detail-item">
                  <span class="detail-label">Acciones:</span>
                  <span>{{ evento.acciones_realizadas }}</span>
                </div>
                <div v-if="evento.tiempo_invertido" class="detail-item">
                  <span class="detail-label">Tiempo:</span>
                  <span>{{ evento.tiempo_invertido }} h</span>
                </div>
                <div v-if="evento.costo" class="detail-item">
                  <span class="detail-label">Costo:</span>
                  <span>Bs {{ evento.costo.toFixed(2) }}</span>
                </div>
                <div v-if="evento.repuestos_utilizados" class="detail-item">
                  <span class="detail-label">Repuestos:</span>
                  <span>{{ evento.repuestos_utilizados }}</span>
                </div>
                <div v-if="evento.ot_titulo" class="detail-item">
                  <span class="detail-label">OT:</span>
                  <span>{{ evento.ot_titulo }}</span>
                </div>
              </div>
            </div>
            <div class="timeline-actions">
              <button class="btn-icon-sm" title="Ver Detalle" @click="openDetailModal(evento)">Detalle</button>
              <button class="btn-icon-sm btn-danger-sm" title="Eliminar" @click="deleteEvento(evento.id)">Eliminar</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && !filteredEventos.length" class="empty-state">
        <p v-if="searchQuery || filtroEquipo || filtroTipo">No se encontraron eventos con los filtros aplicados.</p>
        <p v-else>No hay eventos en el historial. Los eventos se registran automáticamente al completar una Orden de Trabajo.</p>
      </div>

      <!-- Paginación -->
      <div
        v-if="!loading && filteredEventos.length"
        class="table-pagination"
      >
        <button type="button" class="btn-pagination" :disabled="currentPage <= 1" @click="irPaginaAnterior">
          Anterior
        </button>
        <span class="table-pagination-meta">
          Página {{ currentPage }} de {{ totalPages }}
          <span class="table-pagination-range">
            ({{ (currentPage - 1) * PAGE_SIZE + 1 }}–{{ Math.min(currentPage * PAGE_SIZE, filteredEventos.length) }} de {{ filteredEventos.length }})
          </span>
        </span>
        <button type="button" class="btn-pagination" :disabled="currentPage >= totalPages" @click="irPaginaSiguiente">
          Siguiente
        </button>
      </div>
    </main>

    <!-- Modal Detalle del Evento -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal" style="width: 600px;">
        <h3>Detalle del Evento de Mantenimiento</h3>
        <div class="detail-grid">
          <div class="detail-column">
            <h4>Información General</h4>
            <p><strong>Tipo:</strong>
              <span class="timeline-type-badge" :style="{ backgroundColor: tipoEventoColor(selectedEvento.tipo_evento) }">
                {{ selectedEvento.tipo_evento?.toUpperCase() }}
              </span>
            </p>
            <p><strong>Equipo:</strong> {{ selectedEvento.equipo_nombre || 'N/A' }}</p>
            <p><strong>Fecha:</strong> {{ formatDate(selectedEvento.fecha_evento) }}</p>
            <p><strong>Técnico:</strong> {{ selectedEvento.tecnico_nombre || 'No asignado' }}</p>
          </div>
          <div class="detail-column">
            <h4>Datos del Servicio</h4>
            <p><strong>Descripción:</strong> {{ selectedEvento.descripcion }}</p>
            <p v-if="selectedEvento.acciones_realizadas"><strong>Acciones:</strong> {{ selectedEvento.acciones_realizadas }}</p>
            <p v-if="selectedEvento.tiempo_invertido"><strong>Tiempo:</strong> {{ selectedEvento.tiempo_invertido }} horas</p>
            <p v-if="selectedEvento.costo"><strong>Costo:</strong> Bs {{ selectedEvento.costo?.toFixed(2) }}</p>
          </div>
        </div>
        <div v-if="selectedEvento.repuestos_utilizados" class="detail-full">
          <h4>Repuestos Utilizados</h4>
          <p>{{ selectedEvento.repuestos_utilizados }}</p>
        </div>
        <div v-if="selectedEvento.orden_trabajo_id" class="detail-full" style="margin-top: 0.5rem;">
          <p><strong>Orden de Trabajo #{{ selectedEvento.orden_trabajo_id }}</strong>
            <span v-if="selectedEvento.ot_titulo"> — {{ selectedEvento.ot_titulo }}</span>
          </p>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- Modal Crear Evento Manual -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal">
        <h3>Registrar Evento de Mantenimiento</h3>
        <form @submit.prevent="saveEvento">
          <div class="form-group">
            <label>Equipo *</label>
            <select v-model="formData.equipo_id" required>
              <option value="" disabled>Seleccione un equipo</option>
              <option v-for="eq in equipos" :key="eq.id" :value="eq.id">
                {{ eq.nombre_corto || eq.modelo }} ({{ eq.marca }})
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Tipo de Evento *</label>
              <select v-model="formData.tipo_evento" required>
                <option value="preventivo">Preventivo</option>
                <option value="correctivo">Correctivo</option>
                <option value="calibracion">Calibración</option>
                <option value="otro">Otro</option>
              </select>
            </div>
            <div class="form-group">
              <label>Técnico</label>
              <select v-model="formData.tecnico_id">
                <option :value="null">-- Sin Asignar --</option>
                <option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">
                  {{ tec.full_name || tec.username }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Descripción *</label>
            <input v-model="formData.descripcion" type="text" required placeholder="Descripción del evento">
          </div>
          <div class="form-group">
            <label>Acciones Realizadas</label>
            <textarea v-model="formData.acciones_realizadas" rows="3" placeholder="Detalle de las acciones..."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Tiempo Invertido (horas)</label>
              <input v-model="formData.tiempo_invertido" type="number" step="0.5" min="0" placeholder="Ej: 2.5">
            </div>
            <div class="form-group">
              <label>Costo Adicional (Bs)</label>
              <input v-model="formData.costo" type="number" step="0.01" min="0" placeholder="Ej: 150.00">
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCreateModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Registrar Evento</button>
          </div>
        </form>
      </div>
    </div>
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
  margin-bottom: 1.5rem;
}
.top-bar h2 { margin: 0; }
.top-bar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}
.search-input {
  min-width: 200px;
  flex: 1 1 180px;
  max-width: 300px;
  padding: 0.55rem 0.85rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.95rem;
  box-sizing: border-box;
  background: #fff;
}
.search-input::placeholder { color: #94a3b8; }
.search-input:focus {
  outline: none;
  border-color: #3498db;
  box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.2);
}
.filter-select {
  padding: 0.55rem 0.7rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.9rem;
  background: #fff;
  cursor: pointer;
  min-width: 140px;
}
.filter-select:focus {
  outline: none;
  border-color: #3498db;
}

/* === Timeline === */
.timeline {
  position: relative;
  padding-left: 40px;
}
.timeline::before {
  content: '';
  position: absolute;
  left: 18px;
  top: 0;
  bottom: 0;
  width: 3px;
  background: #e2e8f0;
  border-radius: 2px;
}

.timeline-item {
  position: relative;
  margin-bottom: 1.5rem;
}

.timeline-marker {
  position: absolute;
  left: -40px;
  top: 0;
  width: 38px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.timeline-icon {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: white;
  border: 3px solid #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  z-index: 1;
}

.timeline-preventivo .timeline-icon { border-color: #27ae60; background: #f0fdf4; }
.timeline-correctivo .timeline-icon { border-color: #e74c3c; background: #fef2f2; }
.timeline-calibracion .timeline-icon { border-color: #3498db; background: #eff6ff; }
.timeline-otro .timeline-icon { border-color: #9b59b6; background: #faf5ff; }

.timeline-content {
  background: white;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem 1.25rem;
  box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  transition: box-shadow 0.2s;
}
.timeline-content:hover {
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.timeline-header { margin-bottom: 0.5rem; }

.timeline-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.35rem;
}

.timeline-type-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 700;
  color: white;
  letter-spacing: 0.03em;
}

.timeline-equipo {
  font-weight: 600;
  color: #2c3e50;
  font-size: 0.95rem;
}

.timeline-date {
  font-size: 0.8rem;
  color: #64748b;
  margin-left: auto;
}

.timeline-title {
  margin: 0;
  font-size: 1rem;
  color: #1e293b;
}

.timeline-body { margin: 0; }

.timeline-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.25rem 1.25rem;
  font-size: 0.85rem;
  color: #475569;
}

.detail-item {
  display: flex;
  gap: 0.3rem;
}

.detail-label {
  font-weight: 600;
  color: #64748b;
}

.timeline-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.5rem;
  border-top: 1px solid #f1f5f9;
}

.btn-icon-sm {
  background: #f1f5f9;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.78rem;
  color: #475569;
  font-weight: 600;
  transition: all 0.15s;
}
.btn-icon-sm:hover { background: #e2e8f0; color: #1e293b; }
.btn-danger-sm:hover { background: #fee2e2; color: #dc2626; }

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 3rem 1rem;
  font-size: 1rem;
}

/* Paginación */
.table-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1.5rem;
  padding: 0.75rem 0;
}
.table-pagination-meta { font-size: 0.9rem; color: #475569; text-align: center; }
.table-pagination-range { display: block; font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; }
.btn-pagination {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
  transition: background-color 0.2s ease, opacity 0.2s ease;
}
.btn-pagination:hover:not(:disabled) { background-color: #2980b9; }
.btn-pagination:disabled { opacity: 0.45; cursor: not-allowed; }

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; max-width: 90%; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; background-color: white; }
.form-group textarea { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; resize: vertical; font-family: inherit; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 1rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }

/* Detalle */
.detail-grid { display: flex; gap: 2rem; margin-bottom: 1.5rem; }
.detail-column { flex: 1; }
.detail-column h4 { margin-bottom: 0.8rem; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.3rem; }
.detail-column p { margin: 0 0 0.5rem 0; font-size: 0.9rem; color: #555; }
.detail-full { width: 100%; background: #f8f9fa; padding: 1rem; border-radius: 6px; }
.detail-full h4 { margin-top: 0; margin-bottom: 0.5rem; color: #2c3e50; }
.detail-full p { margin: 0; font-size: 0.9rem; color: #555; }

.error { color: #e74c3c; font-weight: bold; margin-bottom: 1rem; }
</style>
