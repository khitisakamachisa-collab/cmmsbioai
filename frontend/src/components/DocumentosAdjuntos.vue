<script setup>
import { ref, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'

const props = defineProps({
  ordenTrabajoId: { type: Number, default: null },
  equipoId: { type: Number, default: null }
})

const documentos = ref([])
const uploading = ref(false)
const loading = ref(false)
const dragOver = ref(false)
const selectedFiles = ref([])
const descripcion = ref('')
const categoria = ref('otro')

const categorias = [
  { value: 'manual', label: 'Manual' },
  { value: 'foto', label: 'Fotografia' },
  { value: 'reporte', label: 'Reporte' },
  { value: 'informe', label: 'Informe' },
  { value: 'garantia', label: 'Garantia' },
  { value: 'calibracion', label: 'Calibracion' },
  { value: 'otro', label: 'Otro' }
]

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

const getFileIcon = (tipo) => {
  if (tipo.startsWith('image/')) return '🖼'
  if (tipo === 'application/pdf') return '📄'
  if (tipo.includes('word') || tipo.includes('document')) return '📝'
  if (tipo.includes('sheet') || tipo.includes('excel')) return '📊'
  if (tipo.includes('zip')) return '📦'
  return '📎'
}

const getCategoriaLabel = (cat) => {
  const found = categorias.find(c => c.value === cat)
  return found ? found.label : cat
}

const fetchDocumentos = async () => {
  if (!props.ordenTrabajoId && !props.equipoId) return

  loading.value = true
  try {
    const params = {}
    if (props.ordenTrabajoId) params.orden_trabajo_id = props.ordenTrabajoId
    if (props.equipoId) params.equipo_id = props.equipoId

    const res = await apiClient.get('/documentos/', { params })
    documentos.value = res.data
  } catch (error) {
    console.error('Error al cargar documentos', error)
  } finally {
    loading.value = false
  }
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  selectedFiles.value = files
}

const handleDragOver = (e) => {
  e.preventDefault()
  dragOver.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  dragOver.value = false
}

const handleDrop = (e) => {
  e.preventDefault()
  dragOver.value = false
  const files = Array.from(e.dataTransfer.files)
  selectedFiles.value = files
}

const uploadFiles = async () => {
  if (!selectedFiles.value.length) return

  uploading.value = true
  let exitosos = 0
  let fallidos = 0

  for (const file of selectedFiles.value) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      if (props.ordenTrabajoId) formData.append('orden_trabajo_id', props.ordenTrabajoId)
      if (props.equipoId) formData.append('equipo_id', props.equipoId)
      if (descripcion.value) formData.append('descripcion', descripcion.value)
      formData.append('categoria', categoria.value)

      await apiClient.post('/documentos/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      exitosos++
    } catch (error) {
      console.error('Error al subir archivo', file.name, error)
      fallidos++
    }
  }

  uploading.value = false
  selectedFiles.value = []
  descripcion.value = ''

  if (fallidos > 0) {
    alert(`${exitosos} archivo(s) subido(s). ${fallidos} fallido(s).`)
  }

  fetchDocumentos()
}

