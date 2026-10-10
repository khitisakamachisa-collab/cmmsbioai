from datetime import datetime

from sqlmodel import SQLModel, create_engine, Session, select, text
from models.users import Usuario
from models.estados import EstadoEquipo
from models.ordenes import EstadoOT, OrdenTrabajo, BitacoraOT
import bcrypt

# Nombre del archivo de la base de datos local
sqlite_file_name = "cmms_bioai.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# Configuración del motor de base de datos
# connect_args={"check_same_thread": False} es necesario solo para SQLite
engine = create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})


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
      Las columnas registro_sanitario_bolivia, calibracion_proxima, responsable_tecnico_id,
      proveedor_principal se quedan en la tabla pero SQLModel las ignora.
    - Migración de datos: proveedor_principal (texto) → proveedor_principal_id (FK)
      No se hace aquí automáticamente porque requiere buscar/crear proveedores.
      Se hace vía endpoint /configuracion/migrar-proveedores (a implementar en Fase 2).
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


def _migrate_equipo_ia():
    """v1.0.0 (RF07): agrega tipo_equipo y criticidad a la tabla 'equipo'.
    Campos requeridos por el módulo predictivo (tesis): tipo_equipo identifica
    las bombas de infusión; criticidad es feature del modelo RUL."""
    new_columns = [
        ("tipo_equipo", "VARCHAR DEFAULT 'Otro'"),
        ("criticidad", "VARCHAR DEFAULT 'Media'"),
    ]
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(equipo)"))
        existing = {row[1] for row in result.fetchall()}
        for col_name, col_type in new_columns:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE equipo ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Migración v1.0.0: columna '{col_name}' agregada a tabla 'equipo' (RF07)")
        conn.commit()


def _migrate_ordentrabajo_v110():
    """v1.1.0 (Flujo de Trabajo OT): agrega sellos de tiempo a 'ordentrabajo'
    (Regla R5: primera escritura inmutable). La tabla bitacora_ot se crea sola
    con SQLModel.metadata.create_all()."""
    new_columns = [
        ("fecha_asignacion", "DATETIME"),
        ("fecha_inicio_trabajo", "DATETIME"),
        ("fecha_resolucion", "DATETIME"),
    ]
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(ordentrabajo)"))
        existing = {row[1] for row in result.fetchall()}
        for col_name, col_type in new_columns:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE ordentrabajo ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Migración v1.1.0: columna '{col_name}' agregada a tabla 'ordentrabajo'")
        conn.commit()


def _migrate_ordentrabajo_v21():
    """v2.1 (Dataset de Prueba / Rediseño de flujos):
    Agrega 15 columnas a 'ordentrabajo' sin borrar ni modificar las existentes.
    Defaults seguros: filas previas quedan como tipo_origen_ot='Usuario',
    tipo_impacto='REAL', sin pausas ni exclusiones de métricas.
    Las tablas symptoms / feedback_predictivo / hitos_ciclo_vida se crean solas
    con SQLModel.metadata.create_all() (models/v21.py)."""
    new_columns = [
        ("tipo_origen_ot", "VARCHAR DEFAULT 'Usuario'"),
        ("tipo_impacto", "VARCHAR DEFAULT 'REAL'"),
        ("sub_estado_logistica", "VARCHAR"),
        ("ventana_garantia_reparacion", "BOOLEAN DEFAULT 0"),
        ("es_reparacion_inefectiva", "BOOLEAN DEFAULT 0"),
        ("en_pausa_tecnica", "BOOLEAN DEFAULT 0"),
        ("motivo_pausa", "VARCHAR"),
        ("tiempo_pausa_acumulado", "FLOAT DEFAULT 0.0"),
        ("cierre_administrativo", "BOOLEAN DEFAULT 0"),
        ("excluida_de_MTTR", "BOOLEAN DEFAULT 0"),
        ("mdt_excluido_disponibilidad", "BOOLEAN DEFAULT 0"),
        ("codigo_falla", "VARCHAR"),
        ("causa_raiz", "VARCHAR"),
        ("accion_tomada", "VARCHAR"),
        ("motivo_cancelacion", "VARCHAR"),
    ]
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(ordentrabajo)"))
        existing = {row[1] for row in result.fetchall()}
        for col_name, col_type in new_columns:
            if col_name not in existing:
                conn.execute(text(f"ALTER TABLE ordentrabajo ADD COLUMN {col_name} {col_type}"))
                print(f"✅ Migración v2.1: columna '{col_name}' agregada a tabla 'ordentrabajo'")
        conn.commit()


