# CMMS-BioAI v0.9.23 — ORDENES: fecha/hora editable + PREVENTIVO: layout + calendario mejorado

## Resumen

Se implementó la edición de fecha y hora de creación en Órdenes de Trabajo, mejoras visuales en Costos/Repuestos/Acciones, indicador de origen (preventivo/correctivo), sincronización con el calendario de Planificación, y mejoras significativas en el módulo de Preventivo (layout de formulario, select de equipo con datos completos, y calendario de planificación con doble evento por MP).

## Cambios solicitados y aplicados

### 1. Campo `fecha_creacion` editable (datetime-local)

Antes `fecha_creacion` era un campo `DATETIME` de solo lectura (se generaba automáticamente al crear la OT). Ahora es completamente editable en los modales Crear y Editar mediante un input `datetime-local` que permite seleccionar fecha y hora en un solo control nativo del navegador.

**Decisión de diseño**: Se evaluó crear un campo `hora_creacion` separado, pero dado que `fecha_creacion` ya es `DATETIME` en SQLite (almacena fecha y hora), se optó por usar un solo campo `datetime-local` en el frontend. Esto simplifica el modelo, esquemas y lógica de backend sin perder funcionalidad.

**Esquema actualizado**:
- `OrdenTrabajoCreate.fecha_creacion`: cambió de `Optional[date]` a `Optional[datetime]`
- `OrdenTrabajoUpdate.fecha_creacion`: cambió de `Optional[date]` a `Optional[datetime]`
- `OrdenTrabajoRead.fecha_creacion`: ya era `Optional[datetime]` (sin cambios)

**Frontend**:
- Nuevas funciones helper: `toLocalDatetimeString()` y `toDatetimeLocal()` para conversión entre `Date` de JavaScript y el formato `YYYY-MM-DDTHH:MM` requerido por `datetime-local`
- Input en modal Crear: `<input type="datetime-local" v-model="formData.fecha_creacion">`
- Input en modal Editar: `<input type="datetime-local" v-model="editFormData.fecha_creacion">`
- Valor por defecto: fecha y hora actual del navegador

**Importante**: `fecha_vencimiento` NO se modifica. Este campo pertenece al sistema de generación automática desde tareas preventivas y no debe usarse para programación manual.

### 2. Calendario sincronizado con `fecha_creacion`

En `PlanificacionView.vue`, la lógica para determinar la fecha de un evento OT cambió de:
```javascript
// ANTES: usaba fecha_vencimiento primero, luego fecha_creacion
const fecha = ot.fecha_vencimiento || ot.fecha_creacion
```
a:
```javascript
// AHORA: usa siempre fecha_creacion (el campo editable)
const fecha = ot.fecha_creacion
```

**¿Por qué es importante?**
Cuando una OT se genera desde preventivo (tiene `orden_preventiva_id` y el icono `🛡️`), el usuario puede editar su `fecha_creacion` para reprogramarla. Con el cambio anterior, esa edición se refleja inmediatamente en el calendario de Planificación.

### 3. Indicador de Origen en la tabla

Se implementaron las opciones B y E para la columna Origen:
- **Opción B (icono en título)**: Las OTs generadas desde preventivo muestran `🛡️` junto al título en la tabla. Al pasar el mouse se ve el tooltip `Preventivo #<id>`.
- **Opción E (reemplazar columna)**: La columna "Origen" fue reemplazada por "Fecha / Hora" que muestra la fecha y hora de creación formateada.

### 4. Estilos visuales mejorados

**Costos Adicionales** (paleta violeta profesional):
- Borde lateral izquierdo violeta (`#7c3aed`)
- Fondo lavanda claro (`#faf5ff`)
- Items con borde izquierdo de 3px (`border-left: 3px solid #7c3aed`)
- Sin cuadro exterior envolvente

**Repuestos Utilizados** (paleta amber profesional):
- Borde lateral izquierdo ámbar (`#d97706`)
- Fondo ámbar claro (`#fffbf0`)
- Items con borde izquierdo de 3px (`border-left: 3px solid #d97706`)
- Sin cuadro exterior envolvente

**Descripción de Falla y Acciones Realizadas** (modal Ver):
- Se eliminó el cuadro exterior (clase `detail-full-view`)
- Nueva clase `detail-no-box` sin fondo ni borde
- El texto se muestra directamente bajo el título de sección

