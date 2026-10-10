<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import apiClient from '../services/api.js'
import DocumentosAdjuntos from '../components/DocumentosAdjuntos.vue'

const router = useRouter()
const route = useRoute()

// --- Variables Generales ---
const ordenes = ref([])
const equipos = ref([])
const estadosOT = ref([]) 
const tecnicos = ref([])
const loading = ref(true)

const currentPage = ref(1)
const pageSize = ref(10)
const searchQuery = ref('')

// v0.9.20: filtros adicionales
const filterTipo = ref('')
const filterPrioridad = ref('')
const filterEstado = ref('')
const sortOrder = ref('desc')  // 'desc' = más nuevas primero, 'asc' = más viejas primero

// Tipos de OT para el menú de selección de Título
const tiposOT = [
  'Correctivo',
  'Preventivo',
  'Predictivo',
  'Calibración',
  'Inspección',
  'Actualización',
  'Diagnóstico',
  'Prueba/Validación',
  'Limpieza',
  'Cambio de repuesto',
  'Grasa/Lubricación',
  'Instalación',
  'Retiro/Dado de baja',
  'Transferencia',
  'Auditoría',
  'Otro'
]

const filteredOrdenes = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  let result = ordenes.value

  // Búsqueda libre
  if (q) {
    result = result.filter((ot) => {
      const titulo = String(ot.titulo ?? '').toLowerCase()
      const falla = String(ot.descripcion_falla ?? '').toLowerCase()
      const id = String(ot.id ?? '')
      const equipo = getEquipoNombre(ot.equipo_id).toLowerCase()
      return titulo.includes(q) || falla.includes(q) || id.includes(q) || equipo.includes(q)
    })
  }

  // v0.9.20: filtros por Tipo, Prioridad, Estado
  if (filterTipo.value) {
    result = result.filter(ot => ot.titulo === filterTipo.value)
  }
  if (filterPrioridad.value) {
    result = result.filter(ot => ot.prioridad === filterPrioridad.value)
  }
  if (filterEstado.value) {
    result = result.filter(ot => String(ot.estado_id) === String(filterEstado.value))
  }

  // v0.9.20: ordenamiento por ID (asc = viejas primero, desc = nuevas primero)
  result = [...result].sort((a, b) => {
    if (sortOrder.value === 'desc') return b.id - a.id
    return a.id - b.id
  })

  return result
})

const paginatedOrdenes = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredOrdenes.value.slice(start, start + pageSize.value)
})

const totalPages = computed(() =>
  Math.max(1, Math.ceil(filteredOrdenes.value.length / pageSize.value))
)

watch(
  () => filteredOrdenes.value.length,
  (len) => {
    const tp = Math.max(1, Math.ceil(len / pageSize.value))
    if (currentPage.value > tp) currentPage.value = tp
  }
)

watch([searchQuery, filterTipo, filterPrioridad, filterEstado, sortOrder], () => {
  currentPage.value = 1
})

const irPaginaAnterior = () => {
  if (currentPage.value > 1) currentPage.value -= 1
}

const irPaginaSiguiente = () => {
  if (currentPage.value < totalPages.value) currentPage.value += 1
}

// --- Control de Modales ---
const showModal = ref(false) // Modal Crear
const showEditModal = ref(false) // Modal Editar (Lápiz)
const showViewModal = ref(false) // Modal Ver (Ojo)
const selectedOT = ref({}) // OT seleccionada

// ═══ v1.1.0 — Flujo de Trabajo OT (máquina de estados R2) ═══
const showFlowModal = ref(false)      // Modal Acciones de Flujo
const flowOT = ref(null)              // OT sobre la que se ejecuta la acción
const flowAccion = ref(null)          // asignar|iniciar|pausar|reanudar|resolver|cancelar|reincidencia
const flowBusy = ref(false)
const bitacoraOT = ref([])            // bitácora para el modal Ver (R4)
const usuarioActual = (() => {
  // username desde el JWT del login (payload.sub)
  try {
    const token = localStorage.getItem('token')
    if (!token) return null
    return JSON.parse(atob(token.split('.')[1])).sub || null
  } catch { return null }
})()

// Debe reflejar TRANSICIONES_VALIDAS del backend (ordenes.py) — v2.1.3 (5 estados)
const ACCIONES_POR_ESTADO = {
  'Abierta':       ['asignar', 'iniciar', 'cancelar'],
  'En Proceso':    ['asignar', 'pausar', 'resolver', 'cancelar'],
  'Esp. Repuesto': ['asignar', 'reanudar', 'cancelar'],
  'Completada':    ['reincidencia'],
  'Cancelada':     ['reincidencia']
}

const META_ACCIONES = {
  asignar:      { label: '👨‍🔧 Asignar técnico', desc: 'Define o reasigna el responsable (puede cambiarse en cualquier momento sin detener el flujo). Fija la fecha de asignación (MTTA) la primera vez.' },
  iniciar:      { label: '▶ Iniciar trabajo', desc: 'Abierta → En Proceso. Requiere técnico asignado; fija la fecha de inicio (tiempo de reacción).' },
  pausar:       { label: '⏸ Pausar (Esp. Repuesto)', desc: 'En Proceso → Esp. Repuesto. Motivo obligatorio; el intervalo alimenta el KPI de espera de repuestos.' },
  reanudar:     { label: '↻ Reanudar', desc: 'Esp. Repuesto → En Proceso. Cierra el intervalo de espera. Puede registrar los repuestos entregados del almacén (se descuentan aquí).' },
  resolver:     { label: '✔ Resolver y completar', desc: '→ Completada. Exige solución y tiempo invertido (R3); fija fecha de resolución. Cierre DEFINITIVO: para re-intervenciones use Reincidencia. Puede registrar repuestos/costos aquí.' },
  cancelar:     { label: '✕ Cancelar', desc: 'Cierra la OT como cancelada. Motivo obligatorio. Cierre DEFINITIVO.' },
  reincidencia: { label: '🔁 Generar OT de reincidencia', desc: 'La OT cerrada es INMUTABLE (v1.1.1). Si la misma falla vuelve, se crea una OT NUEVA vinculada (secuencia de falla +1) que nace Abierta y hereda técnico y datos.' }
}

const flowForm = ref({ tecnico_asignado_id: null, comentario: '', acciones_realizadas: '', tiempo_real_invertido: null, unidad_tiempo: 'horas' })

// v1.1.1: repuestos/costos DENTRO del modal de flujo (reanudar/resolver)
const flowRepuestos = ref([])
const flowRepuestoId = ref(null)
const flowRepuestoCantidad = ref(1)
const flowCostos = ref([])
const flowCostoForm = ref({ tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null })
const totalFlowCostos = computed(() => flowCostos.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))

// v1.1.1: helpers de mensajes de error claros (422 de validación incluido)
const errMsg = (e, fallback) => {
  const d = e?.response?.data?.detail
  if (typeof d === 'string' && d) return d
  if (Array.isArray(d)) {
    return d.map(x => {
      const campo = (x.loc || []).slice(1).join('.')
      return campo ? `${campo}: ${x.msg}` : (x.msg || '')
    }).filter(Boolean).join(' | ') || fallback
  }
  return fallback
}

// v1.1.1: stock efectivo para el modal crear/editar — el backend RESTAURA los
// repuestos previos de esta OT antes de descontar los nuevos, así que el
// disponible real = stock actual + lo que esta OT ya tiene en la lista.
const stockEfectivo = (repId, lista) => {
  const rep = listaRepuestos.value.find(r => r.id === repId)
  if (!rep) return 0
  const yaEnLista = (lista || []).filter(i => i.repuesto_id === repId)
    .reduce((s, i) => s + (Number(i.cantidad) || 0), 0)
  return (rep.cantidad_disponible || 0) + yaEnLista
}

// v1.1.1: descarga de CSV (bitácora) vía axios-blob
const descargarCSV = async (url, filename) => {
  try {
    const res = await apiClient.get(url, { responseType: 'blob' })
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = filename
    link.click()
    URL.revokeObjectURL(link.href)
  } catch {
    alert('No se pudo exportar el CSV')
  }
}
const exportBitacoraOT = () => descargarCSV(`/reportes/bitacora-csv?ot_id=${selectedOT.value.id}`, `bitacora_ot_${selectedOT.value.id}.csv`)
const exportBitacoraEquipo = () => descargarCSV(`/reportes/bitacora-csv?equipo_id=${selectedOT.value.equipo_id}`, `bitacora_equipo_${selectedOT.value.equipo_id}.csv`)

// --- Variables Modal Documentos ---
const showDocsModal = ref(false)
const docsOT = ref({})

// --- Variables para Repuestos ---
const listaRepuestos = ref([])
const selectedRepuestoId = ref(null)
const selectedCantidad = ref(1)
const repuestosSeleccionados = ref([])

// v0.9.21: Variables para Costos Adicionales (RF11 - OtCostoAdicional)
const tiposCosto = [
  'Transporte', 'Servicio Externo', 'Repuesto No Inventariado',
  'Herramienta Renta', 'Honorarios / Mano de Obra',
  'Insumos / Materiales', 'Viáticos', 'Otro'
]
const costosAdicionales = ref([])        // lista de costos (para modal crear)
const editCostosAdicionales = ref([])    // lista de costos (para modal editar)
const detalleCostos = ref([])            // lista de costos (para modal ver)
const costoForm = ref({ tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null })
const editCostoForm = ref({ tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null })

const totalCostos = computed(() => costosAdicionales.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))
const totalEditCostos = computed(() => editCostosAdicionales.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))
const totalDetalleCostos = computed(() => detalleCostos.value.reduce((s, c) => s + (Number(c.monto_costo) || 0), 0))

const addCostoToOT = () => {
  if (!costoForm.value.descripcion_costo || !costoForm.value.monto_costo) {
    alert('Complete descripción y monto del costo')
    return
  }
  costosAdicionales.value.push({ ...costoForm.value, monto_costo: Number(costoForm.value.monto_costo) })
  costoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
}

