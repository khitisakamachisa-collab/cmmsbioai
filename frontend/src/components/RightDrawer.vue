<script setup>
import { ref, watch, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  open: { type: Boolean, default: false }
})
const emit = defineEmits(['close', 'logout'])

const route = useRoute()
const router = useRouter()

const navLinks = [
  { path: '/inicio',       label: 'Inicio',        icon: '🏠' },
  { path: '/equipos',      label: 'Equipos',       icon: '🔧' },
  { path: '/inventario',   label: 'Repuestos',     icon: '📦' },
  { path: '/proveedores',  label: 'Proveedores',   icon: '🏢' },
  { path: '/contratos',    label: 'Contratos',     icon: '📜' },
  { path: '/ordenes',      label: 'Ordenes',       icon: '📋' },
  { path: '/preventivo',   label: 'Preventivo',    icon: '🛡️' },
  { path: '/planificacion',label: 'Planificacion',  icon: '📅' },
  { path: '/historial',    label: 'Historial',     icon: '📂' },
  { path: '/reportes',     label: 'Reportes',      icon: '📊' },
  { path: '/usuarios',     label: 'Usuarios',      icon: '👥' },
  { path: '/ayuda',        label: 'Ayuda',         icon: '❓' },
  { path: '/configuracion',label: 'Configuracion',  icon: '⚙️' }
]

function navigateTo(path) {
  router.push(path)
  emit('close')
}

function onLogout() {
  emit('logout')
}

// Cerrar con Escape
function onKeydown(e) {
  if (e.key === 'Escape' && props.open) {
    emit('close')
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

// Bloquear scroll del body cuando el drawer está abierto
watch(() => props.open, (val) => {
  document.body.style.overflow = val ? 'hidden' : ''
})
</script>

<template>
  <Teleport to="body">
    <!-- Overlay -->
    <Transition name="fade">
      <div v-if="open" class="drawer-overlay" @click="$emit('close')"></div>
    </Transition>

    <!-- Panel -->
    <Transition name="slide">
      <aside v-if="open" class="drawer-panel">
        <div class="drawer-header">
          <h2 class="drawer-title">Menu</h2>
          <button class="drawer-close" @click="$emit('close')" title="Cerrar menu">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>

        <nav class="drawer-nav">
          <button
            v-for="link in navLinks"
            :key="link.path"
            class="drawer-link"
            :class="{ 'drawer-link--active': route.path === link.path }"
            @click="navigateTo(link.path)"
          >
            <span class="drawer-link-icon">{{ link.icon }}</span>
            <span class="drawer-link-label">{{ link.label }}</span>
            <svg v-if="route.path === link.path" class="drawer-link-check" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8l3.5 3.5L13 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </nav>

        <div class="drawer-footer">
          <button class="drawer-logout" @click="onLogout">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <path d="M6.5 14.5v-11a2 2 0 012-2h1a2 2 0 012 2v11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              <path d="M11.5 8h5M13.5 6l2 2-2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Cerrar Sesion</span>
          </button>
        </div>
      </aside>
    </Transition>
  </Teleport>
</template>

<style scoped>
/* ─── Overlay ─── */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 998;
  backdrop-filter: blur(2px);
}

/* ─── Panel ─── */
.drawer-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 280px;
  height: 100vh;
  background: #1e2a3a;
  color: #e2e8f0;
  z-index: 999;
  display: flex;
  flex-direction: column;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.3);
}

/* ─── Header ─── */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.1rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.drawer-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.drawer-close {
  background: rgba(255, 255, 255, 0.06);
  border: none;
  color: #94a3b8;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.drawer-close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #f8fafc;
}

/* ─── Nav Links ─── */
.drawer-nav {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem 0;
}

.drawer-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.7rem 1.25rem;
  border: none;
  background: none;
  color: #cbd5e1;
  font-size: 0.92rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
}

.drawer-link:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #f1f5f9;
}

.drawer-link--active {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  font-weight: 600;
}

.drawer-link--active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.4rem;
  bottom: 0.4rem;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #3b82f6;
}

.drawer-link-icon {
  font-size: 1.15rem;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.drawer-link-label {
  flex: 1;
}

.drawer-link-check {
  flex-shrink: 0;
  color: #3b82f6;
}

/* ─── Footer ─── */
.drawer-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.drawer-logout {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.65rem 1rem;
  border: none;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.12);
  color: #fca5a5;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.drawer-logout:hover {
  background: rgba(239, 68, 68, 0.25);
  color: #fecaca;
}

/* ─── Transiciones ─── */
.fade-enter-active { transition: opacity 0.25s ease; }
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.slide-enter-active { transition: transform 0.28s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-leave-active { transition: transform 0.22s cubic-bezier(0.4, 0, 0.2, 1); }
.slide-enter-from { transform: translateX(100%); }
.slide-leave-to { transform: translateX(100%); }
</style>