### 5. DATOS TEST actualizado

Los datos de prueba generan OTs con `fecha_creacion` como `datetime` completo (incluye hora), sin necesidad de un campo separado para la hora.

## Archivos modificados (7)

| Archivo | Cambios |
|---------|---------|
| `backend/models/ordenes.py` | Eliminado campo `hora_creacion` del modelo `OrdenTrabajo` |
| `backend/schemas/orden_trabajo.py` | `fecha_creacion` cambió a `Optional[datetime]` en Create/Update. Eliminado `hora_creacion` de todos los esquemas |
| `backend/api/routes/ordenes.py` | Simplificada lógica de fecha: `fecha_creacion` se aplica directo como datetime sin combinación con `hora_creacion` |
| `backend/api/routes/configuracion.py` | DATOS TEST: OTs usan `datetime(año, mes, dia, hora, min)` directamente en `fecha_creacion` |
| `backend/database.py` | Eliminada migración `_migrate_hora_creacion()` (campo ya no existe) |
| `frontend/src/views/OrdenesView.vue` | Input `datetime-local` único, funciones helper `toLocalDatetimeString`/`toDatetimeLocal`, icono `🛡️` en título, columna Fecha/Hora, estilos violeta/amber/no-box |
| `frontend/src/views/PlanificacionView.vue` | Calendario usa siempre `fecha_creacion` (no `fecha_vencimiento`) para eventos OT |
| `frontend/src/views/AyudaView.vue` | Actualizada documentación de entidad y módulo: eliminado `hora_creacion`, actualizada descripción de `fecha_creacion` |

## Cómo aplicar

1. Copiar los 7 archivos a tu proyecto reemplazando los existentes.
2. En la carpeta `backend/`, ejecutar:
   ```bash
   pip install -r requirements.txt
   ```
3. Si ya tienes BD con la columna `hora_creacion` de una versión anterior: no es necesario hacer nada. SQLModel ignora columnas que no están en el modelo.
4. En la carpeta `frontend/`, ejecutar:
   ```bash
   npm run build
   ```
5. Refrescar el navegador con **Ctrl+F5**.

## Notas técnicas

- El campo `fecha_creacion` es `DATETIME` en SQLite, lo que permite almacenar fecha y hora con precisión de segundos.
- El input `datetime-local` de HTML5 envía el valor en formato `YYYY-MM-DDTHH:MM`, que Pydantic parsea automáticamente a `datetime`.
- Si `fecha_creacion` no se envía al crear una OT, el `default_factory=datetime.now` del modelo SQLModel asigna la fecha/hora actual.
- La columna `hora_creacion` puede existir en BDs antiguas pero es ignorada completamente por SQLModel (no está en el modelo).

---

## v0.9.23-b — Mejoras en Preventivo y Calendario

### 6. Preventivo: Layout del formulario reorganizado

**Título + Frecuencia en una fila**: Los campos "Título de la Tarea" (bloqueado como "Preventivo") y "Frecuencia (días)" ahora comparten una fila con `form-row`. Gap de 0.75rem entre ellos.

**Última Fecha + Próxima Fecha en una fila**: Los campos "Última Fecha Realizada" y "Próxima Fecha Programada" comparten otra fila con el mismo gap.

**Frecuencia default 90 días**: Cambió de 60 a 90 días como valor por defecto al crear nueva tarea.

**Última Fecha con fecha del sistema**: Al crear, `ultima_fecha` se llena con la fecha actual del sistema en formato `date` (solo fecha, sin hora). El usuario puede editarla.

**Inputs encuadrados**: Todos los inputs y selects de los modales usan `box-sizing: border-box` y `font-size: 0.9rem` uniforme. En `form-row`, cada `form-group` tiene `min-width: 0` para evitar desbordamientos.

### 7. Kit de Mantenimiento: layout mejorado