const removeCostoFromOT = (idx) => {
  costosAdicionales.value.splice(idx, 1)
}

const addEditCostoToOT = () => {
  if (!editCostoForm.value.descripcion_costo || !editCostoForm.value.monto_costo) {
    alert('Complete descripción y monto del costo')
    return
  }
  editCostosAdicionales.value.push({ ...editCostoForm.value, monto_costo: Number(editCostoForm.value.monto_costo) })
  editCostoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
}

const removeEditCostoFromOT = (idx) => {
  editCostosAdicionales.value.splice(idx, 1)
}

// v0.9.21: Sincronizar costos de una OT con el backend
// - costosNuevos: los que están en el formulario pero no tienen id (crear)
// - costosExistentes: los que tienen id (mantener)
// - costosEliminar: los que están en BD pero no en el formulario (eliminar)
async function sincronizarCostosOT(otId, costosFormulario) {
  // costosFormulario: array de {id?, tipo_costo, descripcion_costo, monto_costo}
  // 1. Obtener costos actuales de la OT desde el backend
  const res = await apiClient.get(`/costos/?orden_trabajo_id=${otId}`)
  const costosBD = res.data
  const idsFormulario = costosFormulario.filter(c => c.id).map(c => c.id)

  // 2. Eliminar los que están en BD pero no en el formulario
  for (const cBD of costosBD) {
    if (!idsFormulario.includes(cBD.id)) {
      await apiClient.delete(`/costos/${cBD.id}`)
    }
  }

  // 3. Crear los nuevos (sin id) y actualizar los existentes (con id)
  for (const c of costosFormulario) {
    if (c.id) {
      // Actualizar existente
      await apiClient.put(`/costos/${c.id}`, {
        tipo_costo: c.tipo_costo,
        descripcion_costo: c.descripcion_costo,
        monto_costo: c.monto_costo
      })
    } else {
      // Crear nuevo
      await apiClient.post('/costos/', {
        orden_trabajo_id: otId,
        tipo_costo: c.tipo_costo,
        descripcion_costo: c.descripcion_costo,
        monto_costo: c.monto_costo
      })
    }
  }
}

// v0.9.23: Helpers datetime-local (DEBEN estar antes de formData por hoisting de const)
const toLocalDatetimeString = (date) => {
  const y = date.getFullYear()
  const m = String(date.getMonth() + 1).padStart(2, '0')
  const d = String(date.getDate()).padStart(2, '0')
  const h = String(date.getHours()).padStart(2, '0')
  const min = String(date.getMinutes()).padStart(2, '0')
  return `${y}-${m}-${d}T${h}:${min}`
}

const toDatetimeLocal = (isoStr) => {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return toLocalDatetimeString(d)
}

// Formulario Crear
// v1.1.0 (R1): sin estado_id — toda OT nace Abierta
const formData = ref({
  equipo_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: null,
  unidad_tiempo: 'horas',
  tiempo_real_invertido: null,
  acciones_realizadas: '',
  fecha_creacion: toLocalDatetimeString(new Date())  // v0.9.23: datetime-local default now
})

// Formulario Editar
// v1.1.0 (H2): sin estado_id — el estado solo cambia por acciones de flujo
const editFormData = ref({
  equipo_id: '',
  prioridad: 'Media',
  titulo: '',
  descripcion_falla: '',
  tecnico_asignado_id: null,
  unidad_tiempo: 'horas',
  tiempo_real_invertido: null,
  acciones_realizadas: '',
  fecha_creacion: ''
})

// --- Funciones de Datos ---
const fetchData = async () => {
  try {
    loading.value = true
    const [resOrdenes, resEquipos, resEstados, resUsers] = await Promise.all([
      apiClient.get('/ordenes/'),
      apiClient.get('/equipos/'),
      apiClient.get('/ordenes/estados/'),
      apiClient.get('/users/')
    ])
    ordenes.value = resOrdenes.data
    equipos.value = resEquipos.data
    estadosOT.value = resEstados.data
    tecnicos.value = resUsers.data
  } catch (error) {
    console.error('Error cargando datos', error)
  } finally {
    loading.value = false
  }
}

// v0.9.18: Abrir modal Crear — cargar repuestos y resetear estado
const openCreateModal = async () => {
  formData.value = { equipo_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: null, unidad_tiempo: 'horas', tiempo_real_invertido: null, acciones_realizadas: '', fecha_creacion: toLocalDatetimeString(new Date()) }
  repuestosSeleccionados.value = []
  selectedRepuestoId.value = null
  selectedCantidad.value = 1
  // v0.9.21: resetear costos
  costosAdicionales.value = []
  costoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
  // Cargar repuestos para el selector
  try {
    const resRep = await apiClient.get('/repuestos/')
    listaRepuestos.value = resRep.data
  } catch (e) {
    console.error('Error cargando repuestos:', e)
  }
  showModal.value = true
}

// v1.1.1 — Bloqueo suave: OTs ACTIVAS del equipo seleccionado en el modal Crear
const ESTADOS_CERRADOS_FE = ['Completada', 'Cancelada']
const activasDelEquipoSeleccionado = computed(() => {
  if (!formData.value.equipo_id) return []
  return ordenes.value.filter(o =>
    o.equipo_id === Number(formData.value.equipo_id) &&
    !ESTADOS_CERRADOS_FE.includes(getEstadoNombre(o.estado_id)))
})

const saveOrden = async () => {
  // v1.1.1: bloqueo suave — avisar si el equipo ya tiene OTs activas
  // (un equipo puede tener 2 fallas simultáneas, ej. software + hardware,
  //  pero debe ser una decisión CONSCIENTE del usuario)
  if (activasDelEquipoSeleccionado.value.length > 0) {
    const lista = activasDelEquipoSeleccionado.value
      .map(o => `#${o.id} (${getEstadoNombre(o.estado_id)})`).join(', ')
    if (!confirm(`⚠ Este equipo ya tiene ${activasDelEquipoSeleccionado.value.length} OT activa(s): ${lista}.\n\n¿Desea crear otra OT para el mismo equipo de todos modos?`)) {
      return
    }
  }
  try {
    const payload = { ...formData.value, repuestos_utilizados: repuestosSeleccionados.value }
    if (payload.tiempo_real_invertido === "" || payload.tiempo_real_invertido === null) {
      payload.tiempo_real_invertido = null
    } else {
      payload.tiempo_real_invertido = parseFloat(payload.tiempo_real_invertido)
    }
    const res = await apiClient.post('/ordenes/', payload)
    const nuevaOTId = res.data.id
    // v0.9.21: guardar costos adicionales
    if (costosAdicionales.value.length > 0) {
      await sincronizarCostosOT(nuevaOTId, costosAdicionales.value)
    }
    alert('Orden creada')
    showModal.value = false
    formData.value = { equipo_id: '', prioridad: 'Media', titulo: '', descripcion_falla: '', tecnico_asignado_id: null, unidad_tiempo: 'horas', tiempo_real_invertido: null, acciones_realizadas: '', fecha_creacion: toLocalDatetimeString(new Date()) }
    repuestosSeleccionados.value = []
    costosAdicionales.value = []
    fetchData() 
  } catch (error) {
    alert(errMsg(error, 'Error al crear OT'))
  }
}

// --- NUEVO: Abrir Modal Ver (Solo Lectura) ---
const openViewModal = async (ot) => {
  // Llamamos al detalle para tener datos frescos
  try {
    const res = await apiClient.get(`/ordenes/${ot.id}`)
    selectedOT.value = res.data
    // v0.9.20: cargar lista de repuestos para resolver nombres en el modal Ver
    if (!listaRepuestos.value.length) {
      try {
        const resRep = await apiClient.get('/repuestos/')
        listaRepuestos.value = resRep.data
      } catch (e) {
        console.warn('No se pudieron cargar repuestos para el detalle', e)
      }
    }
    // v0.9.21: cargar costos adicionales de la OT
    try {
      const resCostos = await apiClient.get(`/costos/?orden_trabajo_id=${ot.id}`)
      detalleCostos.value = resCostos.data
    } catch (e) {
      console.warn('No se pudieron cargar costos', e)
      detalleCostos.value = []
    }
    // v1.1.0: bitácora del flujo (R4)
    try {
      const resBit = await apiClient.get(`/ordenes/${ot.id}/bitacora`)
      bitacoraOT.value = resBit.data
    } catch (e) {
      bitacoraOT.value = []
    }
    showViewModal.value = true
  } catch (e) {
    alert("Error al cargar detalles")
  }
}

// v0.9.20: helper para obtener el nombre de un repuesto por su ID
const getRepuestoNombre = (id) => {
  if (!id) return ''
  const rep = listaRepuestos.value.find(r => r.id === id)
  return rep ? rep.nombre_repuesto : `Repuesto #${id}`
}

