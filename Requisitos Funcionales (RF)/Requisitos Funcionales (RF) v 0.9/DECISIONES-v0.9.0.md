# CMMS-BioAI — Decisiones de Diseño v0.9.0

> **Documento maestro de planificación.** Este archivo consolida todas las decisiones tomadas en las conversaciones entre el equipo de diseño, la IA de diseño y la IA de software, con el objetivo de tener una guía clara antes de programar.
>
> **Filosofía**: "Pensar mucho en el papel antes de hacer el código."

---

## 📑 Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Decisiones Confirmadas](#2-decisiones-confirmadas)
3. [RF01 — Gestión de Activos (Equipos Médicos) Actualizado](#3-rf01--gestión-de-activos-equipos-médicos-actualizado)
4. [RF11 — Gestión Detallada de Costos en OT](#4-rf11--gestión-detallada-de-costos-en-ot)
5. [RF12 — Gestión de Contratos de Mantenimiento y Servicios](#5-rf12--gestión-de-contratos-de-mantenimiento-y-servicios)
6. [Cambios Adicionales](#6-cambios-adicionales)
7. **[Observaciones Adicionales v0.9.0](#7-observaciones-adicionales-v090)** ← NUEVO
8. [Roadmap de Versiones](#8-roadmap-de-versiones)
9. [Plan de Ejecución por Versión](#9-plan-de-ejecución-por-versión)
10. [Preguntas Pendientes](#10-preguntas-pendientes)
11. [Opciones Futuras (post-v1.0)](#11-opciones-futuras-post-v10)

---

## 1. Resumen Ejecutivo

La versión v0.9.0 marca un **rediseño estratégico** del sistema CMMS-BioAI con los siguientes objetivos:

1. **Universalidad**: Eliminar el contexto Bolivia del núcleo del sistema para tener un CMMS universal.
2. **Limpieza del modelo de datos**: Eliminar campos obsoletos, agregar campos útiles, normalizar FKs.
3. **Mejor experiencia de usuario**: Formularios consistentes, filtros útiles, identificación clara de equipos.
4. **Visión integral de mantenimiento**: Unificar OT + MP en una vista "Planificación" con calendario.
5. **Trazabilidad financiera**: Gestión detallada de costos por OT (RF11) y contratos (RF12).
6. **Modo TEST**: Cargar datos de ejemplo con múltiples usuarios para probar el sistema.

### Estado actual del proyecto

| Aspecto | Estado |
|---------|--------|
| Versión actual en producción | v0.8.3 |
| Versión objetivo próxima | v0.9.0 (RF01 + Modo TEST + usuarios múltiples) |
| Porcentaje estimado hacia v1.0 | ~45-50% (con roadmap claro) |
| Filosofía | Pequeñas mejoras incrementales, versiones seguras |

---

## 2. Decisiones Confirmadas

### 2.1 Contexto del proyecto

| # | Decisión | Justificación |
|---|----------|---------------|
| 1 | **Versión universal primero**, sin contexto Bolivia | Luego versiones específicas: cliente final, proveedor (importador), fabricante |
| 2 | **Eliminar `registro_sanitario_bolivia`** del RF01 | No aplica en versión universal |
| 3 | **BD nueva desde cero** para v0.9 (sin migración compleja) | El usuario puede borrar la BD vieja y empezar limpio |
| 4 | **Plantillas Excel vacías** como guías para el usuario final | Solo encabezados y 1-2 filas de ejemplo |
| 5 | **Modo TEST** (no "demo") para datos de ejemplo | "demo" sugiere caducidad; "TEST" es más neutral |
| 6 | **Capa 2 mantiene sincronización de `imagen_ruta`** | Funcionalidad arreglada en v0.8.3 se preserva |
| 7 | **`fecha_inicio_garantia` / `fecha_fin_garantia`**: validación + badge visual, sin auto-cambio de estado | El estado operativo es independiente del estado de garantía |

### 2.2 RF01 — Gestión de Activos (Equipos)

| # | Decisión | Detalle |
|---|----------|---------|
| 8 | **Campos eliminados**: `registro_sanitario_bolivia`, `calibracion_proxima`, `responsable_tecnico_id` | Ver §3.2 |
| 9 | **Campos nuevos**: `observaciones`, `fecha_inicio_garantia`, `condicion_origen`, `proveedor_principal_id` (FK) | Ver §3.3 |
| 10 | **Cambios de obligatoriedad**: `nombre_corto` → NOT NULL, `fecha_adquisicion` → opcional | Ver §3.4 |
| 11 | **`descripcion` vs `observaciones`**: técnica vs operativas | Confirmado |
| 12 | **`condicion_origen`**: dropdown estricto con 9 valores | Compra, Donación, Préstamo, Demostración, Evaluación, Leasing, Renta, Comodato, Otro |
| 13 | **`proveedor_principal_id` (FK)**: dropdown con opción "Crear nuevo" | Si el proveedor no existe, se crea al vuelo |
| 14 | **Restricción eliminación equipos**: dura (verificar dependencias) | Ver §3.6 |
| 15 | **Campos no modificables**: `modelo`, `marca`, `numero_serie` | Advertencia ROJA en formularios |
| 16 | **Filtros Equipos**: `ubicacion_actual`, `estado_id`, `condicion_origen` | Búsqueda: nombre/marca/modelo + numero_serie/numero_material |
| 17 | **Eliminar filtro por `responsable_tecnico_id`** del frontend | Campo ya no existe |

### 2.3 RF11 — Costos en OT

| # | Decisión | Detalle |
|---|----------|---------|
| 18 | **RF11 aplica solo a OTs** | Cuando una MP genera una OT, los costos van a la OT |
| 19 | **Tabla `OtCostoAdicional`** con FK a `OrdenTrabajo` | Ver §4.3 |
| 20 | **`tipo_costo` como enum estricto** | Ver §4.4 |
| 21 | **Reutilizar `DocumentoAdjunto`** para justificativos | Nuevo campo `ot_costo_id` |
| 22 | **`.meta.json` de costos: NO por ahora** | El backup/restore JSON ya cubre la BD |

### 2.4 RF12 — Contratos

| # | Decisión | Detalle |
|---|----------|---------|
| 23 | **Tabla `Contrato`** + tabla intermedia **`ContratoEquipo`** (N:M) | No usar `grupo_equipos` como TEXT |
| 24 | **`activo` no se guarda**, se calcula en runtime | `fecha_inicio <= hoy <= fecha_fin` |
| 25 | **`periodicidad_costo` como enum** | Mensual, Trimestral, Semestral, Anual, Único |
| 26 | **`moneda` como dropdown estricto** | USD, EUR, BOB, MXN, ARS, CLP, COP, PEN, BRL, Otro |
| 27 | **`contrato_id` opcional en `OrdenTrabajo`** | Para marcar OTs como cubiertas por contrato |
| 28 | **Contratos NO generan MPs automáticamente en v0.9** | Pospuesto a v1.0 |

### 2.5 Cambios UX/UI

| # | Decisión | Detalle |
|---|----------|---------|
| 29 | **Opción C**: ORDENES + PREVENTIVO separadas + nueva página "Planificación" | Ver §6.1 |
| 30 | **Nombre de la nueva página**: "Planificación" | Calendario unificado OT + MP |
| 31 | **OTs**: dropdown muestra `nombre_corto + numero_serie + ubicacion_actual` | Diferenciar equipos con mismo nombre |
| 32 | **OTs**: mismo formulario en crear/editar, todos los campos editables | Consistencia UX |
| 33 | **Estados multi-dimensión pospuesto a v1.0** | Servirá para filtrado |

### 2.6 Modo TEST

| # | Decisión | Detalle |
|---|----------|---------|
| 34 | **"Cargar datos TEST"** en Configuración | Crea proveedores, equipos, repuestos, herramientas, OTs, MPs, contratos |
| 35 | **"Limpiar BD"** en Configuración | Borra todo excepto admin, catálogos y configuración |
| 36 | **Indicador "🟡 MODO TEST"** en el navbar | Para que el usuario sepa que está en modo prueba |

---

## 3. RF01 — Gestión de Activos (Equipos Médicos) Actualizado

### 3.1 Descripción

El sistema debe permitir registrar, editar, eliminar (con restricciones), consultar y gestionar la información detallada de los equipos médicos. Versión universal (sin contexto Bolivia).

### 3.2 Campos eliminados

| Campo | Justificación |
|-------|------------------------------|
| `registro_sanitario_bolivia` | Universalidad. Las normativas específicas se manejarán en versiones posteriores |
| `calibracion_proxima` | Se gestionará vía MP/OT unificadas (en análisis) |
| `responsable_tecnico_id` | La asignación de técnicos se hace en OT/MP (flexible, no atado al equipo) |

### 3.3 Campos nuevos

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `observaciones` | TEXT | No | Notas operativas / estado actual / accesorios |
| `fecha_inicio_garantia` | DATE | No | Fecha de inicio de la garantía |
| `condicion_origen` | TEXT (enum) | No | Dropdown estricto de 9 valores |
| `proveedor_principal_id` | INTEGER FK | No | Reemplaza `proveedor_principal` (texto libre) |

### 3.4 Cambios de obligatoriedad

| Campo | Antes | Ahora |
|-------|-------|-------|
| `nombre_corto` | Opcional | **NOT NULL** |
| `fecha_adquisicion` | Obligatorio | Opcional |

### 3.5 Modelo de datos final (RF01 v0.9.0)

```python
class Equipo(SQLModel, table=True):
    __tablename__ = "equipo"
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_corto: str                                    # NOT NULL
    modelo: str                                          # NOT NULL (no editable después)
    numero_serie: str = Field(unique=True, index=True)   # NOT NULL, unique (no editable)
    numero_material: Optional[str] = None
    marca: str                                           # NOT NULL (no editable después)
    fecha_adquisicion: Optional[date] = None             # Opcional
    fecha_inicio_garantia: Optional[date] = None         # NUEVO
    fecha_fin_garantia: Optional[date] = None
    ubicacion_actual: Optional[str] = None
    estado_id: Optional[int] = Field(default=None, foreign_key="estadoequipo.id")
    proveedor_principal_id: Optional[int] = Field(default=None, foreign_key="proveedor.id")
    condicion_origen: Optional[str] = None               # NUEVO (enum)
    descripcion: Optional[str] = None
    observaciones: Optional[str] = None                  # NUEVO
    imagen_ruta: Optional[str] = None
```

### 3.6 Restricciones de negocio

- **DELETE**: verificar dependencias (OTs, documentos, MP, historial, contratos)
- **Campos no modificables después de creado**: `modelo`, `marca`, `numero_serie` (advertencia ROJA)
- **Validación**: `fecha_inicio_garantia <= fecha_fin_garantia`

---

## 4. RF11 — Gestión Detallada de Costos en OT

### 4.1 Modelo de datos

```python
class OtCostoAdicional(SQLModel, table=True):
    __tablename__ = "otcostoadicional"
    id: Optional[int] = Field(default=None, primary_key=True)
    orden_trabajo_id: int = Field(foreign_key="ordentrabajo.id", index=True)
    tipo_costo: str                  # enum
    descripcion_costo: str
    monto_costo: float
    fecha_registro: Optional[date] = None
    subido_por: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.now)
```

Agregar a `DocumentoAdjunto`: `ot_costo_id: Optional[int]` (FK)

### 4.2 Enum `tipo_costo`

Transporte, Servicio Externo, Repuesto No Inventariado, Herramienta Renta, Honorarios/Mano de Obra, Insumos/Materiales, Viáticos, Otro

---

## 5. RF12 — Gestión de Contratos

### 5.1 Modelo de datos

```python
class Contrato(SQLModel, table=True):
    __tablename__ = "contrato"
    id: Optional[int] = Field(default=None, primary_key=True)
    proveedor_id: int = Field(foreign_key="proveedor.id", index=True)
    tipo_contrato: str              # enum
    fecha_inicio: date
    fecha_fin: date
    costo_total: Optional[float] = None
    costo_periodico: Optional[float] = None
    periodicidad_costo: str = "Único"
    moneda: str = "USD"
    cobertura_detalle: Optional[str] = None
    tiempo_respuesta: Optional[str] = None
    horario_servicio: Optional[str] = None
    notas: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.now)


class ContratoEquipo(SQLModel, table=True):
    __tablename__ = "contrato_equipo"
    contrato_id: int = Field(foreign_key="contrato.id", primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id", primary_key=True)
```

Agregar a `OrdenTrabajo`: `contrato_id: Optional[int]` (FK)

### 5.2 Enums

- **`tipo_contrato`**: Comodato, Mantenimiento Preventivo, Mantenimiento Correctivo, Leasing, Garantía Extendida, Soporte Técnico, Servicio Integral, Otro
- **`periodicidad_costo`**: Único, Mensual, Trimestral, Semestral, Anual
- **`moneda`**: USD, EUR, BOB, MXN, ARS, CLP, COP, PEN, BRL, Otro

---

## 6. Cambios Adicionales

### 6.1 Nueva página "Planificación" (calendario unificado)

- Vista calendario mensual/semanal/diaria
- Eventos: OTs (color según estado) + MPs (color según vencimiento)
- Filtros: Equipo, Ubicación, Responsable, Estado, Tipo (Todo/OT/MP), Rango fechas
- Click en evento → modal detalle

### 6.2 Modo TEST

- Botón "Cargar datos TEST" en Configuración
- Botón "Limpiar BD" (mantiene admin y catálogos)
- Indicador "🟡 MODO TEST" en navbar

### 6.3 Plantillas Excel vacías

- Encabezados + 1-2 filas de ejemplo (no datos demo completos)
- Datos demo completos se cargan vía Modo TEST

### 6.4 Cambios en OT (RF02)

- Dropdown de equipo: `nombre_corto + numero_serie + ubicacion_actual`
- Formulario consistente crear/editar
- Tab "Costos adicionales" (RF11)
- Dropdown `contrato_id` (RF12)

### 6.5 Menú lateral v0.9.0

```
Inicio
Equipos
Repuestos
Proveedores
Contratos          ← NUEVO (RF12)
Ordenes
Preventivo
Planificación      ← NUEVO (calendario unificado)
Historial
Reportes
Usuarios
?
⚙️
```

---

## 7. Observaciones Adicionales v0.9.0

> **Sección añadida tras identificar problemas reales en el uso del sistema.** Estas observaciones refinan las decisiones anteriores y agregan nuevas funcionalidades.

### 7.1 Problema del Calendario de MP — Separar "fecha programada" vs "frecuencia recordatorio"

#### Problema detectado

Cuando el administrador programa un MP para una fecha específica (ej: este lunes), **el MP no aparece en el calendario en esa fecha**. En su lugar, aparece 90 días después porque el sistema calcula automáticamente `proxima_fecha = ultima_fecha + frecuencia_dias`.

#### Comportamiento esperado

1. **El MP debe aparecer en el calendario en la fecha programada por el usuario** (no en la calculada)
2. **Los 90 días (frecuencia) son un recordatorio**, no la fecha del calendario
3. El recordatorio puede verse en HOME (dashboard): "MPs próximos a vencer en X días"
4. La IA puede usar ese dato para sugerencias

#### Solución técnica propuesta

**Modelo actual** (`TareaPreventiva` en v0.8.3):
```python
frecuencia_dias: int  # ej: 90
ultima_fecha: Optional[date]  # última ejecución
proxima_fecha: Optional[date]  # auto-calculada como ultima_fecha + frecuencia_dias
```

**Modelo propuesto** (v0.9.2 con Planificación):
```python
frecuencia_dias: int  # ej: 90 (solo recordatorio/sugerencia)
ultima_fecha: Optional[date]  # última ejecución real
proxima_fecha: Optional[date]  # fecha REAL programada por el usuario (no auto-calculada)
```

**Comportamiento**:
- Al crear/editar un MP: el usuario setea `proxima_fecha` directamente con un date picker
- Al completar un MP (generar OT y marcarla como completada):
  - `ultima_fecha = fecha de completado`
  - El sistema **sugiere** `proxima_fecha = ultima_fecha + frecuencia_dias`, pero el usuario puede modificarla
- En el calendario: mostrar `proxima_fecha` (la fecha REAL programada)
- En HOME: mostrar "MPs próximos" basado en `proxima_fecha` vs hoy, agrupados por:
  - 🔴 Vencidos (`proxima_fecha < hoy`)
  - 🟡 Próximos 7 días (`hoy <= proxima_fecha < hoy + 7`)
  - 🟢 Próximos 30 días (`hoy + 7 <= proxima_fecha < hoy + 30`)

#### Impacto

- **v0.9.0**: cambiar comportamiento del formulario MP para que `proxima_fecha` sea editable (no auto-calculada). Mostrar sugerencia pero permitir override.
- **v0.9.2**: con la página "Planificación", el calendario usará `proxima_fecha` para mostrar MPs
- **HOME (dashboard)**: agregar widget de "MPs próximos a vencer" usando `proxima_fecha`

#### Decisión

✅ **Confirmar**: separar `proxima_fecha` (fecha real programada) de `frecuencia_dias` (recordatorio).

### 7.2 Usuarios múltiples para Modo TEST

#### Necesidad

Para poder demostrar la funcionalidad de asignación de OTs/MPs a técnicos en el calendario de Planificación, necesitamos más de un usuario en el sistema.

#### Usuarios por defecto (cargados en `seed_database()`)

| Username | Password | Rol | Uso principal |
|----------|----------|-----|---------------|
| `admin` | `admin` | admin | Administrador del sistema (gestiona usuarios, configuración) |
| `tech` | `tech` | tecnico | Técnico biomédico (se le asignan OTs y MPs) |
| `user` | `user` | tecnico | Usuario regular (para demostrar que cualquier técnico puede tener asignaciones) |

#### Notas

- Las contraseñas simples (`admin`, `tech`, `user`) son intencionales para facilitar el TEST
- En producción, el administrador debe cambiarlas y crear usuarios con contraseñas seguras
- Las plantillas Excel de TEST deben hacer referencia a estos usernames (`tech` como técnico asignado en OTs y MPs)
- En modo TEST, las OTs se asignan a `tech` para demostrar la funcionalidad de asignación

#### Cambio en `database.py` → `seed_database()`

```python
# Usuarios TEST (además del admin actual)
usuarios_test = [
    ("admin", "admin", "admin", "Administrador del Sistema"),
    ("tech", "tech", "tecnico", "Técnico Biomédico"),
    ("user", "user", "tecnico", "Usuario Regular"),
]
for username, password, role, full_name in usuarios_test:
    if not session.exec(select(Usuario).where(Usuario.username == username)).first():
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        session.add(Usuario(
            username=username,
            email=f"{username}@test.local",
            hashed_password=hashed,
            full_name=full_name,
            role=role,
            is_active=True
        ))
```

#### Pregunta

**Q-AD1**: ¿Confirmas que cambiamos la contraseña del admin de `admin123` a `admin` para estandarizar?

#### Decisión

✅ **Confirmar**: 3 usuarios TEST: `admin/admin`, `tech/tech`, `user/user` (todos rol tecnico excepto admin).

### 7.3 Funcionalidad de Exportación de Registros

#### Necesidad

El usuario debe poder exportar registros del sistema para usarlos a su discreción (reportes externos, respaldos, auditorías, compartir información).

#### Casos de uso

1. **Exportar lista completa de equipos** (Excel) para inventario físico
2. **Exportar historial de un equipo específico** (PDF) para auditoría
3. **Exportar OTs seleccionadas** (Excel) para reuniones de gestión
4. **Exportar listado de usuarios** (Excel) para RRHH
5. **Exportar inventario de herramientas** (Excel) para control de taller

#### Modalidades de exportación

| Modalidad | Descripción | Ejemplo |
|-----------|-------------|---------|
| **Todos** | Exporta todos los registros de la entidad | "Exportar todos los equipos" |
| **Filtrados** | Exporta los registros que coinciden con los filtros actuales | "Exportar equipos con estado Operativo" |
| **Seleccionados** | Exporta solo los registros marcados con checkbox | "Exportar 5 equipos seleccionados" |
| **Individual** | Exporta el detalle completo de un registro | "Exportar historial del equipo E0001" |

#### Formatos soportados

| Formato | Uso principal | Implementación |
|---------|---------------|----------------|
| **Excel (.xlsx)** | Listados, datos tabulares | `openpyxl` (ya usado en plantillas) |
| **CSV (.csv)** | Intercambio con otros sistemas | `csv` de Python |
| **PDF (.pdf)** | Reportes formales, historiales | `reportlab` (librería nueva) |

#### Entidades exportables

| Entidad | Listado (Excel/CSV) | Detalle (PDF) |
|---------|---------------------|---------------|
| Equipos | ✅ | ✅ (con historial, OTs, documentos) |
| Repuestos | ✅ | ✅ (con OTs donde se usó) |
| Herramientas | ✅ | ✅ (con OTs donde se usó) |
| Proveedores | ✅ | ✅ (con contactos, contratos) |
| Contratos | ✅ | ✅ (con equipos cubiertos) |
| Órdenes de Trabajo | ✅ | ✅ (con costos, repuestos, documentos) |
| Tareas Preventivas | ✅ | ✅ (con OTs generadas) |
| Historial | ✅ | ✅ (filtrado por equipo) |
| Usuarios | ✅ | ❌ (no aplica) |

#### Implementación UI

En cada vista de listado:
- Botón **"📤 Exportar"** con dropdown:
  - "Todos (Excel)"
  - "Todos (CSV)"
  - "Filtrados (Excel)" — solo si hay filtros activos
  - "Seleccionados (Excel)" — solo si hay checkboxes marcados
- En modal de detalle individual:
  - Botón **"📄 Exportar detalle (PDF)"**

#### Nueva RF

Esto debería ser **RF13 — Exportación de Datos** (separado de RF06 Reporting porque tiene su propia lógica de selección y formatos).

#### Decisión

✅ **Confirmar**: crear RF13 — Exportación de Datos.
- v0.9.0: no implementar (foco en RF01 + Modo TEST)
- v0.9.3: implementar RF13 completo (todas las entidades, todos los formatos)
- v0.9.2: implementar parcialmente (export de listados Excel/CSV para Equipos, OTs, MPs)

### 7.4 Resumen de impactos en el roadmap

| Observación | Versión | Impacto |
|-------------|---------|---------|
| 7.1 Calendario MP (separar fecha programada vs frecuencia) | v0.9.0 (formulario) + v0.9.2 (calendario) | Cambio de modelo en `TareaPreventiva` |
| 7.2 Usuarios TEST (admin/tech/user) | v0.9.0 | Modificar `seed_database()` |
| 7.3 Exportación de registros (RF13) | v0.9.2 (parcial) + v0.9.3 (completo) | Nueva RF13 |

---

## 8. Roadmap de Versiones

| Versión | Foco principal | Estado |
|---------|---------------|--------|
| **v0.8.3** | Capa 2 mejorada (recuperación de imágenes y OTs) | ✅ Completada |
| **v0.9.0** | RF01 actualizado + Modo TEST + usuarios múltiples + formulario MP con fecha editable | 🔶 Planificada |
| **v0.9.1** | RF11 (Costos en OT) + mejoras OT (dropdowns, formularios consistentes) | 🔶 Planificada |
| **v0.9.2** | RF12 (Contratos) + nueva página "Planificación" (calendario) + export parcial | 🔶 Planificada |
| **v0.9.3** | RF13 (Exportación completa) + mejoras UX/UI + bug fixes | 🔶 Planificada |
| **v1.0.0** | Estados multi-dimensión + versión final universitaria | 🔶 Planificada |

---

## 9. Plan de Ejecución por Versión

### 9.1 v0.9.0 — RF01 + Modo TEST + Usuarios + MP formulario

**Fase 1 — Backend (modelo + BD)**
1. Actualizar `models/equipos.py` con nuevos campos, eliminar obsoletos
2. Actualizar `schemas/equipo.py`
3. Actualizar `database.py`:
   - `seed_database()`: agregar usuarios `tech` y `user`, estandarizar `admin/admin`
   - Crear `seed_test_data()` para Modo TEST
   - Crear `clear_all_data()` para Limpiar BD
4. Actualizar `models/preventivo.py`: hacer `proxima_fecha` editable (no auto-calculada)
5. Actualizar `utils/meta_json.py` → `build_equipo_meta()`

**Fase 2 — Backend (endpoints)**
6. Actualizar `api/routes/equipos.py` (CRUD + import-excel + plantilla)
7. Implementar `/equipos/from-proveedor-nombre` (crear proveedor al vuelo)
8. Implementar `/configuracion/cargar-test` y `/configuracion/limpiar-bd`
9. Actualizar `api/routes/preventivo.py` (no auto-calcular proxima_fecha)
10. Actualizar `api/routes/configuracion.py` (escaneo con nuevos campos)

**Fase 3 — Frontend**
11. Regenerar plantilla Excel de equipos (vacía con 1-2 filas)
12. Actualizar `EquiposView.vue` (formulario, filtros, badges)
13. Actualizar `ConfiguracionView.vue` (pestaña "Datos TEST")
14. Actualizar `Navbar.vue` (indicador MODO TEST)
15. Actualizar `PreventivoView.vue` (formulario con `proxima_fecha` editable)
16. Actualizar `HomeDashboard.vue` (widget "MPs próximos a vencer")
17. Actualizar `AyudaView.vue`

**Fase 4 — Documentación y verificación**
18. Actualizar `README.md`
19. Crear `INSTALAR-v0.9.0.md`
20. Probar Modo TEST con 3 usuarios
21. Probar formulario MP con fecha editable
22. Probar importación Excel con nueva plantilla

### 9.2 v0.9.1 — RF11 + Mejoras OT

1. Crear modelo `OtCostoAdicional`
2. Actualizar `DocumentoAdjunto` con `ot_costo_id`
3. Endpoints CRUD para `/ots/{id}/costos`
4. Eliminar campos `costo_adicional` y `costos_adicionales` de `OrdenTrabajo`
5. Actualizar `OrdenesView.vue`:
   - Tab "Costos adicionales"
   - Dropdown de equipo con `nombre_corto + numero_serie + ubicacion_actual`
   - Formulario consistente crear/editar
6. Actualizar reportes RF06
7. Actualizar `AyudaView.vue`

### 9.3 v0.9.2 — RF12 + Planificación + Export parcial

1. Crear modelos `Contrato` y `ContratoEquipo`
2. Actualizar `OrdenTrabajo` con `contrato_id`
3. Endpoints CRUD para `/contratos`
4. Crear `ContratosView.vue`
5. Agregar "Contratos" al menú y router
6. Actualizar `EquiposView.vue` (tab contratos)
7. Actualizar `ProveedoresView.vue` (tab contratos)
8. Actualizar `OrdenesView.vue` (dropdown contrato)
9. Crear `PlanificacionView.vue` (calendario unificado)
10. Instalar librería calendario (FullCalendar)
11. Implementar filtros del calendario
12. **Export parcial**: botones "Exportar Excel/CSV" en Equipos, OTs, MPs
13. Actualizar reportes RF06 (costos por contrato)
14. Actualizar `AyudaView.vue`

### 9.4 v0.9.3 — RF13 Export completa + UX

1. Implementar RF13 completo (todas las entidades, todos los formatos)
2. Export PDF con `reportlab`
3. Export individual (detalle de entidad en PDF)
4. Export seleccionados (checkbox en listados)
5. Bug fixes detectados en v0.9.0-v0.9.2
6. Mejoras de rendimiento
7. Refinamiento visual

### 9.5 v1.0.0 — Estados multi-dimensión + versión final

- Rediseño del sistema de estados
- Documentación completa
- Empaquetado para distribución
- Versión final para defensa universitaria

---

## 10. Preguntas Pendientes

### 10.1 RF11 — Costos

**P1**: ¿Confirmas la lista de `tipo_costo`?
- Transporte, Servicio Externo, Repuesto No Inventariado, Herramienta Renta, Honorarios/Mano de Obra, Insumos/Materiales, Viáticos, Otro

**P2**: ¿Confirmas reutilizar `DocumentoAdjunto` con nuevo campo `ot_costo_id`?

### 10.2 RF12 — Contratos

**P3**: ¿Confirmas tabla intermedia `ContratoEquipo` (N:M)?

**P4**: ¿Confirmas enums para `tipo_contrato`, `periodicidad_costo`, `moneda`?

**P5**: ¿Confirmas agregar `contrato_id` opcional a `OrdenTrabajo`?

### 10.3 Menú

**P6**: ¿"Contratos" después de "Proveedores" en el menú?

### 10.4 Roadmap

**P7**: ¿Confirmas división v0.9.0 / v0.9.1 / v0.9.2 / v0.9.3 / v1.0.0?

### 10.5 Modo TEST

**P8**: ¿Confirmas implementación del Modo TEST en v0.9.0?

### 10.6 Plantillas Excel

**P9**: ¿Confirmas que las plantillas pasan a estar vacías (1-2 filas ejemplo)?

### 10.7 Observaciones adicionales (§7)

**Q-AD1**: ¿Confirmas cambiar contraseña admin de `admin123` a `admin` para estandarizar con `tech/tech` y `user/user`?

**Q-AD2**: ¿Confirmas separar `proxima_fecha` (fecha real) de `frecuencia_dias` (recordatorio) en `TareaPreventiva`?

**Q-AD3**: ¿Confirmas RF13 — Exportación de Datos como nueva RF?

**Q-AD4**: ¿Confirmas 3 usuarios TEST: `admin/admin`, `tech/tech`, `user/user`?

---

## 11. Opciones Futuras (post-v1.0)

### 11.1 Estados multi-dimensión

| Dimensión | Campo | Valores posibles |
|-----------|-------|-----------------|
| Operativo | `estado_operativo_id` | Operativo, En Mantenimiento, En Reparación, Fuera de Servicio, Dado de Baja |
| Ubicación | `estado_ubicacion_id` | En Almacén, En Préstamo, En Transporte, En Uso |
| Garantía (derivado) | calculado | En Garantía, Vencida, Sin Garantía |
| Calibración (derivado de MP) | calculado | Al día, Pendiente, Vencida |
| Crítico | `es_critico` (bool) | Sí / No |

### 11.2 Contratos que generan MPs automáticamente

Flag `genera_mp_automatico: bool` en `Contrato`.

### 11.3 Edición de campos bloqueados en Equipo

Flujo "Editar campos bloqueados" con doble confirmación que actualice carpetas y `.meta.json`.

### 11.4 Drag & drop en calendario de Planificación

Reasignar fechas/técnicos arrastrando eventos.

### 11.5 Versiones con normativa específica

post-v1.0: cliente final Bolivia (DIMUTES), importador/proveedor Bolivia, fabricante.

### 11.6 App móvil para técnicos

PWA o nativa: ver OTs asignadas, marcar completadas, subir fotos, firmas.

### 11.7 Multi-idioma (i18n)

Español (por defecto), Inglés, Portugués.

### 11.8 Multi-sede con sincronización

Arquitectura para sincronizar datos entre sedes.

### 11.9 Rol "visualizador" (solo lectura)

Tercer rol además de admin/tecnico, con permisos restringidos (ver §7.2).

### 11.10 Sistema de permisos granular

Permisos por módulo (ej: "ver equipos", "editar equipos", "eliminar equipos", "ver costos", etc.).

---

## 📎 Anexos

### Anexo A: Archivos Excel generados

Junto a este documento, se generan los siguientes archivos Excel con la estructura detallada de cada RF:

- `RF01_Activos_Equipos_v0.9.xlsx` — Estructura actualizada del modelo Equipo
- `RF11_Costos_OT_v0.9.xlsx` — Estructura de la tabla `OtCostoAdicional`
- `RF12_Contratos_v0.9.xlsx` — Estructura de las tablas `Contrato` y `ContratoEquipo`

### Anexo B: Historial de versiones de este documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-06-20 | Creación inicial. Decisiones tomadas en conversaciones con IA de diseño y IA de software. |
| 1.1 | 2026-06-21 | Añadida §7 "Observaciones Adicionales v0.9.0" con: (a) problema del calendario MP, (b) usuarios múltiples TEST, (c) funcionalidad de exportación RF13. Actualizado roadmap y plan de ejecución. |

---

> **Nota final**: Este documento es un **living document**. A medida que avancemos en la implementación y descubramos nuevos detalles, se actualizará. La idea es mantenerlo como **single source of truth** para el desarrollo de v0.9.0 y versiones posteriores.

> **Siguiente paso**: Responder las preguntas pendientes (§10) y luego empezar la implementación de v0.9.0 siguiendo el plan de ejecución (§9.1).