**Orden visual** (izquierda a derecha): Select de repuestos (flex: 1) → Cantidad (52px fijo, texto centrado) → Botón Agregar (amber #d97706).

**Repuestos agregados con fondo resaltado**: Cada `<li>` en la lista de repuestos tiene fondo `#fef3c7` (ámbar claro) para distinguir los elementos agregados.

**Cantidad reducida**: El input de cantidad tiene `width: 52px` con `text-align: center`, suficiente para 3 dígitos.

### 8. Select de Equipo: nombre - modelo - número de serie

En los modales Nuevo y Editar de Preventivo, el select de equipo muestra:
```
nombre_corto - modelo - numero_serie
```

Se agregó la función helper `getEquipoFullLabel(id)` que construye esta etiqueta combinada. Si algún campo está vacío se omite.

### 9. Modal Generar OT: número de serie + inputs igualados

**Número de serie visible**: Se agrega línea "N. Serie:" debajo de "Equipo:" en la info del modal. Se pasan los datos desde `openGenerarOTModal()` usando `getEquipoNumeroSerie()`.

**Inputs igualados**: Se agregó regla CSS `.generar-ot-info + form .form-group input/select` para que todos los inputs del formulario tengan `width: 100%`, `box-sizing: border-box` y `padding: 0.6rem` consistentes, igualando el campo "Fecha y Hora Programada" con los demás.

### 10. Calendario de Planificación: doble evento por MP

Cada tarea preventiva (MP) ahora genera **2 eventos en el calendario**:

| Evento | Campo | Color | Estado |
|--------|-------|-------|--------|
| Última Fecha Realizada | `ultima_fecha` | Índigo `#6366f1` (no realizado) o Verde `#16a34a` (realizado, tiene OT) | "No Realizado" / "Realizado" |
| Próxima Fecha Programada | `proxima_fecha` | Amarillo `#eab308` / Rojo `#ef4444` / Naranja `#f97316` / Verde `#16a34a` | "Programado" / "Vencido" / "Hoy" / "Con OT" |

**Badge en evento**: Los eventos de última fecha muestran "MP Ult." en el badge, los de próxima fecha muestran "MP".

**Modal de detalle**: Incluye badge indicando "Ult. Realizada" (índigo) o "Prox. Programada" (amarillo) junto a la fecha.

**Resumen actualizado**: Nueva categoría "🟣 No Realizados" contando MPs cuya última fecha no tiene OT asociada.

**Leyenda actualizada**: Incluye entradas para MP No Realizado, MP Realizado/Con OT, MP Programado, y MP Vencido.

## Archivos modificados (9)

| Archivo | Cambios |
|---------|---------|
| `backend/models/ordenes.py` | Eliminado campo `hora_creacion` del modelo `OrdenTrabajo` |
| `backend/schemas/orden_trabajo.py` | `fecha_creacion` cambió a `Optional[datetime]` en Create/Update. Eliminado `hora_creacion` de todos los esquemas |
| `backend/api/routes/ordenes.py` | Simplificada lógica de fecha: `fecha_creacion` se aplica directo como datetime sin combinación con `hora_creacion` |
| `backend/api/routes/configuracion.py` | DATOS TEST: OTs usan `datetime(año, mes, dia, hora, min)` directamente en `fecha_creacion` |
| `backend/database.py` | Eliminada migración `_migrate_hora_creacion()` (campo ya no existe) |
| `frontend/src/views/OrdenesView.vue` | Input `datetime-local` único, funciones helper, icono `🛡️` en título, columna Fecha/Hora, estilos violeta/amber/no-box |
| `frontend/src/views/PlanificacionView.vue` | Calendario usa siempre `fecha_creacion` para OTs; MPs generan 2 eventos (ultima_fecha + proxima_fecha); resumen con "No Realizados"; badge tipo fecha en modal |
| `frontend/src/views/PreventivoView.vue` | Layout formulario (Título+Frecuencia, Fechas en filas); frecuencia default 90; select equipo con nombre-modelo-N serie; kit layout (cantidad 52px, botón amber, fondo #fef3c7); modal Generar OT con N. Serie e inputs igualados |
| `frontend/src/views/AyudaView.vue` | Actualizada documentación de entidad y módulo: eliminado `hora_creacion`, actualizada descripción de `fecha_creacion` |

## Cómo aplicar

1. Copiar los archivos a tu proyecto reemplazando los existentes.
2. En la carpeta `backend/`, ejecutar:
   ```bash
   pip install -r requirements.txt
   ```
3. Si ya tienes BD con la columna `hora_creacion` de una versión anterior: no es necesario hacer nada. SQLModel ignora columnas que no están en el modelo.
4. En la carpeta `frontend/`, ejecutar:
   ```bash
   npm run build
   ```
5. Refrescar el navegador con **Ctrl+F5**.