// --- NUEVO: Abrir Modal Editar (Lápiz) ---
const openEditModal = async (ot) => {
  try {
    // 1. Obtener datos frescos de la orden específica
    const res = await apiClient.get(`/ordenes/${ot.id}`)
    const fullOt = res.data
    
    selectedOT.value = fullOt
    
    // 2. Cargar repuestos para el selector
    const resRep = await apiClient.get('/repuestos/')
    listaRepuestos.value = resRep.data
    
    // 3. Llenar formulario de edición
    editFormData.value = {
      equipo_id: fullOt.equipo_id,
      prioridad: fullOt.prioridad || 'Media',
      titulo: fullOt.titulo || '',
      descripcion_falla: fullOt.descripcion_falla || '',
      tecnico_asignado_id: fullOt.tecnico_asignado_id || null,
      unidad_tiempo: fullOt.unidad_tiempo || 'horas',
      tiempo_real_invertido: fullOt.tiempo_real_invertido || null,
      acciones_realizadas: fullOt.acciones_realizadas || '',
      fecha_creacion: toDatetimeLocal(fullOt.fecha_creacion)
    }

    // v0.9.21: cargar costos adicionales existentes
    try {
      const resCostos = await apiClient.get(`/costos/?orden_trabajo_id=${ot.id}`)
      editCostosAdicionales.value = resCostos.data.map(c => ({
        id: c.id,
        tipo_costo: c.tipo_costo,
        descripcion_costo: c.descripcion_costo,
        monto_costo: c.monto_costo
      }))
    } catch (e) {
      editCostosAdicionales.value = []
    }
    editCostoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
    
    // 4. Pre-llenar repuestos existentes de la OT
    repuestosSeleccionados.value = []
    if (fullOt.repuestos_usados && fullOt.repuestos_usados.length > 0) {
      repuestosSeleccionados.value = fullOt.repuestos_usados.map(r => {
        const repInfo = listaRepuestos.value.find(rp => rp.id === r.repuesto_id)
        return {
          repuesto_id: r.repuesto_id,
          nombre: repInfo ? repInfo.nombre_repuesto : `Repuesto #${r.repuesto_id}`,
          cantidad: r.cantidad_utilizada
        }
      })
    }
    
    // 5. Si la OT viene de preventivo y no tiene repuestos, sugerir los del kit
    if (fullOt.orden_preventiva_id && repuestosSeleccionados.value.length === 0) {
      try {
        const resTarea = await apiClient.get(`/preventivo/${fullOt.orden_preventiva_id}`)
        const kitRepuestos = resTarea.data.repuestos_detalle || []
        if (kitRepuestos.length > 0) {
          repuestosSeleccionados.value = kitRepuestos.map(r => {
            const repInfo = listaRepuestos.value.find(rp => rp.id === r.repuesto_id)
            return {
              repuesto_id: r.repuesto_id,
              nombre: repInfo ? repInfo.nombre_repuesto : `Repuesto #${r.repuesto_id}`,
              cantidad: r.cantidad_requerida
            }
          })
        }
      } catch (e) {
        console.warn('No se pudieron cargar repuestos del kit preventivo', e)
      }
    }
    
    showEditModal.value = true
  } catch (e) {
    console.error(e)
    alert("Error al cargar orden para editar")
  }
}

const addRepuestoToOT = () => {
  if (!selectedRepuestoId.value || selectedCantidad.value < 1) return
  const repInfo = listaRepuestos.value.find(r => r.id === selectedRepuestoId.value)
  if (!repInfo) return
  // v1.1.1: stock efectivo = stock actual + lo que esta OT ya tiene en la
  // lista (el backend restaura los previos antes de descontar los nuevos)
  if (selectedCantidad.value > stockEfectivo(selectedRepuestoId.value, repuestosSeleccionados.value)) {
    alert(`No hay suficiente stock de "${repInfo.nombre_repuesto}" (disponible: ${repInfo.cantidad_disponible})`)
    return
  }
  // v1.1.1: si el repuesto ya está en la lista, acumula la cantidad (PK compuesta)
  const existente = repuestosSeleccionados.value.find(i => i.repuesto_id === selectedRepuestoId.value)
  if (existente) {
    existente.cantidad += Number(selectedCantidad.value)
  } else {
    repuestosSeleccionados.value.push({
      repuesto_id: repInfo.id,
      nombre: repInfo.nombre_repuesto,
      cantidad: Number(selectedCantidad.value)
    })
  }
  selectedRepuestoId.value = null
  selectedCantidad.value = 1
}

// v1.1.1: repuestos/costos dentro del modal de flujo (reanudar/resolver).
// Aquí el stock es el ACTUAL: cada entrega del flujo descuenta de verdad.
const addFlowRepuestoToOT = () => {
  if (!flowRepuestoId.value || flowRepuestoCantidad.value < 1) return
  const repInfo = listaRepuestos.value.find(r => r.id === flowRepuestoId.value)
  if (!repInfo) return
  if (Number(flowRepuestoCantidad.value) > repInfo.cantidad_disponible) {
    alert(`No hay suficiente stock de "${repInfo.nombre_repuesto}" (disponible: ${repInfo.cantidad_disponible})`)
    return
  }
  const existente = flowRepuestos.value.find(i => i.repuesto_id === flowRepuestoId.value)
  if (existente) {
    existente.cantidad += Number(flowRepuestoCantidad.value)
  } else {
    flowRepuestos.value.push({ repuesto_id: repInfo.id, nombre: repInfo.nombre_repuesto, cantidad: Number(flowRepuestoCantidad.value) })
  }
  flowRepuestoId.value = null
  flowRepuestoCantidad.value = 1
}
const removeFlowRepuesto = (idx) => flowRepuestos.value.splice(idx, 1)
const addFlowCostoToOT = () => {
  if (!flowCostoForm.value.descripcion_costo || !flowCostoForm.value.monto_costo) {
    alert('Complete descripción y monto del costo')
    return
  }
  flowCostos.value.push({ ...flowCostoForm.value, monto_costo: Number(flowCostoForm.value.monto_costo) })
  flowCostoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
}
const removeFlowCosto = (idx) => flowCostos.value.splice(idx, 1)

const updateOrden = async () => {
  try {
    const payload = { 
      ...editFormData.value,
      repuestos_utilizados: repuestosSeleccionados.value
    };
    
    if (payload.tiempo_real_invertido === "" || payload.tiempo_real_invertido === null) {
      payload.tiempo_real_invertido = null;
    } else {
      payload.tiempo_real_invertido = parseFloat(payload.tiempo_real_invertido);
    }

    await apiClient.put(`/ordenes/${selectedOT.value.id}`, payload)
    // v0.9.21: sincronizar costos adicionales
    await sincronizarCostosOT(selectedOT.value.id, editCostosAdicionales.value)
    alert('Orden actualizada')
    showEditModal.value = false
    fetchData() 
  } catch (error) {
    console.error(error)
    alert(errMsg(error, 'Error al actualizar'))
  }
}

const deleteOrden = async (id) => {
  if (confirm("¿Eliminar esta orden?")) {
    try {
      await apiClient.delete(`/ordenes/${id}`)
      alert('Orden eliminada')
      fetchData()
    } catch (error) {
      alert('Error al eliminar')
    }
  }
}

// --- Helpers ---
const getEquipoNombre = (id) => {
  const eq = equipos.value.find(e => e.id === id)
  return eq ? `${eq.nombre_corto || eq.modelo}` : `ID: ${id}`
}

const getTecnicoNombre = (id) => {
  if (!id) return 'Sin Asignar'
  const t = tecnicos.value.find(u => u.id === id)
  return t ? (t.full_name || t.username) : 'Desconocido'
}

const prioridadClass = (prio) => {
  if (prio === 'Urgente') return 'urgente'
  if (prio === 'Alta') return 'alta'
  return 'media'
}

// Helper para obtener color del estado
const getEstadoColor = (id) => {
  const state = estadosOT.value.find(e => e.id === id)
  return state && state.color ? state.color : '#95a5a6'
}

// v0.9.23: Icono de origen (opción B: icono en título)
const getOrigenIcon = (ot) => {
  if (ot.orden_preventiva_id) return '🛡️'
  return ''
}
const getOrigenTitle = (ot) => {
  if (ot.orden_preventiva_id) return `Preventivo #${ot.orden_preventiva_id}`
  return 'Correctivo manual'
}

// v0.9.23: Formatear fecha y hora de creación para la tabla
const formatFechaHora = (ot) => {
  if (!ot.fecha_creacion) return 'N/A'
  const d = new Date(ot.fecha_creacion)
  const fecha = d.toLocaleDateString('es-BO')
  const hora = d.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' })
  return `${fecha} ${hora}`
}

// --- Función para abrir Modal Documentos ---
const openDocsModal = (ot) => {
  docsOT.value = ot
  showDocsModal.value = true
}

// ═══ v1.1.0 — Helpers del flujo OT ═══
const getEstadoNombre = (id) => estadosOT.value.find(e => e.id === id)?.nombre_estado || 'N/A'

const isOTCerrada = (ot) => ['Completada', 'Cancelada'].includes(getEstadoNombre(ot.estado_id))

// H6: vencimiento visible; resalta si ya venció y la OT sigue abierta
const isVencida = (ot) => {
  if (!ot?.fecha_vencimiento) return false
  if (isOTCerrada(ot)) return false
  return new Date(ot.fecha_vencimiento + 'T23:59:59') < new Date()
}

const formatFecha = (s) => s ? new Date(s).toLocaleDateString('es-BO') : '—'

const fmtDT = (s) => {
  if (!s) return '—'
  const d = new Date(s)
  return `${d.toLocaleDateString('es-BO')} ${d.toLocaleTimeString('es-BO', { hour: '2-digit', minute: '2-digit' })}`
}

const accionesDe = (ot) => ACCIONES_POR_ESTADO[getEstadoNombre(ot.estado_id)] || []

const abrirFlujo = async (ot) => {
  try {
    const res = await apiClient.get(`/ordenes/${ot.id}`)
    flowOT.value = res.data
  } catch {
    flowOT.value = ot
  }
  flowAccion.value = null
  flowForm.value = {
    tecnico_asignado_id: flowOT.value.tecnico_asignado_id || null,
    comentario: '',
    acciones_realizadas: '',
    tiempo_real_invertido: null,
    unidad_tiempo: flowOT.value.unidad_tiempo || 'horas'
  }
  // v1.1.1: reset de repuestos/costos del flujo
  flowRepuestos.value = []
  flowRepuestoId.value = null
  flowRepuestoCantidad.value = 1
  flowCostos.value = []
  flowCostoForm.value = { tipo_costo: 'Transporte', descripcion_costo: '', monto_costo: null }
  // v1.1.1: repuestos ya cargados para el selector (si no están)
  if (!listaRepuestos.value.length) {
    try {
      const resRep = await apiClient.get('/repuestos/')
      listaRepuestos.value = resRep.data
    } catch { /* sin catálogo: el selector queda vacío */ }
  }
  showFlowModal.value = true
}

