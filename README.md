# CMMS-BioAI

[![Version](https://img.shields.io/badge/versi%C3%B3n-v0.9.3-blue.svg)](https://github.com/khitisakamachisa-collab/cmmsbioai)
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
- [Estrategia de Recuperación de Datos (3 Capas)](#estrategia-de-recuperación-de-datos-3-capas)
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

**Versión actual:** v0.9.3 — Prototipo Funcional en Desarrollo Activo

### Módulos Completados

- [x] **RF01 — Gestión de Activos (Equipos Médicos):** CRUD completo, asignación de técnicos responsables, estados con colores dinámicos, búsqueda y filtrado, subida de imágenes, documentos adjuntos, importación/exportación Excel, archivos `.meta.json` para recuperación de datos.
- [x] **RF02 — Gestión de Órdenes de Trabajo (Correctivo):** Ciclo completo (Crear, Asignar, Resolver, Ver), gestión de repuestos utilizados con descuento automático de stock, validaciones de estado, historial automático al completar, archivos índice `.txt` en `uploads/OT/`.
- [x] **RF03 — Mantenimiento Preventivo:** Creación de tareas preventivas con frecuencia en días, asignación de kit de repuestos, cálculo automático de próxima fecha, generación de OT desde tarea preventiva.
- [x] **RF04 — Gestión de Inventario de Repuestos:** CRUD completo, búsqueda, control de stock automático al usarse en OTs, importación/exportación Excel, subida de imágenes, documentos adjuntos, campos extendidos (numero_material, especificaciones_tecnicas, proveedor_ultimo, precio_referencia), prefijo `R` en carpetas, archivos `.meta.json`.
- [x] **RF05 — Historial de Mantenimiento:** Timeline visual de eventos por equipo, registro automático al completar OT, creación manual de eventos, tipos de evento (preventivo, correctivo, calibración, otro).
- [x] **RF06 — Reportes y Estadísticas:** 6 reportes con gráficos interactivos — mantenimiento por equipo, OTs por período, análisis de costos, cumplimiento preventivo, disponibilidad de equipos, inventario.
- [x] **RF08 — Autenticación de Usuarios:** Login con JWT y contraseñas hasheadas con bcrypt, gestión de usuarios (admin/técnico), seed automático de usuario admin por defecto.
- [x] **RF09 — Gestión de Inventario de Herramientas y Materiales:** CRUD completo, categorías (Instrumento de Medición / Herramienta Manual / Consumible / Kit), estados de uso, importación/exportación Excel, subida de imágenes, documentos adjuntos, prefijo `H` en carpetas, archivos `.meta.json`.
- [x] **RF10 — Gestión de Proveedores y Contactos:** CRUD de proveedores con campo `ciudad` (independiente de `direccion`), CRUD de contactos asociados (relación 1:N), búsqueda por empresa/email/teléfono/ciudad, filtros por ciudad y página web, importación masiva Excel/CSV con upsert por `nombre_empresa`, plantilla Excel descargable con datos de ejemplo (20 proveedores biomédicos de Bolivia), modal de resultados de importación con conteo de creados/actualizados/fallidos. Pendiente: convertir los campos de texto `equipo.proveedor_principal` (RF01), `repuesto.proveedor_ultimo` (RF04) y `herramienta.proveedor_ultimo` (RF09) en FK a `Proveedor.id`.
- [x] **Gestión Documental:** Módulo transversal de documentos adjuntos con drag-and-drop, categorías (manual, fotografía, reporte, garantía, calibración, informe, otro), visualización inline y descarga, asociación a equipos, OTs, repuestos y herramientas, archivos `.meta.json` en carpetas `DOC/`.
- [x] **Dashboard con Métricas:** Tarjetas con indicadores en tiempo real + gráficos de Equipos por Estado, Órdenes por Prioridad y Órdenes por Estado.
- [x] **Configuración Centralizada:** Sistema de configuración mediante `config.json` + `config.py` con `get_dir()` para rutas de almacenamiento, nombre de empresa modificable, `uploads_base` editable desde la UI con movimiento automático de archivos y re-montaje de archivos estáticos sin reiniciar.
- [x] **Estrategia de Recuperación de Datos (3 Capas):** Capa 1 — Archivos `.meta.json` junto a cada entidad; Capa 2 — Escaneo y recuperación automática desde `.meta.json`; Capa 3 — Backup/Restore completo (BD + configuración).
- [x] **Página de Configuración:** Interfaz para modificar nombre del sistema y carpeta base de almacenamiento (`uploads_base`), escanear/recuperar datos huérfanos, generar/restaurar backups, mover archivos entre ubicaciones.

### Módulos Pendientes

- [ ] **RF07 — Módulo de Inteligencia Artificial:** Sugerencias de mantenimiento, detección de patrones, recomendaciones de repuestos.
- [ ] Roles y permisos de usuario (autorización por roles en frontend y backend).
- [ ] **RF10 — Migración de campos de texto a FK:** Convertir `equipo.proveedor_principal` (RF01), `repuesto.proveedor_ultimo` (RF04) y `herramienta.proveedor_ultimo` (RF09) en FK a `Proveedor.id`. Esto permitirá tener trazabilidad completa de proveedores en todo el sistema.

---

## Capturas de Pantalla

> **Nota:** Las capturas se agregarán en futuras actualizaciones del repositorio.

| Módulo | Descripción |
|--------|-------------|
| Dashboard | Métricas en tiempo real con gráficos interactivos (Chart.js) |
| Equipos | CRUD de activos médicos con imágenes y documentos adjuntos |
| Órdenes de Trabajo | Gestión del ciclo completo de OTs correctivas |
| Repuestos | Control de repuestos con stock automático e imágenes |
| Herramientas | Inventario de herramientas del taller con categorías y estados |
| Preventivo | Programación de tareas de mantenimiento preventivo |
| Historial | Timeline visual de eventos de mantenimiento por equipo |
| Reportes | 6 reportes estadísticos con gráficos interactivos |
| Configuración | Nombre del sistema, carpeta uploads, backup/restore, escaneo/recuperación |

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
- **Archivos estáticos:** Montaje dinámico que se actualiza automáticamente al cambiar `uploads_base`

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
│   ├── public/                  # Archivos estáticos servidos tal cual por Vite
│   │   ├── favicon.svg
│   │   ├── icons.svg
│   │   └── plantillas/          # Plantillas Excel/CSV descargables desde la UI
│   │       ├── plantilla_equipos.xlsx
│   │       ├── plantilla_equipos.csv
│   │       ├── plantilla_repuestos.xlsx
│   │       ├── plantilla_repuestos.csv
│   │       ├── plantilla_herramientas.xlsx
│   │       ├── plantilla_herramientas.csv
│   │       ├── plantilla_proveedores.xlsx
│   │       └── plantilla_proveedores.csv
│   └── src/
│       ├── main.js
│       ├── App.vue
│       ├── style.css
│       ├── services/
│       │   └── api.js           # Cliente Axios (baseURL: localhost:8000)
│       ├── router/
│       │   └── index.js         # Rutas SPA
│       ├── views/
│       │   ├── LoginView.vue
│       │   ├── HomeDashboard.vue
│       │   ├── EquiposView.vue
│       │   ├── OrdenesView.vue
│       │   ├── InventarioView.vue
│       │   ├── HerramientasView.vue
│       │   ├── PreventivoView.vue
│       │   ├── HistorialView.vue
│       │   ├── ReportesView.vue
│       │   ├── UsuariosView.vue
│       │   └── ConfiguracionView.vue
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
    │   ├── herramientas.py      # Herramienta
    │   ├── preventivo.py        # TareaPreventiva + TareaRepuesto
    │   ├── historial.py         # EventoHistorial
    │   └── documentos.py        # DocumentoAdjunto
    │
    ├── schemas/
    │   ├── equipo.py
    │   ├── orden_trabajo.py
    │   ├── repuesto.py
    │   ├── herramienta.py
    │   ├── preventivo.py
    │   ├── historial.py
    │   ├── user.py
    │   └── estado_equipo.py
    │
    ├── api/routes/
    │   ├── auth.py              # POST /token (JWT)
    │   ├── equipos.py           # CRUD + Excel + imágenes + .meta.json
    │   ├── ordenes.py           # CRUD + stock + auto-historial
    │   ├── repuestos.py         # CRUD + Excel + imágenes + .meta.json
    │   ├── herramientas.py      # CRUD + Excel + imágenes + .meta.json
    │   ├── preventivo.py        # CRUD + generar-OT
    │   ├── estados.py           # CRUD estados de equipo
    │   ├── users.py             # Gestión de usuarios
    │   ├── historial.py         # CRUD + enriquecer respuestas
    │   ├── reportes.py          # 6 endpoints de reportes
    │   ├── documentos.py        # Upload/download/ver/eliminar + .meta.json
    │   ├── dashboard.py         # Métricas del dashboard
    │   └── configuracion.py     # Config + backup/restore + escaneo + mover
    │
    ├── utils/
    │   ├── security.py          # bcrypt + JWT
    │   └── meta_json.py         # write_meta_json / build_*_meta / update_doc_meta
    │
    └── uploads/                 # Almacenamiento de archivos (no versionado)
        ├── EQUIPOS/             # E0001_Modelo_Serie/ (imágenes + DOC/ + OT/)
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

---

## Configuración del Sistema

El archivo `backend/config.json` centraliza la configuración del sistema:

```json
{
  "empresa": {
    "nombre": "CMMS-BioAI"
  },
  "directorios": {
    "uploads_base": "uploads",
    "equipos_imagenes": "EQUIPOS",
    "equipos_documentos": "EQUIPOS",
    "ot_documentos": "OT",
    "repuestos_imagenes": "REPUESTOS",
    "repuestos_documentos": "REPUESTOS",
    "herramientas_imagenes": "HERRAMIENTAS",
    "herramientas_documentos": "HERRAMIENTAS",
    "reportes": "REPORTES"
  },
  "sistema": {
    "idioma": "es",
    "zona_horaria": "America/La_Paz",
    "moneda": "BOB",
    "prefijo_equipos": "E",
    "prefijo_ordenes": "OT",
    "prefijo_inventario": "R"
  }
}
```

### Arquitectura de Directorios

- **`uploads_base`** es la única ruta editable por el usuario. Puede ser relativa (`"uploads"`) o absoluta (`"D:/uploads"`).
- Las sub-carpetas (`EQUIPOS`, `REPUESTOS`, `HERRAMIENTAS`, etc.) son **relativas a `uploads_base`** y se derivan automáticamente.
- Al cambiar `uploads_base`, todas las sub-carpetas se reubican automáticamente sin necesidad de modificar cada una.

**Ejemplo con `uploads_base = "uploads"` (relativa):**

```
get_dir("equipos_imagenes") → /ruta/backend/uploads/EQUIPOS
get_dir("repuestos_documentos") → /ruta/backend/uploads/REPUESTOS
```

**Ejemplo con `uploads_base = "D:/uploads"` (absoluta):**

```
get_dir("equipos_imagenes") → D:/uploads/EQUIPOS
get_dir("repuestos_documentos") → D:/uploads/REPUESTOS
```

### Campos Editables desde la UI

| Campo | Editable | Ubicación |
|-------|----------|-----------|
| `empresa.nombre` | Sí | Página Configuración |
| `directorios.uploads_base` | Sí | Página Configuración |
| Sub-carpetas (`EQUIPOS`, etc.) | No | Se derivan automáticamente |
| `sistema.*` | No | Solo lectura |

### Cambio de Ubicación de Archivos

Cuando se cambia `uploads_base` desde la página de Configuración:

1. El sistema **mueve automáticamente** los archivos de la ubicación anterior a la nueva (copiar → verificar → eliminar originales).
2. Los archivos estáticos se **re-montan automáticamente** sin necesidad de reiniciar el backend.
3. Las rutas en la BD son **relativas** (`EQUIPOS/E0001_.../foto.jpg`), así que funcionan en cualquier ubicación.

Todos los módulos del backend deben importar rutas desde `config.py`:

```python
from config import get_dir, sanitize_filename

dir_equipos = get_dir("equipos_imagenes")  # Ruta absoluta, se crea si no existe
nombre_seguro = sanitize_filename("Inspección")  # → "Inspecci_n"
```

---

## Estructura de Almacenamiento de Archivos

El sistema organiza los archivos subidos en una estructura jerárquica bajo `uploads_base`. Las rutas se configuran centralmente en `config.json` y se acceden mediante `config.py → get_dir(key)`.

Junto a cada entidad se genera un archivo `.meta.json` que contiene los metadatos necesarios para reconstruir el registro en la base de datos si esta se pierde (ver [Estrategia de Recuperación](#estrategia-de-recuperación-de-datos-3-capas)).

### Equipos

```text
uploads/EQUIPOS/
└── E0001_CX23_MIC-OLY-001/             # Carpeta del equipo (E + ID + Modelo + Serie)
    ├── .meta.json                       # Metadatos del equipo para recuperación
    ├── E0001_CX23_MIC-OLY-001.jpg       # Imagen principal del equipo
    ├── DOC/                             # Documentos asociados al equipo
    │   ├── .meta.json                   # Metadatos de documentos para recuperación
    │   ├── manual_usuario.pdf
    │   └── certificado_garantia.pdf
    └── OT/                              # Órdenes de trabajo del equipo
        └── OT0001_Correctivo_CX23_MIC-OLY-001/
            ├── .meta.json               # Metadatos de documentos de la OT
            ├── foto_falla.png
            └── informe_reparacion.pdf
```

### Órdenes de Trabajo

```text
uploads/OT/
└── OT0001_Correctivo_CX23_MIC-OLY-001.txt   # Archivo índice de la OT

uploads/EQUIPOS/E0001_CX23_MIC-OLY-001/
└── OT/
    └── OT0001_Correctivo_CX23_MIC-OLY-001/   # Misma carpeta que el .txt
        ├── .meta.json
        ├── foto_falla.png
        └── informe_reparacion.pdf
```

La carpeta de OT dentro del equipo comparte el mismo nombre que el archivo índice `.txt` en `uploads/OT/`, lo que permite la referencia cruzada directa entre ambos.

### Repuestos

```text
uploads/REPUESTOS/
└── R0001_Filtro_HEPA/                  # Carpeta del repuesto (R + ID + Nombre)
    ├── .meta.json                       # Metadatos del repuesto para recuperación
    ├── R0001_Filtro_HEPA.jpg            # Imagen del repuesto
    └── DOC/                             # Documentos asociados
        ├── .meta.json                   # Metadatos de documentos
        ├── ficha_tecnica.pdf
        └── certificado_calibracion.pdf
```

### Herramientas

```text
uploads/HERRAMIENTAS/
└── H0001_Osciloscopio_digital/          # Carpeta de la herramienta (H + ID + Nombre)
    ├── .meta.json                        # Metadatos de la herramienta para recuperación
    ├── H0001_Osciloscopio_digital.jpg    # Imagen de la herramienta
    └── DOC/                              # Documentos asociados
        ├── .meta.json                    # Metadatos de documentos
        ├── manual_usuario.pdf
        └── certificado_calibracion.pdf
```

### Convención de Nombres

| Entidad | Formato | Ejemplo |
|---------|---------|---------|
| Carpeta de Equipo | `E{ID4d}_Modelo_Serie` | `E0001_CX23_MIC-OLY-001` |
| Carpeta de Repuesto | `R{ID4d}_NombreSanitizado` | `R0001_Filtro_HEPA` |
| Carpeta de Herramienta | `H{ID4d}_NombreSanitizado` | `H0001_Osciloscopio_digital` |
| Archivo índice OT | `OT{ID4d}_Titulo_Tipo_Modelo_Serie.txt` | `OT0001_Correctivo_CX23_MIC-OLY-001.txt` |
| Carpeta OT en equipo | `OT{ID4d}_Titulo_Tipo_Modelo_Serie/` | `OT0001_Correctivo_CX23_MIC-OLY-001/` |
| Imagen de equipo | `E{ID4d}_Modelo_Serie.ext` | `E0001_CX23_MIC-OLY-001.jpg` |
| Imagen de repuesto | `R{ID4d}_Nombre.ext` | `R0001_Filtro_HEPA.jpg` |
| Imagen de herramienta | `H{ID4d}_Nombre.ext` | `H0001_Osciloscopio_digital.jpg` |

Los nombres se sanitizan mediante `config.py → sanitize_filename()`, que reemplaza caracteres no ASCII y espacios por guiones bajos, evitando problemas de codificación entre sistemas operativos.

---

## Estrategia de Recuperación de Datos (3 Capas)

El sistema implementa una estrategia de 3 capas para proteger los datos contra la pérdida de la base de datos SQLite:

### Capa 1 — Archivos `.meta.json` (Prevención)

Cada vez que se crea o actualiza una entidad (equipo, repuesto, herramienta) o se sube un documento, se genera un archivo `.meta.json` junto a los archivos con los metadatos necesarios para reconstruir el registro en la BD.

**Ejemplo de `.meta.json` de un equipo:**

```json
{
  "entidad_tipo": "equipo",
  "id": 1,
  "nombre_corto": "Microscopio Olympus CX23",
  "codigo": "E0001",
  "modelo": "CX23",
  "marca": "Olympus",
  "numero_serie": "MIC-OLY-001",
  "estado_id": 1,
  "imagen_ruta": "EQUIPOS/E0001_CX23_MIC-OLY-001/E0001_CX23_MIC-OLY-001.jpg"
}
```

**Ejemplo de `.meta.json` en carpeta `DOC/`:**

```json
{
  "documentos": [
    {
      "documento_id": 1,
      "nombre_archivo": "manual_usuario.pdf",
      "ruta_archivo": "EQUIPOS/E0001_CX23_MIC-OLY-001/DOC/manual_usuario.pdf",
      "tipo_archivo": "application/pdf",
      "entidad_tipo": "equipos",
      "entidad_id": 1
    }
  ]
}
```

### Capa 2 — Escaneo y Recuperación (Desde `.meta.json` y `.txt` de OTs)

Si la BD se pierde, el sistema puede escanear todos los `.meta.json` y los archivos `.txt` de referencia de OTs, y recuperar los registros:

| Endpoint | Descripción |
|----------|-------------|
| `GET /configuracion/escanear` | Escanea `.meta.json` (entidades + documentos) y `.txt` (OTs) y reporta entidades huérfanas e imágenes faltantes |
| `POST /configuracion/recuperar` | Recupera registros huérfanos desde `.meta.json`/`.txt` y sincroniza imágenes faltantes en registros existentes |

**Qué hace el escaneo (v0.8.3+):**

1. **Detecta huérfanos** (entidades en archivos pero no en BD):
   - Equipos, Repuestos, Herramientas desde `.meta.json` en sus carpetas raíz
   - Órdenes de Trabajo desde archivos `.txt` en `uploads/OT/`
   - Documentos desde `.meta.json` en carpetas `DOC/` y `OT/OTxxxx/`

2. **Detecta imágenes faltantes**: si el registro existe en BD pero con `imagen_ruta=NULL` y el `.meta.json` tiene la ruta, se reporta como "imagen faltante". Al ejecutar "Recuperar / Sincronizar", se actualiza el campo en la BD.

3. **Recupera documentos de OTs**: ahora se escanean las carpetas `OT/OTxxxx_Titulo_Modelo_Serie/` dentro de cada equipo (donde se guardan los documentos asociados a esa OT). Antes solo se escaneaba la carpeta `DOC/` de cada entidad.

4. **Reconstruye OTs desde `.txt`**: el archivo `uploads/OT/OTxxxx_Titulo_Modelo_Serie.txt` (generado automáticamente al subir el primer documento de una OT) contiene el ID, título, prioridad, descripción de la falla y los datos del equipo asociado. La recuperación crea la OT con estado "Abierta" y la asocia al equipo correspondiente.

**Limitaciones conocidas:**
- Las OTs recuperadas se crean con estado "Abierta" (no se puede saber el estado original desde el `.txt`).
- Los campos `acciones_realizadas`, `tiempo_real_invertido`, `costo_adicional` y `costos_adicionales` no se restauran (no están en el `.txt`).
- Los repuestos utilizados en cada OT (`OtRepuestoUtilizado`) no se recuperan (no hay `.meta.json` para esta relación).
- El historial de mantenimiento (`EventoHistorial`) no se recupera (no tiene `.meta.json`).

### Capa 3 — Backup y Restore (Exportación/Importación JSON)

Backup completo de la base de datos y la configuración del sistema como archivo JSON:

| Endpoint | Descripción |
|----------|-------------|
| `GET /configuracion/backup` | Genera backup completo (BD + config.json) como JSON |
| `POST /configuracion/restore` | Restaura backup JSON (BD + config.json preservando `uploads_base` actual) |
| `GET /configuracion/backup/descargar` | Descarga backup como archivo `.json` |
| `POST /configuracion/restore/subir` | Restaura subiendo archivo `.json` |

**Nota sobre restore:** El restore preserva siempre el `uploads_base` actual del sistema, ya que las rutas en la BD son relativas y los archivos físicos pueden estar en una ubicación diferente a la del backup original. Esto permite restaurar un backup hecho en una ubicación a un sistema con otra ubicación de almacenamiento.

### Resumen de la Estrategia

| Capa | Mecanismo | Cuándo usar | Pérdida cubierta |
|------|-----------|-------------|------------------|
| 1 | `.meta.json` | Siempre activo | Corrupción/eliminación de BD |
| 2 | Escaneo + Recuperación | Después de perder la BD | Reconstrucción desde archivos |
| 3 | Backup/Restore | Mantenimiento periódico | Pérdida total (BD + archivos) |

---

## Modelo de Base de Datos

El sistema utiliza 12 tablas en SQLite, gestionadas con SQLModel:

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
| tiempo_real_investido | float? | Tiempo de trabajo |
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

**`herramienta`** — Inventario de herramientas y materiales

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador automático |
| nombre_herramienta | str | Nombre descriptivo |
| numero_identificacion | str? | Código interno del taller |
| descripcion | str? | Descripción detallada |
| categoria | str? | Instrumento de Medición / Herramienta Manual / Consumible / Kit |
| cantidad_disponible | int | Stock actual |
| unidad_medida | str | Unidad (unidad, juego, litro, etc.) |
| ubicacion_almacen | str? | Ubicación física |
| estado_uso | str? | Disponible / En Uso / En Reparación / Dado de Baja |
| imagen_ruta | str? | Ruta relativa a imagen |
| costo_adquisicion | float? | Costo de adquisición |
| fecha_adquisicion | date? | Fecha de adquisición |
| proveedor_ultimo | str? | Último proveedor |
| observaciones | str? | Observaciones adicionales |

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

**`proveedor`** — Empresas proveedoras de equipos, repuestos, herramientas y servicios (RF10)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador |
| nombre_empresa | str (unique) | Nombre legal o comercial del proveedor |
| ciudad | str? | Ciudad principal (independiente de direccion) |
| direccion | str? | Dirección física principal |
| telefono_principal | str? | Teléfono principal de la empresa |
| email_principal | str? | Email principal de la empresa |
| pagina_web | str? | Sitio web oficial |
| notas_generales | str? | Observaciones comerciales |

**`contactoproveedor`** — Contactos asociados a un proveedor (relación 1:N, RF10)

| Campo | Tipo | Descripción |
|-------|------|-------------|
| id | int (PK) | Identificador |
| proveedor_id | int (FK→proveedor) | Proveedor al que pertenece |
| nombre_contacto | str | Nombre completo del contacto |
| cargo | str? | Cargo (Gerente, Vendedor, Soporte, etc.) |
| telefono_contacto | str? | Teléfono directo del contacto |
| email_contacto | str? | Email directo del contacto |
| notas_contacto | str? | Notas específicas del contacto |

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
| POST | `/equipos/` | Crea un nuevo equipo (+ .meta.json) |
| GET | `/equipos/{id}` | Obtiene un equipo por ID |
| PUT | `/equipos/{id}` | Actualiza un equipo (+ actualiza .meta.json) |
| DELETE | `/equipos/{id}` | Elimina un equipo |
| GET | `/equipos/tecnicos` | Lista técnicos disponibles |
| GET | `/equipos/estados` | Lista estados de equipo |
| GET | `/equipos/plantilla-csv` | Descarga plantilla CSV |
| GET | `/equipos/plantilla-excel` | Descarga plantilla Excel |
| POST | `/equipos/import-excel` | Importa equipos desde Excel/CSV |
| POST | `/equipos/{id}/upload_imagen` | Sube imagen de equipo (+ .meta.json) |
| DELETE | `/equipos/{id}/imagen` | Elimina imagen de equipo (+ .meta.json) |

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
| POST | `/repuestos/` | Agrega un repuesto (+ .meta.json) |
| GET | `/repuestos/{id}` | Obtiene un repuesto |
| PUT | `/repuestos/{id}` | Actualiza un repuesto (+ .meta.json) |
| DELETE | `/repuestos/{id}` | Elimina un repuesto |
| GET | `/repuestos/plantilla-csv` | Descarga plantilla CSV |
| GET | `/repuestos/plantilla-excel` | Descarga plantilla Excel |
| POST | `/repuestos/import-excel` | Importa repuestos desde Excel/CSV |
| POST | `/repuestos/{id}/upload_imagen` | Sube imagen de repuesto (+ .meta.json) |
| DELETE | `/repuestos/{id}/imagen` | Elimina imagen de repuesto (+ .meta.json) |

### Herramientas (`/herramientas`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/herramientas/` | Lista todas las herramientas |
| POST | `/herramientas/` | Crea una herramienta (+ .meta.json) |
| GET | `/herramientas/{id}` | Obtiene una herramienta |
| PUT | `/herramientas/{id}` | Actualiza una herramienta (+ .meta.json) |
| DELETE | `/herramientas/{id}` | Elimina una herramienta |
| GET | `/herramientas/plantilla-excel` | Descarga plantilla Excel |
| POST | `/herramientas/import-excel` | Importa herramientas desde Excel/CSV |
| POST | `/herramientas/{id}/upload_imagen` | Sube imagen de herramienta (+ .meta.json) |
| DELETE | `/herramientas/{id}/imagen` | Elimina imagen de herramienta (+ .meta.json) |

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
| POST | `/documentos/` | Sube un documento (con entidad asociada + .meta.json) |
| GET | `/documentos/` | Lista documentos (filtrable por entidad) |
| GET | `/documentos/{id}/ver` | Visualiza documento inline en navegador |
| GET | `/documentos/{id}/descargar` | Descarga documento como adjunto |
| DELETE | `/documentos/{id}` | Elimina un documento (+ actualiza .meta.json) |

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

### Configuración (`/configuracion`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/configuracion/` | Lee la configuración actual (config.json) |
| PUT | `/configuracion/` | Actualiza empresa.nombre y/o directorios.uploads_base |
| GET | `/configuracion/estados-bd` | Resumen de registros en la BD por tabla |
| GET | `/configuracion/escanear` | Escanea .meta.json y reporta entidades huérfanas |
| POST | `/configuracion/recuperar` | Recupera registros huérfanos desde .meta.json |
| GET | `/configuracion/backup` | Genera backup completo (BD + config.json) como JSON |
| POST | `/configuracion/restore` | Restaura backup JSON (preserva uploads_base actual) |
| GET | `/configuracion/backup/descargar` | Descarga backup como archivo .json |
| POST | `/configuracion/restore/subir` | Restaura subiendo archivo .json |
| POST | `/configuracion/mover-archivos` | Mueve archivos entre ubicaciones de uploads_base |

### Usuarios (`/users`)

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/users/` | Lista usuarios |
| POST | `/users/` | Crea un nuevo usuario |

### Proveedores (`/proveedores`) — RF10

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/proveedores/` | Lista todos los proveedores (sin contactos) |
| GET | `/proveedores/con-contactos` | Lista todos los proveedores con sus contactos |
| POST | `/proveedores/` | Crea un nuevo proveedor |
| GET | `/proveedores/{id}` | Obtiene un proveedor por ID (con contactos) |
| PUT | `/proveedores/{id}` | Actualiza un proveedor |
| DELETE | `/proveedores/{id}` | Elimina un proveedor y sus contactos |
| GET | `/proveedores/plantilla-csv` | Descarga plantilla CSV con datos de ejemplo |
| GET | `/proveedores/plantilla-excel` | Descarga plantilla Excel con datos de ejemplo (20 proveedores) |
| POST | `/proveedores/import-excel` | Importa proveedores desde Excel/CSV (upsert por `nombre_empresa`) |
| POST | `/proveedores/{id}/contactos` | Agrega un contacto a un proveedor |
| GET | `/proveedores/{id}/contactos` | Lista los contactos de un proveedor |
| PUT | `/proveedores/contactos/{id}` | Actualiza un contacto |
| DELETE | `/proveedores/contactos/{id}` | Elimina un contacto |

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
| RF09 | Gestión de Inventario de Herramientas y Materiales de Trabajo | Completado |
| RF10 | Gestión de Proveedores y Contactos | Completado |

### RF09 — Gestión de Inventario de Herramientas y Materiales

Diferencia herramientas del taller (osciloscopios, testers, kits) de los repuestos médicos. Las herramientas son activos del taller que no se consumen en una OT; su costo se contabiliza como costo operativo del departamento, no como costo de mantenimiento de un equipo individual.

**Categorías disponibles:**

| Categoría | Ejemplos |
|-----------|----------|
| Instrumento de Medición | Osciloscopios, multímetros, analizadores de seguridad |
| Herramienta Manual | Destornilladores, alicates, estaciones de soldadura |
| Consumible | Alcohol isopropílico, estaño, cintas |
| Kit | Conjuntos de herramientas o accesorios |

**Estados de uso:** Disponible, En Uso, En Reparación, Dado de Baja

**Diferenciación clave con RF04 (Repuestos):**

| Aspecto | Repuestos (RF04) | Herramientas (RF09) |
|---------|------------------|---------------------|
| Propósito | Partes que se reemplazan en equipos médicos | Recursos del taller para reparar equipos |
| Impacto en costos | Se contabiliza como costo de mantenimiento del equipo | Se contabiliza como costo operativo del taller |
| Consumo | Se consumen (stock disminuye) | No se consumen (solo cambia su estado) |
| Vinculación | Directa a una OT y un Equipo Médico | Inventario independiente, uso opcional en OTs |
| Prefijo carpetas | `R` (R0001_...) | `H` (H0001_...) |

### RF10 — Gestión de Proveedores y Contactos

Centraliza el directorio de empresas proveedoras de equipos, repuestos, herramientas y servicios de mantenimiento biomédico. Cada proveedor puede tener **múltiples contactos asociados** (gerente, vendedor, soporte técnico, etc.) con sus propios datos de contacto.

**Campos del Proveedor** (RF10):

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `nombre_empresa` | Sí (unique) | Nombre legal o comercial del proveedor |
| `ciudad` | No | Ciudad principal (independiente de `direccion`, usado por el filtro de ciudad) |
| `direccion` | No | Dirección física completa |
| `telefono_principal` | No | Teléfono de la empresa |
| `email_principal` | No | Email principal |
| `pagina_web` | No | Sitio web oficial |
| `notas_generales` | No | Observaciones comerciales (garantías, condiciones, etc.) |

**Campos del Contacto** (RF10):

| Campo | Obligatorio | Descripción |
|-------|-------------|-------------|
| `nombre_contacto` | Sí | Nombre completo del contacto |
| `cargo` | No | Cargo en la empresa (Gerente, Vendedor, Soporte, etc.) |
| `telefono_contacto` | No | Teléfono directo |
| `email_contacto` | No | Email directo |
| `notas_contacto` | No | Notas específicas (horarios, preferencias, etc.) |

**Funcionalidades implementadas:**

- CRUD completo de proveedores con búsqueda por empresa, email, teléfono o ciudad
- CRUD de contactos asociados (relación 1:N desde el modal de detalle)
- Filtros por ciudad (campo directo) y por "tiene/sin página web"
- Paginación cada 10 registros
- **Importación masiva Excel/CSV** con `upsert` por `nombre_empresa` (si el nombre ya existe, se actualiza; si no, se crea)
- **Plantilla Excel/CSV descargable** con 20 proveedores biomédicos de Bolivia de ejemplo
- Modal de resultados con conteo de creados / actualizados / fallidos y detalle de errores por fila
- Migración automática: al iniciar el backend, se agrega la columna `ciudad` a la tabla `proveedor` si no existe (SQLite ALTER TABLE)

**Relaciones con otros RF** (planificadas para futuras versiones):

| RF | Entidad | Campo actual (texto libre) | Objetivo |
|----|---------|----------------------------|----------|
| RF01 | Equipo | `proveedor_principal` | Convertir en FK a `Proveedor.id` |
| RF04 | Repuesto | `proveedor_ultimo` | Convertir en FK a `Proveedor.id` |
| RF09 | Herramienta | `proveedor_ultimo` | Convertir en FK a `Proveedor.id` |
| RF03/RF05 | TareaPreventiva / EventoHistorial | Sin vínculo directo | Asociar contratos de mantenimiento y servicios con proveedores |

> **Nota:** Los contactos asociados **no se importan** desde el Excel. Una vez importados los proveedores, los contactos se agregan individualmente desde el modal de detalle de cada proveedor (icono de ojo en la tabla).

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
| v0.7.0 | **Herramientas + Recuperación** | RF09 completo, estrategia de recuperación de datos (3 capas), archivos `.meta.json`, escaneo y recuperación de registros huérfanos, backup/restore completo (BD + config.json), página de configuración |
| v0.8.0 | **Arquitectura + Configuración** | Rediseño de directorios (sub-carpetas relativas a `uploads_base`), cambio de prefijo `I`→`R` para repuestos, `uploads_base` editable desde UI, movimiento automático de archivos, re-montaje de archivos estáticos sin reiniciar, restore preserva `uploads_base` actual, nombre de empresa modificable |
| v0.8.1 | **RF10 Proveedores + Ciudad** | Reorden del menú lateral, campo `ciudad` añadido a `Proveedor` (RF10) con migración automática, importación masiva de proveedores desde Excel/CSV con upsert por `nombre_empresa`, plantilla Excel descargable con 20 proveedores biomédicos de Bolivia de ejemplo, modal de resultados de importación con conteo de creados/actualizados/fallidos, página de Ayuda actualizada con relaciones de RF10 con RF01/RF04/RF09/RF03+RF05 |
| v0.8.2 | **Plantillas Estáticas** | Plantillas Excel/CSV migradas del backend a archivos estáticos en `frontend/public/plantillas/` (8 archivos en total: 4 `.xlsx` + 4 `.csv` para Equipos, Repuestos, Herramientas y Proveedores). El frontend descarga directamente desde `/plantillas/<nombre>` sin llamar al backend. Los endpoints `/plantilla-excel` y `/plantilla-csv` del backend se mantienen como respaldo con aviso en su docstring. Script `scripts/generar_plantillas_estaticas.py` para regenerar los 8 archivos cuando se actualicen los modelos. |
| v0.8.3 | **Capa 2 — Recuperación Mejorada** | Arreglo de 3 bugs en el endpoint `/configuracion/recuperar`: (1) **Sincronización de imágenes**: si un equipo/repuesto/herramienta existe en BD con `imagen_ruta=NULL` pero su `.meta.json` tiene la ruta, ahora se sincroniza automáticamente (antes se saltaba el registro por "ya existir"). (2) **Recuperación de OTs**: ahora se leen los archivos `.txt` de referencia en `uploads/OT/` y se reconstruyen las OTs con su título, prioridad, descripción y equipo asociado (antes no se recuperaba ninguna OT). (3) **Documentos de OTs**: ahora se escanean las carpetas `OT/OTxxxx_Titulo_Modelo_Serie/` dentro de cada equipo para recuperar los documentos asociados a cada OT (antes solo se escaneaba `DOC/`). UI del escaneo mejorada con tarjetas para "Imágenes faltantes" y resultados detallados por tipo. |
| v0.9.0 | **RF01 Universal + Modo TEST** | Rediseño mayor del modelo `Equipo` (RF01): eliminados `registro_sanitario_bolivia`, `calibracion_proxima`, `responsable_tecnico_id`, `proveedor_principal` (texto). Agregados `observaciones`, `fecha_inicio_garantia`, `condicion_origen` (enum 9 valores), `proveedor_principal_id` (FK). Campos `modelo`/`marca`/`numero_serie` NO editables después de creado. DELETE con verificación de dependencias. **3 usuarios TEST**: `admin/admin`, `tech/tech`, `user/user`. **Modo TEST**: cargar/limpiar datos. Badge "🧪 MODO TEST". `proxima_fecha` editable. Widget "MPs Próximos (7 días)". |
| v0.9.1 | **RF11 Costos en OT** | Tabla `OtCostoAdicional` con 8 tipos de costo (Transporte, Servicio Externo, etc.). CRUD completo de costos por OT. `DocumentoAdjunto` con `ot_costo_id` para justificativos. Total automático. Eliminados campos obsoletos `costo_adicional` y `costos_adicionales`. Dropdown de equipo con `nombre + serie + ubicación` + info-box. Modal de OT con sección "💰 Costos Adicionales". Historial usa suma de costos al completar OT. |
| v0.9.2 | **RF12 Contratos + RF03 MP Rediseñado + Planificación** | **RF12 Contratos**: tabla `Contrato` + `ContratoEquipo` (N:M), cálculo de vigencia en runtime, 3 enums (tipo_contrato, periodicidad, moneda), badges visuales, página dedicada, secciones en detalle de Equipo y Proveedor, `contrato_id` opcional en `OrdenTrabajo`. **RF03 MP Rediseñado**: ciclo verde→amarillo→rojo (🟢 Programada / 🟡 Recordatorio / 🔴 Vencida), `proxima_fecha` editable, `frecuencia_dias` como sugerencia. **Página Planificación**: calendario mensual unificado OT+MP con filtros (tipo, equipo, ubicación, responsable), colores del ciclo MP + colores de OT, leyenda visual, modal detalle con navegación. |
| v0.9.3 | **AyudaView + Exportación RF13** | AyudaView actualizada con todas las entidades (incluidas OtCostoAdicional, Contrato, ContratoEquipo) y RFs (RF11, RF12, RF13, RF03+, PLAN). Botones "📤 Exportar" en Equipos, Órdenes y Contratos (descarga Excel .xls con datos filtrados). Servicio `export.js` reutilizable con `exportToExcelHTML()` y `exportToCSV()`. |

---

## Observaciones Técnicas

- **Seed de Estados:** Los estados se crean automáticamente al iniciar el backend. Si se personaliza la base de datos manualmente, el seed no sobrescribirá datos existentes (solo inserta si las tablas están vacías).
- **IDs de Base de Datos:** Los IDs son automáticos e incrementales. Si se elimina un registro, ese ID no se reutiliza. Para control normado de inventario, usar `numero_serie` o `numero_material`.
- **Importación Excel:** Las plantillas son **archivos estáticos** ubicados en `frontend/public/plantillas/` (8 archivos: 4 `.xlsx` + 4 `.csv` para Equipos, Repuestos, Herramientas y Proveedores). Vite los sirve directamente desde la URL `/plantillas/<nombre>` sin necesidad de llamar al backend. Los endpoints `/plantilla-excel` y `/plantilla-csv` del backend se mantienen como **respaldo** y para documentación Swagger. Soporta formatos `.xlsx` y `.csv`. Para modificar una plantilla, edita el archivo correspondiente en `frontend/public/plantillas/` o regenera los 8 archivos con `python scripts/generar_plantillas_estaticas.py`.
- **Configuración Centralizada:** Todos los módulos deben usar `from config import get_dir` para obtener rutas de almacenamiento. Nunca calcular rutas con `__file__` desde otros módulos.
- **Arquitectura de Directorios:** `uploads_base` es la única ruta configurable. Las sub-carpetas (`EQUIPOS`, `REPUESTOS`, etc.) son relativas a `uploads_base` y se derivan automáticamente. Al cambiar `uploads_base`, todas las sub-carpetas se reubican sin intervención manual.
- **Re-montaje Dinámico:** Al cambiar `uploads_base`, los archivos estáticos se re-montan automáticamente sin reiniciar el backend. Las imágenes y documentos son accesibles inmediatamente desde la nueva ubicación.
- **Rutas Relativas en BD:** Todas las rutas de archivos en la BD (`imagen_ruta`, `ruta_archivo`) son relativas a `uploads_base`. Esto permite mover toda la carpeta `uploads` a otra ubicación (ej: de `backend/uploads` a `D:\uploads`) sin romper las referencias.
- **Archivos .meta.json:** Se generan automáticamente junto a cada entidad y carpeta `DOC/`. Contienen los metadatos necesarios para reconstruir los registros de la BD si esta se pierde. Son la primera capa de la estrategia de recuperación de datos.
- **Backup/Restore Independiente de Ubicación:** El restore preserva siempre el `uploads_base` actual del sistema. Un backup hecho con `uploads_base = "uploads"` puede restaurarse en un sistema con `uploads_base = "D:/uploads"` sin problemas.
- **Sanitización de Nombres:** La función `sanitize_filename()` en `config.py` normaliza nombres de archivos/carpetas a ASCII seguro, reemplazando caracteres especiales por guiones bajos.
- **Seguridad:** El JWT secret está hardcodeado en `utils/security.py`. Para producción, mover a variable de entorno. Los endpoints no tienen protección de autenticación todavía (pendiente de implementar).
- **CORS:** Configurado con `allow_origins=["*"]` para desarrollo. Restringir para producción.
- **Proxy Vite:** Las peticiones `/uploads/*` desde el frontend se redirigen automáticamente al backend en puerto 8000 mediante el proxy configurado en `vite.config.js`.
- **Migraciones:** Las funciones `_migrate_repuesto_columns()`, `_migrate_documento_herramienta_id()` y `_migrate_proveedor_ciudad()` en `database.py` agregan columnas nuevas a las tablas existentes si no están presentes (SQLite ALTER TABLE), permitiendo evolución del esquema sin pérdida de datos.
- **Prefijos de Carpetas:** Equipos usan `E` (E0001), Repuestos usan `R` (R0001), Herramientas usan `H` (H0001), OTs usan `OT` (OT0001). Estos prefijos están definidos en `config.json` → `sistema.prefijo_*`.

---

## Roadmap

### Próximos Pasos (Prioridad Alta)

1. **Buscadores faltantes** — Agregar búsqueda en Órdenes y Preventivo
2. **Mejoras UX** — Iconos en barras de búsqueda, placeholders más cortos
3. **INVENTARIO: Mejoras de UI** — Separar campos Numero de Material / Código en dos campos, mostrar solo numero_serie en tabla

### Prioridad Media

4. **Roles y permisos** — Autorización por roles en frontend (route guards) y backend (dependencias de auth)
5. **RF10 — Migración a FK** — Convertir `equipo.proveedor_principal`, `repuesto.proveedor_ultimo` y `herramienta.proveedor_ultimo` en FK a `Proveedor.id`
6. **Notificaciones** — Alertas de stock bajo, calibraciones próximas, vencimientos

### Prioridad Baja (Post v1.0)

7. **RF07 — Módulo IA** — Sugerencias de mantenimiento, detección de patrones, recomendaciones
8. **Despliegue unificado** — Frontend compilado servido desde FastAPI (un solo puerto)
9. **Empaquetado** — PyInstaller (.exe) + instalador Inno Setup / NSIS
10. **Reportes PDF** — Exportación de reportes a formato PDF
11. **Normalización** — Estándares UMDNS / GMDN para registro de equipos

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
