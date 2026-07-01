<script setup>
import { ref, computed } from 'vue'
import Navbar from '../components/Navbar.vue'

const seccionActiva = ref('sistema')

const secciones = [
  { id: 'sistema', emoji: '🏥', label: 'El Sistema' },
  { id: 'modulos', emoji: '🧩', label: 'Modulos' },
  { id: 'entidades', emoji: '📦', label: 'Entidades' },
  { id: 'rf', emoji: '📋', label: 'Requisitos RF' },
  { id: 'archivos', emoji: '📁', label: 'Archivos' },
  { id: 'pendientes', emoji: '🚧', label: 'Pendientes' }
]

// ─── Leyenda de estados de campo ───
// rf=true  implementado=true  → 🟢 Campo del RF, implementado
// rf=false implementado=true  → 🟡 Campo extra, no esta en RF
// rf=true  implementado=false → 🔴 Campo del RF, NO implementado

const entidades = [
  {
    nombre: 'Equipo',
    tabla: 'equipo',
    prefijo: 'E',
    rf: 'RF01 v0.9.0',
    descripcion: 'Equipo biomedico (universal, sin contexto Bolivia). ID: E0001, E0002, etc.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'nombre_corto', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre descriptivo abreviado del equipo. NOT NULL en v0.9.0' },
      { nombre: 'modelo', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Modelo especifico del fabricante. NO editable despues de creado' },
      { nombre: 'numero_serie', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Numero de serie unico. NO editable despues de creado' },
      { nombre: 'marca', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre del fabricante. NO editable despues de creado' },
      { nombre: 'numero_material', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Numero de material del fabricante (variante del modelo)' },
      { nombre: 'fecha_adquisicion', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha de adquisicion (opcional en v0.9.0)' },
      { nombre: 'fecha_inicio_garantia', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'v0.9.0: Fecha de inicio de garantia' },
      { nombre: 'fecha_fin_garantia', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha de fin de garantia' },
      { nombre: 'ubicacion_actual', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ubicacion fisica actual (sala, piso, hospital)' },
      { nombre: 'estado_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Estados_Equipo.id' },
      { nombre: 'proveedor_principal_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'v0.9.0: FK a Proveedor.id. Dropdown con opcion "Crear nuevo"' },
      { nombre: 'condicion_origen', tipo: 'TEXT (enum)', rf: true, impl: true, oblig: false, desc: 'v0.9.0: Compra, Donacion, Prestamo, Demostracion, Evaluacion, Leasing, Renta, Comodato, Otro' },
      { nombre: 'descripcion', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Descripcion TECNICA del equipo (que es, que hace)' },
      { nombre: 'observaciones', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'v0.9.0: Notas operativas (como esta, accesorios, advertencias)' },
      { nombre: 'imagen_ruta', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ruta local de la imagen del equipo' },
      // CAMPOS ELIMINADOS en v0.9.0 (no se muestran):
      // - registro_sanitario_bolivia (universalidad)
      // - calibracion_proxima (gestionado via MP/OT)
      // - responsable_tecnico_id (asignacion flexible en OT/MP)
      // - proveedor_principal (texto, reemplazado por FK)
    ]
  },
  {
    nombre: 'OrdenTrabajo',
    tabla: 'ordentrabajo',
    prefijo: '—',
    rf: 'RF02 v0.9.2',
    descripcion: 'Orden de trabajo correctiva o preventiva. v0.9.1: costos via OtCostoAdicional (RF11). v0.9.2: contrato_id opcional (RF12).',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'equipo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Equipos.id' },
      { nombre: 'orden_preventiva_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'FK a Tareas_MP.id - Tarea preventiva que origino esta OT' },
      { nombre: 'estado_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Estados_OT.id' },
      { nombre: 'prioridad', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Baja, Media, Alta, Urgente' },
      { nombre: 'tecnico_asignado_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'FK a Usuarios.id' },
      { nombre: 'fecha_creacion', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha y hora de creacion (automatica)' },
      { nombre: 'fecha_vencimiento', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha limite para la resolucion' },
      { nombre: 'titulo', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Titulo corto descriptivo de la OT' },
      { nombre: 'descripcion_falla', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Descripcion detallada de la falla' },
      { nombre: 'acciones_realizadas', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Detalle de las actividades realizadas' },
      { nombre: 'tiempo_real_invertido', tipo: 'REAL', rf: true, impl: true, oblig: false, desc: 'Horas reales trabajadas' },
      { nombre: 'unidad_tiempo', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Unidad de tiempo (horas/dias)' },
      { nombre: 'contrato_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'v0.9.2: FK opcional a Contrato.id (RF12). Marca la OT como cubierta por contrato' },
      // v0.9.1: costo_adicional y costos_adicionales OBSOLETOS — reemplazados por OtCostoAdicional (RF11)
      // Se mantienen en BD SQLite por compatibilidad pero no se usan
      { nombre: 'tiempo_estimado_horas', tipo: 'REAL', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Tiempo estimado. En RF02 pero no implementado' },
      { nombre: 'categoria_accion', tipo: 'TEXT', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Categoria de la accion. En RF02 pero no implementado' },
      { nombre: 'firma_digital_tecnico', tipo: 'TEXT', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Firma digital del tecnico. En RF02 pero no implementado' }
    ]
  },
  {
    nombre: 'TareaPreventiva',
    tabla: 'tareapreventiva',
    prefijo: '—',
    rf: 'RF03 v0.9.2',
    descripcion: 'Tarea preventiva con ciclo verde-amarillo-rojo. proxima_fecha editable. frecuencia_dias como sugerencia.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'equipo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Equipos.id' },
      { nombre: 'titulo', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Titulo corto descriptivo de la tarea' },
      { nombre: 'descripcion', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Instrucciones detalladas o protocolo' },
      { nombre: 'frecuencia_dias', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'v0.9.2: Solo SUGERENCIA de periodicidad (ej: 90 dias). No auto-calcula proxima_fecha' },
      { nombre: 'ultima_fecha', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha de la ultima ejecucion real' },
      { nombre: 'proxima_fecha', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'v0.9.0: FECHA REAL programada por el usuario (editable, no auto-calculada). Es la fecha que aparece en el calendario' },
      { nombre: 'activa', tipo: 'BOOLEAN', rf: true, impl: true, oblig: true, desc: 'Indica si la tarea esta activa' },
      { nombre: 'responsable_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'FK a Usuarios.id - Tecnico responsable' },
      { nombre: 'estado_recordatorio', tipo: 'TEXT (calculado)', rf: false, impl: true, oblig: false, desc: 'v0.9.2: EXTRA calculado en runtime. Valores: 🟢 Programada (OT activa), 🟡 Recordatorio, 🔴 Vencida. No se guarda en BD' },
      { nombre: 'periodicidad_tipo', tipo: 'TEXT', rf: true, impl: false, oblig: false, desc: 'FALTANTE v1.0: Unidad del intervalo (Dias/Horas/Ciclos)' },
      { nombre: 'condiciones_activacion', tipo: 'TEXT JSON', rf: true, impl: false, oblig: false, desc: 'FALTANTE v1.0: Logica compleja de activacion (OR entre horas y dias)' },
      { nombre: 'logica_periodicidad', tipo: 'TEXT JSON', rf: true, impl: false, oblig: false, desc: 'FALTANTE v1.0: Patrones de periodicidad complejos (ej. 2 veces al ano)' },
      { nombre: 'contador_acumulado', tipo: 'REAL', rf: true, impl: false, oblig: false, desc: 'FALTANTE v1.0: Valor acumulado del contador (horas, ciclos)' }
    ]
  },
  {
    nombre: 'Repuesto',
    tabla: 'repuesto',
    prefijo: 'R',
    rf: 'RF04',
    descripcion: 'Repuesto con stock y alerta de nivel minimo. ID: R0001, etc.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'nombre_repuesto', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre descriptivo del repuesto' },
      { nombre: 'numero_material', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Numero de identificacion del fabricante' },
      { nombre: 'descripcion', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Descripcion tecnica detallada del repuesto' },
      { nombre: 'especificaciones_tecnicas', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Detalles tecnicos especificos (voltaje, tamano, etc.)' },
      { nombre: 'imagen_ruta', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ruta local a la imagen del repuesto (RF04: imagen)' },
      { nombre: 'cantidad_disponible', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Cantidad actualmente disponible en stock local' },
      { nombre: 'unidad_medida', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Unidad de medida (unidad, par, kg, etc.)' },
      { nombre: 'ubicacion_almacen', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ubicacion fisica del repuesto (Caja A1, Estanteria B)' },
      { nombre: 'nivel_stock_minimo', tipo: 'INTEGER', rf: true, impl: true, oblig: false, desc: 'Nivel critico de stock para alertas' },
      { nombre: 'proveedor_ultimo', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Nombre del ultimo proveedor del repuesto' },
      { nombre: 'fecha_ultima_entrada', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha del ultimo registro de entrada' },
      { nombre: 'precio_referencia', tipo: 'REAL', rf: true, impl: true, oblig: false, desc: 'Precio de referencia para analisis de costos' },
      { nombre: 'codigo_equivalente', tipo: 'TEXT', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Codigo alternativo del repuesto (OEM, generico). Esta en RF04 pero no implementado' },
      { nombre: 'numero_serie', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Numero de serie del repuesto. No esta en RF04' }
    ]
  },
  {
    nombre: 'EventoHistorial',
    tabla: 'eventohistorial',
    prefijo: '—',
    rf: 'RF05',
    descripcion: 'Evento en el historial de mantenimiento.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'equipo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Equipos.id - Equipo al que pertenece el evento' },
      { nombre: 'tipo_evento', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Categoria: preventivo, correctivo, calibracion, otro' },
      { nombre: 'fecha_evento', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha y hora del evento (RF05: fecha_registro)' },
      { nombre: 'descripcion', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Descripcion breve del evento (RF05: descripcion_general)' },
      { nombre: 'tecnico_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'FK a Usuarios.id - Tecnico responsable (RF05: tecnico_responsable_id)' },
      { nombre: 'estado_ot_relacionada', tipo: 'TEXT', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Estado de la OT si el evento es una OT. Esta en RF05 pero no implementado' },
      { nombre: 'evento_detalle_id', tipo: 'INTEGER FK', rf: true, impl: false, oblig: false, desc: 'FALTANTE: FK a Detalles_Evento.id. Esta en RF05 pero no implementado (tabla no existe)' },
      { nombre: 'evento_detalle_tipo', tipo: 'TEXT', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Discriminador de tabla de detalles. Esta en RF05 pero no implementado' },
      { nombre: 'orden_trabajo_id', tipo: 'INTEGER FK', rf: false, impl: true, oblig: false, desc: 'EXTRA: FK a OrdenTrabajo.id. No esta en RF05' },
      { nombre: 'acciones_realizadas', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Acciones realizadas en el evento. No esta en RF05' },
      { nombre: 'tiempo_invertido', tipo: 'REAL', rf: false, impl: true, oblig: false, desc: 'EXTRA: Tiempo invertido en el evento. No esta en RF05' },
      { nombre: 'costo', tipo: 'REAL', rf: false, impl: true, oblig: false, desc: 'EXTRA: Costo del evento. No esta en RF05' },
      { nombre: 'repuestos_utilizados', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Resumen de repuestos utilizados. No esta en RF05' }
    ]
  },
  {
    nombre: 'Herramienta',
    tabla: 'herramienta',
    prefijo: 'H',
    rf: 'RF09',
    descripcion: 'Herramienta del taller. ID: H0001, etc.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'nombre_herramienta', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre descriptivo de la herramienta o material' },
      { nombre: 'numero_identificacion', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Numero de identificacion unico (serie o codigo interno)' },
      { nombre: 'descripcion', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Descripcion detallada de la herramienta/material' },
      { nombre: 'categoria', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Categoria: Instrumento, Herramienta Manual, Consumible, Kit' },
      { nombre: 'cantidad_disponible', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Cantidad actualmente disponible en stock' },
      { nombre: 'unidad_medida', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Unidad de medida (unidad, metro, litro, paquete)' },
      { nombre: 'ubicacion_almacen', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ubicacion fisica (Taller - Estante A, Caja Tecnico X)' },
      { nombre: 'estado_uso', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Estado: Disponible, En Uso, En Reparacion, Dado de Baja' },
      { nombre: 'imagen_ruta', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ruta relativa de la imagen de la herramienta' },
      { nombre: 'costo_adquisicion', tipo: 'REAL', rf: true, impl: true, oblig: false, desc: 'Costo de adquisicion del articulo' },
      { nombre: 'fecha_adquisicion', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha de adquisicion de la herramienta/material' },
      { nombre: 'proveedor_ultimo', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Nombre del ultimo proveedor' },
      { nombre: 'observaciones', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Notas o comentarios adicionales' },
      { nombre: 'fecha_registro', tipo: 'DATETIME', rf: true, impl: false, oblig: false, desc: 'FALTANTE: Fecha y hora de registro en el sistema. Esta en RF09 pero no implementado' }
    ]
  },
  {
    nombre: 'Usuario',
    tabla: 'usuario',
    prefijo: '—',
    rf: 'RF08',
    descripcion: 'Usuario del sistema. Roles: tecnico, admin.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'username', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre de usuario unico para inicio de sesion' },
      { nombre: 'email', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Correo electronico del usuario' },
      { nombre: 'hashed_password', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Contrasena almacenada con hashing (bcrypt). No visible en UI' },
      { nombre: 'full_name', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Nombre completo del usuario' },
      { nombre: 'role', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Rol: admin o tecnico. Determina permisos' },
      { nombre: 'is_active', tipo: 'BOOLEAN', rf: true, impl: true, oblig: true, desc: 'Indica si la cuenta esta activa' }
    ]
  },
  {
    nombre: 'Proveedor',
    tabla: 'proveedor',
    prefijo: '—',
    rf: 'RF10',
    descripcion: 'Empresa proveedora de equipos, repuestos, herramientas o servicios.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'nombre_empresa', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre legal o comercial de la empresa proveedora. Unico' },
      { nombre: 'ciudad', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Ciudad principal de la empresa. Campo independiente de direccion. Usado por el filtro de ciudad' },
      { nombre: 'direccion', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Direccion fisica principal de la empresa' },
      { nombre: 'telefono_principal', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Telefono de contacto principal de la empresa' },
      { nombre: 'email_principal', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Email de contacto principal de la empresa' },
      { nombre: 'pagina_web', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Sitio web oficial del proveedor' },
      { nombre: 'notas_generales', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Notas o comentarios generales sobre el proveedor' }
    ]
  },
  {
    nombre: 'ContactoProveedor',
    tabla: 'contactoproveedor',
    prefijo: '—',
    rf: 'RF10',
    descripcion: 'Persona de contacto asociada a un proveedor (gerente, vendedor, soporte).',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'proveedor_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Proveedor.id - Proveedor al que pertenece este contacto' },
      { nombre: 'nombre_contacto', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre completo del contacto' },
      { nombre: 'cargo', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Cargo o posicion (Gerente de Ventas, Jefe de Soporte, etc.)' },
      { nombre: 'telefono_contacto', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Telefono directo del contacto' },
      { nombre: 'email_contacto', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Email directo del contacto' },
      { nombre: 'notas_contacto', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Notas o comentarios especificos sobre este contacto' }
    ]
  },
  {
    nombre: 'EstadoEquipo',
    tabla: 'estadoequipo',
    prefijo: '—',
    rf: 'Hoja 9',
    descripcion: '19 estados con colores (Operativo, En mantenimiento, etc.)',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico' },
      { nombre: 'nombre_estado', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre del estado del equipo. Debe ser unico' },
      { nombre: 'color', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Codigo hex de color para UI. No esta en RF' }
    ]
  },
  {
    nombre: 'EstadoOT',
    tabla: 'estadoot',
    prefijo: '—',
    rf: 'Hoja 10',
    descripcion: '5 estados de OT (Abierta, En Proceso, etc.)',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico' },
      { nombre: 'nombre_estado', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre del estado de la OT. Debe ser unico' },
      { nombre: 'color', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Codigo hex de color para UI. No esta en RF' }
    ]
  },
  {
    nombre: 'DocumentoAdjunto',
    tabla: 'documentoadjunto',
    prefijo: '—',
    rf: 'Hoja 11',
    descripcion: 'Documento adjunto a cualquier entidad (polimorfico).',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico' },
      { nombre: 'equipo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: false, desc: 'FK a Equipos.id' },
      { nombre: 'nombre_archivo', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Nombre original del archivo (RF: nombre_original)' },
      { nombre: 'ruta_archivo', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Ruta relativa donde se almacena el archivo' },
      { nombre: 'tipo_documento', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Categoria del documento (RF: tipo_documento → tipo_archivo + categoria)' },
      { nombre: 'fecha_adjunto', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha de adjunto (RF: fecha_adjunto → fecha_subida)' },
      { nombre: 'orden_trabajo_id', tipo: 'INTEGER FK', rf: false, impl: true, oblig: false, desc: 'EXTRA: FK a OrdenTrabajo.id. Asociacion polimorfica' },
      { nombre: 'repuesto_id', tipo: 'INTEGER FK', rf: false, impl: true, oblig: false, desc: 'EXTRA: FK a Repuesto.id. Asociacion polimorfica' },
      { nombre: 'herramienta_id', tipo: 'INTEGER FK', rf: false, impl: true, oblig: false, desc: 'EXTRA: FK a Herramienta.id. Asociacion polimorfica' },
      { nombre: 'tipo_archivo', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: MIME type del archivo' },
      { nombre: 'tamanio_bytes', tipo: 'INTEGER', rf: false, impl: true, oblig: false, desc: 'EXTRA: Tamano del archivo en bytes' },
      { nombre: 'descripcion', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Descripcion del documento' },
      { nombre: 'categoria', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: manual/foto/reporte/garantia/otro' },
      { nombre: 'subido_por', tipo: 'TEXT', rf: false, impl: true, oblig: false, desc: 'EXTRA: Username de quien subio el documento' }
    ]
  },
  {
    nombre: 'TareaRepuesto',
    tabla: 'tarea_repuesto',
    prefijo: '—',
    rf: 'Hoja 12',
    descripcion: 'Relacion N:M entre TareaPreventiva y Repuesto con cantidad.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: false, impl: true, oblig: true, desc: 'EXTRA: Clave primaria surrogate. RF usa PK compuesta' },
      { nombre: 'tarea_preventiva_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a TareaPreventiva.id (RF: tarea_mp_id)' },
      { nombre: 'repuesto_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Repuesto.id' },
      { nombre: 'cantidad_requerida', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Cantidad del repuesto necesaria para la tarea' }
    ]
  },
  {
    nombre: 'OtRepuestoUtilizado',
    tabla: 'ot_repuesto_utilizado',
    prefijo: '—',
    rf: 'Hoja 14',
    descripcion: 'Relacion N:M entre OrdenTrabajo y Repuesto con cantidad utilizada.',
    campos: [
      { nombre: 'orden_trabajo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a OrdenTrabajo.id. PK compuesta' },
      { nombre: 'repuesto_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Repuesto.id. PK compuesta' },
      { nombre: 'cantidad_utilizada', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Cantidad del repuesto consumida en la OT' }
    ]
  },
  {
    nombre: 'Detalles_Evento',
    tabla: '—',
    prefijo: '—',
    rf: 'Hoja 15',
    descripcion: 'NO IMPLEMENTADA. Tabla de detalles especificos de eventos segun tipo.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: false, oblig: true, desc: 'Identificador unico' },
      { nombre: 'tipo_detalle', tipo: 'TEXT', rf: true, impl: false, oblig: true, desc: 'Tipo: OT, Calibracion, Firmware, etc.' },
      { nombre: 'contenido_detalle', tipo: 'TEXT JSON', rf: true, impl: false, oblig: false, desc: 'Contenido JSON con informacion especifica del evento' }
    ]
  },
  {
    nombre: 'OtCostoAdicional',
    tabla: 'otcostoadicional',
    prefijo: '—',
    rf: 'RF11 v0.9.1',
    descripcion: 'Costo adicional asociado a una OT. Reemplaza los campos obsoletos costo_adicional y costos_adicionales.',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'orden_trabajo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a OrdenTrabajo.id' },
      { nombre: 'tipo_costo', tipo: 'TEXT (enum)', rf: true, impl: true, oblig: true, desc: 'Enum: Transporte, Servicio Externo, Repuesto No Inv., Herramienta Renta, Honorarios/Mano de Obra, Insumos/Materiales, Viaticos, Otro' },
      { nombre: 'descripcion_costo', tipo: 'TEXT', rf: true, impl: true, oblig: true, desc: 'Descripcion del concepto del costo' },
      { nombre: 'monto_costo', tipo: 'REAL', rf: true, impl: true, oblig: true, desc: 'Monto del costo (numero positivo)' },
      { nombre: 'fecha_registro', tipo: 'DATE', rf: true, impl: true, oblig: false, desc: 'Fecha del costo (default = hoy)' },
      { nombre: 'fecha_creacion', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha de creacion en sistema (auditoria)' },
      { nombre: 'subido_por', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Username del usuario que registro el costo' }
    ]
  },
  {
    nombre: 'Contrato',
    tabla: 'contrato',
    prefijo: '—',
    rf: 'RF12 v0.9.2',
    descripcion: 'Contrato de mantenimiento/servicio con un proveedor. activo se calcula en runtime (no se guarda).',
    campos: [
      { nombre: 'id', tipo: 'INTEGER', rf: true, impl: true, oblig: true, desc: 'Identificador unico autoincremental' },
      { nombre: 'proveedor_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Proveedor.id' },
      { nombre: 'tipo_contrato', tipo: 'TEXT (enum)', rf: true, impl: true, oblig: true, desc: 'Enum: Comodato, Mantenimiento Preventivo, Mantenimiento Correctivo, Leasing, Garantia Extendida, Soporte Tecnico, Servicio Integral, Otro' },
      { nombre: 'fecha_inicio', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha de inicio de vigencia' },
      { nombre: 'fecha_fin', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha de fin de vigencia' },
      { nombre: 'costo_total', tipo: 'REAL', rf: true, impl: true, oblig: false, desc: 'Costo total del contrato (si periodicidad = Unico)' },
      { nombre: 'costo_periodico', tipo: 'REAL', rf: true, impl: true, oblig: false, desc: 'Costo periodico (si periodicidad != Unico)' },
      { nombre: 'periodicidad_costo', tipo: 'TEXT (enum)', rf: true, impl: true, oblig: false, desc: 'Enum: Unico, Mensual, Trimestral, Semestral, Anual' },
      { nombre: 'moneda', tipo: 'TEXT (enum)', rf: true, impl: true, oblig: false, desc: 'v0.9.15: Solo BOB (Bolivianos) para todo el proyecto' },
      { nombre: 'cobertura_detalle', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Descripcion de lo que cubre el contrato' },
      { nombre: 'tiempo_respuesta', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Tiempo maximo de respuesta del proveedor (ej: 24 hs)' },
      { nombre: 'horario_servicio', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Horario de servicio acordado (ej: Lun-Vie 8-18hs)' },
      { nombre: 'notas', tipo: 'TEXT', rf: true, impl: true, oblig: false, desc: 'Notas o comentarios adicionales' },
      { nombre: 'fecha_creacion', tipo: 'DATETIME', rf: true, impl: true, oblig: true, desc: 'Fecha de creacion en sistema (auditoria)' }
    ]
  },
  {
    nombre: 'ContratoEquipo',
    tabla: 'contrato_equipo',
    prefijo: '—',
    rf: 'RF12 v0.9.2',
    descripcion: 'Relacion N:M entre Contrato y Equipo. Un contrato puede cubrir 0, 1 o N equipos.',
    campos: [
      { nombre: 'contrato_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Contrato.id. PK compuesta' },
      { nombre: 'equipo_id', tipo: 'INTEGER FK', rf: true, impl: true, oblig: true, desc: 'FK a Equipo.id. PK compuesta' }
    ]
  }
]

const modulos = [
  {
    emoji: '📊', nombre: 'Inicio (Dashboard)', ruta: '/inicio',
    descripcion: 'Panel principal con resumen general del sistema. Muestra metricas clave en tarjetas y graficos interactivos.',
    funcionalidades: ['5 tarjetas de metricas en tiempo real', 'Graficos de equipos por estado, ordenes por prioridad y estado', 'Sugerencias automaticas con enlaces directos']
  },
  {
    emoji: '⚙️', nombre: 'Equipos', ruta: '/equipos',
    descripcion: 'Gestion completa de equipos biomedicos con CRUD, imagenes, documentos, Excel y filtros combinados.',
    funcionalidades: ['CRUD completo', '19 estados predefinidos', 'Imagen principal y documentos adjuntos', 'Importacion masiva Excel/CSV', 'Plantilla Excel/CSV estatica en /plantillas/', 'Filtros combinados AND', 'Historial por equipo']
  },
  {
    emoji: '🔧', nombre: 'Ordenes de Trabajo', ruta: '/ordenes',
    descripcion: 'Gestion de OTs para mantenimiento correctivo y preventivo con descuento automatico de stock.',
    funcionalidades: ['CRUD completo', '5 estados de OT', '4 niveles de prioridad', 'Repuestos utilizados con descuento automatico', 'Evento automatico en Historial al completar', 'Documentos adjuntos por OT']
  },
  {
    emoji: '🔩', nombre: 'Inventario (Repuestos + Herramientas)', ruta: '/inventario',
    descripcion: 'Gestion de inventario dividida en Repuestos y Herramientas. Ambos soportan imagen, documentos e importacion Excel.',
    funcionalidades: ['Repuestos: CRUD con datos tecnicos y stock', 'Herramientas: CRUD con categorias y estado de uso', 'Alerta de stock bajo', 'Importacion masiva Excel/CSV', 'Plantillas Excel/CSV estaticas en /plantillas/', 'Imagen y documentos adjuntos']
  },
  {
    emoji: '🛡️', nombre: 'Preventivo', ruta: '/preventivo',
    descripcion: 'Planificacion de mantenimiento preventivo con frecuencia en dias, kit de repuestos, calendario visual y busqueda avanzada.',
    funcionalidades: ['CRUD de tareas preventivas', 'Calculo automatico de proxima fecha', 'Kit de repuestos requeridos', 'Generacion de OT desde tarea', 'Actualizacion automatica al completar OT preventiva', 'Calendario visual mensual (RF10)', 'Resumen de estado: vencidas, hoy, proximas', 'Detalle de tarea desde calendario', 'Busqueda por titulo, equipo, responsable', 'Filtros: equipo, ubicacion, responsable, estado']
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
    emoji: '🏢', nombre: 'Proveedores', ruta: '/proveedores',
    descripcion: 'Directorio centralizado de empresas proveedoras y sus contactos especificos (RF10).',
    funcionalidades: ['CRUD de proveedores (RF10) con campo ciudad', 'CRUD de contactos asociados (uno a muchos)', 'Busqueda por empresa, email, telefono o ciudad', 'Filtros por ciudad y pagina web', 'Importacion masiva Excel/CSV (upsert por nombre_empresa)', 'Plantilla Excel/CSV estatica descargable desde /plantillas/ (sin backend)', 'Detalle con contactos embebidos en modal', 'Vinculacion futura con equipos (RF01) y repuestos (RF04)']
  },
  {
    emoji: '⚙️', nombre: 'Configuracion', ruta: '/configuracion',
    descripcion: 'Gestion del sistema con 3 capas de recuperacion y configuracion editable de empresa y directorios.',
    funcionalidades: ['Capa 1: Metadatos .meta.json', 'Capa 2: Escaneo y recuperacion', 'Capa 3: Backup/Restore JSON', 'Nombre del sistema editable', 'Directorios configurables', 'Mover archivos a otra particion']
  }
]

// ─── Requisitos Funcionales (desde xlsx) ───
const requisitosRF = [
  {
    id: 'RF01', nombre: 'Gestion de Activos v0.9.0 (Universal)', entidad: 'Equipo',
    descripcion: 'Registro y gestion de equipos biomedicos (universal, sin contexto Bolivia). Campos obsoletos eliminados (registro_sanitario, calibracion, responsable). Nuevos: observaciones, fecha_inicio_garantia, condicion_origen, proveedor_principal_id (FK).',
    camposRF: 16, implementados: 16, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: [],
    estado: 'Completo v0.9.0'
  },
  {
    id: 'RF02', nombre: 'Gestion de OT v0.9.2', entidad: 'OrdenTrabajo',
    descripcion: 'Gestion de ordenes de trabajo correctivas y preventivas. v0.9.1: costos via OtCostoAdicional (RF11). v0.9.2: contrato_id opcional (RF12).',
    camposRF: 14, implementados: 11, faltantes: 3, extras: 2,
    detalleFaltantes: ['tiempo_estimado_horas', 'categoria_accion', 'firma_digital_tecnico'],
    detalleExtras: ['unidad_tiempo', 'contrato_id (RF12)'],
    estado: '3 campos RF faltantes'
  },
  {
    id: 'RF03', nombre: 'Mantenimiento Preventivo v0.9.2', entidad: 'TareaPreventiva',
    descripcion: 'Planificacion de tareas preventivas con ciclo verde-amarillo-rojo. proxima_fecha editable (no auto-calculada). frecuencia_dias como sugerencia.',
    camposRF: 13, implementados: 9, faltantes: 4, extras: 1,
    detalleFaltantes: ['periodicidad_tipo (Dias/Horas/Ciclos) — v1.0', 'condiciones_activacion (JSON) — v1.0', 'logica_periodicidad (JSON) — v1.0', 'contador_acumulado — v1.0'],
    detalleExtras: ['estado_recordatorio (calculado en runtime)'],
    estado: '9/13 implementados. 4 pendientes v1.0'
  },
  {
    id: 'RF04', nombre: 'Gestion de Inventario', entidad: 'Repuesto',
    descripcion: 'Control de inventario de repuestos con stock, alertas, especificaciones tecnicas y precios.',
    camposRF: 14, implementados: 13, faltantes: 1, extras: 1,
    detalleFaltantes: ['codigo_equivalente'],
    detalleExtras: ['numero_serie'],
    estado: '1 campo RF faltante'
  },
  {
    id: 'RF05', nombre: 'Historial de Mantenimiento', entidad: 'EventoHistorial',
    descripcion: 'Registro cronologico de eventos de mantenimiento con detalles, costos y tecnicos.',
    camposRF: 9, implementados: 6, faltantes: 3, extras: 5,
    detalleFaltantes: ['estado_ot_relacionada', 'evento_detalle_id', 'evento_detalle_tipo'],
    detalleExtras: ['orden_trabajo_id', 'acciones_realizadas', 'tiempo_invertido', 'costo', 'repuestos_utilizados'],
    estado: '3 campos RF faltantes + 5 extras'
  },
  {
    id: 'RF06', nombre: 'Reporting', entidad: 'Reportes',
    descripcion: '6 reportes con graficos interactivos y filtros por rango de fechas.',
    camposRF: 7, implementados: 6, faltantes: 1, extras: 0,
    detalleFaltantes: ['REP-07: Repuestos Utilizados (Consumo detallado por equipo/tecnico/periodo)'],
    detalleExtras: [],
    estado: '1 reporte faltante'
  },
  {
    id: 'RF07', nombre: 'Modulo IA', entidad: 'Sistema',
    descripcion: 'Sugerencias inteligentes basadas en descripcion de falla, historial e inventario.',
    camposRF: 3, implementados: 0, faltantes: 3, extras: 0,
    detalleFaltantes: ['NLP procesamiento de descripcion_falla', 'Modelos de clasificacion/similitud', 'Sugerencias de acciones, categorias y repuestos'],
    detalleExtras: [],
    estado: 'No implementado'
  },
  {
    id: 'RF08', nombre: 'Autenticacion', entidad: 'Usuario',
    descripcion: 'Autenticacion y autorizacion basica con roles y JWT.',
    camposRF: 7, implementados: 7, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: [],
    estado: 'Completo'
  },
  {
    id: 'RF09', nombre: 'Herramientas y Materiales', entidad: 'Herramienta',
    descripcion: 'Gestion de herramientas y materiales del taller con categorias, estado de uso y costos.',
    camposRF: 15, implementados: 14, faltantes: 1, extras: 0,
    detalleFaltantes: ['fecha_registro'],
    detalleExtras: [],
    estado: '1 campo RF faltante'
  },
  {
    id: 'RF10', nombre: 'Gestion de Proveedores y Contactos', entidad: 'Proveedor + ContactoProveedor',
    descripcion: 'Directorio centralizado de empresas proveedoras y sus contactos especificos (gerente, vendedor, soporte). Incluye CRUD de proveedores con campo ciudad, CRUD de contactos asociados (1:N), importacion masiva Excel/CSV y filtros avanzados.',
    camposRF: 15, implementados: 15, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: [],
    estado: 'Completo con importacion Excel'
  },
  {
    id: 'RF11', nombre: 'Gestion Detallada de Costos en OT v0.9.1', entidad: 'OtCostoAdicional',
    descripcion: 'Registro de multiples costos individuales (con descripcion, tipo y monto) asociados a una OT. 8 tipos de costo. Total automatico. Documentos justificativos via DocumentoAdjunto con ot_costo_id.',
    camposRF: 8, implementados: 8, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: [],
    estado: 'Completo v0.9.1'
  },
  {
    id: 'RF12', nombre: 'Gestion de Contratos v0.9.2', entidad: 'Contrato + ContratoEquipo',
    descripcion: 'Contratos de mantenimiento/servicio con proveedores. Relacion N:M con equipos. Calculo de vigencia en runtime. 3 enums estrictos. Badges visuales. Pagina dedicada + secciones en Equipo y Proveedor. FK opcional en OrdenTrabajo.',
    camposRF: 14, implementados: 14, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: [],
    estado: 'Completo v0.9.2'
  },
  {
    id: 'RF13', nombre: 'Exportacion de Datos', entidad: 'Sistema',
    descripcion: 'Exportacion de registros en formato Excel/CSV para uso externo (reportes, respaldos, auditorias).',
    camposRF: 0, implementados: 0, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: ['Export Excel en Equipos, OTs, Contratos (v0.9.3 parcial)'],
    estado: 'Parcial v0.9.3'
  },
  {
    id: 'RF03+', nombre: 'MP Rediseñado (Ciclo Verde-Amarillo-Rojo) v0.9.2', entidad: 'TareaPreventiva',
    descripcion: 'Rediseño del modulo de MP: 🟢 Programada (OT activa), 🟡 Recordatorio, 🔴 Vencida. proxima_fecha editable. frecuencia_dias como sugerencia. Calendario unificado en pagina Planificacion.',
    camposRF: 9, implementados: 9, faltantes: 0, extras: 1,
    detalleFaltantes: [],
    detalleExtras: ['estado_recordatorio (calculado en runtime)'],
    estado: 'Completo v0.9.2'
  },
  {
    id: 'PLAN', nombre: 'Pagina Planificacion v0.9.2', entidad: 'Sistema',
    descripcion: 'Calendario mensual unificado OT + MP. Filtros: Tipo, Equipo, Ubicacion, Responsable. Colores del ciclo MP + colores de OT por estado. Click en evento abre detalle.',
    camposRF: 0, implementados: 0, faltantes: 0, extras: 0,
    detalleFaltantes: [],
    detalleExtras: ['Calendario mensual unificado', 'Resumen rapido', 'Leyenda visual', 'Modal detalle con navegacion'],
    estado: 'Implementado v0.9.2'
  }
]

// ─── Requisitos No Funcionales (Hoja 16) ───
const rnfItems = [
  { id: 'RNF01', cat: 'Disponibilidad', req: 'Operacion offline-first completa', estado: 'Implementado', nota: 'El sistema funciona 100% local sin internet' },
  { id: 'RNF02', cat: 'Rendimiento', req: 'CRUD basico en menos de 2 segundos', estado: 'Implementado', nota: 'SQLite local responde en milisegundos' },
  { id: 'RNF03', cat: 'Portabilidad', req: 'Multiplataforma (Windows, Linux, macOS)', estado: 'Parcial', nota: 'Frontend web + Backend Python. Falta empaquetado desktop' },
  { id: 'RNF04', cat: 'Seguridad', req: 'Hashing bcrypt + autenticacion', estado: 'Implementado', nota: 'JWT + bcrypt + roles admin/tecnico' },
  { id: 'RNF05', cat: 'Usabilidad', req: 'Interfaz clara, intuitiva, busquedas rapidas', estado: 'Implementado', nota: 'Vue 3 con filtros, busquedas y navegacion sencilla' },
  { id: 'RNF06', cat: 'Escalabilidad', req: 'Arquitectura para sincronizacion multi-sede futura', estado: 'Pendiente', nota: 'Arquitectura preparada, no implementado aun' },
  { id: 'RNF07', cat: 'Mantenibilidad', req: 'Codigo documentado, SOLID, licencia open source', estado: 'Implementado', nota: 'Codigo abierto, estructura modular' }
]

// ─── Reportes RF06 ───
const reportesRF06 = [
  { id: 'REP-01', nombre: 'Listado de Equipos', estado: 'Implementado', nota: 'En modulo Equipos con filtros' },
  { id: 'REP-02', nombre: 'OTs Pendientes', estado: 'Implementado', nota: 'En modulo Reportes, reporte OTs por periodo' },
  { id: 'REP-03', nombre: 'Historial por Equipo', estado: 'Implementado', nota: 'En modulo Historial + Reportes mantenimiento por equipo' },
  { id: 'REP-04', nombre: 'Actividad de Mantenimiento', estado: 'Implementado', nota: 'En modulo Reportes, cumplimiento preventivo' },
  { id: 'REP-05', nombre: 'Costos por Equipo/Periodo', estado: 'Implementado', nota: 'En modulo Reportes, analisis de costos' },
  { id: 'REP-06', nombre: 'Disponibilidad de Equipos', estado: 'Implementado', nota: 'En modulo Reportes, disponibilidad' },
  { id: 'REP-07', nombre: 'Repuestos Utilizados (Consumo)', estado: 'No implementado', nota: 'Falta reporte detallado de consumo por equipo/tecnico/periodo' }
]

// ─── RF10: Relaciones con otros RF ───
const rf10Relaciones = [
  {
    rf: 'RF01',
    entidad: 'Equipo',
    campoActual: 'proveedor_principal (TEXT)',
    objetivo: 'Convertir equipo.proveedor_principal en FK a Proveedor.id',
    estado: 'Planificado',
    detalle: 'Actualmente el campo proveedor_principal es texto libre. La migracion a FK permitira centralizar la informacion del proveedor y reutilizarla en todos los equipos que compra a ese proveedor.'
  },
  {
    rf: 'RF04',
    entidad: 'Repuesto',
    campoActual: 'proveedor_ultimo (TEXT)',
    objetivo: 'Convertir repuesto.proveedor_ultimo en FK a Proveedor.id',
    estado: 'Planificado',
    detalle: 'Actualmente el campo proveedor_ultimo es texto libre. La migracion a FK permitira trazabilidad completa del proveedor de cada repuesto.'
  },
  {
    rf: 'RF09',
    entidad: 'Herramienta',
    campoActual: 'proveedor_ultimo (TEXT)',
    objetivo: 'Convertir herramienta.proveedor_ultimo en FK a Proveedor.id',
    estado: 'Planificado',
    detalle: 'Las herramientas del taller tambien se compran a proveedores. La FK permitira gestionar de forma unificada el directorio de proveedores.'
  },
  {
    rf: 'RF03 / RF05',
    entidad: 'TareaPreventiva / EventoHistorial',
    campoActual: 'Sin vinculo directo',
    objetivo: 'Asociar contratos de mantenimiento y servicios con proveedores',
    estado: 'Futuro',
    detalle: 'Permitira registrar que empresa externa ejecuta cada mantenimiento preventivo o evento de calibracion/verificacion. Mejora la trazabilidad de servicios contratados.'
  }
]

const pendientes = [
  { emoji: '🧠', nombre: 'Modulo IA (RF07)', prioridad: 'Alta', descripcion: 'Sugerencias automaticas basadas en descripcion de falla, historial e inventario usando NLP y modelos de clasificacion.', estado: 'No implementado', rf: 'RF07' },
  { emoji: '🔒', nombre: 'Proteccion de rutas por autenticacion', prioridad: 'Alta', descripcion: 'Validar token JWT en endpoints y navigation guards en frontend.', estado: 'No implementado', rf: 'RNF04' },
  { emoji: '🏢', nombre: 'Gestion de Proveedores (RF10) - Importacion Excel', prioridad: 'Media', descripcion: 'CRUD de proveedores con campo ciudad, contactos asociados (1:N) e importacion masiva Excel/CSV. Pendiente: convertir los campos de texto proveedor_principal (Equipo) y proveedor_ultimo (Repuesto/Herramienta) en FK a Proveedor.id.', estado: 'Implementado', rf: 'RF10' },
  { emoji: '📄', nombre: 'Paginacion en listados', prioridad: 'Media', descripcion: 'Implementar offset/limit en endpoints de listado.', estado: 'No implementado', rf: 'RNF02' },
  { emoji: '🔐', nombre: 'Secret JWT configurable', prioridad: 'Media', descripcion: 'Mover secreto JWT a variable de entorno o config.json.', estado: 'No implementado', rf: 'RNF04' },
  { emoji: '📊', nombre: 'Reporte REP-07: Consumo de Repuestos', prioridad: 'Media', descripcion: 'Reporte detallado de repuestos utilizados por equipo, tecnico o periodo.', estado: 'No implementado', rf: 'RF06' },
  { emoji: '🔧', nombre: 'Campos RF faltantes en OT (RF02)', prioridad: 'Media', descripcion: 'tiempo_estimado_horas, categoria_accion, firma_digital_tecnico', estado: 'No implementado', rf: 'RF02' },
  { emoji: '🛡️', nombre: 'Campos RF faltantes en Preventivo (RF03)', prioridad: 'Media', descripcion: 'periodicidad_tipo, condiciones_activacion, logica_periodicidad, contador_acumulado', estado: 'No implementado', rf: 'RF03' },
  { emoji: '🔩', nombre: 'Campos RF faltantes en Repuesto (RF04)', prioridad: 'Baja', descripcion: 'codigo_equivalente (codigo alternativo OEM/generico)', estado: 'No implementado', rf: 'RF04' },
  { emoji: '📜', nombre: 'Campos RF faltantes en Historial (RF05)', prioridad: 'Media', descripcion: 'estado_ot_relacionada, evento_detalle_id, evento_detalle_tipo (requiere tabla Detalles_Evento)', estado: 'No implementado', rf: 'RF05' },
  { emoji: '🛠️', nombre: 'Tabla Detalles_Evento (Hoja 15)', prioridad: 'Baja', descripcion: 'Tabla de detalles especificos por tipo de evento (JSON). No implementada.', estado: 'No implementado', rf: 'Hoja 15' },
  { emoji: '📦', nombre: 'Empaquetado desktop (RNF03)', prioridad: 'Baja', descripcion: 'Empaquetar como aplicacion desktop multiplataforma.', estado: 'No implementado', rf: 'RNF03' },
  { emoji: '🌐', nombre: 'Sincronizacion multi-sede (RNF06)', prioridad: 'Baja', descripcion: 'Arquitectura para sincronizar datos entre sedes.', estado: 'No implementado', rf: 'RNF06' }
]

const archivosEstructura = [
  { carpeta: 'uploads/EQUIPOS/', descripcion: 'Imagenes y documentos de equipos', patron: 'E0001_Nombre/E0001_Nombre.jpg' },
  { carpeta: 'uploads/REPUESTOS/', descripcion: 'Imagenes y documentos de repuestos', patron: 'R0001_Nombre/R0001_Nombre.png' },
  { carpeta: 'uploads/HERRAMIENTAS/', descripcion: 'Imagenes y documentos de herramientas', patron: 'H0001_Nombre/H0001_Nombre.jpg' },
  { carpeta: 'uploads/EQUIPOS/E0001_xxx/DOC/', descripcion: 'Documentos adjuntos de un equipo', patron: 'manual_usuario.pdf, foto_dano.jpg' },
  { carpeta: 'frontend/public/plantillas/', descripcion: 'Plantillas Excel/CSV descargables desde la UI', patron: 'plantilla_equipos.xlsx, plantilla_proveedores.csv, etc.' }
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

// ─── Computed ───
const filtroEntidad = ref('')

const entidadesFiltradas = computed(() => {
  if (!filtroEntidad.value) return entidades
  const q = filtroEntidad.value.toLowerCase()
  return entidades.filter(e =>
    e.nombre.toLowerCase().includes(q) ||
    e.rf.toLowerCase().includes(q) ||
    e.tabla.toLowerCase().includes(q)
  )
})

const resumenRF = computed(() => {
  const totalCamposRF = requisitosRF.reduce((s, r) => s + r.camposRF, 0)
  const totalImplementados = requisitosRF.reduce((s, r) => s + r.implementados, 0)
  const totalFaltantes = requisitosRF.reduce((s, r) => s + r.faltantes, 0)
  const totalExtras = requisitosRF.reduce((s, r) => s + r.extras, 0)
  return { totalCamposRF, totalImplementados, totalFaltantes, totalExtras }
})

function getCampoStatus(campo) {
  if (campo.rf && campo.impl) return 'rf-impl'       // 🟢 En RF, implementado
  if (!campo.rf && campo.impl) return 'extra'        // 🟡 Extra, no en RF
  if (campo.rf && !campo.impl) return 'faltante'     // 🔴 En RF, no implementado
  return 'otro'
}

function getCampoIcon(campo) {
  if (campo.rf && campo.impl) return '🟢'
  if (!campo.rf && campo.impl) return '🟡'
  if (campo.rf && !campo.impl) return '🔴'
  return '⚪'
}

function getEstadoClass(estado) {
  if (estado === 'Completo' || estado === 'Completo con extras' || estado === 'Implementado') return 'estado-ok'
  if (estado.includes('faltante') || estado === 'No implementado') return 'estado-faltante'
  if (estado === 'Parcial' || estado === 'Pendiente') return 'estado-pendiente'
  return 'estado-ok'
}
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
          <p><strong>CMMS-BioAI</strong> es un Sistema de Gestion de Mantenimiento Asistido por Computadora diseñado para <strong>equipos biomedicos</strong> en el contexto boliviano. Proyecto de Maestria en Ingenieria Biomedica.</p>
          <p>Permite registrar equipos biomedicos, gestionar OTs, controlar inventario de repuestos y herramientas, planificar mantenimiento preventivo y generar reportes analiticos.</p>
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
        <div class="help-card">
          <h3>Resumen de Requisitos Funcionales</h3>
          <div class="resumen-grid">
            <div class="resumen-card resumen-card--green">
              <div class="resumen-num">{{ resumenRF.totalImplementados }}</div>
              <div class="resumen-label">Campos RF implementados</div>
            </div>
            <div class="resumen-card resumen-card--red">
              <div class="resumen-num">{{ resumenRF.totalFaltantes }}</div>
              <div class="resumen-label">Campos RF faltantes</div>
            </div>
            <div class="resumen-card resumen-card--yellow">
              <div class="resumen-num">{{ resumenRF.totalExtras }}</div>
              <div class="resumen-label">Campos extra (no en RF)</div>
            </div>
            <div class="resumen-card resumen-card--blue">
              <div class="resumen-num">{{ resumenRF.totalCamposRF }}</div>
              <div class="resumen-label">Total campos definidos en RF</div>
            </div>
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

      <!-- ENTIDADES (completo con todos los campos) -->
      <section v-if="seccionActiva === 'entidades'" class="help-section">
        <div class="help-card help-card--info">
          <h3>Modelos de Datos - Campos Completos</h3>
          <p>El sistema gestiona 13 tablas en SQLite. Cada entidad muestra <strong>todos</strong> sus campos con indicador de estado respecto a los Requisitos Funcionales:</p>
          <div class="leyenda">
            <span class="leyenda-item"><span class="dot dot-green"></span> Campo del RF, implementado</span>
            <span class="leyenda-item"><span class="dot dot-yellow"></span> Campo extra, no esta en RF</span>
            <span class="leyenda-item"><span class="dot dot-red"></span> Campo del RF, NO implementado</span>
          </div>
          <div class="filtro-row">
            <input v-model="filtroEntidad" type="text" placeholder="Buscar entidad o RF..." class="filtro-input" />
          </div>
        </div>
        <div v-for="ent in entidadesFiltradas" :key="ent.nombre" class="help-card help-card--entidad">
          <div class="entidad-header">
            <h3>{{ ent.nombre }}</h3>
            <span class="entidad-tabla">{{ ent.tabla }}</span>
            <span class="entidad-rf">{{ ent.rf }}</span>
            <span v-if="ent.prefijo !== '—'" class="entidad-prefijo">Prefijo: {{ ent.prefijo }}</span>
          </div>
          <p class="entidad-desc">{{ ent.descripcion }}</p>
          <div class="campos-table">
            <div class="campo-row campo-row--header">
              <span class="c-status"></span>
              <span class="c-nombre">Campo</span>
              <span class="c-tipo">Tipo</span>
              <span class="c-oblig">Oblig.</span>
              <span class="c-desc">Descripcion</span>
            </div>
            <div v-for="campo in ent.campos" :key="campo.nombre" class="campo-row" :class="'campo-row--' + getCampoStatus(campo)">
              <span class="c-status">{{ getCampoIcon(campo) }}</span>
              <span class="c-nombre"><code>{{ campo.nombre }}</code></span>
              <span class="c-tipo">{{ campo.tipo }}</span>
              <span class="c-oblig">{{ campo.oblig ? 'Si' : 'No' }}</span>
              <span class="c-desc">{{ campo.desc }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- REQUISITOS FUNCIONALES -->
      <section v-if="seccionActiva === 'rf'" class="help-section">
        <div class="help-card help-card--info">
          <h3>Analisis de Requisitos Funcionales (RF)</h3>
          <p>Comparacion detallada entre los Requisitos Funcionales definidos en la documentacion del proyecto y la implementacion actual del sistema. Datos extraidos de la carpeta <code>Requisitos Funcionales (RF)/</code></p>
        </div>

        <!-- Resumen visual -->
        <div class="help-card">
          <h3>Resumen General</h3>
          <div class="resumen-grid">
            <div class="resumen-card resumen-card--green">
              <div class="resumen-num">{{ resumenRF.totalImplementados }}</div>
              <div class="resumen-label">Campos RF implementados</div>
            </div>
            <div class="resumen-card resumen-card--red">
              <div class="resumen-num">{{ resumenRF.totalFaltantes }}</div>
              <div class="resumen-label">Campos RF faltantes</div>
            </div>
            <div class="resumen-card resumen-card--yellow">
              <div class="resumen-num">{{ resumenRF.totalExtras }}</div>
              <div class="resumen-label">Campos extra (no en RF)</div>
            </div>
            <div class="resumen-card resumen-card--blue">
              <div class="resumen-num">{{ resumenRF.totalCamposRF }}</div>
              <div class="resumen-label">Total campos definidos en RF</div>
            </div>
          </div>
        </div>

        <!-- Cada RF -->
        <div v-for="rf in requisitosRF" :key="rf.id" class="help-card help-card--rf">
          <div class="rf-header">
            <span class="rf-id">{{ rf.id }}</span>
            <div class="rf-title-area">
              <h3>{{ rf.nombre }}</h3>
              <span class="rf-entidad">Entidad: {{ rf.entidad }}</span>
            </div>
            <span class="rf-estado" :class="getEstadoClass(rf.estado)">{{ rf.estado }}</span>
          </div>
          <p class="rf-desc">{{ rf.descripcion }}</p>
          <div class="rf-stats">
            <span class="rf-stat rf-stat--green">Implementados: {{ rf.implementados }}/{{ rf.camposRF }}</span>
            <span v-if="rf.faltantes > 0" class="rf-stat rf-stat--red">Faltantes: {{ rf.faltantes }}</span>
            <span v-if="rf.extras > 0" class="rf-stat rf-stat--yellow">Extras: {{ rf.extras }}</span>
          </div>
          <div v-if="rf.detalleFaltantes.length > 0" class="rf-detail rf-detail--red">
            <h4>Campos RF faltantes:</h4>
            <ul>
              <li v-for="f in rf.detalleFaltantes" :key="f">{{ f }}</li>
            </ul>
          </div>
          <div v-if="rf.detalleExtras.length > 0" class="rf-detail rf-detail--yellow">
            <h4>Campos extra (no en RF):</h4>
            <ul>
              <li v-for="e in rf.detalleExtras" :key="e">{{ e }}</li>
            </ul>
          </div>
        </div>

        <!-- RF06 Detalle de reportes -->
        <div class="help-card">
          <h3>RF06 - Reportes: Estado Detallado</h3>
          <div class="reportes-grid">
            <div v-for="rep in reportesRF06" :key="rep.id" class="reporte-card" :class="rep.estado === 'Implementado' ? 'reporte-card--ok' : 'reporte-card--no'">
              <div class="rep-id">{{ rep.id }}</div>
              <div class="rep-nombre">{{ rep.nombre }}</div>
              <div class="rep-estado">{{ rep.estado }}</div>
              <div class="rep-nota">{{ rep.nota }}</div>
            </div>
          </div>
        </div>

        <!-- RF10: Relaciones con otros RF -->
        <div class="help-card help-card--rf10">
          <h3>RF10 - Proveedores: Relaciones con otros RF</h3>
          <p>El modulo de Proveedores (RF10) es <strong>transversal</strong>: centraliza el directorio de empresas proveedoras y, en futuras versiones, reemplazara los campos de texto libre en otras entidades por FK a <code>Proveedor.id</code>. Esto permite tener informacion consistente y un unico punto de actualizacion.</p>
          <div class="rf10-relaciones">
            <div v-for="rel in rf10Relaciones" :key="rel.rf" class="rf10-rel-card">
              <div class="rf10-rel-header">
                <span class="rf10-rel-rf">{{ rel.rf }}</span>
                <span class="rf10-rel-entidad">{{ rel.entidad }}</span>
                <span class="rf10-rel-estado" :class="rel.estado === 'Planificado' ? 'estado-pendiente' : 'estado-faltante'">{{ rel.estado }}</span>
              </div>
              <div class="rf10-rel-campo"><strong>Campo actual:</strong> <code>{{ rel.campoActual }}</code></div>
              <div class="rf10-rel-objetivo"><strong>Objetivo:</strong> {{ rel.objetivo }}</div>
              <div class="rf10-rel-detalle">{{ rel.detalle }}</div>
            </div>
          </div>
        </div>

        <!-- RNF -->
        <div class="help-card">
          <h3>Requisitos No Funcionales (RNF - Hoja 16)</h3>
          <div class="rnf-table">
            <div class="rnf-row rnf-row--header">
              <span class="rnf-id">ID</span>
              <span class="rnf-cat">Categoria</span>
              <span class="rnf-req">Requisito</span>
              <span class="rnf-estado">Estado</span>
            </div>
            <div v-for="rnf in rnfItems" :key="rnf.id" class="rnf-row">
              <span class="rnf-id">{{ rnf.id }}</span>
              <span class="rnf-cat">{{ rnf.cat }}</span>
              <span class="rnf-req">{{ rnf.req }}</span>
              <span class="rnf-estado" :class="rnf.estado === 'Implementado' ? 'estado-ok' : rnf.estado === 'Parcial' ? 'estado-pendiente' : 'estado-faltante'">{{ rnf.estado }}</span>
            </div>
          </div>
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
            <div class="capa-card capa-card--done"><span class="capa-num">2</span><h4>Escaneo y Recuperacion</h4><p><strong>IMPLEMENTADO (v0.8.3)</strong></p></div>
            <div class="capa-card capa-card--done"><span class="capa-num">3</span><h4>Backup y Restore</h4><p><strong>IMPLEMENTADO</strong></p></div>
          </div>
          <div class="capa2-detalle">
            <h4>Capa 2 — Que escanea y recupera (v0.8.3):</h4>
            <ul>
              <li><strong>Equipos, Repuestos, Herramientas</strong>: si existen en archivos (<code>.meta.json</code>) pero no en BD, se crean como nuevos registros.</li>
              <li><strong>Imagenes faltantes</strong>: si el registro existe en BD pero sin <code>imagen_ruta</code> y el <code>.meta.json</code> lo tiene, se sincroniza automaticamente.</li>
              <li><strong>Ordenes de Trabajo</strong>: si existe el <code>.txt</code> de referencia en <code>uploads/OT/</code> pero la OT no esta en BD, se reconstruye con su titulo, prioridad y equipo asociado.</li>
              <li><strong>Documentos</strong>: se escanean carpetas <code>DOC/</code> de cada entidad <strong>Y</strong> carpetas <code>OT/OTxxxx/</code> dentro de cada equipo para recuperar documentos huérfanos (incluyendo los de OTs).</li>
            </ul>
          </div>
        </div>
      </section>

      <!-- PENDIENTES -->
      <section v-if="seccionActiva === 'pendientes'" class="help-section">
        <div class="help-card help-card--warning">
          <h3>Funcionalidades Pendientes</h3>
          <p>Lista de funcionalidades aun no implementadas o parcialmente completadas, vinculadas a sus Requisitos Funcionales.</p>
        </div>
        <div v-for="pend in pendientes" :key="pend.nombre" class="help-card help-card--pendiente">
          <div class="pendiente-header">
            <span class="pendiente-emoji">{{ pend.emoji }}</span>
            <div>
              <h3>{{ pend.nombre }}</h3>
              <div class="pendiente-badges">
                <span class="pendiente-prioridad" :class="'prioridad--' + pend.prioridad.toLowerCase()">{{ pend.prioridad }}</span>
                <span class="pendiente-rf">{{ pend.rf }}</span>
              </div>
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
.help-card--info { border-left: 4px solid #6366f1; background: linear-gradient(135deg, #eef2ff 0%, #ffffff 40%); }
.help-card--rf { border-left: 4px solid #3b82f6; }
.help-card--warning { border-left: 4px solid #f59e0b; background: #fffbeb; }
.help-card--pendiente { border-left: 4px solid #ef4444; }

/* Leyenda */
.leyenda { display: flex; gap: 1.25rem; flex-wrap: wrap; margin-top: 0.75rem; }
.leyenda-item { display: flex; align-items: center; gap: 0.35rem; font-size: 0.82rem; color: #475569; }
.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.dot-green { background: #22c55e; }
.dot-yellow { background: #eab308; }
.dot-red { background: #ef4444; }

/* Filtro */
.filtro-row { margin-top: 0.75rem; }
.filtro-input { width: 100%; max-width: 400px; padding: 0.5rem 0.75rem; border: 2px solid #e2e8f0; border-radius: 8px; font-size: 0.88rem; outline: none; transition: border-color 0.2s; }
.filtro-input:focus { border-color: #3b82f6; }

/* Modulos */
.modulo-header { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.75rem; }
.modulo-emoji { font-size: 1.6rem; flex-shrink: 0; }
.modulo-title-row { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }
.modulo-title-row h3 { margin: 0; }
.modulo-link { font-size: 0.82rem; font-weight: 600; color: #3b82f6; text-decoration: none; padding: 0.2rem 0.6rem; border-radius: 4px; background: #eff6ff; transition: background 0.2s; }
.modulo-link:hover { background: #dbeafe; text-decoration: underline; }
.modulo-funcs h4 { margin: 0 0 0.4rem 0; font-size: 0.85rem; color: #1e293b; }
.modulo-funcs ul { margin: 0; padding-left: 1.2rem; color: #475569; font-size: 0.85rem; line-height: 1.7; }

/* Entidades */
.entidad-header { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; margin-bottom: 0.5rem; }
.entidad-header h3 { margin: 0; }
.entidad-tabla { font-size: 0.78rem; font-weight: 600; color: #6366f1; background: #eef2ff; padding: 0.15rem 0.5rem; border-radius: 4px; }
.entidad-rf { font-size: 0.78rem; font-weight: 600; color: #0891b2; background: #ecfeff; padding: 0.15rem 0.5rem; border-radius: 4px; }
.entidad-prefijo { font-size: 0.78rem; font-weight: 600; color: #059669; background: #ecfdf5; padding: 0.15rem 0.5rem; border-radius: 4px; }
.entidad-desc { margin: 0 0 0.75rem 0; color: #475569; font-size: 0.88rem; }

/* Campos table */
.campos-table { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; font-size: 0.78rem; }
.campo-row { display: grid; grid-template-columns: 30px 180px 100px 50px 1fr; border-bottom: 1px solid #f1f5f9; align-items: center; }
.campo-row:last-child { border-bottom: none; }
.campo-row > span { padding: 0.4rem 0.5rem; color: #475569; }
.campo-row--header { background: #f8fafc; font-weight: 700; color: #334155; }
.campo-row--header > span { color: #334155; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.03em; }
.campo-row--rf-impl { background: #f0fdf4; }
.campo-row--extra { background: #fefce8; }
.campo-row--faltante { background: #fef2f2; }
.c-status { text-align: center; }
.c-nombre code { font-size: 0.78rem; background: transparent; padding: 0; }
.campo-row--faltante .c-nombre code { color: #dc2626; }
.campo-row--extra .c-nombre code { color: #ca8a04; }
.c-oblig { text-align: center; font-weight: 600; }
.c-desc { font-size: 0.76rem; line-height: 1.4; }

/* Resumen */
.resumen-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
@media (max-width: 800px) { .resumen-grid { grid-template-columns: repeat(2, 1fr); } }
.resumen-card { padding: 1rem; border-radius: 8px; text-align: center; border: 1px solid; }
.resumen-num { font-size: 1.75rem; font-weight: 800; line-height: 1; }
.resumen-label { font-size: 0.78rem; margin-top: 0.35rem; font-weight: 500; }
.resumen-card--green { background: #f0fdf4; border-color: #86efac; color: #16a34a; }
.resumen-card--red { background: #fef2f2; border-color: #fca5a5; color: #dc2626; }
.resumen-card--yellow { background: #fefce8; border-color: #fde047; color: #ca8a04; }
.resumen-card--blue { background: #eff6ff; border-color: #93c5fd; color: #2563eb; }

/* RF Cards */
.rf-header { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.rf-id { display: inline-flex; align-items: center; justify-content: center; min-width: 52px; height: 28px; border-radius: 6px; background: #3b82f6; color: white; font-weight: 800; font-size: 0.82rem; flex-shrink: 0; }
.rf-title-area { flex: 1; }
.rf-title-area h3 { margin: 0; display: inline; }
.rf-entidad { font-size: 0.75rem; color: #6366f1; margin-left: 0.5rem; }
.rf-estado { font-size: 0.75rem; font-weight: 700; padding: 0.2rem 0.6rem; border-radius: 4px; white-space: nowrap; }
.rf-desc { margin: 0 0 0.5rem 0; color: #475569; font-size: 0.88rem; }
.rf-stats { display: flex; gap: 0.75rem; margin-bottom: 0.5rem; flex-wrap: wrap; }
.rf-stat { font-size: 0.78rem; font-weight: 600; padding: 0.2rem 0.5rem; border-radius: 4px; }
.rf-stat--green { background: #f0fdf4; color: #16a34a; }
.rf-stat--red { background: #fef2f2; color: #dc2626; }
.rf-stat--yellow { background: #fefce8; color: #ca8a04; }
.rf-detail { padding: 0.5rem 0.75rem; border-radius: 6px; margin-top: 0.35rem; }
.rf-detail h4 { margin: 0 0 0.25rem 0; font-size: 0.78rem; color: #1e293b; }
.rf-detail ul { margin: 0; padding-left: 1.2rem; font-size: 0.78rem; line-height: 1.6; }
.rf-detail--red { background: #fef2f2; }
.rf-detail--red li { color: #991b1b; }
.rf-detail--yellow { background: #fefce8; }
.rf-detail--yellow li { color: #854d0e; }

/* Estado badges */
.estado-ok { background: #f0fdf4; color: #16a34a; }
.estado-faltante { background: #fef2f2; color: #dc2626; }
.estado-pendiente { background: #fffbeb; color: #d97706; }

/* RF10 relaciones */
.help-card--rf10 { border-left: 4px solid #0891b2; background: linear-gradient(135deg, #ecfeff 0%, #ffffff 40%); }
.rf10-relaciones { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 0.75rem; margin-top: 0.75rem; }
.rf10-rel-card { background: #ffffff; border: 1px solid #cffafe; border-radius: 8px; padding: 0.85rem; }
.rf10-rel-header { display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap; margin-bottom: 0.5rem; padding-bottom: 0.5rem; border-bottom: 1px dashed #e0f2fe; }
.rf10-rel-rf { display: inline-flex; align-items: center; justify-content: center; min-width: 80px; padding: 0.2rem 0.5rem; border-radius: 4px; background: #0891b2; color: white; font-weight: 700; font-size: 0.78rem; }
.rf10-rel-entidad { font-size: 0.85rem; font-weight: 600; color: #1e293b; flex: 1; }
.rf10-rel-estado { font-size: 0.72rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; white-space: nowrap; }
.rf10-rel-campo, .rf10-rel-objetivo { font-size: 0.82rem; color: #334155; margin: 0.2rem 0; }
.rf10-rel-campo code { background: #f1f5f9; padding: 0.1rem 0.35rem; border-radius: 4px; font-size: 0.78rem; color: #7c3aed; }
.rf10-rel-detalle { font-size: 0.78rem; color: #64748b; line-height: 1.5; margin-top: 0.4rem; padding-top: 0.4rem; border-top: 1px dashed #e0f2fe; }

/* Reportes grid */
.reportes-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.75rem; }
.reporte-card { padding: 0.75rem; border-radius: 8px; border: 1px solid; }
.reporte-card--ok { background: #f0fdf4; border-color: #86efac; }
.reporte-card--no { background: #fef2f2; border-color: #fca5a5; }
.rep-id { font-weight: 800; font-size: 0.78rem; color: #6366f1; }
.rep-nombre { font-weight: 600; font-size: 0.88rem; color: #1e293b; margin: 0.25rem 0; }
.rep-estado { font-size: 0.75rem; font-weight: 600; }
.rep-nota { font-size: 0.75rem; color: #64748b; margin-top: 0.25rem; }

/* RNF table */
.rnf-table { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.rnf-row { display: grid; grid-template-columns: 60px 120px 1fr 100px; border-bottom: 1px solid #f1f5f9; font-size: 0.82rem; }
.rnf-row:last-child { border-bottom: none; }
.rnf-row > span { padding: 0.5rem 0.5rem; color: #475569; }
.rnf-row--header { background: #f8fafc; font-weight: 700; }
.rnf-row--header > span { color: #334155; }
.rnf-id { font-weight: 700; color: #7c3aed; }
.rnf-cat { font-weight: 600; }
.rnf-estado { font-weight: 600; font-size: 0.78rem; }

/* Tech grid */
.tech-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.75rem; }
@media (max-width: 900px) { .tech-grid { grid-template-columns: repeat(2, 1fr); } }
.tech-item { display: flex; align-items: flex-start; gap: 0.6rem; padding: 0.75rem; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0; }
.tech-icon { font-size: 1.4rem; flex-shrink: 0; }
.tech-item strong { display: block; font-size: 0.88rem; color: #1e293b; }
.tech-item p { margin: 0.15rem 0 0 0; font-size: 0.8rem; color: #64748b; }

/* Convencion */
.conv-table { border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }
.conv-row { display: grid; grid-template-columns: 2fr 2fr 3fr; border-bottom: 1px solid #e2e8f0; font-size: 0.82rem; }
.conv-row:last-child { border-bottom: none; }
.conv-row > span { padding: 0.5rem 0.75rem; color: #475569; }
.conv-row--header > span { background: #f1f5f9; font-weight: 700; color: #334155; }

.meta-code { background: #1e293b; color: #e2e8f0; padding: 1rem; border-radius: 8px; font-size: 0.78rem; line-height: 1.5; overflow-x: auto; white-space: pre; font-family: 'Courier New', monospace; }

/* Capas */
.capas-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.75rem; }
@media (max-width: 800px) { .capas-grid { grid-template-columns: 1fr; } }
.capa-card { padding: 1rem; border-radius: 8px; border: 1px solid; text-align: center; }
.capa-card h4 { margin: 0.5rem 0 0.25rem 0; font-size: 0.9rem; color: #1e293b; }
.capa-card p { font-size: 0.8rem; margin: 0.2rem 0; }
.capa2-detalle { margin-top: 1rem; padding: 0.85rem; background: #f0f9ff; border-left: 4px solid #0284c7; border-radius: 6px; }
.capa2-detalle h4 { margin: 0 0 0.5rem 0; font-size: 0.92rem; color: #0c4a6e; }
.capa2-detalle ul { margin: 0; padding-left: 1.2rem; font-size: 0.82rem; color: #0c4a6e; line-height: 1.7; }
.capa2-detalle li { margin: 0.3rem 0; }
.capa2-detalle code { background: #e0f2fe; padding: 0.1rem 0.35rem; border-radius: 3px; font-size: 0.78rem; color: #0369a1; }
.capa2-detalle strong { color: #0c4a6e; }
.capa-card--done { background: #f0fdf4; border-color: #86efac; }
.capa-num { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; background: #3b82f6; color: white; font-weight: 700; font-size: 0.85rem; }

/* Pendientes */
.pendiente-header { display: flex; align-items: flex-start; gap: 0.75rem; margin-bottom: 0.5rem; }
.pendiente-emoji { font-size: 1.4rem; flex-shrink: 0; }
.pendiente-header h3 { margin: 0; display: inline; }
.pendiente-badges { display: flex; gap: 0.4rem; align-items: center; margin-top: 0.25rem; }
.pendiente-prioridad { display: inline-block; font-size: 0.72rem; font-weight: 700; padding: 0.15rem 0.5rem; border-radius: 4px; }
.prioridad--alta { background: #fef2f2; color: #dc2626; }
.prioridad--media { background: #fffbeb; color: #d97706; }
.prioridad--baja { background: #f0fdf4; color: #16a34a; }
.pendiente-rf { font-size: 0.72rem; font-weight: 600; padding: 0.15rem 0.5rem; border-radius: 4px; background: #eef2ff; color: #6366f1; }
.pendiente-estado { margin-top: 0.5rem; padding: 0.4rem 0.6rem; background: #f8fafc; border-radius: 4px; font-size: 0.82rem; color: #475569; }

/* Animation */
.help-section { animation: fadeIn 0.25s ease; }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }

/* Responsive campos table */
@media (max-width: 900px) {
  .campo-row { grid-template-columns: 30px 1fr; gap: 0; }
  .campo-row > span { padding: 0.3rem 0.5rem; }
  .c-tipo, .c-oblig, .c-desc { display: none; }
  .campo-row--header .c-tipo, .campo-row--header .c-oblig, .campo-row--header .c-desc { display: none; }
  .rnf-row { grid-template-columns: 60px 1fr 100px; }
  .rnf-cat { display: none; }
}
</style>