const seleccionarAccion = (a) => { flowAccion.value = a }

const ejecutarAccion = async () => {
  const a = flowAccion.value
  const otId = flowOT.value.id
  const f = flowForm.value
  let payload = { usuario: usuarioActual }
  let url = ''

  // v1.1.1: repuestos/costos del flujo (solo reanudar/resolver)
  const incluyeRC = (a === 'reanudar' || a === 'resolver')
  if (incluyeRC) {
    if (flowRepuestos.value.length) payload.repuestos_utilizados = flowRepuestos.value.map(i => ({ repuesto_id: i.repuesto_id, cantidad: i.cantidad }))
    if (flowCostos.value.length) payload.costos_adicionales = flowCostos.value.map(c => ({ tipo_costo: c.tipo_costo, descripcion_costo: c.descripcion_costo, monto_costo: c.monto_costo }))
  }

  if (a === 'asignar') {
    if (!f.tecnico_asignado_id) return alert('Seleccione un técnico')
    url = `/ordenes/${otId}/asignar`
    payload = { ...payload, tecnico_asignado_id: f.tecnico_asignado_id, comentario: f.comentario || null }
  } else if (a === 'iniciar' || a === 'reanudar') {
    url = `/ordenes/${otId}/${a}`
    payload = { ...payload, comentario: f.comentario || null }
  } else if (a === 'pausar' || a === 'cancelar') {
    if (!f.comentario || !f.comentario.trim()) return alert('El comentario/motivo es obligatorio')
    url = `/ordenes/${otId}/${a}`
    payload = { ...payload, comentario: f.comentario }
  } else if (a === 'reincidencia') {
    // v1.1.1: la OT cerrada es inmutable → se genera una OT NUEVA vinculada
    if (!f.comentario || !f.comentario.trim()) return alert('Indique el motivo de la reincidencia (qué volvió a fallar)')
    url = `/ordenes/${otId}/reincidencia`
    payload = { ...payload, comentario: f.comentario }
  } else if (a === 'resolver') {
    if (!f.acciones_realizadas || !f.acciones_realizadas.trim()) return alert('Describa las acciones realizadas (obligatorio — R3)')
    const t = parseFloat(f.tiempo_real_invertido)
    if (!t || t <= 0) return alert('Indique el tiempo real invertido, mayor que 0 (R3)')
    url = `/ordenes/${otId}/resolver`
    payload = { ...payload, acciones_realizadas: f.acciones_realizadas, tiempo_real_invertido: t, unidad_tiempo: f.unidad_tiempo, comentario: f.comentario || null }
  } else return

  flowBusy.value = true
  try {
    const res = await apiClient.post(url, payload)
    if (a === 'reincidencia') {
      alert(`🔁 OT de reincidencia #${res.data.id} creada (secuencia de falla: ${res.data.failure_sequence}). Nace Abierta y hereda técnico y datos.`)
    } else {
      alert('Acción aplicada correctamente: ' + a)
    }
    showFlowModal.value = false
    fetchData()
  } catch (e) {
    alert(errMsg(e, 'Error al aplicar la acción'))
  } finally {
    flowBusy.value = false
  }
}

onMounted(async () => {
  await fetchData()
  // v1.1.1: apertura directa del modal ⚡ desde el Calendario (/ordenes?ot=ID)
  const otQ = Number(route.query.ot)
  if (otQ) {
    const ot = ordenes.value.find(o => o.id === otQ)
    if (ot) {
      abrirFlujo(ot)
    } else {
      alert(`La OT #${otQ} del calendario no existe (puede haber sido eliminada)`)
    }
  }
})
</script>

