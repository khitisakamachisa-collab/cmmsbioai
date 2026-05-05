4. Actualización del README.md
Tu README actual es muy académico y formal (perfecto para una tesis o proyecto final de maestría), pero está desactualizado respecto a lo que hemos construido en las últimas sesiones. Algunas rutas y módulos no coinciden con el código actual.

Aquí tienes una versión actualizada y profesional. Copia y reemplaza tu archivo README.md con esto:

CMMS-BioAI
Sistema de Gestión de Mantenimiento Asistido por Computadora (CMMS) desarrollado para el contexto boliviano. Diseñado para ser una solución asequible, offline-first y centrada en el usuario para la gestión de equipos médicos biomédicos.

Estado del Proyecto (Prototipo Funcional)
El sistema se encuentra en fase de desarrollo activo con un prototipo funcional que cubre las siguientes áreas:

 Gestión de Activos (Equipos Médicos).
 Gestión de Órdenes de Trabajo (Correctivo).
 Gestión de Inventario de Repuestos.
 Autenticación de Usuarios (JWT).
 Módulo de Mantenimiento Preventivo (Planificación).
 Módulo de Inteligencia Artificial (Sugerencias).
 Sincronización Multi-sede.
Tecnologías Utilizadas
Backend
Lenguaje: Python 3.10+
Framework: FastAPI
ORM: SQLModel (basado en SQLAlchemy y Pydantic)
Base de Datos: SQLite (ideal para prototipos y uso offline)
Seguridad: JWT (JSON Web Tokens) y Passlib (bcrypt)
Frontend
Framework: Vue.js 3
Empaquetador: Vite
Enrutamiento: Vue Router
Estilos: CSS Scoped
Estructura del Proyecto
CMMS-BioAI/├── backend/│   ├── api/│   │   └── routes/      # Endpoints (Equipos, Ordenes, Usuarios, etc.)│   ├── models/          # Modelos de Base de Datos (Tablas)│   ├── schemas/         # Esquemas de validación (Pydantic)│   ├── main.py          # Punto de entrada de la API│   └── database.py      # Configuración de SQLite├── frontend/│   ├── src/│   │   ├── views/       # Vistas principales (Dashboard, Inventario)│   │   ├── services/    # Conexión con la API (api.js)│   │   └── router/      # Definición de rutas│   └── package.json└── README.md
Instalación y Ejecución Local
Requisitos Previos
Python 3 instalado.
Node.js y npm instalados.
1. Configuración del Backend
Abre una terminal en la carpeta backend:

bash

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
El backend correrá en http://127.0.0.1:8000.

2. Configuración del Frontend
Abre una nueva terminal en la carpeta frontend:

bash

# Instalar dependencias
npm install

# Iniciar la aplicación web
npm run dev
El frontend correrá en http://localhost:5173 (o puerto similar).

Endpoints Principales (API)
La documentación interactiva completa está disponible en http://127.0.0.1:8000/docs (Swagger UI).

Equipos (/equipos)
GET /equipos/ - Lista todos los equipos.
POST /equipos/ - Crea un nuevo equipo.
PUT /equipos/{id} - Actualiza un equipo.
DELETE /equipos/{id} - Elimina un equipo.
GET /equipos/estados - Obtiene la lista de estados disponibles (Operativo, Mantenimiento, etc.).
Órdenes de Trabajo (/ordenes)
GET /ordenes/ - Lista todas las órdenes.
POST /ordenes/ - Crea una nueva orden (ticket de servicio).
PUT /ordenes/{id} - Actualiza el estado o detalles de la orden.
Inventario (/repuestos)
GET /repuestos/ - Lista el inventario.
POST /repuestos/ - Agrega un repuesto nuevo.
Autenticación
POST /token - Inicio de sesión (genera JWT).
Base de Datos
Se utiliza SQLite. El archivo database.db se genera automáticamente en la carpeta backend al ejecutar el servidor por primera vez.

Para visualizar y editar datos manualmente, se recomienda usar DB Browser for SQLite.

Autor
Desarrollado como parte del proyecto de Maestría en Ingeniería Biomédica.