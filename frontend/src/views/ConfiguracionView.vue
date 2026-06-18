<script setup>
import { ref, onMounted, computed } from 'vue'
import Navbar from '../components/Navbar.vue'
import apiClient from '../services/api.js'

// ─── Estado general ───
const tabActiva = ref('capa1')
const cargando = ref(false)
const toast = ref({ show: false, msg: '', type: 'info' })

// ─── Capa 1: Estados BD ───
const estadosBD = ref({})

// ─── Capa 2: Escaneo ───
const escaneoResultado = ref(null)
const escaneando = ref(false)
const recuperando = ref(false)
const recuperacionResultado = ref(null)

// ─── Capa 3: Backup/Restore ───
const backupData = ref(null)
const restaurando = ref(false)
const archivoRestore = ref(null)
const fileInput = ref(null)

// ─── Configuración del Sistema (editable) ───
const configOriginal = ref({})
const configEdit = ref({
  empresa: { nombre: '' },
  directorios: {},
  sistema: {}
})
const guardandoConfig = ref(false)
const moviendoArchivos = ref(false)
const movimientoResultado = ref(null)
const uploadsBaseAnterior = ref('')

// ─── Tabs ───
const tabs = [
  { id: 'capa1', label: 'Capa 1 — BD', icon: '💾' },
  { id: 'capa2', label: 'Capa 2 — Escaneo', icon: '🔍' },
  { id: 'capa3', label: 'Capa 3 — Backup', icon: '📦' },
  { id: 'config', label: 'Configuración', icon: '🛠️' }
]

// ─── Helpers ───
function showToast(msg, type = 'info') {
  toast.value = { show: true, msg, type }
  setTimeout(() => { toast.value.show = false }, 4000)
}

function formatBytes(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i]
}

// ─── Verificar si uploads_base cambió ───
const uploadsBaseCambio = computed(() => {
  return configEdit.value.directorios?.uploads_base !== uploadsBaseAnterior.value
})

// ─── Sub-directorios (fijos, relativos a uploads_base) ───
const subdirectorios = computed(() => {
  const dirs = configEdit.value.directorios || {}
  const result = {}
  for (const [key, value] of Object.entries(dirs)) {
    if (key !== 'uploads_base') {
      result[key] = value
    }
  }
  return result
})

// ─── Cargar datos iniciales ───
onMounted(async () => {
  await Promise.all([
    cargarEstadosBD(),
    cargarConfig()
  ])
})

async function cargarEstadosBD() {
  try {
    const res = await apiClient.get('/configuracion/estados-bd')
    estadosBD.value = res.data
  } catch (e) {
    console.error('Error cargando estados BD:', e)
  }
}

async function cargarConfig() {
  try {
    const res = await apiClient.get('/configuracion/')
    configOriginal.value = JSON.parse(JSON.stringify(res.data))
    configEdit.value = JSON.parse(JSON.stringify(res.data))
    uploadsBaseAnterior.value = res.data.directorios?.uploads_base || 'uploads'
  } catch (e) {
    console.error('Error cargando config:', e)
  }
}

