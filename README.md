# CMMS-BioAI

**Sistema de Gestión de Mantenimiento Asistido por Computadora** desarrollado para el contexto boliviano. Diseñado como solución asequible, offline-first y centrada en el usuario para la gestión de equipos médicos biomédicos en laboratorios clínicos y hospitales.

---

## Estado del Proyecto

**Version actual:** v0.6.0 — Prototipo Funcional Avanzado

El sistema se encuentra en fase de desarrollo activo con los módulos principales operativos y en uso.

### Modulos Completados

- [x] **Gestion de Activos (Equipos Medicos):** CRUD completo, asignacion de tecnicos, estados con colores dinamicos, busqueda y filtrado, paginacion.
- [x] **Gestion de Ordenes de Trabajo (Correctivo):** Ciclo completo (Crear, Asignar, Resolver, Ver), gestion de repuestos utilizados con descarga automatica de stock, validaciones de estado.
- [x] **Gestion de Inventario de Repuestos:** CRUD, busqueda, control de stock automatico al usarse en OTs, niveles minimos de stock.
- [x] **Gestion de Usuarios:** Creacion de tecnicos y administradores con roles.
- [x] **Autenticacion de Usuarios (JWT + bcrypt):** Login seguro con tokens JWT y contrasenas hasheadas con bcrypt.
- [x] **Dashboard con Graficos:** 5 tarjetas con metricas en tiempo real + 3 graficos interactivos (Equipos por Estado, Ordenes por Prioridad, Ordenes por Estado) usando Chart.js + vue-chartjs.
- [x] **Importacion/Exportacion Excel — Equipos:** Descarga de plantilla y carga masiva de equipos desde archivos .xlsx con openpyxl.
- [x] **Importacion/Exportacion Excel — Repuestos:** Descarga de plantilla y carga masiva de repuestos desde archivos .xlsx.
- [x] **Mantenimiento Preventivo:** Creacion de tareas preventivas con frecuencia en dias, asignacion de repuestos/kit de mantenimiento, calculo automatico de proxima fecha, generacion de OT desde tarea preventiva.
- [x] **Historial de Mantenimiento:** Timeline visual de eventos de mantenimiento, filtro por equipo, creacion manual de eventos, registro automatico al completar una OT, tipos de evento (preventivo, correctivo, calibracion, otro).
- [x] **Reportes y Estadisticas:** 6 reportes con graficos y tablas — Mantenimiento por Equipo, OTs por Periodo, Analisis de Costos, Cumplimiento Preventivo, Disponibilidad de Equipos, Inventario de Repuestos.
- [x] **Documentos Adjuntos:** Subida de archivos (PDF, imagenes, etc.) con drag-and-drop, categorias (manual, fotografia, reporte, garantia, calibracion, informe, otro), descarga y eliminacion de documentos, asociacion a equipos y ordenes de trabajo.
- [x] **Seed de Base de Datos:** Creacion automatica de usuario admin y estados por defecto al iniciar el sistema.

### Modulos Pendientes / En Progreso

- [ ] **Sugerencias de Inteligencia Artificial (RF07):** Modulo de IA para sugerencias de mantenimiento basadas en historial y patrones de falla.
- [ ] **Seguridad y Autorizacion:** Proteccion de endpoints con autenticacion, autorizacion por roles, JWT secret en variable de entorno, route guards en frontend.

### Mejoras Pendientes (Feedback de Usuario)

- [ ] **Icono de cuaderno en Acciones:** Mover la gestion de documentos desde los modales Ver/Editar a un boton independiente (icono cuaderno) en la columna de Acciones, con su propio modal dedicado.
- [ ] **Agregar "informe" a categorias de documentos:** Ampliar la lista de categorias existente.
- [ ] **Tamano de modales:** Estandarizar tamanos de ventanas emergentes (modal Ver es mas pequeno que modal Editar), agregar scrollbar vertical para contenido excedido.
- [ ] **Nombres de archivo originales:** Preservar nombres originales en uploads (sin prefijos numericos automaticos).

