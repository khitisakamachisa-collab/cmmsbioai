<script setup>
import { ref, onMounted } from 'vue'
import apiClient from '../services/api.js'

const repuestos = ref([])
const loading = ref(true)
const showModal = ref(false)

const formData = ref({
  nombre_repuesto: '',
  numero_material: '',
  cantidad_disponible: 0,
  unidad_medida: 'unidad',
  ubicacion_almacen: ''
})

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

const saveRepuesto = async () => {
  try {
    await apiClient.post('/repuestos/', formData.value)
    alert('Repuesto agregado')
    showModal.value = false
    formData.value = { nombre_repuesto: '', numero_material: '', cantidad_disponible: 0, unidad_medida: 'unidad', ubicacion_almacen: '' }
    fetchRepuestos()
  } catch (error) {
    alert('Error al guardar')
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
        <router-link to="/usuarios">Usuarios</router-link> <!-- AGREGAR ESTO -->
      </nav>
      <button @click="$router.push('/')">Cerrar Sesión</button>
    </header>

    <main class="content">
      <div class="top-bar">
        <h2>Almacén de Repuestos</h2>
        <button class="btn-primary" @click="showModal = true">+ Agregar Repuesto</button>
      </div>

      <table v-if="!loading && repuestos.length">
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Nº Material</th>
            <th>Stock</th>
            <th>Ubicación</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="rep in repuestos" :key="rep.id">
            <td>#{{ rep.id }}</td>
            <td><strong>{{ rep.nombre_repuesto }}</strong></td>
            <td>{{ rep.numero_material || 'N/A' }}</td>
            <td>
              <span :class="rep.cantidad_disponible <= 5 ? 'low-stock' : 'stock'">
                {{ rep.cantidad_disponible }} {{ rep.unidad_medida }}
              </span>
            </td>
            <td>{{ rep.ubicacion_almacen || 'Sin ubicar' }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="!loading && repuestos.length === 0">No hay repuestos registrados.</div>
    </main>

    <!-- Modal Agregar Repuesto -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>Nuevo Repuesto</h3>
        <form @submit.prevent="saveRepuesto">
          <div class="form-group">
            <label>Nombre *</label>
            <input v-model="formData.nombre_repuesto" required>
          </div>
          <div class="form-group">
            <label>Número de Material / Código</label>
            <input v-model="formData.numero_material">
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Cantidad Inicial</label>
              <input v-model="formData.cantidad_disponible" type="number">
            </div>
            <div class="form-group">
              <label>Unidad</label>
              <select v-model="formData.unidad_medida">
                <option>unidad</option>
                <option>par</option>
                <option>metro</option>
                <option>litro</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Ubicación Física</label>
            <input v-model="formData.ubicacion_almacen" placeholder="Ej: Estante B2">
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
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem;}

.stock { color: #27ae60; font-weight: bold; }
.low-stock { color: #e74c3c; font-weight: bold; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 500px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.form-row { display: flex; gap: 1rem; }
.form-row .form-group { flex: 1; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
</style>