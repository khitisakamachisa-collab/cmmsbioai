<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../services/api.js'

// --- Variables Generales ---
const ordenes = ref([])
const equipos = ref([])
const estadosOT = ref([]) 
const loading = ref(true)

// --- Control de Modales ---
const showModal = ref(false) // Modal Crear
const showCloseModal = ref(false) // Modal Cerrar/Editar
const selectedOT = ref({}) // OT seleccionada para editar

// --- Variables para Repuestos ---
const listaRepuestos = ref([])
const selectedRepuestoId = ref(null)
const selectedCantidad = ref(1)
const repuestosSeleccionados = ref([])

// Formulario Crear
const formData = ref({
  equipo_id: '',
  estado_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: 1
})

// Formulario Cerrar/Editar
const closeFormData = ref({
  estado_id: '',
  acciones_realizadas: '',
  tiempo_real_invertido: null
})

// --- Funciones de Datos ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resOrdenes, resEquipos, resEstados] = await Promise.all([
      apiClient.get('/ordenes/'),
      apiClient.get('/equipos/'),
      apiClient.get('/ordenes/estados/') 
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

const saveOrden = async () => {
  try {
    await apiClient.post('/ordenes/', formData.value)
    alert('Orden creada')
    showModal.value = false
    formData.value = { equipo_id: '', estado_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: 1 }
    fetchData() 
  } catch (error) {
    alert('Error al crear OT')
  }
}

// Abre el modal de cierre con los datos de la OT
const openCloseModal = async (ot) => {
  selectedOT.value = ot
  closeFormData.value = {
    estado_id: ot.estado_id,
    acciones_realizadas: ot.acciones_realizadas || '',
    tiempo_real_invertido: ot.tiempo_real_invertido || null
  }
  
  // Cargar inventario
  try {
    const res = await apiClient.get('/repuestos/')
    listaRepuestos.value = res.data
  } catch (e) { console.error(e) }
  
  repuestosSeleccionados.value = []
  showCloseModal.value = true
}

// Agregar repuesto a la lista temporal
const addRepuestoToOT = () => {
  if (!selectedRepuestoId.value || selectedCantidad.value < 1) return

  const repInfo = listaRepuestos.value.find(r => r.id === selectedRepuestoId.value)
  if (!repInfo) return

  if (selectedCantidad.value > repInfo.cantidad_disponible) {
    alert("No hay suficiente stock")
    return
  }

  repuestosSeleccionados.value.push({
    repuesto_id: repInfo.id,
    nombre: repInfo.nombre_repuesto,
    cantidad: selectedCantidad.value
  })

  selectedRepuestoId.value = null
  selectedCantidad.value = 1
}

const updateOrden = async () => {
  try {
    const payload = { 
      ...closeFormData.value,
      repuestos_utilizados: repuestosSeleccionados.value
    };
    
    if (payload.tiempo_real_invertido === "" || payload.tiempo_real_invertido === null) {
      payload.tiempo_real_invertido = null;
    } else {
      payload.tiempo_real_invertido = parseFloat(payload.tiempo_real_invertido);
    }

    await apiClient.put(`/ordenes/${selectedOT.value.id}`, payload)
    alert('Orden actualizada y stock ajustado')
    showCloseModal.value = false
    fetchData() 
  } catch (error) {
    console.error(error)
    if (error.response && error.response.data) {
        alert(`Error: ${JSON.stringify(error.response.data.detail)}`)
    }
  }
}

