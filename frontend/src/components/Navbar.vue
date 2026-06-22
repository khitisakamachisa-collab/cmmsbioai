<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import apiClient from '../services/api.js'

const route = useRoute()
const sistemaNombre = ref('CMMS-BioAI')
const modoTest = ref(false)

const navLinks = [
  { path: '/inicio', label: 'Inicio' },
  { path: '/equipos', label: 'Equipos' },
  { path: '/inventario', label: 'Repuestos' },
  { path: '/proveedores', label: 'Proveedores' },
  { path: '/ordenes', label: 'Ordenes' },
  { path: '/preventivo', label: 'Preventivo' },
  { path: '/historial', label: 'Historial' },
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

// Verificar si el sistema está en modo TEST
// Criterio: si existe un proveedor con nombre "TechMed Bolivia SRL" (creado por seed_test_data)
async function verificarModoTest() {
  try {
    const res = await apiClient.get('/proveedores/')
    if (Array.isArray(res.data)) {
      modoTest.value = res.data.some(p => p.nombre_empresa === 'TechMed Bolivia SRL')
    }
  } catch (e) {
    // Si falla, asumir que no está en modo TEST
    modoTest.value = false
  }
}

// Exponer la función para que otras vistas puedan llamarla después de cargar/limpiar TEST
defineExpose({ verificarModoTest })

onMounted(async () => {
  try {
    const res = await apiClient.get('/configuracion/')
    if (res.data?.empresa?.nombre) {
      sistemaNombre.value = res.data.empresa.nombre
    }
  } catch (e) {
    // Usar nombre por defecto si no se puede cargar
  }
  // Verificar modo TEST después de cargar la configuración
  await verificarModoTest()
})
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="header-title">{{ sistemaNombre }}</h1>
      <span v-if="modoTest" class="test-badge" title="El sistema tiene datos de ejemplo cargados. Ve a Configuración → Datos TEST para limpiar.">
        🧪 MODO TEST
      </span>
    </div>
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

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.header-title {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.test-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #1e293b;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  letter-spacing: 0.03em;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  animation: pulse-test 2s ease-in-out infinite;
}

@keyframes pulse-test {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
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
