# CMMS-BioAI v0.9.20 — ORDENES: nombre repuesto + color normal + filtros + ordenamiento + Ayuda

## Cambios solicitados y aplicados

### Punto 1: ✅ En el ojo, mostrar nombre del repuesto
**Problema**: En el modal Ver (ojo), los repuestos se mostraban como "3 x Repuesto #2" — solo el ID, sin nombre. No se sabía qué repuesto era.

**Fix**:
- Modificada la función `openViewModal(ot)` para que también cargue `listaRepuestos` desde `/repuestos/` si aún no está cargada.
- Agregado helper `getRepuestoNombre(id)` que busca el repuesto por ID en `listaRepuestos` y devuelve `nombre_repuesto` (con fallback a `Repuesto #ID` si no se encuentra).
- Template del modal Ver actualizado:
  ```html
  <!-- antes -->
  {{ rep.cantidad_utilizada }} x Repuesto #{{ rep.repuesto_id }}
  <!-- ahora -->
  {{ rep.cantidad_utilizada }} x {{ getRepuestoNombre(rep.repuesto_id) }}
  ```
- Ahora se ve: "3 x Filtro de aire" en lugar de "3 x Repuesto #2".

### Punto 2: ✅ En el ojo, "Acciones Realizadas" con color normal
**Problema**: El texto de "Acciones Realizadas" en el modal Ver estaba en verde (`color: #27ae60`), distinto al resto de la interfaz.

**Fix**: Eliminado el estilo inline `color: #27ae60` del `<div class="description-box">`. Ahora usa el color por defecto de `.description-box` (`color: #444`), igual que "Descripción de Falla".

### Punto 3: ✅ Filtros + ordenamiento
**Problema**: No había filtros por Tipo, Prioridad, Estado. Las OTs nuevas se mostraban al final, obligando a navegar muchas páginas para ver la última.

**Fix**:
- Agregadas 4 variables: `filterTipo`, `filterPrioridad`, `filterEstado`, `sortOrder` (default `'desc'` = nuevas primero).
- `filteredOrdenes` (computed) ahora aplica:
  1. Búsqueda libre (por título, falla, ID, equipo) — ya existía
  2. Filtro por Tipo (`ot.titulo === filterTipo`)
  3. Filtro por Prioridad (`ot.prioridad === filterPrioridad`)
  4. Filtro por Estado (`ot.estado_id === filterEstado`)
  5. Ordenamiento por ID: `desc` (nuevas primero) o `asc` (viejas primero)
- `watch` actualizado para resetear `currentPage` a 1 cuando cambian los filtros u orden.
- Agregada barra de filtros en el template (entre el top-bar y la tabla) con:
  - Select "Tipo" (16 tipos de OT)
  - Select "Prioridad" (Urgente/Alta/Media/Baja)
  - Select "Estado" (cargado desde `estadosOT`)
  - Select "Orden" (↓ Nuevas primero / ↑ Viejas primero)
  - Botón "Limpiar filtros" (solo visible si hay filtros activos)
- CSS nuevo para `.filter-bar`, `.filter-group`, `.filter-label`, `.filter-select`, `.btn-clear-filters`.

### Punto 4: ⏸️ Costos múltiples — dejado para después
Como indicaste, este punto es delicado porque puede redefinir la forma de manejar las tablas de costos. Se analizará conforme a las tablas existentes en la página Ayuda y se implementará en una versión futura.

### Punto 5: ✅ Actualizar página Ayuda
Actualizada la descripción del módulo "Ordenes de Trabajo" en `AyudaView.vue` con todas las funcionalidades nuevas de v0.9.18, v0.9.19 y v0.9.20:

- Descripción extendida con notas de versiones.
- Lista de funcionalidades ampliada de 6 a 18 items, incluyendo:
  - 16 tipos de OT
  - Repuestos con descuento de stock al crear y editar
  - Modales Nuevo y Editar unificados (mismos campos)
  - Equipo, Título y Falla editables en modal Editar
  - Repuestos se guardan al crear OT (fix v0.9.19)
  - Iconos con hover de color
  - Lista de repuestos con fondo amarillo
  - Modal Ver redimensionado (600px)
  - Repuestos en Ver con fondo amarillo y nombre
  - Filtros por Tipo, Prioridad, Estado
  - Ordenamiento ascendente/descendente
  - Acciones Realizadas con color normal

## Archivos modificados (2 archivos)

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/OrdenesView.vue` | Puntos 1, 2, 3 (nombre repuesto, color normal, filtros + orden) |
| `frontend/src/views/AyudaView.vue` | Punto 5 (descripción de Ordenes actualizada con v0.9.18-v0.9.20) |

## Cómo aplicar

1. Copia los 2 archivos a tu PC en `D:\cmmsbioai\frontend\src\views\` (reemplazando los existentes).
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5**.
4. Verás:
   - **Modal Ver**: repuestos muestran "cantidad x nombre_repuesto" (ej: "3 x Filtro de aire").
   - **Modal Ver**: "Acciones Realizadas" con color de texto normal (no verde).
   - **Barra de filtros**: Tipo, Prioridad, Estado, Orden (nuevas/viejas primero).
   - **Por defecto**: las OTs nuevas aparecen primero (no hay que navegar páginas).
   - **Página Ayuda**: descripción de Ordenes actualizada con todas las mejoras.

## ⚠️ Importante
- No se requieren cambios en el backend para esta versión (los endpoints ya funcionan correctamente desde v0.9.19).
- El punto 4 (costos múltiples) queda pendiente para una versión futura, cuando se analice la mejor forma de implementarlo conforme a las tablas existentes.

## Versión
- **Versión**: v0.9.20
- **Fecha**: 2026-07-02
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
