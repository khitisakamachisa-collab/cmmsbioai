<script setup>
import { ref } from 'vue'
import Navbar from '../components/Navbar.vue'

const seccionActiva = ref('sistema')

const secciones = [
  { id: 'sistema', emoji: '🏥', label: 'El Sistema' },
  { id: 'modulos', emoji: '🧩', label: 'Modulos' },
  { id: 'entidades', emoji: '📦', label: 'Entidades' },
  { id: 'archivos', emoji: '📁', label: 'Archivos' },
  { id: 'pendientes', emoji: '📋', label: 'Pendientes' }
]

const modulos = [
  {
    emoji: '📊', nombre: 'Inicio (Dashboard)', ruta: '/inicio',
    descripcion: 'Panel principal con resumen general del sistema. Muestra metricas clave en tarjetas y graficos interactivos.',
    funcionalidades: ['5 tarjetas de metricas en tiempo real', 'Graficos de equipos por estado, ordenes por prioridad y estado', 'Sugerencias automaticas con enlaces directos']
  },
  {
    emoji: '⚙️', nombre: 'Equipos', ruta: '/equipos',
    descripcion: 'Gestion completa de equipos biomédicos con CRUD, imagenes, documentos, Excel y filtros combinados.',
    funcionalidades: ['CRUD completo', '19 estados predefinidos', 'Imagen principal y documentos adjuntos', 'Importacion masiva Excel/CSV', 'Filtros combinados AND', 'Historial por equipo']
  },
  {
    emoji: '🔧', nombre: 'Ordenes de Trabajo', ruta: '/ordenes',
    descripcion: 'Gestion de OTs para mantenimiento correctivo y preventivo con descuento automatico de stock.',
    funcionalidades: ['CRUD completo', '5 estados de OT', '4 niveles de prioridad', 'Repuestos utilizados con descuento automatico', 'Evento automatico en Historial al completar', 'Documentos adjuntos por OT']
  },
  {
    emoji: '🔩', nombre: 'Inventario (Repuestos + Herramientas)', ruta: '/inventario',
    descripcion: 'Gestion de inventario dividida en Repuestos y Herramientas. Ambos soportan imagen, documentos e importacion Excel.',
    funcionalidades: ['Repuestos: CRUD con datos tecnicos y stock', 'Herramientas: CRUD con categorias y estado de uso', 'Alerta de stock bajo', 'Importacion masiva Excel/CSV', 'Imagen y documentos adjuntos']
  },
  {
    emoji: '🛡️', nombre: 'Preventivo', ruta: '/preventivo',
    descripcion: 'Planificacion de mantenimiento preventivo con frecuencia en dias y kit de repuestos.',
    funcionalidades: ['CRUD de tareas preventivas', 'Calculo automatico de proxima fecha', 'Kit de repuestos requeridos', 'Generacion de OT desde tarea', 'Actualizacion automatica al completar OT preventiva']
  },
  {
    emoji: '📜', nombre: 'Historial', ruta: '/historial',
    descripcion: 'Timeline cronologico de eventos de mantenimiento.',
    funcionalidades: ['Timeline visual con iconos por tipo', '4 tipos de evento', 'Creacion automatica al completar OT', 'Creacion manual', 'Filtro por equipo']
  },
  {
    emoji: '📈', nombre: 'Reportes', ruta: '/reportes',
    descripcion: '6 reportes con graficos interactivos y filtros por rango de fechas.',
    funcionalidades: ['Mantenimiento por equipo', 'OTs por periodo', 'Analisis de costos', 'Cumplimiento preventivo', 'Disponibilidad de equipos', 'Inventario de repuestos']
  },
  {
    emoji: '👥', nombre: 'Usuarios', ruta: '/usuarios',
    descripcion: 'Administracion de usuarios con roles (tecnico/admin) y autenticacion JWT.',
    funcionalidades: ['CRUD de usuarios', 'Roles: tecnico y administrador', 'JWT con bcrypt', 'Activacion/desactivacion']
  },
  {
    emoji: '⚙️', nombre: 'Configuracion', ruta: '/configuracion',
    descripcion: 'Gestion del sistema con 3 capas de recuperacion y configuracion editable de empresa y directorios.',
    funcionalidades: ['Capa 1: Metadatos .meta.json', 'Capa 2: Escaneo y recuperacion', 'Capa 3: Backup/Restore JSON', 'Nombre del sistema editable', 'Directorios configurables', 'Mover archivos a otra particion']
  }
]

