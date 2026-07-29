<script setup>
import { watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const props = defineProps({
  open: { type: Boolean, default: false },
  mode: { type: String, default: 'hidden' }
})

const emit = defineEmits(['close', 'logout', 'set-mode'])

const route = useRoute()
const router = useRouter()

const navLinks = [
  { path: '/inicio',        label: 'Inicio',        icon: '🏠' },
  { path: '/equipos',       label: 'Equipos',       icon: '🔧' },
  { path: '/inventario',    label: 'Repuestos',     icon: '📦' },
  { path: '/proveedores',   label: 'Proveedores',   icon: '🏢' },
  { path: '/contratos',     label: 'Contratos',     icon: '📜' },
  { path: '/ordenes',       label: 'Ordenes',       icon: '📋' },
  { path: '/preventivo',    label: 'Preventivo',    icon: '🛡️' },
  { path: '/planificacion', label: 'Planificacion',  icon: '📅' },
  { path: '/historial',     label: 'Historial',     icon: '📂' },
  { path: '/reportes',      label: 'Reportes',      icon: '📊' },
  { path: '/usuarios',      label: 'Usuarios',      icon: '👥' },
  { path: '/ayuda',         label: 'Ayuda',         icon: '❓' },
  { path: '/configuracion', label: 'Configuracion',  icon: '⚙️' }
]

function navigateTo(path) {
  router.push(path)
  if (props.mode === 'hidden') {
    emit('close')
  }
}

function onKeydown(e) {
  if (e.key === 'Escape' && props.open && props.mode === 'hidden') {
    emit('close')
  }
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => document.removeEventListener('keydown', onKeydown))

watch(() => props.open, (val) => {
  if (props.mode === 'hidden') {
    document.body.style.overflow = val ? 'hidden' : ''
  }
})
</script>

<template>
  <Teleport to="body">
    <!-- Overlay: solo en modo oculto cuando esta abierto -->
    <Transition name="fade">
      <div v-if="open && mode === 'hidden'" class="sidebar-overlay" @click="$emit('close')"></div>
    </Transition>

    <!-- Panel lateral izquierdo -->
    <aside
      class="sidebar-panel"
      :class="{
        'sb-hidden':  mode === 'hidden',
        'sb-compact': mode === 'compact',
        'sb-expanded': mode === 'expanded',
        'sb-open':    open && mode === 'hidden'
      }"
    >
      <!-- Header: solo en expandido y drawer (v-if para 0 espacio en compacto) -->
      <div v-if="mode !== 'compact'" class="sb-header">
        <h2 class="sb-title">Menu</h2>
        <button v-if="mode === 'hidden'" class="sb-close" @click="$emit('close')" title="Cerrar">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M15 5L5 15M5 5l10 10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>
      </div>

      <!-- Nav links -->
      <nav class="sb-nav">
        <button
          v-for="link in navLinks"
          :key="link.path"
          class="sb-link"
          :class="{ 'sb-link--active': route.path === link.path }"
          :title="link.label"
          @click="navigateTo(link.path)"
        >
          <span class="sb-icon">{{ link.icon }}</span>
          <span v-show="mode !== 'compact'" class="sb-label">{{ link.label }}</span>
        </button>
      </nav>

      <!-- Footer: selector de modo + logout -->
      <div class="sb-footer">
        <div class="sb-mode-selector">
          <button
            class="sb-mode-btn"
            :class="{ 'sb-mode-btn--active': mode === 'hidden' }"
            @click="$emit('set-mode', 'hidden')"
            title="Ocultar menu"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="1" y="1" width="11" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/>
              <path d="M8 9h8.5M14.5 6.5L17 9l-2.5 2.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span v-show="mode !== 'compact'" class="sb-mode-label">Ocultar</span>
          </button>
          <button
            class="sb-mode-btn"
            :class="{ 'sb-mode-btn--active': mode === 'compact' }"
            @click="$emit('set-mode', 'compact')"
            title="Solo iconos"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="4" y="1" width="4" height="16" rx="1.5" stroke="currentColor" stroke-width="1.5"/>
            </svg>
            <span v-show="mode !== 'compact'" class="sb-mode-label">Iconos</span>
          </button>
          <button
            class="sb-mode-btn"
            :class="{ 'sb-mode-btn--active': mode === 'expanded' }"
            @click="$emit('set-mode', 'expanded')"
            title="Iconos + texto"
          >
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <rect x="1" y="1" width="14" height="16" rx="2" stroke="currentColor" stroke-width="1.5"/>
              <path d="M5 6h6M5 9h6M5 12h4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
            <span v-show="mode !== 'compact'" class="sb-mode-label">Menu</span>
          </button>
        </div>

        <button class="sb-logout" @click="$emit('logout')">
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M6.5 14.5v-11a2 2 0 012-2h1a2 2 0 012 2v11" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            <path d="M11.5 8h5M13.5 6l2 2-2 2" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span v-show="mode !== 'compact'" class="sb-logout-label">Cerrar Sesion</span>
        </button>
      </div>
    </aside>
  </Teleport>