def _migrate_ordentrabajo_v111():
    """v1.1.1 (Cierre Definitivo y Reincidencias):
    - Agrega parent_ot_id y failure_sequence a 'ordentrabajo' (cadena de
      reincidencias; la OT cerrada es inmutable y cada re-intervención es
      una OT nueva vinculada).
    NOTA v2.1.3: el estado de OT 'En Monitoreo' que v1.1.1 sembraba aquí
    al lado fue ELIMINADO del catálogo; su migración de datos vive en
    _migrate_eliminar_en_monitoreo() (ver abajo)."""
    with engine.connect() as conn:
        result = conn.execute(text("PRAGMA table_info(ordentrabajo)"))
        existing = {row[1] for row in result.fetchall()}
        if "parent_ot_id" not in existing:
            conn.execute(text("ALTER TABLE ordentrabajo ADD COLUMN parent_ot_id INTEGER REFERENCES ordentrabajo(id)"))
            print("✅ Migración v1.1.1: columna 'parent_ot_id' agregada a tabla 'ordentrabajo'")
        if "failure_sequence" not in existing:
            conn.execute(text("ALTER TABLE ordentrabajo ADD COLUMN failure_sequence INTEGER DEFAULT 1"))
            print("✅ Migración v1.1.1: columna 'failure_sequence' agregada a tabla 'ordentrabajo' (OTs existentes = 1)")
        conn.commit()


def create_db_and_tables():
    """Crea las tablas en la base de datos si no existen, y aplica migraciones."""
    SQLModel.metadata.create_all(engine)
    _migrate_repuesto_columns()
    _migrate_documento_herramienta_id()
    _migrate_proveedor_ciudad()
    _migrate_equipo_v090()
    _migrate_proveedor_ultimo_id()  # v0.9.14
    _migrate_equipo_ia()            # v1.0.0 — RF07 Módulo Predictivo (tipo_equipo + criticidad)
    _migrate_ordentrabajo_v110()    # v1.1.0 — Flujo OT (sellos de tiempo R5)
    _migrate_ordentrabajo_v111()    # v1.1.1 — Reincidencias (parent_ot_id, failure_sequence)
    _migrate_ordentrabajo_v21()     # v2.1 — Dataset de prueba (15 campos nuevos de flujo/métricas)
    _migrate_eliminar_en_monitoreo()  # v2.1.3 — deprecación del estado de OT 'En Monitoreo'
    # v0.9.23: hora_creacion fue eliminada. fecha_creacion (DATETIME) se usa como campo editable.
    # Si la columna hora_creacion existe en BD anterior, se ignora (SQLModel no la lee si no está en el modelo).


def _migrate_eliminar_en_monitoreo():
    """v2.1.3 (Refactorización de estados): deprecación del estado de OT
    'En Monitoreo' (introducido en v1.1.1).

    Motivo: no reflejaba la operación real (las intervenciones rápidas se
    cierran como 'Completada') y generaba inconsistencias en métricas y
    KPIs (el calendario/ventana y los conteos lo trataban de forma
    divergente a los demás estados activos).

    Acciones (IDEMPOTENTE: si el estado no existe, no hace nada y puede
    correrse cualquier cantidad de veces):
      1. Toda OrdenTrabajo en 'En Monitoreo' pasa a 'Completada'
         (cierre automático). Se fija fecha_resolucion (sello R5) solo
         si no tenía, y se cierra una pausa técnica abierta si quedara.
      2. Cada OT migrada recibe bitácora accion='cierre_automatico' con
         usuario='sistema'. El historial previo NO se toca ni se borra.
      3. El estado se elimina del catálogo estadoot (6 → 5 estados).

    IMPORTANTE: el estado de EQUIPO 'En Monitoreo' (tabla estadoequipo,
    equipo con sensores IoT activos) es un concepto DISTINTO y sigue
    vigente — esta migración no lo toca."""
    with Session(engine) as session:
        est_mon = session.exec(
            select(EstadoOT).where(EstadoOT.nombre_estado == "En Monitoreo")).first()
        if not est_mon:
            return  # BD nueva o ya migrada → idempotente
        est_comp = session.exec(
            select(EstadoOT).where(EstadoOT.nombre_estado == "Completada")).first()
        if not est_comp:
            print("⚠ Migración v2.1.3: el catálogo no tiene 'Completada'; "
                  "no se migran OTs ni se elimina 'En Monitoreo'.")
            return
        ots = session.exec(
            select(OrdenTrabajo).where(OrdenTrabajo.estado_id == est_mon.id)).all()
        for ot in ots:
            ot.estado_id = est_comp.id
            if ot.fecha_resolucion is None:
                ot.fecha_resolucion = datetime.now()   # sello R5 del cierre automático
            if ot.en_pausa_tecnica:
                ot.en_pausa_tecnica = False            # una OT cerrada no queda en pausa
            session.add(ot)
            session.add(BitacoraOT(
                orden_trabajo_id=ot.id,
                accion="cierre_automatico",
                usuario="sistema",
                estado_anterior=est_mon.nombre_estado,
                estado_nuevo=est_comp.nombre_estado,
                comentario=("Migración v2.1.3: Estado 'En Monitoreo' deprecado. "
                            "OT cerrada automáticamente."),
            ))
        session.delete(est_mon)
        session.commit()
        if ots:
            print(f"✅ Migración v2.1.3: {len(ots)} OT(s) 'En Monitoreo' → 'Completada' "
                  f"(ids: {sorted(o.id for o in ots)}) con bitácora 'cierre_automatico'")
        print("✅ Migración v2.1.3: estado de OT 'En Monitoreo' eliminado del catálogo "
              "(5 estados). El estado de EQUIPO 'En Monitoreo' NO se toca.")


