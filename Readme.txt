# CMMS-BioAI

Sistema de Gestión de Mantenimiento Asistido por Computadora (CMMS) desarrollado para el contexto boliviano. Diseñado para ser una solución asequible, offline-first y centrada en el usuario para la gestión de equipos médicos biomédicos.

## Estado del Proyecto (Prototipo Funcional)

El sistema se encuentra en fase de desarrollo activo. Se han completado los módulos principales de gestión.

- [x] **Gestión de Activos (Equipos Médicos):** CRUD completo, asignación de técnicos, estados con colores dinámicos, búsqueda y filtrado.
- [x] **Gestión de Órdenes de Trabajo (Correctivo):** Ciclo completo (Crear, Asignar, Resolver, Ver), gestión de repuestos y validaciones.
- [x] **Gestión de Inventario de Repuestos:** CRUD, búsqueda y control de stock automático al usarse en OTs.
- [x] **Gestión de Usuarios:** Creación de técnicos y administradores.
- [x] **Autenticación de Usuarios (JWT con bcrypt):** Login seguro con tokens JWT y contraseñas hasheadas con bcrypt.
- [x] **Dashboard con Gráficos:** Tarjetas con métricas en tiempo real + gráficos de Equipos por Estado, Órdenes por Prioridad y Órdenes por Estado.
- [x] **Importación/Exportación Excel (Equipos):** Descarga de plantilla y carga masiva de equipos desde archivos .xlsx.
- [x] **Importación/Exportación Excel (Repuestos):** Descarga de plantilla y carga masiva de repuestos desde archivos .xlsx.
- [x] **Mantenimiento Preventivo:** Creación de tareas preventivas con frecuencia en días, asignación de repuestos/kit de mantenimiento, cálculo automático de próxima fecha.
- [x] **Seed de Base de Datos:** Creación automática de usuario admin y estados por defecto al iniciar el sistema.
- [ ] Módulo de Inteligencia Artificial (Sugerencias).
- [ ] Gestión Documental (Subida de PDFs/Manuales).

## Tecnologías Utilizadas

### Backend
*   **Lenguaje:** Python 3.10+
*   **Framework:** FastAPI
*   **ORM:** SQLModel (basado en SQLAlchemy y Pydantic)
*   **Base de Datos:** SQLite (ideal para prototipos y uso offline)
*   **Seguridad:** JWT (JSON Web Tokens) y bcrypt (passlib)
*   **Procesamiento Excel:** openpyxl

### Frontend
*   **Framework:** Vue.js 3
*   **Empaquetador:** Vite
*   **Enrutamiento:** Vue Router
*   **Gráficos:** Chart.js + vue-chartjs
*   **Estilos:** CSS Scoped

## Estructura del Proyecto

```text
CMMS-BioAI/
├── backend/
│   ├── api/
│   │   └── routes/      # Endpoints (auth, equipos, ordenes, repuestos, preventivo, estados, users)
│   ├── models/          # Modelos de Base de Datos (Tablas)
│   │   ├── usuarios.py  # Modelo de Usuario
│   │   ├── equipos.py   # Modelo de Equipo
│   │   ├── estados.py   # Modelo EstadoEquipo (lookup)
│   │   ├── ordenes.py   # Modelos OrdenTrabajo y EstadoOT (lookup)
│   │   ├── repuestos.py # Modelo de Repuesto
│   │   └── preventivo.py # Modelos TareaPreventiva y TareaRepuesto
│   ├── schemas/         # Esquemas de validación (Pydantic)
│   ├── main.py          # Punto de entrada de la API
│   ├── database.py      # Configuración de SQLite + seed automático
│   └── security.py      # Utilidades JWT y bcrypt
├── frontend/
│   ├── src/
│   │   ├── views/       # Vistas principales (HomeDashboard, Equipos, Ordenes, Inventario, Preventivo)
│   │   ├── components/  # Componentes compartidos (Navbar)
│   │   ├── services/    # Conexión con la API (api.js)
│   │   └── router/      # Definición de rutas
│   └── package.json
└── README.md
```

## Instalación y Ejecución Local

### Requisitos Previos
*   Python 3 instalado.
*   Node.js y npm instalados.

### 1. Configuración del Backend
Abre una terminal en la carpeta `backend`:

```bash
# Crear entorno virtual (opcional pero recomendado)
python -m venv venv

# Activar entorno (Windows)
venv\Scripts\activate

# Activar entorno (Linux/Mac)
source venv/bin/activate

# Instalar dependencias
pip install fastapi uvicorn sqlmodel python-jose[cryptography] passlib[bcrypt] python-multipart openpyxl bcrypt

# Iniciar el servidor
uvicorn main:app --reload
```

El backend correrá en `http://127.0.0.1:8000`.

Al iniciar por primera vez, el sistema crea automáticamente:
- **Usuario admin por defecto:** usuario `admin`, contraseña `admin123`
- **6 estados de equipo:** Operativo, En Mantenimiento, Averiado (Pendiente Reparación), Retirado/Dado de Baja, En Reserva, En Tránsito
- **5 estados de orden de trabajo:** Abierta, En Proceso, Bloqueada (Esp. Repuestos), Completada, Cancelada

### 2. Configuración del Frontend
Abre una nueva terminal en la carpeta `frontend`:

```bash
# Instalar dependencias
npm install

# Iniciar la aplicación web
npm run dev
```

El frontend correrá en `http://localhost:5173` (o puerto similar).

### 3. Reinicio del Sistema
Para reiniciar la base de datos a cero:
1. Detener el backend (`Ctrl+C`)
2. Eliminar el archivo `cmms_bioai.db`
3. Reiniciar el backend — las tablas y datos seed se recrean automáticamente

## Endpoints Principales (API)

La documentación interactiva completa está disponible en `http://127.0.0.1:8000/docs` (Swagger UI).

### Autenticación (`/auth`)
*   `POST /token` - Inicia sesión y obtiene token JWT.

### Equipos (`/equipos`)
*   `GET /equipos/` - Lista todos los equipos.
*   `POST /equipos/` - Crea un nuevo equipo.
*   `PUT /equipos/{id}` - Actualiza un equipo.
*   `DELETE /equipos/{id}` - Elimina un equipo.
*   `GET /equipos/estados` - Obtiene la lista de estados de equipo.
*   `GET /equipos/plantilla-excel` - Descarga plantilla Excel para carga masiva.
*   `POST /equipos/import-excel` - Importa equipos desde archivo Excel.

### Órdenes de Trabajo (`/ordenes`)
*   `GET /ordenes/` - Lista todas las órdenes.
*   `POST /ordenes/` - Crea una nueva orden.
*   `GET /ordenes/{id}` - Obtiene detalles de una orden.
*   `PUT /ordenes/{id}` - Actualiza estado, acciones o repuestos.
*   `GET /ordenes/estados/` - Obtiene la lista de estados de OT.
*   `POST /ordenes/estados/` - Crea un nuevo estado de OT.

### Inventario (`/repuestos`)
*   `GET /repuestos/` - Lista el inventario.
*   `POST /repuestos/` - Agrega un repuesto nuevo.
*   `PUT /repuestos/{id}` - Actualiza un repuesto.
*   `DELETE /repuestos/{id}` - Elimina un repuesto.
*   `GET /repuestos/plantilla-excel` - Descarga plantilla Excel para carga masiva.
*   `POST /repuestos/import-excel` - Importa repuestos desde archivo Excel.

### Mantenimiento Preventivo (`/preventivo`)
*   `GET /preventivo/` - Lista todas las tareas preventivas.
*   `POST /preventivo/` - Crea una tarea preventiva (con repuestos opcionales).
*   `GET /preventivo/{id}` - Obtiene detalle de una tarea.
*   `PUT /preventivo/{id}` - Actualiza una tarea.
*   `DELETE /preventivo/{id}` - Elimina una tarea.

### Usuarios (`/users`)
*   `GET /users/` - Lista usuarios (para asignación de técnicos).
*   `POST /users/` - Crea un nuevo usuario.

## Datos Seed (Carga Automática)

Al iniciar el backend por primera vez (o tras eliminar la base de datos), se crean automáticamente los siguientes datos:

### Usuario Admin
| Campo | Valor |
|-------|-------|
| Usuario | `admin` |
| Contraseña | `admin123` |
| Email | `admin@biolab.com` |
| Rol | `admin` |

> **Nota:** Cambia la contraseña del admin después del primer inicio de sesión.

### Estados de Equipo (`estadoequipo`)
| ID | Estado | Color |
|----|--------|-------|
| 1 | Operativo | Verde `#27ae60` |
| 2 | En Mantenimiento | Naranja `#f39c12` |
| 3 | Averiado (Pendiente Reparación) | Rojo `#e74c3c` |
| 4 | Retirado/Dado de Baja | Gris `#7f8c8d` |
| 5 | En Reserva | Azul `#3498db` |
| 6 | En Tránsito | Púrpura `#9b59b6` |