---

## Tecnologias Utilizadas

### Backend
| Tecnologia | Version | Uso |
|-----------|---------|-----|
| Python | 3.10+ | Lenguaje principal |
| FastAPI | Latest | Framework web asincrono |
| SQLModel | Latest | ORM (SQLAlchemy + Pydantic) |
| SQLite | 3 | Base de datos embebida (offline-first) |
| python-jose | Latest | JWT tokens |
| passlib[bcrypt] | Latest | Hash de contrasenas |
| openpyxl | Latest | Procesamiento Excel |
| python-multipart | Latest | Subida de archivos |
| uvicorn | Latest | Servidor ASGI |

### Frontend
| Tecnologia | Version | Uso |
|-----------|---------|-----|
| Vue.js | 3.5+ | Framework reactivo |
| Vite | 8+ | Empaquetador y dev server |
| Vue Router | 4+ | Enrutamiento SPA |
| Chart.js | 4+ | Graficos interactivos |
| vue-chartjs | 5+ | Wrapper Vue para Chart.js |
| Axios | 1.x | Cliente HTTP con interceptores JWT |

---

## Estructura del Proyecto

```text
CMMS-BioAI/
├── backend/
│   ├── main.py                    # Punto de entrada FastAPI + routers + static files
│   ├── database.py                # Configuracion SQLite + seed automatico
│   ├── cmms_bioai.db              # Base de datos SQLite
│   ├── requirements.txt           # Dependencias Python
│   ├── uploads/                   # Archivos subidos (documentos adjuntos)
│   │   ├── equipo_{id}/           # Documentos de equipos
│   │   └── ot_{id}/               # Documentos de ordenes de trabajo
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py            # POST /token (login JWT)
│   │       ├── equipos.py         # CRUD equipos + Excel
│   │       ├── ordenes.py         # CRUD ordenes + repuestos + historial auto
│   │       ├── repuestos.py       # CRUD repuestos + Excel
│   │       ├── preventivo.py      # CRUD preventivo + generar OT
│   │       ├── estados.py         # CRUD estados de equipo
│   │       ├── users.py           # CRUD usuarios
│   │       ├── historial.py       # CRUD historial de mantenimiento
│   │       ├── reportes.py        # 6 endpoints de reportes
│   │       ├── documentos.py      # Subir/listar/descargar/eliminar documentos
│   │       └── dashboard.py       # Metricas del dashboard
│   ├── models/
│   │   ├── __init__.py            # Exporta todos los modelos
│   │   ├── users.py               # Usuario
│   │   ├── equipos.py             # Equipo
│   │   ├── estados.py             # EstadoEquipo
│   │   ├── ordenes.py             # OrdenTrabajo, EstadoOT
│   │   ├── repuestos.py           # Repuesto, OtRepuestoUtilizado
│   │   ├── preventivo.py          # TareaPreventiva, TareaRepuesto
│   │   ├── historial.py           # EventoHistorial
│   │   └── documentos.py          # DocumentoAdjunto
│   ├── schemas/                   # Esquemas Pydantic (validacion)
│   │   ├── equipo.py
│   │   ├── orden_trabajo.py
│   │   ├── repuesto.py
│   │   ├── preventivo.py
│   │   ├── estado_equipo.py
│   │   ├── user.py
│   │   └── historial.py
│   └── utils/
│       └── security.py            # JWT + bcrypt utilities
│
└── frontend/
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.js                # Entry point Vue
        ├── App.vue                # Componente raiz
        ├── style.css              # Estilos globales
        ├── router/
        │   └── index.js           # Definicion de rutas
        ├── services/
        │   └── api.js             # Axios client + JWT interceptor
        ├── views/
        │   ├── LoginView.vue      # Login con JWT
        │   ├── HomeDashboard.vue  # Dashboard (metricas + graficos + IA)
        │   ├── EquiposView.vue    # Gestion de equipos
        │   ├── OrdenesView.vue    # Gestion de ordenes de trabajo
        │   ├── InventarioView.vue # Inventario de repuestos
        │   ├── PreventivoView.vue # Mantenimiento preventivo
        │   ├── UsuariosView.vue   # Gestion de usuarios
        │   ├── HistorialView.vue  # Historial de mantenimiento (timeline)
        │   └── ReportesView.vue   # Reportes y estadisticas (6 pestanas)
        └── components/
            ├── Navbar.vue                  # Barra de navegacion
            ├── EquipmentStatusChart.vue    # Grafico de estados (pie)
            ├── WorkOrdersChart.vue         # Grafico de ordenes (bar)
            └── DocumentosAdjuntos.vue      # Componente de documentos (drag-and-drop)
```