const descargarDocumento = async (doc) => {
  try {
    const response = await apiClient.get(`/documentos/${doc.id}/descargar`, {
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', doc.nombre_archivo)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    alert('Error al descargar el archivo')
    console.error(error)
  }
}

const eliminarDocumento = async (doc) => {
  if (!confirm(`¿Eliminar el documento "${doc.nombre_archivo}"?`)) return

  try {
    await apiClient.delete(`/documentos/${doc.id}`)
    fetchDocumentos()
  } catch (error) {
    alert('Error al eliminar el documento')
    console.error(error)
  }
}

watch([() => props.ordenTrabajoId, () => props.equipoId], () => {
  fetchDocumentos()
})

onMounted(() => {
  fetchDocumentos()
})
</script>

<template>
  <div class="documentos-section">
    <h4 class="section-title">
      <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -3px; margin-right: 6px;">
        <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1zM4.5 9a.5.5 0 0 1 0-1h7a.5.5 0 0 1 0 1h-7zM4 11.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm.5 2.5a.5.5 0 0 1 0-1h4a.5.5 0 0 1 0 1h-4z"/>
      </svg>
      Documentos Adjuntos
      <span class="doc-count" v-if="documentos.length">({{ documentos.length }})</span>
    </h4>

    <!-- Zona de subida -->
    <div
      class="upload-zone"
      :class="{ 'upload-zone--active': dragOver, 'upload-zone--has-files': selectedFiles.length }"
      @dragover="handleDragOver"
      @dragleave="handleDragLeave"
      @drop="handleDrop"
      @click="$refs.docFileInput.click()"
    >
      <div v-if="!selectedFiles.length" class="upload-zone-content">
        <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" fill="currentColor" viewBox="0 0 16 16" style="color: #94a3b8;">
          <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
          <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
        </svg>
        <p class="upload-zone-text">Arrastre archivos aqui o haga clic para seleccionar</p>
        <p class="upload-zone-subtext">PDF, imagenes, Word, Excel (max 20 MB c/u)</p>
      </div>
      <div v-else class="upload-zone-files">
        <p class="upload-zone-filename" v-for="(f, i) in selectedFiles" :key="i">
          📎 {{ f.name }} ({{ formatSize(f.size) }})
        </p>
        <p class="upload-zone-subtext">Haga clic para cambiar archivos</p>
      </div>
    </div>
    <input ref="docFileInput" type="file" multiple accept=".pdf,.jpg,.jpeg,.png,.gif,.webp,.doc,.docx,.xls,.xlsx,.csv,.txt,.zip" style="display: none;" @change="handleFileSelect">

    <!-- Campos adicionales para subida -->
    <div v-if="selectedFiles.length" class="upload-fields">
      <div class="upload-field-row">
        <div class="upload-field">
          <label>Categoria</label>
          <select v-model="categoria">
            <option v-for="cat in categorias" :key="cat.value" :value="cat.value">{{ cat.label }}</option>
          </select>
        </div>
        <div class="upload-field" style="flex: 2;">
          <label>Descripcion (opcional)</label>
          <input v-model="descripcion" type="text" placeholder="Ej: Manual de usuario del equipo">
        </div>
      </div>
      <button class="btn-upload" :disabled="uploading" @click="uploadFiles">
        <span v-if="uploading" class="spinner-sm"></span>
        <span v-else>{{ uploading ? 'Subiendo...' : 'Subir Archivo(s)' }}</span>
      </button>
    </div>

    <!-- Lista de documentos existentes -->
    <div v-if="loading" class="doc-loading">Cargando documentos...</div>

    <div v-if="!loading && documentos.length" class="doc-list">
      <div v-for="doc in documentos" :key="doc.id" class="doc-item">
        <div class="doc-icon">{{ getFileIcon(doc.tipo_archivo) }}</div>
        <div class="doc-info">
          <span class="doc-name" @click="descargarDocumento(doc)" title="Click para descargar">{{ doc.nombre_archivo }}</span>
          <div class="doc-meta">
            <span class="doc-badge" :class="'doc-badge--' + doc.categoria">{{ getCategoriaLabel(doc.categoria) }}</span>
            <span class="doc-size">{{ formatSize(doc.tamanio_bytes) }}</span>
            <span v-if="doc.fecha_subida" class="doc-date">{{ new Date(doc.fecha_subida).toLocaleDateString('es-BO') }}</span>
            <span v-if="doc.subido_por" class="doc-user">por {{ doc.subido_por }}</span>
          </div>
          <p v-if="doc.descripcion" class="doc-desc">{{ doc.descripcion }}</p>
        </div>
        <div class="doc-actions">
          <button class="btn-doc-action" title="Descargar" @click="descargarDocumento(doc)">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
            </svg>
          </button>
          <button class="btn-doc-action btn-doc-delete" title="Eliminar" @click="eliminarDocumento(doc)">
            <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
              <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <div v-if="!loading && !documentos.length" class="doc-empty">
      No hay documentos adjuntos.
    </div>
  </div>
</template>

<style scoped>
.documentos-section {
  /* Sin borde ni padding-top cuando es modal independiente */
}

.section-title {
  margin: 0 0 0.75rem 0;
  font-size: 1rem;
  color: #2c3e50;
  display: flex;
  align-items: center;
}

.doc-count {
  font-weight: normal;
  color: #64748b;
  font-size: 0.85rem;
  margin-left: 4px;
}

/* Zona de subida */
.upload-zone {
  border: 2px dashed #cbd5e1;
  border-radius: 8px;
  padding: 1.2rem 1rem;
  text-align: center;
  cursor: pointer;
  transition: all 0.25s ease;
  background: #f8fafc;
  margin-bottom: 0.75rem;
}
.upload-zone:hover { border-color: #3498db; background: #f0f7ff; }
.upload-zone--active { border-color: #3498db; background: #e8f4fd; border-style: solid; }
.upload-zone--has-files { border-color: #27ae60; border-style: solid; background: #f0fdf4; }
.upload-zone-content { display: flex; flex-direction: column; align-items: center; gap: 0.3rem; }
.upload-zone-text { font-size: 0.9rem; font-weight: 600; color: #475569; margin: 0; }
.upload-zone-subtext { font-size: 0.78rem; color: #94a3b8; margin: 0; }
.upload-zone-filename { font-size: 0.85rem; color: #27ae60; margin: 0.15rem 0; font-weight: 500; }
.upload-zone-files { display: flex; flex-direction: column; align-items: center; }

/* Campos de subida */
.upload-fields {
  margin-bottom: 0.75rem;
}
.upload-field-row {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.upload-field { flex: 1; }
.upload-field label { display: block; font-size: 0.8rem; font-weight: 600; color: #475569; margin-bottom: 0.25rem; }
.upload-field input, .upload-field select {
  width: 100%;
  padding: 0.4rem 0.6rem;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 0.85rem;
  box-sizing: border-box;
}

.btn-upload {
  background-color: #27ae60;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}
.btn-upload:hover { background-color: #219a52; }
.btn-upload:disabled { opacity: 0.5; cursor: not-allowed; }

.spinner-sm {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* Lista de documentos */
.doc-loading { text-align: center; color: #94a3b8; padding: 1rem; font-size: 0.9rem; }
.doc-empty { text-align: center; color: #94a3b8; padding: 0.75rem; font-size: 0.85rem; font-style: italic; }

.doc-list {
  max-height: 400px;
  overflow-y: auto;
}

.doc-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.6rem;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  margin-bottom: 0.4rem;
  background: #fff;
  transition: background 0.15s;
}
.doc-item:hover { background: #f8fafc; }

.doc-icon { font-size: 1.4rem; flex-shrink: 0; line-height: 1; }

.doc-info { flex: 1; min-width: 0; }
.doc-name {
  font-weight: 600;
  font-size: 0.88rem;
  color: #3498db;
  cursor: pointer;
  word-break: break-all;
}
.doc-name:hover { text-decoration: underline; }

.doc-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
  align-items: center;
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: #64748b;
}

.doc-badge {
  padding: 1px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  color: white;
}
.doc-badge--manual { background: #3498db; }
.doc-badge--foto { background: #9b59b6; }
.doc-badge--reporte { background: #27ae60; }
.doc-badge--informe { background: #2196F3; }
.doc-badge--garantia { background: #f39c12; }
.doc-badge--calibracion { background: #e67e22; }
.doc-badge--otro { background: #95a5a6; }

.doc-size, .doc-date, .doc-user { font-size: 0.73rem; }

.doc-desc {
  margin: 0.2rem 0 0 0;
  font-size: 0.8rem;
  color: #475569;
  font-style: italic;
}

.doc-actions {
  display: flex;
  gap: 0.3rem;
  flex-shrink: 0;
}

.btn-doc-action {
  background: #f0f2f5;
  border: none;
  padding: 5px;
  border-radius: 4px;
  cursor: pointer;
  color: #555;
  display: flex;
  align-items: center;
  transition: all 0.15s;
}
.btn-doc-action:hover { background: #dfe2e6; color: #000; }
.btn-doc-delete:hover { background: #fee2e2; color: #c0392b; }
</style>
