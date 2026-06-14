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
    emoji: '📊',
    nombre: 'Inicio (Dashboard)',
    ruta: '/inicio',
    descripcion: 'Panel principal con resumen general del sistema. Muestra metricas clave en tarjetas: total de equipos, ordenes pendientes, equipos en mantenimiento, repuestos con stock bajo y tareas preventivas vencidas. Incluye graficos interactivos de distribucion de equipos por estado, ordenes por prioridad y ordenes por estado. La seccion de Sugerencias del Sistema genera alertas automaticas basadas en reglas: equipos sin preventivo, stock bajo, preventivo vencido, OTs pendientes y calibraciones proximas.',
    funcionalidades: [
      '5 tarjetas de metricas en tiempo real',
      'Grafico Doughnut de equipos por estado',
      'Grafico de barras de ordenes por prioridad',
      'Grafico Doughnut de ordenes por estado',
      'Sugerencias automaticas con enlaces directos'
    ]
  },
  {
    emoji: '⚙️',
    nombre: 'Equipos',
    ruta: '/equipos',
    descripcion: 'Gestion completa de equipos biomédicos. Registro detallado con datos como modelo, numero de serie, marca, registro sanitario Bolivia, ubicacion, calibracion proxima, responsable tecnico y estado operativo. Permite subir una imagen principal por equipo y multiples documentos adjuntos (manuales, garantias, fotos, reportes). Soporta importacion masiva desde Excel/CSV con logica de upsert (actualiza si el numero de serie ya existe). Filtros combinados por estado, marca y busqueda de texto. Modal de detalle (OJO) con informacion completa, historial de mantenimiento y documentos.',
    funcionalidades: [
      'CRUD completo de equipos biomédicos',
      '19 estados predefinidos (Operativo, En mantenimiento, En calibracion, Bloqueado/LOTO, etc.)',
      'Imagen principal con vista previa',
      'Documentos adjuntos multiples por equipo',
      'Importacion masiva Excel/CSV con upsert',
      'Descarga de plantilla Excel/CSV',
      'Filtros combinados AND (estado + marca + texto)',
      'Historial de mantenimiento por equipo',
      'Asignacion de responsable tecnico'
    ]
  },
  {
    emoji: '🔧',
    nombre: 'Ordenes de Trabajo',
    ruta: '/ordenes',
    descripcion: 'Gestion de ordenes de trabajo para mantenimiento correctivo y preventivo. Cada OT se asocia a un equipo, tiene prioridad (Urgente, Alta, Media, Baja), estado (Abierta, En Proceso, Esp. Repuesto, Completada, Cancelada), tecnico asignado y fecha de vencimiento. Al completar una OT, se descuenta automaticamente el stock de repuestos utilizados y se genera un evento en el Historial. Si la OT proviene de una tarea preventiva, se actualizan automaticamente las fechas del ciclo preventivo.',
    funcionalidades: [
      'CRUD completo de ordenes de trabajo',
      '5 estados de OT con colores diferenciados',
      '4 niveles de prioridad',
      'Registro de repuestos utilizados por OT (descuento automatico de stock)',
      'Al completar OT: evento automatico en Historial',
      'Al completar OT preventiva: actualizacion automatica de fechas',
      'Acciones realizadas y tiempo invertido al cierre',
      'Registro de costos adicionales',
      'Documentos adjuntos por OT'
    ]
  },
  {
    emoji: '🔩',
    nombre: 'Inventario (Repuestos + Herramientas)',
    ruta: '/inventario',
    descripcion: 'Gestion de inventario dividida en dos pestanas: Repuestos y Herramientas. Los repuestos tienen datos tecnicos, especificaciones, stock minimo, proveedor y precio de referencia. Las herramientas tienen categoria (Manual, Electrica, Medicion, Seguridad), estado de uso y costo. Ambos soportan imagen principal, documentos adjuntos e importacion masiva desde Excel. El sistema genera alertas automaticas cuando el stock de un repuesto cae por debajo del nivel minimo configurado.',
    funcionalidades: [
      'Repuestos: CRUD con datos tecnicos y especificaciones',
      'Herramientas: CRUD con categorias y estado de uso',
      'Imagen principal y documentos adjuntos para ambos',
      'Importacion masiva Excel/CSV con upsert',
      'Alerta de stock bajo contra nivel minimo configurable',
      '4 categorias de herramientas: Manual, Electrica, Medicion, Seguridad',
      '4 estados de uso: Disponible, En uso, En reparacion, Dado de baja',
      'Precio de referencia y proveedor',
      'Prefijos de ID: R (Repuestos), H (Herramientas)'
    ]
  },
  {
    emoji: '🛡️',
    nombre: 'Preventivo',
    ruta: '/preventivo',
    descripcion: 'Planificacion y seguimiento de mantenimiento preventivo. Cada tarea se asocia a un equipo con frecuencia en dias (ej. cada 30, 90, 180, 365 dias), responsable y lista de repuestos requeridos (kit). El sistema calcula automaticamente la proxima fecha de ejecucion. Permite generar ordenes de trabajo directamente desde una tarea preventiva, copiando equipo, tecnico y repuestos sugeridos. Verifica que no exista ya una OT abierta para la misma tarea antes de generar.',
    funcionalidades: [
      'CRUD de tareas preventivas con frecuencia configurable',
      'Calculo automatico de proxima fecha',
      'Kit de repuestos requeridos por tarea',
      'Generacion de OT desde tarea preventiva (con validacion de duplicados)',
      'Vinculacion OT <-> Tarea preventiva via orden_preventiva_id',
      'Actualizacion automatica de fechas al completar OT preventiva',
      'Filtro por estado (activa/inactiva)',
      'Indicador visual de tareas vencidas'
    ]
  },
  {
    emoji: '📜',
    nombre: 'Historial',
    ruta: '/historial',
    descripcion: 'Linea de tiempo cronologica de todos los eventos de mantenimiento del sistema. Los eventos se crean automaticamente al completar una orden de trabajo, o pueden registrarse manualmente. Cada evento registra tipo (preventivo, correctivo, calibracion, otro), descripcion, acciones realizadas, tiempo invertido, costo y repuestos utilizados. Se puede filtrar por equipo para ver el historial completo de un equipo especifico.',
    funcionalidades: [
      'Timeline visual de eventos con iconos por tipo',
      '4 tipos de evento: Preventivo, Correctivo, Calibracion, Otro',
      'Creacion automatica al completar OT',
      'Creacion manual de eventos',
      'Filtro por equipo',
      'Registro de acciones, tiempo, costo y repuestos',
      'Enriquecimiento automatico con nombres de equipo y tecnico'
    ]
  },
  {
    emoji: '📈',
    nombre: 'Reportes',
    ruta: '/reportes',
    descripcion: 'Modulo de reportes y analisis con 6 secciones: Mantenimiento por equipo (resumen de OTs y costos), OTs por periodo (con estadisticas), Analisis de costos (por equipo y tipo), Cumplimiento preventivo (vencidas, proximas, al dia), Disponibilidad de equipos (distribucion por estado) e Inventario de repuestos (stock bajo, mas utilizados). Todos los reportes soportan filtros por rango de fechas.',
    funcionalidades: [
      'Mantenimiento por equipo: resumen de OTs y costos',
      'OTs por periodo: resumen estadistico con filtros',
      'Analisis de costos: por equipo, por tipo, totales y promedios',
      'Cumplimiento preventivo: vencidas, proximas a vencer, al dia',
      'Disponibilidad de equipos: distribucion por estado',
      'Inventario de repuestos: alertas de stock bajo y mas utilizados',
      'Filtros por rango de fechas en todos los reportes'
    ]
  },
  {
    emoji: '👥',
    nombre: 'Usuarios',
    ruta: '/usuarios',
    descripcion: 'Administracion de usuarios del sistema. Cada usuario tiene nombre de usuario, email, nombre completo, rol (tecnico o administrador) y estado activo/inactivo. La autenticacion se realiza mediante JWT (JSON Web Token) con contrasenas encriptadas con bcrypt. El sistema de autenticacion esta implementado pero actualmente los endpoints no exigen token para operar.',
    funcionalidades: [
      'CRUD de usuarios',
      'Roles: tecnico y administrador',
      'Autenticacion JWT con bcrypt',
      'Activacion/desactivacion de usuarios',
      'Asignacion de tecnicos a equipos y OTs'
    ]
  }
]

