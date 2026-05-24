<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'

// --- Variables Generales ---
const equipos = ref([])
const estados = ref([])
const tecnicos = ref([])
const loading = ref(true)
const error_msg = ref('')

const PAGE_SIZE = 10
const currentPage = ref(1)
const searchQuery = ref('')

// --- Variables Modal ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})

// --- Variables Historial ---
const showHistoryModal = ref(false)
const historyData = ref([])
const selectedEquipName = ref('')

// --- Variables Modal Detalle ---
const showDetailModal = ref(false)
const selectedEquipo = ref({})

// --- Variables Modal Importar Excel ---
const showImportModal = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importDragOver = ref(false)

// Función para abrir el modal de detalles
const openDetailModal = (equipo) => {
  selectedEquipo.value = equipo
  showDetailModal.value = true
}

// Helper para mostrar el nombre del técnico
const getTecnicoName = (id) => {
  if (!id) return 'Sin Asignar'
  const tec = tecnicos.value.find(t => t.id === id)
  return tec ? (tec.full_name || tec.username) : 'Desconocido'
}

// --- Funciones de Datos (Fetch) ---
const fetchEquipos = async () => {
  try {
    loading.value = true
    const response = await apiClient.get('/equipos/')
    equipos.value = response.data
  } catch (error) {
    error_msg.value = 'Error al cargar equipos'
    console.error(error)
  } finally {
    loading.value = false
  }
}

const fetchEstados = async () => {
  try {
    const response = await apiClient.get('/equipos/estados')
    estados.value = response.data
  } catch (error) {
    console.error('Error al cargar estados', error)
  }
}

const fetchTecnicos = async () => {
  try {
    const response = await apiClient.get('users')
    tecnicos.value = response.data
  } catch (error) {
    console.error('Error al cargar técnicos', error)
  }
}

const filteredEquipos = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return equipos.value
  return equipos.value.filter((eq) => {
    const nombre = String(eq.nombre_corto ?? '').toLowerCase()
    const marca = String(eq.marca ?? '').toLowerCase()
    const modelo = String(eq.modelo ?? '').toLowerCase()
    return nombre.includes(q) || marca.includes(q) || modelo.includes(q)
  })
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredEquipos.value.length / PAGE_SIZE))
)

watch(
  () => filteredEquipos.value.length,
  (len) => {
    const tp = Math.max(1, Math.ceil(len / PAGE_SIZE))
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

// --- Funciones del Modal ---
const openCreateModal = () => {
  isEditing.value = false
  formData.value = {
    nombre_corto: '',
    modelo: '',
    numero_serie: '',
    marca: '',
    fecha_adquisicion: '',
    ubicacion_actual: '',
    estado_id: 1,
    registro_sanitario_bolivia: '',
    proveedor_principal: '',
    descripcion: '',
    calibracion_proxima: '',
    responsable_tecnico_id: null
  }
  showModal.value = true
}

const openEditModal = (equipo) => {
  isEditing.value = true
  formData.value = { ...equipo }
  
  if (equipo.fecha_adquisicion) {
    formData.value.fecha_adquisicion = equipo.fecha_adquisicion.substring(0, 10)
  }
  if (equipo.calibracion_proxima) {
    formData.value.calibracion_proxima = equipo.calibracion_proxima.substring(0, 10)
  } else {
    formData.value.calibracion_proxima = ''
  }
  
  showModal.value = true
}

const saveEquipo = async () => {
  try {
    const payload = { ...formData.value };

    if (payload.fecha_adquisicion === "") payload.fecha_adquisicion = null;
    if (payload.calibracion_proxima === "") payload.calibracion_proxima = null;
    if (payload.responsable_tecnico_id === "") payload.responsable_tecnico_id = null;

    if (isEditing.value) {
      await apiClient.put(`/equipos/${payload.id}`, payload)
      alert('Equipo actualizado')
    } else {
      await apiClient.post('/equipos/', payload)
      alert('Equipo creado')
    }
    showModal.value = false
    fetchEquipos() 
  } catch (error) {
    console.error(error.response)
    if (error.response && error.response.data && error.response.data.detail) {
        const details = error.response.data.detail;
        if (Array.isArray(details)) {
            alert(`Error de validación: ${details[0].msg} en campo ${details[0].loc.join('-')}`);
        } else {
            alert('Error: ' + details);
        }
    } else {
        alert('Error desconocido al guardar');
    }
  }
}

const deleteEquipo = async (id) => {
  if (confirm("¿Estás seguro de eliminar este equipo?")) {
    try {
      await apiClient.delete(`/equipos/${id}`)
      alert('Equipo eliminado')
      fetchEquipos()
    } catch (error) {
      alert('Error al eliminar')
    }
  }
}

// --- Función Historial ---
const openHistory = async (equipo) => {
  selectedEquipName.value = equipo.nombre_corto || equipo.modelo
  try {
    const res = await apiClient.get(`/ordenes/?equipo_id=${equipo.id}`)
    historyData.value = res.data
    showHistoryModal.value = true
  } catch (error) {
    console.error("Error al cargar historial", error)
  }
}

// --- Funciones Importar Excel ---
const openImportModal = () => {
  importFile.value = null
  importResult.value = null
  importing.value = false
  importDragOver.value = false
  showImportModal.value = true
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    importFile.value = file
    importResult.value = null
  }
}

const handleDragOver = (e) => {
  e.preventDefault()
  importDragOver.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  importDragOver.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  importDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    importFile.value = file
    importResult.value = null
  }
}

