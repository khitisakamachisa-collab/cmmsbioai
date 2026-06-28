<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'

// --- Variables generales ---
const proveedores = ref([])
const equipos = ref([])  // v0.9.11: lista de equipos para selector chips/tags
const loading = ref(true)
const errorMsg = ref('')

const PAGE_SIZE = 10
const currentPage = ref(1)

// --- Filtros de busqueda ---
const searchQuery = ref('')
const filterCiudad = ref('')   // usa el campo 'ciudad' del modelo (fallback a direccion)
const filterWeb = ref('')      // tiene web / no tiene web

// --- Modal Crear/Editar Proveedor ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})
const saving = ref(false)

// v0.9.11: Equipos asociados al proveedor (chips/tags)
const equiposAsignadosIds = ref([])   // ids de equipos cuyo proveedor_principal es este
const equiposSearchQuery = ref('')
const savingEquipos = ref(false)

// --- Modal Detalle (con contactos) ---
const showDetailModal = ref(false)
const selectedProveedor = ref(null)

// --- Modal Contacto (crear/editar) ---
const showContactoModal = ref(false)
const contactoEditing = ref(false)
const contactoFormData = ref({})
const contactoPadreId = ref(null)

// --- Importación Excel ---
const showImportModal = ref(false)
const importFile = ref(null)
const importing = ref(false)
const importResult = ref(null)
const importDragOver = ref(false)

// v0.9.6: Modal gestión de contactos (separado del detalle de solo lectura)
const showContactosModal = ref(false)
const proveedorContactos = ref(null)  // proveedor actualmente seleccionado para gestionar contactos

// --- Helpers ---
// Devuelve la ciudad: usa el campo 'ciudad' si existe; si no, intenta derivarla de 'direccion'
const getCiudad = (prov) => {
  if (!prov) return ''
  if (prov.ciudad && String(prov.ciudad).trim()) return String(prov.ciudad).trim()
  if (!prov.direccion) return ''
  const parts = String(prov.direccion).split(',')
  return parts[parts.length - 1].trim()
}

const ciudadesUnicas = computed(() => {
  const vals = new Set()
  proveedores.value.forEach(p => {
    const c = getCiudad(p)
    if (c) vals.add(c)
  })
  return Array.from(vals).sort()
})

const tieneFiltrosActivos = computed(() => {
  return searchQuery.value.trim() || filterCiudad.value || filterWeb.value
})

const limpiarFiltros = () => {
  searchQuery.value = ''
  filterCiudad.value = ''
  filterWeb.value = ''
}

const filteredProveedores = computed(() => {
  let result = proveedores.value

  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    result = result.filter(p => {
      const nombre = String(p.nombre_empresa ?? '').toLowerCase()
      const email = String(p.email_principal ?? '').toLowerCase()
      const tel = String(p.telefono_principal ?? '').toLowerCase()
      const ciu = String(p.ciudad ?? '').toLowerCase()
      return nombre.includes(q) || email.includes(q) || tel.includes(q) || ciu.includes(q)
    })
  }

  if (filterCiudad.value) {
    result = result.filter(p => getCiudad(p) === filterCiudad.value)
  }

  if (filterWeb.value === 'con') {
    result = result.filter(p => p.pagina_web)
  } else if (filterWeb.value === 'sin') {
    result = result.filter(p => !p.pagina_web)
  }

  return result
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredProveedores.value.length / PAGE_SIZE))
)

watch([searchQuery, filterCiudad, filterWeb], () => {
  currentPage.value = 1
})

watch(() => filteredProveedores.value.length, (len) => {
  const tp = Math.max(1, Math.ceil(len / PAGE_SIZE))
  if (currentPage.value > tp) currentPage.value = tp
})

const irPaginaAnterior = () => { if (currentPage.value > 1) currentPage.value -= 1 }
const irPaginaSiguiente = () => { if (currentPage.value < totalPages.value) currentPage.value += 1 }

// --- Fetch ---
const fetchProveedores = async () => {
  try {
    loading.value = true
    const res = await apiClient.get('/proveedores/con-contactos')
    proveedores.value = res.data
  } catch (e) {
    errorMsg.value = 'Error al cargar proveedores'
    console.error(e)
  } finally {
    loading.value = false
  }
}

// --- CRUD Proveedores ---
const openCreateModal = () => {
  isEditing.value = false
  formData.value = {
    nombre_empresa: '',
    ciudad: '',
    direccion: '',
    telefono_principal: '',
    email_principal: '',
    pagina_web: '',
    notas_generales: ''
  }
  // v0.9.11: reset equipos asociados para nuevo proveedor
  equiposAsignadosIds.value = []
  equiposSearchQuery.value = ''
  showModal.value = true
}

const openEditModal = async (prov) => {
  isEditing.value = true
  formData.value = { ...prov }
  // v0.9.11: cargar equipos asociados al proveedor
  equiposAsignadosIds.value = []
  equiposSearchQuery.value = ''
  showModal.value = true
  try {
    const res = await apiClient.get(`/proveedores/${prov.id}/equipos`)
    if (Array.isArray(res.data)) {
      equiposAsignadosIds.value = res.data.map(e => e.id)
    }
  } catch (e) {
    console.error('Error cargando equipos del proveedor:', e)
  }
}