const entidades = [
  { nombre: 'Equipo', tabla: 'equipo', prefijo: 'E', descripcion: 'Equipo biomédico. ID: E0001, E0002, etc.', campos: 'modelo, numero_serie, marca, estado_id, imagen_ruta' },
  { nombre: 'OrdenTrabajo', tabla: 'ordentrabajo', prefijo: '—', descripcion: 'Orden de trabajo correctiva o preventiva.', campos: 'equipo_id, estado_id, prioridad, titulo, descripcion_falla' },
  { nombre: 'Repuesto', tabla: 'repuesto', prefijo: 'R', descripcion: 'Repuesto con stock y alerta de nivel minimo. ID: R0001, etc.', campos: 'nombre_repuesto, cantidad_disponible, nivel_stock_minimo, precio_referencia' },
  { nombre: 'Herramienta', tabla: 'herramienta', prefijo: 'H', descripcion: 'Herramienta del taller. ID: H0001, etc.', campos: 'nombre_herramienta, categoria, estado_uso, costo_adquisicion' },
  { nombre: 'TareaPreventiva', tabla: 'tareapreventiva', prefijo: '—', descripcion: 'Tarea preventiva programada.', campos: 'equipo_id, frecuencia_dias, proxima_fecha, activa' },
  { nombre: 'DocumentoAdjunto', tabla: 'documentoadjunto', prefijo: '—', descripcion: 'Documento adjunto a cualquier entidad.', campos: 'nombre_archivo, ruta_archivo, categoria, equipo_id/repuesto_id/herramienta_id' },
  { nombre: 'EventoHistorial', tabla: 'eventohistorial', prefijo: '—', descripcion: 'Evento en el historial de mantenimiento.', campos: 'equipo_id, tipo_evento, descripcion, acciones_realizadas' },
  { nombre: 'EstadoEquipo', tabla: 'estadoequipo', prefijo: '—', descripcion: '19 estados con colores (Operativo, En mantenimiento, etc.)', campos: 'nombre_estado, color' },
  { nombre: 'EstadoOT', tabla: 'estadoot', prefijo: '—', descripcion: '5 estados de OT (Abierta, En Proceso, etc.)', campos: 'nombre_estado, color' },
  { nombre: 'Usuario', tabla: 'usuario', prefijo: '—', descripcion: 'Usuario del sistema. Roles: tecnico, admin.', campos: 'username, email, full_name, role, is_active' }
]

const pendientes = [
  { emoji: '📅', nombre: 'Calendario Preventivo (RF10)', prioridad: 'Alta', descripcion: 'Vista de calendario visual para tareas preventivas programadas.', estado: 'No implementado' },
  { emoji: '🏢', nombre: 'Gestion de Proveedores (RF12)', prioridad: 'Media', descripcion: 'CRUD de proveedores con historial de compras.', estado: 'No implementado' },
  { emoji: '🔒', nombre: 'Proteccion de rutas por autenticacion', prioridad: 'Alta', descripcion: 'Validar token JWT en endpoints y navigation guards en frontend.', estado: 'No implementado' },
  { emoji: '📄', nombre: 'Paginacion en listados', prioridad: 'Media', descripcion: 'Implementar offset/limit en endpoints de listado.', estado: 'No implementado' },
  { emoji: '🔐', nombre: 'Secret JWT configurable', prioridad: 'Media', descripcion: 'Mover secreto JWT a variable de entorno o config.json.', estado: 'No implementado' },
  { emoji: '🛠️', nombre: 'Configuracion editable', prioridad: 'Alta', descripcion: 'Nombre del sistema, directorios y mover archivos a otra particion.', estado: 'Implementado' }
]

