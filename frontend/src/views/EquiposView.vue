<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'
import DocumentosAdjuntos from '../components/DocumentosAdjuntos.vue'

// --- Variables Generales ---
const equipos = ref([])
const estados = ref([])
const proveedores = ref([])  // v0.9.0: reemplaza tecnicos
const loading = ref(true)
const error_msg = ref('')
const contratosEquipo = ref([])  // v0.9.2: contratos del equipo en detalle

const PAGE_SIZE = 10
const currentPage = ref(1)
const searchQuery = ref('')

// --- Filtros de busqueda v0.9.0 ---
const filterUbicacion = ref('')
const filterEstado = ref('')
const filterCondicion = ref('')

// --- Variables Modal ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})

// v0.9.0: Variables para crear proveedor al vuelo
const showNuevoProveedorModal = ref(false)
const nuevoProveedorNombre = ref('')
const creandoProveedor = ref(false)

// --- Variables Historial ---
const showHistoryModal = ref(false)
const historyData = ref([])
const selectedEquipName = ref('')

// --- Variables Modal Detalle ---
const showDetailModal = ref(false)
const selectedEquipo = ref({})

// --- Variables Modal Documentos ---
const showDocsModal = ref(false)
const docsEquipo = ref({})

// --- Variables Modal Importar Excel ---
const showImportModal = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importDragOver = ref(false)

// --- Variables Imagen Upload ---
const imagenFile = ref(null)
const imagenPreview = ref('')
const subiendoImagen = ref(false)

// v0.9.0: Valores válidos para condicion_origen
const CONDICIONES_ORIGEN = [
  'Compra', 'Donación', 'Préstamo', 'Demostración', 'Evaluación',
  'Leasing', 'Renta', 'Comodato', 'Otro'
]

// Función para abrir el modal de detalles
const openDetailModal = async (equipo) => {
  selectedEquipo.value = equipo
  contratosEquipo.value = []  // v0.9.2: limpiar antes de cargar
  showDetailModal.value = true
  // v0.9.2: Cargar contratos del equipo
  try {
    const res = await apiClient.get(`/contratos/?equipo_id=${equipo.id}`)
    contratosEquipo.value = res.data
  } catch (e) {
    console.warn('No se pudieron cargar contratos del equipo', e)
  }
}

// Función para abrir el modal de documentos
const openDocsModal = (equipo) => {
  docsEquipo.value = equipo
  showDocsModal.value = true
}

// v0.9.0: Helper para mostrar el nombre del proveedor
const getProveedorName = (id) => {
  if (!id) return 'N/A'
  const prov = proveedores.value.find(p => p.id === id)
  return prov ? prov.nombre_empresa : 'N/A'
}

// v0.9.0: Badge de garantía mejorado (usa fecha_inicio y fecha_fin)
const getGarantiaBadge = (equipo) => {
  if (!equipo.fecha_fin_garantia) return { text: '', class: '' }
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  const fin = new Date(equipo.fecha_fin_garantia)
  if (fin < hoy) return { text: 'Garantía vencida', class: 'badge-garantia-vencida' }
  const diasRestantes = Math.ceil((fin - hoy) / (1000 * 60 * 60 * 24))
  if (diasRestantes <= 30) return { text: `Garantía por vencer (${diasRestantes}d)`, class: 'badge-garantia-proxima' }
  return { text: 'En garantía', class: 'badge-garantia' }
}

// Helper: ¿Equipo en garantía?
const enGarantia = (fechaFinGarantia) => {
  if (!fechaFinGarantia) return false
  const fin = new Date(fechaFinGarantia)
  const hoy = new Date()
  hoy.setHours(0, 0, 0, 0)
  return fin >= hoy
}

// Función para seleccionar imagen
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

// Helper: obtener nombre legible de la ruta de imagen
const getImagenNombre = (ruta) => {
  if (!ruta) return ''
  // Extraer solo el nombre del archivo de la ruta
  const parts = ruta.split('/')
  return parts[parts.length - 1] || ruta
}