def _migrate_proveedor_ultimo_id():
    """v0.9.14: Agrega columna proveedor_ultimo_id a 'repuesto' y 'herramienta'."""
    with engine.connect() as conn:
        # Repuesto
        result = conn.execute(text("PRAGMA table_info(repuesto)"))
        existing = {row[1] for row in result.fetchall()}
        if "proveedor_ultimo_id" not in existing:
            conn.execute(text("ALTER TABLE repuesto ADD COLUMN proveedor_ultimo_id INTEGER REFERENCES proveedor(id)"))
            print("✅ Migración v0.9.14: columna 'proveedor_ultimo_id' agregada a tabla 'repuesto'")
        # Herramienta
        result = conn.execute(text("PRAGMA table_info(herramienta)"))
        existing = {row[1] for row in result.fetchall()}
        if "proveedor_ultimo_id" not in existing:
            conn.execute(text("ALTER TABLE herramienta ADD COLUMN proveedor_ultimo_id INTEGER REFERENCES proveedor(id)"))
            print("✅ Migración v0.9.14: columna 'proveedor_ultimo_id' agregada a tabla 'herramienta'")
        conn.commit()


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
    - 11 estados de equipo (catálogo biomédico)
    - 5 estados base de OT (v2.1.3: 'En Monitoreo' eliminado del catálogo)
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

        # === 2. Seed: Estados de Equipo (11 estados biomédicos) ===
        equipo_estado_count = session.exec(select(EstadoEquipo)).first()
        if not equipo_estado_count:
            estados_equipo = [
                EstadoEquipo(id=1,  nombre_estado="Operativo",              color="#27ae60"),
                EstadoEquipo(id=2,  nombre_estado="En mantenimiento",       color="#f39c12"),
                EstadoEquipo(id=3,  nombre_estado="En reparación",          color="#e74c3c"),
                EstadoEquipo(id=4,  nombre_estado="Fuera de servicio",      color="#7f8c8d"),
                EstadoEquipo(id=5,  nombre_estado="En calibración",         color="#9b59b6"),
                EstadoEquipo(id=6,  nombre_estado="En inspección",          color="#1abc9c"),
                EstadoEquipo(id=7,  nombre_estado="Esp. Repuesto",          color="#e67e22"),
                EstadoEquipo(id=8,  nombre_estado="Esp. atención técnica",  color="#c0392b"),
                EstadoEquipo(id=9,  nombre_estado="Retirado/Baja",          color="#636e72"),
                EstadoEquipo(id=10, nombre_estado="En Monitoreo",           color="#00cec9"),
                EstadoEquipo(id=11, nombre_estado="Otro",                   color="#95a5a6"),
            ]
            for estado in estados_equipo:
                session.add(estado)
            print("✅ Seed: 11 estados de equipo creados")

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
            print("✅ Seed: 5 estados base de OT creados (v2.1.3 — sin 'En Monitoreo')")

        session.commit()
