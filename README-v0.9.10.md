# CMMS-BioAI v0.9.10 — Contratos: fix edición + alineación + detalle solo lectura + negrillas

## Cambios solicitados y aplicados

### 1. 🐛 FIX: Error al editar contrato ("PUT /contratos/undefined")
**Síntoma**: Al editar un contrato y guardar, aparecía el error:
```
Error al guardar contrato: [{"type":"int_parsing","loc":["path","contrato_id"],"msg":"Input should be a valid integer, unable to parse string as an integer","input":"undefined"}]
```
**Causa raíz**: La función `abrirEditar(c)` llenaba `formData` y activaba `isEditing`, pero **no guardaba referencia al contrato** en `selectedContrato.value`. Luego `guardarContrato()` intentaba obtener `selectedContrato.value?.id` que era `undefined`, generando el PUT a `/contratos/undefined`.

**Fix**: Agregada la línea `selectedContrato.value = c` al inicio de `abrirEditar(c)`.

**Validación backend**: Probado con TestClient — crear contrato → PUT /contratos/{id} ahora responde 200 OK y actualiza los campos correctamente.

### 2. Alineación de iconos en Acciones
**Problema**: Los iconos estaban muy a la derecha, no alineados como en las otras páginas.

**Causa**: La regla `.actions-cell` tenía `justify-content: flex-end;` que empujaba los botones a la derecha de la celda.

**Fix**: Eliminado `justify-content: flex-end;` de `.actions-cell`. Ahora los iconos quedan alineados a la izquierda de la celda, igual que en Equipos y Proveedores.

### 3. Modal "ojo" = SOLO LECTURA
**Problema**: El modal de detalle (al hacer clic en el "ojo") tenía botones "🗑 Eliminar" y "✏️ Editar" en el pie, lo que viola la semántica del "ojo" (ver es solo ver).

**Fix**: Eliminados los botones "Eliminar" y "Editar" del footer del modal de detalle. Solo queda "Cerrar".

### 4. Marca y número de serie en negrillas
**Problema**: En los chips y en los resultados de búsqueda, la marca y el número de serie se mostraban en gris claro (`text-muted`), poco visibles.

**Fix**:
- **Chips**: cambiado `<small class="chip-sub">` por `<strong class="chip-sub-bold">` con color azul oscuro `#1e40af` y font-weight 600.
- **Resultados de búsqueda**: cambiado `<small class="text-muted">` por `<strong class="equipo-item-bold">` con color `#334155` (gris oscuro) y font-weight 600.
- Ahora los 3 campos (nombre, marca, SN) se ven claramente en negrilla.

### 5. Quitar subtítulo del header
**Problema**: El header mostraba "Gestión de contratos de mantenimiento, leasing, comodato y otros (RF12)" debajo del título.

**Fix**: Eliminado el `<p class="subtitle">...</p>` del template. Solo queda el `<h2>Contratos</h2>`.

## Archivos modificados

| Archivo | Acción |
|---------|--------|
| `frontend/src/views/ContratosView.vue` | **EDITADO** — 5 cambios en 1 archivo |

## Cómo aplicar

1. Copia el archivo `frontend/src/views/ContratosView.vue` a tu copia local.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5** (limpiar caché).
4. Verás:
   - Al editar un contrato, se guarda correctamente (sin error).
   - Iconos de Acciones alineados a la izquierda de la celda.
   - Modal "ojo" solo muestra "Cerrar" (sin editar ni eliminar).
   - Marca y SN en negrilla en chips y resultados de búsqueda.
   - Header sin subtítulo.

## Versión
- **Versión**: v0.9.10
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
