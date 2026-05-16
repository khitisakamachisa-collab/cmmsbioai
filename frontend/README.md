# CMMS-BioAI

Sistema de Gestión de Mantenimiento Asistido por Computadora (CMMS) desarrollado para el contexto boliviano. Diseñado para ser una solución asequible, offline-first y centrada en el usuario para la gestión de equipos médicos biomédicos.

## Estado del Proyecto (Prototipo Funcional)

El sistema se encuentra en fase de desarrollo activo. Se han completado los módulos principales de gestión.

- [x] **Gestión de Activos (Equipos Médicos):** CRUD completo, asignación de técnicos, estados con colores dinámicos, búsqueda y filtrado.
- [x] **Gestión de Órdenes de Trabajo (Correctivo):** Ciclo completo (Crear, Asignar, Resolver, Ver), gestión de repuestos y validaciones.
- [x] **Gestión de Inventario de Repuestos:** CRUD, búsqueda y control de stock automático al usarse en OTs.
- [x] **Gestión de Usuarios:** Creación de técnicos y administradores.
- [x] **Dashboard Resumen:** Tarjetas con métricas en tiempo real (Total Equipos, OTs Pendientes, En Mantenimiento).
- [x] **Autenticación de Usuarios (JWT).**
- [ ] Módulo de Mantenimiento Preventivo (Planificación).
- [ ] Módulo de Inteligencia Artificial (Sugerencias).
- [ ] Sistema de Configuración de Estados (Personalizable).
- [ ] Gestión Documental (Subida de PDFs/Manuales).

## Tecnologías Utilizadas

### Backend
*   **Lenguaje:** Python 3.10+
*   **Framework:** FastAPI
*   **ORM:** SQLModel (basado en SQLAlchemy y Pydantic)
*   **Base de Datos:** SQLite (ideal para prototipos y uso offline)
*   **Seguridad:** JWT (JSON Web Tokens) y Passlib (bcrypt)

### Frontend
*   **Framework:** Vue.js 3
*   **Empaquetador:** Vite
*   **Enrutamiento:** Vue Router
*   **Estilos:** CSS Scoped

## Estructura del Proyecto

```text
CMMS-BioAI/
├── backend/
│   ├── api/
│   │   └── routes/      # Endpoints (Equipos, Ordenes, Usuarios, etc.)
│   ├── models/          # Modelos de Base de Datos (Tablas)
│   ├── schemas/         # Esquemas de validación (Pydantic)
│   ├── main.py          # Punto de entrada de la API
│   └── database.py      # Configuración de SQLite
├── frontend/
│   ├── src/
│   │   ├── views/       # Vistas principales (Dashboard, Inventario)
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
pip install fastapi uvicorn sqlmodel python-jose[cryptography] passlib[bcrypt] python-multipart

# Iniciar el servidor
uvicorn main:app --reload
```
El backend correrá en `http://127.0.0.1:8000`.

### 2. Configuración del Frontend
Abre una nueva terminal en la carpeta `frontend`:

```bash
# Instalar dependencias
npm install

# Iniciar la aplicación web
npm run dev
```
El frontend correrá en `http://localhost:5173` (o puerto similar).

## Endpoints Principales (API)

La documentación interactiva completa está disponible en `http://127.0.0.1:8000/docs` (Swagger UI).

### Equipos (`/equipos`)
*   `GET /equipos/` - Lista todos los equipos.
*   `POST /equipos/` - Crea un nuevo equipo.
*   `PUT /equipos/{id}` - Actualiza un equipo.
*   `DELETE /equipos/{id}` - Elimina un equipo.
*   `GET /equipos/estados` - Obtiene la lista de estados disponibles.

### Órdenes de Trabajo (`/ordenes`)
*   `GET /ordenes/` - Lista todas las órdenes.
*   `POST /ordenes/` - Crea una nueva orden.
*   `GET /ordenes/{id}` - Obtiene detalles de una orden.
*   `PUT /ordenes/{id}` - Actualiza estado, acciones o repuestos.

### Inventario (`/repuestos`)
*   `GET /repuestos/` - Lista el inventario.
*   `POST /repuestos/` - Agrega un repuesto nuevo.

### Usuarios (`/users`)
*   `GET /users/` - Lista usuarios (para asignación de técnicos).

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

## Observaciones y Pendientes

### Observaciones Técnicas
*   **IDs de Estados:** Actualmente, los contadores del Dashboard (ej. "En Mantenimiento") funcionan buscando un `estado_id` fijo (ej. ID 2). Si el usuario personaliza los estados en la base de datos, debe asegurarse de que los IDs coincidan con la lógica del Frontend, o modificar los `computed` en `DashboardView.vue`.
*   **IDs de Base de Datos:** Los IDs de los equipos son automáticos. Si se elimina un equipo, ese ID no se reutiliza. Para un control de inventario normado, se recomienda usar el campo `numero_serie` o crear un campo `codigo_activo`.

### Pendientes (Roadmap)
1.  **Sistema de Configuración de Estados:**
    *   Permitir que el usuario cree, edite y asigne colores a los estados desde la interfaz.
    *   Hacer que los contadores del Dashboard sean dinámicos (buscando por nombre de estado, no por ID fijo).
2.  **Normalización de Equipos:**
    *   Analizar e implementar estándares internacionales (como UMDNS o GMDN) para el registro de equipos médicos.
3.  **Gestión Documental:**
    *   Módulo para subir y visualizar archivos PDF (manuales, garantías, registros sanitarios) asociados a los equipos.
4.  **Módulo Preventivo:**
    *   Programación automática de mantenimientos basados en fechas o contadores de uso.

## Autor

Desarrollado como parte del proyecto de Maestría en Ingeniería Biomédica.
```

---
