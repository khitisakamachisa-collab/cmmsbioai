# CMMS-BioAI

[![Version](https://img.shields.io/badge/versi%C3%B3n-v0.7.0-blue.svg)](https://github.com/khitisakamachisa-collab/cmmsbioai)
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
- [Estrategia de Recuperación de Datos](#estrategia-de-recuperación-de-datos)
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

**Versión actual:** v0.7.0 — Prototipo Funcional en Desarrollo Activo

### Módulos Completados

- [x] **RF01 — Gestión de Activos (Equipos Médicos):** CRUD completo, asignación de técnicos responsables, estados con colores dinámicos, búsqueda y filtrado, subida de imágenes, documentos adjuntos, importación/exportación Excel.
- [x] **RF02 — Gestión de Órdenes de Trabajo (Correctivo):** Ciclo completo (Crear, Asignar, Resolver, Ver), gestión de repuestos utilizados con descuento automático de stock, validaciones de estado, historial automático al completar.
- [x] **RF03 — Mantenimiento Preventivo:** Creación de tareas preventivas con frecuencia en días, asignación de kit de repuestos, cálculo automático de próxima fecha, generación de OT desde tarea preventiva.
- [x] **RF04 — Gestión de Inventario de Repuestos:** CRUD completo, búsqueda, control de stock automático al usarse en OTs, importación/exportación Excel, subida de imágenes, documentos adjuntos, campos extendidos (numero_material, codigo_equivalente, especificaciones_tecnicas, proveedor_ultimo, fecha_ultima_entrada, precio_referencia).
- [x] **RF05 — Historial de Mantenimiento:** Timeline visual de eventos por equipo, registro automático al completar OT, creación manual de eventos, tipos de evento (preventivo, correctivo, calibración, otro).
- [x] **RF06 — Reportes y Estadísticas:** 6 reportes con gráficos interactivos — mantenimiento por equipo, OTs por período, análisis de costos, cumplimiento preventivo, disponibilidad de equipos, inventario.
- [x] **RF08 — Autenticación de Usuarios:** Login con JWT y contraseñas hasheadas con bcrypt, gestión de usuarios (admin/técnico), seed automático de usuario admin por defecto.
- [x] **RF09 — Gestión de Inventario de Herramientas y Materiales de Trabajo:** CRUD completo con categorías (Instrumento de Medición, Herramienta Manual, Consumible, Kit), estados de uso, importación/exportación Excel, subida de imágenes, documentos adjuntos, diferenciación clara respecto a repuestos (costo operativo vs. costo de mantenimiento).
- [x] **Gestión Documental:** Módulo transversal de documentos adjuntos con drag-and-drop, categorías (manual, fotografía, reporte, garantía, calibración, informe, otro), visualización inline y descarga, asociación a equipos, OTs, repuestos y herramientas.
- [x] **Dashboard con Métricas:** Tarjetas con indicadores en tiempo real + gráficos de Equipos por Estado, Órdenes por Prioridad y Órdenes por Estado + sugerencias automáticas del sistema.
- [x] **Configuración Centralizada:** Sistema de configuración mediante `config.json` + `config.py` con `get_dir()` para rutas de almacenamiento, nombres sanitizados para carpetas, y parámetros del sistema configurables.
- [x] **Página de Configuración (⚙️):** Interfaz de gestión del sistema con 3 capas de recuperación de datos — metadatos en archivos `.meta.json`, escaneo y recuperación de registros huérfanos, backup y restore completo de la base de datos como JSON.
- [x] **Página de Ayuda (?):** Documentación integrada del sistema con descripción de módulos, entidades, estructura de archivos y lista de funcionalidades pendientes.

### Módulos Pendientes

- [ ] **RF07 — Módulo de Inteligencia Artificial:** Sugerencias de mantenimiento, detección de patrones, recomendaciones de repuestos.
- [ ] **RF10 — Calendario Preventivo:** Vista de calendario visual para tareas preventivas programadas.
- [ ] **RF12 — Gestión de Proveedores:** CRUD de proveedores con datos de contacto e historial de compras.
- [ ] Roles y permisos de usuario (autorización por roles en frontend y backend).
- [ ] Protección de endpoints con autenticación JWT.
- [ ] Paginación en listados.

---

## Capturas de Pantalla

> **Nota:** Las capturas se agregarán en futuras actualizaciones del repositorio.

| Módulo | Descripción |
|--------|-------------|
| Dashboard | Métricas en tiempo real con gráficos interactivos (Chart.js) + sugerencias automáticas |
| Equipos | CRUD de activos médicos con imágenes y documentos adjuntos |
| Órdenes de Trabajo | Gestión del ciclo completo de OTs correctivas |
| Repuestos | Control de repuestos con stock automático e importación Excel |
| Herramientas | Inventario de herramientas del taller con categorías y estados de uso |
| Preventivo | Programación de tareas de mantenimiento preventivo |
| Historial | Timeline visual de eventos de mantenimiento por equipo |
| Reportes | 6 reportes estadísticos con gráficos interactivos |
| Configuración | 3 capas de recuperación + gestión del sistema |
| Ayuda | Documentación integrada del sistema |

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
- **Recuperación:** 3 capas — `.meta.json`, escaneo/recuperación, backup/restore JSON

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
│       │   └── index.js         # 11 rutas SPA
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── HomeDashboard.vue
│       │   ├── EquiposView.vue
│       │   ├── OrdenesView.vue
│       │   ├── InventarioView.vue         # Repuestos + Herramientas
│       │   ├── PreventivoView.vue
│       │   ├── HistorialView.vue
│       │   ├── ReportesView.vue
│       │   ├── UsuariosView.vue
│       │   ├── AyudaView.vue              # Documentación del sistema
│       │   └── ConfiguracionView.vue      # Configuración y recuperación
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
    │   ├── herramientas.py      # Herramienta (nuevo en v0.7.0)
    │   ├── preventivo.py        # TareaPreventiva + TareaRepuesto
    │   ├── historial.py         # EventoHistorial
    │   └── documentos.py        # DocumentoAdjunto
    │
    ├── schemas/
    │   ├── equipo.py
    │   ├── orden_trabajo.py
    │   ├── repuesto.py
    │   ├── herramienta.py       # (nuevo en v0.7.0)
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
    │   ├── herramientas.py      # CRUD + Excel + imágenes (nuevo en v0.7.0)
    │   ├── preventivo.py        # CRUD + generar-OT
    │   ├── estados.py           # CRUD estados de equipo
    │   ├── users.py             # Gestión de usuarios
    │   ├── historial.py         # CRUD + enriquecer respuestas
    │   ├── reportes.py          # 6 endpoints de reportes
    │   ├── documentos.py        # Upload/download/ver/eliminar
    │   ├── dashboard.py         # Métricas del dashboard
    │   └── configuracion.py     # Config + escaneo + backup/restore (nuevo en v0.7.0)
    │
    ├── utils/
    │   ├── security.py          # bcrypt + JWT
    │   └── meta_json.py         # Escritura de .meta.json para recuperación
    │
    └── uploads/                 # Almacenamiento de archivos (no versionado)
        ├── EQUIPOS/             # E0001_Modelo_Serie/ (imágenes + DOC/)
        ├── REPUESTOS/           # R0001_Nombre/ (imágenes + DOC/)
        ├── HERRAMIENTAS/        # H0001_Nombre/ (imágenes + DOC/)
        ├── OT/                  # Archivos índice .txt de OTs
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

> **Nota:** Si se tiene un backup JSON (generado desde la página Configuración), se puede restaurar después del reinicio para recuperar todos los datos sin perder información.

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
    "repuestos_imagenes": "uploads/REPUESTOS",
    "repuestos_documentos": "uploads/REPUESTOS",
    "herramientas_imagenes": "uploads/HERRAMIENTAS",
    "herramientas_documentos": "uploads/HERRAMIENTAS",
    "reportes": "uploads/REPORTES"
  },
  "sistema": {
    "idioma": "es",
    "zona_horaria": "America/La_Paz",
    "moneda": "BOB",
    "prefijo_equipos": "E",
    "prefijo_ordenes": "OT",
    "prefijo_repuestos": "R"
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
    ├── .meta.json                   # Metadatos para recuperación
    └── DOC/                         # Documentos asociados al equipo
        ├── .meta.json               # Índice de documentos
        ├── manual_usuario.pdf
        └── certificado_garantia.pdf
```

### Repuestos

```text
uploads/REPUESTOS/
└── R0001_nombre_repuesto/
    ├── R0001_nombre_repuesto.jpg    # Imagen del repuesto
    ├── .meta.json                   # Metadatos para recuperación
    └── DOC/                         # Documentos asociados
        ├── .meta.json               # Índice de documentos
        ├── ficha_tecnica.pdf
        └── certificado_calibracion.pdf
```

### Herramientas

```text
uploads/HERRAMIENTAS/
└── H0001_nombre_herramienta/
    ├── H0001_nombre_herramienta.jpg # Imagen de la herramienta
    ├── .meta.json                   # Metadatos para recuperación
    └── DOC/                         # Documentos asociados
        ├── .meta.json               # Índice de documentos
        └── manual_osciloscopio.pdf
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

### Convención de Nombres

| Entidad | Formato | Ejemplo |
|---------|---------|---------|
| Carpeta de Equipo | `E{ID4d}_Modelo_Serie` | `E0001_CX23_MIC-OLY-001` |
| Carpeta de Repuesto | `R{ID4d}_NombreSanitizado` | `R0001_Gel_Ecografico` |
| Carpeta de Herramienta | `H{ID4d}_NombreSanitizado` | `H0001_Osciloscopio_Rigol` |
| Archivo índice OT | `OT{ID4d}_Titulo_Tipo_Modelo_Serie.txt` | `OT0001_Calibracion_Preventivo_CX23_MIC-OLY-001.txt` |
| Carpeta OT en equipo | `OT{ID4d}_Titulo_Tipo_Modelo_Serie/` | `OT0001_Calibracion_Preventivo_CX23_MIC-OLY-001/` |

Los nombres se sanitizan mediante `config.py → sanitize_filename()`, que reemplaza caracteres no ASCII y espacios por guiones bajos, evitando problemas de codificación entre sistemas operativos.

---

## Estrategia de Recuperación de Datos

El sistema implementa una estrategia de recuperación en **3 capas** para proteger los datos contra la pérdida de la base de datos SQLite. Esta funcionalidad se gestiona desde la página **Configuración (⚙️)** del sistema.

### Capa 1 — Metadatos en Archivos (.meta.json)

Cada carpeta de entidad (equipo, repuesto, herramienta) contiene un archivo `.meta.json` con los metadatos esenciales del registro y sus documentos adjuntos. Este archivo se actualiza automáticamente cada vez que se sube una imagen o un documento. Si la base de datos se pierde, los datos esenciales pueden reconstruirse escaneando estos archivos.

**Ejemplo de `.meta.json`:**

```json
{
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
}
```

### Capa 2 — Escaneo y Recuperación

La página Configuración incluye un escáner que lee todos los archivos `.meta.json` y los compara con los registros existentes en la base de datos. Si detecta entidades que existen en archivos pero no en la BD (registros huérfanos), permite recuperarlas y recrear los registros automáticamente con los datos disponibles en los metadatos.

- **Endpoint:** `GET /configuracion/escanear` — Escanea y reporta estado
- **Endpoint:** `POST /configuracion/recuperar` — Recupera registros huérfanos

### Capa 3 — Backup y Restore

Permite exportar toda la base de datos como un archivo JSON descargable y restaurarla desde ese archivo. El backup incluye metadatos (sistema, versión, fecha, totales) y todos los datos de las tablas. La restauración respeta el orden de dependencias de claves foráneas (padres primero) para garantizar la integridad referencial.

- **Endpoint:** `GET /configuracion/backup` — Genera backup como JSON
- **Endpoint:** `GET /configuracion/backup/descargar` — Descarga backup como archivo
- **Endpoint:** `POST /configuracion/restore` — Restaura desde JSON en el body
- **Endpoint:** `POST /configuracion/restore/subir` — Restaura subiendo un archivo JSON

**Formato del backup:**

```json
{
  "metadatos": {
    "sistema": "CMMS-BioAI",
    "version": "1.0",
    "fecha_backup": "2025-06-14T10:30:00",
    "descripcion": "Backup completo de la base de datos",
    "totales": {
      "estados_equipo": 19,
      "equipos": 15,
      "repuestos": 8
    }
  },
  "datos": {
    "estados_equipo": [...],
    "estados_ot": [...],
    "usuarios": [...],
    "equipos": [...],
    "repuestos": [...],
    "herramientas": [...],
    "ordenes_trabajo": [...],
    "documentos": [...],
    "eventos_historial": [...],
    "tareas_preventivas": [...],
    "tareas_repuestos": [...],
    "ot_repuestos_utilizados": [...]
  }
}
```

**Orden de restauración (respeta FK):** estados_equipo → estados_ot → usuarios → equipos → repuestos → herramientas → ordenes_trabajo → documentos → eventos_historial → tareas_preventivas → tareas_repuestos → ot_repuestos_utilizados

---

## Modelo de Base de Datos

El sistema utiliza 11 tablas en SQLite, gestionadas con SQLModel:

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

**`herramienta`** — Inventario de herramientas y materiales de trabajo

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| nombre_herramienta | str | Nombre descriptivo |
| numero_identificacion | str? (unique) | Código interno del taller |
| descripcion | str? | Descripción detallada |
| categoria | str | Instrumento de Medición / Herramienta Manual / Consumible / Kit |
| cantidad_disponible | int | Stock actual |
| unidad_medida | str | Unidad (unidad, juego, litro, etc.) |
| ubicacion_almacen | str? | Ubicación física |
| estado_uso | str | Disponible / En Uso / En Reparación / Dado de Baja |
| imagen_ruta | str? | Ruta relativa a imagen |
| costo_adquisicion | float? | Costo de adquisición |
| fecha_adquisicion | date? | Fecha de adquisición |
| proveedor_ultimo | str? | Último proveedor |
| observaciones | str? | Notas adicionales |

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
| herramienta_id | int? (FK→herramienta) | Herramienta asociada |
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

### Repuestos (`/repuestos`)

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

### Herramientas (`/herramientas`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/herramientas/` | Lista todas las herramientas |
| POST | `/herramientas/` | Crea una herramienta |
| GET | `/herramientas/{id}` | Obtiene una herramienta |
| PUT | `/herramientas/{id}` | Actualiza una herramienta |
| DELETE | `/herramientas/{id}` | Elimina una herramienta |
| GET | `/herramientas/plantilla-excel` | Descarga plantilla Excel |
| POST | `/herramientas/import-excel` | Importa herramientas desde Excel |
| POST | `/herramientas/{id}/upload_imagen` | Sube imagen de herramienta |
| DELETE | `/herramientas/{id}/imagen` | Elimina imagen de herramienta |

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

### Configuración (`/configuracion`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/configuracion/` | Lee configuración actual |
| PUT | `/configuracion/` | Actualiza configuración |
| GET | `/configuracion/estados-bd` | Resumen de registros por tabla |
| GET | `/configuracion/escanear` | Escanea .meta.json y reporta huérfanos |
| POST | `/configuracion/recuperar` | Recupera registros huérfanos |
| GET | `/configuracion/backup` | Genera backup completo como JSON |
| GET | `/configuracion/backup/descargar` | Descarga backup como archivo |
| POST | `/configuracion/restore` | Restaura BD desde JSON |
| POST | `/configuracion/restore/subir` | Restaura BD subiendo archivo JSON |

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
| RF09 | Gestión de Inventario de Herramientas y Materiales de Trabajo | Completado |
| RF10 | Calendario Preventivo | Pendiente |
| RF12 | Gestión de Proveedores | Pendiente |

### RF09 — Gestión de Inventario de Herramientas y Materiales de Trabajo

Módulo de inventario separado para herramientas del taller (osciloscopios, testers, kits) y consumibles generales (alcohol, estaño), diferenciado de repuestos en impacto financiero y control de disponibilidad.

**Atributos:** id, nombre_herramienta, numero_identificacion, descripcion, categoria (Instrumento de Medición / Herramienta Manual / Consumible / Kit), cantidad_disponible, unidad_medida, ubicacion_almacen, estado_uso (Disponible / En Uso / En Reparación / Dado de Baja), imagen_ruta, costo_adquisicion, fecha_adquisicion, proveedor_ultimo, observaciones.

**Funcionalidades implementadas:**
- CRUD completo de herramientas
- Importación/exportación Excel con lógica de upsert
- Subida de imagen principal por herramienta
- Documentos adjuntos por herramienta
- 4 categorías: Instrumento de Medición, Herramienta Manual, Consumible, Kit
- 4 estados de uso: Disponible, En Uso, En Reparación, Dado de Baja
- Integración con la vista Inventario (pestañas Repuestos / Herramientas)
- Archivo .meta.json para recuperación de datos

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
| v0.7.0 | **Herramientas + Configuración + Ayuda** | RF09 Herramientas (CRUD, Excel, imágenes, documentos, .meta.json), página Configuración con 3 capas de recuperación (metadatos, escaneo/recuperación, backup/restore JSON), página Ayuda con documentación integrada, navbar actualizado (Inventario→Repuestos, ?, ⚙️), 11 tablas en BD |

---

## Observaciones Técnicas

- **Seed de Estados:** Los estados se crean automáticamente al iniciar el backend. Si se personaliza la base de datos manualmente, el seed no sobrescribirá datos existentes (solo inserta si las tablas están vacías).
- **IDs de Base de Datos:** Los IDs son automáticos e incrementales. Si se elimina un registro, ese ID no se reutiliza. Para control normado de inventario, usar `numero_serie` o `numero_material`.
- **Importación Excel:** Las plantillas se generan dinámicamente en el backend (no son archivos estáticos), garantizando sincronización con los modelos de datos actuales. Soportan lógica de upsert (actualiza si el registro ya existe).
- **Configuración Centralizada:** Todos los módulos deben usar `from config import get_dir` para obtener rutas de almacenamiento. Nunca calcular rutas con `__file__` desde otros módulos.
- **Sanitización de Nombres:** La función `sanitize_filename()` en `config.py` normaliza nombres de archivos/carpetas a ASCII seguro, reemplazando caracteres especiales por guiones bajos.
- **Archivos .meta.json:** Cada carpeta de entidad contiene un `.meta.json` con metadatos esenciales para recuperación. Estos archivos se actualizan automáticamente al subir imágenes o documentos.
- **Backup/Restore:** El backup exporta toda la BD como JSON. La restauración limpia las tablas existentes e inserta los datos respetando el orden de dependencias FK. Los campos fecha se convierten automáticamente entre string ISO y tipos Python date/datetime.
- **Seguridad:** El JWT secret está hardcodeado en `utils/security.py`. Para producción, mover a variable de entorno. Los endpoints no tienen protección de autenticación todavía (pendiente de implementar).
- **CORS:** Configurado con `allow_origins=["*"]` para desarrollo. Restringir para producción.
- **Proxy Vite:** Las peticiones `/uploads/*` desde el frontend se redirigen automáticamente al backend en puerto 8000 mediante el proxy configurado en `vite.config.js`.
- **Migraciones:** La función `_migrate_repuesto_columns()` en `database.py` agrega columnas nuevas a la tabla `repuesto` si no existen (SQLite ALTER TABLE), permitiendo evolución del esquema sin pérdida de datos.
- **Herramientas vs Repuestos:** Las herramientas se diferencian de los repuestos en su modelo de uso: las herramientas no se consumen en OTs (solo cambia su estado_uso), mientras que los repuestos se descuentan del stock. Los costos de herramientas son operativos del taller, no de mantenimiento de un equipo individual.

---

## Roadmap

### Próximos Pasos (Prioridad Alta)

1. **RF10 — Calendario Preventivo** — Vista de calendario visual para tareas preventivas programadas (mensual/semanal)
2. **Protección de rutas por autenticación** — `Depends(get_current_user)` en endpoints protegidos + navigation guards en frontend
3. **Paginación en listados** — Implementar offset/limit en endpoints de listado para mejorar rendimiento

### Prioridad Media

4. **RF12 — Gestión de Proveedores** — CRUD de proveedores, vinculación con equipos y OTs
5. **Roles y permisos** — Autorización por roles en frontend (route guards) y backend (dependencias de auth)
6. **Secret JWT configurable** — Mover secreto JWT a variable de entorno o config.json
7. **Reportes PDF** — Exportación de reportes a formato PDF

### Prioridad Baja (Post v1.0)

8. **RF07 — Módulo IA** — Sugerencias de mantenimiento, detección de patrones, recomendaciones
9. **Despliegue unificado** — Frontend compilado servido desde FastAPI (un solo puerto)
10. **Empaquetado** — PyInstaller (.exe) + instalador Inno Setup / NSIS
11. **Normalización** — Estándares UMDNS / GMDN para registro de equipos
12. **Notificaciones** — Alertas de vencimiento, stock bajo, calibraciones próximas

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
