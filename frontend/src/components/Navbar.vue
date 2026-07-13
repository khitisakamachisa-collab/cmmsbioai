<script setup>
import { ref, onMounted, watch, provide } from 'vue'
import { useRouter } from 'vue-router'
import apiClient from '../services/api.js'
import Sidebar from './Sidebar.vue'

const router = useRouter()
const sistemaNombre = ref('CMMS-BioAI')
const modoTest = ref(false)
const drawerOpen = ref(false)

// Sidebar mode: 'hidden', 'compact', 'expanded'
const sidebarMode = ref(localStorage.getItem('cmms-sidebar-mode') || 'hidden')

const emit = defineEmits(['logout'])

// --- Notificaciones y Mensajes ---
const showNotifPanel = ref(false)
const showMsgPanel = ref(false)
const showSugPanel = ref(false)

const alertas = ref([
  { id: 1, texto: 'Equipo "Rayos X Portatil" requiere calibracion antes del 15/07', tiempo: 'Hace 2 horas', tipo: 'warning', leida: false },
  { id: 2, texto: '5 ordenes de trabajo pendientes sin asignar tecnico', tiempo: 'Hace 4 horas', tipo: 'danger', leida: false },
  { id: 3, texto: 'Contrato #3 con TechMed vence en 7 dias', tiempo: 'Hace 1 dia', tipo: 'warning', leida: false },
  { id: 4, texto: 'Stock bajo: Jeringa 5ml quedan 3 unidades', tiempo: 'Hace 2 dias', tipo: 'info', leida: true },
])

const sugerencias = ref([
  { id: 1, texto: 'El equipo "Ventilador UV" tiene 3 OT correctivas en el ultimo mes. Considera programar mantenimiento preventivo.', tiempo: 'Hace 1 hora', leida: false, categoria: 'mantenimiento' },
  { id: 2, texto: 'El tecnico Carlos Ramirez tiene la mayor carga de trabajo. Redistribuir tareas podria mejorar tiempos de respuesta.', tiempo: 'Hace 3 horas', leida: false, categoria: 'operacion' },
  { id: 3, texto: 'Se detecto un patron: los fallos electricos aumentan un 40% en temporada de lluvias. Anticipa repuestos.', tiempo: 'Hace 1 dia', leida: false, categoria: 'prediccion' },
  { id: 4, texto: 'El proveedor BioParts tiene el mejor tiempo de entrega (1.2 dias promedio). Priorizar pedidos ahi.', tiempo: 'Hace 2 dias', leida: true, categoria: 'proveedores' },
  { id: 5, texto: 'El 65% de las OT se cierran en menos de 48h. El benchmark del sector es 72h. Buen desempeno.', tiempo: 'Hace 3 dias', leida: true, categoria: 'metricas' },
])

const mensajes = ref([
  { id: 1, remitente: 'Sistema', texto: 'Bienvenido al modulo de Mantenimiento Preventivo v0.9.23', tiempo: 'Hace 30 min', leido: false },
  { id: 2, remitente: 'Dr. Martinez', texto: 'Solicito revision del monitor de signos vitales en Terapia Intensiva', tiempo: 'Hace 3 horas', leido: false },
  { id: 3, remitente: 'Sistema', texto: 'Resumen semanal: 12 OT cerradas, 3 en progreso, 2 urgentes', tiempo: 'Hace 1 dia', leido: true },
  { id: 4, remitente: 'Lic. Rojas', texto: 'Se necesita reposicion urgente de electrodos ECG en Urgencias', tiempo: 'Hace 2 dias', leido: false },
  { id: 5, remitente: 'Sistema', texto: 'Actualizacion disponible: nueva funcionalidad de reportes PDF', tiempo: 'Hace 3 dias', leido: true },
  { id: 6, remitente: 'Admin', texto: 'Recordatorio: respaldar base de datos antes de fin de mes', tiempo: 'Hace 5 dias', leido: true },
])

const alertasNoLeidas = () => alertas.value.filter(a => !a.leida).length
const mensajesNoLeidos = () => mensajes.value.filter(m => !m.leido).length
const sugerenciasNoLeidas = () => sugerencias.value.filter(s => !s.leida).length

const toggleNotifPanel = () => {
  showNotifPanel.value = !showNotifPanel.value
  showMsgPanel.value = false
  showSugPanel.value = false
}
const toggleMsgPanel = () => {
  showMsgPanel.value = !showMsgPanel.value
  showNotifPanel.value = false
  showSugPanel.value = false
}
const toggleSugPanel = () => {
  showSugPanel.value = !showSugPanel.value
  showNotifPanel.value = false
  showMsgPanel.value = false
}
const closePanels = () => {
  showNotifPanel.value = false
  showMsgPanel.value = false
  showSugPanel.value = false
}

