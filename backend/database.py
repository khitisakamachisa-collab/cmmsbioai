from sqlmodel import SQLModel, create_engine, Session, select, text
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


# ============================================================
# MIGRACIONES (para bases de datos existentes que se actualizan a v0.9.0)
# ============================================================

def _migrate_repuesto_columns():
    """Agrega columnas nuevas a la tabla 'repuesto' si no existen (SQLite ALTER TABLE)."""
    new_columns = [
        ("numero_serie", "VARCHAR"),
        ("especificaciones_tecnicas", "VARCHAR"),
        ("proveedor_ultimo", "VARCHAR"),
        ("fecha_ultima_entrada", "DATE"),
        ("precio_referencia", "FLOAT"),
    ]
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(repuesto)"))
        existing = {row[1] for row in result.fetchall()}
        for col_name, col_type in new_columns:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE repuesto ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Migración: columna '{col_name}' agregada a tabla 'repuesto'")
        conn.commit()


def _migrate_documento_herramienta_id():
    """Agrega columna herramienta_id a la tabla 'documentoadjunto' si no existe."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(documentoadjunto)"))
        existing = {row[1] for row in result.fetchall()}
        if "herramienta_id" not in existing:
            conn.execute(text("ALTER TABLE documentoadjunto ADD COLUMN herramienta_id INTEGER REFERENCES herramienta(id)"))
            print("✅ Migración: columna 'herramienta_id' agregada a tabla 'documentoadjunto'")
        conn.commit()


def _migrate_proveedor_ciudad():
    """Agrega columna 'ciudad' a la tabla 'proveedor' si no existe (RF10)."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(proveedor)"))
        existing = {row[1] for row in result.fetchall()}
        if "ciudad" not in existing:
            conn.execute(text("ALTER TABLE proveedor ADD COLUMN ciudad VARCHAR"))
            print("✅ Migración: columna 'ciudad' agregada a tabla 'proveedor'")
        conn.commit()


def _migrate_equipo_v090():
    """
    Migra la tabla 'equipo' al esquema v0.9.0:
    - Agrega columnas nuevas: observaciones, fecha_inicio_garantia, condicion_origen, proveedor_principal_id
    - NO elimina columnas obsoletas (SQLite no soporta DROP COLUMN fácilmente).
    """
    new_columns = [
        ("observaciones", "VARCHAR"),
        ("fecha_inicio_garantia", "DATE"),
        ("condicion_origen", "VARCHAR"),
        ("proveedor_principal_id", "INTEGER REFERENCES proveedor(id)"),
    ]
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(equipo)"))
        existing = {row[1] for row in result.fetchall()}
        for col_name, col_type in new_columns:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE equipo ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Migración v0.9.0: columna '{col_name}' agregada a tabla 'equipo'")
        conn.commit()