---

## Instalacion y Ejecucion Local

### Requisitos Previos
- Python 3.10+ instalado
- Node.js 18+ y npm instalados

### 1. Configuracion del Backend

Abre una terminal en la carpeta `backend`:

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor
uvicorn main:app --reload
```

El backend correra en `http://127.0.0.1:8000`.

La documentacion interactiva de la API esta disponible en `http://127.0.0.1:8000/docs` (Swagger UI).

### 2. Configuracion del Frontend

Abre una nueva terminal en la carpeta `frontend`:

```bash
# Instalar dependencias
npm install

# Iniciar la aplicacion web
npm run dev
```

El frontend correra en `http://localhost:5173`.

### 3. Primer Inicio

Al iniciar el backend por primera vez, el sistema crea automaticamente:

| Dato | Detalle |
|------|---------|
| **Usuario admin** | usuario: `admin`, contrasena: `admin123` |
| **6 estados de equipo** | Operativo, En Mantenimiento, Averiado, Retirado, En Reserva, En Transito |
| **5 estados de OT** | Abierta, En Proceso, Bloqueada, Completada, Cancelada |

> **Nota de seguridad:** Cambia la contrasena del admin despues del primer inicio de sesion.

### 4. Reinicio del Sistema

Para reiniciar la base de datos a cero:
1. Detener el backend (`Ctrl+C`)
2. Eliminar el archivo `cmms_bioai.db`
3. Reiniciar el backend — las tablas y datos seed se recrean automaticamente

---

## Endpoints de la API

### Autenticacion (`/auth`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/token` | Login, retorna JWT token |

### Equipos (`/equipos`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/equipos/` | Listar todos los equipos |
| POST | `/equipos/` | Crear equipo |
| PUT | `/equipos/{id}` | Actualizar equipo |
| DELETE | `/equipos/{id}` | Eliminar equipo |
| GET | `/equipos/estados` | Listar estados de equipo |
| POST | `/equipos/estados` | Crear estado de equipo |
| GET | `/equipos/tecnicos` | Listar tecnicos |
| GET | `/equipos/plantilla-excel` | Descargar plantilla Excel |
| POST | `/equipos/import-excel` | Importar equipos desde Excel |

### Ordenes de Trabajo (`/ordenes`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/ordenes/` | Listar ordenes (filtrar por equipo) |
| POST | `/ordenes/` | Crear orden de trabajo |
| GET | `/ordenes/{ot_id}` | Detalle de OT (con repuestos) |
| PUT | `/ordenes/{ot_id}` | Actualizar OT (stock + historial auto) |
| DELETE | `/ordenes/{ot_id}` | Eliminar orden |
| GET | `/ordenes/estados/` | Listar estados de OT |
| POST | `/ordenes/estados/` | Crear estado de OT |

### Inventario (`/repuestos`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/repuestos/` | Listar inventario |
| POST | `/repuestos/` | Crear repuesto |
| GET | `/repuestos/{rep_id}` | Detalle de repuesto |
| PUT | `/repuestos/{rep_id}` | Actualizar repuesto |
| DELETE | `/repuestos/{rep_id}` | Eliminar repuesto |
| GET | `/repuestos/plantilla-excel` | Descargar plantilla Excel |
| POST | `/repuestos/import-excel` | Importar repuestos desde Excel |