// Eliminar imagen del equipo
const eliminarImagenEquipo = async () => {
  if (!confirm('¿Eliminar la imagen de este equipo?')) return
  try {
    await apiClient.delete(`/equipos/${formData.value.id}/imagen`)
    formData.value.imagen_ruta = null
    imagenFile.value = null
    imagenPreview.value = ''
    alert('Imagen eliminada')
    fetchEquipos()
  } catch (error) {
    alert('Error al eliminar la imagen')
  }
}

// Subir imagen inmediatamente (para cuando ya existe el equipo)
const subirImagenAhora = async () => {
  if (!imagenFile.value) return
  const equipoId = formData.value.id
  if (!equipoId) {
    alert('Guarde el equipo primero antes de subir la imagen')
    return
  }
  try {
    subiendoImagen.value = true
    const imgFormData = new FormData()
    imgFormData.append('file', imagenFile.value)
    const res = await apiClient.post(`/equipos/${equipoId}/upload_imagen`, imgFormData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    formData.value.imagen_ruta = res.data.imagen_ruta
    imagenFile.value = null
    alert('Imagen subida correctamente')
    fetchEquipos()
  } catch (error) {
    alert('Error al subir la imagen: ' + (error.response?.data?.detail || error.message))
  } finally {
    subiendoImagen.value = false
  }
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

// v0.9.0: Cargar proveedores para el dropdown del formulario
const fetchProveedores = async () => {
  try {
    const res = await apiClient.get('/equipos/proveedores')
    proveedores.value = res.data
  } catch (error) {
    console.error("Error al cargar proveedores:", error)
    // Fallback: intentar con /proveedores/
    try {
      const res2 = await apiClient.get('/proveedores/')
      proveedores.value = res2.data.map(p => ({ id: p.id, nombre_empresa: p.nombre_empresa, ciudad: p.ciudad }))
    } catch (e) {
      console.error("Fallback también falló:", e)
    }
  }
}

// v0.9.0: Opciones de filtros (derivadas de datos)
const ubicacionesUnicas = computed(() => {
  const vals = new Set()
  equipos.value.forEach(eq => { if (eq.ubicacion_actual) vals.add(eq.ubicacion_actual) })
  return Array.from(vals).sort()
})

const tieneFiltrosActivos = computed(() => {
  return searchQuery.value.trim() || filterUbicacion.value || filterEstado.value || filterCondicion.value
})

const limpiarFiltros = () => {
  searchQuery.value = ''
  filterUbicacion.value = ''
  filterEstado.value = ''
  filterCondicion.value = ''
}

const filteredEquipos = computed(() => {
  let result = equipos.value

  // v0.9.0: Búsqueda por nombre/marca/modelo + numero_serie/numero_material
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    result = result.filter((eq) => {
      const nombre = String(eq.nombre_corto ?? '').toLowerCase()
      const marca = String(eq.marca ?? '').toLowerCase()
      const modelo = String(eq.modelo ?? '').toLowerCase()
      const serie = String(eq.numero_serie ?? '').toLowerCase()
      const material = String(eq.numero_material ?? '').toLowerCase()
      return nombre.includes(q) || marca.includes(q) || modelo.includes(q) || serie.includes(q) || material.includes(q)
    })
  }

  // v0.9.0: Filtro por ubicación
  if (filterUbicacion.value) {
    result = result.filter(eq => eq.ubicacion_actual === filterUbicacion.value)
  }

  // v0.9.0: Filtro por estado
  if (filterEstado.value) {
    result = result.filter(eq => eq.estado_id === parseInt(filterEstado.value))
  }

  // v0.9.0: Filtro por condición de origen
  if (filterCondicion.value) {
    result = result.filter(eq => eq.condicion_origen === filterCondicion.value)
  }

  return result
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

watch([searchQuery, filterUbicacion, filterEstado, filterCondicion], () => {
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
    numero_material: '',
    marca: '',
    fecha_adquisicion: '',
    fecha_inicio_garantia: '',   // v0.9.0
    fecha_fin_garantia: '',
    ubicacion_actual: '',
    estado_id: 1,
    proveedor_principal_id: null,  // v0.9.0: FK (era texto)
    condicion_origen: '',          // v0.9.0: nuevo
    descripcion: '',
    observaciones: '',             // v0.9.0: nuevo
    imagen_ruta: '',
  }
  imagenFile.value = null
  imagenPreview.value = ''
  showModal.value = true
}

const openEditModal = (equipo) => {
  isEditing.value = true
  formData.value = { ...equipo }

  // Convertir fechas a formato YYYY-MM-DD para el input type="date"
  if (equipo.fecha_adquisicion) {
    formData.value.fecha_adquisicion = equipo.fecha_adquisicion.substring(0, 10)
  }
  if (equipo.fecha_inicio_garantia) {
    formData.value.fecha_inicio_garantia = equipo.fecha_inicio_garantia.substring(0, 10)
  } else {
    formData.value.fecha_inicio_garantia = ''
  }
  if (equipo.fecha_fin_garantia) {
    formData.value.fecha_fin_garantia = equipo.fecha_fin_garantia.substring(0, 10)
  } else {
    formData.value.fecha_fin_garantia = ''
  }

  imagenFile.value = null
  imagenPreview.value = equipo.imagen_ruta ? `/uploads/${equipo.imagen_ruta}` : ''
  showModal.value = true
}

const saveEquipo = async () => {
  try {
    const payload = { ...formData.value };

    // Limpiar campos vacíos a null
    if (payload.fecha_adquisicion === "") payload.fecha_adquisicion = null;
    if (payload.fecha_inicio_garantia === "") payload.fecha_inicio_garantia = null;
    if (payload.fecha_fin_garantia === "") payload.fecha_fin_garantia = null;
    if (payload.proveedor_principal_id === "") payload.proveedor_principal_id = null;
    if (payload.condicion_origen === "") payload.condicion_origen = null;

    // v0.9.0: NO enviar campos no editables al editar (modelo, marca, numero_serie)
    // El backend los rechazaría. El schema EquipoUpdate no los incluye, así que
    // el backend simplemente los ignora, pero por limpieza los removemos del payload.
    if (isEditing.value) {
      delete payload.modelo;
      delete payload.marca;
      delete payload.numero_serie;
    }

    let equipoId;
    if (isEditing.value) {
      await apiClient.put(`/equipos/${payload.id}`, payload)
      equipoId = payload.id
    } else {
      const res = await apiClient.post('/equipos/', payload)
      equipoId = res.data.id
    }

    // Subir imagen si se seleccionó una
    if (imagenFile.value && equipoId) {
      const imgFormData = new FormData()
      imgFormData.append('file', imagenFile.value)
      await apiClient.post(`/equipos/${equipoId}/upload_imagen`, imgFormData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
    }

    alert(isEditing.value ? 'Equipo actualizado' : 'Equipo creado')
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
      // v0.9.0: mostrar el mensaje detallado del backend (dependencias)
      if (error.response && error.response.data && error.response.data.detail) {
        alert('No se puede eliminar:\n\n' + error.response.data.detail)
      } else {
        alert('Error al eliminar el equipo')
      }
    }
  }
}

// v0.9.0: Crear proveedor al vuelo desde el formulario de equipo
const abrirModalNuevoProveedor = () => {
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
    const res = await apiClient.post('/equipos/from-proveedor-nombre', {
      nombre_empresa: nombre
    })
    // Recargar lista de proveedores
    await fetchProveedores()
    // Seleccionar el proveedor recién creado
    formData.value.proveedor_principal_id = res.data.id
    showNuevoProveedorModal.value = false
    alert(`Proveedor "${nombre}" creado. Podrás completar sus datos en la página de Proveedores.`)
  } catch (error) {
    if (error.response?.data?.detail) {
      alert('Error: ' + error.response.data.detail)
    } else {
      alert('Error al crear el proveedor')
    }
  } finally {
    creandoProveedor.value = false
  }
}

// --- Función Historial ---
const openHistory = async (equipo) => {
  selectedEquipName.value = equipo.nombre_corto || equipo.modelo
  try {
    const res = await apiClient.get(`/historial/equipo/${equipo.id}`)
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

const downloadTemplate = () => {
  // Descarga directa desde archivos estáticos en /public/plantillas/
  // (sin llamar al backend, más rápido y funciona offline)
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_equipos.xlsx`
  link.download = 'CMMS-BioAI_Plantilla_Equipos.xlsx'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const downloadTemplateCSV = () => {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_equipos.csv`
  link.download = 'CMMS-BioAI_Plantilla_Equipos.csv'
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
  fetchProveedores()  // v0.9.0: reemplaza fetchTecnicos
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Gestión de Equipos Médicos</h2>
        <div class="top-bar-actions">
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input
              v-model="searchQuery"
              type="search"
              class="search-input"
              placeholder="Nombre, marca, modelo..."
              autocomplete="off"
              aria-label="Buscar equipos"
            >
          </div>
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
      
      <!-- v0.9.0: Barra de filtros (ubicacion, estado, condicion_origen) -->
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Ubicación:</label>
          <select v-model="filterUbicacion" class="filter-select">
            <option value="">Todas</option>
            <option v-for="u in ubicacionesUnicas" :key="u" :value="u">{{ u }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Estado:</label>
          <select v-model="filterEstado" class="filter-select">
            <option value="">Todos</option>
            <option v-for="e in estados" :key="e.id" :value="e.id">{{ e.nombre_estado }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Condición:</label>
          <select v-model="filterCondicion" class="filter-select">
            <option value="">Todas</option>
            <option v-for="c in CONDICIONES_ORIGEN" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <button v-if="tieneFiltrosActivos" class="btn-clear-filters" @click="limpiarFiltros" title="Limpiar todos los filtros">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
          </svg>
          Limpiar
        </button>
        <span v-if="tieneFiltrosActivos" class="filter-count">{{ filteredEquipos.length }} de {{ equipos.length }}</span>
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
            <th>Condición</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredEquipos.length">
            <td class="table-empty-cell" colspan="8">
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
            <td>{{ equipo.nombre_corto || 'N/A' }}</td>
            <td>{{ equipo.modelo }}</td>
            <td>{{ equipo.marca }}</td>
            <td>{{ equipo.ubicacion_actual }}</td>
            <td>
              <span class="badge" :style="{ backgroundColor: getEstadoColor(equipo.estado_id) }">
                {{ getNombreEstado(equipo.estado_id) }}
              </span>
              <span v-if="getGarantiaBadge(equipo).text" :class="getGarantiaBadge(equipo).class" :title="`Fin garantía: ${equipo.fecha_fin_garantia}`">
                {{ getGarantiaBadge(equipo).text }}
              </span>
            </td>
            <td>
              <span v-if="equipo.condicion_origen" class="badge-condicion">{{ equipo.condicion_origen }}</span>
              <span v-else>—</span>
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
              <button class="btn-icon btn-doc-icon" title="Documentos Adjuntos" @click="openDocsModal(equipo)">
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
            <p><strong>Columnas obligatorias:</strong> modelo, numero_serie, marca</p>
            <p><strong>Fechas:</strong> Si no tiene fecha de adquisicion, se asigna 1900-01-01 automaticamente.</p>
            <p>Si el numero_serie ya existe, el equipo se <strong>actualizara</strong> con los nuevos datos.</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showImportModal = false">Cancelar</button>
            <button type="button" class="btn-outline" @click="downloadTemplate" title="Descargar plantilla Excel con datos de ejemplo">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
              </svg>
              Plantilla Excel
            </button>
            <button type="button" class="btn-outline" @click="downloadTemplateCSV" title="Descargar plantilla CSV">
              <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16" style="vertical-align: -2px; margin-right: 4px;">
                <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
                <path d="M7.646 11.854a.5.5 0 0 0 .708 0l3-3a.5.5 0 0 0-.708-.708L8.5 10.293V1.5a.5.5 0 0 0-1 0v8.793L5.354 8.146a.5.5 0 1 0-.708.708l3 3z"/>
              </svg>
              Plantilla CSV
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
          <!-- v0.9.0: Advertencia ROJA para campos no editables en modo edición -->
          <div v-if="isEditing" class="warning-no-editable">
            ⚠️ <strong>Campos no modificables:</strong> Marca, Modelo y Número de Serie
            NO se pueden cambiar después de creado el equipo porque afectan la estructura
            de carpetas y archivos del sistema. Si necesita corregir un error, elimine el
            equipo y créelo de nuevo.
          </div>

          <div class="form-group">
            <label>Nombre Corto *</label>
            <input v-model="formData.nombre_corto" type="text" required placeholder="Ej: Monitor UCI 02">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Marca *</label>
              <input v-model="formData.marca" type="text" required :disabled="isEditing"
                :class="{ 'input-locked': isEditing }" :title="isEditing ? 'No modificable después de creado' : ''">
            </div>
            <div class="form-group">
              <label>Modelo *</label>
              <input v-model="formData.modelo" type="text" required :disabled="isEditing"
                :class="{ 'input-locked': isEditing }" :title="isEditing ? 'No modificable después de creado' : ''">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Número de Serie *</label>
              <input v-model="formData.numero_serie" type="text" required placeholder="Único" :disabled="isEditing"
                :class="{ 'input-locked': isEditing }" :title="isEditing ? 'No modificable después de creado' : ''">
            </div>
            <div class="form-group">
              <label>Número de Material</label>
              <input v-model="formData.numero_material" type="text" placeholder="Variante del modelo">
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Fecha Adquisición</label>
              <input v-model="formData.fecha_adquisicion" type="date">
            </div>
            <div class="form-group">
              <label>Condición de Origen</label>
              <select v-model="formData.condicion_origen">
                <option value="">— Seleccionar —</option>
                <option v-for="c in CONDICIONES_ORIGEN" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Inicio Garantía</label>
              <input v-model="formData.fecha_inicio_garantia" type="date">
            </div>
            <div class="form-group">
              <label>Fin de Garantía</label>
              <input v-model="formData.fecha_fin_garantia" type="date">
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
          <!-- v0.9.0: Proveedor como FK con dropdown + "Crear nuevo" -->
          <div class="form-group">
            <label>Proveedor Principal</label>
            <div class="proveedor-row">
              <select v-model="formData.proveedor_principal_id" class="proveedor-select">
                <option :value="null">— Sin proveedor —</option>
                <option v-for="p in proveedores" :key="p.id" :value="p.id">
                  {{ p.nombre_empresa }}{{ p.ciudad ? ' (' + p.ciudad + ')' : '' }}
                </option>
              </select>
              <button type="button" class="btn-add-proveedor" @click="abrirModalNuevoProveedor" title="Crear nuevo proveedor">
                + Nuevo
              </button>
            </div>
          </div>
          <div class="form-group">
            <label>Imagen del Equipo</label>
            <div class="imagen-upload-container">
              <div v-if="isEditing && formData.imagen_ruta && !imagenFile" class="imagen-existente">
                <a :href="`/uploads/${formData.imagen_ruta}`" target="_blank" class="imagen-link">
                  {{ getImagenNombre(formData.imagen_ruta) }}
                </a>
                <button type="button" class="btn-icon-sm" @click="eliminarImagenEquipo" title="Eliminar imagen">✕</button>
              </div>
              <div v-if="imagenFile" class="imagen-nueva">
                <span class="imagen-filename">{{ imagenFile.name }}</span>
                <button type="button" class="btn-icon-sm" @click="imagenFile = null" title="Quitar selección">✕</button>
                <button type="button" class="btn-subir-imagen" @click="subirImagenAhora" :disabled="subiendoImagen">
                  {{ subiendoImagen ? 'Subiendo...' : 'Subir imagen' }}
                </button>
              </div>
              <div class="imagen-upload-controls">
                <input type="file" ref="imagenInput" accept="image/*" @change="handleImagenSelect" style="display:none">
                <button type="button" class="btn-outline" @click="$refs.imagenInput.click()">
                  {{ formData.imagen_ruta && !imagenFile ? 'Cambiar imagen' : 'Seleccionar imagen' }}
                </button>
                <span v-if="!formData.imagen_ruta && !imagenFile && !isEditing" style="font-size: 0.82rem; color: #94a3b8;">Se subirá al guardar el equipo</span>
                <span v-if="!formData.imagen_ruta && !imagenFile && isEditing" style="font-size: 0.82rem; color: #94a3b8;">Sin imagen</span>
              </div>
            </div>
          </div>
          <!-- v0.9.0: Descripción técnica -->
          <div class="form-group">
            <label>Descripción Técnica</label>
            <textarea v-model="formData.descripcion" rows="2" placeholder="¿Qué es? ¿Qué hace? Ej: Microscopio binocular para microbiología"></textarea>
          </div>
          <!-- v0.9.0: Observaciones operativas (NUEVO) -->
          <div class="form-group">
            <label>Observaciones</label>
            <textarea v-model="formData.observaciones" rows="2" placeholder="¿Cómo está? Ej: Funciona correctamente, requiere calibración, le falta cable de alimentación"></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- v0.9.0: Modal Crear Proveedor al vuelo -->
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

    <!-- Modal Historial -->
    <div v-if="showHistoryModal" class="modal-overlay" @click.self="showHistoryModal = false">
      <div class="modal" style="width: 850px;">
        <h3>Historial de Mantenimiento: {{ selectedEquipName }}</h3>
        <div v-if="historyData.length === 0" class="empty-state">
          Este equipo no tiene registros de mantenimiento aún.
        </div>
        <div v-else class="history-timeline">
          <div v-for="evento in historyData" :key="evento.id" class="history-event">
            <div class="history-event-header">
              <span class="history-type-badge" :class="'badge-' + evento.tipo_evento">
                {{ evento.tipo_evento?.toUpperCase() }}
              </span>
              <span class="history-date">{{ new Date(evento.fecha_evento).toLocaleDateString('es-BO', { year: 'numeric', month: 'short', day: 'numeric' }) }}</span>
            </div>
            <div class="history-event-body">
              <p class="history-desc">{{ evento.descripcion }}</p>
              <div class="history-details">
                <span v-if="evento.tecnico_nombre" class="history-detail-item">
                  <strong>Técnico:</strong> {{ evento.tecnico_nombre }}
                </span>
                <span v-if="evento.acciones_realizadas" class="history-detail-item">
                  <strong>Acciones:</strong> {{ evento.acciones_realizadas }}
                </span>
                <span v-if="evento.tiempo_invertido" class="history-detail-item">
                  <strong>Tiempo:</strong> {{ evento.tiempo_invertido }} h
                </span>
                <span v-if="evento.costo" class="history-detail-item">
                  <strong>Costo:</strong> Bs {{ evento.costo.toFixed(2) }}
                </span>
                <span v-if="evento.repuestos_utilizados" class="history-detail-item">
                  <strong>Repuestos:</strong> {{ evento.repuestos_utilizados }}
                </span>
                <span v-if="evento.ot_titulo" class="history-detail-item">
                  <strong>OT:</strong> {{ evento.ot_titulo }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div class="modal-actions">
          <button class="btn-secondary" @click="showHistoryModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- Modal Ver Detalles -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal" style="width: 700px;">
        <h3>Detalles del Equipo: {{ selectedEquipo.nombre_corto || selectedEquipo.modelo }}</h3>
        <div class="detail-grid">
          <div class="detail-column">
            <h4>Identificación</h4>
            <p><strong>ID:</strong> {{ selectedEquipo.id }}</p>
            <p><strong>Marca:</strong> {{ selectedEquipo.marca }}</p>
            <p><strong>Modelo:</strong> {{ selectedEquipo.modelo }}</p>
            <p><strong>Nº Serie:</strong> {{ selectedEquipo.numero_serie }}</p>
            <p v-if="selectedEquipo.numero_material"><strong>Nº Material:</strong> {{ selectedEquipo.numero_material }}</p>
            <p><strong>Ubicación:</strong> {{ selectedEquipo.ubicacion_actual || 'N/A' }}</p>
            <p v-if="selectedEquipo.condicion_origen"><strong>Condición:</strong> {{ selectedEquipo.condicion_origen }}</p>
          </div>
          <div class="detail-column">
            <h4>Administrativo</h4>
            <p><strong>Estado:</strong>
              <span class="badge" :style="{ backgroundColor: getEstadoColor(selectedEquipo.estado_id) }">
                {{ getNombreEstado(selectedEquipo.estado_id) }}
              </span>
              <span v-if="getGarantiaBadge(selectedEquipo).text" :class="getGarantiaBadge(selectedEquipo).class">
                {{ getGarantiaBadge(selectedEquipo).text }}
              </span>
            </p>
            <p v-if="selectedEquipo.fecha_adquisicion"><strong>Adquisición:</strong> {{ selectedEquipo.fecha_adquisicion }}</p>
            <p v-if="selectedEquipo.fecha_inicio_garantia"><strong>Inicio Garantía:</strong> {{ selectedEquipo.fecha_inicio_garantia }}</p>
            <p v-if="selectedEquipo.fecha_fin_garantia"><strong>Fin Garantía:</strong> {{ selectedEquipo.fecha_fin_garantia }}</p>
            <p><strong>Proveedor:</strong> {{ getProveedorName(selectedEquipo.proveedor_principal_id) }}</p>
          </div>
        </div>
        <div class="detail-full">
          <h4>Notas</h4>
          <p v-if="selectedEquipo.imagen_ruta"><strong>Imagen:</strong> <a :href="`/uploads/${selectedEquipo.imagen_ruta}`" target="_blank" class="imagen-link">{{ getImagenNombre(selectedEquipo.imagen_ruta) }}</a></p>
          <p v-if="selectedEquipo.descripcion"><strong>Descripción técnica:</strong></p>
          <div v-if="selectedEquipo.descripcion" class="description-box">
            {{ selectedEquipo.descripcion }}
          </div>
          <p v-if="selectedEquipo.observaciones" style="margin-top: 0.5rem;"><strong>Observaciones:</strong></p>
          <div v-if="selectedEquipo.observaciones" class="description-box" style="background: #fefce8; border-color: #fde047;">
            {{ selectedEquipo.observaciones }}
          </div>
        </div>

        <!-- v0.9.2: Contratos asociados al equipo (RF12) -->
        <div class="detail-full">
          <h4>📋 Contratos Asociados</h4>
          <div v-if="contratosEquipo.length > 0" class="contratos-list">
            <div v-for="c in contratosEquipo" :key="c.id" class="contrato-card">
              <div class="contrato-card-header">
                <span class="contrato-tipo">{{ c.tipo_contrato }}</span>
                <span :class="c.activo ? 'contrato-badge-vigente' : (c.dias_restantes < 0 ? 'contrato-badge-vencido' : 'contrato-badge-pendiente')">
                  {{ c.activo ? 'Vigente' : (c.dias_restantes < 0 ? 'Vencido' : 'No iniciado') }}
                </span>
              </div>
              <div class="contrato-card-body">
                <p><strong>Proveedor:</strong> {{ c.proveedor_nombre }}</p>
                <p><strong>Vigencia:</strong> {{ c.fecha_inicio?.substring(0, 10) }} - {{ c.fecha_fin?.substring(0, 10) }}</p>
                <p v-if="c.costo_total"><strong>Costo:</strong> {{ c.moneda }} {{ Number(c.costo_total).toFixed(2) }}</p>
                <p v-if="c.tiempo_respuesta"><strong>Respuesta:</strong> {{ c.tiempo_respuesta }}</p>
              </div>
            </div>
          </div>
          <p v-else style="color: #94a3b8; font-style: italic;">Este equipo no tiene contratos asociados.</p>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- Modal Documentos Adjuntos -->
    <div v-if="showDocsModal" class="modal-overlay" @click.self="showDocsModal = false">
      <div class="modal modal-docs">
        <h3>Documentos - {{ docsEquipo.nombre_corto || docsEquipo.modelo }}</h3>
        <DocumentosAdjuntos v-if="docsEquipo.id" :equipoId="docsEquipo.id" />
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDocsModal = false">Cerrar</button>
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

/* Barra de filtros */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.65rem;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.filter-group {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.filter-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #64748b;
  white-space: nowrap;
}
.filter-label--extra {
  color: #ca8a04;
}
.filter-select {
  padding: 0.35rem 0.6rem;
  border: 1px solid #cbd5e1;
  border-radius: 6px;
  font-size: 0.82rem;
  background: #fff;
  color: #334155;
  min-width: 120px;
  max-width: 180px;
}
.filter-select:focus {
  outline: none;
  border-color: #3498db;
}
.btn-clear-filters {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  padding: 0.35rem 0.7rem;
  border: 1px solid #fecaca;
  border-radius: 6px;
  background: #fef2f2;
  color: #dc2626;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-clear-filters:hover {
  background: #fee2e2;
}
.filter-count {
  font-size: 0.78rem;
  font-weight: 600;
  color: #64748b;
  background: #f1f5f9;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }



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

.badge-garantia {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
  background: #2563eb;
  margin-left: 6px;
  vertical-align: middle;
}

/* v0.9.0: Nuevos badges de garantía */
.badge-garantia-vencida {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #fff;
  background: #dc2626;
  margin-left: 6px;
  vertical-align: middle;
}
.badge-garantia-proxima {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 700;
  color: #1e293b;
  background: #fbbf24;
  margin-left: 6px;
  vertical-align: middle;
}
.badge-condicion {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.7rem;
  font-weight: 600;
  color: #1e3a8a;
  background: #dbeafe;
}

/* v0.9.0: Campos no editables (deshabilitados en edición) */
.warning-no-editable {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-left: 4px solid #dc2626;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  font-size: 0.82rem;
  color: #991b1b;
  line-height: 1.5;
}
.warning-no-editable strong { color: #dc2626; }

.input-locked {
  background: #f1f5f9 !important;
  color: #64748b !important;
  cursor: not-allowed;
  border-color: #cbd5e1 !important;
}

/* v0.9.0: Proveedor dropdown con botón "Crear nuevo" */
.proveedor-row { display: flex; gap: 0.5rem; align-items: flex-end; }
.proveedor-select { flex: 1; }
.btn-add-proveedor {
  background: #16a34a; color: white; border: none;
  padding: 0.5rem 0.85rem; border-radius: 6px; cursor: pointer;
  font-weight: 600; font-size: 0.82rem; white-space: nowrap;
  transition: background 0.2s;
}
.btn-add-proveedor:hover { background: #15803d; }

/* v0.9.2: Contratos en modal de detalle del equipo */
.contratos-list { display: flex; flex-direction: column; gap: 0.5rem; margin-top: 0.5rem; }
.contrato-card { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.contrato-card-header { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.75rem; background: #f8fafc; }
.contrato-tipo { font-weight: 600; font-size: 0.85rem; color: #1e293b; }
.contrato-badge-vigente { padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #16a34a; }
.contrato-badge-vencido { padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #dc2626; }
.contrato-badge-pendiente { padding: 2px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; color: #fff; background: #64748b; }
.contrato-card-body { padding: 0.5rem 0.75rem; }
.contrato-card-body p { margin: 0.2rem 0; font-size: 0.82rem; color: #475569; }

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
.btn-icon-sm:hover { background: #fecaca; }

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
.btn-doc-icon:hover { background: #e8f4fd; color: #2563eb; }

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; max-width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.modal-docs { width: 650px; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; background-color: white; }
.form-group textarea { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; resize: vertical; font-family: inherit; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

/* Historial */
.history-timeline { max-height: 450px; overflow-y: auto; margin-top: 0.5rem; }
.history-event { border-left: 3px solid #e2e8f0; padding: 0.75rem 1rem; margin-bottom: 0.75rem; border-radius: 0 6px 6px 0; background: #f8fafc; transition: background 0.2s; }
.history-event:hover { background: #f1f5f9; }
.history-event-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.4rem; }
.history-type-badge { padding: 2px 10px; border-radius: 10px; font-size: 0.7rem; font-weight: 700; color: white; letter-spacing: 0.03em; }
.badge-preventivo { background: #27ae60; }
.badge-correctivo { background: #e74c3c; }
.badge-calibracion { background: #3498db; }
.badge-otro { background: #9b59b6; }
.history-date { font-size: 0.82rem; color: #64748b; margin-left: auto; }
.history-desc { margin: 0 0 0.35rem 0; font-size: 0.92rem; font-weight: 600; color: #1e293b; }
.history-details { display: flex; flex-wrap: wrap; gap: 0.2rem 1.2rem; font-size: 0.82rem; color: #475569; }
.history-detail-item { display: inline-flex; gap: 0.25rem; }
.empty-state { text-align: center; color: #888; padding: 2rem; }

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
