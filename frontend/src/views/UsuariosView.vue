<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import apiClient from '../services/api.js'

const usuarios = ref([])
const currentPage = ref(1)
const pageSize = ref(10)
const showModal = ref(false)
const formData = ref({ nombre_completo: '', email: '', password: '', rol: 'tecnico' })

const paginatedUsuarios = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return usuarios.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(usuarios.value.length / pageSize.value))
)

watch(
  () => usuarios.value.length,
  (len) => {
    const tp = Math.max(1, Math.ceil(len / pageSize.value))
    if (currentPage.value > tp) currentPage.value = tp
  }
)

const irPaginaAnterior = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}

const irPaginaSiguiente = () => {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

const fetchUsuarios = async () => {
  try {
    const res = await apiClient.get('/users/')
    usuarios.value = res.data
  } catch (error) {
    console.error(error)
  }
}

const saveUsuario = async () => {
  try {
    // Enviamos nombre_completo, el backend lo mapea a full_name
    await apiClient.post('/users/', formData.value)
    alert('Usuario creado exitosamente')
    showModal.value = false
    // Limpiar form
    formData.value = { nombre_completo: '', email: '', password: '', rol: 'tecnico' }
    fetchUsuarios()
  } catch (error) {
    alert('Error: ' + (error.response?.data?.detail || 'No se pudo crear'))
  }
}

onMounted(() => {
  fetchUsuarios()
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
        <router-link to="/usuarios">Usuarios</router-link>
      </nav>
      <button @click="$router.push('/')">Cerrar Sesión</button>
    </header>

    <main class="content">
      <div class="top-bar">
        <h2>Gestión de Usuarios y Técnicos</h2>
        <button class="btn-primary" @click="showModal = true">+ Nuevo Usuario</button>
      </div>

      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Email</th>
            <th>Rol</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="user in paginatedUsuarios" :key="user.id">
            <td>{{ user.id }}</td>
            <td><strong>{{ user.full_name || user.username }}</strong></td>
            <td>{{ user.email }}</td>
            <td>
              <span class="badge" :class="user.role === 'admin' ? 'bg-orange' : 'bg-gray'">
                {{ user.role }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <div
        v-if="usuarios.length"
        class="table-pagination"
        role="navigation"
        aria-label="Paginación de usuarios"
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

    <!-- Modal Crear Usuario -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <h3>Nuevo Usuario</h3>
        <form @submit.prevent="saveUsuario">
          <div class="form-group">
            <label>Nombre Completo</label>
            <input v-model="formData.nombre_completo" required>
          </div>
          <div class="form-group">
            <label>Email (será su usuario)</label>
            <input v-model="formData.email" type="email" required>
          </div>
          <div class="form-group">
            <label>Contraseña</label>
            <input v-model="formData.password" type="password" required>
          </div>
          <div class="form-group">
            <label>Rol</label>
            <select v-model="formData.rol">
              <option value="tecnico">Técnico</option>
              <option value="admin">Administrador</option>
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
/* Estilos necesarios para que se vea igual que DashboardView */
.header { background-color: #2c3e50; color: white; padding: 1rem 2rem; display: flex; justify-content: space-between; align-items: center; }
.header nav a { color: white; text-decoration: none; margin-right: 15px; font-weight: bold; }
.header button { background-color: #e74c3c; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer; }
.content { padding: 2rem; }
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
.top-bar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; }
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 2rem; border-radius: 8px; width: 400px; }
.form-group { margin-bottom: 1rem; }
.form-group label { display: block; margin-bottom: 0.5rem; font-weight: bold; }
.form-group input, .form-group select { width: 100%; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; }
.bg-orange { background-color: #e67e22; }
.bg-gray { background-color: #95a5a6; }

.table-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  margin-top: 1rem;
  padding: 0.75rem 0;
}
.table-pagination-meta {
  font-size: 0.9rem;
  color: #475569;
}
.btn-pagination {
  background-color: #3498db;
  color: white;
  border: none;
  padding: 0.5rem 1.1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.9rem;
}
.btn-pagination:hover:not(:disabled) {
  background-color: #2980b9;
}
.btn-pagination:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}
</style>