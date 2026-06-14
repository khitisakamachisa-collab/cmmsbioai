<script setup>
import { ref, onMounted } from 'vue'
import Navbar from '../components/Navbar.vue'
import apiClient from '../services/api.js'

// --- Estado general ---
const loading = ref(false)
const mensaje = ref(null)  // { tipo: 'success'|'error'|'info', texto: '' }

// --- Capa 1: Metadatos (informativo) ---
const estadosBD = ref(null)

// --- Capa 2: Escaneo y Recuperación ---
const escaneoResultado = ref(null)
const recuperacionResultado = ref(null)
const escaneando = ref(false)
const recuperando = ref(false)

// --- Capa 3: Backup y Restore ---
const backupLoading = ref(false)
const restoreLoading = ref(false)
const archivoBackup = ref(null)
const restoreResultado = ref(null)

// --- Configuración ---
const config = ref(null)
const editandoConfig = ref(false)

// --- Funciones ---

const mostrarMensaje = (tipo, texto) => {
  mensaje.value = { tipo, texto }
  setTimeout(() => { mensaje.value = null }, 5000)
}

const cargarEstadosBD = async () => {
  try {
    const res = await apiClient.get('/configuracion/estados-bd')
    estadosBD.value = res.data
  } catch (error) {
    console.error('Error cargando estados BD', error)
  }
}

const cargarConfig = async () => {
  try {
    const res = await apiClient.get('/configuracion/')
    config.value = res.data
  } catch (error) {
    console.error('Error cargando configuración', error)
  }
}

const escanear = async () => {
  escaneando.value = true
  escaneoResultado.value = null
  try {
    const res = await apiClient.get('/configuracion/escanear')
    escaneoResultado.value = res.data
    if (res.data.resumen.total_huerfanos === 0) {
      mostrarMensaje('success', 'Escaneo completado: no se encontraron registros huérfanos.')
    } else {
      mostrarMensaje('info', `Escaneo completado: ${res.data.resumen.total_huerfanos} registro(s) huérfano(s) encontrado(s).`)
    }
  } catch (error) {
    mostrarMensaje('error', 'Error al escanear: ' + (error.response?.data?.detail || error.message))
  } finally {
    escaneando.value = false
  }
}

const recuperar = async () => {
  if (!confirm('¿Está seguro de recuperar los registros huérfanos? Se crearán nuevos registros en la base de datos a partir de los archivos .meta.json.')) {
    return
  }
  recuperando.value = true
  recuperacionResultado.value = null
  try {
    const res = await apiClient.post('/configuracion/recuperar')
    recuperacionResultado.value = res.data
    mostrarMensaje('success', `Recuperación completada: ${res.data.total_recuperados} registro(s) recuperado(s).`)
    // Actualizar estados
    await cargarEstadosBD()
    if (escaneoResultado.value) {
      await escanear()
    }
  } catch (error) {
    mostrarMensaje('error', 'Error al recuperar: ' + (error.response?.data?.detail || error.message))
  } finally {
    recuperando.value = false
  }
}

const descargarBackup = async () => {
  backupLoading.value = true
  try {
    const res = await apiClient.get('/configuracion/backup/descargar', {
      responseType: 'blob'
    })
    // Crear enlace de descarga
    const url = window.URL.createObjectURL(new Blob([res.data]))
    const link = document.createElement('a')
    link.href = url
    // Extraer nombre del header
    const contentDisposition = res.headers['content-disposition']
    let filename = 'cmms_bioai_backup.json'
    if (contentDisposition) {
      const match = contentDisposition.match(/filename="?(.+?)"?$/)
      if (match) filename = match[1]
    }
    link.setAttribute('download', filename)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    mostrarMensaje('success', 'Backup descargado correctamente.')
  } catch (error) {
    mostrarMensaje('error', 'Error al generar backup: ' + (error.response?.data?.detail || error.message))
  } finally {
    backupLoading.value = false
  }
}

const verBackupPantalla = async () => {
  backupLoading.value = true
  try {
    const res = await apiClient.get('/configuracion/backup')
    // Mostrar en una ventana nueva como JSON formateado
    const jsonStr = JSON.stringify(res.data, null, 2)
    const blob = new Blob([jsonStr], { type: 'application/json' })
    const url = window.URL.createObjectURL(blob)
    window.open(url, '_blank')
    mostrarMensaje('info', 'Backup generado. Se abrió en una nueva pestaña.')
  } catch (error) {
    mostrarMensaje('error', 'Error al generar backup: ' + (error.response?.data?.detail || error.message))
  } finally {
    backupLoading.value = false
  }
}