const archivosEstructura = [
  { carpeta: 'uploads/EQUIPOS/', descripcion: 'Imagenes y documentos de equipos', patron: 'E0001_Nombre/E0001_Nombre.jpg' },
  { carpeta: 'uploads/REPUESTOS/', descripcion: 'Imagenes y documentos de repuestos', patron: 'R0001_Nombre/R0001_Nombre.png' },
  { carpeta: 'uploads/HERRAMIENTAS/', descripcion: 'Imagenes y documentos de herramientas', patron: 'H0001_Nombre/H0001_Nombre.jpg' },
  { carpeta: 'uploads/EQUIPOS/E0001_xxx/DOC/', descripcion: 'Documentos adjuntos de un equipo', patron: 'manual_usuario.pdf, foto_dano.jpg' }
]

const metaJsonEjemplo = `{
  "entidad_tipo": "equipo",
  "id": 1,
  "nombre_corto": "Monitor de Signos Vitales",
  "codigo": "E0001",
  "modelo": "IntelliVue MX800",
  "marca": "Philips",
  "numero_serie": "SN-2024-001",
  "imagen_ruta": "EQUIPOS/E0001_Monitor/E0001_Monitor.jpg"
}`
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />
    <main class="content">
      <div class="help-header">
        <h2>Ayuda del Sistema</h2>
        <p class="help-subtitle">Guia de referencia completa de CMMS-BioAI</p>
      </div>

      <nav class="help-nav">
        <button v-for="sec in secciones" :key="sec.id" class="help-nav-btn" :class="{ 'help-nav-btn--active': seccionActiva === sec.id }" @click="seccionActiva = sec.id">
          <span class="help-nav-emoji">{{ sec.emoji }}</span>
          <span class="help-nav-label">{{ sec.label }}</span>
        </button>
      </nav>

      <!-- SISTEMA -->
      <section v-if="seccionActiva === 'sistema'" class="help-section">
        <div class="help-card help-card--hero">
          <h3>Que es CMMS-BioAI?</h3>
          <p><strong>CMMS-BioAI</strong> es un Sistema de Gestion de Mantenimiento Asistido por Computadora diseñado para <strong>equipos biomédicos</strong> en el contexto boliviano. Proyecto de Maestria en Ingenieria Biomédica.</p>
          <p>Permite registrar equipos biomédicos, gestionar OTs, controlar inventario de repuestos y herramientas, planificar mantenimiento preventivo y generar reportes analiticos.</p>
        </div>
        <div class="help-card">
          <h3>Tecnologias</h3>
          <div class="tech-grid">
            <div class="tech-item"><span class="tech-icon">🐍</span><div><strong>Backend</strong><p>Python + FastAPI + SQLModel + SQLite</p></div></div>
            <div class="tech-item"><span class="tech-icon">💚</span><div><strong>Frontend</strong><p>Vue 3 + Vue Router + Chart.js + Axios</p></div></div>
            <div class="tech-item"><span class="tech-icon">🔐</span><div><strong>Auth</strong><p>OAuth2 + JWT + bcrypt</p></div></div>
            <div class="tech-item"><span class="tech-icon">💾</span><div><strong>BD</strong><p>SQLite con recuperacion via .meta.json</p></div></div>
          </div>
        </div>
      </section>

      <!-- MODULOS -->
      <section v-if="seccionActiva === 'modulos'" class="help-section">
        <div v-for="mod in modulos" :key="mod.nombre" class="help-card help-card--modulo">
          <div class="modulo-header">
            <span class="modulo-emoji">{{ mod.emoji }}</span>
            <div class="modulo-title-row">
              <h3>{{ mod.nombre }}</h3>
              <router-link :to="mod.ruta" class="modulo-link">Ir al modulo &rarr;</router-link>
            </div>
          </div>
          <p class="modulo-desc">{{ mod.descripcion }}</p>
          <div class="modulo-funcs">
            <h4>Funcionalidades:</h4>
            <ul><li v-for="func in mod.funcionalidades" :key="func">{{ func }}</li></ul>
          </div>
        </div>
      </section>

      <!-- ENTIDADES -->
      <section v-if="seccionActiva === 'entidades'" class="help-section">
        <div class="help-card"><h3>Modelos de Datos</h3><p>El sistema gestiona 11 tablas en SQLite.</p></div>
        <div v-for="ent in entidades" :key="ent.nombre" class="help-card help-card--entidad">
          <div class="entidad-header">
            <h3>{{ ent.nombre }}</h3>
            <span class="entidad-tabla">{{ ent.tabla }}</span>
            <span v-if="ent.prefijo !== '—'" class="entidad-prefijo">Prefijo: {{ ent.prefijo }}</span>
          </div>
          <p>{{ ent.descripcion }}</p>
          <div class="entidad-campos"><strong>Campos:</strong> <code>{{ ent.campos }}</code></div>
        </div>
      </section>

      <!-- ARCHIVOS -->
      <section v-if="seccionActiva === 'archivos'" class="help-section">
        <div class="help-card">
          <h3>Estructura de Archivos y Recuperacion</h3>
          <p>Estrategia de <strong>recuperacion en 3 capas</strong>: .meta.json, escaneo/recuperacion, backup/restore JSON.</p>
        </div>
        <div class="help-card">
          <h3>Convencion de Nombres</h3>
          <div class="conv-table">
            <div class="conv-row conv-row--header"><span>Tipo</span><span>Carpeta</span><span>Patron</span></div>
            <div v-for="arc in archivosEstructura" :key="arc.carpeta" class="conv-row">
              <span>{{ arc.descripcion }}</span><span><code>{{ arc.carpeta }}</code></span><span><code>{{ arc.patron }}</code></span>
            </div>
          </div>
        </div>
        <div class="help-card">
          <h3>Ejemplo .meta.json</h3>
          <pre class="meta-code">{{ metaJsonEjemplo }}</pre>
        </div>
        <div class="help-card">
          <h3>Capas de Recuperacion</h3>
          <div class="capas-grid">
            <div class="capa-card capa-card--done"><span class="capa-num">1</span><h4>Metadatos en Archivos</h4><p><strong>IMPLEMENTADO</strong></p></div>
            <div class="capa-card capa-card--done"><span class="capa-num">2</span><h4>Escaneo y Recuperacion</h4><p><strong>IMPLEMENTADO</strong></p></div>
            <div class="capa-card capa-card--done"><span class="capa-num">3</span><h4>Backup y Restore</h4><p><strong>IMPLEMENTADO</strong></p></div>
          </div>
        </div>
      </section>

      <!-- PENDIENTES -->
      <section v-if="seccionActiva === 'pendientes'" class="help-section">
        <div class="help-card help-card--warning">
          <h3>Funcionalidades Pendientes</h3>
          <p>Lista de funcionalidades aun no implementadas o parcialmente completadas.</p>
        </div>
        <div v-for="pend in pendientes" :key="pend.nombre" class="help-card help-card--pendiente">
          <div class="pendiente-header">
            <span class="pendiente-emoji">{{ pend.emoji }}</span>
            <div>
              <h3>{{ pend.nombre }}</h3>
              <span class="pendiente-prioridad" :class="'prioridad--' + pend.prioridad.toLowerCase()">{{ pend.prioridad }}</span>
            </div>
          </div>
          <p>{{ pend.descripcion }}</p>
          <div class="pendiente-estado"><strong>Estado:</strong> {{ pend.estado }}</div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }
