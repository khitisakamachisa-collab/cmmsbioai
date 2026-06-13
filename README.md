# CMMS-BioAI

[![Version](https://img.shields.io/badge/versi%C3%B3n-v0.6.x-blue.svg)](https://github.com/khitisakamachisa-collab/cmmsbioai)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB.svg?logo=python&logoColor=white)](https://python.org)
[![Vue.js](https://img.shields.io/badge/Vue.js-3.5+-4FC08D.svg?logo=vue.js&logoColor=white)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57.svg?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Licencia](https://img.shields.io/badge/licencia-MIT-green.svg)](LICENSE)

**Sistema de Gestión de Mantenimiento Asistido por Computadora (CMMS)** para equipos médicos biomédicos, desarrollado para el contexto boliviano. Diseñado como solución asequible, offline-first y centrada en el usuario, como parte de un proyecto de Maestría en Ingeniería Biomédica.

---

## Tabla de Contenidos

- [Estado del Proyecto](#estado-del-proyecto)
- [Capturas de Pantalla](#capturas-de-pantalla)
- [Tecnologías Utilizadas](#tecnologías-utilizadas)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Instalación y Ejecución Local](#instalación-y-ejecución-local)
- [Configuración del Sistema](#configuración-del-sistema)
- [Estructura de Almacenamiento de Archivos](#estructura-de-almacenamiento-de-archivos)
- [Modelo de Base de Datos](#modelo-de-base-de-datos)
- [API REST — Endpoints](#api-rest--endpoints)
- [Datos Seed (Carga Automática)](#datos-seed-carga-automática)
- [Requisitos Funcionales (RF)](#requisitos-funcionales-rf)
- [Historial de Versiones](#historial-de-versiones)
- [Observaciones Técnicas](#observaciones-técnicas)
- [Roadmap](#roadmap)
- [Contribución](#contribución)
- [Autor](#autor)

---

## Estado del Proyecto

**Versión actual:** v0.6.x — Prototipo Funcional en Desarrollo Activo

### Módulos Completados

- [x] **RF01 — Gestión de Activos (Equipos Médicos):** CRUD completo, asignación de técnicos responsables, estados con colores dinámicos, búsqueda y filtrado, subida de imágenes, documentos adjuntos, importación/exportación Excel.
- [x] **RF02 — Gestión de Órdenes de Trabajo (Correctivo):** Ciclo completo (Crear, Asignar, Resolver, Ver), gestión de repuestos utilizados con descuento automático de stock, validaciones de estado, historial automático al completar.
- [x] **RF03 — Mantenimiento Preventivo:** Creación de tareas preventivas con frecuencia en días, asignación de kit de repuestos, cálculo automático de próxima fecha, generación de OT desde tarea preventiva.
- [x] **RF04 — Gestión de Inventario de Repuestos:** CRUD completo, búsqueda, control de stock automático al usarse en OTs, importación/exportación Excel, subida de imágenes, documentos adjuntos, campos extendidos (numero_material, codigo_equivalente, especificaciones_tecnicas, proveedor_ultimo, fecha_ultima_entrada, precio_referencia).
- [x] **RF05 — Historial de Mantenimiento:** Timeline visual de eventos por equipo, registro automático al completar OT, creación manual de eventos, tipos de evento (preventivo, correctivo, calibración, otro).
- [x] **RF06 — Reportes y Estadísticas:** 6 reportes con gráficos interactivos — mantenimiento por equipo, OTs por período, análisis de costos, cumplimiento preventivo, disponibilidad de equipos, inventario.
- [x] **RF08 — Autenticación de Usuarios:** Login con JWT y contraseñas hasheadas con bcrypt, gestión de usuarios (admin/técnico), seed automático de usuario admin por defecto.
- [x] **Gestión Documental:** Módulo transversal de documentos adjuntos con drag-and-drop, categorías (manual, fotografía, reporte, garantía, calibración, informe, otro), visualización inline y descarga, asociación a equipos, OTs y repuestos.
- [x] **Dashboard con Métricas:** Tarjetas con indicadores en tiempo real + gráficos de Equipos por Estado, Órdenes por Prioridad y Órdenes por Estado.
- [x] **Configuración Centralizada:** Sistema de configuración mediante `config.json` + `config.py` con `get_dir()` para rutas de almacenamiento, nombres sanitizados para carpetas, y parámetros del sistema configurables.

### Módulos Pendientes

- [ ] **RF07 — Módulo de Inteligencia Artificial:** Sugerencias de mantenimiento, detección de patrones, recomendaciones de repuestos.
- [ ] **RF09 — Gestión de Inventario de Herramientas y Materiales de Trabajo:** Inventario separado para herramientas del taller (osciloscopios, testers, kits) y consumibles generales (alcohol, estaño), diferenciado de repuestos en impacto financiero y control de disponibilidad.
- [ ] Roles y permisos de usuario (autorización por roles en frontend y backend).
- [ ] Página de Configuración del sistema (gestión de estados, rutas, parámetros).
- [ ] Página de Ayuda (guía de uso, FAQ).

---

## Capturas de Pantalla

> **Nota:** Las capturas se agregarán en futuras actualizaciones del repositorio.

| Módulo | Descripción |
|--------|-------------|
| Dashboard | Métricas en tiempo real con gráficos interactivos (Chart.js) |
| Equipos | CRUD de activos médicos con imágenes y documentos adjuntos |
| Órdenes de Trabajo | Gestión del ciclo completo de OTs correctivas |
| Inventario | Control de repuestos con stock automático |
| Preventivo | Programación de tareas de mantenimiento preventivo |
| Historial | Timeline visual de eventos de mantenimiento por equipo |
| Reportes | 6 reportes estadísticos con gráficos interactivos |

---

## Tecnologías Utilizadas

### Backend

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| Python | 3.10+ | Lenguaje principal |
| FastAPI | 0.100+ | Framework web asíncrono |
| SQLModel | — | ORM (basado en SQLAlchemy + Pydantic) |
| SQLite | 3 | Base de datos (ideal para uso offline) |
| JWT (python-jose) | — | Autenticación con tokens |
| bcrypt (passlib) | — | Hash de contraseñas |
| openpyxl | — | Procesamiento de archivos Excel |
| python-multipart | — | Manejo de uploads de archivos |
| uvicorn | — | Servidor ASGI |

### Frontend

| Tecnología | Versión | Uso |
|-----------|---------|-----|
| Vue.js | 3.5+ | Framework reactivo |
| Vite | 8.x | Empaquetador y dev server |
| Vue Router | 4.x | Enrutamiento SPA |
| Chart.js | 4.x | Gráficos y visualizaciones |
| vue-chartjs | 5.x | Wrapper Vue para Chart.js |
| Axios | 1.x | Cliente HTTP para API |

### Infraestructura

- **Proxy Vite:** `/uploads` → `http://127.0.0.1:8000` (servir archivos estáticos del backend)
- **CORS:** Configurado con `allow_origins=["*"]` para desarrollo
- **Base de datos:** Archivo único `cmms_bioai.db` (SQLite, portátil)

---

## Estructura del Proyecto

```text
CMMS-BioAI/
├── README.md
├── .gitignore                   # Archivos excluidos de Git
├── PENDIENTES.md
├── versiones.txt
│
├── Requisitos Funcionales (RF)/ # 16 hojas de especificaciones funcionales
│   ├── Hoja 1  RF01_Gestion_Activos.xlsx
│   ├── Hoja 2  RF02_Gestion_OT.xlsx
│   ├── Hoja 3  RF03_Mantenimiento_Preventivo.xlsx
│   ├── Hoja 4  RF04_Gestion_Inventario.xlsx
│   ├── Hoja 5  RF05_Historial_Mantenimiento.xlsx
│   ├── Hoja 6  RF06_Reporting.xlsx
│   ├── Hoja 7  RF07_Modulo_IA.xlsx
│   ├── Hoja 8  RF08_Autenticacion.xlsx
│   └── Hojas 9-16 (Estados, Documentos, Detalles, RNF)
│
├── frontend/
│   ├── index.html
│   ├── vite.config.js           # Config Vite + proxy /uploads
│   ├── package.json
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── style.css
│       ├── services/
│       │   └── api.js           # Cliente Axios (baseURL: localhost:8000)
│       ├── router/
│       │   └── index.js         # 9 rutas SPA
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── HomeDashboard.vue
│       │   ├── EquiposView.vue
│       │   ├── OrdenesView.vue
│       │   ├── InventarioView.vue
│       │   ├── PreventivoView.vue
│       │   ├── HistorialView.vue
│       │   ├── ReportesView.vue
│       │   └── UsuariosView.vue
│       └── components/
│           ├── Navbar.vue
│           ├── DocumentosAdjuntos.vue      # Drag-and-drop de archivos
│           ├── WorkOrdersChart.vue
│           └── EquipmentStatusChart.vue
│
└── backend/
    ├── main.py                  # Punto de entrada FastAPI
    ├── database.py              # SQLite + seed + migraciones
    ├── config.py                # Configuración centralizada (lee config.json)
    ├── config.json              # Parámetros del sistema y rutas de almacenamiento
    ├── requirements.txt
    │
    ├── models/
    │   ├── __init__.py
    │   ├── users.py             # Usuario
    │   ├── equipos.py           # Equipo
    │   ├── estados.py           # EstadoEquipo (catálogo)
    │   ├── ordenes.py           # OrdenTrabajo + EstadoOT (catálogo)
    │   ├── repuestos.py         # Repuesto + OtRepuestoUtilizado
    │   ├── preventivo.py        # TareaPreventiva + TareaRepuesto
    │   ├── historial.py         # EventoHistorial
    │   └── documentos.py        # DocumentoAdjunto
    │
    ├── schemas/
    │   ├── equipo.py
    │   ├── orden_trabajo.py
    │   ├── repuesto.py
    │   ├── preventivo.py
    │   ├── historial.py
    │   ├── user.py
    │   └── estado_equipo.py
    │
    ├── api/routes/
    │   ├── auth.py              # POST /token (JWT)
    │   ├── equipos.py           # CRUD + Excel + imágenes
    │   ├── ordenes.py           # CRUD + stock + auto-historial
    │   ├── repuestos.py         # CRUD + Excel + imágenes
    │   ├── preventivo.py        # CRUD + generar-OT
    │   ├── estados.py           # CRUD estados de equipo
    │   ├── users.py             # Gestión de usuarios
    │   ├── historial.py         # CRUD + enriquecer respuestas
    │   ├── reportes.py          # 6 endpoints de reportes
    │   ├── documentos.py        # Upload/download/ver/eliminar
    │   └── dashboard.py         # Métricas del dashboard
    │
    ├── utils/
    │   └── security.py          # bcrypt + JWT
    │
    └── uploads/                 # Almacenamiento de archivos (no versionado)
        ├── EQUIPOS/             # E0001_Modelo_Serie/ (imágenes + DOC/)
        ├── OT/                  # Archivos índice .txt de OTs
        ├── INVENTARIO/          # I0001_xxx/ (imágenes + DOC/)
        └── REPORTES/            # Reportes generados
```

---

## Instalación y Ejecución Local

### Requisitos Previos

- **Python 3.10+** instalado ([descargar](https://python.org))
- **Node.js 18+** y **npm** instalados ([descargar](https://nodejs.org))
- **Git** instalado ([descargar](https://git-scm.com))

### 1. Clonar el Repositorio

```bash
git clone https://github.com/khitisakamachisa-collab/cmmsbioai.git
cd cmmsbioai
```

### 2. Configuración del Backend

Abre una terminal en la carpeta `backend`:

```bash
# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno — Windows
venv\Scripts\activate

# Activar entorno — Linux / macOS
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt

# Iniciar el servidor
uvicorn main:app --reload
```

El backend correrá en `http://127.0.0.1:8000`.

Al iniciar por primera vez, el sistema crea automáticamente:

- **Usuario admin por defecto:** usuario `admin`, contraseña `admin123`
- **19 estados de equipo** (Operativo, En Mantenimiento, Averiado, etc.)
- **5 estados de orden de trabajo** (Abierta, En Proceso, Esp. Repuesto, Completada, Cancelada)
- **Carpetas de uploads** según `config.json`

La documentación interactiva de la API está disponible en:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

### 3. Configuración del Frontend

Abre una nueva terminal en la carpeta `frontend`:

```bash
# Instalar dependencias
npm install

# Iniciar la aplicación web
npm run dev
```

El frontend correrá en `http://localhost:5173`. Vite redirige automáticamente las peticiones `/uploads/*` al backend en el puerto 8000.

### 4. Primer Inicio de Sesión

| Campo | Valor |
|-------|-------|
| URL | `http://localhost:5173` |
| Usuario | `admin` |
| Contraseña | `admin123` |

> **Importante:** Cambiar la contraseña del admin después del primer inicio de sesión.

### 5. Reinicio del Sistema

Para reiniciar la base de datos a cero:

1. Detener el backend (`Ctrl+C`)
2. Eliminar el archivo `backend/cmms_bioai.db`
3. Reiniciar el backend — las tablas y datos seed se recrean automáticamente

---

## Configuración del Sistema

El archivo `backend/config.json` centraliza la configuración del sistema:

```json
{
  "empresa": {
    "nombre": "CMMS-BioAI",
    "logo_ruta": ""
  },
  "directorios": {
    "uploads_base": "uploads",
    "equipos_imagenes": "uploads/EQUIPOS",
    "equipos_documentos": "uploads/EQUIPOS",
    "ot_documentos": "uploads/OT",
    "inventario_imagenes": "uploads/INVENTARIO",
    "inventario_documentos": "uploads/INVENTARIO",
    "reportes": "uploads/REPORTES"
  },
  "sistema": {
    "idioma": "es",
    "zona_horaria": "America/La_Paz",
    "moneda": "BOB",
    "prefijo_equipos": "E",
    "prefijo_ordenes": "OT",
    "prefijo_inventario": "I"
  }
}
```

Todos los módulos del backend deben importar rutas desde `config.py`:

```python
from config import get_dir, sanitize_filename

dir_equipos = get_dir("equipos_imagenes")  # Ruta absoluta, se crea si no existe
nombre_seguro = sanitize_filename("Inspección")  # → "Inspecci_n"
```

---

## Estructura de Almacenamiento de Archivos

El sistema organiza los archivos subidos en una estructura jerárquica bajo `backend/uploads/`. Las rutas se configuran centralmente en `config.json` y se acceden mediante `config.py → get_dir(key)`.

### Equipos

```text
uploads/EQUIPOS/
└── E0001_CX23_MIC-OLY-001/         # Carpeta del equipo (E + ID + Modelo + Nro. Serie)
    ├── E0001_CX23_MIC-OLY-001.jpg  # Imagen principal del equipo
    └── DOC/                         # Documentos asociados al equipo
        ├── manual_usuario.pdf
        └── certificado_garantia.pdf
```

### Órdenes de Trabajo

```text
uploads/OT/
└── OT0001_titulo_tipo_Modelo_Serie.txt   # Archivo índice de la OT

uploads/EQUIPOS/E0001_CX23_MIC-OLY-001/
└── OT/
    └── OT0001_titulo_tipo_Modelo_Serie/   # Carpeta con mismo nombre que el .txt
        ├── foto_falla.png
        └── informe_reparacion.pdf
```

La carpeta de OT dentro del equipo comparte el mismo nombre que el archivo índice `.txt` en `uploads/OT/`, lo que permite la referencia cruzada directa entre ambos.

### Inventario (Repuestos)

```text
uploads/INVENTARIO/
└── I0001_nombre_repuesto/
    ├── I0001_nombre_repuesto.jpg   # Imagen del repuesto
    └── DOC/                        # Documentos asociados
        ├── ficha_tecnica.pdf
        └── certificado_calibracion.pdf
```

### Convención de Nombres

| Entidad | Formato | Ejemplo |
|---------|---------|---------|
| Carpeta de Equipo | `E{ID4d}_Modelo_Serie` | `E0001_CX23_MIC-OLY-001` |
| Carpeta de Inventario | `I{ID4d}_NombreSanitizado` | `I0001_Gel_Ecografico` |
| Archivo índice OT | `OT{ID4d}_Titulo_Tipo_Modelo_Serie.txt` | `OT0001_Calibracion_Preventivo_CX23_MIC-OLY-001.txt` |
| Carpeta OT en equipo | `OT{ID4d}_Titulo_Tipo_Modelo_Serie/` | `OT0001_Calibracion_Preventivo_CX23_MIC-OLY-001/` |

Los nombres se sanitizan mediante `config.py → sanitize_filename()`, que reemplaza caracteres no ASCII y espacios por guiones bajos, evitando problemas de codificación entre sistemas operativos.

---

## Modelo de Base de Datos

El sistema utiliza 10 tablas en SQLite, gestionadas con SQLModel:

### Tablas Principales

**`equipo`** — Registro de activos médicos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| nombre_corto | str? | Nombre abreviado |
| modelo | str | Modelo del equipo |
| numero_serie | str (unique) | Número de serie |
| numero_material | str? | Número de material (variante del modelo) |
| marca | str | Fabricante |
| fecha_adquisicion | date | Fecha de adquisición |
| fecha_fin_garantia | date? | Fin de garantía |
| registro_sanitario_bolivia | str? | Registro sanitario nacional |
| ubicacion_actual | str? | Ubicación física |
| proveedor_principal | str? | Proveedor de servicio/repuestos |
| descripcion | str? | Descripción detallada |
| imagen_ruta | str? | Ruta relativa a imagen |
| calibracion_proxima | date? | Próxima calibración programada |
| responsable_tecnico_id | int? (FK→usuario) | Técnico responsable |
| estado_id | int? (FK→estadoequipo) | Estado actual del equipo |

**`ordentrabajo`** — Órdenes de trabajo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| equipo_id | int (FK→equipo) | Equipo asociado |
| orden_preventiva_id | int? (FK→tareapreventiva) | OT generada desde preventivo |
| estado_id | int (FK→estadoot) | Estado de la OT |
| prioridad | str | Nivel de prioridad |
| tecnico_asignado_id | int? (FK→usuario) | Técnico asignado |
| fecha_creacion | datetime | Fecha de creación (automática) |
| fecha_vencimiento | date? | Fecha límite |
| titulo | str | Título descriptivo |
| descripcion_falla | str | Descripción del problema |
| acciones_realizadas | str? | Acciones al resolver |
| tiempo_real_invertido | float? | Tiempo de trabajo |
| unidad_tiempo | str | "horas" o "dias" |
| costo_adicional | float? | Costo general de la OT |
| costos_adicionales | float? | Costos externos (transporte, etc.) |

**`repuesto`** — Inventario de repuestos

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| nombre_repuesto | str | Nombre descriptivo |
| numero_serie | str? | Número de serie del repuesto |
| numero_material | str? | Número de material del fabricante |
| codigo_equivalente | str? | Código alternativo (OEM, genérico) |
| descripcion | str? | Descripción detallada |
| especificaciones_tecnicas | str? | Detalles técnicos (voltaje, tamaño, etc.) |
| cantidad_disponible | int | Stock actual |
| unidad_medida | str | Unidad (unidad, metro, litro, etc.) |
| ubicacion_almacen | str? | Ubicación física |
| nivel_stock_minimo | int? | Alerta de stock bajo |
| proveedor_ultimo | str? | Último proveedor |
| fecha_ultima_entrada | date? | Último ingreso |
| precio_referencia | float? | Precio para análisis de costos |
| imagen_ruta | str? | Ruta relativa a imagen |

**`tareapreventiva`** — Tareas de mantenimiento preventivo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| equipo_id | int (FK→equipo) | Equipo asociado |
| responsable_id | int? (FK→usuario) | Técnico responsable |
| titulo | str | Nombre de la tarea |
| descripcion | str? | Detalles de la actividad |
| frecuencia_dias | int | Intervalo en días |
| ultima_fecha | date? | Última ejecución |
| proxima_fecha | date? | Próxima fecha programada |
| activa | bool | Tarea activa/inactiva |

**`eventohistorial`** — Historial de mantenimiento

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| equipo_id | int (FK→equipo) | Equipo asociado |
| orden_trabajo_id | int? (FK→ordentrabajo) | OT que generó el evento |
| tipo_evento | str | preventivo / correctivo / calibracion / otro |
| descripcion | str | Descripción del evento |
| tecnico_id | int? (FK→usuario) | Técnico ejecutor |
| fecha_evento | datetime | Fecha (automática) |
| acciones_realizadas | str? | Acciones realizadas |
| tiempo_invertido | float? | Tiempo de trabajo |
| costo | float? | Costo del evento |
| repuestos_utilizados | str? | Resumen textual de repuestos |

**`documentoadjunto`** — Documentos asociados

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| orden_trabajo_id | int? (FK→ordentrabajo) | OT asociada |
| equipo_id | int? (FK→equipo) | Equipo asociado |
| repuesto_id | int? (FK→repuesto) | Repuesto asociado |
| nombre_archivo | str | Nombre original |
| ruta_archivo | str | Ruta relativa en servidor |
| tipo_archivo | str | MIME type |
| tamanio_bytes | int | Tamaño del archivo |
| descripcion | str? | Descripción breve |
| categoria | str? | manual / fotografía / reporte / garantía / calibración / informe / otro |
| fecha_subida | datetime | Fecha (automática) |
| subido_por | str? | Username de quien subió |

### Tablas de Relación

**`tarea_repuesto`** — Kit de repuestos por tarea preventiva

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador |
| tarea_preventiva_id | int (FK→tareapreventiva) | Tarea asociada |
| repuesto_id | int (FK→repuesto) | Repuesto requerido |
| cantidad_requerida | int | Cantidad necesaria |

**`otrepuestoutilizado`** — Repuestos utilizados en OT

| Campo | Tipo | Descripción |
|-------|------|-------------|
| orden_trabajo_id | int (FK→ordentrabajo, PK) | OT asociada |
| repuesto_id | int (FK→repuesto, PK) | Repuesto utilizado |
| cantidad_utilizada | int (PK) | Cantidad consumida |

### Tablas Catálogo

**`usuario`** — Usuarios del sistema

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador |
| username | str (unique) | Nombre de usuario |
| email | str? | Correo electrónico |
| hashed_password | str | Contraseña hasheada (bcrypt) |
| full_name | str? | Nombre completo |
| role | str | admin / tecnico |
| is_active | bool | Usuario activo |

**`estadoequipo`** — Catálogo de estados de equipo (19 valores seed)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador |
| nombre_estado | str | Nombre del estado |
| color | str | Color hexadecimal |

**`estadoot`** — Catálogo de estados de OT (5 valores seed)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador |
| nombre_estado | str | Nombre del estado |
| color | str | Color hexadecimal |

---

## API REST — Endpoints

La documentación interactiva completa está disponible en `http://127.0.0.1:8000/docs` (Swagger UI) y `http://127.0.0.1:8000/redoc`.

### Autenticación

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/token` | Inicia sesión, obtiene token JWT (OAuth2 form-data) |

### Equipos (`/equipos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/equipos/` | Lista todos los equipos |
| POST | `/equipos/` | Crea un nuevo equipo |
| GET | `/equipos/{id}` | Obtiene un equipo por ID |
| PUT | `/equipos/{id}` | Actualiza un equipo |
| DELETE | `/equipos/{id}` | Elimina un equipo |
| GET | `/equipos/tecnicos` | Lista técnicos disponibles |
| GET | `/equipos/estados` | Lista estados de equipo |
| GET | `/equipos/plantilla-excel` | Descarga plantilla Excel |
| POST | `/equipos/import-excel` | Importa equipos desde Excel |
| POST | `/equipos/{id}/upload_imagen` | Sube imagen de equipo |
| GET | `/equipos/{id}/imagen` | Obtiene imagen de equipo |

### Órdenes de Trabajo (`/ordenes`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/ordenes/` | Lista todas las órdenes |
| POST | `/ordenes/` | Crea una nueva orden |
| GET | `/ordenes/{id}` | Obtiene detalle de una orden |
| PUT | `/ordenes/{id}` | Actualiza estado, acciones o repuestos |
| GET | `/ordenes/estados/` | Lista estados de OT |
| POST | `/ordenes/estados/` | Crea un nuevo estado de OT |

### Inventario / Repuestos (`/repuestos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/repuestos/` | Lista el inventario |
| POST | `/repuestos/` | Agrega un repuesto |
| GET | `/repuestos/{id}` | Obtiene un repuesto |
| PUT | `/repuestos/{id}` | Actualiza un repuesto |
| DELETE | `/repuestos/{id}` | Elimina un repuesto |
| GET | `/repuestos/plantilla-excel` | Descarga plantilla Excel |
| POST | `/repuestos/import-excel` | Importa repuestos desde Excel |
| POST | `/repuestos/{id}/upload_imagen` | Sube imagen de repuesto |
| GET | `/repuestos/{id}/imagen` | Obtiene imagen de repuesto |

### Mantenimiento Preventivo (`/preventivo`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/preventivo/` | Lista todas las tareas preventivas |
| POST | `/preventivo/` | Crea una tarea (con repuestos opcionales) |
| GET | `/preventivo/{id}` | Obtiene detalle de una tarea |
| PUT | `/preventivo/{id}` | Actualiza una tarea |
| DELETE | `/preventivo/{id}` | Elimina una tarea |
| POST | `/preventivo/{id}/generar-ot` | Genera OT desde tarea preventiva |

### Documentos (`/documentos`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/documentos/` | Sube un documento (con entidad asociada) |
| GET | `/documentos/` | Lista documentos (filtrable por entidad) |
| GET | `/documentos/{id}/ver` | Visualiza documento inline en navegador |
| GET | `/documentos/{id}/descargar` | Descarga documento como adjunto |
| DELETE | `/documentos/{id}` | Elimina un documento |

### Historial (`/historial`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/historial/` | Lista todos los eventos |
| POST | `/historial/` | Crea un evento manual |
| GET | `/historial/equipo/{id}` | Lista eventos de un equipo |
| GET | `/historial/{id}` | Obtiene detalle de un evento |

### Reportes (`/reportes`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/reportes/mantenimiento-por-equipo` | Mantenimiento por equipo |
| GET | `/reportes/ots-por-periodo` | OTs por período |
| GET | `/reportes/costos` | Análisis de costos |
| GET | `/reportes/cumplimiento-preventivo` | Cumplimiento preventivo |
| GET | `/reportes/disponibilidad-equipos` | Disponibilidad de equipos |
| GET | `/reportes/inventario` | Reporte de inventario |

### Dashboard (`/dashboard`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/dashboard/metrics` | Métricas generales del dashboard |

### Usuarios (`/users`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/users/` | Lista usuarios |
| POST | `/users/` | Crea un nuevo usuario |

### Estados de Equipo (`/estados-equipo`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/estados-equipo/` | Lista estados |
| POST | `/estados-equipo/` | Crea un estado |
| PUT | `/estados-equipo/{id}` | Actualiza un estado |
| DELETE | `/estados-equipo/{id}` | Elimina un estado |

---

## Datos Seed (Carga Automática)

### Usuario Admin

| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contraseña | `admin123` |
| Email | `admin@biolab.com` |
| Rol | `admin` |

> **Importante:** Cambiar la contraseña del admin después del primer inicio de sesión.

### Estados de Equipo (`estadoequipo`)

| ID | Estado | Color |
|----|--------|-------|
| 1 | Operativo | Verde `#27ae60` |
| 2 | En mantenimiento | Naranja `#f39c12` |
| 3 | En reparación | Rojo `#e74c3c` |
| 4 | Fuera de servicio | Gris `#7f8c8d` |
| 5 | En espera/Standby | Azul `#3498db` |
| 6 | En calibración | Púrpura `#9b59b6` |
| 7 | En inspección | Teal `#1abc9c` |
| 8 | Esp. Repuesto | Naranja oscuro `#e67e22` |
| 9 | Bloqueado/LOTO | Rojo oscuro `#c0392b` |
| 10 | En almacén | Gris claro `#95a5a6` |
| 11 | Almacén repuestos | Marrón `#795548` |
| 12 | Retirado/Baja | Gris `#636e72` |
| 13 | En transporte | Azul `#0984e3` |
| 14 | En préstamo | Violeta `#6c5ce7` |
| 15 | En certificación | Verde menta `#00b894` |
| 16 | En modificación | Amarillo `#fdcb6e` |
| 17 | Condición crítica | Rojo intenso `#d63031` |
| 18 | Degradado | Coral `#e17055` |
| 19 | En monitoreo | Cian `#00cec9` |

### Estados de Orden de Trabajo (`estadoot`)

| ID | Estado | Color |
|----|--------|-------|
| 1 | Abierta | Azul `#3b82f6` |
| 2 | En Proceso | Naranja `#f39c12` |
| 3 | Esp. Repuesto | Naranja oscuro `#e67e22` |
| 4 | Completada | Verde `#27ae60` |
| 5 | Cancelada | Gris `#95a5a6` |

---

## Requisitos Funcionales (RF)

| RF | Nombre | Estado |
|----|--------|--------|
| RF01 | Gestión de Activos (Equipos Médicos) | Completado |
| RF02 | Gestión de Órdenes de Trabajo | Completado |
| RF03 | Mantenimiento Preventivo | Completado |
| RF04 | Gestión de Inventario de Repuestos | Completado |
| RF05 | Historial de Mantenimiento | Completado |
| RF06 | Reporting y Estadísticas | Completado |
| RF07 | Módulo de Inteligencia Artificial | Pendiente |
| RF08 | Autenticación de Usuarios | Completado |
| RF09 | Gestión de Inventario de Herramientas y Materiales de Trabajo | Planificado |

### RF09 — Gestión de Inventario de Herramientas (Planificado)

Diferencia herramientas del taller (osciloscopios, testers, kits) de los repuestos médicos. Las herramientas son activos del taller que no se consumen en una OT; su costo se contabiliza como costo operativo del departamento, no como costo de mantenimiento de un equipo individual.

**Atributos planificados:** id, nombre_herramienta, numero_identificacion, descripcion, categoria (Instrumento de Medición / Herramienta Manual / Consumible / Kit), cantidad_disponible, unidad_medida, ubicacion_almacen, estado_uso (Disponible / En Uso / En Reparación / Dado de Baja), imagen_ruta, costo_adquisicion, fecha_adquisicion, proveedor_ultimo, observaciones.

**Diferenciación clave con RF04 (Repuestos):**

| Aspecto | Repuestos (RF04) | Herramientas (RF09) |
|---------|------------------|---------------------|
| Propósito | Partes que se reemplazan en equipos médicos | Recursos del taller para reparar equipos |
| Impacto en costos | Se contabiliza como costo de mantenimiento del equipo | Se contabiliza como costo operativo del taller |
| Consumo | Se consumen (stock disminuye) | No se consumen (solo cambia su estado) |
| Vinculación | Directa a una OT y un Equipo Médico | Inventario independiente, uso opcional en OTs |

---

## Historial de Versiones

| Versión | Módulo | Descripción |
|---------|--------|-------------|
| v0.1.0 | **Base** | CRUD Equipos, Órdenes, Repuestos, Usuarios + Auth JWT/bcrypt |
| v0.2.0 | **Dashboard + Excel** | Gráficos Chart.js, importación/exportación Excel Equipos |
| v0.3.0 | **Preventivo + Seed** | Tareas preventivas, Excel Repuestos, seed automático de BD |
| v0.4.0 | **Historial** | Timeline de mantenimiento, registro automático al completar OT |
| v0.5.0 | **Reportes** | 6 reportes con gráficos (costos, disponibilidad, cumplimiento, etc.) |
| v0.6.0 | **Documentos** | Subida/descarga/eliminación de archivos, drag-and-drop, categorías |
| v0.6.x | **Mejoras UI** | Scrollbars en modales, acceso a documentos desde acciones, nombres preservados, categoría "informe", configuración centralizada config.json, imágenes en equipos y repuestos, visualización inline de documentos |

---

## Observaciones Técnicas

- **Seed de Estados:** Los estados se crean automáticamente al iniciar el backend. Si se personaliza la base de datos manualmente, el seed no sobrescribirá datos existentes (solo inserta si las tablas están vacías).
- **IDs de Base de Datos:** Los IDs son automáticos e incrementales. Si se elimina un registro, ese ID no se reutiliza. Para control normado de inventario, usar `numero_serie` o `numero_material`.
- **Importación Excel:** Las plantillas se generan dinámicamente en el backend (no son archivos estáticos), garantizando sincronización con los modelos de datos actuales.
- **Configuración Centralizada:** Todos los módulos deben usar `from config import get_dir` para obtener rutas de almacenamiento. Nunca calcular rutas con `__file__` desde otros módulos.
- **Sanitización de Nombres:** La función `sanitize_filename()` en `config.py` normaliza nombres de archivos/carpetas a ASCII seguro, reemplazando caracteres especiales por guiones bajos.
- **Seguridad:** El JWT secret está hardcodeado en `utils/security.py`. Para producción, mover a variable de entorno. Los endpoints no tienen protección de autenticación todavía (pendiente de implementar).
- **CORS:** Configurado con `allow_origins=["*"]` para desarrollo. Restringir para producción.
- **Proxy Vite:** Las peticiones `/uploads/*` desde el frontend se redirigen automáticamente al backend en puerto 8000 mediante el proxy configurado en `vite.config.js`.
- **Migraciones:** La función `_migrate_repuesto_columns()` en `database.py` agrega columnas nuevas a la tabla `repuesto` si no existen (SQLite ALTER TABLE), permitiendo evolución del esquema sin pérdida de datos.

---

## Roadmap

### Próximos Pasos (Prioridad Alta)

1. **Buscadores faltantes** — Agregar búsqueda en Órdenes y Preventivo
2. **Mejoras UX** — Iconos en barras de búsqueda, placeholders más cortos
3. **INVENTARIO: Mejoras de UI** — Separar campos Numero de Material / Código en dos campos, mostrar solo numero_serie en tabla

### Prioridad Media

4. **RF09 — Herramientas y Materiales** — Nuevo módulo de inventario de herramientas del taller
5. **Roles y permisos** — Autorización por roles en frontend (route guards) y backend (dependencias de auth)
6. **Página de Configuración** — Gestión de estados, rutas y parámetros desde la UI
7. **Página de Ayuda** — Guía de uso, FAQ, tour guiado
8. **Módulo de Proveedores** — CRUD de proveedores, vinculación con equipos y OTs

### Prioridad Baja (Post v1.0)

9. **RF07 — Módulo IA** — Sugerencias de mantenimiento, detección de patrones, recomendaciones
10. **Despliegue unificado** — Frontend compilado servido desde FastAPI (un solo puerto)
11. **Empaquetado** — PyInstaller (.exe) + instalador Inno Setup / NSIS
12. **Reportes PDF** — Exportación de reportes a formato PDF
13. **Normalización** — Estándares UMDNS / GMDN para registro de equipos
14. **Notificaciones** — Alertas de vencimiento, stock bajo, calibraciones próximas

---

## Contribución

1. Haz un Fork del repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Haz commit de tus cambios (`git commit -m 'Agregar nueva funcionalidad'`)
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## Autor

Desarrollado como parte del proyecto de Maestría en Ingeniería Biomédica.

Repositorio: [https://github.com/khitisakamachisa-collab/cmmsbioai](https://github.com/khitisakamachisa-collab/cmmsbioai)
