<script setup>
import { ref, onMounted, provide } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import RightDrawer from './RightDrawer.vue'

const router = useRouter()
const sistemaNombre = ref('CMMS-BioAI')
const modoTest = ref(false)
const drawerOpen = ref(false)

const emit = defineEmits(['logout'])

const toggleDrawer = () => {
  drawerOpen.value = !drawerOpen.value
}

const closeDrawer = () => {
  drawerOpen.value = false
}

const logout = () => {
  drawerOpen.value = false
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
    modoTest.value = false
  }
}

// Proporcionar verificarModoTest a componentes hijos (ej. ConfiguracionView)
provide('verificarModoTest', verificarModoTest)

defineExpose({ verificarModoTest })

onMounted(async () => {
  try {
    const res = await apiClient.get('/configuracion/')
    if (res.data?.empresa?.nombre) {
      sistemaNombre.value = res.data.empresa.nombre
    }
  } catch (e) {
    // Usar nombre por defecto
  }
  await verificarModoTest()
})
</script>

<template>
  <header class="header">
    <div class="header-left">
      <h1 class="header-title">{{ sistemaNombre }}</h1>
      <span v-if="modoTest" class="test-badge" title="El sistema tiene datos de ejemplo cargados. Ve a Configuracion → Datos TEST para limpiar.">
        🧪 TEST
      </span>
    </div>

    <button class="menu-toggle" @click="toggleDrawer" title="Abrir menu">
      <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
        <path d="M3 6h16M3 11h16M3 16h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>

    <RightDrawer :open="drawerOpen" @close="closeDrawer" @logout="logout" />
  </header>
</template>

<style scoped>
.header {
  background-color: #2c3e50;
  color: white;
  padding: 0.6rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  min-width: 0; /* permite truncar si es necesario */
}

.header-title {
  margin: 0;
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.test-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  color: #1e293b;
  font-size: 0.68rem;
  font-weight: 700;
  padding: 0.2rem 0.5rem;
  border-radius: 10px;
  letter-spacing: 0.03em;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  animation: pulse-test 2s ease-in-out infinite;
  flex-shrink: 0;
}

@keyframes pulse-test {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.85; }
}

.menu-toggle {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  flex-shrink: 0;
}

.menu-toggle:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.2);
  color: #fff;
}
</style>