const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? `${eq.nombre_corto || eq.modelo}` : `ID: ${id}`
}

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
        <router-link to="/ordenes">Órdenes</router-link> |
        <router-link to="/inventario">Inventario</router-link>
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
            <th>Estado</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="ot in ordenes" :key="ot.id">
            <td>#{{ ot.id }}</td>
            <td>{{ getEquipoNombre(ot.equipo_id) }}</td>
            <td>
              <strong>{{ ot.titulo }}</strong><br>
              <small style="color: #666">{{ ot.descripcion_falla.substring(0, 30) }}...</small>
            </td>
            <td>
              <span class="badge" :class="prioridadClass(ot.prioridad)">
                {{ ot.prioridad }}
              </span>
            </td>
            <td>
               <span class="badge state">
                 {{ estadosOT.find(e => e.id === ot.estado_id)?.nombre_estado || 'N/A' }}
               </span>
            </td>
            <td>
              <button class="btn-secondary btn-sm" @click="openCloseModal(ot)">
                Ver / Cerrar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </main>

    <!-- Modal Crear OT -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>Nueva Orden de Trabajo</h3>
        <form @submit.prevent="saveOrden">
          <div class="form-group">
            <label>Equipo Afectado *</label>
            <select v-model="formData.equipo_id" required>
              <option value="" disabled>Seleccione...</option>
              <option v-for="eq in equipos" :key="eq.id" :value="eq.id">
                {{ eq.nombre_corto || eq.modelo }}
              </option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Estado *</label>
              <select v-model="formData.estado_id" required>
                <option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Prioridad</label>
              <select v-model="formData.prioridad">
                <option>Alta</option><option>Media</option><option>Baja</option><option>Urgente</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Título</label>
            <input v-model="formData.titulo" required>
          </div>
          <div class="form-group">
            <label>Descripción</label>
            <textarea v-model="formData.descripcion_falla" required></textarea>
          </div>
          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Crear</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Cerrar / Editar OT -->
    <div v-if="showCloseModal" class="modal-overlay" @click.self="showCloseModal = false">
      <div class="modal">
        <h3>Detalles y Cierre de OT #{{ selectedOT.id }}</h3>
        
        <div class="ot-details">
          <p><strong>Equipo:</strong> {{ getEquipoNombre(selectedOT.equipo_id) }}</p>
          <p><strong>Falla Reportada:</strong> {{ selectedOT.descripcion_falla }}</p>
        </div>

        <hr>

        <form @submit.prevent="updateOrden">
          <div class="form-group">
            <label>Nuevo Estado *</label>
            <select v-model="closeFormData.estado_id" required>
              <option v-for="est in estadosOT" :key="est.id" :value="est.id">
                {{ est.nombre_estado }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Acciones Realizadas</label>
            <textarea v-model="closeFormData.acciones_realizadas" rows="4" placeholder="Describa la reparación..."></textarea>
          </div>

          <div class="form-group">
            <label>Tiempo Real (Horas)</label>
            <input v-model="closeFormData.tiempo_real_invertido" type="number" step="0.5" placeholder="Ej: 1.5">
          </div>

          <!-- Sección de Repuestos -->
          <hr>
          <h4>Repuestos Utilizados</h4>
          
          <div class="repuesto-selector">
            <select v-model="selectedRepuestoId">
              <option :value="null">Seleccionar repuesto...</option>
              <option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">
                {{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})
              </option>
            </select>
            <input type="number" v-model="selectedCantidad" min="1" style="width: 60px">
            <button type="button" class="btn-sm" @click="addRepuestoToOT">Agregar</button>
          </div>

          <ul class="repuesto-lista">
            <li v-for="(item, idx) in repuestosSeleccionados" :key="idx">
              {{ item.cantidad }} x {{ item.nombre }}
            </li>
          </ul>

          <div class="modal-actions">
            <button type="button" class="btn-secondary" @click="showCloseModal = false">Cancelar</button>
            <button type="submit" class="btn-primary">Guardar Cambios</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Header Unificado */
.header { background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header nav a { color: white; text-decoration: none; margin-right: 15px; font-weight: bold; }
.header nav a:hover { text-decoration: underline; }

/* Botón Cerrar Sesión (Rojo) - Agregado */
.header button { 
  background-color: #e74c3c; 
  color: white; 
  border: none; 
  padding: 0.5rem 1rem; 
  border-radius: 4px; 
  cursor: pointer; 
}

.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }

/* Botones de Acción Unificados */
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 1rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem;}
.btn-sm { font-size: 0.85rem; padding: 5px 10px; }

.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; }
.urgente { background-color: #e74c3c; }
.alta { background-color: #e67e22; }
.media { background-color: #f1c40f; color: #333; }
.state { background-color: #3498db; }

/* Modales y Formularios */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 600px; max-width: 90%; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select, .form-group textarea { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
.ot-details { background: #f8f9fa; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }
.ot-details p { margin: 0.2rem 0; }

/* Repuestos */
.repuesto-selector { display: flex; gap: 10px; align-items: center; margin-bottom: 10px; }
.repuesto-selector select { flex: 1; padding: 5px; }
.repuesto-lista { list-style: none; padding: 0; background: #f9f9f9; margin-top: 5px; }
.repuesto-lista li { padding: 5px; border-bottom: 1px solid #eee; font-size: 0.9rem; }
</style>