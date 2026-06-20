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
7. [Roadmap de Versiones](#7-roadmap-de-versiones)
8. [Plan de Ejecución por Versión](#8-plan-de-ejecución-por-versión)
9. [Preguntas Pendientes](#9-preguntas-pendientes)
10. [Opciones Futuras (post-v1.0)](#10-opciones-futuras-post-v10)

---

## 1. Resumen Ejecutivo

La versión v0.9.0 marca un **rediseño estratégico** del sistema CMMS-BioAI con los siguientes objetivos:

1. **Universalidad**: Eliminar el contexto Bolivia del núcleo del sistema para tener un CMMS universal. Las normativas específicas (Bolivia cliente final, Bolivia importador/proveedor, fabricante) se manejarán en versiones posteriores.
2. **Limpieza del modelo de datos**: Eliminar campos obsoletos o redundantes, agregar campos útiles, normalizar FKs.
3. **Mejor experiencia de usuario**: Formularios consistentes, filtros útiles, identificación clara de equipos.
4. **Visión integral de mantenimiento**: Unificar OT + MP en una vista "Planificación" con calendario.
5. **Trazabilidad financiera**: Gestión detallada de costos por OT (RF11) y contratos (RF12).
6. **Modo TEST**: Cargar datos de ejemplo para probar el sistema sin tener que crear todo a mano.

### Estado actual del proyecto

| Aspecto | Estado |
|---------|--------|
| Versión actual en producción | v0.8.3 |
| Versión objetivo próxima | v0.9.0 (RF01 + Modo TEST) |
| Porcentaje estimado hacia v1.0 | ~45-50% (con roadmap claro) |
| Filosofía | Pequeñas mejoras incrementales, versiones seguras |

> **Nota sobre el porcentaje**: Con el rediseño, retrocedemos en porcentaje pero avanzamos en claridad. Cada decisión planificada nos acerca más rápido a v1.0.

---

## 2. Decisiones Confirmadas

### 2.1 Contexto del proyecto

| # | Decisión | Justificación |
|---|----------|---------------|
| 1 | **Versión universal primero**, sin contexto Bolivia | Luego haremos versiones específicas: cliente final, proveedor (importador), fabricante — cada una con su normativa |
| 2 | **Eliminar `registro_sanitario_bolivia`** del RF01 | No aplica en versión universal |
| 3 | **BD nueva desde cero** para v0.9 (sin migración compleja) | El usuario puede borrar la BD vieja y empezar limpio. Para preservar datos: backup JSON (Capa 3) + restore en v0.9 |
| 4 | **Plantillas Excel vacías** como guías para el usuario final | Las plantillas ya no tendrán datos demo, solo encabezados y 1-2 filas de ejemplo, para que el usuario las llene con su información |
| 5 | **Modo TEST** (no "demo") para datos de ejemplo | El término "demo" sugiere caducidad de licencia. "TEST" es más neutral |
| 6 | **Capa 2 mantiene sincronización de `imagen_ruta`** | Funcionalidad arreglada en v0.8.3 se preserva |
| 7 | **`fecha_inicio_garantia` / `fecha_fin_garantia`**: validación + badge visual, sin auto-cambio de estado | El estado operativo del equipo es independiente del estado de garantía |

### 2.2 RF01 — Gestión de Activos (Equipos)

| # | Decisión | Detalle |
|---|----------|---------|
| 8 | **Campos eliminados**: `registro_sanitario_bolivia`, `calibracion_proxima`, `responsable_tecnico_id` | Ver §3.2 para justificación |
| 9 | **Campos nuevos**: `observaciones`, `fecha_inicio_garantia`, `condicion_origen`, `proveedor_principal_id` (FK) | Ver §3.3 |
| 10 | **Cambios de obligatoriedad**: `nombre_corto` → NOT NULL, `fecha_adquisicion` → opcional | Ver §3.4 |
| 11 | **`descripcion` vs `observaciones`**: descripción = técnica (¿qué es?), observaciones = operativas (¿cómo está?) | Confirmado |
| 12 | **`condicion_origen`**: dropdown estricto con 9 valores | Compra, Donación, Préstamo, Demostración, Evaluación, Leasing, Renta, Comodato, Otro |
| 13 | **`proveedor_principal_id` (FK)**: dropdown con opción "Crear nuevo" | Si el proveedor no existe, se crea al vuelo con solo `nombre_empresa` |
| 14 | **Restricción eliminación equipos**: dura (rechazar si tiene OTs, documentos, MP, historial) | Ver §3.6 |
| 15 | **Campos no modificables** después de creado: `modelo`, `marca`, `numero_serie` | Advertencia ROJA en formularios. Evita inconsistencias en carpetas y `.meta.json` |
| 16 | **Filtros Equipos**: `ubicacion_actual`, `estado_id`, `condicion_origen` | Búsqueda: nombre/marca/modelo + numero_serie/numero_material |
| 17 | **Eliminar filtro por `responsable_tecnico_id`** del frontend | Campo ya no existe |

### 2.3 RF11 — Costos en OT

| # | Decisión | Detalle |
|---|----------|---------|
| 18 | **RF11 aplica solo a OTs** (no a MP directo) | Cuando una MP genera una OT, los costos van a la OT |
| 19 | **Tabla `OtCostoAdicional`** con FK a `OrdenTrabajo` | Ver §4.3 |
| 20 | **`tipo_costo` como enum estricto** (dropdown) | Ver §4.4 |
| 21 | **Reutilizar `DocumentoAdjunto`** para justificativos de costos | Nuevo campo `ot_costo_id` en `DocumentoAdjunto`. No crear tabla de documentos separada |
| 22 | **`.meta.json` de costos: NO por ahora** | El backup/restore JSON ya cubre la BD. Mantener simple |

### 2.4 RF12 — Contratos

| # | Decisión | Detalle |
|---|----------|---------|
| 23 | **Tabla `Contrato`** + tabla intermedia **`ContratoEquipo`** (N:M) | No usar `grupo_equipos` como TEXT (rompe relaciones FK) |
| 24 | **`activo` no se guarda**, se calcula en runtime | `fecha_inicio <= hoy <= fecha_fin` |
| 25 | **`periodicidad_costo` como enum** | Mensual, Trimestral, Semestral, Anual, Único |
| 26 | **`moneda` como dropdown estricto** | USD, EUR, BOB, MXN, ARS, CLP, COP, PEN, Otro |
| 27 | **`contrato_id` opcional en `OrdenTrabajo`** | Para marcar OTs como cubiertas por contrato |
| 28 | **Contratos NO generan MPs automáticamente en v0.9** | Pospuesto a v1.0 con flag `genera_mp_automatico` |

### 2.5 Cambios adicionales (UX/UI)

| # | Decisión | Detalle |
|---|----------|---------|
| 29 | **Opción C**: Mantener ORDENES + PREVENTIVO separadas + nueva página "Planificación" | Ver §6.1 |
| 30 | **Nombre de la nueva página**: "Planificación" | Calendario unificado OT + MP con filtros |
| 31 | **OTs**: dropdown de equipo muestra `nombre_corto + numero_serie + ubicacion_actual` | Para diferenciar equipos con mismo nombre |
| 32 | **OTs**: mismo formulario en crear/editar, todos los campos editables | Consistencia UX |
| 33 | **Estados multi-dimensión pospuesto a v1.0** | Anotado, servirá para filtrado. Ver §10.1 |

### 2.6 Modo TEST

| # | Decisión | Detalle |
|---|----------|---------|
| 34 | **"Cargar datos TEST"** en Configuración | Crea ~10 proveedores, ~15 equipos, ~8 repuestos, ~8 herramientas, ~10 OTs, ~10 MPs, ~5 contratos |
| 35 | **"Limpiar BD"** en Configuración | Borra todo excepto admin, catálogos (estados) y configuración. Doble confirmación |
| 36 | **Indicador visual "🟡 MODO TEST"** en el navbar mientras haya datos TEST | Para que el usuario sepa que está en modo prueba |

---

## 3. RF01 — Gestión de Activos (Equipos Médicos) Actualizado

### 3.1 Descripción

El sistema debe permitir registrar, editar, eliminar (con restricciones), consultar y gestionar la información detallada de los equipos médicos. Esto incluye identificación única, datos técnicos, estado operativo, ubicación, información del proveedor, fechas clave de garantía y notas relevantes. Se debe permitir adjuntar documentos e imágenes al equipo.

### 3.2 Campos eliminados

| Campo | Justificación de eliminación |
|-------|------------------------------|
| `registro_sanitario_bolivia` | Eliminado por universalidad. Las normativas específicas se manejarán en versiones posteriores |
| `calibracion_proxima` | Se gestionará vía Mantenimiento Preventivo (MP) y OT unificadas (en análisis). La calibración periódica será parte del plan unificado |
| `responsable_tecnico_id` | La asignación de técnicos se hace en OT/MP (flexible, no atado al equipo). El administrador asigna personal a las acciones según necesidad |

### 3.3 Campos nuevos

| Campo | Tipo | Obligatorio | Descripción |
|-------|------|-------------|-------------|
| `observaciones` | TEXT | No | Notas operativas / estado actual / advertencias / accesorios (¿cómo está?) |
| `fecha_inicio_garantia` | DATE | No | Fecha de inicio de la garantía (puede ser fecha de entrega o fecha de instalación, lo que ocurra primero según condiciones del proveedor) |
| `condicion_origen` | TEXT (enum) | No | Dropdown estricto: Compra, Donación, Préstamo, Demostración, Evaluación, Leasing, Renta, Comodato, Otro |
| `proveedor_principal_id` | INTEGER FK → `Proveedor.id` | No | Reemplaza a `proveedor_principal` (texto libre). Dropdown con opción "Crear nuevo" |

### 3.4 Cambios de obligatoriedad

| Campo | Antes (v0.8.3) | Ahora (v0.9.0) | Justificación |
|-------|----------------|----------------|---------------|
| `nombre_corto` | Opcional | **NOT NULL** | Es el identificador visible del equipo, debe estar siempre |
| `fecha_adquisicion` | Obligatorio | Opcional | Puede no conocerse la fecha exacta (donaciones, comodatos, etc.) |

### 3.5 Modelo de datos final (RF01 v0.9.0)

```python
class Equipo(SQLModel, table=True):
    """Equipo médico - RF01 v0.9.0 (universal, sin contexto Bolivia)"""
    __tablename__ = "equipo"

    # Identificación
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre_corto: str                                    # NOT NULL (era opcional)
    modelo: str                                          # NOT NULL (no editable después de crear)
    numero_serie: str = Field(unique=True, index=True)   # NOT NULL, unique (no editable después)
    numero_material: Optional[str] = None
    marca: str                                           # NOT NULL (no editable después de crear)

    # Fechas
    fecha_adquisicion: Optional[date] = None             # Opcional (era obligatorio)
    fecha_inicio_garantia: Optional[date] = None         # NUEVO
    fecha_fin_garantia: Optional[date] = None            # Mantenido

    # Ubicación y estado
    ubicacion_actual: Optional[str] = None
    estado_id: Optional[int] = Field(default=None, foreign_key="estadoequipo.id")

    # Proveedor (FK en vez de texto libre)
    proveedor_principal_id: Optional[int] = Field(
        default=None, foreign_key="proveedor.id"
    )                                                    # NUEVO (reemplaza proveedor_principal)

    # Origen
    condicion_origen: Optional[str] = None               # NUEVO (enum)

    # Descripción
    descripcion: Optional[str] = None                    # Técnica (¿qué es?)
    observaciones: Optional[str] = None                  # NUEVO: Operativas (¿cómo está?)

    # Imagen
    imagen_ruta: Optional[str] = None
```

### 3.6 Reglas de negocio

#### Restricción de eliminación (DELETE)

El endpoint `DELETE /equipos/{id}` debe verificar dependencias antes de eliminar:

| Dependencia | Acción si existe |
|-------------|------------------|
| OTs asociadas (`OrdenTrabajo.equipo_id`) | Rechazar con mensaje: "No se puede eliminar: el equipo tiene X OTs asociadas" |
| Documentos asociados (`DocumentoAdjunto.equipo_id`) | Rechazar con mensaje similar |
| Tareas preventivas (`TareaPreventiva.equipo_id`) | Rechazar con mensaje similar |
| Eventos de historial (`EventoHistorial.equipo_id`) | Rechazar con mensaje similar |
| Contratos asociados (`ContratoEquipo.equipo_id`) | Rechazar con mensaje similar |

**Alternativa**: si el usuario quiere "retirar" el equipo sin eliminarlo, puede cambiar el `estado_id` a "Retirado/Baja" (ya existe en el catálogo de 19 estados).

#### Campos no modificables después de creado

| Campo | Razón |
|-------|-------|
| `modelo` | Afecta nombre de carpeta (`E0001_Modelo_Serie`) y `.meta.json` |
| `marca` | Afecta nombre de carpeta |
| `numero_serie` | Afecta nombre de carpeta, es identificador único, FK en otras tablas |

**Implementación frontend**:
- En modo **Nuevo**: campos editables normalmente
- En modo **Editar**: campos `disabled` (deshabilitados) con texto de ayuda en ROJO:
  > ⚠️ Estos campos no son modificables después de creado el equipo porque afectan la estructura de carpetas y archivos del sistema.

**Excepción (futura v0.9.3+)**: flujo "Editar campos bloqueados" con doble confirmación que actualice también carpetas y `.meta.json`. No crítico para v0.9.

### 3.7 Dropdowns del formulario

#### `condicion_origen` (9 valores)
- Compra
- Donación
- Préstamo
- Demostración
- Evaluación
- Leasing
- Renta
- Comodato
- Otro

#### `proveedor_principal_id` (con opción "Crear nuevo")
1. Lista todos los proveedores de la BD (`GET /proveedores/`)
2. Opción especial: **"+ Crear nuevo proveedor..."**
3. Al elegir "Crear nuevo":
   - Abre mini-modal inline para ingresar solo `nombre_empresa`
   - POST a `/proveedores/` con `nombre_empresa`
   - Obtiene el ID creado
   - Lo selecciona automáticamente en el dropdown
4. Los demás datos del proveedor (ciudad, dirección, contacto, etc.) se completan después desde la página Proveedores

#### `estado_id`
- Lista los 19 estados del catálogo `EstadoEquipo` (sin cambios)

### 3.8 Filtros y búsqueda en EquiposView

#### Barra de búsqueda (texto libre)
- Busca en: `nombre_corto`, `marca`, `modelo`
- Plus: `numero_serie`, `numero_material` (búsqueda exacta o parcial)

#### Filtros (dropdowns)
| Filtro | Origen |
|--------|--------|
| Ubicación actual | Lista única de `ubicacion_actual` de equipos existentes |
| Estado | Lista de `EstadoEquipo` |
| Condición de origen | Los 9 valores del enum `condicion_origen` |

#### Eliminado
- ❌ Filtro por `responsable_tecnico_id` (campo eliminado)

### 3.9 Validaciones

| Campo | Validación |
|-------|------------|
| `numero_serie` | Único en la BD |
| `fecha_inicio_garantia` | Si está seteado, debe ser `<= fecha_fin_garantia` (si esta última también está seteada) |
| `fecha_fin_garantia` | Si está seteado, debe ser `>= fecha_inicio_garantia` |
| `nombre_corto` | No vacío (NOT NULL) |
| `modelo` | No vacío (NOT NULL) |
| `marca` | No vacío (NOT NULL) |

### 3.10 Badges visuales en tarjetas/tabla

| Badge | Condición | Color |
|-------|-----------|-------|
| 🟢 "En garantía" | `fecha_fin_garantia >= hoy` | Verde |
| 🔴 "Garantía vencida" | `fecha_fin_garantia < hoy` | Rojo |
| ⚪ "Sin garantía" | `fecha_fin_garantia` es NULL | Gris |
| 🟡 "Bajo contrato" | Tiene contrato vigente (RF12) | Amarillo |
| 🔵 "{condicion_origen}" | Muestra el origen del equipo | Azul |

---

## 4. RF11 — Gestión Detallada de Costos en OT

### 4.1 Descripción

El sistema debe permitir registrar múltiples costos individuales (con descripción y monto) asociados a una Orden de Trabajo (OT), en lugar de un solo campo de costo adicional. Esto incluye la posibilidad de adjuntar justificaciones documentales (facturas, recibos).

### 4.2 Justificación

Mejorar el análisis de costos y la trazabilidad financiera de las actividades de mantenimiento. Permite distinguir claramente entre el costo de los repuestos utilizados (gestionados en `OtRepuestoUtilizado`) y otros gastos asociados a una intervención (transporte, servicios externos, horas de técnico externo, etc.), lo cual es crucial para la evaluación de costos reales de mantenimiento y la toma de decisiones financieras.

### 4.3 Modelo de datos (RF11 v0.9.0)

```python
class OtCostoAdicional(SQLModel, table=True):
    """Costo adicional asociado a una OT - RF11 v0.9.0"""
    __tablename__ = "otcostoadicional"

    id: Optional[int] = Field(default=None, primary_key=True)
    orden_trabajo_id: int = Field(foreign_key="ordentrabajo.id", index=True)
    tipo_costo: str                  # enum (ver §4.4)
    descripcion_costo: str           # qué se compró/pagó
    monto_costo: float
    fecha_registro: Optional[date] = None    # default = hoy
    subido_por: Optional[str] = None         # username
    fecha_creacion: datetime = Field(default_factory=datetime.now)  # auditoría
```

**Cambio en `DocumentoAdjunto`** (tabla existente, agregar campo):
```python
# Agregar a DocumentoAdjunto:
ot_costo_id: Optional[int] = Field(
    default=None, foreign_key="otcostoadicional.id"
)
```

### 4.4 Enum `tipo_costo`

| Valor | Ejemplo de uso |
|-------|----------------|
| Transporte | Pasaje, flete,combustible |
| Servicio Externo | Reparación por tercero, calibración externa |
| Repuesto No Inventariado | Compra puntual de un repuesto que no está en stock |
| Herramienta Renta | Alquiler de herramienta especializada |
| Honorarios / Mano de Obra | Pago a técnico externo, consultor |
| Insumos / Materiales | Cables, cintas, soldadura, etc. |
| Viáticos | Comidas, hospedaje del técnico en sitio remoto |
| Otro | Cualquier otro concepto |

### 4.5 Funcionalidades

- **CRUD completo** de costos adicionales por OT
- **Listado** de costos en el modal de detalle de la OT (tab "Costos")
- **Subida de documentos justificativos** (factura, recibo) reutilizando `DocumentoAdjunto` con `categoria="costo"` y `ot_costo_id=X`
- **Cálculo de total** automático en el detalle de la OT
- **Reportes RF06**: incluir desglose de costos por tipo en reporte de costos

### 4.6 Eliminación de campos obsoletos en `OrdenTrabajo`

| Campo | Acción |
|-------|--------|
| `costo_adicional` (REAL) | ❌ Eliminar (reemplazado por `OtCostoAdicional`) |
| `costos_adicionales` (REAL) | ❌ Eliminar (reemplazado por `OtCostoAdicional`) |

> **Nota**: Estos campos se eliminan de la tabla `ordentrabajo` ya que los costos ahora se gestionan en `OtCostoAdicional`. El total se calcula como `SUM(OtCostoAdicional.monto_costo WHERE orden_trabajo_id=X)`.

### 4.7 Implementación UI

En `OrdenesView.vue` → modal de detalle/edición de OT:
- Nueva tab **"Costos adicionales"**
- Lista de costos con columnas: tipo, descripción, monto, fecha, acciones (editar/eliminar)
- Botón **"+ Agregar costo"** que abre mini-formulario
- Cada costo puede tener documentos adjuntos (icono 📎)
- Total automático al pie de la lista

---

## 5. RF12 — Gestión de Contratos de Mantenimiento y Servicios

### 5.1 Descripción

El sistema debe permitir gestionar la información de contratos firmados con proveedores para el mantenimiento, soporte o servicios relacionados con uno o varios equipos médicos. Esto incluye el tipo de contrato, fechas de vigencia, costos, cobertura y condiciones específicas.

### 5.2 Justificación

Incorporar la gestión de contratos permite una visión financiera integral del mantenimiento de los equipos, diferenciando costos cubiertos por contrato de costos reales. Facilita la toma de decisiones sobre renovación de contratos, evaluación de proveedores y cálculo del costo total de propiedad (TCO) del equipo.

### 5.3 Modelo de datos (RF12 v0.9.0)

```python
class Contrato(SQLModel, table=True):
    """Contrato de mantenimiento/servicio con un proveedor - RF12 v0.9.0"""
    __tablename__ = "contrato"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relaciones
    proveedor_id: int = Field(foreign_key="proveedor.id", index=True)
    # NOTA: No hay equipo_id directo. La relación N:M se maneja en ContratoEquipo.

    # Tipo y vigencia
    tipo_contrato: str              # enum (ver §5.5)
    fecha_inicio: date              # NOT NULL
    fecha_fin: date                 # NOT NULL
    # activo: NO se guarda, se calcula en runtime (fecha_inicio <= hoy <= fecha_fin)

    # Costos
    costo_total: Optional[float] = None
    costo_periodico: Optional[float] = None
    periodicidad_costo: str = "Único"   # enum (ver §5.6)
    moneda: str = "USD"                  # enum (ver §5.7)

    # Detalles del servicio
    cobertura_detalle: Optional[str] = None
    tiempo_respuesta: Optional[str] = None     # ej: "24 hs", "48 hs"
    horario_servicio: Optional[str] = None     # ej: "Lun-Vie 8-18hs"

    # Notas y auditoría
    notas: Optional[str] = None
    fecha_creacion: datetime = Field(default_factory=datetime.now)


class ContratoEquipo(SQLModel, table=True):
    """Relación N:M entre Contrato y Equipo - RF12 v0.9.0"""
    __tablename__ = "contrato_equipo"

    contrato_id: int = Field(foreign_key="contrato.id", primary_key=True)
    equipo_id: int = Field(foreign_key="equipo.id", primary_key=True)
```

**Cambio en `OrdenTrabajo`** (tabla existente, agregar campo):
```python
# Agregar a OrdenTrabajo:
contrato_id: Optional[int] = Field(
    default=None, foreign_key="contrato.id"
)
```

### 5.4 Justificación de tabla intermedia `ContratoEquipo`

| Opción | Pros | Contras | Decisión |
|--------|------|---------|----------|
| `grupo_equipos` como TEXT ("1,5,7,12") | Simple, una columna | Rompe FK, queries frágiles (LIKE), no cascade | ❌ Descartada |
| **Tabla intermedia `ContratoEquipo`** | FKs correctas, JOIN eficiente, cascade, queries simples | Una tabla más | ✅ Adoptada |

### 5.5 Enum `tipo_contrato`

| Valor | Descripción |
|-------|-------------|
| Comodato | Préstamo gratuito de equipo por tiempo determinado |
| Mantenimiento Preventivo | Servicio de MP programado |
| Mantenimiento Correctivo | Servicio de reparación a demanda |
| Leasing | Arrendamiento financiero del equipo |
| Garantía Extendida | Extiende garantía del fabricante |
| Soporte Técnico | Asistencia técnica remota o presencial |
| Servicio Integral | Combina MP + correctivo + soporte |
| Otro | Otro tipo no listado |

### 5.6 Enum `periodicidad_costo`

| Valor | Descripción |
|-------|-------------|
| Único | Pago único (usar `costo_total`) |
| Mensual | Pago mensual (usar `costo_periodico`) |
| Trimestral | Pago cada 3 meses |
| Semestral | Pago cada 6 meses |
| Anual | Pago anual |

### 5.7 Enum `moneda`

| Valor | Código ISO | Descripción |
|-------|------------|-------------|
| USD | USD | Dólar estadounidense |
| EUR | EUR | Euro |
| BOB | BOB | Boliviano (Bolivia) |
| MXN | MXN | Peso mexicano |
| ARS | ARS | Peso argentino |
| CLP | CLP | Peso chileno |
| COP | COP | Peso colombiano |
| PEN | PEN | Sol peruano |
| BRL | BRL | Real brasileño |
| Otro | — | Otra moneda no listada |

### 5.8 Funcionalidades

- **CRUD completo** de contratos
- **Listado** con filtros: proveedor, tipo, vigencia (vigente/vencido/por vencer)
- **Asociación a equipos** (N:M): un contrato puede cubrir 0, 1 o N equipos
- **Asociación a proveedor** (N:1): cada contrato tiene un proveedor
- **Visualización**:
  - En la página Contratos: tabla con vigencia calculada
  - En el detalle del Proveedor: tab "Contratos"
  - En el detalle del Equipo: tab "Contratos asociados"
- **Cálculo de costos contractuales** para reportes (RF06)
- **Marca de OTs como "Cubiertas por contrato"** vía `OrdenTrabajo.contrato_id` (opcional)

### 5.9 Implementación UI

#### Nueva página "Contratos"
- Tabla con columnas: ID, Proveedor, Tipo, Vigencia (con badge), Equipos cubiertos, Costo, Acciones
- Filtros: Proveedor, Tipo, Vigencia (Vigente/Vencido/Por vencer), Equipo
- Botones: Nuevo contrato, Editar, Eliminar (con restricción), Ver detalle

#### En EquiposView (modal detalle)
- Nueva tab **"Contratos asociados"**
- Lista los contratos que cubren este equipo (vigentes y vencidos)
- Badge "🟡 Bajo contrato" en la tarjeta del equipo si tiene contrato vigente

#### En ProveedoresView (modal detalle)
- Nueva tab **"Contratos"** (además de "Contactos")
- Lista los contratos firmados con este proveedor

#### En OrdenesView (formulario crear/editar)
- Dropdown opcional `contrato_id` que lista contratos vigentes del equipo seleccionado
- Si el equipo no tiene contrato vigente, el dropdown está vacío/deshabilitado

### 5.10 Reportes RF06 (afectados por RF12)

- **Nuevo reporte**: "Costos por contrato vs fuera de contrato" (mensual/trimestral/anual)
- **Nuevo reporte**: "Contratos por vencer" (próximos 30/60/90 días)
- **Modificar reporte "Análisis de costos"**: agregar desglose "Cubierto por contrato" vs "Costo directo"

---

## 6. Cambios Adicionales

### 6.1 Nueva página "Planificación" (calendario unificado OT + MP)

#### Descripción
Página nueva que muestra un calendario interactivo con todas las actividades de mantenimiento del sistema: OTs correctivas, OTs generadas desde MP, y tareas MP programadas.

#### Justificación
El administrador necesita planificar, supervisar y justificar tiempos. Los técnicos necesitan ver su agenda. Una vista temporal unificada es invaluable para la gestión.

#### Estructura
- **Vista calendario** (FullCalendar o similar):
  - Mensual / Semanal / Diaria
  - Eventos:
    - OTs: color según estado (Abierta=azul, En Proceso=naranja, Completada=verde)
    - MPs: color según estado (vencida=rojo, próxima=amarillo, OK=verde)
- **Filtros**:
  - Equipo
  - Ubicación
  - Responsable / Técnico asignado
  - Estado
  - Tipo (Todo / Solo OT / Solo MP)
  - Rango de fechas
- **Interacciones**:
  - Click en evento → abre modal detalle de OT o MP
  - (Futuro v1.0) Drag & drop para reasignar fechas/técnicos

#### Menú
Se agrega "Planificación" al menú lateral, entre "Preventivo" e "Historial".

### 6.2 Modo TEST (datos de ejemplo)

#### Descripción
Sistema para cargar datos de ejemplo que permitan probar el sistema sin tener que crear todo a mano. Útil para:
- Testing del sistema por parte del desarrollador
- Capacitación de usuarios finales
- Reproducir escenarios complejos

#### Implementación

**En `Configuración → nueva pestaña "Datos TEST"`:**

🟢 **Botón "Cargar datos TEST"**:
- Crea:
  - ~10 proveedores con contactos
  - ~15 equipos con todos los estados posibles, imágenes (placeholders), documentos (PDFs fake con texto "TEST")
  - ~8 repuestos con stock variado
  - ~8 herramientas con categorías
  - ~10 OTs (correctivas y preventivas) con documentos y costos adicionales
  - ~10 tareas preventivas
  - ~5 contratos (algunos vigentes, otros vencidos, algunos por vencer)
  - Eventos de historial
- Marca el sistema como "modo TEST activo" (en `sistema_configuracion` o detectando un proveedor con nombre "TechMed Bolivia SRL")

🔴 **Botón "Limpiar BD (mantener admin y catálogos)"**:
- Borra TODOS los equipos, repuestos, herramientas, OTs, MPs, contratos, costos, documentos, eventos
- Borra archivos en `uploads/` (excepto la carpeta en sí)
- NO borra: usuario admin, estados de equipo, estados de OT, configuración del sistema
- Doble confirmación

🟡 **Indicador "MODO TEST"** en el navbar mientras haya datos TEST cargados.

### 6.3 Plantillas Excel vacías

#### Cambio de enfoque
Las plantillas Excel en `frontend/public/plantillas/` pasan de tener datos demo completos a:
- **Encabezados completos** (igual que antes)
- **1-2 filas de ejemplo** (mínimas, para mostrar el formato)
- **Hoja de instrucciones** (mantenida)

#### Justificación
El usuario final usará la plantilla como guía para renombrar y ordenar SUS datos, luego los cargará al sistema. No necesita datos demo completos (para eso está el Modo TEST).

### 6.4 Cambios en OT (RF02)

#### Dropdown de equipo en OT
- Antes: `nombre_corto` solamente
- Ahora: `nombre_corto (numero_serie) · ubicacion_actual`
- Ejemplo: `Microscopio Olympus CX23 (MIC-OLY-001) · Lab. Microbiología`
- Implementación: select con buscador (combobox) para filtrar mientras escribes

#### Consistencia crear/editar OT
- Mismo formulario en ambos modos
- Todos los campos editables (excepto ID)
- Agregar tab "Costos adicionales" (RF11)
- Agregar dropdown `contrato_id` (RF12)

### 6.5 Cambios en menú lateral

#### Menú v0.9.0 (orden propuesto)
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

## 7. Roadmap de Versiones

### Criterio de división
Cada versión debe ser:
- **Auto-contenida**: completa en sí misma, no deja cosas a medias
- **Probablemente estable**: cambios manejables, no demasiados a la vez
- **Incremental**: agrega valor real sobre la versión anterior

### Roadmap propuesto

| Versión | Foco principal | Estado |
|---------|---------------|--------|
| **v0.8.3** | Capa 2 mejorada (recuperación de imágenes y OTs) | ✅ Completada |
| **v0.9.0** | RF01 actualizado + Modo TEST + plantillas vacías | 🔶 Planificada |
| **v0.9.1** | RF11 (Costos en OT) + mejoras OT (dropdowns, formularios consistentes) | 🔶 Planificada |
| **v0.9.2** | RF12 (Contratos) + nueva página "Planificación" (calendario) | 🔶 Planificada |
| **v0.9.3** | Mejoras UX/UI + bug fixes detectados en v0.9.0-v0.9.2 | 🔶 Planificada |
| **v1.0.0** | Estados multi-dimensión + versión final universitaria | 🔶 Planificada |

### Justificación de la división

**v0.9.0 — RF01 + Modo TEST** (sin RF11 ni RF12 todavía):
- Es el cambio más grande de modelo (elimina campos, agrega campos, FK a proveedor)
- Es crítico hacerlo bien antes de agregar más cosas encima
- El Modo TEST permite probar el sistema sin tener que crear datos a mano
- Las plantillas vacías son parte del cambio de enfoque

**v0.9.1 — RF11 + mejoras OT**:
- RF11 depende de OT (agrega tabla `OtCostoAdicional`)
- Aprovechamos para arreglar el dropdown de equipo y la consistencia crear/editar OT
- No toca el modelo Equipo, así que no choca con v0.9.0

**v0.9.2 — RF12 + Planificación**:
- RF12 es grande (2 tablas nuevas + página nueva)
- Aprovechamos para agregar la página "Planificación" que necesita OT + MP ya estables
- Las dependencias (FK a contrato en OT) ya están listas de v0.9.1

**v0.9.3 — Mejoras UX/UI**:
- Bug fixes detectados durante las versiones anteriores
- Mejoras de rendimiento
- Refinamiento visual

**v1.0.0 — Estados multi-dimensión**:
- Rediseño del sistema de estados (operativo, ubicación, garantía, calibración, crítico)
- Versión final para defensa universitaria
- Documentación completa

---

## 8. Plan de Ejecución por Versión

### 8.1 v0.9.0 — RF01 + Modo TEST

**Fase 1 — Backend (modelo + BD)**
1. Actualizar `models/equipos.py` con nuevos campos, eliminar campos obsoletos
2. Actualizar `schemas/equipo.py` (Create/Update/Read)
3. Actualizar `database.py`:
   - Eliminar seed de campos obsoletos
   - Crear función `seed_test_data()` para Modo TEST
   - Crear función `clear_all_data()` para Limpiar BD
4. Actualizar `utils/meta_json.py` → `build_equipo_meta()` con nuevos campos
5. Implementar endpoint `/configuracion/cargar-test`
6. Implementar endpoint `/configuracion/limpiar-bd`

**Fase 2 — Backend (endpoints)**
7. Actualizar `api/routes/equipos.py`:
   - POST/PUT/GET: manejar nuevos campos
   - DELETE: verificar dependencias
   - Import-excel: soportar `proveedor_principal` (texto) → crear FK automáticamente
   - Plantilla-excel: actualizar encabezados
8. Implementar endpoint `/equipos/from-proveedor-nombre` (para crear proveedor al vuelo)
9. Actualizar `api/routes/configuracion.py` (escaneo/recuperación con nuevos campos)

**Fase 3 — Frontend**
10. Regenerar `frontend/public/plantillas/plantilla_equipos.xlsx` (vacía con 1-2 filas ejemplo)
11. Actualizar `frontend/src/views/EquiposView.vue`:
    - Formulario: nuevos campos, dropdown de proveedor con "crear nuevo", advertencia ROJA para campos no editables
    - Tabla: eliminar columnas obsoletas
    - Filtros: `ubicacion_actual`, `estado_id`, `condicion_origen`
    - Eliminar filtro por responsable
    - Badges de garantía
12. Actualizar `frontend/src/views/ConfiguracionView.vue`:
    - Nueva pestaña "Datos TEST" con botones Cargar/Limpiar
    - Indicador "MODO TEST" en navbar (componente `Navbar.vue`)
13. Actualizar `frontend/src/views/AyudaView.vue` (RF01 actualizado)

**Fase 4 — Documentación y verificación**
14. Actualizar `README.md` (v0.9.0, RF01, modelo de datos)
15. Crear `INSTALAR-v0.9.0.md`
16. Probar Modo TEST: cargar datos, verificar, limpiar, volver a cargar
17. Probar migración: backup JSON de v0.8.3 → instalar v0.9.0 → restore
18. Probar importación Excel con nueva plantilla

### 8.2 v0.9.1 — RF11 + Mejoras OT

1. Crear modelo `OtCostoAdicional` en `backend/models/`
2. Actualizar `DocumentoAdjunto` con campo `ot_costo_id`
3. Crear schemas y endpoints CRUD para `/ots/{id}/costos`
4. Eliminar campos `costo_adicional` y `costos_adicionales` de `OrdenTrabajo`
5. Actualizar `OrdenesView.vue`:
   - Tab "Costos adicionales" en modal detalle
   - Dropdown de equipo con `nombre_corto + numero_serie + ubicacion_actual`
   - Formulario consistente crear/editar
6. Actualizar reportes RF06 (desglose de costos por tipo)
7. Actualizar `AyudaView.vue` con RF11

### 8.3 v0.9.2 — RF12 + Planificación

1. Crear modelos `Contrato` y `ContratoEquipo` en `backend/models/`
2. Actualizar `OrdenTrabajo` con campo `contrato_id`
3. Crear schemas y endpoints CRUD para `/contratos`
4. Crear `frontend/src/views/ContratosView.vue`
5. Agregar "Contratos" al menú y al router
6. Actualizar `EquiposView.vue` con tab "Contratos asociados"
7. Actualizar `ProveedoresView.vue` con tab "Contratos"
8. Actualizar `OrdenesView.vue` con dropdown `contrato_id`
9. Crear `frontend/src/views/PlanificacionView.vue` (calendario)
10. Agregar "Planificación" al menú y al router
11. Instalar librería de calendario (FullCalendar o similar)
12. Implementar filtros del calendario
13. Actualizar reportes RF06 (costos por contrato, contratos por vencer)
14. Actualizar `AyudaView.vue` con RF12 y Planificación

### 8.4 v1.0.0 — Estados multi-dimensión + versión final

- Rediseño del sistema de estados (ver §10.1)
- Documentación completa
- Empaquetado para distribución (PyInstaller)
- Versión final para defensa universitaria

---

## 9. Preguntas Pendientes

### 9.1 RF11 — Costos

**P1**: ¿Confirmas la lista de `tipo_costo`?
- Transporte, Servicio Externo, Repuesto No Inventariado, Herramienta Renta, Honorarios/Mano de Obra, Insumos/Materiales, Viáticos, Otro

**P2**: ¿Confirmas reutilizar `DocumentoAdjunto` con nuevo campo `ot_costo_id`?
- En vez de crear `ruta_documento_costo` separado en `OtCostoAdicional`

### 9.2 RF12 — Contratos

**P3**: ¿Confirmas tabla intermedia `ContratoEquipo` (N:M)?
- En vez de `grupo_equipos` como TEXT serializado

**P4**: ¿Confirmas enums para `tipo_contrato`, `periodicidad_costo`, `moneda`?
- Ver listas en §5.5, §5.6, §5.7

**P5**: ¿Confirmas agregar `contrato_id` opcional a `OrdenTrabajo`?
- Para marcar OTs como cubiertas por contrato

### 9.3 Menú

**P6**: ¿"Contratos" después de "Proveedores" en el menú?
- Ver menú propuesto en §6.5

### 9.4 Roadmap

**P7**: ¿Confirmas división v0.9.0 / v0.9.1 / v0.9.2 / v0.9.3 / v1.0.0?
- Ver §7

### 9.5 Modo TEST

**P8**: ¿Confirmas implementación del Modo TEST en v0.9.0?
- Botones Cargar/Limpiar en Configuración
- Indicador "MODO TEST" en navbar

### 9.6 Plantillas Excel

**P9**: ¿Confirmas que las plantillas Excel pasan a estar vacías (solo 1-2 filas ejemplo)?
- En vez de tener datos demo completos
- Los datos demo completos se cargan vía Modo TEST

---

## 10. Opciones Futuras (post-v1.0)

### 10.1 Estados multi-dimensión

**Problema actual**: El catálogo de 19 estados mezcla dimensiones distintas (operativo, ubicación, garantía, etc.).

**Propuesta para v1.0**:

| Dimensión | Campo | Valores posibles |
|-----------|-------|-----------------|
| Operativo | `estado_operativo_id` | Operativo, En Mantenimiento, En Reparación, Fuera de Servicio, Dado de Baja |
| Ubicación | `estado_ubicacion_id` | En Almacén, En Préstamo, En Transporte, En Uso |
| Garantía (derivado) | calculado | En Garantía, Vencida, Sin Garantía |
| Calibración (derivado de MP) | calculado | Al día, Pendiente, Vencida |
| Crítico | `es_critico` (bool) | Sí / No (LOTO, Condición crítica, etc.) |

**Beneficios**:
- Filtrado más flexible (por cada dimensión independientemente)
- No se mezclan dimensiones (un equipo puede estar Operativo + En Préstamo + Garantía Vigente)
- Reportes más precisos

**Costo**: rediseño grande, migración, afecta formularios y reportes.

### 10.2 Contratos que generan MPs automáticamente

Agregar flag `genera_mp_automatico: bool` a `Contrato`:
- Si es `True` y el contrato es de tipo "Mantenimiento Preventivo", genera tareas MP automáticamente según `frecuencia_dias` definida en el contrato.
- Útil para contratos de servicio integral.

### 10.3 Edición de campos bloqueados en Equipo

Flujo "Editar campos bloqueados" con doble confirmación que actualice también:
- Nombre de la carpeta (`E0001_Modelo_Serie` → `E0001_NuevoModelo_NuevaSerie`)
- `.meta.json` del equipo
- Referencias cruzadas en OTs, documentos, etc.

### 10.4 Drag & drop en calendario de Planificación

Permitir reasignar fechas/técnicos arrastrando eventos en el calendario.

### 10.5 Versión con normativa Bolivia (cliente final)

Después de v1.0:
- Agregar campos específicos de normativa boliviana (DIMUTES, etc.)
- Reportes específicos para DIGEMIGA/SEDES
- Versión diferenciada para cliente final vs importador vs fabricante

### 10.6 App móvil para técnicos

App móvil (PWA o nativa) para que los técnicos:
- Vean sus OTs asignadas
- Marquen OTs como completadas
- Suban fotos de los trabajos realizados
- Firmen digitalmente

### 10.7 Multi-idioma

 Internacionalización del sistema (i18n):
- Español (por defecto)
- Inglés
- Portugués
- Otros según necesidad

### 10.8 Multi-sede con sincronización

Arquitectura para sincronizar datos entre sedes (sucursal central + sucursales remotas):
- Resolución de conflictos
- Sincronización offline-first
- Replicación bidireccional

---

## 📎 Anexos

### Anexo A: Archivos Excel generados

Junto a este documento, se generan los siguientes archivos Excel con la estructura detallada de cada RF:

- `RF01_Activos_Equipos_v0.9.xlsx` — Estructura actualizada del modelo Equipo
- `RF11_Costos_OT_v0.9.xlsx` — Estructura de la tabla `OtCostoAdicional`
- `RF12_Contratos_v0.9.xlsx` — Estructura de las tablas `Contrato` y `ContratoEquipo`

Cada Excel contiene:
- Hoja 1: Descripción general del RF (formato estándar)
- Hoja 2: Estructura detallada de la tabla (campos, tipos, obligatoriedad, descripción)
- Hoja 3 (si aplica): Valores de enums (dropdowns estrictos)
- Hoja final: Opciones futuras (post-v1.0) como recordatorio

### Anexo B: Historial de versiones de este documento

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.0 | 2026-06-20 | Creación inicial. Decisiones tomadas en conversaciones con IA de diseño y IA de software. |

---

> **Nota final**: Este documento es un **living document**. A medida que avancemos en la implementación y descubramos nuevos detalles, se actualizará. La idea es mantenerlo como **single source of truth** para el desarrollo de v0.9.0 y versiones posteriores.

> **Siguiente paso**: Responder las preguntas pendientes (§9) y luego empezar la implementación de v0.9.0 siguiendo el plan de ejecución (§8.1).
