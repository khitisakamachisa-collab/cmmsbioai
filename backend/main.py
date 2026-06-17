from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import create_db_and_tables, seed_database
from models import Usuario, Equipo, EstadoEquipo, OrdenTrabajo, EstadoOT, EventoHistorial, DocumentoAdjunto, OtRepuestoUtilizado
from api.routes import estados, users, equipos, ordenes, auth, repuestos, preventivo, historial, reportes, documentos, herramientas, configuracion, proveedores
from config import get_dir

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: crear tablas si no existen
    create_db_and_tables()
    # Poblar tablas con datos iniciales (solo si están vacías)
    seed_database()
    yield
    # Shutdown: (se puede agregar lógica de cierre aquí si se necesita)

app = FastAPI(title="CMMS-BioAI Backend", lifespan=lifespan)

# Configurar CORS (Esto permite que Vue se conecte)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción pon el dominio exacto
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(estados.router)
app.include_router(users.router)
app.include_router(equipos.router)
app.include_router(ordenes.router)
app.include_router(auth.router)
app.include_router(repuestos.router)
app.include_router(preventivo.router)
app.include_router(historial.router)
app.include_router(reportes.router)
app.include_router(documentos.router)
app.include_router(herramientas.router)
app.include_router(configuracion.router)
app.include_router(proveedores.router)

# Servir archivos estaticos (documentos subidos) - usa config.py
uploads_dir = get_dir("uploads_base")
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

@app.get("/")
def root():
    return {"message": "Bienvenido al Backend de CMMS-BioAI"}