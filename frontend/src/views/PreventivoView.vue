<script setup>
import { ref, onMounted, computed } from 'vue'
import apiClient from '../services/api.js'

// --- Variables ---
const tareas = ref([])
const equipos = ref([])
const usuarios = ref([])
const loading = ref(true)

// --- Modal ---
const showModal = ref(false)
const isEditing = ref(false)
const formData = ref({})

// --- Datos ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resTareas, resEquipos, resUsers] = await Promise.all([
      apiClient.get('/preventivo/'),
      apiClient.get('/equipos/'),
      apiClient.get('/users/')
    ])
    tareas.value = resTareas.data
    equipos.value = resEquipos.data
    usuarios.value = resUsers.data
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
  }
}

// --- Acciones CRUD ---
const openCreateModal = () => {
  isEditing.value = false
  formData.value = {
    equipo_id: '',
    responsable_id: null,
    titulo: '',
    frecuencia_dias: 90,
    ultima_fecha: null
  }
  showModal.value = true
}

const openEditModal = (tarea) => {
  isEditing.value = true
  formData.value = { ...tarea }
  if (tarea.ultima_fecha) formData.value.ultima_fecha = tarea.ultima_fecha.substring(0, 10)
  showModal.value = true
}

const saveTarea = async () => {
  try {
    if (isEditing.value) {
      await apiClient.put(`/preventivo/${formData.value.id}`, formData.value)
      alert('Tarea actualizada')
    } else {
      await apiClient.post('/preventivo/', formData.value)
      alert('Tarea creada')
    }
    showModal.value = false
    fetchData()
  } catch (error) {
    alert('Error al guardar tarea')
    console.error(error)
  }
}

const deleteTarea = async (id) => {
  if (confirm("¿Eliminar esta tarea preventiva?")) {
    try {
      await apiClient.delete(`/preventivo/${id}`) // Asumiendo que implementaste DELETE en backend
      alert('Tarea eliminada')
      fetchData()
    } catch (e) {
      alert('Error al eliminar')
    }
  }
}

// --- Helpers Visuales ---
const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? (eq.nombre_corto || eq.modelo) : 'N/A'
}
const getUsuarioNombre = (id) => {
  const u = usuarios.value.find(u => u.id === id)
  return u ? (u.full_name || u.username) : 'Sin asignar'
}

// Helper para calcular estado visual (Vencido, Próximo, OK)
const getStatusClass = (proximaFecha) => {
  if (!proximaFecha) return 'status-unknown'
  const today = new Date().setHours(0,0,0,0)
  const dueDate = new Date(proximaFecha).setHours(0,0,0,0)
  
  if (dueDate < today) return 'status-overdue' // Rojo: Vencido
  if (dueDate === today) return 'status-due-today' // Naranja: Hoy
  
  const diffDays = (dueDate - today) / (1000 * 60 * 60 * 24)
  if (diffDays <= 7) return 'status-upcoming' // Amarillo: Próximo (7 días)
  
  return 'status-ok' // Verde: OK
}

onMounted(() => {
  fetchData()
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
        <router-link to="/preventivo">Preventivo</router-link> |
        <router-link to="/usuarios">Usuarios</router-link> <!-- Faltaba este -->
      </nav>
      <button @click="$router.push('/')">Cerrar Sesión</button>
    </header>

    <main class="content">
      <div class="top-bar">
        <h2>Mantenimiento Preventivo</h2>
        <button class="btn-primary" @click="openCreateModal">+ Nueva Tarea</button>
      </div>

      <div v-if="loading">Cargando...</div>

      <table v-if="!loading && tareas.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Equipo</th>
            <th>Título</th>
            <th>Frecuencia</th>
            <th>Próxima Fecha</th>
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="tarea in tareas" :key="tarea.id">
            <td>#{{ tarea.id }}</td>
            <td>{{ getEquipoNombre(tarea.equipo_id) }}</td>
            <td><strong>{{ tarea.titulo }}</strong></td>
            <td>Cada {{ tarea.frecuencia_dias }} días</td>
            <td>{{ tarea.proxima_fecha || 'Pendiente' }}</td>
            <td>
              <span class="badge" :class="getStatusClass(tarea.proxima_fecha)">
                {{ tarea.proxima_fecha ? new Date(tarea.proxima_fecha).toLocaleDateString() : 'Sin fecha' }}
              </span>
            </td>
            <td class="actions-cell">
              <button class="btn-icon" title="Editar" @click="openEditModal(tarea)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                   <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10z"/>
                </svg>
              </button>
              <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteTarea(tarea.id)">
                 <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                  <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </main>

    <!-- Modal Crear/Editar -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Tarea Preventiva' : 'Nueva Tarea Preventiva' }}</h3>
        <form @submit.prevent="saveTarea">
          
          <div class="form-group">
            <label>Equipo *</label>
            <select v-model="formData.equipo_id" required>
              <option value="" disabled>Seleccione...</option>
              <option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}</option>
            </select>
          </div>

          <div class="form-group">
            <label>Título de la Tarea *</label>
            <input v-model="formData.titulo" placeholder="Ej: Calibración Anual" required>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Frecuencia (días)</label>
              <input v-model="formData.frecuencia_dias" type="number" min="1" required>
            </div>
            <div class="form-group">
              <label>Última Fecha Realizada</label>
              <input v-model="formData.ultima_fecha" type="date">
            </div>
          </div>

          <div class="form-group">
            <label>Responsable</label>
            <select v-model="formData.responsable_id">
              <option :value="null">-- Sin Asignar --</option>
              <option v-for="u in usuarios" :key="u.id" :value="u.id">{{ u.full_name || u.username }}</option>
            </select>
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
/* Reutilizamos estilos de DashboardView */
.header { background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header nav a { color: white; text-decoration: none; margin-right: 15px; font-weight: bold; }
.header button { background-color: #e74c3c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }

/* Iconos */
.actions-cell { display: flex; gap: 0.5rem; }
.btn-icon { background: #f0f2f5; border: none; padding: 8px; border-radius: 6px; cursor: pointer; color: #555; }
.btn-icon:hover { background: #dfe2e6; }
.btn-danger-icon:hover { background: #fee2e2; color: #c0392b; }

/* Badges de Estado Preventivo */
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: bold; }
.status-ok { background-color: #d4edda; color: #155724; } /* Verde: OK */
.status-upcoming { background-color: #fff3cd; color: #856404; } /* Amarillo: Próximo */
.status-overdue { background-color: #f8d7da; color: #721c24; } /* Rojo: Vencido */
.status-unknown { background-color: #e2e3e5; color: #383d41; }

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; max-width: 90%; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
</style>