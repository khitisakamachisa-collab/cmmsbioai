<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'

const repuestos = ref([])
const loading = ref(true)
const searchQuery = ref('')

const currentPage = ref(1)
const pageSize = ref(10)

const showModal = ref(false)
const isEditing = ref(false)
const showDetailModal = ref(false)
const selectedRepuesto = ref({})

// --- Variables Modal Importar Excel ---
const showImportModal = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importDragOver = ref(false)

const emptyForm = () => ({
  nombre_repuesto: '',
  numero_material: '',
  descripcion: '',
  cantidad_disponible: 0,
  unidad_medida: 'unidad',
  ubicacion_almacen: '',
  nivel_stock_minimo: null
})

const formData = ref(emptyForm())

const fetchRepuestos = async () => {
  try {
    loading.value = true
    const res = await apiClient.get('/repuestos/')
    repuestos.value = res.data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

const filteredRepuestos = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return repuestos.value
  return repuestos.value.filter((rep) => {
    const nombre = String(rep.nombre_repuesto ?? '').toLowerCase()
    const material = String(rep.numero_material ?? '').toLowerCase()
    return nombre.includes(q) || material.includes(q)
  })
})

const paginatedRepuestos = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredRepuestos.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredRepuestos.value.length / pageSize.value))
)

watch(
  () => filteredRepuestos.value.length,
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

const isLowStock = (rep) => {
  const min = rep.nivel_stock_minimo
  if (min != null && min !== '') return Number(rep.cantidad_disponible) <= Number(min)
  return Number(rep.cantidad_disponible) <= 5
}

const openCreateModal = () => {
  isEditing.value = false
  formData.value = emptyForm()
  showModal.value = true
}

const openEditModal = (rep) => {
  isEditing.value = true
  formData.value = {
    id: rep.id,
    nombre_repuesto: rep.nombre_repuesto,
    numero_material: rep.numero_material || '',
    descripcion: rep.descripcion || '',
    cantidad_disponible: rep.cantidad_disponible,
    unidad_medida: rep.unidad_medida,
    ubicacion_almacen: rep.ubicacion_almacen || '',
    nivel_stock_minimo: rep.nivel_stock_minimo ?? null
  }
  showModal.value = true
}

const openDetailModal = async (rep) => {
  try {
    const res = await apiClient.get(`/repuestos/${rep.id}`)
    selectedRepuesto.value = res.data
  } catch {
    selectedRepuesto.value = { ...rep }
  }
  showDetailModal.value = true
}

const saveRepuesto = async () => {
  try {
    const payload = { ...formData.value }
    const id = payload.id
    if (id != null) delete payload.id

    if (payload.nivel_stock_minimo === '') payload.nivel_stock_minimo = null

    if (isEditing.value) {
      await apiClient.put(`/repuestos/${formData.value.id}`, payload)
      alert('Repuesto actualizado')
    } else {
      await apiClient.post('/repuestos/', payload)
      alert('Repuesto agregado')
    }
    showModal.value = false
    fetchRepuestos()
  } catch (error) {
    console.error(error)
    alert('Error al guardar')
  }
}

const deleteRepuesto = async (id) => {
  if (!confirm('¿Eliminar este repuesto del inventario?')) return
  try {
    await apiClient.delete(`/repuestos/${id}`)
    alert('Repuesto eliminado')
    fetchRepuestos()
  } catch (error) {
    console.error(error)
    alert('No se pudo eliminar (puede estar en uso en una orden).')
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
    const response = await apiClient.get('/repuestos/plantilla-excel', {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    const contentDisposition = response.headers['content-disposition']
    let filename = 'CMMS-BioAI_Plantilla_Repuestos.xlsx'
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
    const response = await apiClient.post('/repuestos/import-excel', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    importResult.value = response.data
    fetchRepuestos()
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

onMounted(() => {
  fetchRepuestos()
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Almacén de Repuestos</h2>
        <div class="top-bar-actions">
          <input
            v-model="searchQuery"
            type="search"
            class="search-input"
            placeholder="Buscar por nombre o número de material..."
            autocomplete="off"
            aria-label="Buscar repuestos"
          >
          <button class="btn-import" @click="openImportModal" title="Cargar repuestos desde Excel">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
            </svg>
            Cargar Excel
          </button>
          <button type="button" class="btn-primary" @click="openCreateModal">+ Agregar Repuesto</button>
        </div>
      </div>

      <div v-if="loading">Cargando inventario...</div>

      <table v-if="!loading && repuestos.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Nº Material</th>
            <th>Stock</th>
            <th>Ubicación</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredRepuestos.length">
            <td class="table-empty-cell" colspan="6">
              {{ searchQuery.trim() ? 'No hay repuestos que coincidan con la búsqueda.' : 'No hay repuestos registrados.' }}
            </td>
          </tr>
          <template v-else>
            <tr v-for="rep in paginatedRepuestos" :key="rep.id">
              <td>#{{ rep.id }}</td>
              <td><strong>{{ rep.nombre_repuesto }}</strong></td>
              <td>{{ rep.numero_material || 'N/A' }}</td>
              <td>
                <span :class="isLowStock(rep) ? 'low-stock' : 'stock'">
                  {{ rep.cantidad_disponible }} {{ rep.unidad_medida }}
                </span>
              </td>
              <td>{{ rep.ubicacion_almacen || 'Sin ubicar' }}</td>
              <td class="actions-cell">
                <button
                  type="button"
                  class="btn-icon"
                  title="Ver detalles"
                  @click="openDetailModal(rep)"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                  </svg>
                </button>
                <button type="button" class="btn-icon" title="Editar" @click="openEditModal(rep)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                  </svg>
                </button>
                <button type="button" class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteRepuesto(rep.id)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                  </svg>
                </button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <div
        v-if="!loading && repuestos.length && filteredRepuestos.length"
        class="table-pagination"
        role="navigation"
        aria-label="Paginación del inventario"
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

      <div v-if="!loading && repuestos.length === 0" class="empty-state">No hay repuestos registrados.</div>
    </main>

    <!-- Modal Importar Excel -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal" style="width: 580px;">
        <h3>Importar Repuestos desde Excel</h3>

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
            <p><strong>Columnas obligatorias:</strong> nombre_repuesto, cantidad_disponible</p>
            <p>Si el numero_material ya existe, el repuesto se <strong>actualizará</strong>.</p>
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
          <p style="text-align: center; color: #475569;">Importando repuestos...</p>
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

            <div v-if="importResult.errores && importResult.errores.length > 0" class="import-errors">
              <h4>Detalle de errores</h4>
              <div class="error-list">
                <div v-for="(err, idx) in importResult.errores" :key="idx" class="error-item">
                  <span class="error-fila">Fila {{ err.fila }}</span>
                  <span class="error-serie">({{ err.nombre }})</span>
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

    <!-- Modal Crear / Editar -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Repuesto' : 'Nuevo Repuesto' }}</h3>
        <form @submit.prevent="saveRepuesto">
          <div class="form-group">
            <label>Nombre *</label>
            <input v-model="formData.nombre_repuesto" type="text" required>
          </div>
          <div class="form-group">
            <label>Número de Material / Código</label>
            <input v-model="formData.numero_material" type="text">
          </div>
          <div class="form-group">
            <label>Descripción / Notas</label>
            <textarea v-model="formData.descripcion" rows="3" placeholder="Detalle del repuesto, proveedor habitual, etc."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ isEditing ? 'Cantidad disponible' : 'Cantidad inicial' }}</label>
              <input v-model.number="formData.cantidad_disponible" type="number" min="0" required>
            </div>
            <div class="form-group">
              <label>Unidad</label>
              <select v-model="formData.unidad_medida">
                <option value="unidad">unidad</option>
                <option value="par">par</option>
                <option value="metro">metro</option>
                <option value="litro">litro</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Ubicación en almacén</label>
              <input v-model="formData.ubicacion_almacen" type="text" placeholder="Ej: Estante B2">
            </div>
            <div class="form-group">
              <label>Stock mínimo (alerta)</label>
              <input v-model.number="formData.nivel_stock_minimo" type="number" min="0" placeholder="Opcional">
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal detalle (solo lectura) -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal modal-details">
        <h3>Detalle del repuesto: {{ selectedRepuesto.nombre_repuesto }}</h3>

        <div class="detail-grid">
          <div class="detail-column">
            <h4>Identificación</h4>
            <p><strong>ID:</strong> {{ selectedRepuesto.id }}</p>
            <p><strong>Nombre:</strong> {{ selectedRepuesto.nombre_repuesto }}</p>
            <p><strong>Nº material:</strong> {{ selectedRepuesto.numero_material || 'N/A' }}</p>
            <p><strong>Ubicación:</strong> {{ selectedRepuesto.ubicacion_almacen || 'Sin ubicar' }}</p>
            <p v-if="selectedRepuesto.imagen"><strong>Imagen:</strong> {{ selectedRepuesto.imagen }}</p>
          </div>
          <div class="detail-column">
            <h4>Inventario</h4>
            <p>
              <strong>Stock actual:</strong>
              <span :class="isLowStock(selectedRepuesto) ? 'low-stock' : 'stock'">
                {{ selectedRepuesto.cantidad_disponible }} {{ selectedRepuesto.unidad_medida }}
              </span>
            </p>
            <p><strong>Stock mínimo:</strong> {{ selectedRepuesto.nivel_stock_minimo ?? 'No definido' }}</p>
          </div>
        </div>

        <div class="detail-full">
          <h4>Descripción</h4>
          <div class="description-box">
            {{ selectedRepuesto.descripcion || 'Sin descripción.' }}
          </div>
        </div>

        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
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
  max-width: 380px;
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

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }

.table-empty-cell {
  text-align: center;
  color: #64748b;
  padding: 1.5rem 12px;
  font-size: 0.95rem;
}

.empty-state {
  text-align: center;
  color: #64748b;
  padding: 2rem;
  margin-top: 1rem;
}

.stock { color: #27ae60; font-weight: bold; }
.low-stock { color: #e74c3c; font-weight: bold; }

.btn-primary {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.6rem 1.2rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: bold;
  font-size: 1rem;
}
.btn-primary:hover { background-color: #2980b9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary {
  background-color: #95a5a6;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

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

.actions-cell {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

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
.btn-icon:hover {
  background: #dfe2e6;
  color: #000;
}
.btn-danger-icon:hover {
  background: #fee2e2;
  color: #c0392b;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 100;
}
.modal {
  background: white;
  padding: 2rem;
  border-radius: 8px;
  width: 500px;
  max-width: 90%;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
}
.modal-details {
  width: 640px;
}

.form-group { margin-bottom: 1rem; }
.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-size: 0.9rem;
  font-weight: bold;
}
.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  box-sizing: border-box;
  background-color: white;
  font-family: inherit;
}
.form-group textarea { resize: vertical; }

.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 1.5rem;
}

.detail-grid {
  display: flex;
  gap: 2rem;
  margin-bottom: 1.5rem;
}
.detail-column { flex: 1; }
.detail-column h4 {
  margin-bottom: 0.8rem;
  color: #2c3e50;
  border-bottom: 2px solid #eee;
  padding-bottom: 0.3rem;
}
.detail-column p {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: #555;
}

.detail-full {
  width: 100%;
  background: #f8f9fa;
  padding: 1rem;
  border-radius: 6px;
}
.detail-full h4 {
  margin-top: 0;
  margin-bottom: 0.5rem;
  color: #2c3e50;
}

.description-box {
  word-break: break-word;
  overflow-y: auto;
  max-height: 160px;
  white-space: pre-wrap;
  background: white;
  padding: 0.8rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  min-height: 50px;
  color: #444;
  font-size: 0.9rem;
}

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