const marcarAlertaLeida = (id) => {
  const a = alertas.value.find(x => x.id === id)
  if (a) a.leida = true
}
const marcarMensajeLeido = (id) => {
  const m = mensajes.value.find(x => x.id === id)
  if (m) m.leido = true
}
const marcarTodasAlertas = () => { alertas.value.forEach(a => a.leida = true) }
const marcarTodosMensajes = () => { mensajes.value.forEach(m => m.leido = true) }
const marcarSugerenciaLeida = (id) => {
  const s = sugerencias.value.find(x => x.id === id)
  if (s) s.leida = true
}
const marcarTodasSugerencias = () => { sugerencias.value.forEach(s => s.leida = true) }

function getSidebarWidth() {
  if (sidebarMode.value === 'compact') return '60px'
  if (sidebarMode.value === 'expanded') return '250px'
  return '0px'
}

// Actualizar variable CSS cuando cambia el modo
function applySidebarWidth() {
  document.documentElement.style.setProperty('--sidebar-width', getSidebarWidth())
}

watch(sidebarMode, (val) => {
  localStorage.setItem('cmms-sidebar-mode', val)
  applySidebarWidth()
  // Si se cambia a modo visible, cerrar el drawer
  if (val !== 'hidden') {
    drawerOpen.value = false
  }
})

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

// Verificar modo TEST
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

provide('verificarModoTest', verificarModoTest)

defineExpose({ verificarModoTest })

