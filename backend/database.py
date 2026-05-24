from sqlmodel import SQLModel, create_engine, Session, select
from models.users import Usuario
from models.estados import EstadoEquipo
from models.ordenes import EstadoOT
import bcrypt

# Nombre del archivo de la base de datos local
sqlite_file_name = "cmms_bioai.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Configuración del motor de base de datos
# connect_args={"check_same_thread": False} es necesario solo para SQLite
engine = create_engine(sqlite_url, echo=True, connect_args={"check_same_thread": False})

def create_db_and_tables():
    """Crea las tablas en la base de datos si no existen."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Dependencia para obtener una sesión de base de datos en los endpoints."""
    with Session(engine) as session:
        yield session

def seed_database():
    """Poblar tablas con datos iniciales si están vacías."""
    with Session(engine) as session:

        # === 1. Seed: Usuario Admin por defecto ===
        admin_exists = session.exec(
            select(Usuario).where(Usuario.role == "admin")
        ).first()
        if not admin_exists:
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt()).decode()
            admin = Usuario(
                username="admin",
                email="admin@biolab.com",
                hashed_password=hashed,
                full_name="Administrador",
                role="admin",
                is_active=True
            )
            session.add(admin)
            print("✅ Seed: Usuario admin creado (admin / admin123)")

        # === 2. Seed: Estados de Equipo ===
        equipo_estado_count = session.exec(select(EstadoEquipo)).first()
        if not equipo_estado_count:
            estados_equipo = [
                EstadoEquipo(id=1, nombre_estado="Operativo", color="#27ae60"),
                EstadoEquipo(id=2, nombre_estado="En Mantenimiento", color="#f39c12"),
                EstadoEquipo(id=3, nombre_estado="Averiado (Pendiente Reparación)", color="#e74c3c"),
                EstadoEquipo(id=4, nombre_estado="Retirado/Dado de Baja", color="#7f8c8d"),
                EstadoEquipo(id=5, nombre_estado="En Reserva", color="#3498db"),
                EstadoEquipo(id=6, nombre_estado="En Tránsito", color="#9b59b6"),
            ]
            for estado in estados_equipo:
                session.add(estado)
            print("✅ Seed: 6 estados de equipo creados")

        # === 3. Seed: Estados de Orden de Trabajo ===
        ot_estado_count = session.exec(select(EstadoOT)).first()
        if not ot_estado_count:
            estados_ot = [
                EstadoOT(id=1, nombre_estado="Abierta", color="#3b82f6"),
                EstadoOT(id=2, nombre_estado="En Proceso", color="#f39c12"),
                EstadoOT(id=3, nombre_estado="Bloqueada (Esp. Repuestos)", color="#e67e22"),
                EstadoOT(id=4, nombre_estado="Completada", color="#27ae60"),
                EstadoOT(id=5, nombre_estado="Cancelada", color="#95a5a6"),
            ]
            for estado in estados_ot:
                session.add(estado)
            print("✅ Seed: 5 estados de orden de trabajo creados")

        session.commit()