const entidades = [
  {
    nombre: 'Equipo',
    tabla: 'equipo',
    campos: 'modelo, numero_serie, marca, registro_sanitario, ubicacion, calibracion_proxima, estado_id, responsable_tecnico_id, imagen_ruta',
    prefijo: 'E',
    descripcion: 'Equipo biomédico registrado en el sistema. Cada equipo tiene un identificador E0001, E0002, etc.'
  },
  {
    nombre: 'OrdenTrabajo',
    tabla: 'ordentrabajo',
    campos: 'equipo_id, estado_id, prioridad, tecnico_asignado_id, titulo, descripcion_falla, acciones_realizadas, tiempo_real_invertido, costo_adicional',
    prefijo: '—',
    descripcion: 'Orden de trabajo para mantenimiento correctivo o preventivo de un equipo.'
  },
  {
    nombre: 'Repuesto',
    tabla: 'repuesto',
    campos: 'nombre_repuesto, numero_serie, especificaciones_tecnicas, cantidad_disponible, nivel_stock_minimo, precio_referencia, proveedor_ultimo',
    prefijo: 'R',
    descripcion: 'Repuesto o material de reposicion. Identificador R0001, R0002, etc. Stock con alerta de nivel minimo.'
  },
  {
    nombre: 'Herramienta',
    tabla: 'herramienta',
    campos: 'nombre_herramienta, numero_identificacion, categoria, cantidad_disponible, estado_uso, costo_adquisicion, proveedor_ultimo',
    prefijo: 'H',
    descripcion: 'Herramienta de trabajo. Identificador H0001, H0002, etc. Categorias: Manual, Electrica, Medicion, Seguridad.'
  },
  {
    nombre: 'TareaPreventiva',
    tabla: 'tareapreventiva',
    campos: 'equipo_id, responsable_id, titulo, frecuencia_dias, ultima_fecha, proxima_fecha, activa',
    prefijo: '—',
    descripcion: 'Tarea de mantenimiento preventivo programada con frecuencia en dias.'
  },
  {
    nombre: 'DocumentoAdjunto',
    tabla: 'documentoadjunto',
    campos: 'nombre_archivo, ruta_archivo, tipo_archivo, tamanio_bytes, categoria, subido_por, equipo_id/orden_trabajo_id/repuesto_id/herramienta_id',
    prefijo: '—',
    descripcion: 'Documento adjunto a cualquier entidad. Categorias: manual, foto, reporte, garantia, otro. Max 20MB.'
  },
  {
    nombre: 'EventoHistorial',
    tabla: 'eventohistorial',
    campos: 'equipo_id, orden_trabajo_id, tipo_evento, descripcion, tecnico_id, acciones_realizadas, tiempo_invertido, costo',
    prefijo: '—',
    descripcion: 'Evento en el historial de mantenimiento. Tipos: preventivo, correctivo, calibracion, otro.'
  },
  {
    nombre: 'EstadoEquipo',
    tabla: 'estadoequipo',
    campos: 'nombre_estado, color',
    prefijo: '—',
    descripcion: 'Estado operativo del equipo. 19 estados predefinidos con colores (Operativo, En mantenimiento, En calibracion, Bloqueado/LOTO, etc.)'
  },
  {
    nombre: 'EstadoOT',
    tabla: 'estadoot',
    campos: 'nombre_estado, color',
    prefijo: '—',
    descripcion: 'Estado de la orden de trabajo. 5 estados: Abierta, En Proceso, Esp. Repuesto, Completada, Cancelada.'
  },
  {
    nombre: 'Usuario',
    tabla: 'usuario',
    campos: 'username, email, full_name, role, is_active, hashed_password',
    prefijo: '—',
    descripcion: 'Usuario del sistema. Roles: tecnico, administrador. Autenticacion JWT con bcrypt.'
  }
]

