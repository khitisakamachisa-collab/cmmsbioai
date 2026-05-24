from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import create_db_and_tables, seed_database
from models import Usuario, Equipo, EstadoEquipo, OrdenTrabajo, EstadoOT
from api.routes import estados, users, equipos, ordenes, auth, repuestos, preventivo

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

@app.get("/")
def root():
    return {"message": "Bienvenido al Backend de CMMS-BioAI"}