### Mantenimiento Preventivo (`/preventivo`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/preventivo/` | Listar tareas preventivas |
| POST | `/preventivo/` | Crear tarea preventiva |
| GET | `/preventivo/{tarea_id}` | Detalle de tarea |
| POST | `/preventivo/{tarea_id}/generar-ot` | Generar OT desde preventivo |
| PUT | `/preventivo/{tarea_id}` | Actualizar tarea |
| DELETE | `/preventivo/{tarea_id}` | Eliminar tarea |

### Historial (`/historial`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/historial/` | Listar eventos (filtrar por equipo) |
| POST | `/historial/` | Crear evento manual |
| GET | `/historial/equipo/{equipo_id}` | Historial por equipo |
| GET | `/historial/{evento_id}` | Detalle de evento |
| PUT | `/historial/{evento_id}` | Actualizar evento |
| DELETE | `/historial/{evento_id}` | Eliminar evento |

### Reportes (`/reportes`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/reportes/mantenimiento-por-equipo` | Resumen de mantenimiento por equipo |
| GET | `/reportes/ots-por-periodo` | OTs por rango de fechas |
| GET | `/reportes/costos` | Analisis de costos |
| GET | `/reportes/preventivo-cumplimiento` | Cumplimiento preventivo |
| GET | `/reportes/disponibilidad-equipos` | Disponibilidad de equipos |
| GET | `/reportes/inventario-repuestos` | Reporte de inventario de repuestos |

### Documentos Adjuntos (`/documentos`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/documentos/` | Subir documento (multipart) |
| GET | `/documentos/` | Listar documentos (filtrar por OT/equipo) |
| GET | `/documentos/{doc_id}/descargar` | Descargar documento |
| DELETE | `/documentos/{doc_id}` | Eliminar documento |

### Dashboard (`/dashboard`)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/dashboard/metrics` | Metricas del dashboard |

---

## Modelos de Base de Datos

### Usuario (`usuario`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| username | str | unique, indexed |
| email | str | unique, indexed |
| hashed_password | str | bcrypt hash |
| full_name | str | opcional |
| role | str | "admin" o "tecnico" |
| is_active | bool | default True |

### Equipo (`equipo`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| nombre_corto | str | opcional |
| modelo | str | requerido |
| numero_serie | str | unique, indexed |
| marca | str | requerido |
| fecha_adquisicion | date | requerido |
| registro_sanitario_bolivia | str | opcional |
| ubicacion_actual | str | opcional |
| proveedor_principal | str | opcional |
| descripcion | str | opcional |
| calibracion_proxima | date | opcional |
| responsable_tecnico_id | int | FK -> usuario.id |
| estado_id | int | FK -> estadoequipo.id |

### OrdenTrabajo (`ordentrabajo`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| equipo_id | int | FK -> equipo.id |
| orden_preventiva_id | int | FK -> tareapreventiva.id, opcional |
| estado_id | int | FK -> estadoot.id |
| prioridad | str | "baja", "media", "alta", "urgente" |
| tecnico_asignado_id | int | FK -> usuario.id, opcional |
| fecha_creacion | datetime | auto |
| fecha_vencimiento | date | opcional |
| titulo | str | requerido |
| descripcion_falla | str | requerido |
| acciones_realizadas | str | opcional |
| tiempo_real_invertido | float | opcional (horas) |
| costo_adicional | float | opcional |

### Repuesto (`repuesto`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| nombre_repuesto | str | requerido |
| numero_material | str | opcional |
| descripcion | str | opcional |
| cantidad_disponible | int | default 0 |
| unidad_medida | str | default "unidad" |
| ubicacion_almacen | str | opcional |
| nivel_stock_minimo | int | opcional |

### TareaPreventiva (`tareapreventiva`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| equipo_id | int | FK -> equipo.id |
| responsable_id | int | FK -> usuario.id, opcional |
| titulo | str | requerido |
| descripcion | str | opcional |
| frecuencia_dias | int | requerido |
| ultima_fecha | date | opcional |
| proxima_fecha | date | opcional |
| activa | bool | default True |