.help-header { margin-bottom: 1.5rem; }
.help-header h2 { margin: 0 0 0.25rem 0; color: #1e293b; font-size: 1.5rem; }
.help-subtitle { margin: 0; color: #64748b; font-size: 0.95rem; }

.help-nav { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.help-nav-btn { display: flex; align-items: center; gap: 0.35rem; padding: 0.5rem 1rem; border: 2px solid #e2e8f0; border-radius: 8px; background: white; cursor: pointer; font-size: 0.88rem; font-weight: 600; color: #475569; transition: all 0.2s; }
.help-nav-btn:hover { border-color: #3b82f6; color: #2563eb; background: #eff6ff; }
.help-nav-btn--active { border-color: #3b82f6; background: #3b82f6; color: white; }
.help-nav-emoji { font-size: 1.1rem; }

.help-card { background: white; border-radius: 10px; padding: 1.25rem; box-shadow: 0 1px 6px rgba(15,23,42,0.07); border: 1px solid rgba(0,0,0,0.06); margin-bottom: 1rem; }
.help-card h3 { margin: 0 0 0.75rem 0; font-size: 1.05rem; font-weight: 700; color: #1e293b; }
.help-card p { margin: 0 0 0.5rem 0; color: #475569; line-height: 1.6; font-size: 0.9rem; }
.help-card code { background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.82rem; color: #7c3aed; }
.help-card--hero { border-left: 4px solid #3b82f6; background: linear-gradient(135deg, #eff6ff 0%, #ffffff 40%); }
.help-card--modulo { border-left: 4px solid #22c55e; }
.help-card--entidad { border-left: 4px solid #f59e0b; }
.help-card--warning { border-left: 4px solid #f59e0b; background: #fffbeb; }
.help-card--pendiente { border-left: 4px solid #ef4444; }

.modulo-header { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.75rem; }
.modulo-emoji { font-size: 1.6rem; flex-shrink: 0; }
.modulo-title-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.modulo-title-row h3 { margin: 0; }
.modulo-link { font-size: 0.82rem; font-weight: 600; color: #3b82f6; text-decoration: none; padding: 0.2rem 0.6rem; border-radius: 4px; background: #eff6ff; transition: background 0.2s; }
.modulo-link:hover { background: #dbeafe; text-decoration: underline; }
.modulo-funcs h4 { margin: 0 0 0.4rem 0; font-size: 0.85rem; color: #1e293b; }
.modulo-funcs ul { margin: 0; padding-left: 1.2rem; color: #475569; font-size: 0.85rem; line-height: 1.7; }

.entidad-header { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.entidad-header h3 { margin: 0; }
.entidad-tabla { font-size: 0.78rem; font-weight: 600; color: #6366f1; background: #eef2ff; padding: 0.15rem 0.5rem; border-radius: 4px; }
.entidad-prefijo { font-size: 0.78rem; font-weight: 600; color: #059669; background: #ecfdf5; padding: 0.15rem 0.5rem; border-radius: 4px; }
.entidad-campos { margin-top: 0.5rem; padding: 0.6rem 0.8rem; background: #f8fafc; border-radius: 6px; font-size: 0.82rem; }

.tech-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
@media (max-width: 900px) { .tech-grid { grid-template-columns: repeat(2, 1fr); } }
.tech-item { display: flex; align-items: flex-start; gap: 0.6rem; padding: 0.75rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.tech-icon { font-size: 1.4rem; flex-shrink: 0; }
.tech-item strong { display: block; font-size: 0.88rem; color: #1e293b; }
.tech-item p { margin: 0.15rem 0 0 0; font-size: 0.8rem; color: #64748b; }

.conv-table { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.conv-row { display: grid; grid-template-columns: 2fr 2fr 3fr; border-bottom: 1px solid #e2e8f0; font-size: 0.82rem; }
.conv-row:last-child { border-bottom: none; }
.conv-row > span { padding: 0.5rem 0.75rem; color: #475569; }
.conv-row--header > span { background: #f1f5f9; font-weight: 700; color: #334155; }

.meta-code { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 8px; font-size: 0.78rem; line-height: 1.5; overflow-x: auto; white-space: pre; font-family: 'Courier New', monospace; }

.capas-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
@media (max-width: 800px) { .capas-grid { grid-template-columns: 1fr; } }
.capa-card { padding: 1rem; border-radius: 8px; border: 1px solid; text-align: center; }
.capa-card h4 { margin: 0.5rem 0 0.25rem 0; font-size: 0.9rem; color: #1e293b; }
.capa-card p { font-size: 0.8rem; margin: 0.2rem 0; }
.capa-card--done { background: #f0fdf4; border-color: #86efac; }
.capa-num { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; background: #3b82f6; color: white; font-weight: 700; font-size: 0.85rem; }

.pendiente-header { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.5rem; }
.pendiente-emoji { font-size: 1.4rem; flex-shrink: 0; }
.pendiente-header h3 { margin: 0; display: inline; }
.pendiente-prioridad { display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; margin-left: 0.5rem; vertical-align: middle; }
.prioridad--alta { background: #fef2f2; color: #dc2626; }
.prioridad--media { background: #fffbeb; color: #d97706; }
.prioridad--baja { background: #f0fdf4; color: #16a34a; }
.pendiente-estado { margin-top: 0.5rem; padding: 0.4rem 0.6rem; background: #f8fafc; border-radius: 4px; font-size: 0.82rem; color: #475569; }

.help-section { animation: fadeIn 0.25s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
