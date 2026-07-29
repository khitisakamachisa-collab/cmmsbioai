# CMMS-BioAI v0.9.16 — Restauración de mejoras perdidas + v0.9.15 preservada

## 🚨 Diagnóstico de lo que pasó

En v0.9.15 trabajé accidentalmente sobre una **versión vieja e incompleta** de `ContratosView.vue` (34 KB) en lugar de la versión correcta que tú tenías en tu PC (63 KB, con todas las mejoras v0.9.4 a v0.9.14). Esto causó que se perdieran 6 mejoras importantes:

1. Buscador arriba a la derecha (separado de filtros)
2. Botones SVG con colores en Acciones (regresaron a emojis)
3. Botón de Documentos (faltante)
4. Columna "Equipos" en la tabla (no debía estar)
5. Botón "Cargar Excel" con plantillas (faltante)
6. Selector chips/tags para Equipos Asociados (regresó al checkbox grid antiguo)

## ✅ Solución aplicada

**NO se borró nada ni se empezó desde cero.** En su lugar:

1. **Re-cloné el repositorio de GitHub** (que tú subiste con todas las mejoras correctamente aplicadas).
2. **Comparé tamaños** de todas las vistas `.vue` entre mi local y GitHub:
   - `ContratosView.vue`: 34 KB (local viejo) vs 63 KB (GitHub correcto) → **28 KB de mejoras perdidas**
   - `ProveedoresView.vue`: 39 KB (local viejo) vs 61 KB (GitHub correcto) → **21 KB de mejoras perdidas**
   - `PlanificacionView.vue`: ausente en local, 22 KB en GitHub
   - Resto de vistas: idénticas (sin cambios)
3. **Copié las versiones correctas** de GitHub a mi workspace.
4. **Reapliqué manualmente los 3 cambios de v0.9.15** sobre las versiones correctas.

## 🔧 Las 6 correcciones restauradas (todas ya estaban en GitHub)

### 1. ✅ Buscador arriba a la derecha
El buscador (`search-wrapper` con icono SVG de lupa) está en la barra superior derecha, separado de los filtros (que están en su propia tarjeta debajo). Mismo patrón que EQUIPOS.

### 2. ✅ Acciones con 4 botones SVG alineados
Cuatro botones en la celda Acciones, todos con SVGs (no emojis) y clases específicas:
- `.btn-view` (Ver detalle) — SVG de ojo, hover verde
- `.btn-edit` (Editar) — SVG de lápiz, hover azul
- `.btn-doc` (Documentos) — SVG de documento, hover cian
- `.btn-delete` (Eliminar) — SVG de papelera, hover rojo

Clase `actions-cell` aplicada al `<td>` para alineación horizontal con `display: flex`.

### 3. ✅ Iconos SVG (no emojis)
12 elementos `<svg>` en el archivo (buscador, 4 botones de acciones, drop-zone de importar, plantillas, etc.). Todos con `fill="currentColor"` para heredar el color.

### 4. ✅ Columna "Equipos" eliminada de la tabla
La columna `<th>Equipos</th>` y su `<td>` con `equipos-count` fueron removidos. La tabla ahora tiene 7 columnas: ID, Proveedor, Tipo, Vigencia, Estado, Costo, Acciones.

### 5. ✅ Botón "Cargar Excel" con plantillas
Botón verde "Cargar Excel" (clase `btn-import`) en la barra superior. Al hacer clic abre un modal con:
- Drop-zone con drag&drop
- Validación de extensión (.xlsx / .csv)
- Botones "Plantilla Excel" y "Plantilla CSV" (outline)
- Spinner de progreso
- Cards de resultados (Nuevos / Actualizados / Fallidos / Total)
- Lista de errores detallada

### 6. ✅ Selector chips/tags para Equipos Asociados
En Nuevo/Editar Contrato, el selector de equipos usa:
- Chips amarillos (`#fde68a`) con texto negro para equipos seleccionados
- Botón "×" en cada chip para quitar
- Buscador interno con lista desplegable de resultados
- Botón "+ Agregar" verde en cada resultado
- Botón "Limpiar selección" al lado del contador

## ✅ Cambios v0.9.15 preservados (reaplicados sobre la versión correcta)

### A. Vigencia: ambas fechas en negrita
- Clase `text-muted` reemplazada por `vigencia-fin` en la segunda fecha
- Estilo `.vigencia-fin { font-weight: 600; color: #1e293b; }`

### B. Inputs alineados en Nuevo/Editar
- `.input` mejorado con `box-sizing: border-box`, `min-height: 38px`, `line-height: 1.4`
- `select.input` con `appearance: none` + flecha SVG personalizada
- `input.input[type=date/number/text]` con `height: 38px`
- `textarea.input` con `min-height: 60px`
- Eliminado `textarea.input` duplicado

### C. Moneda solo BOB
- `const monedas = ['BOB']`
- `resetForm()`: `moneda: 'BOB'`
- `abrirEditar(c)`: `moneda: 'BOB'` (forzado, ignora valor anterior)
- Campo "Moneda" en formulario: `<input readonly>` con clase `input-readonly` (fondo gris, no editable)
- Backend (ya hecho en v0.9.15): `MONEDAS = {'BOB'}`, validación rechaza otras monedas con 422

## Archivos incluidos en este ZIP (3 archivos frontend)

| Archivo | Origen | Tamaño |
|---------|--------|--------|
| `frontend/src/views/ContratosView.vue` | GitHub + reaplicar v0.9.15 | 63 KB |
| `frontend/src/views/ProveedoresView.vue` | GitHub (con todas las mejoras) | 61 KB |
| `frontend/src/views/PlanificacionView.vue` | GitHub (por si acaso) | 22 KB |

**Nota**: Los archivos backend (`schemas/contrato.py`, `models/contratos.py`, `api/routes/contratos.py`) ya tienen los cambios de v0.9.15 aplicados y NO necesitan ser reemplazados. Están correctos en tu PC.

## Cómo aplicar

1. Copia los 3 archivos `.vue` a tu PC en `D:\cmmsbioai\frontend\src\views\` (reemplazando los existentes).
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5**.
4. Verás TODAS las mejoras restauradas + los cambios de v0.9.15:
   - Buscador arriba a la derecha ✓
   - 4 iconos SVG con colores en hover ✓
   - Botón Documentos presente ✓
   - Columna "Equipos" eliminada de la tabla ✓
   - Botón "Cargar Excel" con plantillas ✓
   - Selector chips/tags de equipos ✓
   - Vigencia ambas fechas en negrita ✓
   - Inputs alineados (misma altura) ✓
   - Moneda BOB fija (readonly) ✓

## 🔍 Recomendación para el futuro

**Para evitar que esto vuelva a pasar**, te recomiendo:

1. **Después de aplicar esta v0.9.16 en tu PC**, sube TODO a GitHub (`git add . && git commit -m "v0.9.16" && git push`). Así GitHub quedará como respaldo autoritativo.

2. **Antes de cada nueva sesión de cambios**, yo debería hacer `git pull` desde GitHub para asegurar que trabajo sobre la última versión. Lo haré automáticamente en lo sucesivo.

3. **No es necesario borrar todo y empezar**. El problema fue específico de ContratosView y ProveedoresView (ya corregidos). Las otras 13 vistas están idénticas y correctas.

## Versión
- **Versión**: v0.9.16
- **Fecha**: 2026-07-01
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