<template>
  <div class="dashboard-container">

    <main class="content">
      <div class="top-bar">
        <h2>Listado de Órdenes de Trabajo</h2>
        <div class="top-bar-actions">
          <div class="search-wrapper">
            <svg class="search-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
              <path d="M11.742 10.344a6.5 6.5 0 1 0-1.397 1.398h-.001c.03.04.062.078.098.115l3.85 3.85a1 1 0 0 0 1.415-1.414l-3.85-3.85a1.007 1.007 0 0 0-.115-.1zM12 6.5a5.5 5.5 0 1 1-11 0 5.5 5.5 0 0 1 11 0z"/>
            </svg>
            <input v-model="searchQuery" type="search" class="search-input" placeholder="Titulo, equipo, ID..." autocomplete="off">
          </div>
          <button class="btn-primary btn-icon-only" @click="openCreateModal" title="Nueva Orden">+</button>
        </div>
      </div>

      <div class="filter-bar">
        <div class="filter-group">
          <label class="filter-label">Tipo:</label>
          <select v-model="filterTipo" class="filter-select"><option value="">Todos</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Prioridad:</label>
          <select v-model="filterPrioridad" class="filter-select"><option value="">Todas</option><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Estado:</label>
          <select v-model="filterEstado" class="filter-select"><option value="">Todos</option><option v-for="est in estadosOT" :key="est.id" :value="est.id">{{ est.nombre_estado }}</option></select>
        </div>
        <div class="filter-group">
          <label class="filter-label">Orden:</label>
          <select v-model="sortOrder" class="filter-select"><option value="desc">↓ Nuevas primero</option><option value="asc">↑ Viejas primero</option></select>
        </div>
        <button v-if="filterTipo || filterPrioridad || filterEstado" class="btn-clear-filters" @click="filterTipo = ''; filterPrioridad = ''; filterEstado = ''">Limpiar filtros</button>
      </div>

      <div v-if="loading">Cargando...</div>

      <table v-if="!loading && ordenes.length">
        <thead><tr><th>ID</th><th>Equipo</th><th>Título</th><th>Prioridad</th><th>Estado</th><th>Fecha / Hora</th><th>Vence</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr v-for="ot in paginatedOrdenes" :key="ot.id">
            <td>#{{ ot.id }}</td>
            <td>{{ getEquipoNombre(ot.equipo_id) }}</td>
            <td><strong>{{ getOrigenIcon(ot) }} {{ ot.titulo }}</strong><br><small>{{ ot.descripcion_falla.substring(0, 30) }}...</small></td>
            <td><span class="badge" :class="prioridadClass(ot.prioridad)">{{ ot.prioridad }}</span></td>
            <td><span class="badge" :style="{ backgroundColor: getEstadoColor(ot.estado_id) }">{{ estadosOT.find(e => e.id === ot.estado_id)?.nombre_estado || 'N/A' }}</span></td>
            <td><small>{{ formatFechaHora(ot) }}</small></td>
            <td><small :class="{ 'vencida': isVencida(ot) }">{{ ot.fecha_vencimiento ? formatFecha(ot.fecha_vencimiento) : '—' }}</small></td>
            <td class="actions-cell">
              <button class="btn-icon btn-flow" title="Acciones de Flujo (estado)" @click="abrirFlujo(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.52.359A.5.5 0 0 1 6 0h4a.5.5 0 0 1 .474.658L8.694 6H12.5a.5.5 0 0 1 .395.807l-7 9a.5.5 0 0 1-.873-.454L6.823 9.5H3.5a.5.5 0 0 1-.48-.641l2.5-8.5z"/></svg></button>
              <button class="btn-icon btn-view" title="Ver Detalles" @click="openViewModal(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M16 8s-3-5.5-8-5.5S0 8 0 8s3 5.5 8 5.5S16 8 16 8zM8 11a3 3 0 1 1 0-6 3 3 0 0 1 0 6z"/></svg></button>
              <button class="btn-icon btn-edit" :title="isOTCerrada(ot) ? 'OT cerrada (solo lectura)' : 'Editar'" :disabled="isOTCerrada(ot)" @click="openEditModal(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168l10-10zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207 11.207 2.5zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293l6.5-6.5zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325z"/></svg></button>
              <button class="btn-icon btn-delete" title="Eliminar" @click="deleteOrden(ot.id)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/><path fill-rule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/></svg></button>
              <button class="btn-icon btn-doc" title="Documentos Adjuntos" @click="openDocsModal(ot)"><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16"><path d="M9.293 0H4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V4.707A1 1 0 0 0 13.707 4L10 .293A1 1 0 0 0 9.293 0zM9.5 3.5v-2l3 3h-2a1 1 0 0 1-1-1z"/></svg></button>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="!loading && ordenes.length" class="table-pagination" role="navigation" aria-label="Paginación del listado de órdenes">
        <button type="button" class="btn-pagination" :disabled="currentPage <= 1" @click="irPaginaAnterior">Anterior</button>
        <span class="table-pagination-meta">Página {{ currentPage }} de {{ totalPages }}</span>
        <button type="button" class="btn-pagination" :disabled="currentPage >= totalPages" @click="irPaginaSiguiente">Siguiente</button>
      </div>
    </main>

    <!-- ==================== Modal Crear OT ==================== -->
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal modal-wide modal-xl">
        <h3>Nueva Orden de Trabajo</h3>
        <!-- v1.1.1: bloqueo suave — aviso de OTs activas del equipo -->
        <div v-if="activasDelEquipoSeleccionado.length" class="aviso-ot-activas">
          ⚠ Este equipo ya tiene <strong>{{ activasDelEquipoSeleccionado.length }}</strong> OT activa(s):
          <span v-for="(o, i) in activasDelEquipoSeleccionado" :key="o.id">{{ i ? ', ' : '' }}#{{ o.id }} ({{ getEstadoNombre(o.estado_id) }})</span>.
          Podrás crear otra solo si lo confirmas al guardar.
        </div>
        <form @submit.prevent="saveOrden">
          <div class="detail-tables">
            <div class="detail-table-block">
              <h4>Asignación</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Equipo Afectado *</td><td><select v-model="formData.equipo_id" class="detail-field" required><option value="" disabled>Seleccione...</option><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}{{ eq.numero_serie ? ' — ' + eq.numero_serie : '' }}</option></select></td></tr>
                <tr><td class="detail-label">Estado inicial</td><td><span class="badge" style="background:#3b82f6">Abierta</span><small class="nota-flujo">&nbsp;Toda OT nace "Abierta" (R1). Avance con el botón ⚡ de la fila.</small></td></tr>
                <tr><td class="detail-label">Prioridad</td><td><select v-model="formData.prioridad" class="detail-field"><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select></td></tr>
                <tr><td class="detail-label">Técnico Asignado</td><td><select v-model="formData.tecnico_asignado_id" class="detail-field"><option :value="null">-- Sin Asignar --</option><option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">{{ tec.full_name || tec.username }}</option></select></td></tr>
              </tbody></table>
            </div>
            <div class="detail-table-block">
              <h4>Tipo y Tiempos</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Título / Tipo *</td><td><select v-model="formData.titulo" class="detail-field" required><option value="" disabled>Seleccione tipo...</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select></td></tr>
                <tr><td class="detail-label">Fecha / Hora</td><td><input v-model="formData.fecha_creacion" type="datetime-local" class="detail-field"></td></tr>
                <tr><td class="detail-label">Tiempo Invertido</td><td><div class="field-inline"><input v-model="formData.tiempo_real_invertido" type="number" step="0.5" min="0" class="detail-field" placeholder="Ej: 1.5"><select v-model="formData.unidad_tiempo" class="detail-field" style="width: 100px;"><option value="horas">Horas</option><option value="dias">Días</option></select></div></td></tr>
              </tbody></table>
            </div>
          </div>
          <div class="detail-descriptions">
            <div class="desc-col"><strong>Descripción / Falla *</strong><textarea v-model="formData.descripcion_falla" required rows="3" class="detail-field detail-textarea" placeholder="Describa la falla reportada..."></textarea></div>
            <div class="desc-col"><strong>Acciones Realizadas</strong><textarea v-model="formData.acciones_realizadas" rows="3" class="detail-field detail-textarea" placeholder="Describa la reparación..."></textarea></div>
          </div>
          <div class="costos-repuestos-row">
            <div class="cr-col">
              <div class="costos-section">
                <div class="costo-form-inline">
                  <div class="cr-field" style="flex: 3;"><label>Costos Adicionales</label><input v-model="costoForm.descripcion_costo" type="text" class="detail-field" placeholder="Descripción del costo"></div>
                  <div class="cr-field"><label>Tipo</label><select v-model="costoForm.tipo_costo" class="detail-field"><option v-for="t in tiposCosto" :key="t" :value="t">{{ t }}</option></select></div>
                  <div class="cr-field" style="flex: 0.5;"><label>Monto</label><input v-model="costoForm.monto_costo" type="number" step="0.01" min="0" class="detail-field" placeholder="0.00"></div>
                  <div class="cr-field" style="flex: 0 0 25%;"><button type="button" class="btn-add-costo" @click="addCostoToOT">+ Agregar</button></div>
                </div>
                <ul class="costo-lista" v-if="costosAdicionales.length">
                  <li v-for="(c, idx) in costosAdicionales" :key="idx"><span class="costo-tipo">{{ c.tipo_costo }}</span><span class="costo-desc">{{ c.descripcion_costo }}</span><span class="costo-monto">Bs. {{ Number(c.monto_costo).toFixed(2) }}</span><button type="button" class="costo-remove" @click="removeCostoFromOT(idx)" title="Quitar costo">×</button></li>
                  <li class="costo-total"><span>Total:</span><span class="costo-monto-total">Bs. {{ totalCostos.toFixed(2) }}</span></li>
                </ul>
                <p v-else class="costo-empty">No hay costos agregados.</p>
              </div>
            </div>
            <div class="cr-col">
              <h4 class="section-title">Repuestos Utilizados</h4>
              <div class="repuestos-section">
                <div class="repuesto-selector">
                  <select v-model="selectedRepuestoId" class="detail-field"><option :value="null">Seleccionar...</option><option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">{{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})</option></select>
                  <input type="number" v-model="selectedCantidad" min="1" class="detail-field" style="width: 80px;">
                  <button type="button" class="btn-add-repuesto" @click="addRepuestoToOT">Agregar</button>
                </div>
                <ul class="repuesto-lista" v-if="repuestosSeleccionados.length"><li v-for="(item, idx) in repuestosSeleccionados" :key="idx">{{ item.cantidad }} x {{ item.nombre }}</li></ul>
                <p v-else class="repuesto-empty">No hay repuestos agregados.</p>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn-primary">Crear</button>
            <button type="button" class="btn-secondary" @click="showModal = false">Cancelar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- ==================== MODAL VER ==================== -->
    <div v-if="showViewModal" class="modal-overlay" @click.self="showViewModal = false">
      <div class="modal modal-wide">
        <h3>Detalle de Orden #{{ selectedOT.id }}</h3>
        <div class="detail-tables">
          <div class="detail-table-block">
            <h4>Información General</h4>
            <table class="detail-table"><tbody>
              <tr><td class="detail-label">Equipo</td><td>{{ getEquipoNombre(selectedOT.equipo_id) }}</td></tr>
              <tr><td class="detail-label">Título / Tipo</td><td>{{ selectedOT.titulo }}</td></tr>
              <tr><td class="detail-label">Prioridad</td><td><span class="badge" :class="prioridadClass(selectedOT.prioridad)">{{ selectedOT.prioridad }}</span></td></tr>
              <tr><td class="detail-label">Estado</td><td><span class="badge" :style="{ backgroundColor: getEstadoColor(selectedOT.estado_id) }">{{ estadosOT.find(e => e.id === selectedOT.estado_id)?.nombre_estado }}</span></td></tr>
              <tr v-if="selectedOT.orden_preventiva_id"><td class="detail-label">Origen</td><td><span class="badge badge-preventivo">Preventivo #{{ selectedOT.orden_preventiva_id }}</span></td></tr>
              <tr v-if="selectedOT.parent_ot_id"><td class="detail-label">Reincidencia</td><td><span class="badge" style="background:#0d9488">🔁 de la OT #{{ selectedOT.parent_ot_id }}</span></td></tr>
              <tr v-if="selectedOT.failure_sequence > 1"><td class="detail-label">Secuencia de falla</td><td><strong>{{ selectedOT.failure_sequence }}</strong> <small class="nota-flujo">(detectar fallas crónicas)</small></td></tr>
              <tr><td class="detail-label">Vence</td><td><span :class="{ 'vencida': isVencida(selectedOT) }">{{ selectedOT.fecha_vencimiento ? formatFecha(selectedOT.fecha_vencimiento) : '—' }}</span></td></tr>
            </tbody></table>
          </div>
          <div class="detail-table-block">
            <h4>Asignación y Tiempos</h4>
            <table class="detail-table"><tbody>
              <tr><td class="detail-label">Técnico</td><td>{{ getTecnicoNombre(selectedOT.tecnico_asignado_id) }}</td></tr>
              <tr><td class="detail-label">Fecha Creación</td><td>{{ selectedOT.fecha_creacion ? formatFechaHora(selectedOT) : 'N/A' }}</td></tr>
              <tr><td class="detail-label">Asignación</td><td>{{ fmtDT(selectedOT.fecha_asignacion) }}</td></tr>
              <tr><td class="detail-label">Inicio de trabajo</td><td>{{ fmtDT(selectedOT.fecha_inicio_trabajo) }}</td></tr>
              <tr><td class="detail-label">Resolución</td><td>{{ fmtDT(selectedOT.fecha_resolucion) }}</td></tr>
              <tr><td class="detail-label">Tiempo Invertido</td><td>{{ selectedOT.tiempo_real_invertido || 0 }} {{ selectedOT.unidad_tiempo === 'dias' ? 'días' : 'horas' }}</td></tr>
            </tbody></table>
          </div>
        </div>
        <div class="detail-descriptions">
          <div class="desc-col"><strong>Descripción de Falla</strong><div class="description-box">{{ selectedOT.descripcion_falla }}</div></div>
          <div v-if="selectedOT.acciones_realizadas" class="desc-col"><strong>Acciones Realizadas</strong><div class="description-box">{{ selectedOT.acciones_realizadas }}</div></div>
        </div>
        <div class="detail-section-title">Costos Adicionales ({{ detalleCostos.length }})</div>
        <div v-if="!detalleCostos.length" class="empty-section">Sin costos registrados.</div>
        <table v-else class="detail-table detail-table-full">
          <thead><tr><th class="detail-th">Tipo</th><th class="detail-th">Descripción</th><th class="detail-th">Monto</th></tr></thead>
          <tbody>
            <tr v-for="c in detalleCostos" :key="c.id"><td><span class="badge" style="background: #7c3aed; font-size: 0.72rem; padding: 1px 8px; border-radius: 10px;">{{ c.tipo_costo }}</span></td><td>{{ c.descripcion_costo }}</td><td style="font-weight: 700; color: #5b21b6; white-space: nowrap;">Bs. {{ Number(c.monto_costo).toFixed(2) }}</td></tr>
            <tr style="background: #ede9fe; border-top: 2px solid #7c3aed;"><td colspan="2" style="font-weight: 700; text-align: right; padding: 0.4rem 0.6rem;">Total:</td><td style="font-weight: 700; color: #5b21b6; font-size: 1rem; padding: 0.4rem 0.6rem;">Bs. {{ totalDetalleCostos.toFixed(2) }}</td></tr>
          </tbody>
        </table>
        <div class="detail-section-title">Repuestos Utilizados</div>
        <div v-if="!selectedOT.repuestos_usados || !selectedOT.repuestos_usados.length" class="empty-section">Sin repuestos registrados.</div>
        <table v-else class="detail-table detail-table-full">
          <thead><tr><th class="detail-th">Cantidad</th><th class="detail-th">Repuesto</th></tr></thead>
          <tbody><tr v-for="rep in selectedOT.repuestos_usados" :key="rep.repuesto_id"><td>{{ rep.cantidad_utilizada }} x</td><td>{{ getRepuestoNombre(rep.repuesto_id) }}</td></tr></tbody>
        </table>
        <div class="detail-section-title">Bitácora del flujo ({{ bitacoraOT.length }}) — trazabilidad R4</div>
        <div v-if="!bitacoraOT.length" class="empty-section">Sin registros de bitácora (OT anterior a la v1.1.0).</div>
        <ul v-else class="bitacora-lista">
          <li v-for="b in bitacoraOT" :key="b.id">
            <span class="bitacora-fecha">{{ fmtDT(b.fecha) }}</span>
            <span class="bitacora-accion">{{ b.accion }}</span>
            <span class="bitacora-usuario">{{ b.usuario || 'sistema' }}</span>
            <span v-if="b.estado_anterior || b.estado_nuevo" class="bitacora-estado">{{ b.estado_anterior || '—' }} → {{ b.estado_nuevo || '—' }}</span>
            <span v-if="b.comentario" class="bitacora-comentario">{{ b.comentario }}</span>
          </li>
        </ul>
        <div class="modal-actions" style="justify-content: space-between; flex-wrap: wrap; gap: .5rem;">
          <div style="display:flex; gap:.5rem; flex-wrap:wrap;">
            <button class="btn-secondary" style="background:#0d9488" @click="exportBitacoraOT" title="CSV con fecha, acción, usuario y comentarios de esta OT">📤 Bitácora de la OT (CSV)</button>
            <button class="btn-secondary" style="background:#475569" @click="exportBitacoraEquipo" title="Bitácora de TODAS las OTs de este equipo">📤 Bitácora del equipo (CSV)</button>
          </div>
          <button class="btn-secondary" @click="showViewModal = false">Cerrar</button>
        </div>
      </div>
    </div>

    <!-- ==================== MODAL ACCIONES DE FLUJO (v1.1.1) ==================== -->
    <div v-if="showFlowModal && flowOT" class="modal-overlay" @click.self="showFlowModal = false">
      <div class="modal modal-wide">
        <h3>Acciones de Flujo — OT #{{ flowOT.id }}</h3>
        <div class="flow-head">
          <span class="badge" :style="{ backgroundColor: getEstadoColor(flowOT.estado_id) }">{{ getEstadoNombre(flowOT.estado_id) }}</span>
          <strong>{{ flowOT.titulo }}</strong>
          <span>{{ getEquipoNombre(flowOT.equipo_id) }}</span>
          <span v-if="flowOT.tecnico_asignado_id" class="flow-tec">👤 {{ getTecnicoNombre(flowOT.tecnico_asignado_id) }}</span>
          <span v-if="flowOT.parent_ot_id || flowOT.failure_sequence > 1" class="badge" style="background:#0d9488" title="Cadena de reincidencias (v1.1.1)">🔁 secuencia {{ flowOT.failure_sequence }}</span>
        </div>
        <p v-if="flowOT.parent_ot_id" class="nota-flujo">🔁 Reincidencia de la <strong>OT #{{ flowOT.parent_ot_id }}</strong> — secuencia de falla {{ flowOT.failure_sequence }} del mismo equipo.</p>

        <!-- v1.1.1: contexto de la OT (solo lectura) para decidir la acción -->
        <div class="detail-descriptions" style="margin-bottom:0.75rem">
          <div class="desc-col"><strong>Descripción de la falla</strong><div class="description-box">{{ flowOT.descripcion_falla || '—' }}</div></div>
          <div v-if="flowOT.acciones_realizadas" class="desc-col"><strong>Acciones ya realizadas</strong><div class="description-box">{{ flowOT.acciones_realizadas }}</div></div>
        </div>

        <p class="nota-flujo">El estado solo cambia mediante estas acciones (máquina de estados R2). Toda acción queda registrada en la bitácora (R4). Una OT cerrada es definitiva: la re-intervención genera una OT nueva vinculada.</p>

        <div class="flow-acciones">
          <button v-for="a in accionesDe(flowOT)" :key="a" type="button" class="flow-btn" :class="{ 'flow-btn--activa': flowAccion === a }" @click="seleccionarAccion(a)">
            {{ META_ACCIONES[a].label }}
          </button>
          <span v-if="!accionesDe(flowOT).length" class="empty-section">Sin acciones disponibles para este estado.</span>
        </div>

        <div v-if="flowAccion" class="flow-form">
          <p class="flow-desc">{{ META_ACCIONES[flowAccion].desc }}</p>

          <div v-if="flowAccion === 'asignar'" class="flow-field">
            <label>Técnico *</label>
            <select v-model="flowForm.tecnico_asignado_id" class="detail-field">
              <option :value="null" disabled>Seleccione técnico...</option>
              <option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">{{ tec.full_name || tec.username }}</option>
            </select>
            <label style="margin-top:.5rem">Comentario (opcional)</label>
            <input v-model="flowForm.comentario" type="text" class="detail-field" placeholder="Ej: reasignado por disponibilidad">
          </div>

          <div v-else-if="flowAccion === 'iniciar' || flowAccion === 'reanudar'" class="flow-field">
            <label>Comentario (opcional)</label>
            <input v-model="flowForm.comentario" type="text" class="detail-field" placeholder="Ej: inicio de intervención en sitio">
          </div>

          <div v-else-if="flowAccion === 'pausar' || flowAccion === 'cancelar'" class="flow-field">
            <label>{{ flowAccion === 'pausar' ? 'Motivo de la pausa *' : 'Motivo de la cancelación *' }}</label>
            <textarea v-model="flowForm.comentario" rows="2" class="detail-field detail-textarea" :placeholder="flowAccion === 'pausar' ? 'Ej: espera repuesto kit de bobinas' : 'Explique brevemente el motivo (R7)'" style="min-height:60px"></textarea>
          </div>

          <div v-else-if="flowAccion === 'reincidencia'" class="flow-field">
            <label>Motivo de la reincidencia * (¿qué volvió a fallar?)</label>
            <textarea v-model="flowForm.comentario" rows="2" class="detail-field detail-textarea" placeholder="Ej: recae el mismo síntoma tras 5 días de uso" style="min-height:60px"></textarea>
            <small class="nota-flujo">La OT #{{ flowOT.id }} permanece cerrada e inmutable. Se creará una OT NUEVA (nace Abierta, secuencia de falla {{ (flowOT.failure_sequence || 1) + 1 }}) que hereda equipo, tipo, prioridad, técnico y descripción.</small>
          </div>

          <div v-else-if="flowAccion === 'resolver'" class="flow-field">
            <label>Acciones realizadas (solución aplicada) *</label>
            <textarea v-model="flowForm.acciones_realizadas" rows="3" class="detail-field detail-textarea" placeholder="Describa la reparación/solución..."></textarea>
            <div class="field-inline" style="margin-top:.5rem">
              <div style="flex:1">
                <label>Tiempo real invertido *</label>
                <input v-model="flowForm.tiempo_real_invertido" type="number" step="0.5" min="0.5" class="detail-field" placeholder="Ej: 1.5">
              </div>
              <div>
                <label>Unidad</label>
                <select v-model="flowForm.unidad_tiempo" class="detail-field" style="width:100px"><option value="horas">Horas</option><option value="dias">Días</option></select>
              </div>
            </div>
            <label style="margin-top:.5rem">Comentario (opcional)</label>
            <input v-model="flowForm.comentario" type="text" class="detail-field">
          </div>

          <!-- v1.1.1 (R8): repuestos del almacén + costos DENTRO del flujo -->
          <div v-if="flowAccion === 'reanudar' || flowAccion === 'resolver'" class="costos-repuestos-row" style="margin-top:.9rem">
            <div class="cr-col">
              <h4 class="section-title">Repuestos entregados (almacén) — opcional</h4>
              <div class="repuesto-selector">
                <select v-model="flowRepuestoId" class="detail-field"><option :value="null">Seleccionar...</option><option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">{{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})</option></select>
                <input type="number" v-model="flowRepuestoCantidad" min="1" class="detail-field" style="width: 80px;">
                <button type="button" class="btn-add-repuesto" @click="addFlowRepuestoToOT">Agregar</button>
              </div>
              <ul class="repuesto-lista" v-if="flowRepuestos.length"><li v-for="(item, idx) in flowRepuestos" :key="idx">{{ item.cantidad }} x {{ item.nombre }}<button type="button" class="costo-remove" @click="removeFlowRepuesto(idx)" title="Quitar">×</button></li></ul>
              <p v-else class="repuesto-empty">Sin repuestos del flujo. Se descuentan del almacén al confirmar.</p>
            </div>
            <div class="cr-col">
              <h4 class="section-title">Costos adicionales — opcional</h4>
              <div class="costo-form-inline">
                <div class="cr-field" style="flex: 3;"><input v-model="flowCostoForm.descripcion_costo" type="text" class="detail-field" placeholder="Descripción del costo"></div>
                <div class="cr-field"><select v-model="flowCostoForm.tipo_costo" class="detail-field"><option v-for="t in tiposCosto" :key="t" :value="t">{{ t }}</option></select></div>
                <div class="cr-field" style="flex: 0.5;"><input v-model="flowCostoForm.monto_costo" type="number" step="0.01" min="0" class="detail-field" placeholder="0.00"></div>
                <div class="cr-field" style="flex: 0 0 18%;"><button type="button" class="btn-add-costo" @click="addFlowCostoToOT">+ Agregar</button></div>
              </div>
              <ul class="costo-lista" v-if="flowCostos.length">
                <li v-for="(c, idx) in flowCostos" :key="idx"><span class="costo-tipo">{{ c.tipo_costo }}</span><span class="costo-desc">{{ c.descripcion_costo }}</span><span class="costo-monto">Bs. {{ Number(c.monto_costo).toFixed(2) }}</span><button type="button" class="costo-remove" @click="removeFlowCosto(idx)" title="Quitar costo">×</button></li>
                <li class="costo-total"><span>Total:</span><span class="costo-monto-total">Bs. {{ totalFlowCostos.toFixed(2) }}</span></li>
              </ul>
              <p v-else class="costo-empty">No hay costos agregados.</p>
            </div>
          </div>

          <div class="modal-actions">
            <button type="button" class="btn-primary" :disabled="flowBusy" @click="ejecutarAccion">{{ flowBusy ? 'Aplicando…' : (flowAccion === 'reincidencia' ? 'Crear OT de reincidencia' : 'Confirmar acción') }}</button>
            <button type="button" class="btn-secondary" @click="flowAccion = null">Volver</button>
          </div>
        </div>
        <div class="modal-actions"><button class="btn-secondary" @click="showFlowModal = false">Cerrar</button></div>
      </div>
    </div>

    <!-- ==================== MODAL EDITAR ==================== -->
    <div v-if="showEditModal" class="modal-overlay" @click.self="showEditModal = false">
      <div class="modal modal-wide modal-xl">
        <h3>Editar OT #{{ selectedOT.id }} <small class="nota-flujo">(el estado se modifica con Acciones de Flujo ⚡)</small></h3>
        <form @submit.prevent="updateOrden">
          <div class="detail-tables">
            <div class="detail-table-block">
              <h4>Asignación</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Equipo Afectado *</td><td><select v-model="editFormData.equipo_id" class="detail-field" required><option value="" disabled>Seleccione...</option><option v-for="eq in equipos" :key="eq.id" :value="eq.id">{{ eq.nombre_corto || eq.modelo }}{{ eq.numero_serie ? ' — ' + eq.numero_serie : '' }}</option></select></td></tr>
                <tr><td class="detail-label">Estado</td><td><span class="badge" :style="{ backgroundColor: getEstadoColor(selectedOT.estado_id) }">{{ getEstadoNombre(selectedOT.estado_id) }}</span><small class="nota-flujo">&nbsp;Se modifica solo con Acciones de Flujo (botón ⚡).</small></td></tr>
                <tr><td class="detail-label">Prioridad</td><td><select v-model="editFormData.prioridad" class="detail-field"><option>Urgente</option><option>Alta</option><option>Media</option><option>Baja</option></select></td></tr>
                <tr><td class="detail-label">Técnico Asignado</td><td><select v-model="editFormData.tecnico_asignado_id" class="detail-field"><option :value="null">-- Sin Asignar --</option><option v-for="tec in tecnicos" :key="tec.id" :value="tec.id">{{ tec.full_name || tec.username }}</option></select></td></tr>
              </tbody></table>
            </div>
            <div class="detail-table-block">
              <h4>Tipo y Tiempos</h4>
              <table class="detail-table"><tbody>
                <tr><td class="detail-label">Título / Tipo</td><td><select v-if="selectedOT.orden_preventiva_id" disabled class="detail-field" style="background: #f8fafc; color: #64748b; cursor: not-allowed;"><option value="Preventivo" selected>Preventivo</option></select><select v-else v-model="editFormData.titulo" class="detail-field" required><option value="" disabled>Seleccione tipo...</option><option v-for="t in tiposOT" :key="t" :value="t">{{ t }}</option></select></td></tr>
                <tr><td class="detail-label">Fecha / Hora</td><td><input v-model="editFormData.fecha_creacion" type="datetime-local" class="detail-field"></td></tr>
                <tr><td class="detail-label">Tiempo Invertido</td><td><div class="field-inline"><input v-model="editFormData.tiempo_real_invertido" type="number" step="0.5" min="0" class="detail-field" placeholder="Ej: 1.5"><select v-model="editFormData.unidad_tiempo" class="detail-field" style="width: 100px;"><option value="horas">Horas</option><option value="dias">Días</option></select></div></td></tr>
              </tbody></table>
            </div>
          </div>
          <div class="detail-descriptions">
            <div class="desc-col"><strong>Descripción / Falla *</strong><textarea v-model="editFormData.descripcion_falla" required rows="3" class="detail-field detail-textarea" placeholder="Describa la falla..."></textarea></div>
            <div class="desc-col"><strong>Acciones Realizadas</strong><textarea v-model="editFormData.acciones_realizadas" rows="3" class="detail-field detail-textarea" placeholder="Describa la reparación..."></textarea></div>
          </div>
          <div class="costos-repuestos-row">
            <div class="cr-col">
              <div class="costos-section">
                <div class="costo-form-inline">
                  <div class="cr-field" style="flex: 3;"><label>Costos Adicionales</label><input v-model="editCostoForm.descripcion_costo" type="text" class="detail-field" placeholder="Descripción del costo"></div>
                  <div class="cr-field"><label>Tipo</label><select v-model="editCostoForm.tipo_costo" class="detail-field"><option v-for="t in tiposCosto" :key="t" :value="t">{{ t }}</option></select></div>
                  <div class="cr-field" style="flex: 0.5;"><label>Monto</label><input v-model="editCostoForm.monto_costo" type="number" step="0.01" min="0" class="detail-field" placeholder="0.00"></div>
                  <div class="cr-field" style="flex: 0 0 25%;"><button type="button" class="btn-add-costo" @click="addEditCostoToOT">+ Agregar</button></div>
                </div>
                <ul class="costo-lista" v-if="editCostosAdicionales.length">
                  <li v-for="(c, idx) in editCostosAdicionales" :key="idx"><span class="costo-tipo">{{ c.tipo_costo }}</span><span class="costo-desc">{{ c.descripcion_costo }}</span><span class="costo-monto">Bs. {{ Number(c.monto_costo).toFixed(2) }}</span><button type="button" class="costo-remove" @click="removeEditCostoFromOT(idx)" title="Quitar costo">×</button></li>
                  <li class="costo-total"><span>Total:</span><span class="costo-monto-total">Bs. {{ totalEditCostos.toFixed(2) }}</span></li>
                </ul>
                <p v-else class="costo-empty">No hay costos agregados.</p>
              </div>
            </div>
            <div class="cr-col">
              <h4 class="section-title">Repuestos Utilizados</h4>
              <div class="repuestos-section">
                <div class="repuesto-selector">
                  <select v-model="selectedRepuestoId" class="detail-field"><option :value="null">Seleccionar...</option><option v-for="rep in listaRepuestos" :key="rep.id" :value="rep.id">{{ rep.nombre_repuesto }} (Stock: {{ rep.cantidad_disponible }})</option></select>
                  <input type="number" v-model="selectedCantidad" min="1" class="detail-field" style="width: 80px;">
                  <button type="button" class="btn-add-repuesto" @click="addRepuestoToOT">Agregar</button>
                </div>
                <ul class="repuesto-lista" v-if="repuestosSeleccionados.length"><li v-for="(item, idx) in repuestosSeleccionados" :key="idx">{{ item.cantidad }} x {{ item.nombre }}</li></ul>
                <p v-else class="repuesto-empty">No hay repuestos agregados.</p>
              </div>
            </div>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn-primary">Guardar Cambios</button>
            <button type="button" class="btn-secondary" @click="showEditModal = false">Cancelar</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Modal Documentos Adjuntos -->
    <div v-if="showDocsModal" class="modal-overlay" @click.self="showDocsModal = false">
      <div class="modal modal-docs">
        <h3>Documentos - OT #{{ docsOT.id }} ({{ docsOT.titulo }})</h3>
        <DocumentosAdjuntos v-if="docsOT.id" :ordenTrabajoId="docsOT.id" />
        <div class="modal-actions"><button class="btn-secondary" @click="showDocsModal = false">Cerrar</button></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* === Layout General === */
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