### Estados de Orden de Trabajo (`estadoot`)
| ID | Estado | Color |
|----|--------|-------|
| 1 | Abierta | Azul `#3b82f6` |
| 2 | En Proceso | Naranja `#f39c12` |
| 3 | Bloqueada (Esp. Repuestos) | Naranja oscuro `#e67e22` |
| 4 | Completada | Verde `#27ae60` |
| 5 | Cancelada | Gris `#95a5a6` |

## Respaldo y Versionado (GitHub)

Para guardar los cambios realizados y respaldar el proyecto en GitHub, ejecuta los siguientes comandos en la terminal raíz del proyecto:

```bash
# 1. Agregar todos los archivos modificados
git add .

# 2. Crear un punto de guardado (Commit) con un mensaje descriptivo
git commit -m "Descripción breve de los cambios realizados"

# 3. Subir los cambios al repositorio remoto (GitHub)
git push origin main
```

## Historial de Cambios

### v0.3.0 — Seed de BD + Fix Preventivo + Excel Repuestos
- Seed automático: usuario admin por defecto, 6 estados de equipo, 5 estados de OT
- Fix: creación de tareas preventivas con repuestos (error de acceso a objeto Pydantic)
- Fix: refresh de objeto SQLModel después de múltiples commits
- Importación/Exportación Excel para Inventario/Repuestos
- Fix: detección de hoja correcta en Excel (no depender de `wb.active`)
- Fix: ordenamiento de rutas estáticas antes de dinámicas en repuestos

### v0.2.0 — Dashboard con Gráficos + Excel Equipos
- Dashboard mejorado con gráficos (Chart.js + vue-chartjs): Equipos por Estado, Órdenes por Prioridad, Órdenes por Estado
- Importación/Exportación Excel para Equipos (plantilla + carga masiva)
- Navbar como componente compartido
- Separación de vistas: HomeDashboard (métricas) y EquiposView (CRUD)

### v0.1.0 — Bug Fixes Iniciales + Funcionalidad Base
- Fix: autenticación SHA-256 migrada a bcrypt
- Fix: modelo Estado renombrado a EstadoEquipo
- Fix: endpoints mixtos separados (equipos vs estados)
- Fix: campos faltantes en schemas
- Fix: campos duplicados en formularios
- Fix: Navbar como componente reutilizable
- CRUD completo de Equipos, Órdenes, Repuestos, Usuarios
- Autenticación JWT funcional

## Observaciones Técnicas

*   **Seed de Estados:** Los estados se crean automáticamente al iniciar el backend. Si se personaliza la base de datos manualmente, el seed no sobrescribirá datos existentes (solo inserta si las tablas están vacías).
*   **IDs de Base de Datos:** Los IDs de los equipos son automáticos. Si se elimina un equipo, ese ID no se reutiliza. Para un control de inventario normado, se recomienda usar el campo `numero_serie` o crear un campo `codigo_activo`.
*   **Importación Excel:** Las plantillas se generan dinámicamente en el backend (no son archivos estáticos), garantizando sincronización con los modelos de datos actuales.
*   **Seguridad:** El JWT secret está hardcodeado (`security.py`). Para producción, mover a variable de entorno.

## Pendientes (Roadmap)

1.  **Módulo de Inteligencia Artificial:**
    *   Sugerencias de mantenimiento basadas en historial de equipos y órdenes.
    *   Detección de patrones de falla.
2.  **Mejoras de Seguridad:**
    *   Protección de endpoints con autenticación (solo usuarios logueados).
    *   Autorización por roles (solo admin puede crear usuarios/estados).
    *   JWT secret en variable de entorno.
3.  **Normalización de Equipos:**
    *   Analizar e implementar estándares internacionales (como UMDNS o GMDN) para el registro de equipos médicos.
4.  **Gestión Documental:**
    *   Módulo para subir y visualizar archivos PDF (manuales, garantías, registros sanitarios) asociados a los equipos.
5.  **Sistema de Configuración de Estados:**
    *   Interfaz para que el usuario gestione estados (crear, editar colores) desde la UI.

## Autor

Desarrollado como parte del proyecto de Maestría en Ingeniería Biomédica.