const pendientes = [
  {
    emoji: '⚙️',
    nombre: 'Configuracion',
    prioridad: 'Alta',
    descripcion: 'Pagina de configuracion del sistema (icono: ⚙️) con tres capas: Capa 1 — Metadatos de archivos (.meta.json) [YA IMPLEMENTADO]; Capa 2 — Escaneo y recuperacion: reconstruir la base de datos a partir de los archivos .meta.json si se pierde la BD; Capa 3 — Backup/Restore: exportar e importar la base de datos completa como archivo JSON o SQLite.',
    estado: 'Parcial (Capa 1 implementada)'
  },
  {
    emoji: '📅',
    nombre: 'Calendario Preventivo (RF10)',
    prioridad: 'Alta',
    descripcion: 'Vista de calendario visual que muestre las tareas preventivas programadas en formato mensual/semanal. Permita ver de un vistazo que tareas estan pendientes, vencidas y proximas. Navegacion entre meses y semanas.',
    estado: 'No implementado'
  },
  {
    emoji: '🏢',
    nombre: 'Gestion de Proveedores (RF12)',
    prioridad: 'Media',
    descripcion: 'Modulo de gestion de proveedores con datos de contacto, historial de compras, tiempos de entrega y evaluacion. Vinculacion con repuestos y equipos para trazabilidad completa.',
    estado: 'No implementado'
  },
  {
    emoji: '🔒',
    nombre: 'Proteccion de rutas por autenticacion',
    prioridad: 'Alta',
    descripcion: 'Los endpoints de la API no validan el token JWT actualmente. Implementar Depends(get_current_user) en todas las rutas protegidas y navigation guards en el frontend para redirigir a login si no hay sesion activa.',
    estado: 'No implementado'
  },
  {
    emoji: '📄',
    nombre: 'Paginacion en listados',
    prioridad: 'Media',
    descripcion: 'Todos los endpoints de listado devuelven el conjunto completo de registros. Implementar paginacion con offset/limit para mejorar el rendimiento con volumenes grandes de datos.',
    estado: 'No implementado'
  },
  {
    emoji: '🔐',
    nombre: 'Secret JWT configurable',
    prioridad: 'Media',
    descripcion: 'El secreto JWT esta hardcoded en el codigo fuente. Deberia ser configurable via variables de entorno o config.json para mayor seguridad en produccion.',
    estado: 'No implementado'
  },
  {
    emoji: '🔄',
    nombre: 'Renombrar menu Inventario → Repuestos',
    prioridad: 'Baja',
    descripcion: 'El menu lateral muestra "Inventario" pero internamente ya se renombro a Repuestos. Actualizar la etiqueta del menu para consistencia.',
    estado: 'Pendiente'
  }
]

