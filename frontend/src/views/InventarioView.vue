<script setup>
import { ref, computed, onMounted } from 'vue'
import apiClient from '../services/api.js'

const repuestos = ref([])
const loading = ref(true)
const searchQuery = ref('')

const showModal = ref(false)
const isEditing = ref(false)
const showDetailModal = ref(false)
const selectedRepuesto = ref({})

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

onMounted(() => {
  fetchRepuestos()
})
</script>

<template>
  <div class="dashboard-container">
    <header class="header">
      <h1>CMMS-BioAI</h1>
      <nav>
        <router-link to="/dashboard">Equipos</router-link> |
        <router-link to="/ordenes">Órdenes</router-link> |
        <router-link to="/inventario">Inventario</router-link> |
        <router-link to="/usuarios">Usuarios</router-link>
      </nav>
      <button type="button" @click="$router.push('/')">Cerrar Sesión</button>
    </header>

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
            <tr v-for="rep in filteredRepuestos" :key="rep.id">
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

      <div v-if="!loading && repuestos.length === 0" class="empty-state">No hay repuestos registrados.</div>
    </main>

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
.header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header nav a {
  color: white;
  text-decoration: none;
  margin-right: 15px;
  font-weight: bold;
}
.header nav a:hover { text-decoration: underline; }
.header button {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
}

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
.btn-secondary {
  background-color: #95a5a6;
  color: white;
  border: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

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
</style>
