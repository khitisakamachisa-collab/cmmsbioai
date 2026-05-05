<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../services/api.js'

const ordenes = ref([])
const equipos = ref([])
const estadosOT = ref([]) // Para el dropdown de estados
const loading = ref(true)
const showModal = ref(false)

const formData = ref({
  equipo_id: '',
  estado_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: 1 // Por defecto asignamos al admin/user 1
})

// 1. Cargar Datos Iniciales
const fetchData = async () => {
  try {
    loading.value = true
    // Cargar todo en paralelo para ir rápido
    const [resOrdenes, resEquipos, resEstados] = await Promise.all([
      apiClient.get('/ordenes/'),
      apiClient.get('/equipos/'),
      apiClient.get('/ordenes/estados/') // Endpoint que creamos en el backend
    ])
    
    ordenes.value = resOrdenes.data
    equipos.value = resEquipos.data
    estadosOT.value = resEstados.data

  } catch (error) {
    console.error('Error cargando datos', error)
  } finally {
    loading.value = false
  }
}

// 2. Guardar Nueva Orden
const saveOrden = async () => {
  try {
    await apiClient.post('/ordenes/', formData.value)
    alert('Orden de Trabajo creada exitosamente')
    showModal.value = false
    // Limpiar formulario
    formData.value = { equipo_id: '', estado_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: 1 }
    fetchData() // Recargar lista
  } catch (error) {
    alert('Error al crear OT')
    console.error(error)
  }
}

// Función auxiliar para mostrar el nombre del equipo en la tabla (en vez del ID)
const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? `${eq.nombre_corto || eq.modelo} (${eq.marca})` : `ID: ${id}`
}

// Función auxiliar para color de prioridad
const prioridadClass = (prio) => {
  if (prio === 'Urgente') return 'urgente'
  if (prio === 'Alta') return 'alta'
  return 'media'
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
        <router-link to="/ordenes">Órdenes</router-link>
      </nav>
      <button @click="$router.push('/')">Cerrar Sesión</button>
    </header>

    <main class="content">
      <div class="top-bar">
        <h2>Listado de Órdenes de Trabajo</h2>
        <button class="btn-primary" @click="showModal = true">+ Nueva Orden</button>
      </div>

      <div v-if="loading">Cargando...</div>

      <table v-if="!loading && ordenes.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Equipo</th>
            <th>Título / Falla</th>
            <th>Prioridad</th>
            <th>Estado ID</th>
            <th>Fecha</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ot in ordenes" :key="ot.id">
            <td>#{{ ot.id }}</td>
            <td>{{ getEquipoNombre(ot.equipo_id) }}</td>
            <td>
              <strong>{{ ot.titulo }}</strong><br>
              <small style="color: #666">{{ ot.descripcion_falla.substring(0, 40) }}...</small>
            </td>
            <td>
              <span class="badge" :class="prioridadClass(ot.prioridad)">
                {{ ot.prioridad }}
              </span>
            </td>
            <td>{{ ot.estado_id }}</td>
            <td>{{ new Date(ot.fecha_creacion).toLocaleDateString() }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!loading && ordenes.length === 0">No hay órdenes registradas.</div>
    </main>

    <!-- Modal Nueva OT -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>Nueva Orden de Trabajo</h3>
        <form @submit.prevent="saveOrden">
          
          <div class="form-group">
            <label>Equipo Afectado *</label>
            <select v-model="formData.equipo_id" required>
              <option value="" disabled>Seleccione un equipo...</option>
              <option v-for="eq in equipos" :key="eq.id" :value="eq.id">
                {{ eq.nombre_corto || eq.modelo }} (S/N: {{ eq.numero_serie }})
              </option>
            </select>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Estado *</label>
              <select v-model="formData.estado_id" required>
                <option value="" disabled>Seleccione...</option>
                <option v-for="est in estadosOT" :key="est.id" :value="est.id">
                  {{ est.nombre_estado }}
                </option>
              </select>
            </div>
            <div class="form-group">
              <label>Prioridad *</label>
              <select v-model="formData.prioridad" required>
                <option>Alta</option>
                <option>Media</option>
                <option>Baja</option>
                <option>Urgente</option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Título Corto *</label>
            <input v-model="formData.titulo" type="text" placeholder="Ej: Falla de encendido" required>
          </div>

          <div class="form-group">
            <label>Descripción de la Falla *</label>
            <textarea v-model="formData.descripcion_falla" rows="3" placeholder="Detalle del problema..." required></textarea>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Crear Orden</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Reutilizamos estilos de Dashboard, añadimos algunos nuevos */
.header { background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header nav a { color: white; text-decoration: none; margin-right: 15px; font-weight: bold; }
.header nav a:hover { text-decoration: underline; }
.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; }
.top-bar { display: flex; justify-content: space-between; align-items: center; }

.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; }

/* Badges de prioridad */
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; }
.urgente { background-color: #e74c3c; }
.alta { background-color: #e67e22; }
.media { background-color: #f1c40f; color: #333; }

/* Modal y Form */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 600px; max-width: 90%; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
</style>