<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
import DocumentosAdjuntos from '../components/DocumentosAdjuntos.vue'

// =============================================
// TAB SYSTEM
// =============================================
const activeTab = ref('repuestos')

// =============================================
// v0.9.14: PROVEEDORES (compartido por Repuestos y Herramientas)
// =============================================
const proveedores = ref([])
const showNuevoProveedorModal = ref(false)
const nuevoProveedorNombre = ref('')
const creandoProveedor = ref(false)
// Para saber a qué formulario regresar el proveedor creado ('repuesto' o 'herramienta')
const proveedorModalContext = ref('repuesto')

const fetchProveedores = async () => {
  try {
    const res = await apiClient.get('/proveedores/')
    proveedores.value = Array.isArray(res.data) ? res.data : []
  } catch (e) {
    console.error('Error cargando proveedores:', e)
  }
}

const getProveedorName = (id) => {
  if (!id) return ''
  const p = proveedores.value.find(p => p.id === id)
  return p ? p.nombre_empresa : ''
}

const abrirModalNuevoProveedor = (contexto) => {
  proveedorModalContext.value = contexto  // 'repuesto' o 'herramienta'
  nuevoProveedorNombre.value = ''
  showNuevoProveedorModal.value = true
}

const crearProveedorAlVuelo = async () => {
  const nombre = nuevoProveedorNombre.value.trim()
  if (!nombre) {
    alert('El nombre del proveedor es obligatorio')
    return
  }
  creandoProveedor.value = true
  try {
    const res = await apiClient.post('/proveedores/', { nombre_empresa: nombre })
    await fetchProveedores()
    // Asignar al formulario correspondiente
    if (proveedorModalContext.value === 'repuesto') {
      formData.value.proveedor_ultimo_id = res.data.id
    } else {
      herrFormData.value.proveedor_ultimo_id = res.data.id
    }
    showNuevoProveedorModal.value = false
    alert(`Proveedor "${nombre}" creado. Podrás completar sus datos en la página de Proveedores.`)
  } catch (error) {
    const msg = error.response?.data?.detail || 'Error al crear el proveedor'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
  } finally {
    creandoProveedor.value = false
  }
}

// =============================================
// REPUESTOS - Variables & Logic
// =============================================
const repuestos = ref([])
const loading = ref(true)
const searchQuery = ref('')

const currentPage = ref(1)
const pageSize = ref(10)

const showModal = ref(false)
const isEditing = ref(false)
const showDetailModal = ref(false)
const selectedRepuesto = ref({})

// --- Variables Modal Documentos ---
const showDocsModal = ref(false)
const docsRepuesto = ref({})
const docsHerramienta = ref({})

// --- Variables Imagen Upload ---
const imagenFile = ref(null)
const imagenPreview = ref('')
const subiendoImagen = ref(false)

// --- Variables Modal Importar Excel ---
const showImportModal = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importDragOver = ref(false)

const emptyForm = () => ({
  nombre_repuesto: '',
  numero_serie: '',
  numero_material: '',
  descripcion: '',
  especificaciones_tecnicas: '',
  cantidad_disponible: 0,
  unidad_medida: 'unidad',
  ubicacion_almacen: '',
  nivel_stock_minimo: null,
  proveedor_ultimo: '',
  proveedor_ultimo_id: null,  // v0.9.14
  fecha_ultima_entrada: '',
  precio_referencia: null,
  imagen_ruta: ''
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
    const serie = String(rep.numero_serie ?? '').toLowerCase()
    const material = String(rep.numero_material ?? '').toLowerCase()
    const proveedor = String(rep.proveedor_ultimo ?? '').toLowerCase()
    const ubicacion = String(rep.ubicacion_almacen ?? '').toLowerCase()
    return nombre.includes(q) || serie.includes(q) || material.includes(q) || proveedor.includes(q) || ubicacion.includes(q)
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

const formatPrecio = (val) => {
  if (val == null || val === '') return 'N/A'
  return 'Bs. ' + Number(val).toFixed(2)
}

// --- Funciones Imagen Repuestos ---
const handleImagenSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    alert('Solo se permiten archivos de imagen')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('La imagen no debe superar 5MB')
    return
  }
  imagenFile.value = file
}

const getImagenNombre = (ruta) => {
  if (!ruta) return ''
  const parts = ruta.split('/')
  return parts[parts.length - 1] || ruta
}

const eliminarImagenRepuesto = async () => {
  if (!confirm('¿Eliminar la imagen de este repuesto?')) return
  try {
    await apiClient.delete(`/repuestos/${formData.value.id}/imagen`)
    formData.value.imagen_ruta = null
    imagenFile.value = null
    imagenPreview.value = ''
    alert('Imagen eliminada')
    fetchRepuestos()
  } catch (error) {
    alert('Error al eliminar la imagen')
  }
}

