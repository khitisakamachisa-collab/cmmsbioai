<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'
import Navbar from '../components/Navbar.vue'

// --- Variables generales ---
const proveedores = ref([])
const loading = ref(true)
const errorMsg = ref('')

const PAGE_SIZE = 10
const currentPage = ref(1)

// --- Filtros de busqueda ---
const searchQuery = ref('')
const filterCiudad = ref('')   // derivado de direccion
const filterWeb = ref('')      // tiene web / no tiene web

// --- Modal Crear/Editar Proveedor ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})

// --- Modal Detalle (con contactos) ---
const showDetailModal = ref(false)
const selectedProveedor = ref(null)

// --- Modal Contacto (crear/editar) ---
const showContactoModal = ref(false)
const contactoEditing = ref(false)
const contactoFormData = ref({})
const contactoPadreId = ref(null)

// --- Helpers ---
const getCiudad = (direccion) => {
  if (!direccion) return ''
  // Heuristica simple: ultima parte despues de coma
  const parts = direccion.split(',')
  return parts[parts.length - 1].trim()
}

const ciudadesUnicas = computed(() => {
  const vals = new Set()
  proveedores.value.forEach(p => {
    const c = getCiudad(p.direccion)
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
      return nombre.includes(q) || email.includes(q) || tel.includes(q)
    })
  }

  if (filterCiudad.value) {
    result = result.filter(p => getCiudad(p.direccion) === filterCiudad.value)
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
    direccion: '',
    telefono_principal: '',
    email_principal: '',
    pagina_web: '',
    notas_generales: ''
  }
  showModal.value = true
}

const openEditModal = (prov) => {
  isEditing.value = true
  formData.value = { ...prov }
  showModal.value = true
}

const saveProveedor = async () => {
  try {
    const payload = { ...formData.value }
    if (isEditing.value) {
      await apiClient.put(`/proveedores/${payload.id}`, payload)
      alert('Proveedor actualizado')
    } else {
      await apiClient.post('/proveedores/', payload)
      alert('Proveedor creado')
    }
    showModal.value = false
    fetchProveedores()
  } catch (e) {
    const msg = e.response?.data?.detail || 'Error al guardar'
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg))
    console.error(e)
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
  showContactoModal.value = true
}

const openEditContacto = (contacto) => {
  contactoEditing.value = true
  contactoPadreId.value = contacto.proveedor_id
  contactoFormData.value = { ...contacto }
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
    // Refrescar y actualizar el detalle
    await fetchProveedores()
    const updated = proveedores.value.find(p => p.id === contactoPadreId.value)
    if (updated) selectedProveedor.value = updated
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
    await fetchProveedores()
    const updated = proveedores.value.find(p => p.id === contactoPadreId.value)
    if (updated) selectedProveedor.value = updated
  } catch (e) {
    alert('Error al eliminar contacto')
    console.error(e)
  }
}

onMounted(() => {
  fetchProveedores()
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
              placeholder="Empresa, email o telefono..." autocomplete="off" />
          </div>
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
            <th>Telefono</th>
            <th>Email</th>
            <th>Web</th>
            <th>Contactos</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="!filteredProveedores.length">
            <td class="table-empty-cell" colspan="7">
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
              <button class="btn-icon" title="Ver Detalle y Contactos" @click="openDetailModal(prov)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                </svg>
              </button>
              <button class="btn-icon" title="Editar" @click="openEditModal(prov)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5z"/>
                </svg>
              </button>
              <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteProveedor(prov.id)">
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
        No hay proveedores registrados. Haga clic en "Nuevo Proveedor" para comenzar.
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
          <div class="form-group">
            <label>Direccion</label>
            <input v-model="formData.direccion" type="text" placeholder="Av. Blanco Galindo, Cochabamba">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Telefono Principal</label>
              <input v-model="formData.telefono_principal" type="text" placeholder="+591 4 4223344">
            </div>
            <div class="form-group">
              <label>Email Principal</label>
              <input v-model="formData.email_principal" type="email" placeholder="ventas@empresa.bo">
            </div>
          </div>
          <div class="form-group">
            <label>Pagina Web</label>
            <input v-model="formData.pagina_web" type="text" placeholder="https://empresa.bo">
          </div>
          <div class="form-group">
            <label>Notas Generales</label>
            <textarea v-model="formData.notas_generales" rows="3"
              placeholder="Distribuidor autorizado, garantias, condiciones comerciales..."></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar</button>
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
            <button class="btn-sm btn-add-contacto" @click="openCreateContacto(selectedProveedor.id)">
              + Agregar Contacto
            </button>
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
              <div class="contacto-actions">
                <button class="btn-icon-sm" title="Editar" @click="openEditContacto(c)">
                  <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" fill="currentColor" viewBox="0 0 16 16">
                    <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10z"/>
                  </svg>
                </button>
                <button class="btn-icon-sm btn-danger-icon" title="Eliminar" @click="deleteContacto(c.id)">
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
          <button class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
          <button class="btn-edit-detail" @click="openEditModal(selectedProveedor); showDetailModal = false">Editar Empresa</button>
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

/* Iconos */
.actions-cell { display: flex; gap: 0.5rem; }
.btn-icon {
  background: #f0f2f5; border: none; padding: 8px; border-radius: 6px;
  cursor: pointer; color: #555; transition: background 0.2s;
}
.btn-icon:hover { background: #dfe2e6; }
.btn-icon-sm {
  background: #f0f2f5; border: none; padding: 5px; border-radius: 4px;
  cursor: pointer; color: #555; transition: background 0.2s;
}
.btn-icon-sm:hover { background: #dfe2e6; }
.btn-danger-icon:hover { background: #fee2e2; color: #c0392b; }
</style>