### EventoHistorial (`eventohistorial`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| equipo_id | int | FK -> equipo.id |
| orden_trabajo_id | int | FK -> ordentrabajo.id, opcional |
| tipo_evento | str | "preventivo", "correctivo", "calibracion", "otro" |
| descripcion | str | requerido |
| tecnico_id | int | FK -> usuario.id, opcional |
| fecha_evento | datetime | auto |
| acciones_realizadas | str | opcional |
| tiempo_invertido | float | opcional |
| costo | float | opcional |
| repuestos_utilizados | str | resumen textual |

### DocumentoAdjunto (`documentoadjunto`)
| Campo | Tipo | Notas |
|-------|------|-------|
| id | int | PK auto |
| orden_trabajo_id | int | FK -> ordentrabajo.id, opcional |
| equipo_id | int | FK -> equipo.id, opcional |
| nombre_archivo | str | nombre en servidor |
| ruta_archivo | str | ruta al archivo |
| tipo_archivo | str | MIME type |
| tamanio_bytes | int | tamano en bytes |
| descripcion | str | opcional |
| categoria | str | "manual", "fotografia", "reporte", "garantia", "calibracion", "informe", "otro" |
| fecha_subida | datetime | auto |
| subido_por | str | opcional |

### Tablas Lookup (Seed Automatico)

**EstadoEquipo** (`estadoequipo`):
| ID | Estado | Color |
|----|--------|-------|
| 1 | Operativo | #27ae60 (verde) |
| 2 | En Mantenimiento | #f39c12 (naranja) |
| 3 | Averiado (Pendiente Reparacion) | #e74c3c (rojo) |
| 4 | Retirado/Dado de Baja | #7f8c8d (gris) |
| 5 | En Reserva | #3498db (azul) |
| 6 | En Transito | #9b59b6 (purpura) |

**EstadoOT** (`estadoot`):
| ID | Estado | Color |
|----|--------|-------|
| 1 | Abierta | #3b82f6 (azul) |
| 2 | En Proceso | #f39c12 (naranja) |
| 3 | Bloqueada (Esp. Repuestos) | #e67e22 (naranja oscuro) |
| 4 | Completada | #27ae60 (verde) |
| 5 | Cancelada | #95a5a6 (gris) |

---

## Respaldo y Versionado (GitHub)

```bash
# 1. Agregar todos los archivos modificados
git add .

# 2. Crear un punto de guardado (Commit) con mensaje descriptivo
git commit -m "Descripcion breve de los cambios realizados"

# 3. Subir los cambios al repositorio remoto (GitHub)
git push origin main
```

---

## Historial de Cambios

### v0.6.0 — Documentos Adjuntos
- Modulo completo de gestion documental: subida, descarga y eliminacion de archivos
- Componente reutilizable `DocumentosAdjuntos.vue` con drag-and-drop
- Categorias de documento: manual, fotografia, reporte, garantia, calibracion, informe, otro
- Asociacion de documentos a equipos y ordenes de trabajo
- Servidor de archivos estaticos via FastAPI (`/uploads`)
- Modelo `DocumentoAdjunto` con metadatos (tipo MIME, tamano, categoria, descripcion)

### v0.5.0 — Reportes y Estadisticas
- 6 endpoints de reportes en el backend
- Vista `ReportesView.vue` con 6 pestanas y graficos interactivos
- Reportes: Mantenimiento por Equipo, OTs por Periodo, Analisis de Costos, Cumplimiento Preventivo, Disponibilidad de Equipos, Inventario de Repuestos
- Graficos Chart.js (barras y doughnut) en cada reporte

### v0.4.0 — Historial de Mantenimiento
- Modelo `EventoHistorial` con tipos de evento (preventivo, correctivo, calibracion, otro)
- Registro automatico de eventos al completar una Orden de Trabajo
- Vista `HistorialView.vue` con timeline visual y filtros
- Creacion manual de eventos de mantenimiento