onMounted(async () => {
  applySidebarWidth()
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
      <button
        v-if="sidebarMode === 'hidden'"
        class="menu-toggle"
        @click="toggleDrawer"
        title="Abrir menu"
      >
        <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
          <path d="M3 6h16M3 11h16M3 16h16" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </svg>
      </button>
      <h1 class="header-title">{{ sistemaNombre }}</h1>
      <span v-if="modoTest" class="test-badge" title="Datos de ejemplo cargados. Ve a Configuracion → Datos TEST para limpiar.">
        TEST
      </span>
    </div>

    <div class="header-right">
      <!-- Icono Alertas -->
      <button class="notif-btn" :class="{ active: showNotifPanel }" @click="toggleNotifPanel" title="Alertas">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 2a6 6 0 00-6 6v3l-1.5 2H17.5L16 11V8a6 6 0 00-6-6z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M7.5 16.5a2.5 2.5 0 005 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/>
        </svg>
        <span v-if="alertasNoLeidas() > 0" class="notif-badge badge-alert">{{ alertasNoLeidas() }}</span>
      </button>

      <!-- Icono Mensajes -->
      <button class="notif-btn" :class="{ active: showMsgPanel }" @click="toggleMsgPanel" title="Mensajes">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M2 4h16a1 1 0 011 1v8a1 1 0 01-1 1H5l-3 3V5a1 1 0 011-1z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
        </svg>
        <span v-if="mensajesNoLeidos() > 0" class="notif-badge badge-msg">{{ mensajesNoLeidos() }}</span>
      </button>

      <!-- Icono Sugerencias -->
      <button class="notif-btn" :class="{ active: showSugPanel }" @click="toggleSugPanel" title="Sugerencias">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
          <path d="M10 2a1 1 0 011 1v5.126a4.002 4.002 0 01-2 0V3a1 1 0 011-1zM10 12.5a1.75 1.75 0 110 3.5 1.75 1.75 0 010-3.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
          <path d="M17.071 5.929a7 7 0 010 8.142M2.929 5.929a7 7 0 000 8.142" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" fill="none"/>
          <path d="M14.828 8.172a4 4 0 010 3.656M5.172 8.172a4 4 0 000 3.656" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" fill="none"/>
        </svg>
        <span v-if="sugerenciasNoLeidas() > 0" class="notif-badge badge-sug">{{ sugerenciasNoLeidas() }}</span>
      </button>
    </div>
  </header>

  <!-- Click fuera para cerrar paneles -->
  <div v-if="showNotifPanel || showMsgPanel || showSugPanel" class="panel-overlay" @click="closePanels"></div>

  <!-- Panel Alertas -->
  <Transition name="slide">
    <div v-if="showNotifPanel" class="side-panel panel-alertas">
      <div class="panel-header">
        <h3><svg width="18" height="18" viewBox="0 0 20 20" fill="none" style="vertical-align: -3px; margin-right: 6px;"><path d="M10 2a6 6 0 00-6 6v3l-1.5 2H17.5L16 11V8a6 6 0 00-6-6z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M7.5 16.5a2.5 2.5 0 005 0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/></svg>Alertas</h3>
        <button v-if="alertasNoLeidas() > 0" class="panel-link" @click="marcarTodasAlertas">Marcar todas como leidas</button>
      </div>
      <div class="panel-body">
        <div
          v-for="a in alertas" :key="a.id"
          class="notif-item"
          :class="{ 'notif-unread': !a.leida }"
          @click="marcarAlertaLeida(a.id)"
        >
          <div class="notif-icon-wrap" :class="'tipo-' + a.tipo">
            <svg v-if="a.tipo === 'danger'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm0 10a1 1 0 110-2 1 1 0 010 2zm1-4a1 1 0 00-2 0V5a1 1 0 112 0v2z"/></svg>
            <svg v-else-if="a.tipo === 'warning'" width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8.982 1.566a1.13 1.13 0 00-1.96 0L.165 13.233c-.457.778.091 1.767.98 1.767h13.713c.889 0 1.438-.99.98-1.767L8.982 1.566zM8 5a.905.905 0 01.9.995l-.35 3.507a.552.552 0 01-1.1 0L7.1 5.995A.905.905 0 018 5zm.002 6a1 1 0 100 2 1 1 0 000-2z"/></svg>
            <svg v-else width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 16A8 8 0 108 0a8 8 0 000 16zm.93-9.412l-1 4.705c-.07.34.029.533.304.533.194 0 .487-.07.686-.246l-.088.416c-.287.346-.92.598-1.465.598-.703 0-1.002-.422-.808-1.319l.738-3.468c.064-.293.006-.399-.287-.47l-.451-.081.082-.381 1.96-.42h.035l-.007.006z"/><path d="M8 5.5a1 1 0 110-2 1 1 0 010 2z"/></svg>
          </div>
          <div class="notif-content">
            <p class="notif-text">{{ a.texto }}</p>
            <span class="notif-time">{{ a.tiempo }}</span>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Panel Mensajes -->
  <Transition name="slide">
    <div v-if="showMsgPanel" class="side-panel panel-mensajes">
      <div class="panel-header">
        <h3><svg width="18" height="18" viewBox="0 0 20 20" fill="none" style="vertical-align: -3px; margin-right: 6px;"><path d="M2 4h16a1 1 0 011 1v8a1 1 0 01-1 1H5l-3 3V5a1 1 0 011-1z" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/></svg>Mensajes</h3>
        <button v-if="mensajesNoLeidos() > 0" class="panel-link" @click="marcarTodosMensajes">Marcar todas como leidas</button>
      </div>
      <div class="panel-body">
        <div
          v-for="m in mensajes" :key="m.id"
          class="notif-item"
          :class="{ 'notif-unread': !m.leido }"
          @click="marcarMensajeLeido(m.id)"
        >
          <div class="msg-avatar">{{ m.remitente.charAt(0) }}</div>
          <div class="notif-content">
            <p class="msg-sender">{{ m.remitente }}</p>
            <p class="notif-text">{{ m.texto }}</p>
            <span class="notif-time">{{ m.tiempo }}</span>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <!-- Panel Sugerencias -->
  <Transition name="slide">
    <div v-if="showSugPanel" class="side-panel panel-sugerencias">
      <div class="panel-header">
        <h3><svg width="18" height="18" viewBox="0 0 20 20" fill="none" style="vertical-align: -3px; margin-right: 6px;"><path d="M10 2a1 1 0 011 1v5.126a4.002 4.002 0 01-2 0V3a1 1 0 011-1zM10 12.5a1.75 1.75 0 110 3.5 1.75 1.75 0 010-3.5z" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" fill="none"/><path d="M17.071 5.929a7 7 0 010 8.142M2.929 5.929a7 7 0 000 8.142" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" fill="none"/><path d="M14.828 8.172a4 4 0 010 3.656M5.172 8.172a4 4 0 000 3.656" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" fill="none"/></svg>Sugerencias</h3>
        <button v-if="sugerenciasNoLeidas() > 0" class="panel-link" @click="marcarTodasSugerencias">Marcar todas como leidas</button>
      </div>
      <div class="panel-body">
        <div
          v-for="s in sugerencias" :key="s.id"
          class="notif-item"
          :class="{ 'notif-unread': !s.leida }"
          @click="marcarSugerenciaLeida(s.id)"
        >
          <div class="sug-icon-wrap" :class="'cat-' + s.categoria">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor"><path d="M8 1a7 7 0 100 14A7 7 0 008 1zm1 10.5a1 1 0 11-2 0 1 1 0 012 0zM8.25 3.75a.75.75 0 01.75.75v4a.75.75 0 01-1.5 0v-4a.75.75 0 01.75-.75z" opacity="0.9"/></svg>
          </div>
          <div class="notif-content">
            <p class="notif-text">{{ s.texto }}</p>
            <div class="notif-meta">
              <span class="sug-categoria" :class="'cat-tag-' + s.categoria">{{ s.categoria }}</span>
              <span class="notif-time">{{ s.tiempo }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Transition>

  <Sidebar
    :open="drawerOpen"
    :mode="sidebarMode"
    @close="closeDrawer"
    @logout="logout"
    @set-mode="sidebarMode = $event"
  />
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
  min-width: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
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

/* --- Botones de notificacion --- */
.notif-btn {
  position: relative;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}
.notif-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
}
.notif-btn.active {
  background: rgba(59, 130, 246, 0.25);
  color: #60a5fa;
  border-color: rgba(59, 130, 246, 0.4);
}

/* --- Badge contador (estilo Facebook) --- */
.notif-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  border-radius: 9px;
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 4px;
  line-height: 1;
  border: 2px solid #2c3e50;
  pointer-events: none;
}
.badge-alert {
  background: #ef4444;
  color: #fff;
}
.badge-msg {
  background: #3b82f6;
  color: #fff;
}
.badge-sug {
  background: #10b981;
  color: #fff;
}

/* --- Overlay para cerrar panel --- */
.panel-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 998;
}