/* === Top Bar === */
.top-bar { display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; margin-bottom: 1rem; gap: 0.75rem; }
.top-bar h2 { margin: 0; }
.top-bar-actions { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; }
.search-wrapper { position: relative; display: flex; align-items: center; min-width: 200px; flex: 1 1 180px; max-width: 320px; }
.search-icon { position: absolute; left: 10px; color: #94a3b8; pointer-events: none; z-index: 1; }
.search-input { width: 100%; padding: 0.55rem 0.85rem 0.55rem 2.2rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9rem; box-sizing: border-box; background: #fff; }
.search-input::placeholder { color: #94a3b8; }
.search-input:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52,152,219,0.2); }

/* === Barra de Filtros === */
.filter-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.65rem; margin-bottom: 1rem; padding: 0.75rem 1rem; background: white; border-radius: 8px; border: 1px solid #e2e8f0; }
.filter-group { display: flex; align-items: center; gap: 0.35rem; }
.filter-label { font-size: 0.82rem; font-weight: 600; color: #64748b; white-space: nowrap; }
.filter-select { padding: 0.35rem 0.6rem; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.82rem; background: #fff; color: #334155; min-width: 130px; max-width: 200px; }
.filter-select:focus { outline: none; border-color: #3498db; }
.btn-clear-filters { display: flex; align-items: center; gap: 0.3rem; padding: 0.35rem 0.7rem; border: 1px solid #fecaca; border-radius: 6px; background: #fef2f2; color: #dc2626; font-size: 0.78rem; font-weight: 600; cursor: pointer; transition: all 0.2s; }
.btn-clear-filters:hover { background: #fee2e2; }

/* === Tabla Principal === */
table { width: 100%; border-collapse: collapse; margin-top: 1rem; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
th { background-color: #f8f9fa; font-weight: bold; }

/* === Paginación === */
.table-pagination { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 1rem; margin-top: 1rem; padding: 0.75rem 0; }
.table-pagination-meta { font-size: 0.9rem; color: #475569; text-align: center; }
.btn-pagination { background-color: #3498db; color: white; border: none; padding: 0.5rem 1.1rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9rem; transition: background-color 0.2s ease, opacity 0.2s ease; }
.btn-pagination:hover:not(:disabled) { background-color: #2980b9; }
.btn-pagination:disabled { opacity: 0.45; cursor: not-allowed; }

/* === Botones === */
.btn-primary { background-color: #3498db; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; cursor: pointer; font-weight: bold; font-size: 1rem; }
.btn-primary:hover { background-color: #2980b9; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-secondary { background-color: #95a5a6; color: white; border: none; padding: 0.4rem 0.8rem; border-radius: 4px; cursor: pointer; font-size: 0.9rem; }
.btn-icon-only { width: 42px; height: 42px; padding: 0; display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 1.2rem; line-height: 1; }

/* === Badges === */
.badge { padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; color: white; font-weight: bold; }
.urgente { background-color: #e74c3c; }
.alta { background-color: #e67e22; }
.media { background-color: #f1c40f; color: #333; }
.badge-preventivo { background-color: #8b5cf6; color: white; font-size: 0.7rem; }

/* === Iconos de Acción === */
.actions-cell { display: flex; gap: 0.5rem; align-items: center; }
.btn-icon { background: #f0f2f5; color: #555; border: none; padding: 8px; border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.btn-view:hover { background: #16a34a; color: #ffffff; }
.btn-edit:hover { background: #2563eb; color: #ffffff; }
.btn-delete:hover { background: #dc2626; color: #ffffff; }
.btn-doc:hover { background: #0891b2; color: #ffffff; }

/* === Modales === */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; justify-content: center; align-items: center; z-index: 100; }
.modal { background: white; padding: 1.2rem 1.25rem; border-radius: 8px; width: 500px; max-width: 90%; max-height: 85vh; overflow-y: auto; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }
.modal-wide { width: min(980px, 96vw); }
.modal-xl { width: min(1040px, 96vw); }
.modal-docs { width: 650px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 1rem; margin-top: 1.5rem; }

/* === Detail Table (nuevo layout para modales crear/editar) === */
.detail-tables { display: flex; gap: 1.5rem; margin-bottom: 1.5rem; }
.detail-table-block { flex: 1; }
.detail-table-block h4 { margin-bottom: 0.6rem; color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 0.3rem; font-size: 0.95rem; }
.detail-table { width: 100%; border-collapse: collapse; }
.detail-table td { padding: 0.35rem 0.6rem; font-size: 0.88rem; border-bottom: 1px solid #eee; vertical-align: middle; }
.detail-table tr:last-child td { border-bottom: none; }
.detail-label { color: #666; font-weight: 600; width: 35%; white-space: nowrap; font-size: 0.8rem; padding-right: 0.35rem; }
.detail-field { width: 100%; padding: 0.45rem 0.55rem; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; background: #fff; font-size: 0.85rem; color: #334155; }
.detail-field:focus { outline: none; border-color: #3498db; box-shadow: 0 0 0 2px rgba(52, 152, 219, 0.16); }
.detail-textarea { min-height: 84px; resize: vertical; font-family: inherit; }
.field-inline { display: flex; gap: 0.4rem; align-items: stretch; }
.field-inline .detail-field { flex: 1; }

/* === Descripciones === */
.detail-descriptions { display: flex; gap: 1.5rem; margin-bottom: 1rem; }
.desc-col { flex: 1; }
.desc-col strong { display: block; margin-bottom: 0.25rem; color: #2c3e50; font-size: 0.85rem; }
.description-box { background: white; border: 1px solid #e0e0e0; border-radius: 4px; padding: 0.6rem; font-size: 0.85rem; color: #444; min-height: 50px; line-height: 1.5; word-break: break-word; overflow-y: auto; max-height: 150px; white-space: pre-wrap; }

/* === Sub-tablas en modal Ver === */
.detail-table-full { margin-bottom: 0.5rem; }
.detail-th { font-size: 0.78rem; color: #666; font-weight: 600; padding: 0.3rem 0.6rem; text-align: left; background: #f5f7fa; border-bottom: 1px solid #dde; }
.detail-section-title { font-size: 0.95rem; font-weight: 600; color: #2c3e50; margin-bottom: 0.5rem; margin-top: 0.8rem; }
.empty-section { text-align: center; padding: 1rem; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 6px; color: #64748b; font-size: 0.88rem; margin-bottom: 0.5rem; }

/* === Sección de Título === */
.section-title { margin: 1rem 0 0.5rem 0; padding: 0; font-size: 1rem; font-weight: 700; color: #1e293b; border: none; background: none; }

/* === Costos + Repuestos en la misma fila === */
.costos-repuestos-row { display: flex; gap: 1.25rem; }
.cr-col { flex: 1; min-width: 0; }
@media (max-width: 768px) { .costos-repuestos-row { flex-direction: column; } .detail-tables { flex-direction: column; } }

/* === Costos Adicionales === */
.costos-section { padding: 0; margin-top: 0.5rem; }
.costo-form-inline { display: flex; gap: 0.5rem; align-items: flex-end; margin-bottom: 0.75rem; flex-wrap: wrap; }
.cr-field { min-width: 100px; }
.cr-field label { display: block; font-size: 0.78rem; font-weight: 600; color: #64748b; margin-bottom: 0.2rem; }
.btn-add-costo { background: #7c3aed; color: white; border: none; padding: 0.55rem 0.8rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; white-space: nowrap; transition: background 0.2s; margin-top: 0.25rem; }
.btn-add-costo:hover { background: #6d28d9; }
.costo-lista { list-style: none; padding: 0; margin: 0; }
.costo-lista li { display: flex; align-items: center; gap: 0.5rem; padding: 6px 10px; background: #faf5ff; border-left: 3px solid #7c3aed; border-radius: 4px; margin-bottom: 4px; font-size: 0.85rem; color: #1e293b; flex-wrap: wrap; }
.costo-tipo { background: #7c3aed; color: white; padding: 1px 8px; border-radius: 10px; font-size: 0.72rem; font-weight: 700; white-space: nowrap; }
.costo-desc { flex: 1; min-width: 100px; }
.costo-monto { font-weight: 700; color: #5b21b6; white-space: nowrap; }
.costo-remove { background: #a78bfa; color: white; border: none; cursor: pointer; font-size: 0.85rem; line-height: 1; width: 20px; height: 20px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; padding: 0; transition: all 0.15s; flex-shrink: 0; }
.costo-remove:hover { background: #7c3aed; }
.costo-total { display: flex; justify-content: space-between; align-items: center; padding: 8px 10px !important; background: #ede9fe !important; border-left: 3px solid #7c3aed !important; font-weight: 700; margin-top: 6px !important; }
.costo-monto-total { color: #5b21b6; font-size: 1rem !important; }
.costo-empty { color: #78716c; font-style: italic; font-size: 0.85rem; margin: 0.5rem 0 0 0; }

/* === Repuestos === */
.repuestos-section { padding: 0; margin-top: 0.5rem; }
.repuesto-selector { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 10px; }
.repuesto-selector select { flex: 1; }
.btn-add-repuesto { background: #d97706; color: white; border: none; padding: 0.55rem 0.8rem; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; white-space: nowrap; transition: background 0.2s; }
.btn-add-repuesto:hover { background: #b45309; }
.repuesto-lista { list-style: none; padding: 0; margin-top: 8px; }
.repuesto-lista li { padding: 8px 12px; background: #fffbf0; border-left: 3px solid #d97706; border-bottom: 1px solid #fef3c7; font-size: 0.9rem; color: #1e293b; font-weight: 500; }
.repuesto-lista li:last-child { border-bottom: none; }
.repuesto-empty { color: #78716c; font-style: italic; font-size: 0.85rem; margin: 0.5rem 0 0 0; }

/* === v1.1.0 — Flujo de Trabajo OT === */
.nota-flujo { color: #64748b; font-size: 0.78rem; }
.vencida { color: #dc2626; font-weight: 700; }
.aviso-ot-activas { background: #fffbeb; border: 1px solid #f59e0b; color: #92400e; border-radius: 8px; padding: 0.6rem 0.9rem; font-size: 0.85rem; margin-bottom: 0.9rem; }
.btn-flow { background: #fff7ed; color: #c2410c; border: 1px solid #fdba74; }
.btn-flow:hover { background: #ffedd5; color: #9a3412; }
.btn-icon:disabled { opacity: 0.35; cursor: not-allowed; }
.flow-head { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.35rem; }
.flow-tec { color: #475569; font-size: 0.85rem; }
.flow-acciones { display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.75rem 0; }
.flow-btn { padding: 0.5rem 0.8rem; border: 2px solid #e2e8f0; border-radius: 8px; background: #fff; cursor: pointer; font-weight: 600; font-size: 0.85rem; color: #475569; transition: all 0.2s; }
.flow-btn:hover { border-color: #3b82f6; color: #2563eb; background: #eff6ff; }
.flow-btn--activa { border-color: #3b82f6; background: #3b82f6; color: #fff; }
.flow-form { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 0.9rem 1rem; }
.flow-desc { margin: 0 0 0.6rem; color: #475569; font-size: 0.85rem; }
.flow-field label { display: block; font-size: 0.8rem; font-weight: 600; color: #334155; margin-bottom: 0.2rem; }
.bitacora-lista { list-style: none; margin: 0; padding: 0; max-height: 260px; overflow: auto; }
.bitacora-lista li { display: flex; flex-wrap: wrap; gap: 0.4rem 0.7rem; align-items: baseline; padding: 0.45rem 0.2rem; border-bottom: 1px dashed #e2e8f0; font-size: 0.83rem; }
.bitacora-lista li:last-child { border-bottom: none; }
.bitacora-fecha { color: #64748b; font-variant-numeric: tabular-nums; min-width: 130px; }
.bitacora-accion { font-weight: 700; color: #1d4ed8; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.4px; background: #eff6ff; padding: 1px 8px; border-radius: 10px; }
.bitacora-usuario { color: #334155; font-weight: 600; }
.bitacora-estado { color: #b45309; }
.bitacora-comentario { width: 100%; color: #475569; padding-left: 1rem; border-left: 3px solid #e2e8f0; }
</style>