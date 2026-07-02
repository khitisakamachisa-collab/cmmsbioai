# CMMS-BioAI v0.9.18 — ORDENES: unificar Nuevo/Editar + Repuestos ancho + campos editables

## Cambios solicitados y aplicados

### 1. ✅ Nuevo y Editar con las mismas opciones
**Problema**: El modal "Nueva Orden" tenía menos campos que el modal "Editar". Específicamente, Nuevo NO tenía: Tiempo Invertido, Acciones Realizadas, Costos (General y Adicionales), Repuestos Utilizados.

**Fix**: Se agregaron al modal NUEVO todos los campos que faltaban, para que ambos modales tengan exactamente las mismas opciones:
- Equipo Afectado (select)
- Estado (select)
- Prioridad (select)
- Técnico Asignado (select)
- Título / Tipo de OT (select)
- Descripción / Falla (textarea)
- **Tiempo Invertido + unidad (number + select)** ← NUEVO
- **Acciones Realizadas (textarea)** ← NUEVO
- **Costo General (Bs.) (number)** ← NUEVO
- **Costos Adicionales (Bs.) (number)** ← NUEVO
- **Repuestos Utilizados (selector + lista)** ← NUEVO

**Cambios en script setup**:
- `formData` (Crear) ahora incluye: `tiempo_real_invertido`, `acciones_realizadas`, `costo_adicional`, `costos_adicionales`.
- `editFormData` (Editar) ahora incluye: `equipo_id`, `titulo`, `descripcion_falla` (además de los que ya tenía).
- Nueva función `openCreateModal()` que resetea el formulario, limpia repuestos seleccionados, carga `listaRepuestos` desde `/repuestos/`, y abre el modal. Reemplaza el `@click="showModal = true"` del botón "+ Nueva Orden".
- `saveOrden()` ahora envía `repuestos_utilizados` en el payload y parsea `tiempo_real_invertido` a float.
- `openEditModal()` ahora llena `equipo_id`, `titulo`, `descripcion_falla` en `editFormData`.
- `updateOrden()` ya hacía `...editFormData.value` así que automáticamente envía los campos nuevos.

### 2. ✅ Selector de Repuestos Utilizados con mismo ancho
**Problema**: El `<select>` del selector de repuestos era más delgado que el resto de inputs. Tenía `display: flex` pero el select no tenía `flex: 1`, así que tomaba el ancho mínimo.

**Fix**: Agregadas reglas CSS específicas:
```css
.repuesto-selector select { flex: 1; padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
.repuesto-selector input { padding: 0.6rem; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
```

Ahora el select ocupa todo el ancho disponible (`flex: 1`), el input de cantidad tiene 80px (antes 60px), y ambos tienen el mismo padding y borde que el resto de inputs del formulario. El selector completo ahora encuadra con el resto de elementos.

### 3. ✅ En Editar, Equipo/Título/Falla editables
**Problema**: En el modal Editar, los campos Equipo, Título y Falla estaban en un div `.ot-details` como **solo lectura** (texto plano). No se podían modificar.

**Fix**: Eliminado el div `.ot-details` con texto plano. En su lugar, se agregaron campos editables en el formulario:
- **Equipo Afectado**: `<select v-model="editFormData.equipo_id">` con la lista de equipos.
- **Título / Tipo de OT**: `<select v-model="editFormData.titulo">` con la lista de tipos.
- **Descripción / Falla**: `<textarea v-model="editFormData.descripcion_falla">`.

Estos campos aparecen al inicio del formulario de edición, antes de Estado/Prioridad. Ahora el usuario puede corregir el equipo, tipo o descripción de la falla si se equivocó al crear la OT.

## Archivos modificados (1 archivo)

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/OrdenesView.vue` | Unificar modales + repuestos ancho + campos editables |

## Cómo aplicar

1. Copia `OrdenesView.vue` a tu PC en `D:\cmmsbioai\frontend\src\views\` (reemplazando el existente).
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5**.
4. Verás:
   - **Nueva Orden**: ahora tiene Tiempo Invertido, Acciones Realizadas, Costos y Repuestos Utilizados (igual que Editar).
   - **Editar**: ahora Equipo, Título y Falla son editables (selects y textarea, no texto plano).
   - **Repuestos Utilizados**: el select ahora ocupa todo el ancho disponible, encuadrando con el resto de inputs.

## Notas técnicas

- El campo `.ot-details` (div de solo lectura con texto plano) se eliminó del template del modal Editar, pero su regla CSS `.ot-details { background: #f8f9fa; padding: 1rem; border-radius: 4px; margin-bottom: 1rem; }` se mantiene por compatibilidad (no afecta visualmente).
- El backend `PUT /ordenes/{id}` ya acepta todos los campos (equipo_id, titulo, descripcion_falla, estado_id, prioridad, tecnico_asignado_id, unidad_tiempo, tiempo_real_invertido, acciones_realizadas, costo_adicional, costos_adicionales, repuestos_utilizados) — no se requieren cambios en el backend.
- El ancho del modal NUEVO se cambió de 500px (default) a 700px para que coincida con el de EDITAR y los campos quepan bien.

## Versión
- **Versión**: v0.9.18
- **Fecha**: 2026-07-02
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