// ─── Capa 2: Escanear ───
async function escanear() {
  escaneando.value = true
  try {
    const res = await apiClient.get('/configuracion/escanear')
    escaneoResultado.value = res.data
    showToast('Escaneo completado', 'success')
  } catch (e) {
    showToast('Error al escanear: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    escaneando.value = false
  }
}

async function recuperar() {
  if (!confirm('¿Recuperar registros huérfanos y sincronizar imágenes faltantes desde los archivos .meta.json y .txt de OT?')) return
  recuperando.value = true
  try {
    const res = await apiClient.post('/configuracion/recuperar')
    recuperacionResultado.value = res.data
    const r = res.data.recuperados
    const partes = []
    if (r.equipos) partes.push(`${r.equipos} equipos`)
    if (r.repuestos) partes.push(`${r.repuestos} repuestos`)
    if (r.herramientas) partes.push(`${r.herramientas} herramientas`)
    if (r.ordenes) partes.push(`${r.ordenes} OTs`)
    if (r.documentos) partes.push(`${r.documentos} documentos`)
    if (r.imagenes_sincronizadas) partes.push(`${r.imagenes_sincronizadas} imágenes sincronizadas`)
    const msg = partes.length ? `Recuperación: ${partes.join(', ')}.` : 'No se encontró nada por recuperar.'
    showToast(msg, partes.length ? 'success' : 'info')
    await cargarEstadosBD()
    // Volver a escanear para mostrar el estado actualizado
    await escanear()
  } catch (e) {
    showToast('Error al recuperar: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    recuperando.value = false
  }
}

// ─── Capa 3: Backup ───
async function generarBackup() {
  cargando.value = true
  try {
    const res = await apiClient.get('/configuracion/backup')
    backupData.value = res.data
    showToast('Backup generado correctamente', 'success')
  } catch (e) {
    showToast('Error al generar backup: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    cargando.value = false
  }
}

function descargarBackup() {
  if (!backupData.value) return
  const blob = new Blob([JSON.stringify(backupData.value, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `cmms_bioai_backup_${new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)}.json`
  a.click()
  URL.revokeObjectURL(url)
}

async function restaurarDesdeJSON() {
  const backup = backupData.value
  if (!backup) {
    showToast('Primero genera un backup', 'error')
    return
  }
  if (!confirm('⚠️ ADVERTENCIA: Esto ELIMINARÁ todos los datos actuales y los reemplazará con el backup. ¿Está seguro?')) return
  if (!confirm('¿Seguro? Esta operación NO se puede deshacer.')) return

  restaurando.value = true
  try {
    const res = await apiClient.post('/configuracion/restore', backup)
    const total = res.data.total_registros
    const errores = res.data.errores?.length || 0
    const configOk = res.data.config_restaurada
    let msg = `Restauración completada: ${total} registros restaurados`
    if (configOk) msg += ' + configuración restaurada'
    if (errores > 0) {
      showToast(`${msg} con ${errores} errores.`, 'warning')
    } else {
      showToast(msg, 'success')
    }
    await cargarEstadosBD()
    await cargarConfig()
  } catch (e) {
    showToast('Error al restaurar: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    restaurando.value = false
  }
}

async function subirRestaurar() {
  if (!archivoRestore.value) {
    showToast('Selecciona un archivo JSON de backup', 'error')
    return
  }
  if (!confirm('⚠️ ADVERTENCIA: Esto ELIMINARÁ todos los datos actuales. ¿Está seguro?')) return

  restaurando.value = true
  try {
    const formData = new FormData()
    formData.append('archivo', archivoRestore.value)
    const res = await apiClient.post('/configuracion/restore/subir', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    const total = res.data.total_registros
    const configOk = res.data.config_restaurada
    let msg = `Restauración completada: ${total} registros`
    if (configOk) msg += ' + configuración restaurada'
    showToast(msg, 'success')
    await cargarEstadosBD()
    await cargarConfig()
    archivoRestore.value = null
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    showToast('Error al restaurar: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    restaurando.value = false
  }
}

// ─── Configuración editable ───
async function guardarConfig() {
  guardandoConfig.value = true
  movimientoResultado.value = null
  try {
    const payload = {
      empresa: configEdit.value.empresa,
      directorios: configEdit.value.directorios
    }
    const res = await apiClient.put('/configuracion/', payload)
    configOriginal.value = JSON.parse(JSON.stringify(res.data.config))
    showToast('Configuración guardada correctamente', 'success')
  } catch (e) {
    showToast('Error al guardar: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    guardandoConfig.value = false
  }
}

async function moverArchivos() {
  if (!confirm(`¿Mover todos los archivos de "${uploadsBaseAnterior.value}" a "${configEdit.value.directorios?.uploads_base}"?\n\nEsta operación copiará los archivos y luego eliminará los originales.`)) return

  moviendoArchivos.value = true
  movimientoResultado.value = null
  try {
    const res = await apiClient.post('/configuracion/mover-archivos', {
      origen: uploadsBaseAnterior.value,
      destino: configEdit.value.directorios?.uploads_base
    })
    movimientoResultado.value = res.data
    uploadsBaseAnterior.value = configEdit.value.directorios?.uploads_base
    showToast(`Archivos movidos: ${res.data.archivos_movidos} archivos`, 'success')
  } catch (e) {
    showToast('Error al mover: ' + (e.response?.data?.detail || e.message), 'error')
  } finally {
    moviendoArchivos.value = false
  }
}

function resetConfig() {
  configEdit.value = JSON.parse(JSON.stringify(configOriginal.value))
  showToast('Configuración revertida al último guardado', 'info')
}

// ─── Labels para directorios ───
const dirLabels = {
  uploads_base: 'Carpeta base (uploads)',
  equipos_imagenes: 'Imágenes de Equipos',
  equipos_documentos: 'Documentos de Equipos',
  ot_documentos: 'Documentos de OT',
  repuestos_imagenes: 'Imágenes de Repuestos',
  repuestos_documentos: 'Documentos de Repuestos',
  herramientas_imagenes: 'Imágenes de Herramientas',
  herramientas_documentos: 'Documentos de Herramientas',
  reportes: 'Reportes'
}</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <h2>Configuración del Sistema</h2>

      <!-- Toast -->
      <div v-if="toast.show" class="toast" :class="'toast--' + toast.type">
        {{ toast.msg }}
      </div>

      <!-- Tabs -->
      <nav class="config-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="config-tab"
          :class="{ 'config-tab--active': tabActiva === tab.id }"
          @click="tabActiva = tab.id"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          <span class="tab-label">{{ tab.label }}</span>
        </button>
      </nav>

      <!-- ═══════════ CAPA 1: Estados BD ═══════════ -->
      <section v-if="tabActiva === 'capa1'" class="config-section">
        <div class="config-card">
          <h3>Capa 1 — Metadatos en Archivos</h3>
          <p>Los archivos <code>.meta.json</code> se crean automáticamente junto a cada imagen o documento subido. Si la base de datos se pierde, los datos esenciales pueden reconstruirse escaneando estos archivos.</p>
          <div class="status-badge status-badge--ok">ACTIVO</div>
        </div>

        <div class="config-card">
          <h3>Estado de la Base de Datos</h3>
          <div class="bd-grid">
            <div v-for="(count, tabla) in estadosBD" :key="tabla" class="bd-item">
              <span class="bd-count">{{ count }}</span>
              <span class="bd-label">{{ tabla.replace(/_/g, ' ') }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- ═══════════ CAPA 2: Escaneo ═══════════ -->
      <section v-if="tabActiva === 'capa2'" class="config-section">
        <div class="config-card">
          <h3>Capa 2 — Escaneo y Recuperación</h3>
          <p>Escanea los archivos <code>.meta.json</code> y los <code>.txt</code> de referencia de OTs, y los compara con la BD. Detecta:</p>
          <ul class="capa2-features">
            <li><strong>Huérfanos:</strong> registros en archivos pero no en BD (se pueden recuperar).</li>
            <li><strong>Imágenes faltantes:</strong> registros en BD cuyo <code>imagen_ruta</code> está vacío pero el <code>.meta.json</code> lo tiene (se sincronizan al recuperar).</li>
            <li><strong>OTs huérfanas:</strong> Órdenes de Trabajo que existen como <code>.txt</code> en <code>uploads/OT/</code> pero no en la BD.</li>
            <li><strong>Documentos huérfanos:</strong> Documentos en <code>.meta.json</code> de carpetas <code>DOC/</code> y <code>OT/OTxxxx/</code> que no están en BD.</li>
          </ul>
          <div class="btn-row">
            <button class="btn btn--primary" @click="escanear" :disabled="escaneando">
              {{ escaneando ? 'Escaneando...' : '🔍 Escanear .meta.json' }}
            </button>
            <button
              v-if="escaneoResultado && (escaneoResultado.resumen.total_huerfanos > 0 || escaneoResultado.resumen.total_imagenes_faltantes > 0)"
              class="btn btn--warning"
              @click="recuperar"
              :disabled="recuperando"
            >
              {{ recuperando ? 'Recuperando...' : '🔄 Recuperar / Sincronizar' }}
            </button>
          </div>
        </div>

        <!-- Resultado del escaneo -->
        <div v-if="escaneoResultado" class="config-card">
          <h3>Resultado del Escaneo</h3>
          <div class="scan-summary">
            <div class="scan-stat">
              <span class="scan-num">{{ escaneoResultado.resumen.total_en_archivos }}</span>
              <span class="scan-label">En archivos</span>
            </div>
            <div class="scan-stat">
              <span class="scan-num">{{ escaneoResultado.resumen.total_en_bd }}</span>
              <span class="scan-label">En BD</span>
            </div>
            <div class="scan-stat scan-stat--alert" v-if="escaneoResultado.resumen.total_huerfanos > 0">
              <span class="scan-num">{{ escaneoResultado.resumen.total_huerfanos }}</span>
              <span class="scan-label">Huérfanos</span>
            </div>
            <div class="scan-stat scan-stat--ok" v-else>
              <span class="scan-num">0</span>
              <span class="scan-label">Huérfanos</span>
            </div>
            <div class="scan-stat scan-stat--warn" v-if="escaneoResultado.resumen.total_imagenes_faltantes > 0">
              <span class="scan-num">{{ escaneoResultado.resumen.total_imagenes_faltantes }}</span>
              <span class="scan-label">Imágenes faltantes</span>
            </div>
          </div>

          <!-- Detalle por tipo -->
          <div v-for="(data, tipo) in escaneoResultado.detalle" :key="tipo" class="scan-detail">
            <h4>{{ tipo }}</h4>
            <span>En BD: {{ data.en_bd }} | En archivos: {{ data.en_archivos.length }} | Huérfanos: {{ data.huerfanos.length }}<span v-if="data.imagenes_faltantes"> | Imágenes faltantes: {{ data.imagenes_faltantes.length }}</span></span>

            <ul v-if="data.huerfanos.length > 0" class="huerfanos-list">
              <li v-for="h in data.huerfanos" :key="h.id">
                <strong>ID {{ h.id }}</strong> — {{ h.nombre || h.titulo }} <code>{{ h.carpeta }}</code>
              </li>
            </ul>

            <ul v-if="data.imagenes_faltantes && data.imagenes_faltantes.length > 0" class="imagenes-faltantes-list">
              <li v-for="img in data.imagenes_faltantes" :key="img.id">
                <strong>ID {{ img.id }}</strong> — {{ img.nombre }}: el <code>.meta.json</code> tiene <code>{{ img.imagen_ruta_meta }}</code> pero la BD tiene <code>{{ img.imagen_ruta_bd || 'NULL' }}</code>
              </li>
            </ul>
          </div>
        </div>

        <!-- Resultado de la recuperación -->
        <div v-if="recuperacionResultado" class="config-card config-card--info">
          <h3>Resultado de la Recuperación</h3>
          <div class="recuperacion-grid">
            <div class="rec-stat" v-if="recuperacionResultado.recuperados.equipos > 0">
              <span class="rec-num">{{ recuperacionResultado.recuperados.equipos }}</span>
              <span class="rec-label">Equipos creados</span>
            </div>
            <div class="rec-stat" v-if="recuperacionResultado.recuperados.repuestos > 0">
              <span class="rec-num">{{ recuperacionResultado.recuperados.repuestos }}</span>
              <span class="rec-label">Repuestos creados</span>
            </div>
            <div class="rec-stat" v-if="recuperacionResultado.recuperados.herramientas > 0">
              <span class="rec-num">{{ recuperacionResultado.recuperados.herramientas }}</span>
              <span class="rec-label">Herramientas creadas</span>
            </div>
            <div class="rec-stat" v-if="recuperacionResultado.recuperados.ordenes > 0">
              <span class="rec-num">{{ recuperacionResultado.recuperados.ordenes }}</span>
              <span class="rec-label">OTs creadas</span>
            </div>
            <div class="rec-stat" v-if="recuperacionResultado.recuperados.documentos > 0">
              <span class="rec-num">{{ recuperacionResultado.recuperados.documentos }}</span>
              <span class="rec-label">Documentos creados</span>
            </div>
            <div class="rec-stat rec-stat--sync" v-if="recuperacionResultado.recuperados.imagenes_sincronizadas > 0">
              <span class="rec-num">{{ recuperacionResultado.recuperados.imagenes_sincronizadas }}</span>
              <span class="rec-label">Imágenes sincronizadas</span>
            </div>
          </div>

          <p v-if="recuperacionResultado.errores.length > 0" class="rec-errores">
            <strong>Errores ({{ recuperacionResultado.errores.length }}):</strong>
          </p>
          <ul v-if="recuperacionResultado.errores.length > 0" class="errores-list">
            <li v-for="(err, idx) in recuperacionResultado.errores" :key="idx">{{ err }}</li>
          </ul>

          <p v-if="recuperacionResultado.total_recuperados === 0 && recuperacionResultado.errores.length === 0" class="rec-noop">
            No se encontraron registros por recuperar ni imágenes por sincronizar.
          </p>
        </div>
      </section>

      <!-- ═══════════ CAPA 3: Backup/Restore ═══════════ -->
      <section v-if="tabActiva === 'capa3'" class="config-section">
        <div class="config-card">
          <h3>Capa 3 — Backup y Restore</h3>
          <p>Exporta toda la base de datos <strong>y la configuración del sistema</strong> (nombre, directorios, parámetros) como un archivo JSON descargable. Restaurar reemplaza todos los datos existentes y restaura la configuración guardada.</p>
          <div class="btn-row">
            <button class="btn btn--primary" @click="generarBackup" :disabled="cargando">
              {{ cargando ? 'Generando...' : '📦 Generar Backup' }}
            </button>
            <button v-if="backupData" class="btn btn--secondary" @click="descargarBackup">
              ⬇️ Descargar JSON
            </button>
          </div>
        </div>

        <!-- Info del backup generado -->
        <div v-if="backupData" class="config-card config-card--info">
          <h3>Backup Generado</h3>
          <p><strong>Fecha:</strong> {{ backupData.metadatos.fecha_backup }}</p>
          <p v-if="backupData.configuracion"><strong>Incluye configuración:</strong> nombre, directorios y parámetros del sistema</p>
          <p><strong>Registros:</strong></p>
          <div class="backup-totals">
            <span v-for="(total, tabla) in backupData.metadatos.totales" :key="tabla" class="backup-tag">
              {{ tabla }}: {{ total }}
            </span>
          </div>
          <div class="btn-row" style="margin-top: 1rem;">
            <button class="btn btn--danger" @click="restaurarDesdeJSON" :disabled="restaurando">
              {{ restaurando ? 'Restaurando...' : '⚠️ Restaurar este backup' }}
            </button>
          </div>
        </div>

        <!-- Subir backup -->
        <div class="config-card">
          <h3>Restaurar desde Archivo</h3>
          <p>Sube un archivo JSON de backup previamente descargado.</p>
          <div class="upload-row">
            <input
              ref="fileInput"
              type="file"
              accept=".json"
              @change="archivoRestore = $event.target.files[0]"
              class="file-input"
            />
            <button
              class="btn btn--warning"
              @click="subirRestaurar"
              :disabled="restaurando || !archivoRestore"
            >
              {{ restaurando ? 'Restaurando...' : '📤 Subir y Restaurar' }}
            </button>
          </div>
        </div>
      </section>

      <!-- ═══════════ CONFIGURACIÓN EDITABLE ═══════════ -->
      <section v-if="tabActiva === 'config'" class="config-section">

        <!-- Empresa -->
        <div class="config-card config-card--edit">
          <h3>🏥 Nombre del Sistema</h3>
          <p>El nombre se muestra en la barra de navegación y en el título del sistema. Se respalda junto con el backup y se restaura automáticamente.</p>
          <div class="form-group">
            <label>Nombre del Sistema</label>
            <input
              v-model="configEdit.empresa.nombre"
              type="text"
              class="form-input"
              placeholder="CMMS-BioAI"
            />
            <small>Este nombre aparecerá en la barra superior de navegación de todas las páginas.</small>
          </div>
        </div>

        <!-- Directorios: solo uploads_base editable -->
        <div class="config-card config-card--edit">
          <h3>📁 Carpeta Base de Almacenamiento</h3>
          <p>Todos los archivos (imágenes, documentos, reportes) se guardan dentro de esta carpeta. Las sub-carpetas (<code>EQUIPOS</code>, <code>REPUESTOS</code>, etc.) se crean automáticamente dentro de ella.</p>

          <div class="form-group form-group--highlight">
            <label>
              Carpeta base (uploads_base)
              <span class="label-badge">EDITABLE</span>
            </label>
            <input
              v-model="configEdit.directorios.uploads_base"
              type="text"
              class="form-input"
              placeholder="uploads"
            />
            <small>
              ⚡ Puede ser relativa a <code>backend/</code> (ej: <code>uploads</code>) o absoluta
              (ej: <code>D:/uploads</code> en Windows o <code>/mnt/datos/uploads</code> en Linux).<br/>
              Al cambiar esta ruta, <strong>todas las sub-carpetas se reubican automáticamente</strong>
              — no es necesario editarlas individualmente.
            </small>
          </div>

          <!-- Preview de estructura resultante -->
          <div class="structure-preview">
            <h4>Estructura resultante:</h4>
            <div class="tree">
              <div class="tree-item tree-item--base">
                📂 {{ configEdit.directorios.uploads_base || 'uploads' }}/
              </div>
              <div class="tree-item" v-for="(subdir, key) in subdirectorios" :key="key">
                ├── 📁 {{ subdir }}/
                <span class="tree-label">{{ dirLabels[key] || key }}</span>
              </div>
            </div>
          </div>

          <!-- Aviso si uploads_base cambió -->
          <div v-if="uploadsBaseCambio" class="move-notice">
            <div class="move-notice-icon">⚠️</div>
            <div class="move-notice-text">
              <strong>Ha cambiado la carpeta base de uploads.</strong><br/>
              Antes: <code>{{ uploadsBaseAnterior }}</code> → Ahora: <code>{{ configEdit.directorios.uploads_base }}</code><br/>
              <span>Pasos: 1) Guarde la configuración → 2) Mueva los archivos → 3) Reinicie el servidor.</span>
            </div>
          </div>
        </div>

        <!-- Botones de acción -->
        <div class="config-card config-card--actions">
          <div class="btn-row">
            <button class="btn btn--primary" @click="guardarConfig" :disabled="guardandoConfig">
              {{ guardandoConfig ? 'Guardando...' : '💾 Guardar Configuración' }}
            </button>
            <button class="btn btn--secondary" @click="resetConfig">
              ↩️ Revertir cambios
            </button>
            <button
              v-if="uploadsBaseCambio"
              class="btn btn--warning"
              @click="moverArchivos"
              :disabled="moviendoArchivos"
            >
              {{ moviendoArchivos ? 'Moviendo...' : '🚚 Mover archivos a nueva ubicación' }}
            </button>
          </div>

          <!-- Resultado del movimiento -->
          <div v-if="movimientoResultado" class="move-result" :class="movimientoResultado.origen_mantenido ? 'move-result--warn' : 'move-result--ok'">
            <p>✅ {{ movimientoResultado.mensaje }}</p>
            <p>Archivos movidos: <strong>{{ movimientoResultado.archivos_movidos }}</strong> ({{ formatBytes(movimientoResultado.bytes_movidos) }})</p>
            <p v-if="movimientoResultado.origen_mantenido">⚠️ La carpeta original no se pudo eliminar automáticamente. Puede eliminarla manualmente.</p>
          </div>
        </div>

        <!-- Sistema (solo lectura) -->
        <div class="config-card config-card--readonly">
          <h3>🔒 Parámetros del Sistema <span class="readonly-badge">SOLO LECTURA</span></h3>
          <p>Estos parámetros son específicos para el mercado boliviano y no se modifican por ahora.</p>
          <div class="readonly-grid">
            <div class="readonly-item">
              <span class="readonly-label">Idioma</span>
              <span class="readonly-value">{{ configEdit.sistema?.idioma || 'es' }}</span>
            </div>
            <div class="readonly-item">
              <span class="readonly-label">Zona Horaria</span>
              <span class="readonly-value">{{ configEdit.sistema?.zona_horaria || 'America/La_Paz' }}</span>
            </div>
            <div class="readonly-item">
              <span class="readonly-label">Moneda</span>
              <span class="readonly-value">{{ configEdit.sistema?.moneda || 'BOB' }}</span>
            </div>
            <div class="readonly-item">
              <span class="readonly-label">Prefijo Equipos</span>
              <span class="readonly-value">{{ configEdit.sistema?.prefijo_equipos || 'E' }}</span>
            </div>
            <div class="readonly-item">
              <span class="readonly-label">Prefijo Órdenes</span>
              <span class="readonly-value">{{ configEdit.sistema?.prefijo_ordenes || 'OT' }}</span>
            </div>
            <div class="readonly-item">
              <span class="readonly-label">Prefijo Repuestos</span>
              <span class="readonly-value">{{ configEdit.sistema?.prefijo_inventario || 'R' }}</span>
            </div>
          </div>
        </div>
      </section>

    </main>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }
.content h2 { color: #1e293b; margin: 0 0 1.5rem 0; font-size: 1.5rem; }

/* === Toast === */
.toast {
  position: fixed; top: 1.5rem; right: 1.5rem;
  padding: 0.85rem 1.5rem; border-radius: 8px;
  font-weight: 600; font-size: 0.9rem;
  z-index: 9999; animation: slideIn 0.3s ease;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.toast--info { background: #dbeafe; color: #1e40af; }
.toast--success { background: #dcfce7; color: #166534; }
.toast--error { background: #fee2e2; color: #991b1b; }
.toast--warning { background: #fef3c7; color: #92400e; }
@keyframes slideIn { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }

/* === Tabs === */
.config-tabs {
  display: flex; gap: 0.5rem; margin-bottom: 1.5rem; flex-wrap: wrap;
}
.config-tab {
  display: flex; align-items: center; gap: 0.4rem;
  padding: 0.6rem 1.1rem; border: 2px solid #e2e8f0;
  border-radius: 8px; background: white; cursor: pointer;
  font-size: 0.88rem; font-weight: 600; color: #475569;
  transition: all 0.2s ease;
}
.config-tab:hover { border-color: #3b82f6; color: #2563eb; background: #eff6ff; }
.config-tab--active { border-color: #3b82f6; background: #3b82f6; color: white; }
.config-tab--active:hover { background: #2563eb; color: white; }
.tab-icon { font-size: 1.1rem; }

/* === Cards === */
.config-card {
  background: white; border-radius: 10px; padding: 1.25rem;
  box-shadow: 0 1px 6px rgba(15,23,42,0.07); border: 1px solid rgba(0,0,0,0.06);
  margin-bottom: 1rem;
}
.config-card h3 {
  margin: 0 0 0.75rem 0; font-size: 1.05rem; font-weight: 700; color: #1e293b;
  display: flex; align-items: center; gap: 0.5rem;
}
.config-card p { margin: 0 0 0.5rem 0; color: #475569; line-height: 1.6; font-size: 0.9rem; }
.config-card code { background: #f1f5f9; padding: 0.15rem 0.4rem; border-radius: 4px; font-size: 0.82rem; color: #7c3aed; }
.config-card--info { border-left: 4px solid #3b82f6; }
.config-card--edit { border-left: 4px solid #22c55e; }
.config-card--readonly { border-left: 4px solid #94a3b8; background: #f8fafc; }
.config-card--actions { border-left: 4px solid #f59e0b; }

/* === Status Badge === */
.status-badge {
  display: inline-block; padding: 0.25rem 0.75rem; border-radius: 20px;
  font-size: 0.78rem; font-weight: 700; letter-spacing: 0.05em;
}
.status-badge--ok { background: #dcfce7; color: #166534; }

/* === BD Grid === */
.bd-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.75rem; margin-top: 0.75rem;
}
.bd-item {
  background: #f8fafc; border-radius: 8px; padding: 0.75rem;
  text-align: center; border: 1px solid #e2e8f0;
}
.bd-count { display: block; font-size: 1.8rem; font-weight: 700; color: #1e293b; }
.bd-label { display: block; font-size: 0.78rem; color: #64748b; text-transform: capitalize; margin-top: 0.25rem; }

/* === Buttons === */
.btn-row { display: flex; gap: 0.75rem; flex-wrap: wrap; margin-top: 0.75rem; }
.btn {
  padding: 0.55rem 1.2rem; border-radius: 6px; border: none;
  font-weight: 600; font-size: 0.88rem; cursor: pointer;
  transition: all 0.2s; display: inline-flex; align-items: center; gap: 0.35rem;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn--primary { background: #3b82f6; color: white; }
.btn--primary:hover:not(:disabled) { background: #2563eb; }
.btn--secondary { background: #64748b; color: white; }
.btn--secondary:hover:not(:disabled) { background: #475569; }
.btn--warning { background: #f59e0b; color: white; }
.btn--warning:hover:not(:disabled) { background: #d97706; }
.btn--danger { background: #ef4444; color: white; }
.btn--danger:hover:not(:disabled) { background: #dc2626; }

/* === Scan Summary === */
.scan-summary { display: flex; gap: 1.5rem; margin: 1rem 0; flex-wrap: wrap; }
.scan-stat { text-align: center; padding: 0.75rem 1.5rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.scan-num { display: block; font-size: 1.8rem; font-weight: 700; color: #1e293b; }
.scan-label { display: block; font-size: 0.78rem; color: #64748b; margin-top: 0.2rem; }
.scan-stat--alert { border-color: #fca5a5; background: #fef2f2; }
.scan-stat--alert .scan-num { color: #dc2626; }
.scan-stat--ok { border-color: #86efac; background: #f0fdf4; }
.scan-stat--ok .scan-num { color: #16a34a; }
.scan-stat--warn { border-color: #fde047; background: #fefce8; }
.scan-stat--warn .scan-num { color: #ca8a04; }

.scan-detail { margin-top: 0.75rem; padding: 0.75rem; background: #f8fafc; border-radius: 6px; }
.scan-detail h4 { margin: 0 0 0.35rem 0; font-size: 0.9rem; color: #1e293b; text-transform: capitalize; }
.scan-detail span { font-size: 0.82rem; color: #64748b; }
.huerfanos-list { margin: 0.35rem 0 0 0; padding-left: 1.2rem; font-size: 0.82rem; color: #dc2626; }
.huerfanos-list li { margin: 0.2rem 0; }
.huerfanos-list code { background: #fef2f2; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.78rem; color: #991b1b; }

.imagenes-faltantes-list { margin: 0.35rem 0 0 0; padding-left: 1.2rem; font-size: 0.78rem; color: #ca8a04; }
.imagenes-faltantes-list li { margin: 0.25rem 0; }
.imagenes-faltantes-list code { background: #fefce8; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.74rem; color: #854d0e; }

/* Features list (capa 2) */
.capa2-features { margin: 0.5rem 0; padding-left: 1.5rem; font-size: 0.85rem; color: #475569; line-height: 1.7; }
.capa2-features li { margin: 0.25rem 0; }
.capa2-features strong { color: #1e293b; }
.capa2-features code { background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.78rem; color: #7c3aed; }

/* Resultado de recuperación */
.recuperacion-grid { display: flex; flex-wrap: wrap; gap: 0.75rem; margin: 0.5rem 0; }
.rec-stat { text-align: center; padding: 0.65rem 1.1rem; background: #ecfdf5; border: 1px solid #86efac; border-radius: 8px; }
.rec-stat .rec-num { display: block; font-size: 1.5rem; font-weight: 700; color: #16a34a; }
.rec-stat .rec-label { display: block; font-size: 0.75rem; color: #15803d; margin-top: 0.15rem; }
.rec-stat--sync { background: #eff6ff; border-color: #93c5fd; }
.rec-stat--sync .rec-num { color: #2563eb; }
.rec-stat--sync .rec-label { color: #1d4ed8; }

.rec-errores { margin-top: 0.75rem; font-size: 0.88rem; color: #dc2626; }
.errores-list { margin: 0.35rem 0 0 0; padding-left: 1.2rem; font-size: 0.78rem; color: #991b1b; max-height: 200px; overflow-y: auto; }
.rec-noop { font-size: 0.88rem; color: #64748b; font-style: italic; }

/* === Backup === */
.backup-totals { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
.backup-tag {
  display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
  background: #eff6ff; color: #1e40af; font-size: 0.78rem; font-weight: 600;
}
.upload-row { display: flex; gap: 0.75rem; align-items: center; margin-top: 0.75rem; flex-wrap: wrap; }
.file-input { font-size: 0.88rem; }

/* === Form === */
.form-group { margin-bottom: 1rem; }
.form-group label {
  display: block; font-weight: 600; font-size: 0.88rem; color: #334155;
  margin-bottom: 0.35rem;
}
.form-input {
  width: 100%; padding: 0.55rem 0.75rem; border: 2px solid #e2e8f0;
  border-radius: 6px; font-size: 0.9rem; transition: border-color 0.2s;
  box-sizing: border-box;
}
.form-input:focus { outline: none; border-color: #3b82f6; }
.form-group small { display: block; margin-top: 0.25rem; font-size: 0.78rem; color: #64748b; }
.form-group--highlight .form-input { border-color: #f59e0b; background: #fffbeb; }
.form-group--highlight .form-input:focus { border-color: #d97706; }
.label-badge {
  display: inline-block; padding: 0.1rem 0.4rem; border-radius: 3px;
  background: #f59e0b; color: white; font-size: 0.68rem; font-weight: 700;
  vertical-align: middle; margin-left: 0.35rem;
}

/* === Move Notice === */
.move-notice {
  display: flex; gap: 0.75rem; align-items: flex-start;
  padding: 1rem; border-radius: 8px; background: #fef3c7;
  border: 1px solid #fde68a; margin-top: 0.75rem;
}
.move-notice-icon { font-size: 1.4rem; flex-shrink: 0; }
.move-notice-text { font-size: 0.88rem; color: #92400e; line-height: 1.5; }
.move-notice-text code { background: #fde68a; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.82rem; }

/* === Move Result === */
.move-result {
  margin-top: 1rem; padding: 1rem; border-radius: 8px;
  font-size: 0.88rem; line-height: 1.6;
}
.move-result--ok { background: #dcfce7; border: 1px solid #86efac; color: #166534; }
.move-result--warn { background: #fef3c7; border: 1px solid #fde68a; color: #92400e; }
.move-result p { margin: 0.25rem 0; }

/* === Readonly === */
.readonly-badge {
  display: inline-block; padding: 0.15rem 0.5rem; border-radius: 3px;
  background: #94a3b8; color: white; font-size: 0.68rem; font-weight: 700;
  letter-spacing: 0.05em; vertical-align: middle;
}
.readonly-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.75rem; margin-top: 0.75rem;
}
.readonly-item {
  background: #f1f5f9; padding: 0.65rem 0.85rem; border-radius: 6px;
  border: 1px solid #e2e8f0;
}
.readonly-label { display: block; font-size: 0.75rem; color: #64748b; font-weight: 600; text-transform: uppercase; }
.readonly-value { display: block; font-size: 1rem; color: #1e293b; font-weight: 700; margin-top: 0.15rem; }

/* === Structure Preview Tree === */
.structure-preview {
  margin-top: 1rem; padding: 1rem; background: #f8fafc;
  border-radius: 8px; border: 1px solid #e2e8f0;
}
.structure-preview h4 {
  margin: 0 0 0.75rem 0; font-size: 0.88rem; font-weight: 700; color: #475569;
}
.tree-item {
  font-family: 'Courier New', monospace; font-size: 0.85rem; color: #334155;
  padding: 0.2rem 0; line-height: 1.6;
}
.tree-item--base {
  font-weight: 700; color: #1e293b; font-size: 0.92rem; margin-bottom: 0.15rem;
}
.tree-label {
  font-family: inherit; font-size: 0.78rem; color: #64748b;
  margin-left: 0.5rem; font-style: italic;
}
</style>
