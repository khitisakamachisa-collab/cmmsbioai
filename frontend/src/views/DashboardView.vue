<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../services/api.js'

// --- Variables Generales ---
const equipos = ref([])
const loading = ref(true)
const error_msg = ref('')

// --- NUEVO: Variable para guardar los estados disponibles ---
const estados = ref([])

// --- Variables Modal ---
const showModal = ref(false)
const isEditing = ref(false) 
const formData = ref({}) 

// --- Variables Historial ---
const showHistoryModal = ref(false)
const historyData = ref([])
const selectedEquipName = ref('')

// --- Funciones de Datos ---
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

// --- NUEVO: Función para obtener los estados del backend ---
const fetchEstados = async () => {
  try {
    const response = await apiClient.get('/equipos/estados')
    estados.value = response.data
  } catch (error) {
    console.error('Error al cargar estados', error)
  }
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
    estado_id: 1, // Por defecto 'Operativo' (ID 1)
    responsable_tecnico_id: 1
  }
  showModal.value = true
}

const openEditModal = (equipo) => {
  isEditing.value = true
  formData.value = { ...equipo }
  if (equipo.fecha_adquisicion) {
    formData.value.fecha_adquisicion = equipo.fecha_adquisicion.substring(0, 10)
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
  if (confirm("¿Estás seguro de eliminar este equipo? Se borrarán sus órdenes de trabajo asociadas.")) {
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

// --- NUEVO: Helper para mostrar nombre de estado en la tabla ---
const getNombreEstado = (id) => {
  const estado = estados.value.find(e => e.id === id)
  return estado ? estado.nombre_estado : 'Desconocido'
}

// --- NUEVO: Helper para asignar colores según el NOMBRE del estado ---
const getEstadoClass = (id) => {
  const nombre = getNombreEstado(id).toLowerCase() // Obtenemos el nombre (ej: "operativo")
  
  if (nombre.includes('operativo')) return 'bg-green'
  if (nombre.includes('inactivo')) return 'bg-red'
  if (nombre.includes('Fallo leve')) return 'bg-gray'
  if (nombre.includes('baja')) return 'bg-blue'
  if (nombre.includes('mantenimiento')) return 'bg-orange'
  
  return 'bg-default' // Color por defecto si no coincide con ninguno
}

onMounted(() => {
  fetchEquipos()
  fetchEstados() // Cargamos los estados al iniciar
})
</script>

<template>
  <div class="dashboard-container">
    <header class="header">
      <h1>CMMS-BioAI</h1>
      <nav>
        <router-link to="/dashboard">Equipos</router-link> |
        <router-link to="/ordenes">Órdenes</router-link> |
        <router-link to="/inventario">Inventario</router-link>
      </nav>
      <button @click="$router.push('/')">Cerrar Sesión</button>
    </header>

    <main class="content">
      <div class="top-bar">
        <h2>Listado de Equipos</h2>
        <button class="btn-primary" @click="openCreateModal">+ Nuevo Equipo</button>
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
          <tr v-for="equipo in equipos" :key="equipo.id">
            <td>{{ equipo.id }}</td>
            <td>{{ equipo.nombre_corto || 'N/A' }}</td>
            <td>{{ equipo.modelo }}</td>
            <td>{{ equipo.marca }}</td>
            <td>{{ equipo.ubicacion_actual }}</td>
            <td>
              <!-- MEJORA: Mostramos el nombre real del estado -->
              <span class="badge" :class="getEstadoClass(equipo.estado_id)">
               {{ getNombreEstado(equipo.estado_id) }}
              </span>
            </td>
            <td>
              <button class="btn-edit btn-sm" @click="openEditModal(equipo)">Editar</button>
              <button class="btn-danger btn-sm" @click="deleteEquipo(equipo.id)">Eliminar</button>
              <button class="btn-secondary btn-sm" @click="openHistory(equipo)">Ver Historial</button>
            </td>
          </tr>
        </tbody>
      </table>
    </main>

    <!-- Modal Crear/Editar Equipo -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>{{ isEditing ? 'Editar Equipo' : 'Registrar Nuevo Equipo' }}</h3>
        <form @submit.prevent="saveEquipo">
          <div class="form-group">
            <label>Nombre Corto (Opcional)</label>
            <input v-model="formData.nombre_corto" type="text" placeholder="Ej: Monitor UCI 02">
          </div>
          
          <div class="form-row">
            <div class="form-group">
              <label>Marca *</label>
              <input v-model="formData.marca" type="text" required placeholder="Ej: Philips">
            </div>
            <div class="form-group">
              <label>Modelo *</label>
              <input v-model="formData.modelo" type="text" required placeholder="Ej: MX-500">
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
             <!-- NUEVO: SELECTOR DE ESTADO -->
            <div class="form-group">
              <label>Estado del Equipo</label>
              <select v-model="formData.estado_id" required>
                <option v-for="estado in estados" :key="estado.id" :value="estado.id">
                  {{ estado.nombre_estado }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label>Ubicación</label>
            <input v-model="formData.ubicacion_actual" type="text" placeholder="Ej: UCI Box 5">
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
  </div>
</template>

<style scoped>
/* Estilos Existentes */
.btn-edit { background-color: #f39c12; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-right: 5px; }
.btn-danger { background-color: #c0392b; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; margin-right: 5px; }
.btn-sm { font-size: 0.85rem; }

.dashboard-container { padding: 0; }
.header { background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header nav a { color: white; text-decoration: none; margin-right: 15px; font-weight: bold; }
.header nav a:hover { text-decoration: underline; }
.header button { background-color: #e74c3c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }

.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }

.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 1rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem;}

/* NUEVO: Estilos para badges de estado */
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; background-color: #95a5a6; } /* Default gris */
.operativo { background-color: #27ae60; } /* Verde */
.mantenimiento { background-color: #e67e22; } /* Naranja */

/* Modales */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; max-width: 90%; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-size: 0.9rem; font-weight: bold; }

/* NUEVO: Estilo para inputs y selects */
.form-group input, 
.form-group select { 
  width: 100%; 
  padding: 0.6rem; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
  box-sizing: border-box; 
  background-color: white; /* Para que el select no se vea raro en algunos navegadores */
}

/* NUEVO: Fila de formulario para poner campos lado a lado */
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }

.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

/* Estilos Historial */
.history-table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.9rem; }
.history-table th, .history-table td { padding: 8px; border-bottom: 1px solid #eee; text-align: left; }
.history-table th { background-color: #f8f9fa; }
.empty-state { text-align: center; color: #888; padding: 2rem; }
.state-badge { background: #eee; color: #333; padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; }

/* Clases de colores para los estados */
.bg-green { background-color: #27ae60; color: white; } /* Operativo */
.bg-orange { background-color: #e67e22; color: white; } /* Mantenimiento */
.bg-red { background-color: #c0392b; color: white; } /* Dado de Baja */
.bg-gray { background-color: #95a5a6; color: white; } /* Reserva / Default */
.bg-blue { background-color:rgb(78, 101, 202); color: white; } /*  */
.bg-default { background-color: #7f8c8d; color: white; } /* Otros */

/* Asegúrate de que la clase .badge base tenga padding */
.badge { 
  padding: 4px 8px; 
  border-radius: 12px; 
  font-size: 0.8rem; 
  font-weight: bold;
}


</style>