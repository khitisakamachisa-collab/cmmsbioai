<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../services/api.js'

// --- Variables Generales ---
const equipos = ref([])
const estados = ref([])
const tecnicos = ref([]) // Variable para técnicos
const loading = ref(true)
const error_msg = ref('')

// --- Variables Modal ---
const showModal = ref(false)
const isEditing = ref(false) 
const formData = ref({}) 

// --- Variables Historial ---
const showHistoryModal = ref(false)
const historyData = ref([])
const selectedEquipName = ref('')

// --- Variables Modal Detalle (NUEVO) ---
const showDetailModal = ref(false)
const selectedEquipo = ref({})


// Función para abrir el modal de detalles
const openDetailModal = (equipo) => {
  selectedEquipo.value = equipo
  showDetailModal.value = true
}

// Helper para mostrar el nombre del técnico (NUEVO)
const getTecnicoName = (id) => {
  if (!id) return 'Sin Asignar'
  const tec = tecnicos.value.find(t => t.id === id)
  return tec ? tec.nombre : 'Desconocido'
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

const fetchTecnicos = async () => {
  try {
    const response = await apiClient.get('/equipos/tecnicos')
    tecnicos.value = response.data
  } catch (error) {
    console.error('Error al cargar técnicos', error)
  }
}

// --- Funciones del Modal ---

const openCreateModal = () => {
  isEditing.value = false
  // Inicializamos formulario con TODOS los campos (antiguos y nuevos)
  formData.value = {
    nombre_corto: '',
    modelo: '',
    numero_serie: '',
    marca: '',
    fecha_adquisicion: '',
    ubicacion_actual: '',
    estado_id: 1,
    // Nuevos campos inicializados
    registro_sanitario_bolivia: '',
    proveedor_principal: '',
    descripcion: '',
    calibracion_proxima: '',
    responsable_tecnico_id: null // null = sin asignar
  }
  showModal.value = true
}

const openEditModal = (equipo) => {
  isEditing.value = true
  formData.value = { ...equipo }
  
  // Ajustes de formato de fecha para inputs date
  if (equipo.fecha_adquisicion) {
    formData.value.fecha_adquisicion = equipo.fecha_adquisicion.substring(0, 10)
  }
  if (equipo.calibracion_proxima) {
    formData.value.calibracion_proxima = equipo.calibracion_proxima.substring(0, 10)
  } else {
    formData.value.calibracion_proxima = ''
  }
  
  showModal.value = true
}

const saveEquipo = async () => {
  try {
    const payload = { ...formData.value };

    // Limpieza de campos vacíos a null (opcional pero recomendado para la BD)
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
  if (confirm("¿Estás seguro de eliminar este equipo?")) {
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
  fetchTecnicos() // Cargamos técnicos al inicio
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
              <!-- Usamos el color dinámico directamente -->
              <span class="badge" :style="{ backgroundColor: getEstadoColor(equipo.estado_id) }">
                {{ getNombreEstado(equipo.estado_id) }}
              </span>
            </td>
            <td class="actions-cell">
                <!-- NUEVO: Botón Ver Detalle (Icono Ojo) -->
              <button class="btn-icon" title="Ver Detalles" @click="openDetailModal(equipo)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/>
                </svg>
              </button>

              <!-- Botón Editar (Icono Lápiz) -->
              <button class="btn-icon" title="Editar" @click="openEditModal(equipo)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/>
                </svg>
              </button>

              <!-- Botón Eliminar (Icono Papelera) -->
              <button class="btn-icon btn-danger-icon" title="Eliminar" @click="deleteEquipo(equipo.id)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
                  <path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
                </svg>
              </button>

              <!-- Botón Historial (Icono Reloj) -->
              <button class="btn-icon btn-secondary-icon" title="Ver Historial" @click="openHistory(equipo)">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                  <path d="M8 3.5a.5.5 0 0 0-1 0V9a.5.5 0 0 0 .252.434l3.5 2a.5.5 0 0 0 .496-.868L8 8.71V3.5z"/>
                  <path d="M8 16A8 8 0 1 0 8 0a8 8 0 0 0 0 16zm7-8A7 7 0 1 1 1 8a7 7 0 0 1 14 0z"/>
                </svg>
              </button>
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
          
          <!-- Fila 1: Identificación -->
          <div class="form-group">
            <label>Nombre Corto</label>
            <input v-model="formData.nombre_corto" type="text" placeholder="Ej: Monitor UCI 02">
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>Marca *</label>
              <input v-model="formData.marca" type="text" required>
            </div>
            <div class="form-group">
              <label>Modelo *</label>
              <input v-model="formData.modelo" type="text" required>
            </div>
          </div>

          <div class="form-group">
            <label>Número de Serie *</label>
            <input v-model="formData.numero_serie" type="text" required placeholder="Único">
          </div>

          <!-- Fila 2: Fechas Importantes -->
          <div class="form-row">
            <div class="form-group">
              <label>Fecha Adquisición *</label>
              <input v-model="formData.fecha_adquisicion" type="date" required>
            </div>
            <div class="form-group">
              <label>Próxima Calibración</label>
              <input v-model="formData.calibracion_proxima" type="date">
            </div>
          </div>

          <!-- Fila 3: Ubicación y Estado -->
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

          <!-- Fila 4: Datos Administrativos (NUEVOS) -->
          <div class="form-row">
            <div class="form-group">
              <label>Registro Sanitario</label>
              <input v-model="formData.registro_sanitario_bolivia" type="text" placeholder="Código o N/A">
            </div>
            <div class="form-group">
              <label>Proveedor</label>
              <input v-model="formData.proveedor_principal" type="text" placeholder="Empresa proveedora">
            </div>
          </div>

          <!-- Fila 5: Responsable (NUEVO) -->
          <div class="form-group">
            <label>Técnico Responsable (Opcional)</label>
            <select v-model="formData.responsable_tecnico_id">
              <option :value="null">-- Sin Asignar --</option>
              <option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">
                {{ tec.nombre }}
              </option>
            </select>
          </div>

          <!-- Descripción (NUEVO) -->
          <div class="form-group">
            <label>Descripción / Notas</label>
            <textarea v-model="formData.descripcion" rows="3" placeholder="Detalles adicionales del equipo..."></textarea>
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
    <!-- Modal Ver Detalles (NUEVO) -->
    <div v-if="showDetailModal" class="modal-overlay" @click.self="showDetailModal = false">
      <div class="modal" style="width: 650px;">
        <h3>Detalles del Equipo: {{ selectedEquipo.nombre_corto || selectedEquipo.modelo }}</h3>
        
        <div class="detail-grid">
          <!-- Columna Izquierda -->
          <div class="detail-column">
            <h4>Identificación</h4>
            <p><strong>ID:</strong> {{ selectedEquipo.id }}</p>
            <p><strong>Marca:</strong> {{ selectedEquipo.marca }}</p>
            <p><strong>Modelo:</strong> {{ selectedEquipo.modelo }}</p>
            <p><strong>Nº Serie:</strong> {{ selectedEquipo.numero_serie }}</p>
            <p><strong>Ubicación:</strong> {{ selectedEquipo.ubicacion_actual || 'N/A' }}</p>
          </div>

          <!-- Columna Derecha -->
          <div class="detail-column">
            <h4>Administrativo</h4>
            <p><strong>Estado:</strong> 
              <span class="badge" :style="{ backgroundColor: getEstadoColor(selectedEquipo.estado_id) }">
                {{ getNombreEstado(selectedEquipo.estado_id) }}
              </span>
            </p>
            <p><strong>Fecha Adquisición:</strong> {{ selectedEquipo.fecha_adquisicion || 'N/A' }}</p>
            <p><strong>Registro Sanitario:</strong> {{ selectedEquipo.registro_sanitario_bolivia || 'N/A' }}</p>
            <p><strong>Proveedor:</strong> {{ selectedEquipo.proveedor_principal || 'N/A' }}</p>
            <p><strong>Próx. Calibración:</strong> {{ selectedEquipo.calibracion_proxima || 'N/A' }}</p>
          </div>
        </div>

        <!-- Fila Completa -->
        <div class="detail-full">
          <h4>Responsable y Notas</h4>
          <p><strong>Técnico Responsable:</strong> {{ getTecnicoName(selectedEquipo.responsable_tecnico_id) }}</p>
          <p><strong>Descripción:</strong></p>
          <div class="description-box">
            {{ selectedEquipo.descripcion || 'Sin descripción adicional.' }}
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-secondary" @click="showDetailModal = false">Cerrar</button>
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
/* Estilos para Iconos de Acción */
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

.btn-secondary-icon:hover {
  background: #e2e8f0;
  color: #475569;
}

/* Estilo para area de texto */
.form-group textarea {
  width: 100%; 
  padding: 0.6rem; 
  border: 1px solid #ccc; 
  border-radius: 4px; 
  box-sizing: border-box; 
  resize: vertical; /* Permite redimensionar solo verticalmente */
  font-family: inherit;
}
  /* Estilos para el Modal de Detalles */
  .detail-grid {
    display: flex;
    gap: 2rem;
    margin-bottom: 1.5rem;
  }

  .detail-column {
    flex: 1;
  }

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
    background: white;
    padding: 0.8rem;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    min-height: 50px;
    color: #444;
    font-size: 0.9rem;
  }
</style>