const subirImagenAhora = async () => {
  if (!imagenFile.value) return
  const repId = formData.value.id
  if (!repId) {
    alert('Guarde el repuesto primero antes de subir la imagen')
    return
  }
  try {
    subiendoImagen.value = true
    const imgFormData = new FormData()
    imgFormData.append('file', imagenFile.value)
    const res = await apiClient.post(`/repuestos/${repId}/upload_imagen`, imgFormData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    formData.value.imagen_ruta = res.data.imagen_ruta
    imagenFile.value = null
    alert('Imagen subida correctamente')
    fetchRepuestos()
  } catch (error) {
    alert('Error al subir la imagen: ' + (error.response?.data?.detail || error.message))
  } finally {
    subiendoImagen.value = false
  }
}

// --- Funciones Modal Repuestos ---
const openCreateModal = () => {
  isEditing.value = false
  formData.value = emptyForm()
  imagenFile.value = null
  imagenPreview.value = ''
  showModal.value = true
}

const openEditModal = (rep) => {
  isEditing.value = true
  formData.value = {
    id: rep.id,
    nombre_repuesto: rep.nombre_repuesto,
    numero_serie: rep.numero_serie || '',
    numero_material: rep.numero_material || '',
    descripcion: rep.descripcion || '',
    especificaciones_tecnicas: rep.especificaciones_tecnicas || '',
    cantidad_disponible: rep.cantidad_disponible,
    unidad_medida: rep.unidad_medida,
    ubicacion_almacen: rep.ubicacion_almacen || '',
    nivel_stock_minimo: rep.nivel_stock_minimo ?? null,
    proveedor_ultimo: rep.proveedor_ultimo || '',
    proveedor_ultimo_id: rep.proveedor_ultimo_id ?? null,  // v0.9.14
    fecha_ultima_entrada: rep.fecha_ultima_entrada ? rep.fecha_ultima_entrada.substring(0, 10) : '',
    precio_referencia: rep.precio_referencia ?? null,
    imagen_ruta: rep.imagen_ruta || ''
  }
  imagenFile.value = null
  imagenPreview.value = rep.imagen_ruta ? `/uploads/${rep.imagen_ruta}` : ''
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

const openDocsModal = (rep) => {
  docsRepuesto.value = rep
  showDocsModal.value = true
}

const saveRepuesto = async () => {
  try {
    const payload = { ...formData.value }
    const id = payload.id
    if (id != null) delete payload.id

    if (payload.nivel_stock_minimo === '') payload.nivel_stock_minimo = null
    if (payload.fecha_ultima_entrada === '') payload.fecha_ultima_entrada = null
    if (payload.precio_referencia === '' || payload.precio_referencia === 0) payload.precio_referencia = null
    if (payload.proveedor_ultimo_id === '' ) payload.proveedor_ultimo_id = null  // v0.9.14

    let repId;
    if (isEditing.value) {
      await apiClient.put(`/repuestos/${formData.value.id}`, payload)
      repId = formData.value.id
    } else {
      const res = await apiClient.post('/repuestos/', payload)
      repId = res.data.id
    }

    // Subir imagen si se seleccionó una
    if (imagenFile.value && repId) {
      const imgFormData = new FormData()
      imgFormData.append('file', imagenFile.value)
      await apiClient.post(`/repuestos/${repId}/upload_imagen`, imgFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    }

    alert(isEditing.value ? 'Repuesto actualizado' : 'Repuesto agregado')
    showModal.value = false
    fetchRepuestos()
  } catch (error) {
    console.error(error.response || error)
    if (error.response && error.response.data && error.response.data.detail) {
      const details = error.response.data.detail;
      if (Array.isArray(details)) {
        alert(`Error de validación: ${details[0].msg} en campo ${details[0].loc.join('-')}`);
      } else {
        alert('Error: ' + details);
      }
    } else {
      alert('Error al guardar');
    }
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

// --- Funciones Importar Excel Repuestos ---
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

const downloadTemplate = () => {
  // Descarga directa desde archivos estáticos en /public/plantillas/
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_repuestos.xlsx`
  link.download = 'CMMS-BioAI_Plantilla_Repuestos.xlsx'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const downloadTemplateCSV = () => {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_repuestos.csv`
  link.download = 'CMMS-BioAI_Plantilla_Repuestos.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const uploadExcel = async () => {
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
    const response = await apiClient.post('/repuestos/import-excel', fd, {
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

// =============================================
// HERRAMIENTAS - Variables & Logic
// =============================================
const herramientas = ref([])
const herrLoading = ref(false)
const herrSearchQuery = ref('')

const herrCurrentPage = ref(1)
const herrPageSize = ref(10)

const herrShowModal = ref(false)
const herrIsEditing = ref(false)
const herrShowDetailModal = ref(false)
const herrSelected = ref({})

const herrShowDocsModal = ref(false)

// --- Variables Imagen Upload Herramienta ---
const herrImagenFile = ref(null)
const herrImagenPreview = ref('')
const herrSubiendoImagen = ref(false)

// --- Variables Modal Importar Excel Herramientas ---
const herrShowImportModal = ref(false)
const herrImportFile = ref(null)
const herrImporting = ref(false)
const herrImportResult = ref(null)
const herrImportDragOver = ref(false)

const categoriasHerramienta = [
  'Instrumento de Medición',
  'Herramienta Manual',
  'Consumible',
  'Kit'
]

const estadosUso = [
  'Disponible',
  'En Uso',
  'En Reparación',
  'Dado de Baja'
]

const herrEmptyForm = () => ({
  nombre_herramienta: '',
  numero_identificacion: '',
  descripcion: '',
  categoria: 'Herramienta Manual',
  cantidad_disponible: 0,
  unidad_medida: 'unidad',
  ubicacion_almacen: '',
  estado_uso: 'Disponible',
  imagen_ruta: '',
  costo_adquisicion: null,
  fecha_adquisicion: '',
  proveedor_ultimo: '',
  proveedor_ultimo_id: null,  // v0.9.14
  observaciones: ''
})

const herrFormData = ref(herrEmptyForm())

// --- Badge colors ---
const getEstadoUsoColor = (estado) => {
  const colors = {
    'Disponible': '#27ae60',
    'En Uso': '#f39c12',
    'En Reparación': '#e74c3c',
    'Dado de Baja': '#7f8c8d'
  }
  return colors[estado] || '#7f8c8d'
}

const getCategoriaColor = (categoria) => {
  const colors = {
    'Instrumento de Medición': '#3498db',
    'Herramienta Manual': '#1abc9c',
    'Consumible': '#9b59b6',
    'Kit': '#e67e22'
  }
  return colors[categoria] || '#7f8c8d'
}

// --- Fetch Herramientas ---
const fetchHerramientas = async () => {
  try {
    herrLoading.value = true
    const res = await apiClient.get('/herramientas/')
    herramientas.value = res.data
  } catch (error) {
    console.error(error)
  } finally {
    herrLoading.value = false
  }
}

const filteredHerramientas = computed(() => {
  const q = herrSearchQuery.value.trim().toLowerCase()
  if (!q) return herramientas.value
  return herramientas.value.filter((h) => {
    const nombre = String(h.nombre_herramienta ?? '').toLowerCase()
    const numero = String(h.numero_identificacion ?? '').toLowerCase()
    const categoria = String(h.categoria ?? '').toLowerCase()
    const ubicacion = String(h.ubicacion_almacen ?? '').toLowerCase()
    return nombre.includes(q) || numero.includes(q) || categoria.includes(q) || ubicacion.includes(q)
  })
})

const paginatedHerramientas = computed(() => {
  const start = (herrCurrentPage.value - 1) * herrPageSize.value
  return filteredHerramientas.value.slice(start, start + herrPageSize.value)
})

const herrTotalPages = computed(() =>
  Math.max(1, Math.ceil(filteredHerramientas.value.length / herrPageSize.value))
)

watch(
  () => filteredHerramientas.value.length,
  (len) => {
    const tp = Math.max(1, Math.ceil(len / herrPageSize.value))
    if (herrCurrentPage.value > tp) herrCurrentPage.value = tp
  }
)

watch(herrSearchQuery, () => {
  herrCurrentPage.value = 1
})

const herrIrPaginaAnterior = () => {
  if (herrCurrentPage.value > 1) herrCurrentPage.value -= 1
}

const herrIrPaginaSiguiente = () => {
  if (herrCurrentPage.value < herrTotalPages.value) herrCurrentPage.value += 1
}

// --- Funciones Imagen Herramienta ---
const herrHandleImagenSelect = (event) => {
  const file = event.target.files[0]
  if (!file) return
  if (!file.type.startsWith('image/')) {
    alert('Solo se permiten archivos de imagen')
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    alert('La imagen no debe superar 5MB')
    return
  }
  herrImagenFile.value = file
}

const herrEliminarImagen = async () => {
  if (!confirm('¿Eliminar la imagen de esta herramienta?')) return
  try {
    await apiClient.delete(`/herramientas/${herrFormData.value.id}/imagen`)
    herrFormData.value.imagen_ruta = null
    herrImagenFile.value = null
    herrImagenPreview.value = ''
    alert('Imagen eliminada')
    fetchHerramientas()
  } catch (error) {
    alert('Error al eliminar la imagen')
  }
}

const herrSubirImagenAhora = async () => {
  if (!herrImagenFile.value) return
  const herrId = herrFormData.value.id
  if (!herrId) {
    alert('Guarde la herramienta primero antes de subir la imagen')
    return
  }
  try {
    herrSubiendoImagen.value = true
    const imgFormData = new FormData()
    imgFormData.append('file', herrImagenFile.value)
    const res = await apiClient.post(`/herramientas/${herrId}/upload_imagen`, imgFormData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    herrFormData.value.imagen_ruta = res.data.imagen_ruta
    herrImagenFile.value = null
    alert('Imagen subida correctamente')
    fetchHerramientas()
  } catch (error) {
    alert('Error al subir la imagen: ' + (error.response?.data?.detail || error.message))
  } finally {
    herrSubiendoImagen.value = false
  }
}

// --- Funciones Modal Herramientas ---
const herrOpenCreateModal = () => {
  herrIsEditing.value = false
  herrFormData.value = herrEmptyForm()
  herrImagenFile.value = null
  herrImagenPreview.value = ''
  herrShowModal.value = true
}

const herrOpenEditModal = (h) => {
  herrIsEditing.value = true
  herrFormData.value = {
    id: h.id,
    nombre_herramienta: h.nombre_herramienta,
    numero_identificacion: h.numero_identificacion || '',
    descripcion: h.descripcion || '',
    categoria: h.categoria || 'Herramienta Manual',
    cantidad_disponible: h.cantidad_disponible,
    unidad_medida: h.unidad_medida || 'unidad',
    ubicacion_almacen: h.ubicacion_almacen || '',
    estado_uso: h.estado_uso || 'Disponible',
    imagen_ruta: h.imagen_ruta || '',
    costo_adquisicion: h.costo_adquisicion ?? null,
    fecha_adquisicion: h.fecha_adquisicion ? h.fecha_adquisicion.substring(0, 10) : '',
    proveedor_ultimo: h.proveedor_ultimo || '',
    proveedor_ultimo_id: h.proveedor_ultimo_id ?? null,  // v0.9.14
    observaciones: h.observaciones || ''
  }
  herrImagenFile.value = null
  herrImagenPreview.value = h.imagen_ruta ? `/uploads/${h.imagen_ruta}` : ''
  herrShowModal.value = true
}

const herrOpenDetailModal = async (h) => {
  try {
    const res = await apiClient.get(`/herramientas/${h.id}`)
    herrSelected.value = res.data
  } catch {
    herrSelected.value = { ...h }
  }
  herrShowDetailModal.value = true
}

const herrOpenDocsModal = (h) => {
  docsHerramienta.value = h
  herrShowDocsModal.value = true
}

const herrSaveHerramienta = async () => {
  try {
    const payload = { ...herrFormData.value }
    const id = payload.id
    if (id != null) delete payload.id

    if (payload.costo_adquisicion === '' || payload.costo_adquisicion === 0) payload.costo_adquisicion = null
    if (payload.fecha_adquisicion === '') payload.fecha_adquisicion = null
    if (payload.proveedor_ultimo_id === '') payload.proveedor_ultimo_id = null  // v0.9.14

    let herrId;
    if (herrIsEditing.value) {
      await apiClient.put(`/herramientas/${herrFormData.value.id}`, payload)
      herrId = herrFormData.value.id
    } else {
      const res = await apiClient.post('/herramientas/', payload)
      herrId = res.data.id
    }

    // Subir imagen si se seleccionó una
    if (herrImagenFile.value && herrId) {
      const imgFormData = new FormData()
      imgFormData.append('file', herrImagenFile.value)
      await apiClient.post(`/herramientas/${herrId}/upload_imagen`, imgFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    }

    alert(herrIsEditing.value ? 'Herramienta actualizada' : 'Herramienta agregada')
    herrShowModal.value = false
    fetchHerramientas()
  } catch (error) {
    console.error(error.response || error)
    if (error.response && error.response.data && error.response.data.detail) {
      const details = error.response.data.detail;
      if (Array.isArray(details)) {
        alert(`Error de validación: ${details[0].msg} en campo ${details[0].loc.join('-')}`);
      } else {
        alert('Error: ' + details);
      }
    } else {
      alert('Error al guardar');
    }
  }
}

const herrDeleteHerramienta = async (id) => {
  if (!confirm('¿Eliminar esta herramienta del inventario?')) return
  try {
    await apiClient.delete(`/herramientas/${id}`)
    alert('Herramienta eliminada')
    fetchHerramientas()
  } catch (error) {
    console.error(error)
    alert('No se pudo eliminar (puede estar en uso en una orden).')
  }
}

// --- Funciones Importar Excel Herramientas ---
const herrOpenImportModal = () => {
  herrImportFile.value = null
  herrImportResult.value = null
  herrImporting.value = false
  herrImportDragOver.value = false
  herrShowImportModal.value = true
}

const herrHandleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    herrImportFile.value = file
    herrImportResult.value = null
  }
}

const herrHandleDragOver = (e) => {
  e.preventDefault()
  herrImportDragOver.value = true
}

const herrHandleDragLeave = (e) => {
  e.preventDefault()
  herrImportDragOver.value = false
}

const herrHandleDrop = (e) => {
  e.preventDefault()
  herrImportDragOver.value = false
  const file = e.dataTransfer.files[0]
  if (file) {
    herrImportFile.value = file
    herrImportResult.value = null
  }
}

const herrDownloadTemplate = () => {
  // Descarga directa desde archivos estáticos en /public/plantillas/
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_herramientas.xlsx`
  link.download = 'CMMS-BioAI_Plantilla_Herramientas.xlsx'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const herrUploadExcel = async () => {
  if (!herrImportFile.value) {
    alert('Seleccione un archivo primero')
    return
  }
  const ext = herrImportFile.value.name.toLowerCase()
  if (!ext.endsWith('.xlsx') && !ext.endsWith('.csv')) {
    alert('Solo se aceptan archivos .xlsx o .csv')
    return
  }
  try {
    herrImporting.value = true
    herrImportResult.value = null
    const fd = new FormData()
    fd.append('file', herrImportFile.value)
    const response = await apiClient.post('/herramientas/import-excel', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    herrImportResult.value = response.data
    fetchHerramientas()
  } catch (error) {
    if (error.response && error.response.data && error.response.data.detail) {
      alert('Error: ' + error.response.data.detail)
    } else {
      alert('Error al importar el archivo')
    }
    console.error(error)
  } finally {
    herrImporting.value = false
  }
}

const herrResetImport = () => {
  herrImportFile.value = null
  herrImportResult.value = null
}

// =============================================
// ON MOUNTED
// =============================================
onMounted(() => {
  fetchRepuestos()
  fetchHerramientas()
  fetchProveedores()  // v0.9.14
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <!-- TAB BAR -->
      <div class="tabs-bar">
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'repuestos' }"
          @click="activeTab = 'repuestos'"
        >
          Repuestos
        </button>
        <button
          class="tab-btn"
          :class="{ active: activeTab === 'herramientas' }"
          @click="activeTab = 'herramientas'"
        >
          Herramientas
        </button>
      </div>

      <!-- ============================================= -->
      <!-- REPUESTOS TAB -->
      <!-- ============================================= -->
      <template v-if="activeTab === 'repuestos'">
        <div class="top-bar">
          <h2>Almacen de Repuestos</h2>
          <div class="top-bar-actions">
            <div class="search-wrapper">
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
              </svg>
              <input
                v-model="searchQuery"
                type="search"
                class="search-input"
                placeholder="Nombre, serie, material..."
                autocomplete="off"
                aria-label="Buscar repuestos"
              >
            </div>
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
              <th>N. Serie</th>
              <th>Stock</th>
              <th>Ubicacion</th>
              <th>P. Ref.</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredRepuestos.length">
              <td class="table-empty-cell" colspan="7">
                {{ searchQuery.trim() ? 'No hay repuestos que coincidan con la busqueda.' : 'No hay repuestos registrados.' }}
              </td>
            </tr>
            <template v-else>
              <tr v-for="rep in paginatedRepuestos" :key="rep.id">
                <td>#{{ rep.id }}</td>
                <td>
                  <strong>{{ rep.nombre_repuesto }}</strong>
                </td>
                <td>{{ rep.numero_serie || 'N/A' }}</td>
                <td>
                  <span :class="isLowStock(rep) ? 'low-stock' : 'stock'">
                    {{ rep.cantidad_disponible }} {{ rep.unidad_medida }}
                  </span>
                </td>
                <td>{{ rep.ubicacion_almacen || 'Sin ubicar' }}</td>
                <td>{{ formatPrecio(rep.precio_referencia) }}</td>
                <td class="actions-cell">
                  <button type="button" class="btn-icon btn-view" title="Ver detalles" @click="openDetailModal(rep)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                    </svg>
                  </button>
                  <button type="button" class="btn-icon btn-edit" title="Editar" @click="openEditModal(rep)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                    </svg>
                  </button>
                  <button type="button" class="btn-icon btn-delete" title="Eliminar" @click="deleteRepuesto(rep.id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                      <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                    </svg>
                  </button>
                  <button type="button" class="btn-icon btn-doc" title="Documentos Adjuntos" @click="openDocsModal(rep)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1z"/>
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
          aria-label="Paginacion del inventario"
        >
          <button type="button" class="btn-pagination" :disabled="currentPage <= 1" @click="irPaginaAnterior">Anterior</button>
          <span class="table-pagination-meta">Pagina {{ currentPage }} de {{ totalPages }}</span>
          <button type="button" class="btn-pagination" :disabled="currentPage >= totalPages" @click="irPaginaSiguiente">Siguiente</button>
        </div>

        <div v-if="!loading && repuestos.length === 0" class="empty-state">No hay repuestos registrados.</div>
      </template>

      <!-- ============================================= -->
      <!-- HERRAMIENTAS TAB -->
      <!-- ============================================= -->
      <template v-if="activeTab === 'herramientas'">
        <div class="top-bar">
          <h2>Herramientas y Materiales</h2>
          <div class="top-bar-actions">
            <div class="search-wrapper">
              <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
              </svg>
              <input
                v-model="herrSearchQuery"
                type="search"
                class="search-input"
                placeholder="Nombre, identificacion, categoria..."
                autocomplete="off"
                aria-label="Buscar herramientas"
              >
            </div>
            <button class="btn-import" @click="herrOpenImportModal" title="Cargar herramientas desde Excel">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
              </svg>
              Cargar Excel
            </button>
            <button type="button" class="btn-primary" @click="herrOpenCreateModal">+ Agregar Herramienta</button>
          </div>
        </div>

        <div v-if="herrLoading">Cargando herramientas...</div>

        <table v-if="!herrLoading && herramientas.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nombre</th>
              <th>Categoria</th>
              <th>Cantidad</th>
              <th>Estado</th>
              <th>Ubicacion</th>
              <th>Costo</th>
              <th>Acciones</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="!filteredHerramientas.length">
              <td class="table-empty-cell" colspan="8">
                {{ herrSearchQuery.trim() ? 'No hay herramientas que coincidan con la busqueda.' : 'No hay herramientas registradas.' }}
              </td>
            </tr>
            <template v-else>
              <tr v-for="h in paginatedHerramientas" :key="h.id">
                <td>#{{ h.id }}</td>
                <td>
                  <strong>{{ h.nombre_herramienta }}</strong>
                </td>
                <td>
                  <span class="badge" :style="{ backgroundColor: getCategoriaColor(h.categoria) }">
                    {{ h.categoria || 'N/A' }}
                  </span>
                </td>
                <td>
                  <span class="stock">{{ h.cantidad_disponible }} {{ h.unidad_medida }}</span>
                </td>
                <td>
                  <span class="badge" :style="{ backgroundColor: getEstadoUsoColor(h.estado_uso) }">
                    {{ h.estado_uso || 'N/A' }}
                  </span>
                </td>
                <td>{{ h.ubicacion_almacen || 'Sin ubicar' }}</td>
                <td>{{ formatPrecio(h.costo_adquisicion) }}</td>
                <td class="actions-cell">
                  <button type="button" class="btn-icon btn-view" title="Ver detalles" @click="herrOpenDetailModal(h)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                    </svg>
                  </button>
                  <button type="button" class="btn-icon btn-edit" title="Editar" @click="herrOpenEditModal(h)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                    </svg>
                  </button>
                  <button type="button" class="btn-icon btn-delete" title="Eliminar" @click="herrDeleteHerramienta(h.id)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                      <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                    </svg>
                  </button>
                  <button type="button" class="btn-icon btn-doc" title="Documentos Adjuntos" @click="herrOpenDocsModal(h)">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1z"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </template>
          </tbody>
        </table>

        <div
          v-if="!herrLoading && herramientas.length && filteredHerramientas.length"
          class="table-pagination"
          role="navigation"
          aria-label="Paginacion de herramientas"
        >
          <button type="button" class="btn-pagination" :disabled="herrCurrentPage <= 1" @click="herrIrPaginaAnterior">Anterior</button>
          <span class="table-pagination-meta">Pagina {{ herrCurrentPage }} de {{ herrTotalPages }}</span>
          <button type="button" class="btn-pagination" :disabled="herrCurrentPage >= herrTotalPages" @click="herrIrPaginaSiguiente">Siguiente</button>
        </div>

        <div v-if="!herrLoading && herramientas.length === 0" class="empty-state">No hay herramientas registradas.</div>
      </template>
    </main>

    <!-- ============================================= -->
    <!-- MODALES REPUESTOS -->
    <!-- ============================================= -->

    <!-- Modal Importar Excel Repuestos -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal" style="width: 580px;">
        <h3>Importar Repuestos desde Excel</h3>
        <div v-if="!importResult && !importing">
          <div class="drop-zone" :class="{ 'drop-zone--active': importDragOver, 'drop-zone--has-file': importFile }" @dragover="handleDragOver" @dragleave="handleDragLeave" @drop="handleDrop" @click="$refs.fileInput.click()">
            <div v-if="!importFile" class="drop-zone-content">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" viewBox="0 0 16 16" style="color: #94a3b8;"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/></svg>
              <p class="drop-zone-text">Arrastre su archivo Excel o CSV aqui</p>
              <p class="drop-zone-subtext">o haga clic para seleccionar</p>
            </div>
            <div v-else class="drop-zone-content">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" viewBox="0 0 16 16" style="color: #27ae60;"><path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1zm-3.5 8l-1.5-1.5L5 10l1 1 3-3 .5.5-3.5 3.5z"/></svg>
              <p class="drop-zone-filename">{{ importFile.name }}</p>
              <p class="drop-zone-subtext">{{ (importFile.size / 1024).toFixed(1) }} KB</p>
            </div>
          </div>
          <input ref="fileInput" type="file" accept=".xlsx,.csv" style="display: none;" @change="handleFileSelect">
          <div class="import-info">
            <p><strong>Formato:</strong> Archivo .xlsx o .csv con encabezados en la primera fila.</p>
            <p><strong>Columnas obligatorias:</strong> nombre_repuesto, cantidad_disponible</p>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showImportModal = false">Cancelar</button>
            <button type="button" class="btn-outline" @click="downloadTemplate" title="Descargar plantilla Excel">Plantilla Excel</button>
            <button type="button" class="btn-outline" @click="downloadTemplateCSV" title="Descargar plantilla CSV">Plantilla CSV</button>
            <button type="button" class="btn-primary" :disabled="!importFile" @click="uploadExcel">Importar</button>
          </div>
        </div>
        <div v-if="importing" class="import-progress">
          <div class="spinner"></div>
          <p style="text-align: center; color: #475569;">Importando repuestos...</p>
        </div>
        <div v-if="importResult && !importing">
          <div class="import-result">
            <div class="result-summary">
              <div class="result-item result-success"><span class="result-number">{{ importResult.exitosos }}</span><span class="result-label">Nuevos</span></div>
              <div class="result-item result-updated"><span class="result-number">{{ importResult.actualizados }}</span><span class="result-label">Actualizados</span></div>
              <div class="result-item result-failed"><span class="result-number">{{ importResult.fallidos }}</span><span class="result-label">Fallidos</span></div>
              <div class="result-item result-total"><span class="result-number">{{ importResult.total_procesados }}</span><span class="result-label">Total</span></div>
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
            <button type="button" class="btn-secondary" @click="resetImport">Importar otro</button>
            <button type="button" class="btn-primary" @click="showImportModal = false">Cerrar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear / Editar Repuesto -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Repuesto' : 'Nuevo Repuesto' }}</h3>
        <form @submit.prevent="saveRepuesto">
          <div class="form-group">
            <label>Nombre *</label>
            <input v-model="formData.nombre_repuesto" type="text" required>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Numero de Serie</label>
              <input v-model="formData.numero_serie" type="text" placeholder="Serie del repuesto">
            </div>
            <div class="form-group">
              <label>Numero de Material</label>
              <input v-model="formData.numero_material" type="text" placeholder="Codigo del fabricante">
            </div>
          </div>
          <div class="form-group">
            <label>Imagen del Repuesto</label>
            <div class="imagen-upload-container">
              <div v-if="isEditing && formData.imagen_ruta && !imagenFile" class="imagen-existente">
                <a :href="`/uploads/${formData.imagen_ruta}`" target="_blank" class="imagen-link">{{ getImagenNombre(formData.imagen_ruta) }}</a>
                <button type="button" class="btn-icon-sm" @click="eliminarImagenRepuesto" title="Eliminar imagen">&#10005;</button>
              </div>
              <div v-if="imagenFile" class="imagen-nueva">
                <span class="imagen-filename">{{ imagenFile.name }}</span>
                <button type="button" class="btn-icon-sm" @click="imagenFile = null" title="Quitar seleccion">&#10005;</button>
                <button type="button" class="btn-subir-imagen" @click="subirImagenAhora" :disabled="subiendoImagen">
                  {{ subiendoImagen ? 'Subiendo...' : 'Subir imagen' }}
                </button>
              </div>
              <div class="imagen-upload-controls">
                <input type="file" ref="imagenInput" accept="image/*" @change="handleImagenSelect" style="display:none">
                <button type="button" class="btn-outline" @click="$refs.imagenInput.click()">
                  {{ formData.imagen_ruta && !imagenFile ? 'Cambiar imagen' : 'Seleccionar imagen' }}
                </button>
                <span v-if="!formData.imagen_ruta && !imagenFile && !isEditing" style="font-size: 0.82rem; color: #94a3b8;">Se subira al guardar</span>
                <span v-if="!formData.imagen_ruta && !imagenFile && isEditing" style="font-size: 0.82rem; color: #94a3b8;">Sin imagen</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>Descripcion / Notas</label>
            <textarea v-model="formData.descripcion" rows="2" placeholder="Detalle del repuesto, uso, etc."></textarea>
          </div>
          <div class="form-group">
            <label>Especificaciones Tecnicas</label>
            <textarea v-model="formData.especificaciones_tecnicas" rows="2" placeholder="Voltaje, tamano, capacidad, etc."></textarea>
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
                <option value="kit">kit</option>
                <option value="paquete">paquete</option>
                <option value="rollo">rollo</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Ubicacion en almacen</label>
              <input v-model="formData.ubicacion_almacen" type="text" placeholder="Ej: Estante B2">
            </div>
            <div class="form-group">
              <label>Stock minimo (alerta)</label>
              <input v-model.number="formData.nivel_stock_minimo" type="number" min="0" placeholder="Opcional">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Proveedor Ultimo</label>
              <div class="proveedor-row">
                <select v-model="formData.proveedor_ultimo_id" class="proveedor-select">
                  <option :value="null">— Sin proveedor —</option>
                  <option v-for="p in proveedores" :key="p.id" :value="p.id">
                    {{ p.nombre_empresa }}{{ p.ciudad ? ' (' + p.ciudad + ')' : '' }}
                  </option>
                </select>
                <button type="button" class="btn-add-proveedor" @click="abrirModalNuevoProveedor('repuesto')" title="Crear nuevo proveedor">
                  + Nuevo
                </button>
              </div>
              <!-- v0.9.14: campo de texto legacy oculto, se mantiene para compatibilidad -->
              <input type="hidden" v-model="formData.proveedor_ultimo">
            </div>
            <div class="form-group">
              <label>Fecha Ultima Entrada</label>
              <input v-model="formData.fecha_ultima_entrada" type="date">
            </div>
          </div>
          <div class="form-group">
            <label>Precio de Referencia (Bs.)</label>
            <input v-model.number="formData.precio_referencia" type="number" step="0.01" min="0" placeholder="Precio de referencia para costos">
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal detalle repuesto -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal modal-details">
        <h3>Detalle del repuesto: {{ selectedRepuesto.nombre_repuesto }}</h3>
        <div class="detail-grid">
          <div class="detail-column">
            <h4>Identificacion</h4>
            <p><strong>ID:</strong> #{{ selectedRepuesto.id }}</p>
            <p><strong>Nombre:</strong> {{ selectedRepuesto.nombre_repuesto }}</p>
            <p><strong>N. Serie:</strong> {{ selectedRepuesto.numero_serie || 'N/A' }}</p>
            <p><strong>N. Material:</strong> {{ selectedRepuesto.numero_material || 'N/A' }}</p>
            <p><strong>Ubicacion:</strong> {{ selectedRepuesto.ubicacion_almacen || 'Sin ubicar' }}</p>
            <p v-if="selectedRepuesto.imagen_ruta"><strong>Imagen:</strong> <a :href="`/uploads/${selectedRepuesto.imagen_ruta}`" target="_blank" class="imagen-link">{{ getImagenNombre(selectedRepuesto.imagen_ruta) }}</a></p>
          </div>
          <div class="detail-column">
            <h4>Inventario</h4>
            <p>
              <strong>Stock actual:</strong>
              <span :class="isLowStock(selectedRepuesto) ? 'low-stock' : 'stock'">
                {{ selectedRepuesto.cantidad_disponible }} {{ selectedRepuesto.unidad_medida }}
              </span>
            </p>
            <p><strong>Stock minimo:</strong> {{ selectedRepuesto.nivel_stock_minimo ?? 'No definido' }}</p>
            <p><strong>Proveedor ultimo:</strong> {{ getProveedorName(selectedRepuesto.proveedor_ultimo_id) || selectedRepuesto.proveedor_ultimo || 'N/A' }}</p>
            <p><strong>Fecha ultima entrada:</strong> {{ selectedRepuesto.fecha_ultima_entrada || 'N/A' }}</p>
            <p><strong>Precio referencia:</strong> {{ formatPrecio(selectedRepuesto.precio_referencia) }}</p>
          </div>
        </div>
        <div class="detail-full">
          <h4>Descripcion</h4>
          <div class="description-box">
            {{ selectedRepuesto.descripcion || 'Sin descripcion.' }}
          </div>
        </div>
        <div v-if="selectedRepuesto.especificaciones_tecnicas" class="detail-full">
          <h4>Especificaciones Tecnicas</h4>
          <div class="description-box">
            {{ selectedRepuesto.especificaciones_tecnicas }}
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- Modal Documentos Adjuntos Repuesto -->
    <div v-if="showDocsModal" class="modal-overlay" @click.self="showDocsModal = false">
      <div class="modal modal-docs">
        <h3>Documentos - {{ docsRepuesto.nombre_repuesto }}</h3>
        <DocumentosAdjuntos v-if="docsRepuesto.id" :repuestoId="docsRepuesto.id" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDocsModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ============================================= -->
    <!-- MODALES HERRAMIENTAS -->
    <!-- ============================================= -->

    <!-- Modal Importar Excel Herramientas -->
    <div v-if="herrShowImportModal" class="modal-overlay" @click.self="herrShowImportModal = false">
      <div class="modal" style="width: 580px;">
        <h3>Importar Herramientas desde Excel</h3>
        <div v-if="!herrImportResult && !herrImporting">
          <div class="drop-zone" :class="{ 'drop-zone--active': herrImportDragOver, 'drop-zone--has-file': herrImportFile }" @dragover="herrHandleDragOver" @dragleave="herrHandleDragLeave" @drop="herrHandleDrop" @click="$refs.herrFileInput.click()">
            <div v-if="!herrImportFile" class="drop-zone-content">
              <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" fill="currentColor" viewBox="0 0 16 16" style="color: #94a3b8;"><path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/><path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/></svg>
              <p class="drop-zone-text">Arrastre su archivo Excel o CSV aqui</p>
              <p class="drop-zone-subtext">o haga clic para seleccionar</p>
            </div>
            <div v-else class="drop-zone-content">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" fill="currentColor" viewBox="0 0 16 16" style="color: #27ae60;"><path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1zm-3.5 8l-1.5-1.5L5 10l1 1 3-3 .5.5-3.5 3.5z"/></svg>
              <p class="drop-zone-filename">{{ herrImportFile.name }}</p>
              <p class="drop-zone-subtext">{{ (herrImportFile.size / 1024).toFixed(1) }} KB</p>
            </div>
          </div>
          <input ref="herrFileInput" type="file" accept=".xlsx,.csv" style="display: none;" @change="herrHandleFileSelect">
          <div class="import-info">
            <p><strong>Formato:</strong> Archivo .xlsx o .csv con encabezados en la primera fila.</p>
            <p><strong>Columnas obligatorias:</strong> nombre_herramienta, cantidad_disponible</p>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="herrShowImportModal = false">Cancelar</button>
            <button type="button" class="btn-outline" @click="herrDownloadTemplate" title="Descargar plantilla Excel">Plantilla Excel</button>
            <button type="button" class="btn-primary" :disabled="!herrImportFile" @click="herrUploadExcel">Importar</button>
          </div>
        </div>
        <div v-if="herrImporting" class="import-progress">
          <div class="spinner"></div>
          <p style="text-align: center; color: #475569;">Importando herramientas...</p>
        </div>
        <div v-if="herrImportResult && !herrImporting">
          <div class="import-result">
            <div class="result-summary">
              <div class="result-item result-success"><span class="result-number">{{ herrImportResult.exitosos }}</span><span class="result-label">Nuevos</span></div>
              <div class="result-item result-updated"><span class="result-number">{{ herrImportResult.actualizados }}</span><span class="result-label">Actualizados</span></div>
              <div class="result-item result-failed"><span class="result-number">{{ herrImportResult.fallidos }}</span><span class="result-label">Fallidos</span></div>
              <div class="result-item result-total"><span class="result-number">{{ herrImportResult.total_procesados }}</span><span class="result-label">Total</span></div>
            </div>
            <div v-if="herrImportResult.errores && herrImportResult.errores.length > 0" class="import-errors">
              <h4>Detalle de errores</h4>
              <div class="error-list">
                <div v-for="(err, idx) in herrImportResult.errores" :key="idx" class="error-item">
                  <span class="error-fila">Fila {{ err.fila }}</span>
                  <span class="error-serie">({{ err.nombre }})</span>
                  <span class="error-msg">{{ err.errores.join(', ') }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="herrResetImport">Importar otro</button>
            <button type="button" class="btn-primary" @click="herrShowImportModal = false">Cerrar</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal Crear / Editar Herramienta -->
    <div v-if="herrShowModal" class="modal-overlay" @click.self="herrShowModal = false">
      <div class="modal">
        <h3>{{ herrIsEditing ? 'Editar Herramienta' : 'Nueva Herramienta' }}</h3>
        <form @submit.prevent="herrSaveHerramienta">
          <div class="form-group">
            <label>Nombre de la Herramienta *</label>
            <input v-model="herrFormData.nombre_herramienta" type="text" required>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Numero de Identificacion</label>
              <input v-model="herrFormData.numero_identificacion" type="text" placeholder="Codigo o serie de la herramienta">
            </div>
            <div class="form-group">
              <label>Categoria *</label>
              <select v-model="herrFormData.categoria" required>
                <option v-for="cat in categoriasHerramienta" :key="cat" :value="cat">{{ cat }}</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Imagen de la Herramienta</label>
            <div class="imagen-upload-container">
              <div v-if="herrIsEditing && herrFormData.imagen_ruta && !herrImagenFile" class="imagen-existente">
                <a :href="`/uploads/${herrFormData.imagen_ruta}`" target="_blank" class="imagen-link">{{ getImagenNombre(herrFormData.imagen_ruta) }}</a>
                <button type="button" class="btn-icon-sm" @click="herrEliminarImagen" title="Eliminar imagen">&#10005;</button>
              </div>
              <div v-if="herrImagenFile" class="imagen-nueva">
                <span class="imagen-filename">{{ herrImagenFile.name }}</span>
                <button type="button" class="btn-icon-sm" @click="herrImagenFile = null" title="Quitar seleccion">&#10005;</button>
                <button type="button" class="btn-subir-imagen" @click="herrSubirImagenAhora" :disabled="herrSubiendoImagen">
                  {{ herrSubiendoImagen ? 'Subiendo...' : 'Subir imagen' }}
                </button>
              </div>
              <div class="imagen-upload-controls">
                <input type="file" ref="herrImagenInput" accept="image/*" @change="herrHandleImagenSelect" style="display:none">
                <button type="button" class="btn-outline" @click="$refs.herrImagenInput.click()">
                  {{ herrFormData.imagen_ruta && !herrImagenFile ? 'Cambiar imagen' : 'Seleccionar imagen' }}
                </button>
                <span v-if="!herrFormData.imagen_ruta && !herrImagenFile && !herrIsEditing" style="font-size: 0.82rem; color: #94a3b8;">Se subira al guardar</span>
                <span v-if="!herrFormData.imagen_ruta && !herrImagenFile && herrIsEditing" style="font-size: 0.82rem; color: #94a3b8;">Sin imagen</span>
              </div>
            </div>
          </div>
          <div class="form-group">
            <label>Descripcion</label>
            <textarea v-model="herrFormData.descripcion" rows="2" placeholder="Detalle de la herramienta, uso, etc."></textarea>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>{{ herrIsEditing ? 'Cantidad disponible' : 'Cantidad inicial' }}</label>
              <input v-model.number="herrFormData.cantidad_disponible" type="number" min="0" required>
            </div>
            <div class="form-group">
              <label>Unidad</label>
              <select v-model="herrFormData.unidad_medida">
                <option value="unidad">unidad</option>
                <option value="par">par</option>
                <option value="metro">metro</option>
                <option value="litro">litro</option>
                <option value="kit">kit</option>
                <option value="paquete">paquete</option>
                <option value="rollo">rollo</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Ubicacion en almacen</label>
              <input v-model="herrFormData.ubicacion_almacen" type="text" placeholder="Ej: Estante B2">
            </div>
            <div class="form-group">
              <label>Estado de Uso *</label>
              <select v-model="herrFormData.estado_uso" required>
                <option v-for="est in estadosUso" :key="est" :value="est">{{ est }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Costo de Adquisicion (Bs.)</label>
              <input v-model.number="herrFormData.costo_adquisicion" type="number" step="0.01" min="0" placeholder="Costo de compra">
            </div>
            <div class="form-group">
              <label>Fecha de Adquisicion</label>
              <input v-model="herrFormData.fecha_adquisicion" type="date">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Proveedor Ultimo</label>
              <div class="proveedor-row">
                <select v-model="herrFormData.proveedor_ultimo_id" class="proveedor-select">
                  <option :value="null">— Sin proveedor —</option>
                  <option v-for="p in proveedores" :key="p.id" :value="p.id">
                    {{ p.nombre_empresa }}{{ p.ciudad ? ' (' + p.ciudad + ')' : '' }}
                  </option>
                </select>
                <button type="button" class="btn-add-proveedor" @click="abrirModalNuevoProveedor('herramienta')" title="Crear nuevo proveedor">
                  + Nuevo
                </button>
              </div>
              <input type="hidden" v-model="herrFormData.proveedor_ultimo">
            </div>
          </div>
          <div class="form-group">
            <label>Observaciones</label>
            <textarea v-model="herrFormData.observaciones" rows="2" placeholder="Observaciones adicionales"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="herrShowModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal detalle herramienta -->
    <div v-if="herrShowDetailModal" class="modal-overlay" @click.self="herrShowDetailModal = false">
      <div class="modal modal-details">
        <h3>Detalle de la herramienta: {{ herrSelected.nombre_herramienta }}</h3>
        <div class="detail-grid">
          <div class="detail-column">
            <h4>Identificacion</h4>
            <p><strong>ID:</strong> #{{ herrSelected.id }}</p>
            <p><strong>Nombre:</strong> {{ herrSelected.nombre_herramienta }}</p>
            <p><strong>N. Identificacion:</strong> {{ herrSelected.numero_identificacion || 'N/A' }}</p>
            <p><strong>Categoria:</strong> <span class="badge" :style="{ backgroundColor: getCategoriaColor(herrSelected.categoria) }">{{ herrSelected.categoria || 'N/A' }}</span></p>
            <p><strong>Ubicacion:</strong> {{ herrSelected.ubicacion_almacen || 'Sin ubicar' }}</p>
            <p v-if="herrSelected.imagen_ruta"><strong>Imagen:</strong> <a :href="`/uploads/${herrSelected.imagen_ruta}`" target="_blank" class="imagen-link">{{ getImagenNombre(herrSelected.imagen_ruta) }}</a></p>
          </div>
          <div class="detail-column">
            <h4>Inventario y Estado</h4>
            <p>
              <strong>Cantidad:</strong>
              <span class="stock">{{ herrSelected.cantidad_disponible }} {{ herrSelected.unidad_medida }}</span>
            </p>
            <p>
              <strong>Estado:</strong>
              <span class="badge" :style="{ backgroundColor: getEstadoUsoColor(herrSelected.estado_uso) }">{{ herrSelected.estado_uso || 'N/A' }}</span>
            </p>
            <p><strong>Costo adquisicion:</strong> {{ formatPrecio(herrSelected.costo_adquisicion) }}</p>
            <p><strong>Fecha adquisicion:</strong> {{ herrSelected.fecha_adquisicion || 'N/A' }}</p>
            <p><strong>Proveedor ultimo:</strong> {{ getProveedorName(herrSelected.proveedor_ultimo_id) || herrSelected.proveedor_ultimo || 'N/A' }}</p>
          </div>
        </div>
        <div v-if="herrSelected.descripcion" class="detail-full">
          <h4>Descripcion</h4>
          <div class="description-box">
            {{ herrSelected.descripcion }}
          </div>
        </div>
        <div v-if="herrSelected.observaciones" class="detail-full">
          <h4>Observaciones</h4>
          <div class="description-box">
            {{ herrSelected.observaciones }}
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn-secondary" @click="herrShowDetailModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- Modal Documentos Adjuntos Herramienta -->
    <div v-if="herrShowDocsModal" class="modal-overlay" @click.self="herrShowDocsModal = false">
      <div class="modal modal-docs">
        <h3>Documentos - {{ docsHerramienta.nombre_herramienta }}</h3>
        <DocumentosAdjuntos v-if="docsHerramienta.id" :herramientaId="docsHerramienta.id" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="herrShowDocsModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- v0.9.14: Modal Crear Proveedor al vuelo (compartido por Repuestos y Herramientas) -->
    <div v-if="showNuevoProveedorModal" class="modal-overlay" @click.self="showNuevoProveedorModal = false">
      <div class="modal" style="width: 420px;">
        <h3>Crear Nuevo Proveedor</h3>
        <p style="font-size: 0.85rem; color: #64748b; margin-bottom: 1rem;">
          Ingrese solo el nombre de la empresa. Los demás datos (ciudad, dirección, contactos)
          podrá completarlos después desde la página de Proveedores.
        </p>
        <form @submit.prevent="crearProveedorAlVuelo">
          <div class="form-group">
            <label>Nombre de la Empresa *</label>
            <input v-model="nuevoProveedorNombre" type="text" required placeholder="Ej: TechMed Bolivia SRL" autofocus>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showNuevoProveedorModal = false">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="creandoProveedor">
              {{ creandoProveedor ? 'Creando...' : 'Crear Proveedor' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

/* Tabs */
.tabs-bar {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e2e8f0;
  margin-bottom: 1rem;
}
.tab-btn {
  padding: 0.65rem 1.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  color: #64748b;
  background: none;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
}
.tab-btn:hover { color: #334155; }
.tab-btn.active {
  color: #1B4332;
  border-bottom-color: #1B4332;
}

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

/* Buscador con icono */
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

table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }

.table-empty-cell { text-align: center; color: #64748b; padding: 1.5rem 12px; font-size: 0.95rem; }
.empty-state { text-align: center; color: #64748b; padding: 2rem; margin-top: 1rem; }
.stock { color: #27ae60; font-weight: bold; }
.low-stock { color: #e74c3c; font-weight: bold; }

/* Badge for categorias and estados */
.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 0.78rem;
  font-weight: 600;
  color: #fff;
  white-space: nowrap;
}

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

.actions-cell { display: flex; gap: 0.5rem; align-items: center; }
.btn-icon {
  background: #f0f2f5; color: #555;
  border: none; padding: 8px; border-radius: 6px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
/* v0.9.14: Iconos estilo Equipos — gris por defecto, color solo en hover */
.btn-view:hover { background: #16a34a; color: #ffffff; }
.btn-edit:hover { background: #2563eb; color: #ffffff; }
.btn-delete:hover { background: #dc2626; color: #ffffff; }
.btn-doc:hover { background: #0891b2; color: #ffffff; }

/* v0.9.14: Dropdown de proveedor con botón "+ Nuevo" */
.proveedor-row { display: flex; gap: 0.5rem; align-items: center; }
.proveedor-select {
  flex: 1; padding: 0.5rem 0.7rem; border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.9rem; background: #fff; box-sizing: border-box; font-family: inherit;
}
.proveedor-select:focus { outline: none; border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59,130,246,0.15); }
.btn-add-proveedor {
  background-color: #f59e0b; color: white; border: none;
  padding: 0.5rem 0.85rem; border-radius: 6px; cursor: pointer;
  font-weight: 600; font-size: 0.85rem; white-space: nowrap; transition: background 0.2s;
}
.btn-add-proveedor:hover { background-color: #d97706; }

/* Imagen upload */
.imagen-upload-container { display: flex; flex-direction: column; gap: 0.4rem; }
.imagen-existente { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.6rem; background: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; }
.imagen-nueva { display: flex; align-items: center; gap: 0.5rem; padding: 0.4rem 0.6rem; background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; flex-wrap: wrap; }
.btn-subir-imagen {
  background-color: #2563eb; color: white; border: none;
  padding: 0.3rem 0.7rem; border-radius: 4px; cursor: pointer;
  font-weight: 600; font-size: 0.82rem; transition: background 0.2s;
}
.btn-subir-imagen:hover:not(:disabled) { background-color: #1d4ed8; }
.btn-subir-imagen:disabled { opacity: 0.5; cursor: not-allowed; }
.imagen-link {
  color: #2563eb; text-decoration: none; font-weight: 600; font-size: 0.88rem;
  display: inline; transition: color 0.2s;
}
.imagen-link:hover { color: #1d4ed8; text-decoration: underline; }
.imagen-upload-controls { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; }
.imagen-filename { font-size: 0.82rem; color: #27ae60; font-weight: 600; }
.btn-icon-sm {
  background: #fee2e2; border: none; color: #c0392b; width: 22px; height: 22px;
  border-radius: 50%; cursor: pointer; font-size: 0.75rem; display: flex;
  align-items: center; justify-content: center; transition: background 0.2s;
}

/* Modales */
.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(0, 0, 0, 0.5); display: flex; justify-content: center;
  align-items: center; z-index: 100;
}
.modal {
  background: white; padding: 2rem; border-radius: 8px; width: 500px;
  max-width: 90%; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  max-height: 90vh; overflow-y: auto;
}
.modal-details { width: 640px; }
.modal-docs { width: 700px; }

.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: bold; }
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px;
  box-sizing: border-box; background-color: white; font-family: inherit;
}
.form-group textarea { resize: vertical; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

.detail-grid { display: flex; gap: 2rem; margin-bottom: 1.5rem; }
.detail-column { flex: 1; }
.detail-column h4 { margin-bottom: 0.8rem; color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 0.3rem; }
.detail-column p { margin: 0 0 0.5rem 0; font-size: 0.9rem; color: #555; }
.detail-full { width: 100%; background: #f8f9fa; padding: 1rem; border-radius: 6px; margin-bottom: 1rem; }
.detail-full h4 { margin-top: 0; margin-bottom: 0.5rem; color: #2c3e50; }
.description-box {
  word-break: break-word; overflow-y: auto; max-height: 160px; white-space: pre-wrap;
  background: white; padding: 0.8rem; border: 1px solid #e0e0e0; border-radius: 4px;
  min-height: 50px; color: #444; font-size: 0.9rem;
}

.table-pagination {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
  gap: 1rem; margin-top: 1rem; padding: 0.75rem 0;
}
.table-pagination-meta { font-size: 0.9rem; color: #475569; }
.btn-pagination {
  background-color: #3498db; color: white; border: none; padding: 0.5rem 1.1rem;
  border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem;
}
.btn-pagination:hover:not(:disabled) { background-color: #2980b9; }
.btn-pagination:disabled { opacity: 0.45; cursor: not-allowed; }

/* Importar Excel */
.drop-zone {
  border: 2px dashed #cbd5e1; border-radius: 10px; padding: 2rem 1.5rem;
  text-align: center; cursor: pointer; transition: all 0.25s ease;
  margin-bottom: 1rem; background: #f8fafc;
}
.drop-zone:hover { border-color: #3498db; background: #f0f7ff; }
.drop-zone--active { border-color: #3498db; background: #e8f4fd; border-style: solid; }
.drop-zone--has-file { border-color: #27ae60; border-style: solid; background: #f0fdf4; }
.drop-zone-content { display: flex; flex-direction: column; align-items: center; gap: 0.4rem; }
.drop-zone-text { font-size: 1rem; font-weight: 600; color: #475569; margin: 0; }
.drop-zone-subtext { font-size: 0.85rem; color: #94a3b8; margin: 0; }
.drop-zone-filename { font-size: 0.95rem; font-weight: 600; color: #27ae60; margin: 0; word-break: break-all; }
.import-info { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.85rem; color: #475569; }
.import-info p { margin: 0.2rem 0; }
.import-progress { padding: 2rem; display: flex; flex-direction: column; align-items: center; gap: 1rem; }
.spinner { width: 40px; height: 40px; border: 4px solid #e2e8f0; border-top-color: #3498db; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.import-result { margin-bottom: 1rem; }
.result-summary { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; margin-bottom: 1rem; }
.result-item { text-align: center; padding: 0.75rem; border-radius: 8px; }
.result-number { display: block; font-size: 1.6rem; font-weight: 700; line-height: 1.2; }
.result-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; color: #64748b; }
.result-success { background: #f0fdf4; } .result-success .result-number { color: #16a34a; }
.result-updated { background: #eff6ff; } .result-updated .result-number { color: #2563eb; }
.result-failed { background: #fef2f2; } .result-failed .result-number { color: #dc2626; }
.result-total { background: #f8fafc; border: 1px solid #e2e8f0; } .result-total .result-number { color: #1e293b; }
.import-errors { background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 0.75rem; }
.import-errors h4 { margin: 0 0 0.5rem 0; color: #991b1b; font-size: 0.9rem; }
.error-list { max-height: 200px; overflow-y: auto; }
.error-item { padding: 0.35rem 0; font-size: 0.83rem; color: #7f1d1d; border-bottom: 1px solid #fecaca; }
.error-item:last-child { border-bottom: none; }
.error-fila { font-weight: 700; }
.error-serie { color: #991b1b; font-size: 0.8rem; }
.error-msg { color: #b91c1c; }
</style>
