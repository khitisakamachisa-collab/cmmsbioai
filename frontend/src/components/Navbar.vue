<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '../services/api.js'

const route = useRoute()
const sistemaNombre = ref('CMMS-BioAI')

const navLinks = [
  { path: '/inicio', label: 'Inicio' },
  { path: '/equipos', label: 'Equipos' },
  { path: '/ordenes', label: 'Ordenes' },
  { path: '/inventario', label: 'Repuestos' },
  { path: '/preventivo', label: 'Preventivo' },
  { path: '/historial', label: 'Historial' },
  { path: '/proveedores', label: 'Proveedores' },
  { path: '/reportes', label: 'Reportes' },
  { path: '/usuarios', label: 'Usuarios' },
  { path: '/ayuda', label: '?' },
  { path: '/configuracion', label: '\u2699\uFE0F' }
]

const emit = defineEmits(['logout'])

const logout = () => {
  localStorage.removeItem('token')
  emit('logout')
}

onMounted(async () => {
  try {
    const res = await apiClient.get('/configuracion/')
    if (res.data?.empresa?.nombre) {
      sistemaNombre.value = res.data.empresa.nombre
    }
  } catch (e) {
    // Usar nombre por defecto si no se puede cargar
  }
})
</script>

<template>
  <header class="header">
    <h1 class="header-title">{{ sistemaNombre }}</h1>
    <nav class="header-nav">
      <router-link
        v-for="link in navLinks"
        :key="link.path"
        :to="link.path"
        class="nav-link"
        :class="{ 'nav-link--active': route.path === link.path }"
      >
        {{ link.label }}
      </router-link>
    </nav>
    <button class="btn-logout" @click="logout">Cerrar Sesion</button>
  </header>
</template>

<style scoped>
.header {
  background-color: #2c3e50;
  color: white;
  padding: 1rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.header-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.header-nav {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.nav-link {
  color: rgba(255, 255, 255, 0.75);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
  padding: 0.35rem 0.75rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.nav-link:hover {
  color: white;
  background-color: rgba(255, 255, 255, 0.1);
  text-decoration: none;
}

.nav-link--active {
  color: white;
  background-color: rgba(255, 255, 255, 0.15);
}

.btn-logout {
  background-color: #e74c3c;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
  font-size: 0.85rem;
  transition: background-color 0.2s;
}

.btn-logout:hover {
  background-color: #c0392b;
}
</style>