/* ============================= */
/* Panel lateral derecho - TEMA OSCURO (igual que sidebar #1e2a3a y navbar #2c3e50) */
/* ============================= */
.side-panel {
  position: fixed;
  top: 0;
  right: 0;
  width: 380px;
  max-width: 90vw;
  height: 100vh;
  background: #1e2a3a;
  box-shadow: -4px 0 24px rgba(0, 0, 0, 0.35);
  z-index: 999;
  display: flex;
  flex-direction: column;
  color: #e2e8f0;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.9rem 1.25rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: #2c3e50;
  flex-shrink: 0;
}
.panel-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: 0.03em;
  display: flex;
  align-items: center;
}
.panel-link {
  background: none;
  border: none;
  color: #60a5fa;
  font-size: 0.75rem;
  cursor: pointer;
  font-weight: 600;
  padding: 0;
  white-space: nowrap;
}
.panel-link:hover {
  color: #93bbfc;
  text-decoration: underline;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 0.4rem 0;
}

/* --- Scrollbar oscuro para el panel --- */
.panel-body::-webkit-scrollbar {
  width: 6px;
}
.panel-body::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.15);
}
.panel-body::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}
.panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

/* --- Items de notificacion/mensaje --- */
.notif-item {
  display: flex;
  gap: 0.75rem;
  padding: 0.85rem 1.25rem;
  cursor: pointer;
  transition: background 0.15s;
  border-left: 3px solid transparent;
}
.notif-item:hover {
  background: rgba(255, 255, 255, 0.06);
}
.notif-unread {
  background: rgba(59, 130, 246, 0.1);
  border-left-color: #3b82f6;
}
.notif-unread:hover {
  background: rgba(59, 130, 246, 0.18);
}

.notif-content {
  flex: 1;
  min-width: 0;
}
.notif-text {
  margin: 0 0 0.3rem 0;
  font-size: 0.84rem;
  color: #cbd5e1;
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.notif-time {
  font-size: 0.72rem;
  color: #64748b;
}

/* --- Meta row (sugerencias: categoria + tiempo) --- */
.notif-meta {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  margin-top: 0.35rem;
}

/* Iconos de tipo alerta */
.notif-icon-wrap {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.tipo-danger { background: rgba(239, 68, 68, 0.2); color: #f87171; }
.tipo-warning { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.tipo-info { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }

/* Avatar de mensaje */
.msg-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}
.msg-sender {
  margin: 0 0 0.15rem 0;
  font-size: 0.8rem;
  font-weight: 700;
  color: #f1f5f9;
}

/* --- Iconos de sugerencia por categoria --- */
.sug-icon-wrap {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}
.cat-mantenimiento { background: rgba(245, 158, 11, 0.2); color: #fbbf24; }
.cat-operacion { background: rgba(59, 130, 246, 0.2); color: #60a5fa; }
.cat-prediccion { background: rgba(168, 85, 247, 0.2); color: #c084fc; }
.cat-proveedores { background: rgba(16, 185, 129, 0.2); color: #34d399; }
.cat-metricas { background: rgba(236, 72, 153, 0.2); color: #f472b6; }

/* Tags de categoria */
.sug-categoria {
  display: inline-block;
  font-size: 0.65rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 8px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}
.cat-tag-mantenimiento { background: rgba(245, 158, 11, 0.15); color: #fbbf24; }
.cat-tag-operacion { background: rgba(59, 130, 246, 0.15); color: #60a5fa; }
.cat-tag-prediccion { background: rgba(168, 85, 247, 0.15); color: #c084fc; }
.cat-tag-proveedores { background: rgba(16, 185, 129, 0.15); color: #34d399; }
.cat-tag-metricas { background: rgba(236, 72, 153, 0.15); color: #f472b6; }

/* --- Animacion slide --- */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.25s ease, opacity 0.25s ease;
}
.slide-enter-from,
.slide-leave-to {
  transform: translateX(100%);
  opacity: 0;
}
</style>