const archivosEstructura = [
  {
    carpeta: 'uploads/EQUIPOS/',
    descripcion: 'Imagenes y documentos de equipos',
    patron: 'E0001_NombreCarpeta/E0001_NombreCarpeta.jpg',
    meta: '.meta.json con datos del equipo y array documentos'
  },
  {
    carpeta: 'uploads/REPUESTOS/',
    descripcion: 'Imagenes y documentos de repuestos',
    patron: 'R0001_NombreCarpeta/R0001_NombreCarpeta.png',
    meta: '.meta.json con datos del repuesto y array documentos'
  },
  {
    carpeta: 'uploads/HERRAMIENTAS/',
    descripcion: 'Imagenes y documentos de herramientas',
    patron: 'H0001_NombreCarpeta/H0001_NombreCarpeta.jpg',
    meta: '.meta.json con datos de la herramienta y array documentos'
  },
  {
    carpeta: 'uploads/EQUIPOS/E0001_xxx/DOC/',
    descripcion: 'Subcarpeta de documentos adjuntos de un equipo',
    patron: 'manual_usuario.pdf, foto_dano.jpg, etc.',
    meta: '.meta.json con array documentos (actualizado por cada subida)'
  }
]

const metaJsonEjemplo = `{
  "entidad_tipo": "equipo",
  "entidad_id": 1,
  "entidad_nombre": "Monitor de Signos Vitales",
  "codigo": "E0001",
  "modelo": "IntelliVue MX800",
  "marca": "Philips",
  "numero_serie": "SN-2024-001",
  "imagen_ruta": "EQUIPOS/E0001_MonitorSignos/E0001_MonitorSignos.jpg",
  "documentos": [
    {
      "nombre_archivo": "manual_usuario.pdf",
      "ruta_archivo": "EQUIPOS/E0001_MonitorSignos/DOC/manual_usuario.pdf",
      "tipo_archivo": "application/pdf",
      "categoria": "manual",
      "fecha_subida": "2025-01-15T10:30:00"
    }
  ]
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

      <!-- Navegacion por secciones -->
      <nav class="help-nav">
        <button
          v-for="sec in secciones"
          :key="sec.id"
          class="help-nav-btn"
          :class="{ 'help-nav-btn--active': seccionActiva === sec.id }"
          @click="seccionActiva = sec.id"
        >
          <span class="help-nav-emoji">{{ sec.emoji }}</span>
          <span class="help-nav-label">{{ sec.label }}</span>
        </button>
      </nav>

      <!-- SECCION: El Sistema -->
      <section v-if="seccionActiva === 'sistema'" class="help-section">
        <div class="help-card help-card--hero">
          <h3>¿Que es CMMS-BioAI?</h3>
          <p>
            <strong>CMMS-BioAI</strong> es un Sistema de Gestion de Mantenimiento Asistido por Computadora (Computerized Maintenance Management System)
            diseñado especificamente para <strong>equipos biomédicos</strong> en el contexto de laboratorios clinicos y hospitales de Bolivia.
            Es un proyecto de Maestria en Ingenieria Biomédica que integra gestion de activos, ordenes de trabajo, inventario de repuestos,
            mantenimiento preventivo y reportes analiticos en una plataforma web unificada.
          </p>
          <p>
            El sistema permite registrar y dar seguimiento a equipos biomédicos (monitores de signos vitales, analizadores de laboratorio,
            ventiladores mecánicos, etc.), gestionar ordenes de trabajo correctivas y preventivas, controlar el inventario de repuestos y
            herramientas, planificar el mantenimiento preventivo con frecuencias configurables, y generar reportes de cumplimiento, costos
            y disponibilidad. Incorpora un modulo de sugerencias automaticas basadas en reglas que alerta sobre situaciones criticas como
            stock bajo, preventivos vencidos o calibraciones proximas.
          </p>
        </div>

        <div class="help-card">
          <h3>Tecnologias Utilizadas</h3>
          <div class="tech-grid">
            <div class="tech-item">
              <span class="tech-icon">🐍</span>
              <div>
                <strong>Backend</strong>
                <p>Python + FastAPI + SQLModel + SQLite</p>
              </div>
            </div>
            <div class="tech-item">
              <span class="tech-icon">💚</span>
              <div>
                <strong>Frontend</strong>
                <p>Vue 3 + Vue Router + Chart.js + Axios</p>
              </div>
            </div>
            <div class="tech-item">
              <span class="tech-icon">🔐</span>
              <div>
                <strong>Autenticacion</strong>
                <p>OAuth2 + JWT + bcrypt</p>
              </div>
            </div>
            <div class="tech-item">
              <span class="tech-icon">💾</span>
              <div>
                <strong>Base de Datos</strong>
                <p>SQLite con recuperacion via .meta.json</p>
              </div>
            </div>
          </div>
        </div>

        <div class="help-card">
          <h3>Flujo de Trabajo Principal</h3>
          <div class="flow-steps">
            <div class="flow-step">
              <span class="flow-num">1</span>
              <div>
                <strong>Registrar Equipos</strong>
                <p>Ingrese los equipos biomédicos con sus datos tecnicos, estado e imagen.</p>
              </div>
            </div>
            <div class="flow-step">
              <span class="flow-num">2</span>
              <div>
                <strong>Planificar Preventivo</strong>
                <p>Defina tareas preventivas con frecuencia y repuestos requeridos.</p>
              </div>
            </div>
            <div class="flow-step">
              <span class="flow-num">3</span>
              <div>
                <strong>Gestionar Ordenes</strong>
                <p>Cree OTs desde preventivo o correctivo, asigne tecnicos y repuestos.</p>
              </div>
            </div>
            <div class="flow-step">
              <span class="flow-num">4</span>
              <div>
                <strong>Completar y Registrar</strong>
                <p>Al completar OTs, el historial y stock se actualizan automaticamente.</p>
              </div>
            </div>
            <div class="flow-step">
              <span class="flow-num">5</span>
              <div>
                <strong>Analizar y Reportar</strong>
                <p>Genere reportes de cumplimiento, costos y disponibilidad.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCION: Modulos -->
      <section v-if="seccionActiva === 'modulos'" class="help-section">
        <div
          v-for="mod in modulos"
          :key="mod.nombre"
          class="help-card help-card--modulo"
        >
          <div class="modulo-header">
            <span class="modulo-emoji">{{ mod.emoji }}</span>
            <div class="modulo-title-row">
              <h3>{{ mod.nombre }}</h3>
              <router-link :to="mod.ruta" class="modulo-link">Ir al modulo &rarr;</router-link>
            </div>
          </div>
          <p class="modulo-desc">{{ mod.descripcion }}</p>
          <div class="modulo-funcs">
            <h4>Funcionalidades principales:</h4>
            <ul>
              <li v-for="func in mod.funcionalidades" :key="func">{{ func }}</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- SECCION: Entidades -->
      <section v-if="seccionActiva === 'entidades'" class="help-section">
        <div class="help-card">
          <h3>Modelos de Datos del Sistema</h3>
          <p>El sistema gestiona 10 tablas en la base de datos SQLite. A continuacion se describe cada entidad, sus campos principales y su proposito dentro del CMMS.</p>
        </div>
        <div
          v-for="ent in entidades"
          :key="ent.nombre"
          class="help-card help-card--entidad"
        >
          <div class="entidad-header">
            <h3>{{ ent.nombre }}</h3>
            <span class="entidad-tabla">{{ ent.tabla }}</span>
            <span v-if="ent.prefijo !== '—'" class="entidad-prefijo">Prefijo: {{ ent.prefijo }}</span>
          </div>
          <p>{{ ent.descripcion }}</p>
          <div class="entidad-campos">
            <strong>Campos principales:</strong>
            <code>{{ ent.campos }}</code>
          </div>
        </div>
      </section>

      <!-- SECCION: Archivos -->
      <section v-if="seccionActiva === 'archivos'" class="help-section">
        <div class="help-card">
          <h3>Estructura de Archivos y Recuperacion</h3>
          <p>
            El sistema utiliza una estrategia de <strong>recuperacion en capas</strong> para proteger los datos. Ademas de la base de datos SQLite,
            cada carpeta de archivos subidos contiene un archivo <code>.meta.json</code> con los metadatos de la entidad y sus documentos adjuntos.
            Si la base de datos se pierde, estos archivos permiten reconstruir la informacion critica.
          </p>
        </div>

        <div class="help-card">
          <h3>Convencion de Nombres</h3>
          <p>Los archivos subidos siguen un patron consistente que facilita la identificacion:</p>
          <div class="conv-table">
            <div class="conv-row conv-row--header">
              <span>Tipo</span>
              <span>Carpeta</span>
              <span>Patron de Nombre</span>
            </div>
            <div v-for="arc in archivosEstructura" :key="arc.carpeta" class="conv-row">
              <span>{{ arc.descripcion }}</span>
              <span><code>{{ arc.carpeta }}</code></span>
              <span><code>{{ arc.patron }}</code></span>
            </div>
          </div>
        </div>

        <div class="help-card">
          <h3>Ejemplo de .meta.json</h3>
          <p>Cada carpeta de entidad contiene un <code>.meta.json</code> con la informacion necesaria para reconstruir el registro:</p>
          <pre class="meta-code">{{ metaJsonEjemplo }}</pre>
        </div>

        <div class="help-card">
          <h3>Capas de Recuperacion</h3>
          <div class="capas-grid">
            <div class="capa-card capa-card--done">
              <span class="capa-num">1</span>
              <h4>Metadatos en Archivos</h4>
              <p><strong>ESTADO: IMPLEMENTADO</strong></p>
              <p>Los archivos .meta.json almacenan metadatos junto a los archivos fisicos. Si se pierde la BD, los datos esenciales pueden recuperarse escaneando estos archivos.</p>
            </div>
            <div class="capa-card capa-card--pending">
              <span class="capa-num">2</span>
              <h4>Escaneo y Recuperacion</h4>
              <p><strong>ESTADO: PENDIENTE</strong></p>
              <p>Funcionalidad en la pagina Configuracion que leera los .meta.json y recreara los registros en la base de datos automaticamente.</p>
            </div>
            <div class="capa-card capa-card--pending">
              <span class="capa-num">3</span>
              <h4>Backup y Restore</h4>
              <p><strong>ESTADO: PENDIENTE</strong></p>
              <p>Exportacion e importacion de la base de datos completa como archivo JSON o SQLite para respaldo y restauracion.</p>
            </div>
          </div>
        </div>
      </section>

      <!-- SECCION: Pendientes -->
      <section v-if="seccionActiva === 'pendientes'" class="help-section">
        <div class="help-card help-card--warning">
          <h3>Funcionalidades Pendientes</h3>
          <p>
            A continuacion se listan las funcionalidades que aun no han sido implementadas o estan parcialmente completadas.
            Esta seccion sirve como hoja de ruta para el desarrollo continuo del sistema.
          </p>
        </div>

        <div
          v-for="pend in pendientes"
          :key="pend.nombre"
          class="help-card help-card--pendiente"
        >
          <div class="pendiente-header">
            <span class="pendiente-emoji">{{ pend.emoji }}</span>
            <div>
              <h3>{{ pend.nombre }}</h3>
              <span class="pendiente-prioridad" :class="'prioridad--' + pend.prioridad.toLowerCase()">
                {{ pend.prioridad }}
              </span>
            </div>
          </div>
          <p>{{ pend.descripcion }}</p>
          <div class="pendiente-estado">
            <strong>Estado:</strong> {{ pend.estado }}
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<style scoped>
.dashboard-container { padding: 0; }
.content { padding: 2rem; }

.help-header {
  margin-bottom: 1.5rem;
}
.help-header h2 {
  margin: 0 0 0.25rem 0;
  color: #1e293b;
  font-size: 1.5rem;
}
.help-subtitle {
  margin: 0;
  color: #64748b;
  font-size: 0.95rem;
}

/* === Navegacion por secciones === */
.help-nav {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}
.help-nav-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.5rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 8px;
  background: white;
  cursor: pointer;
  font-size: 0.88rem;
  font-weight: 600;
  color: #475569;
  transition: all 0.2s ease;
}
.help-nav-btn:hover {
  border-color: #3b82f6;
  color: #2563eb;
  background: #eff6ff;
}
.help-nav-btn--active {
  border-color: #3b82f6;
  background: #3b82f6;
  color: white;
}
.help-nav-btn--active:hover {
  background: #2563eb;
  color: white;
}
.help-nav-emoji {
  font-size: 1.1rem;
}
.help-nav-label {
  font-size: 0.85rem;
}

/* === Tarjetas de contenido === */
.help-card {
  background: white;
  border-radius: 10px;
  padding: 1.25rem;
  box-shadow: 0 1px 6px rgba(15, 23, 42, 0.07);
  border: 1px solid rgba(0, 0, 0, 0.06);
  margin-bottom: 1rem;
}
.help-card h3 {
  margin: 0 0 0.75rem 0;
  font-size: 1.05rem;
  font-weight: 700;
  color: #1e293b;
}
.help-card p {
  margin: 0 0 0.5rem 0;
  color: #475569;
  line-height: 1.6;
  font-size: 0.9rem;
}
.help-card p:last-child {
  margin-bottom: 0;
}
.help-card code {
  background: #f1f5f9;
  padding: 0.15rem 0.4rem;
  border-radius: 4px;
  font-size: 0.82rem;
  color: #7c3aed;
  word-break: break-all;
}

.help-card--hero {
  border-left: 4px solid #3b82f6;
  background: linear-gradient(135deg, #eff6ff 0%, #ffffff 40%);
}

.help-card--modulo {
  border-left: 4px solid #22c55e;
}

.help-card--entidad {
  border-left: 4px solid #f59e0b;
}

.help-card--warning {
  border-left: 4px solid #f59e0b;
  background: #fffbeb;
}

.help-card--pendiente {
  border-left: 4px solid #ef4444;
}

/* === Modulo header === */
.modulo-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.modulo-emoji {
  font-size: 1.6rem;
  flex-shrink: 0;
  margin-top: 0.1rem;
}
.modulo-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}
.modulo-title-row h3 {
  margin: 0;
}
.modulo-link {
  font-size: 0.82rem;
  font-weight: 600;
  color: #3b82f6;
  text-decoration: none;
  padding: 0.2rem 0.6rem;
  border-radius: 4px;
  background: #eff6ff;
  transition: background 0.2s;
}
.modulo-link:hover {
  background: #dbeafe;
  text-decoration: underline;
}
.modulo-desc {
  margin-bottom: 0.75rem !important;
}
.modulo-funcs h4 {
  margin: 0 0 0.4rem 0;
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e293b;
}
.modulo-funcs ul {
  margin: 0;
  padding-left: 1.2rem;
  color: #475569;
  font-size: 0.85rem;
  line-height: 1.7;
}
.modulo-funcs li {
  margin-bottom: 0.15rem;
}

/* === Entidad === */
.entidad-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
  margin-bottom: 0.5rem;
}
.entidad-header h3 {
  margin: 0;
}
.entidad-tabla {
  font-size: 0.78rem;
  font-weight: 600;
  color: #6366f1;
  background: #eef2ff;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}
.entidad-prefijo {
  font-size: 0.78rem;
  font-weight: 600;
  color: #059669;
  background: #ecfdf5;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}
.entidad-campos {
  margin-top: 0.5rem;
  padding: 0.6rem 0.8rem;
  background: #f8fafc;
  border-radius: 6px;
  font-size: 0.82rem;
}
.entidad-campos strong {
  color: #334155;
  margin-right: 0.4rem;
}
.entidad-campos code {
  background: transparent;
  color: #7c3aed;
  font-size: 0.8rem;
  word-break: break-all;
}

/* === Tecnologias grid === */
.tech-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}
@media (max-width: 900px) {
  .tech-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 550px) {
  .tech-grid { grid-template-columns: 1fr; }
}
.tech-item {
  display: flex;
  align-items: flex-start;
  gap: 0.6rem;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.tech-icon {
  font-size: 1.4rem;
  flex-shrink: 0;
}
.tech-item strong {
  display: block;
  font-size: 0.88rem;
  color: #1e293b;
}
.tech-item p {
  margin: 0.15rem 0 0 0;
  font-size: 0.8rem;
  color: #64748b;
}

/* === Flujo de trabajo === */
.flow-steps {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 0.75rem;
}
@media (max-width: 900px) {
  .flow-steps { grid-template-columns: repeat(3, 1fr); }
}
@media (max-width: 550px) {
  .flow-steps { grid-template-columns: 1fr; }
}
.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 0.75rem;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}
.flow-num {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
  flex-shrink: 0;
}
.flow-step strong {
  display: block;
  font-size: 0.85rem;
  color: #1e293b;
  margin-bottom: 0.25rem;
}
.flow-step p {
  margin: 0;
  font-size: 0.78rem;
  color: #64748b;
  line-height: 1.4;
}

/* === Convencion tabla === */
.conv-table {
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  overflow: hidden;
}
.conv-row {
  display: grid;
  grid-template-columns: 2fr 2fr 3fr;
  gap: 0;
  border-bottom: 1px solid #e2e8f0;
  font-size: 0.82rem;
}
.conv-row:last-child {
  border-bottom: none;
}
.conv-row > span {
  padding: 0.5rem 0.75rem;
  color: #475569;
}
.conv-row--header > span {
  background: #f1f5f9;
  font-weight: 700;
  color: #334155;
}
.conv-row code {
  font-size: 0.78rem;
}

/* === Meta JSON ejemplo === */
.meta-code {
  background: #1e293b;
  color: #e2e8f0;
  padding: 1rem;
  border-radius: 8px;
  font-size: 0.78rem;
  line-height: 1.5;
  overflow-x: auto;
  white-space: pre;
  font-family: 'Courier New', monospace;
}

/* === Capas de recuperacion === */
.capas-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}
@media (max-width: 800px) {
  .capas-grid { grid-template-columns: 1fr; }
}
.capa-card {
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid;
  text-align: center;
}
.capa-card h4 {
  margin: 0.5rem 0 0.25rem 0;
  font-size: 0.9rem;
  color: #1e293b;
}
.capa-card p {
  font-size: 0.8rem;
  line-height: 1.5;
  margin: 0.2rem 0;
}
.capa-card--done {
  background: #f0fdf4;
  border-color: #86efac;
}
.capa-card--pending {
  background: #fffbeb;
  border-color: #fde68a;
}
.capa-num {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  font-weight: 700;
  font-size: 0.85rem;
}

/* === Pendiente === */
.pendiente-header {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  margin-bottom: 0.5rem;
}
.pendiente-emoji {
  font-size: 1.4rem;
  flex-shrink: 0;
  margin-top: 0.15rem;
}
.pendiente-header h3 {
  margin: 0;
  display: inline;
}
.pendiente-prioridad {
  display: inline-block;
  font-size: 0.72rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  margin-left: 0.5rem;
  vertical-align: middle;
}
.prioridad--alta {
  background: #fef2f2;
  color: #dc2626;
}
.prioridad--media {
  background: #fffbeb;
  color: #d97706;
}
.prioridad--baja {
  background: #f0fdf4;
  color: #16a34a;
}
.pendiente-estado {
  margin-top: 0.5rem;
  padding: 0.4rem 0.6rem;
  background: #f8fafc;
  border-radius: 4px;
  font-size: 0.82rem;
  color: #475569;
}

/* === Seccion animacion === */
.help-section {
  animation: fadeIn 0.25s ease;
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
