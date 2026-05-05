from sqlmodel import SQLModel, create_engine, Session

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