const seleccionarArchivo = (event) => {
  archivoBackup.value = event.target.files[0]
}

const subirRestore = async () => {
  if (!archivoBackup.value) {
    mostrarMensaje('error', 'Seleccione un archivo de backup primero.')
    return
  }

  if (!confirm('⚠️ ATENCIÓN: Esta operación ELIMINARÁ todos los datos actuales y los reemplazará con el backup. ¿Está completamente seguro?')) {
    return
  }
  if (!confirm('Esta acción NO se puede deshacer. ¿Continuar con la restauración?')) {
    return
  }

  restoreLoading.value = true
  restoreResultado.value = null
  try {
    const formData = new FormData()
    formData.append('archivo', archivoBackup.value)
    const res = await apiClient.post('/configuracion/restore/subir', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    restoreResultado.value = res.data
    mostrarMensaje('success', `Restauración completada: ${res.data.total_registros} registro(s) restaurados.`)
    // Actualizar estados
    await cargarEstadosBD()
    archivoBackup.value = null
  } catch (error) {
    mostrarMensaje('error', 'Error al restaurar: ' + (error.response?.data?.detail || error.message))
  } finally {
    restoreLoading.value = false
  }
}

onMounted(async () => {
  loading.value = true
  await Promise.all([cargarEstadosBD(), cargarConfig()])
  loading.value = false
})
</script>

<template>
  <div class="dashboard-container">
    <Navbar @logout="$router.push('/')" />

    <main class="content">
      <div class="config-header">
        <h2>Configuración</h2>
        <p class="config-subtitle">Administración y recuperación del sistema CMMS-BioAI</p>
      </div>

      <!-- Mensaje flotante -->
      <div v-if="mensaje" class="mensaje-toast" :class="'toast--' + mensaje.tipo">
        {{ mensaje.texto }}
      </div>

      <div v-if="loading" class="loading-state">Cargando información del sistema...</div>

      <template v-if="!loading">
        <!-- ===== CAPA 1: Metadatos en Archivos ===== -->
        <section class="capa-section">
          <div class="capa-header">
            <span class="capa-num capa-num--done">1</span>
            <div>
              <h3>Metadatos en Archivos</h3>
              <p class="capa-status estado--implementado">IMPLEMENTADO</p>
            </div>
          </div>
          <p class="capa-desc">
            Cada archivo subido genera un <code>.meta.json</code> con los datos clave del registro.
            Esto permite reconstruir la información si la base de datos se pierde.
            A continuación se muestra el estado actual de la base de datos:
          </p>

          <div v-if="estadosBD" class="stats-grid">
            <div class="stat-item">
              <span class="stat-icon">⚙️</span>
              <div>
                <span class="stat-value">{{ estadosBD.equipos }}</span>
                <span class="stat-label">Equipos</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">🔩</span>
              <div>
                <span class="stat-value">{{ estadosBD.repuestos }}</span>
                <span class="stat-label">Repuestos</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">🔧</span>
              <div>
                <span class="stat-value">{{ estadosBD.herramientas }}</span>
                <span class="stat-label">Herramientas</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">📋</span>
              <div>
                <span class="stat-value">{{ estadosBD.ordenes_trabajo }}</span>
                <span class="stat-label">OTs</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">📄</span>
              <div>
                <span class="stat-value">{{ estadosBD.documentos }}</span>
                <span class="stat-label">Documentos</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">📜</span>
              <div>
                <span class="stat-value">{{ estadosBD.eventos_historial }}</span>
                <span class="stat-label">Historial</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">🛡️</span>
              <div>
                <span class="stat-value">{{ estadosBD.tareas_preventivas }}</span>
                <span class="stat-label">Preventivo</span>
              </div>
            </div>
            <div class="stat-item">
              <span class="stat-icon">👥</span>
              <div>
                <span class="stat-value">{{ estadosBD.usuarios }}</span>
                <span class="stat-label">Usuarios</span>
              </div>
            </div>
          </div>
        </section>

        <!-- ===== CAPA 2: Escaneo y Recuperación ===== -->
        <section class="capa-section">
          <div class="capa-header">
            <span class="capa-num capa-num--new">2</span>
            <div>
              <h3>Escaneo y Recuperación</h3>
              <p class="capa-status estado--nuevo">NUEVO</p>
            </div>
          </div>
          <p class="capa-desc">
            Escanea los archivos <code>.meta.json</code> del directorio de uploads y compara
            con los registros existentes en la base de datos. Los registros "huérfanos"
            (que existen en archivos pero no en la BD) pueden ser recuperados automáticamente.
          </p>

          <div class="capa-actions">
            <button
              class="btn btn--primary"
              @click="escanear"
              :disabled="escaneando"
            >
              {{ escaneando ? 'Escaneando...' : '🔍 Escanear Archivos' }}
            </button>
            <button
              class="btn btn--success"
              @click="recuperar"
              :disabled="recuperando || !escaneoResultado || escaneoResultado.resumen.total_huerfanos === 0"
            >
              {{ recuperando ? 'Recuperando...' : '♻️ Recuperar Huérfanos' }}
            </button>
          </div>

          <!-- Resultado del escaneo -->
          <div v-if="escaneoResultado" class="resultado-panel">
            <h4>Resultado del Escaneo</h4>
            <div class="escaneo-grid">
              <div class="escaneo-card">
                <span class="escaneo-num">{{ escaneoResultado.resumen.total_en_archivos }}</span>
                <span class="escaneo-label">En archivos</span>
              </div>
              <div class="escaneo-card">
                <span class="escaneo-num">{{ escaneoResultado.resumen.total_en_bd }}</span>
                <span class="escaneo-label">En BD</span>
              </div>
              <div class="escaneo-card escaneo-card--alert" v-if="escaneoResultado.resumen.total_huerfanos > 0">
                <span class="escaneo-num">{{ escaneoResultado.resumen.total_huerfanos }}</span>
                <span class="escaneo-label">Huérfanos</span>
              </div>
              <div class="escaneo-card escaneo-card--ok" v-else>
                <span class="escaneo-num">0</span>
                <span class="escaneo-label">Huérfanos</span>
              </div>
              <div class="escaneo-card">
                <span class="escaneo-num">{{ escaneoResultado.resumen.total_docs_en_archivos }}</span>
                <span class="escaneo-label">Docs en archivos</span>
              </div>
              <div class="escaneo-card" :class="escaneoResultado.resumen.total_docs_huerfanos > 0 ? 'escaneo-card--alert' : ''">
                <span class="escaneo-num">{{ escaneoResultado.resumen.total_docs_huerfanos }}</span>
                <span class="escaneo-label">Docs huérfanos</span>
              </div>
            </div>

            <!-- Detalle de huérfanos por tipo -->
            <div v-if="escaneoResultado.resumen.total_huerfanos > 0" class="huerfanos-detalle">
              <h5>Detalle de registros huérfanos:</h5>
              <div v-for="(tipo_data, tipo) in escaneoResultado.detalle" :key="tipo">
                <div v-if="tipo_data.huerfanos && tipo_data.huerfanos.length > 0" class="huerfano-tipo">
                  <strong>{{ tipo }}:</strong>
                  <span v-for="h in tipo_data.huerfanos" :key="h.id" class="huerfano-badge">
                    ID {{ h.id }} — {{ h.nombre }}
                  </span>
                </div>
              </div>
            </div>
          </div>

          <!-- Resultado de la recuperación -->
          <div v-if="recuperacionResultado" class="resultado-panel resultado--success">
            <h4>Resultado de la Recuperación</h4>
            <div class="escaneo-grid">
              <div class="escaneo-card">
                <span class="escaneo-num">{{ recuperacionResultado.recuperados.equipos }}</span>
                <span class="escaneo-label">Equipos</span>
              </div>
              <div class="escaneo-card">
                <span class="escaneo-num">{{ recuperacionResultado.recuperados.repuestos }}</span>
                <span class="escaneo-label">Repuestos</span>
              </div>
              <div class="escaneo-card">
                <span class="escaneo-num">{{ recuperacionResultado.recuperados.herramientas }}</span>
                <span class="escaneo-label">Herramientas</span>
              </div>
              <div class="escaneo-card">
                <span class="escaneo-num">{{ recuperacionResultado.recuperados.documentos }}</span>
                <span class="escaneo-label">Documentos</span>
              </div>
            </div>
            <p v-if="recuperacionResultado.total_recuperados > 0" class="recuperacion-ok">
              ✅ Total recuperados: {{ recuperacionResultado.total_recuperados }} registro(s)
            </p>
            <p v-else class="recuperacion-vacio">
              No se encontraron registros nuevos para recuperar.
            </p>
            <div v-if="recuperacionResultado.errores && recuperacionResultado.errores.length > 0" class="errores-lista">
              <strong>Errores:</strong>
              <ul>
                <li v-for="(err, idx) in recuperacionResultado.errores" :key="idx">{{ err }}</li>
              </ul>
            </div>
          </div>
        </section>

        <!-- ===== CAPA 3: Backup y Restore ===== -->
        <section class="capa-section">
          <div class="capa-header">
            <span class="capa-num capa-num--new">3</span>
            <div>
              <h3>Backup y Restore</h3>
              <p class="capa-status estado--nuevo">NUEVO</p>
            </div>
          </div>
          <p class="capa-desc">
            Exporta toda la base de datos como un archivo JSON que puede descargarse y
            guardarse como respaldo. En caso de pérdida de datos, el archivo puede
            restaurarse para recuperar el estado completo del sistema.
          </p>

          <div class="capa-split">
            <!-- Backup -->
            <div class="capa-split-card">
              <h4>📥 Generar Backup</h4>
              <p>Exporta todos los registros de la base de datos como archivo JSON.</p>
              <div class="capa-actions">
                <button
                  class="btn btn--primary"
                  @click="descargarBackup"
                  :disabled="backupLoading"
                >
                  {{ backupLoading ? 'Generando...' : '💾 Descargar Backup' }}
                </button>
                <button
                  class="btn btn--secondary"
                  @click="verBackupPantalla"
                  :disabled="backupLoading"
                >
                  👁️ Ver en Pantalla
                </button>
              </div>
            </div>

            <!-- Restore -->
            <div class="capa-split-card">
              <h4>📤 Restaurar Backup</h4>
              <p>⚠️ <strong>ELIMINARÁ</strong> todos los datos actuales y los reemplazará con el backup.</p>
              <div class="restore-upload">
                <input
                  type="file"
                  accept=".json"
                  @change="seleccionarArchivo"
                  class="file-input"
                />
                <span v-if="archivoBackup" class="file-name">📎 {{ archivoBackup.name }}</span>
              </div>
              <div class="capa-actions">
                <button
                  class="btn btn--danger"
                  @click="subirRestore"
                  :disabled="restoreLoading || !archivoBackup"
                >
                  {{ restoreLoading ? 'Restaurando...' : '🔄 Restaurar Backup' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Resultado del restore -->
          <div v-if="restoreResultado" class="resultado-panel resultado--success">
            <h4>Resultado de la Restauración</h4>
            <div class="escaneo-grid">
              <div v-for="(count, tabla) in restoreResultado.restaurados" :key="tabla" class="escaneo-card">
                <span class="escaneo-num">{{ count }}</span>
                <span class="escaneo-label">{{ tabla.replace(/_/g, ' ') }}</span>
              </div>
            </div>
            <p class="recuperacion-ok">
              ✅ Total restaurados: {{ restoreResultado.total_registros }} registro(s)
            </p>
            <p v-if="restoreResultado.backup_origen.fecha_backup" class="backup-origen">
              Backup del: {{ restoreResultado.backup_origen.fecha_backup }}
            </p>
            <div v-if="restoreResultado.errores && restoreResultado.errores.length > 0" class="errores-lista">
              <strong>Errores:</strong>
              <ul>
                <li v-for="(err, idx) in restoreResultado.errores" :key="idx">{{ err }}</li>
              </ul>
            </div>
          </div>
        </section>

        <!-- ===== Configuración del Sistema ===== -->
        <section class="capa-section">
          <div class="capa-header">
            <span class="capa-icon">🛠️</span>
            <div>
              <h3>Configuración del Sistema</h3>
              <p class="capa-status estado--info">SOLO LECTURA</p>
            </div>
          </div>
          <p class="capa-desc">
            Configuración actual del sistema almacenada en <code>config.json</code>.
          </p>

          <div v-if="config" class="config-grid">
            <div class="config-card">
              <h5>Empresa</h5>
              <div class="config-row">
                <span>Nombre:</span>
                <strong>{{ config.empresa?.nombre || '—' }}</strong>
              </div>
            </div>
            <div class="config-card">
              <h5>Sistema</h5>
              <div class="config-row">
                <span>Idioma:</span>
                <strong>{{ config.sistema?.idioma || '—' }}</strong>
              </div>
              <div class="config-row">
                <span>Zona horaria:</span>
                <strong>{{ config.sistema?.zona_horaria || '—' }}</strong>
              </div>
              <div class="config-row">
                <span>Moneda:</span>
                <strong>{{ config.sistema?.moneda || '—' }}</strong>
              </div>
            </div>
            <div class="config-card">
              <h5>Prefijos</h5>
              <div class="config-row">
                <span>Equipos:</span>
                <strong class="prefijo-badge">{{ config.sistema?.prefijo_equipos || 'E' }}</strong>
              </div>
              <div class="config-row">
                <span>Repuestos:</span>
                <strong class="prefijo-badge">{{ config.sistema?.prefijo_repuestos || 'R' }}</strong>
              </div>
              <div class="config-row">
                <span>Órdenes:</span>
                <strong class="prefijo-badge">{{ config.sistema?.prefijo_ordenes || 'OT' }}</strong>
              </div>
            </div>
            <div class="config-card">
              <h5>Directorios</h5>
              <div v-for="(ruta, key) in config.directorios" :key="key" class="config-row">
                <span>{{ key }}:</span>
                <code>{{ ruta }}</code>
              </div>
            </div>
          </div>
        </section>
      </template>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

.config-header {
  margin-bottom: 1.5rem;
}
.config-header h2 {
  margin: 0 0 0.25rem 0;
  color: #1e293b;
  font-size: 1.5rem;
}
.config-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}

.loading-state {
  text-align: center;
  padding: 3rem;
  color: #64748b;
}

/* === Mensaje toast === */
.mensaje-toast {
  position: fixed;
  top: 1rem;
  right: 1rem;
  padding: 0.85rem 1.25rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
  z-index: 1000;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  animation: slideIn 0.3s ease;
}
@keyframes slideIn {
  from { opacity: 0; transform: translateX(50px); }
  to { opacity: 1; transform: translateX(0); }
}
.toast--success { background: #22c55e; }
.toast--error { background: #ef4444; }
.toast--info { background: #3b82f6; }

/* === Capa Section === */
.capa-section {
  background: white;
  border-radius: 10px;
  padding: 1.5rem;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 1.25rem;
}
.capa-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.capa-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  font-weight: 700;
  font-size: 1.05rem;
  flex-shrink: 0;
}
.capa-num--done {
  background: #dcfce7;
  color: #16a34a;
  border: 2px solid #86efac;
}
.capa-num--new {
  background: #dbeafe;
  color: #2563eb;
  border: 2px solid #93c5fd;
}
.capa-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}
.capa-header h3 {
  margin: 0;
  font-size: 1.1rem;
  color: #1e293b;
}
.capa-status {
  display: inline-block;
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  margin-top: 0.2rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.estado--implementado { background: #dcfce7; color: #16a34a; }
.estado--nuevo { background: #dbeafe; color: #2563eb; }
.estado--info { background: #f1f5f9; color: #64748b; }
.capa-desc {
  color: #475569;
  font-size: 0.9rem;
  line-height: 1.6;
  margin: 0 0 1rem 0;
}
.capa-desc code {
  background: #f1f5f9;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.82rem;
  color: #7c3aed;
}

/* === Stats Grid (Capa 1) === */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.65rem;
}
@media (max-width: 900px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 550px) {
  .stats-grid { grid-template-columns: 1fr; }
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  padding: 0.65rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.stat-icon {
  font-size: 1.2rem;
}
.stat-value {
  display: block;
  font-size: 1.2rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}
.stat-label {
  display: block;
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
}

/* === Botones === */
.capa-actions {
  display: flex;
  gap: 0.65rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}
.btn {
  padding: 0.55rem 1.15rem;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.88rem;
  cursor: pointer;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.btn--primary {
  background: #3b82f6;
  color: white;
}
.btn--primary:hover:not(:disabled) { background: #2563eb; }
.btn--success {
  background: #22c55e;
  color: white;
}
.btn--success:hover:not(:disabled) { background: #16a34a; }
.btn--secondary {
  background: #64748b;
  color: white;
}
.btn--secondary:hover:not(:disabled) { background: #475569; }
.btn--danger {
  background: #ef4444;
  color: white;
}
.btn--danger:hover:not(:disabled) { background: #dc2626; }

/* === Resultado Panel === */
.resultado-panel {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  padding: 1rem;
  margin-top: 0.75rem;
}
.resultado-panel h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  color: #1e293b;
}
.resultado--success {
  border-color: #86efac;
  background: #f0fdf4;
}

/* === Escaneo Grid === */
.escaneo-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.65rem;
  margin-bottom: 0.75rem;
}
.escaneo-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
  text-align: center;
}
.escaneo-card--alert {
  border-color: #fca5a5;
  background: #fef2f2;
}
.escaneo-card--ok {
  border-color: #86efac;
  background: #f0fdf4;
}
.escaneo-num {
  font-size: 1.4rem;
  font-weight: 700;
  color: #1e293b;
  line-height: 1.2;
}
.escaneo-card--alert .escaneo-num { color: #dc2626; }
.escaneo-card--ok .escaneo-num { color: #16a34a; }
.escaneo-label {
  font-size: 0.72rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  margin-top: 0.2rem;
}

/* === Huérfanos detalle === */
.huerfanos-detalle {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e2e8f0;
}
.huerfanos-detalle h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.85rem;
  color: #dc2626;
}
.huerfano-tipo {
  margin-bottom: 0.4rem;
  font-size: 0.85rem;
  color: #475569;
}
.huerfano-badge {
  display: inline-block;
  background: #fef2f2;
  color: #dc2626;
  border: 1px solid #fca5a5;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  margin-left: 0.35rem;
  margin-bottom: 0.25rem;
}

/* === Recuperación resultado === */
.recuperacion-ok {
  color: #16a34a;
  font-weight: 600;
  font-size: 0.9rem;
  margin: 0.5rem 0 0 0;
}
.recuperacion-vacio {
  color: #64748b;
  font-size: 0.85rem;
  margin: 0.5rem 0 0 0;
}
.backup-origen {
  color: #64748b;
  font-size: 0.82rem;
  margin: 0.25rem 0 0 0;
}
.errores-lista {
  margin-top: 0.5rem;
  color: #dc2626;
  font-size: 0.82rem;
}
.errores-lista ul {
  margin: 0.25rem 0 0 0;
  padding-left: 1.2rem;
}

/* === Capa Split (Backup/Restore) === */
.capa-split {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}
@media (max-width: 700px) {
  .capa-split { grid-template-columns: 1fr; }
}
.capa-split-card {
  padding: 1rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.capa-split-card h4 {
  margin: 0 0 0.5rem 0;
  font-size: 0.95rem;
  color: #1e293b;
}
.capa-split-card p {
  margin: 0 0 0.75rem 0;
  font-size: 0.85rem;
  color: #475569;
  line-height: 1.5;
}
.restore-upload {
  margin-bottom: 0.75rem;
}
.file-input {
  font-size: 0.85rem;
  width: 100%;
}
.file-name {
  display: block;
  font-size: 0.82rem;
  color: #475569;
  margin-top: 0.25rem;
}

/* === Config Grid === */
.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}
@media (max-width: 700px) {
  .config-grid { grid-template-columns: 1fr; }
}
.config-card {
  padding: 0.85rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.config-card h5 {
  margin: 0 0 0.5rem 0;
  font-size: 0.88rem;
  color: #1e293b;
  border-bottom: 1px solid #e2e8f0;
  padding-bottom: 0.35rem;
}
.config-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.82rem;
  color: #475569;
  gap: 0.5rem;
}
.config-row span {
  flex-shrink: 0;
  font-weight: 500;
}
.config-row strong {
  text-align: right;
  font-size: 0.85rem;
}
.config-row code {
  background: #f1f5f9;
  padding: 0.1rem 0.35rem;
  border-radius: 4px;
  font-size: 0.78rem;
  color: #7c3aed;
  word-break: break-all;
}
.prefijo-badge {
  background: #dbeafe;
  color: #2563eb;
  padding: 0.1rem 0.5rem;
  border-radius: 4px;
  font-size: 0.85rem;
}
</style>