</template>

<style scoped>
/* ─── Overlay ─── */
.sidebar-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  z-index: 998;
  backdrop-filter: blur(2px);
}

/* ─── Panel base ─── */
.sidebar-panel {
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  background: #1e2a3a;
  color: #e2e8f0;
  z-index: 999;
  display: flex;
  flex-direction: column;
  transition: width 0.25s ease, transform 0.28s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
}

/* ─── Modo oculto (off-screen) ─── */
.sb-hidden {
  width: 250px;
  transform: translateX(-100%);
  box-shadow: none;
}
.sb-hidden.sb-open {
  transform: translateX(0);
  box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
}

/* ─── Modo compacto (iconos, 60px) ─── */
.sb-compact {
  width: 60px;
  transform: translateX(0);
}

/* ─── Modo expandido (iconos + texto, 250px) ─── */
.sb-expanded {
  width: 250px;
  transform: translateX(0);
}

/* ─── Header ─── */
.sb-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1.25rem;
  border-bottom: none;
  flex-shrink: 0;
}

.sb-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.sb-close {
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
  flex-shrink: 0;
}
.sb-close:hover {
  background: rgba(255, 255, 255, 0.12);
  color: #f8fafc;
}

/* ─── Nav links ─── */
.sb-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 0;
}

.sb-link {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  padding: 0.45rem 1.25rem;
  border: none;
  background: none;
  color: #cbd5e1;
  font-size: 0.92rem;
  font-weight: 500;
  text-align: left;
  cursor: pointer;
  transition: all 0.15s ease;
  position: relative;
  white-space: nowrap;
}

/* En modo compacto, centrar el icono */
.sb-compact .sb-link {
  justify-content: center;
  padding: 0.45rem 0;
  gap: 0;
}

.sb-link:hover {
  background: rgba(255, 255, 255, 0.06);
  color: #f1f5f9;
}

.sb-link--active {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  font-weight: 600;
}

.sb-link--active::before {
  content: '';
  position: absolute;
  right: 0;
  top: 0.4rem;
  bottom: 0.4rem;
  width: 3px;
  border-radius: 3px 0 0 3px;
  background: #3b82f6;
}

.sb-icon {
  font-size: 1.15rem;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.sb-label {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* ─── Footer ─── */
.sb-footer {
  padding: 0.6rem 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

/* Selector de modo */
.sb-mode-selector {
  display: flex;
  gap: 2px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 3px;
  margin-bottom: 0.5rem;
}

.sb-mode-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  padding: 0.35rem 0.3rem;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s;
}

/* En modo compacto, los botones de modo se hacen mas pequeños */
.sb-compact .sb-mode-selector {
  flex-direction: column;
  gap: 2px;
  padding: 3px;
  margin-bottom: 0.4rem;
}

.sb-compact .sb-mode-btn {
  padding: 0.3rem;
}

.sb-mode-btn:hover {
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.04);
}

.sb-mode-btn--active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.sb-mode-label {
  font-size: 0.68rem;
  font-weight: 600;
  white-space: nowrap;
}

/* Logout */
.sb-logout {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  width: 100%;
  padding: 0.55rem 0.75rem;
  border: none;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.1);
  color: #fca5a5;
  font-size: 0.82rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.sb-compact .sb-logout {
  padding: 0.5rem;
}

.sb-logout:hover {
  background: rgba(239, 68, 68, 0.22);
  color: #fecaca;
}

.sb-logout-label {
  white-space: nowrap;
}

/* ─── Transiciones overlay ─── */
.fade-enter-active { transition: opacity 0.25s ease; }
.fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>