const saveProveedor = async () => {
  saving.value = true
  try {
    const payload = { ...formData.value }
    let proveedorId
    if (isEditing.value) {
      const res = await apiClient.put(`/proveedores/${payload.id}`, payload)
      proveedorId = payload.id
      // v0.9.11: sincronizar equipos asociados
      await apiClient.put(`/proveedores/${proveedorId}/equipos`, { equipos_ids: equiposAsignadosIds.value })
    } else {
      const res = await apiClient.post('/proveedores/', payload)
      proveedorId = res.data.id
      // v0.9.11: si se asociaron equipos en el alta, sincronizar
      if (equiposAsignadosIds.value.length > 0) {
        await apiClient.put(`/proveedores/${proveedorId}/equipos`, { equipos_ids: equiposAsignadosIds.value })
      }
    }
    alert(isEditing.value ? 'Proveedor actualizado' : 'Proveedor creado')
    showModal.value = false
    fetchProveedores()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Error al guardar'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
    console.error(e)
  } finally {
    saving.value = false
  }
}

const deleteProveedor = async (id) => {
  if (!confirm('Eliminar este proveedor y TODOS sus contactos asociados?')) return
  try {
    await apiClient.delete(`/proveedores/${id}`)
    alert('Proveedor eliminado')
    if (selectedProveedor.value && selectedProveedor.value.id === id) {
      showDetailModal.value = false
    }
    fetchProveedores()
  } catch (e) {
    alert('Error al eliminar')
    console.error(e)
  }
}

// --- Detalle (ver contactos) ---
const openDetailModal = (prov) => {
  selectedProveedor.value = prov
  showDetailModal.value = true
}

// --- CRUD Contactos ---
const openCreateContacto = (proveedorId) => {
  contactoEditing.value = false
  contactoPadreId.value = proveedorId
  contactoFormData.value = {
    nombre_contacto: '',
    cargo: '',
    telefono_contacto: '',
    email_contacto: '',
    notas_contacto: ''
  }
  // v0.9.7: cerrar el modal padre (gestión de contactos o detalle) para que el de contacto quede al frente
  showContactosModal.value = false
  showDetailModal.value = false
  showContactoModal.value = true
}

const openEditContacto = (contacto) => {
  contactoEditing.value = true
  contactoPadreId.value = contacto.proveedor_id
  contactoFormData.value = { ...contacto }
  // v0.9.7: cerrar el modal padre (gestión de contactos o detalle) para que el de contacto quede al frente
  showContactosModal.value = false
  showDetailModal.value = false
  showContactoModal.value = true
}

const saveContacto = async () => {
  try {
    const payload = { ...contactoFormData.value }
    if (contactoEditing.value) {
      await apiClient.put(`/proveedores/contactos/${payload.id}`, payload)
      alert('Contacto actualizado')
    } else {
      await apiClient.post(`/proveedores/${contactoPadreId.value}/contactos`, payload)
      alert('Contacto agregado')
    }
    showContactoModal.value = false
    // v0.9.7: refresca y REABRE el modal de gestión de contactos para que el usuario vuelva a la lista
    await refrescarProveedorContactos()
    if (proveedorContactos.value) {
      showContactosModal.value = true
    }
  } catch (e) {
    alert('Error al guardar contacto')
    console.error(e)
  }
}

const deleteContacto = async (contactoId) => {
  if (!confirm('Eliminar este contacto?')) return
  try {
    await apiClient.delete(`/proveedores/contactos/${contactoId}`)
    alert('Contacto eliminado')
    await refrescarProveedorContactos()
  } catch (e) {
    alert('Error al eliminar contacto')
    console.error(e)
  }
}

// --- Importación Excel (lógica replicada de EquiposView) ---
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