def _migrate_documento_ot_costo_id():
    """v0.9.1: Agrega columna 'ot_costo_id' a la tabla 'documentoadjunto' para RF11."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(documentoadjunto)"))
        existing = {row[1] for row in result.fetchall()}
        if "ot_costo_id" not in existing:
            conn.execute(text("ALTER TABLE documentoadjunto ADD COLUMN ot_costo_id INTEGER REFERENCES otcostoadicional(id)"))
            print("✅ Migración v0.9.1: columna 'ot_costo_id' agregada a tabla 'documentoadjunto'")
        conn.commit()


def create_db_and_tables():
    """Crea las tablas en la base de datos si no existen, y aplica migraciones."""
    SQLModel.metadata.create_all(engine)
    _migrate_repuesto_columns()
    _migrate_documento_herramienta_id()
    _migrate_proveedor_ciudad()
    _migrate_equipo_v090()
    _migrate_documento_ot_costo_id()


def get_session():
    """Dependencia para obtener una sesión de base de datos en los endpoints."""
    with Session(engine) as session:
        yield session


# ============================================================
# SEED DE DATOS INICIALES
# ============================================================

def seed_database():
    """
    Poblar tablas con datos iniciales si están vacías.

    Crea:
    - 3 usuarios TEST: admin/admin, tech/tech, user/user
    - 19 estados de equipo (catálogo biomédico)
    - 5 estados de orden de trabajo
    """
    with Session(engine) as session:

        # === 1. Seed: Usuarios por defecto (admin, tech, user) ===
        # Contraseñas simples intencionalmente para facilitar el TEST.
        # En producción, el administrador debe cambiarlas.
        usuarios_seed = [
            ("admin", "admin", "admin",   "Administrador del Sistema", "admin@biolab.com"),
            ("tech",  "tech",  "tecnico", "Técnico Biomédico",         "tech@biolab.com"),
            ("user",  "user",  "tecnico", "Usuario Regular",           "user@biolab.com"),
        ]
        for username, password, role, full_name, email in usuarios_seed:
            existe = session.exec(
                select(Usuario).where(Usuario.username == username)
            ).first()
            if not existe:
                hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
                usuario = Usuario(
                    username=username,
                    email=email,
                    hashed_password=hashed,
                    full_name=full_name,
                    role=role,
                    is_active=True
                )
                session.add(usuario)
                print(f"✅ Seed: Usuario '{username}' creado ({username} / {password})")

        # === 2. Seed: Estados de Equipo (19 estados biomédicos) ===
        equipo_estado_count = session.exec(select(EstadoEquipo)).first()
        if not equipo_estado_count:
            estados_equipo = [
                EstadoEquipo(id=1,  nombre_estado="Operativo",              color="#27ae60"),
                EstadoEquipo(id=2,  nombre_estado="En mantenimiento",       color="#f39c12"),
                EstadoEquipo(id=3,  nombre_estado="En reparación",          color="#e74c3c"),
                EstadoEquipo(id=4,  nombre_estado="Fuera de servicio",      color="#7f8c8d"),
                EstadoEquipo(id=5,  nombre_estado="En espera/Standby",     color="#3498db"),
                EstadoEquipo(id=6,  nombre_estado="En calibración",        color="#9b59b6"),
                EstadoEquipo(id=7,  nombre_estado="En inspección",         color="#1abc9c"),
                EstadoEquipo(id=8,  nombre_estado="Esp. Repuesto",         color="#e67e22"),
                EstadoEquipo(id=9,  nombre_estado="Bloqueado/LOTO",        color="#c0392b"),
                EstadoEquipo(id=10, nombre_estado="En almacén",            color="#95a5a6"),
                EstadoEquipo(id=11, nombre_estado="Almacén repuestos",     color="#795548"),
                EstadoEquipo(id=12, nombre_estado="Retirado/Baja",         color="#636e72"),
                EstadoEquipo(id=13, nombre_estado="En transporte",         color="#0984e3"),
                EstadoEquipo(id=14, nombre_estado="En préstamo",           color="#6c5ce7"),
                EstadoEquipo(id=15, nombre_estado="En certificación",      color="#00b894"),
                EstadoEquipo(id=16, nombre_estado="En modificación",       color="#fdcb6e"),
                EstadoEquipo(id=17, nombre_estado="Condición crítica",     color="#d63031"),
                EstadoEquipo(id=18, nombre_estado="Degradado",             color="#e17055"),
                EstadoEquipo(id=19, nombre_estado="En monitoreo",          color="#00cec9"),
            ]
            for estado in estados_equipo:
                session.add(estado)
            print("✅ Seed: 19 estados de equipo creados")

        # === 3. Seed: Estados de Orden de Trabajo ===
        ot_estado_count = session.exec(select(EstadoOT)).first()
        if not ot_estado_count:
            estados_ot = [
                EstadoOT(id=1, nombre_estado="Abierta", color="#3b82f6"),
                EstadoOT(id=2, nombre_estado="En Proceso", color="#f39c12"),
                EstadoOT(id=3, nombre_estado="Esp. Repuesto", color="#e67e22"),
                EstadoOT(id=4, nombre_estado="Completada", color="#27ae60"),
                EstadoOT(id=5, nombre_estado="Cancelada", color="#95a5a6"),
            ]
            for estado in estados_ot:
                session.add(estado)
            print("✅ Seed: 5 estados de orden de trabajo creados (con 'Esp. Repuesto')")

        session.commit()