const downloadTemplate = async () => {
  try {
    const response = await apiClient.get('/equipos/plantilla-excel', {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const contentDisposition = response.headers['content-disposition']
    let filename = 'CMMS-BioAI_Plantilla_Equipos.xlsx'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+?)"?$/)
      if (match) filename = match[1]
    }
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('Error al descargar la plantilla')
    console.error(error)
  }
}

const uploadExcel = async () => {
  if (!importFile.value) {
    alert('Seleccione un archivo primero')
    return
  }
  if (!importFile.value.name.toLowerCase().endsWith('.xlsx')) {
    alert('Solo se aceptan archivos .xlsx')
    return
  }
  try {
    importing.value = true
    importResult.value = null
    const formData = new FormData()
    formData.append('file', importFile.value)
    const response = await apiClient.post('/equipos/import-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    importResult.value = response.data
    fetchEquipos() // Refrescar la lista
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      alert('Error: ' + error.response.data.detail)
    } else {
      alert('Error al importar el archivo')
    }
    console.error(error)
  } finally {
    importing.value = false
  }
}

const resetImport = () => {
  importFile.value = null
  importResult.value = null
}

// --- Helpers para Vista ---
const getNombreEstado = (id) => {
  const estado = estados.value.find(e => e.id === id)
  return estado ? estado.nombre_estado : 'Desconocido'
}

const getEstadoColor = (id) => {
  const estado = estados.value.find(e => e.id === id)
  return estado ? estado.color : '#95a5a6'
}