### v0.3.0 — Seed de BD + Fix Preventivo + Excel Repuestos
- Seed automatico: usuario admin por defecto, 6 estados de equipo, 5 estados de OT
- Fix: creacion de tareas preventivas con repuestos
- Fix: refresh de objeto SQLModel despues de multiples commits
- Importacion/Exportacion Excel para Inventario/Repuestos
- Fix: deteccion de hoja correcta en Excel

### v0.2.0 — Dashboard con Graficos + Excel Equipos
- Dashboard mejorado con graficos (Chart.js + vue-chartjs)
- Importacion/Exportacion Excel para Equipos
- Navbar como componente compartido
- Separacion de vistas: HomeDashboard y EquiposView

### v0.1.0 — Funcionalidad Base + Bug Fixes
- CRUD completo de Equipos, Ordenes, Repuestos, Usuarios
- Autenticacion JWT funcional (bcrypt)
- Fix: migracion SHA-256 a bcrypt
- Fix: modelo Estado renombrado a EstadoEquipo
- Fix: endpoints mixtos separados

---

## Roadmap — Plan a Seguir

### Paso H — Sugerencias de IA (RF07)
- Integracion con modelo de IA para sugerencias de mantenimiento predictivo
- Analisis de historial de equipos y ordenes para detectar patrones de falla
- Recomendaciones automaticas en el Dashboard (frecuencia de mantenimiento, repuestos criticos)
- Alertas tempranas basadas en datos historicos

### Paso I — Seguridad y Autorizacion
- **Proteccion de endpoints:** Requerir JWT en todos los endpoints (excepto `/token`)
- **Autorizacion por roles:** Solo admin puede crear usuarios, estados y gestionar configuracion
- **Route guards en frontend:** Proteger rutas Vue Router, redirigir a login si no autenticado
- **JWT secret en variable de entorno:** Mover clave hardcoded a `.env`
- **CORS restringido:** Configurar origenes permitidos en produccion

### Mejoras Futuras
- **Normalizacion de equipos:** Implementar estandares UMDNS o GMDN para registro de equipos medicos
- **Sistema de configuracion de estados:** Interfaz para que el usuario gestione estados (crear, editar colores) desde la UI
- **Exportacion de reportes a PDF:** Generar reportes descargables en formato PDF
- **Notificaciones:** Alertas por vencimiento de OTs, stock bajo de repuestos, calibraciones proximas
- **Modo offline mejorado:** Service worker para funcionamiento sin conexion

---

## Observaciones Tecnicas

- **Seed de Estados:** Los estados se crean automaticamente al iniciar el backend. Si se personaliza la base de datos manualmente, el seed no sobrescribira datos existentes (solo inserta si las tablas estan vacias).
- **IDs de Base de Datos:** Los IDs son automaticos. Si se elimina un registro, ese ID no se reutiliza. Para control de inventario normado, usar `numero_serie` o crear un campo `codigo_activo`.
- **Importacion Excel:** Las plantillas se generan dinamicamente en el backend (no son archivos estaticos), garantizando sincronizacion con los modelos de datos actuales.
- **Seguridad:** El JWT secret esta hardcodeado en `security.py`. Para produccion, mover a variable de entorno.
- **CORS:** Actualmente permite todos los origenes (`*`). Restringir en produccion.
- **Documentos:** Los archivos se almacenan en `backend/uploads/` con subcarpetas por entidad (`equipo_{id}/`, `ot_{id}/`). El servidor FastAPI sirve estos archivos como contenido estatico en `/uploads`.
- **Composite PK:** La tabla `otrepuestoutilizado` usa clave primaria compuesta `(orden_trabajo_id, repuesto_id)`. La actualizacion usa estrategia de reemplazo (delete + re-insert).
- **SQLModel refresh:** Despues de `session.commit()`, es necesario llamar `session.refresh(obj)` antes de `model_dump()` para evitar errores de atributos expirados.

---

## Autor

Desarrollado como parte del proyecto de Maestria en Ingenieria Biomedica.

---

## Licencia

Proyecto de investigacion academica. Todos los derechos reservados.
