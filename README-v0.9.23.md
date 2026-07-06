# CMMS-BioAI v0.9.23 — ORDENES: fecha/hora editable + UI mejorada + calendario

## Resumen

Se implementó la edición de fecha y hora de creación en Órdenes de Trabajo, mejoras visuales en Costos/Repuestos/Acciones, indicador de origen (preventivo/correctivo) y sincronización con el calendario de Planificación.

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