onMounted(() => {
  fetchEquipos()
  fetchEstados()
  fetchTecnicos()
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Gestión de Equipos Médicos</h2>
        <div class="top-bar-actions">
          <input
            v-model="searchQuery"
            type="search"
            class="search-input"
            placeholder="Buscar por nombre, marca o modelo..."
            autocomplete="off"
            aria-label="Buscar equipos por nombre, marca o modelo"
          >
          <button class="btn-import" @click="openImportModal" title="Cargar equipos desde Excel">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
            </svg>
            Cargar Excel
          </button>
          <button class="btn-primary" @click="openCreateModal">+ Nuevo Equipo</button>
        </div>
      </div>
      
      <div v-if="loading">Cargando equipos...</div>
      <div v-if="error_msg" class="error">{{ error_msg }}</div>

      <table v-if="!loading && equipos.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Modelo</th>
            <th>Marca</th>
            <th>Ubicación</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredEquipos.length">
            <td class="table-empty-cell" colspan="7">
              {{ searchQuery.trim() ? 'No hay equipos que coincidan con la búsqueda.' : 'No hay equipos para mostrar.' }}
            </td>
          </tr>
          <template v-else>
            <tr
              v-for="equipo in filteredEquipos.slice(
                (currentPage - 1) * PAGE_SIZE,
                currentPage * PAGE_SIZE
              )"
              :key="equipo.id"
            >
            <td>{{ equipo.id }}</td>
            <td>
              <span
                class="equipo-nombre-link"
                role="button"
                tabindex="0"
                @click="openDetailModal(equipo)"
                @keydown.enter.prevent="openDetailModal(equipo)"
                @keydown.space.prevent="openDetailModal(equipo)"
              >{{ equipo.nombre_corto || 'N/A' }}</span>
            </td>
            <td>{{ equipo.modelo }}</td>
            <td>{{ equipo.marca }}</td>
            <td>{{ equipo.ubicacion_actual }}</td>
            <td>
              <span class="badge" :style="{ backgroundColor: getEstadoColor(equipo.estado_id) }">
                {{ getNombreEstado(equipo.estado_id) }}
              </span>
            </td>
            <td class="actions-cell">
              <button class="btn-icon" title="Ver Detalles" @click="openDetailModal(equipo)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                </svg>
              </button>
              <button class="btn-icon" title="Editar" @click="openEditModal(equipo)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                </svg>
              </button>
              <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteEquipo(equipo.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                  <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
              </button>
              <button class="btn-icon btn-secondary-icon" title="Ver Historial" @click="openHistory(equipo)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
                  <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
                </svg>
              </button>
            </td>
          </tr>
          </template>
        </tbody>
      </table>

      <div
        v-if="!loading && equipos.length && filteredEquipos.length"
        class="table-pagination"
        role="navigation"
        aria-label="Paginación del listado de equipos"
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
          <span class="table-pagination-range">
            ({{ (currentPage - 1) * PAGE_SIZE + 1 }}–{{ Math.min(currentPage * PAGE_SIZE, filteredEquipos.length) }} de {{ filteredEquipos.length }})
          </span>
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

    <!-- Modal Importar Excel -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal" style="width: 580px;">
        <h3>Importar Equipos desde Excel</h3>

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
              <p class="drop-zone-text">Arrastre su archivo Excel aquí</p>
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
          <input ref="fileInput" type="file" accept=".xlsx" style="display: none;" @change="handleFileSelect">

          <div class="import-info">
            <p><strong>Formato:</strong> Archivo .xlsx con encabezados en la primera fila.</p>
            <p><strong>Columnas obligatorias:</strong> modelo, numero_serie, marca, fecha_adquisicion</p>
            <p>Si el numero_serie ya existe, el equipo se <strong>actualizará</strong> con los nuevos datos.</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showImportModal = false">Cancelar</button>
            <button type="button" class="btn-outline" @click="downloadTemplate" title="Descargar plantilla con datos de ejemplo">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
              </svg>
              Descargar Plantilla
            </button>
            <button type="button" class="btn-primary" :disabled="!importFile" @click="uploadExcel">
              Importar
            </button>
          </div>
        </div>

        <!-- Paso 2: Procesando -->
        <div v-if="importing" class="import-progress">
          <div class="spinner"></div>
          <p style="text-align: center; color: #475569;">Importando equipos...</p>
        </div>

        <!-- Paso 3: Resultados -->
        <div v-if="importResult && !importing">
          <div class="import-result">
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

            <!-- Errores detallados -->
            <div v-if="importResult.errores && importResult.errores.length > 0" class="import-errors">
              <h4>Detalle de errores</h4>
              <div class="error-list">
                <div v-for="(err, idx) in importResult.errores" :key="idx" class="error-item">
                  <span class="error-fila">Fila {{ err.fila }}</span>
                  <span class="error-serie">(Serie: {{ err.numero_serie }})</span>
                  <span class="error-msg">{{ err.errores.join(', ') }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="resetImport">Importar otro archivo</button>
            <button type="button" class="btn-primary" @click="showImportModal = false">Cerrar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear/Editar Equipo -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Equipo' : 'Registrar Nuevo Equipo' }}</h3>
        <form @submit.prevent="saveEquipo">
          <div class="form-group">
            <label>Nombre Corto</label>
            <input v-model="formData.nombre_corto" type="text" placeholder="Ej: Monitor UCI 02">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Marca *</label>
              <input v-model="formData.marca" type="text" required>
            </div>
            <div class="form-group">
              <label>Modelo *</label>
              <input v-model="formData.modelo" type="text" required>
            </div>
          </div>
          <div class="form-group">
            <label>Número de Serie *</label>
            <input v-model="formData.numero_serie" type="text" required placeholder="Único">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Fecha Adquisición *</label>
              <input v-model="formData.fecha_adquisicion" type="date" required>
            </div>
            <div class="form-group">
              <label>Próxima Calibración</label>
              <input v-model="formData.calibracion_proxima" type="date">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Ubicación</label>
              <input v-model="formData.ubicacion_actual" type="text" placeholder="Ej: UCI Box 5">
            </div>
            <div class="form-group">
              <label>Estado del Equipo</label>
              <select v-model="formData.estado_id" required>
                <option v-for="estado in estados" :key="estado.id" :value="estado.id">
                  {{ estado.nombre_estado }}
                </option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Registro Sanitario</label>
              <input v-model="formData.registro_sanitario_bolivia" type="text" placeholder="Código o N/A">
            </div>
            <div class="form-group">
              <label>Proveedor</label>
              <input v-model="formData.proveedor_principal" type="text" placeholder="Empresa proveedora">
            </div>
          </div>
          <div class="form-group">
            <label>Técnico Responsable (Opcional)</label>
            <select v-model="formData.responsable_tecnico_id">
              <option :value="null">-- Sin Asignar --</option>
              <option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">
                {{ tec.full_name || tec.username }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label>Descripción / Notas</label>
            <textarea v-model="formData.descripcion" rows="3" placeholder="Detalles adicionales del equipo..."></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Historial -->
    <div v-if="showHistoryModal" class="modal-overlay" @click.self="showHistoryModal = false">
      <div class="modal" style="width: 800px;">
        <h3>Historial de Mantenimiento: {{ selectedEquipName }}</h3>
        <div v-if="historyData.length === 0" class="empty-state">
          Este equipo no tiene registros de mantenimiento aún.
        </div>
        <table v-else class="history-table">
          <thead>
            <tr>
              <th>Fecha</th>
              <th>Título</th>
              <th>Problema</th>
              <th>Solución</th>
              <th>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="ot in historyData" :key="ot.id">
              <td>{{ new Date(ot.fecha_creacion).toLocaleDateString() }}</td>
              <td><strong>{{ ot.titulo }}</strong></td>
              <td style="font-size: 0.85rem">{{ ot.descripcion_falla }}</td>
              <td style="font-size: 0.85rem; color: green">
                {{ ot.acciones_realizadas || 'Pendiente' }}
              </td>
              <td>
                <span class="state-badge">
                  {{ ot.estado_id == 1 ? 'Pendiente' : (ot.estado_id == 3 ? 'Completada' : 'Otro') }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showHistoryModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- Modal Ver Detalles -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal" style="width: 650px;">
        <h3>Detalles del Equipo: {{ selectedEquipo.nombre_corto || selectedEquipo.modelo }}</h3>
        <div class="detail-grid">
          <div class="detail-column">
            <h4>Identificación</h4>
            <p><strong>ID:</strong> {{ selectedEquipo.id }}</p>
            <p><strong>Marca:</strong> {{ selectedEquipo.marca }}</p>
            <p><strong>Modelo:</strong> {{ selectedEquipo.modelo }}</p>
            <p><strong>Nº Serie:</strong> {{ selectedEquipo.numero_serie }}</p>
            <p><strong>Ubicación:</strong> {{ selectedEquipo.ubicacion_actual || 'N/A' }}</p>
          </div>
          <div class="detail-column">
            <h4>Administrativo</h4>
            <p><strong>Estado:</strong> 
              <span class="badge" :style="{ backgroundColor: getEstadoColor(selectedEquipo.estado_id) }">
                {{ getNombreEstado(selectedEquipo.estado_id) }}
              </span>
            </p>
            <p><strong>Fecha Adquisición:</strong> {{ selectedEquipo.fecha_adquisicion || 'N/A' }}</p>
            <p><strong>Registro Sanitario:</strong> {{ selectedEquipo.registro_sanitario_bolivia || 'N/A' }}</p>
            <p><strong>Proveedor:</strong> {{ selectedEquipo.proveedor_principal || 'N/A' }}</p>
            <p><strong>Próx. Calibración:</strong> {{ selectedEquipo.calibracion_proxima || 'N/A' }}</p>
          </div>
        </div>
        <div class="detail-full">
          <h4>Responsable y Notas</h4>
          <p><strong>Técnico Responsable:</strong> {{ getTecnicoName(selectedEquipo.responsable_tecnico_id) }}</p>
          <p><strong>Descripción:</strong></p>
          <div class="description-box">
            {{ selectedEquipo.descripcion || 'Sin descripción adicional.' }}
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
        </div>
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
  margin-bottom: 1rem;
}
.top-bar h2 { margin: 0; }
.top-bar-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
}
.search-input {
  min-width: 220px;
  flex: 1 1 200px;
  max-width: 360px;
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

table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }

.equipo-nombre-link { color: #3498db; cursor: pointer; text-decoration: none; }
.equipo-nombre-link:hover { text-decoration: underline; }

.table-empty-cell { text-align: center; color: #64748b; padding: 1.5rem 12px; font-size: 0.95rem; }

.table-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
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

.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 1rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }

.btn-import {
  background-color: #27ae60; color: white; border: none; padding: 0.6rem 1.1rem;
  border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem;
  display: flex; align-items: center; gap: 0.4rem; transition: background-color 0.2s;
}
.btn-import:hover { background-color: #219a52; }
.btn-import svg { flex-shrink: 0; }

.btn-outline {
  background-color: transparent; color: #3498db; border: 1.5px solid #3498db;
  padding: 0.45rem 0.9rem; border-radius: 4px; cursor: pointer; font-weight: 600;
  font-size: 0.85rem; transition: all 0.2s; display: flex; align-items: center;
}
.btn-outline:hover { background-color: #ebf5fb; }

.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; color: white; }

.actions-cell { display: flex; gap: 0.5rem; align-items: center; }
.btn-icon {
  background: #f0f2f5;
  border: none;
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #555;
  transition: all 0.2s;
}
.btn-icon:hover { background: #dfe2e6; color: #000; }
.btn-danger-icon:hover { background: #fee2e2; color: #c0392b; }
.btn-secondary-icon:hover { background: #e2e8f0; color: #475569; }

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

/* Historial */
.history-table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
.history-table th, .history-table td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
.history-table th { background-color: #f8f9fa; }
.empty-state { text-align: center; color: #888; padding: 2rem; }
.state-badge { background: #eee; color: #333; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }

/* Detalles */
.detail-grid { display: flex; gap: 2rem; margin-bottom: 1.5rem; }
.detail-column { flex: 1; }
.detail-column h4 { margin-bottom: 0.8rem; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.3rem; }
.detail-column p { margin: 0 0 0.5rem 0; font-size: 0.9rem; color: #555; }
.detail-full { width: 100%; background: #f8f9fa; padding: 1rem; border-radius: 6px; }
.detail-full h4 { margin-top: 0; margin-bottom: 0.5rem; color: #2c3e50; }
.description-box {
  background: white; padding: 0.8rem; border: 1px solid #e0e0e0; border-radius: 4px;
  min-height: 50px; color: #444; font-size: 0.9rem;
  word-break: break-word; overflow-y: auto; max-height: 150px; white-space: pre-wrap;
}

/* === Importar Excel === */
.drop-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 10px;
  padding: 2rem 1.5rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
  margin-bottom: 1rem;
  background: #f8fafc;
}
.drop-zone:hover { border-color: #3498db; background: #f0f7ff; }
.drop-zone--active { border-color: #3498db; background: #e8f4fd; border-style: solid; }
.drop-zone--has-file { border-color: #27ae60; border-style: solid; background: #f0fdf4; }
.drop-zone-content { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; }
.drop-zone-text { font-size: 1rem; font-weight: 600; color: #475569; margin: 0; }
.drop-zone-subtext { font-size: 0.85rem; color: #94a3b8; margin: 0; }
.drop-zone-filename { font-size: 0.95rem; font-weight: 600; color: #27ae60; margin: 0; word-break: break-all; }

.import-info {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.85rem;
  color: #475569;
}
.import-info p { margin: 0.2rem 0; }

.import-progress {
  padding: 2rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1rem;
}

.spinner {
  width: 40px; height: 40px;
  border: 4px solid #e2e8f0;
  border-top-color: #3498db;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.import-result { margin-bottom: 1rem; }

.result-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
  margin-bottom: 1rem;
}
.result-item {
  text-align: center;
  padding: 0.75rem;
  border-radius: 8px;
}
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
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 6px;
  padding: 0.75rem;
}
.import-errors h4 { margin: 0 0 0.5rem 0; color: #991b1b; font-size: 0.9rem; }
.error-list { max-height: 200px; overflow-y: auto; }
.error-item {
  padding: 0.35rem 0;
  font-size: 0.83rem;
  color: #7f1d1d;
  border-bottom: 1px solid #fecaca;
}
.error-item:last-child { border-bottom: none; }
.error-fila { font-weight: 700; }
.error-serie { color: #991b1b; font-size: 0.8rem; }
.error-msg { color: #b91c1c; }
</style>