const descargarPlantillaExcel = () => {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_proveedores.xlsx`
  link.download = 'CMMS-BioAI_Plantilla_Proveedores.xlsx'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const descargarPlantillaCSV = () => {
  const link = document.createElement('a')
  link.href = `${import.meta.env.BASE_URL}plantillas/plantilla_proveedores.csv`
  link.download = 'CMMS-BioAI_Plantilla_Proveedores.csv'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

const submitImport = async () => {
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
    const res = await apiClient.post('/proveedores/import-excel', fd, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    importResult.value = res.data
    await fetchProveedores()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Error al importar'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
    console.error(e)
  } finally {
    importing.value = false
  }
}

const resetImport = () => {
  importFile.value = null
  importResult.value = null
}

// v0.9.6: Abrir modal de gestión de contactos (CRUD completo)
const openContactosModal = (prov) => {
  proveedorContactos.value = prov
  showContactosModal.value = true
}

// Refrescar el proveedor actual tras CRUD de contactos
const refrescarProveedorContactos = async () => {
  await fetchProveedores()
  if (proveedorContactos.value) {
    const updated = proveedores.value.find(p => p.id === proveedorContactos.value.id)
    if (updated) proveedorContactos.value = updated
  }
  if (selectedProveedor.value) {
    const updatedSel = proveedores.value.find(p => p.id === selectedProveedor.value.id)
    if (updatedSel) selectedProveedor.value = updatedSel
  }
}

// v0.9.11: Cargar lista de equipos para el selector chips/tags
const fetchEquipos = async () => {
  try {
    const res = await apiClient.get('/equipos/')
    const data = res.data
    equipos.value = Array.isArray(data) ? data : (data.items || [])
  } catch (e) {
    console.error('Error cargando equipos:', e)
  }
}

// v0.9.11: Equipos seleccionados como objetos (para mostrar chips)
const equiposSeleccionados = computed(() => {
  return equiposAsignadosIds.value
    .map(id => equipos.value.find(e => e.id === id))
    .filter(Boolean)
})

// Resultados de búsqueda excluyendo ya seleccionados
const equiposFiltrados = computed(() => {
  const q = equiposSearchQuery.value.trim().toLowerCase()
  let base = equipos.value.filter(eq => !equiposAsignadosIds.value.includes(eq.id))
  if (q) {
    base = base.filter(eq => {
      const nombre = String(eq.nombre_corto ?? '').toLowerCase()
      const modelo = String(eq.modelo ?? '').toLowerCase()
      const serie = String(eq.numero_serie ?? '').toLowerCase()
      const marca = String(eq.marca ?? '').toLowerCase()
      return nombre.includes(q) || modelo.includes(q) || serie.includes(q) || marca.includes(q)
    })
  }
  return base
})

function agregarEquipo(eq) {
  if (!equiposAsignadosIds.value.includes(eq.id)) {
    equiposAsignadosIds.value.push(eq.id)
  }
  equiposSearchQuery.value = ''
}

function quitarEquipo(id) {
  equiposAsignadosIds.value = equiposAsignadosIds.value.filter(i => i !== id)
}

function limpiarSeleccionEquipos() {
  equiposAsignadosIds.value = []
}

onMounted(() => {
  fetchProveedores()
  fetchEquipos()
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="top-bar">
        <h2>Gestion de Proveedores y Contactos</h2>
        <div class="top-bar-actions">
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input v-model="searchQuery" type="search" class="search-input"
              placeholder="Empresa, email, telefono o ciudad..." autocomplete="off" />
          </div>
          <button class="btn-import" @click="openImportModal" title="Cargar proveedores desde Excel">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M.5 9.9a.5.5 0 0 1 .5.5v2.5a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1v-2.5a.5.5 0 0 1 1 0v2.5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2v-2.5a.5.5 0 0 1 .5-.5z"/>
              <path d="M7.646 1.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1-.708.708L8.5 2.707V11.5a.5.5 0 0 1-1 0V2.707L5.354 4.854a.5.5 0 1 1-.708-.708l3-3z"/>
            </svg>
            Cargar Excel
          </button>
          <button class="btn-primary" @click="openCreateModal">+ Nuevo Proveedor</button>
        </div>
      </div>

      <!-- Barra de filtros -->
      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Ciudad:</label>
          <select v-model="filterCiudad" class="filter-select">
            <option value="">Todas</option>
            <option v-for="c in ciudadesUnicas" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Pagina Web:</label>
          <select v-model="filterWeb" class="filter-select">
            <option value="">Todos</option>
            <option value="con">Con web</option>
            <option value="sin">Sin web</option>
          </select>
        </div>
        <button v-if="tieneFiltrosActivos" class="btn-clear-filters" @click="limpiarFiltros">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
            <path d="M4.646 4.646a.5.5 0 0 1 .708 0L8 7.293l2.646-2.647a.5.5 0 0 1 .708.708L8.707 8l2.647 2.646a.5.5 0 0 1-.708.708L8 8.707l-2.646 2.647a.5.5 0 0 1-.708-.708L7.293 8 4.646 5.354a.5.5 0 0 1 0-.708z"/>
          </svg>
          Limpiar
        </button>
        <span v-if="tieneFiltrosActivos" class="filter-count">{{ filteredProveedores.length }} de {{ proveedores.length }}</span>
      </div>

      <div v-if="loading">Cargando proveedores...</div>
      <div v-if="errorMsg" class="error">{{ errorMsg }}</div>

      <table v-if="!loading && proveedores.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Empresa</th>
            <th>Ciudad</th>
            <th>Telefono</th>
            <th>Email</th>
            <th>Web</th>
            <th>Contactos</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredProveedores.length">
            <td class="table-empty-cell" colspan="8">
              {{ tieneFiltrosActivos ? 'No hay proveedores que coincidan.' : 'No hay proveedores registrados.' }}
            </td>
          </tr>
          <tr v-for="prov in filteredProveedores.slice((currentPage - 1) * PAGE_SIZE, currentPage * PAGE_SIZE)"
              :key="prov.id">
            <td>#{{ prov.id }}</td>
            <td>
              <strong>{{ prov.nombre_empresa }}</strong>
              <div v-if="prov.direccion" class="sub-text">{{ prov.direccion }}</div>
            </td>
            <td>{{ getCiudad(prov) || '—' }}</td>
            <td>{{ prov.telefono_principal || '—' }}</td>
            <td>
              <a v-if="prov.email_principal" :href="'mailto:' + prov.email_principal" class="link-mail">
                {{ prov.email_principal }}
              </a>
              <span v-else>—</span>
            </td>
            <td>
              <a v-if="prov.pagina_web" :href="prov.pagina_web" target="_blank" rel="noopener" class="link-web">
                Visitar
              </a>
              <span v-else>—</span>
            </td>
            <td>
              <span class="badge-contactos" :class="{ 'badge-contactos--zero': !prov.contactos?.length }">
                {{ prov.contactos?.length || 0 }}
              </span>
            </td>
            <td class="actions-cell">
              <button class="btn-icon btn-view" title="Ver Detalle" @click="openDetailModal(prov)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                </svg>
              </button>
              <button class="btn-icon btn-edit" title="Editar Empresa" @click="openEditModal(prov)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5z"/>
                </svg>
              </button>
              <button class="btn-icon btn-contactos" title="Gestionar Contactos" @click="openContactosModal(prov)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6zm2-3a2 2 0 1 1-4 0 2 2 0 0 1 4 0z"/>
                  <path d="M8 9a5 5 0 0 0-5 5v1h10v-1a5 5 0 0 0-5-5zM4 13a4 4 0 0 1 8 0H4z"/>
                </svg>
              </button>
              <button class="btn-icon btn-delete" title="Eliminar" @click="deleteProveedor(prov.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                  <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && !proveedores.length" class="empty-state">
        No hay proveedores registrados. Haga clic en "Nuevo Proveedor" o "Importar" para comenzar.
      </div>

      <div v-if="!loading && filteredProveedores.length"
           class="table-pagination" role="navigation">
        <button type="button" class="btn-pagination" :disabled="currentPage <= 1" @click="irPaginaAnterior">
          Anterior
        </button>
        <span class="table-pagination-meta">
          Pagina {{ currentPage }} de {{ totalPages }}
          <span class="table-pagination-range">
            ({{ (currentPage - 1) * PAGE_SIZE + 1 }}–{{ Math.min(currentPage * PAGE_SIZE, filteredProveedores.length) }} de {{ filteredProveedores.length }})
          </span>
        </span>
        <button type="button" class="btn-pagination" :disabled="currentPage >= totalPages" @click="irPaginaSiguiente">
          Siguiente
        </button>
      </div>
    </main>

    <!-- ==================== Modal Crear/Editar Proveedor ==================== -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Proveedor' : 'Nuevo Proveedor' }}</h3>
        <form @submit.prevent="saveProveedor">
          <div class="form-group">
            <label>Nombre de Empresa *</label>
            <input v-model="formData.nombre_empresa" type="text" required placeholder="TechMed Bolivia SRL">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Ciudad</label>
              <input v-model="formData.ciudad" type="text" placeholder="Cochabamba, La Paz, Santa Cruz...">
            </div>
            <div class="form-group">
              <label>Telefono Principal</label>
              <input v-model="formData.telefono_principal" type="text" placeholder="+591 4 4223344">
            </div>
          </div>
          <div class="form-group">
            <label>Direccion</label>
            <input v-model="formData.direccion" type="text" placeholder="Av. Blanco Galindo km 7.5">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Email Principal</label>
              <input v-model="formData.email_principal" type="email" placeholder="ventas@empresa.bo">
            </div>
            <div class="form-group">
              <label>Pagina Web</label>
              <input v-model="formData.pagina_web" type="text" placeholder="https://empresa.bo">
            </div>
          </div>
          <div class="form-group">
            <label>Notas Generales</label>
            <textarea v-model="formData.notas_generales" rows="3"
              placeholder="Distribuidor autorizado, garantias, condiciones comerciales..."></textarea>
          </div>

          <!-- v0.9.11: Equipos Asociados al proveedor (chips/tags) -->
          <div class="form-group">
            <label>
              Equipos Asociados
              <span class="equipos-counter">({{ equiposAsignadosIds.length }} seleccionado{{ equiposAsignadosIds.length === 1 ? '' : 's' }})</span>
              <button v-if="equiposAsignadosIds.length > 0" type="button" class="btn-limpiar-seleccion" @click="limpiarSeleccionEquipos">Limpiar selección</button>
            </label>
            <div class="equipos-selector">
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

              <div v-if="equiposSearchQuery" class="equipos-resultados">
                <p v-if="!equipos.length" class="text-muted equipos-empty">No hay equipos registrados.</p>
                <p v-else-if="!equiposFiltrados.length" class="text-muted equipos-empty">No se encontraron equipos con "{{ equiposSearchQuery }}" o ya están todos seleccionados.</p>
                <div v-else class="equipos-resultados-list">
                  <div v-for="eq in equiposFiltrados" :key="eq.id" class="equipo-item" @click="agregarEquipo(eq)">
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

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false" :disabled="saving">Cancelar</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Guardando...' : 'Guardar' }}
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- ==================== Modal Detalle (con contactos) ==================== -->
    <div v-if="showDetailModal && selectedProveedor" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal" style="width: 780px;">
        <h3>{{ selectedProveedor.nombre_empresa }}</h3>

        <div class="detail-grid">
          <div class="detail-column">
            <h4>Datos de la Empresa</h4>
            <p><strong>ID:</strong> #{{ selectedProveedor.id }}</p>
            <p v-if="selectedProveedor.ciudad"><strong>Ciudad:</strong> {{ selectedProveedor.ciudad }}</p>
            <p v-if="selectedProveedor.direccion"><strong>Direccion:</strong> {{ selectedProveedor.direccion }}</p>
            <p v-if="selectedProveedor.telefono_principal"><strong>Telefono:</strong> {{ selectedProveedor.telefono_principal }}</p>
            <p v-if="selectedProveedor.email_principal">
              <strong>Email:</strong>
              <a :href="'mailto:' + selectedProveedor.email_principal" class="link-mail"> {{ selectedProveedor.email_principal }}</a>
            </p>
            <p v-if="selectedProveedor.pagina_web">
              <strong>Web:</strong>
              <a :href="selectedProveedor.pagina_web" target="_blank" rel="noopener" class="link-web"> {{ selectedProveedor.pagina_web }}</a>
            </p>
          </div>
          <div class="detail-column">
            <h4>Notas</h4>
            <div class="description-box">
              {{ selectedProveedor.notas_generales || 'Sin notas adicionales.' }}
            </div>
          </div>
        </div>

        <hr class="detail-separator">

        <div class="contactos-section">
          <div class="contactos-header">
            <h4>Contactos Asociados ({{ selectedProveedor.contactos?.length || 0 }})</h4>
            <!-- v0.9.6: modal de detalle es SOLO LECTURA — sin botón "Agregar Contacto" -->
          </div>

          <div v-if="!selectedProveedor.contactos || !selectedProveedor.contactos.length" class="empty-contactos">
            Este proveedor no tiene contactos asociados.
          </div>

          <div v-else class="contactos-list">
            <div v-for="c in selectedProveedor.contactos" :key="c.id" class="contacto-card">
              <div class="contacto-info">
                <div class="contacto-nombre">
                  <strong>{{ c.nombre_contacto }}</strong>
                  <span v-if="c.cargo" class="contacto-cargo">{{ c.cargo }}</span>
                </div>
                <div class="contacto-datos">
                  <span v-if="c.telefono_contacto">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.567 17.567 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328zM1.884.511a1.745 1.745 0 0 1 2.612.63L6.29 2.986a1.745 1.745 0 0 1 .162 1.794l-.548 2.19a.37.37 0 0 0 .094.37l1.387 1.387a.37.37 0 0 0 .37.094l2.19-.548a1.745 1.745 0 0 1 1.794.162l1.845 1.794a1.745 1.745 0 0 1-.43 2.838l-1.034.78a3.5 3.5 0 0 1-2.93.519 18.555 18.555 0 0 1-7.04-4.46A18.555 18.555 0 0 1 .965 6.5a3.5 3.5 0 0 1 .519-2.93l.78-1.034z"/>
                    </svg>
                    {{ c.telefono_contacto }}
                  </span>
                  <span v-if="c.email_contacto">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M.05 3.555A2 2 0 0 1 2 2h12a2 2 0 0 1 1.95 1.555L8 8.414.05 3.555ZM0 4.697v7.104l5.803-3.558L0 4.697ZM6.761 8.83l-6.57 4.027A2 2 0 0 0 2 14h12a2 2 0 0 0 1.808-1.144l-6.57-4.027L8 9.586l-1.239-.757Zm3.436-.586L16 11.801V4.697l-5.803 3.546Z"/>
                    </svg>
                    <a :href="'mailto:' + c.email_contacto" class="link-mail">{{ c.email_contacto }}</a>
                  </span>
                </div>
                <div v-if="c.notas_contacto" class="contacto-notas">{{ c.notas_contacto }}</div>
              </div>
              <!-- v0.9.6: detalle es SOLO LECTURA, sin acciones de editar/eliminar contactos -->
            </div>
          </div>
        </div>

        <!-- v0.9.6: el modal de detalle solo permite cerrar (el ojo = solo visualizar) -->
        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ==================== Modal Crear/Editar Contacto ==================== -->
    <div v-if="showContactoModal" class="modal-overlay" @click.self="showContactoModal = false">
      <div class="modal" style="width: 520px;">
        <h3>{{ contactoEditing ? 'Editar Contacto' : 'Nuevo Contacto' }}</h3>
        <form @submit.prevent="saveContacto">
          <div class="form-group">
            <label>Nombre del Contacto *</label>
            <input v-model="contactoFormData.nombre_contacto" type="text" required placeholder="Carlos Perez">
          </div>
          <div class="form-group">
            <label>Cargo</label>
            <input v-model="contactoFormData.cargo" type="text" placeholder="Gerente de Ventas, Jefe de Soporte...">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Telefono</label>
              <input v-model="contactoFormData.telefono_contacto" type="text" placeholder="+591 70123456">
            </div>
            <div class="form-group">
              <label>Email</label>
              <input v-model="contactoFormData.email_contacto" type="email" placeholder="carlos@empresa.bo">
            </div>
          </div>
          <div class="form-group">
            <label>Notas del Contacto</label>
            <textarea v-model="contactoFormData.notas_contacto" rows="2"
              placeholder="Horario de atencion, preferencias de contacto..."></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showContactoModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ==================== Modal Gestionar Contactos (v0.9.6) ==================== -->
    <div v-if="showContactosModal && proveedorContactos" class="modal-overlay" @click.self="showContactosModal = false">
      <div class="modal" style="width: 780px;">
        <h3>Contactos — {{ proveedorContactos.nombre_empresa }}</h3>

        <div class="contactos-section">
          <div class="contactos-header">
            <h4>Contactos Asociados ({{ proveedorContactos.contactos?.length || 0 }})</h4>
            <button class="btn-sm btn-add-contacto" @click="openCreateContacto(proveedorContactos.id)">
              + Agregar Contacto
            </button>
          </div>

          <div v-if="!proveedorContactos.contactos || !proveedorContactos.contactos.length" class="empty-contactos">
            Este proveedor no tiene contactos asociados. Haga clic en "+ Agregar Contacto" para crear el primero.
          </div>

          <div v-else class="contactos-list">
            <div v-for="c in proveedorContactos.contactos" :key="c.id" class="contacto-card">
              <div class="contacto-info">
                <div class="contacto-nombre">
                  <strong>{{ c.nombre_contacto }}</strong>
                  <span v-if="c.cargo" class="contacto-cargo">{{ c.cargo }}</span>
                </div>
                <div class="contacto-datos">
                  <span v-if="c.telefono_contacto">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M3.654 1.328a.678.678 0 0 0-1.015-.063L1.605 2.3c-.483.484-.661 1.169-.45 1.77a17.568 17.568 0 0 0 4.168 6.608 17.567 17.567 0 0 0 6.608 4.168c.601.211 1.286.033 1.77-.45l1.034-1.034a.678.678 0 0 0-.063-1.015l-2.307-1.794a.678.678 0 0 0-.58-.122l-2.19.547a1.745 1.745 0 0 1-1.657-.459L5.482 8.062a1.745 1.745 0 0 1-.46-1.657l.548-2.19a.678.678 0 0 0-.122-.58L3.654 1.328zM1.884.511a1.745 1.745 0 0 1 2.612.63L6.29 2.986a1.745 1.745 0 0 1 .162 1.794l-.548 2.19a.37.37 0 0 0 .094.37l1.387 1.387a.37.37 0 0 0 .37.094l2.19-.548a1.745 1.745 0 0 1 1.794.162l1.845 1.794a1.745 1.745 0 0 1-.43 2.838l-1.034.78a3.5 3.5 0 0 1-2.93.519 18.555 18.555 0 0 1-7.04-4.46A18.555 18.555 0 0 1 .965 6.5a3.5 3.5 0 0 1 .519-2.93l.78-1.034z"/>
                    </svg>
                    {{ c.telefono_contacto }}
                  </span>
                  <span v-if="c.email_contacto">
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" fill="currentColor" viewBox="0 0 16 16">
                      <path d="M.05 3.555A2 2 0 0 1 2 2h12a2 2 0 0 1 1.95 1.555L8 8.414.05 3.555ZM0 4.697v7.104l5.803-3.558L0 4.697ZM6.761 8.83l-6.57 4.027A2 2 0 0 0 2 14h12a2 2 0 0 0 1.808-1.144l-6.57-4.027L8 9.586l-1.239-.757Zm3.436-.586L16 11.801V4.697l-5.803 3.546Z"/>
                    </svg>
                    <a :href="'mailto:' + c.email_contacto" class="link-mail">{{ c.email_contacto }}</a>
                  </span>
                </div>
                <div v-if="c.notas_contacto" class="contacto-notas">{{ c.notas_contacto }}</div>
              </div>
              <div class="contacto-actions">
                <button class="btn-icon-sm btn-edit-sm" title="Editar Contacto" @click="openEditContacto(c)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10z"/>
                  </svg>
                </button>
                <button class="btn-icon-sm btn-delete-sm" title="Eliminar Contacto" @click="deleteContacto(c.id)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                    <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showContactosModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ==================== Modal Importar Excel (estilo Equipos: drop-zone + spinner) ==================== -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="modal" style="width: 580px;">
        <h3>Importar Proveedores desde Excel</h3>

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
            <p><strong>Columna obligatoria:</strong> nombre_empresa</p>
            <p>Si el nombre de la empresa ya existe, el registro se <strong>actualizará</strong> (upsert).</p>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showImportModal = false">Cancelar</button>
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
            <button type="button" class="btn-primary" :disabled="!importFile" @click="submitImport">
              Importar
            </button>
          </div>
        </div>

        <!-- Paso 2: Procesando -->
        <div v-if="importing" class="import-progress">
          <div class="spinner"></div>
          <p style="text-align: center; color: #475569;">Importando proveedores...</p>
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
                  <span class="error-nombre">(Empresa: {{ err.nombre }})</span>
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
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

.top-bar {
  display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;
  gap: 0.75rem 1rem; margin-bottom: 1rem;
}
.top-bar h2 { margin: 0; }
.top-bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }

.search-wrapper {
  position: relative; display: flex; align-items: center;
  min-width: 200px; flex: 1 1 180px; max-width: 360px;
}
.search-icon { position: absolute; left: 10px; color: #94a3b8; pointer-events: none; z-index: 1; }
.search-input {
  width: 100%; padding: 0.55rem 0.85rem 0.55rem 2.2rem;
  border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.9rem; box-sizing: border-box; background: #fff;
}
.search-input::placeholder { color: #94a3b8; }
.search-input:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }

/* Barra de filtros */
.filter-bar {
  display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem;
  margin-bottom: 1rem; padding: 0.75rem 1rem;
  background: white; border-radius: 8px; border: 1px solid #e2e8f0;
}
.filter-group { display: flex; align-items: center; gap: 0.35rem; }
.filter-label { font-size: 0.82rem; font-weight: 600; color: #64748b; white-space: nowrap; }
.filter-select {
  padding: 0.35rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.82rem; background: #fff; color: #334155; min-width: 120px; max-width: 180px;
}
.filter-select:focus { outline: none; border-color: #3498db; }
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

table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; font-size: 0.88rem; }
th { background-color: #f8f9fa; font-weight: bold; }

.sub-text { font-size: 0.75rem; color: #94a3b8; margin-top: 2px; }
.link-mail { color: #2563eb; text-decoration: none; }
.link-mail:hover { text-decoration: underline; }
.link-web { color: #16a34a; text-decoration: none; font-weight: 600; }
.link-web:hover { text-decoration: underline; }

.badge-contactos {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 28px; padding: 4px 8px; border-radius: 12px;
  background: #dbeafe; color: #1e40af; font-weight: 700; font-size: 0.8rem;
}
.badge-contactos--zero { background: #f1f5f9; color: #94a3b8; }

.table-empty-cell { text-align: center; color: #64748b; padding: 1.5rem 12px; font-size: 0.95rem; }
.empty-state { text-align: center; padding: 2.5rem 1rem; color: #64748b; font-size: 0.95rem; }

.table-pagination {
  display: flex; flex-wrap: wrap; align-items: center; justify-content: center;
  gap: 1rem; margin-top: 1rem; padding: 0.75rem 0;
}
.table-pagination-meta { font-size: 0.9rem; color: #475569; text-align: center; }
.table-pagination-range { display: block; font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; }
.btn-pagination {
  background-color: #3498db; color: white; border: none;
  padding: 0.5rem 1.1rem; border-radius: 6px; cursor: pointer;
  font-weight: 600; font-size: 0.9rem; transition: background-color 0.2s ease, opacity 0.2s ease;
}
.btn-pagination:hover:not(:disabled) { background-color: #2980b9; }
.btn-pagination:disabled { opacity: 0.45; cursor: not-allowed; }

.error { color: #dc2626; background: #fef2f2; padding: 0.75rem; border-radius: 6px; margin: 1rem 0; }

/* Modales */
.modal-overlay {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center;
  z-index: 1000; padding: 1rem;
}
.modal {
  background: white; padding: 1.5rem; border-radius: 8px;
  width: 100%; max-width: 550px; max-height: 90vh; overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0,0,0,0.2);
}
.modal h3 { margin: 0 0 1rem 0; color: #1e293b; border-bottom: 2px solid #e2e8f0; padding-bottom: 0.5rem; }
.modal h4 { margin: 0 0 0.5rem 0; color: #475569; font-size: 0.95rem; }

.form-group { margin-bottom: 0.85rem; }
.form-group label { display: block; margin-bottom: 0.3rem; font-weight: 600; color: #334155; font-size: 0.88rem; }
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 0.5rem 0.7rem; border: 1px solid #cbd5e1; border-radius: 6px;
  font-size: 0.9rem; box-sizing: border-box; font-family: inherit;
}
.form-group input:focus, .form-group select:focus, .form-group textarea:focus {
  outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.15);
}
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem; }
@media (max-width: 600px) { .form-row { grid-template-columns: 1fr; } }

.modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #e2e8f0; }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-secondary:hover { background-color: #7f8c8d; }
.btn-edit-detail { background-color: #f59e0b; color: white; border: none; padding: 0.55rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem; }
.btn-edit-detail:hover { background-color: #d97706; }

/* Detalle */
.detail-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.25rem; margin-bottom: 0.5rem; }
@media (max-width: 700px) { .detail-grid { grid-template-columns: 1fr; } }
.detail-column p { margin: 0.35rem 0; font-size: 0.88rem; color: #334155; }
.description-box {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 0.6rem; font-size: 0.85rem; color: #475569; min-height: 60px; line-height: 1.5;
}
.detail-separator { border: none; border-top: 1px solid #e2e8f0; margin: 1rem 0; }

/* Contactos */
.contactos-section { margin-top: 0.5rem; }
.contactos-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; }
.contactos-header h4 { margin: 0; font-size: 1rem; color: #1e293b; }
.btn-sm { padding: 0.35rem 0.75rem; font-size: 0.82rem; border: none; border-radius: 4px; cursor: pointer; font-weight: 600; }
.btn-add-contacto { background: #16a34a; color: white; }
.btn-add-contacto:hover { background: #15803d; }

.empty-contactos {
  text-align: center; padding: 1.25rem; background: #f8fafc;
  border: 1px dashed #cbd5e1; border-radius: 6px;
  color: #64748b; font-size: 0.88rem;
}

.contactos-list { display: flex; flex-direction: column; gap: 0.5rem; }
.contacto-card {
  display: flex; justify-content: space-between; align-items: flex-start;
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.65rem 0.85rem;
  transition: border-color 0.2s;
}
.contacto-card:hover { border-color: #93c5fd; }
.contacto-info { flex: 1; min-width: 0; }
.contacto-nombre { font-size: 0.92rem; margin-bottom: 0.25rem; }
.contacto-cargo {
  display: inline-block; margin-left: 0.5rem;
  background: #eef2ff; color: #6366f1; font-size: 0.72rem; font-weight: 600;
  padding: 0.1rem 0.45rem; border-radius: 3px;
}
.contacto-datos {
  display: flex; flex-wrap: wrap; gap: 0.85rem; font-size: 0.8rem; color: #475569;
}
.contacto-datos span { display: inline-flex; align-items: center; gap: 0.3rem; }
.contacto-datos svg { color: #64748b; }
.contacto-notas {
  margin-top: 0.35rem; font-size: 0.78rem; color: #64748b;
  font-style: italic; padding-left: 0.5rem; border-left: 2px solid #e2e8f0;
}
.contacto-actions { display: flex; gap: 0.3rem; flex-shrink: 0; }

/* Iconos — v0.9.7: grises por defecto, color solo en hover */
.actions-cell { display: flex; gap: 0.5rem; align-items: center; }
.btn-icon {
  background: #f0f2f5; color: #555;
  border: none; padding: 8px; border-radius: 6px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.btn-view:hover { background: #16a34a; color: #ffffff; }
.btn-edit:hover { background: #2563eb; color: #ffffff; }
.btn-contactos:hover { background: #ea580c; color: #ffffff; }
.btn-delete:hover { background: #dc2626; color: #ffffff; }

/* Iconos pequeños (dentro del modal de contactos) — también grises por defecto */
.btn-icon-sm {
  background: #f0f2f5; color: #555;
  border: none; padding: 5px; border-radius: 4px; cursor: pointer;
  display: flex; align-items: center; justify-content: center; transition: all 0.2s;
}
.btn-edit-sm:hover { background: #2563eb; color: #ffffff; }
.btn-delete-sm:hover { background: #dc2626; color: #ffffff; }

/* Botón "Cargar Excel" (mismo estilo que Equipos) */
.btn-import {
  background-color: #27ae60; color: white; border: none; padding: 0.6rem 1.1rem;
  border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 0.9rem;
  display: flex; align-items: center; gap: 0.4rem; transition: background-color 0.2s;
}
.btn-import:hover { background-color: #219a52; }
.btn-import svg { flex-shrink: 0; }

/* Botón outline para plantillas dentro del modal importar */
.btn-outline {
  background-color: transparent; color: #3498db; border: 1.5px solid #3498db;
  padding: 0.45rem 0.9rem; border-radius: 4px; cursor: pointer; font-weight: 600;
  font-size: 0.85rem; transition: all 0.2s; display: flex; align-items: center;
}
.btn-outline:hover { background-color: #ebf5fb; }

/* Drop-zone para arrastrar archivos (mismo estilo que Equipos) */
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

.import-info {
  background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
  padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.85rem; color: #475569;
}
.import-info p { margin: 0.2rem 0; }

.import-progress {
  padding: 2rem; display: flex; flex-direction: column; align-items: center; gap: 1rem;
}
.spinner {
  width: 40px; height: 40px; border: 4px solid #e2e8f0;
  border-top-color: #3498db; border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.import-result { margin-bottom: 1rem; }
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

/* v0.9.11: Selector de Equipos Asociados con chips/tags (igual a Contratos) */
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
.equipos-search-input:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.15); }
.equipos-search-clear {
  position: absolute; right: 6px; top: 50%; transform: translateY(-50%);
  background: transparent; border: none; color: #94a3b8; cursor: pointer;
  font-size: 1.3rem; line-height: 1; padding: 0.2rem 0.4rem; border-radius: 4px;
}
.equipos-search-clear:hover { background: #f1f5f9; color: #475569; }

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
</style>
