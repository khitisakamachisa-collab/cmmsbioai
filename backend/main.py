from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware # <--- 1. Importar esto
from database import create_db_and_tables
from models import Usuario, Equipo, EstadoEquipo, OrdenTrabajo, EstadoOT
#from api.routes import estados, users, equipos, ordenes, auth
from api.routes import estados, users, equipos, ordenes, auth, repuestos # Agregar repuestos

app = FastAPI(title="CMMS-BioAI Backend")

# 2. Configurar CORS (Esto permite que Vue se conecte)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción pon el dominio exacto, pero "*" permite todo por ahora
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ... el resto del código sigue igual ...
app.include_router(estados.router)
app.include_router(users.router)
app.include_router(equipos.router)
app.include_router(ordenes.router)
app.include_router(auth.router)
app.include_router(repuestos.router) # <--- Agregar esto

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def root():
    return {"message": "Bienvenido al Backend de CMMS-BioAI"}