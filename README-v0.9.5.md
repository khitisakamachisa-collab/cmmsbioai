# CMMS-BioAI v0.9.5 — Ajustes visuales en página Equipos

## Cambios solicitados y aplicados

### 1. Búsqueda por número de serie
- **Placeholder actualizado**: antes decía `Nombre, marca, modelo...`, ahora dice
  `Nombre, marca, modelo, núm. serie, núm. material...`.
- **Lógica de filtrado**: ya estaba implementada desde v0.9.0 (la función
  `filteredEquipos` ya incluye `numero_serie` y `numero_material` en la
  comparación), pero el usuario no lo sabía porque el placeholder no lo indicaba.
  Ahora es visible para el usuario final.

### 2. Columna "Condición" eliminada de la tabla
- Se elimina la columna **Condición** del encabezado (`<thead>`) y de cada fila.
- Se ajusta `colspan` de la fila vacía de `8` a `7`.
- **El filtro "Condición" se mantiene** en la barra de filtros (no se toca).
- El campo `condicion_origen` sigue presente en el formulario de crear/editar
  y se sigue guardando en la base de datos. Solo dejaba de mostrarse en la
  tabla para reducir ruido visual.

### 3. Iconos de Acciones con colores por defecto
Antes todos los botones eran gris claro (`#f0f2f5`) y solo mostraban color al
pasar el cursor. Ahora cada acción tiene su color identificable desde el
principio:

| Acción            | Clase          | Color por defecto (fondo / ícono) | Color en hover        |
|-------------------|----------------|------------------------------------|------------------------|
| 👁 Ver Detalles   | `.btn-view`    | Verde claro `#dcfce7` / Verde oscuro `#15803d` | Verde sólido `#16a34a` + ícono blanco |
| ✏️ Editar         | `.btn-edit`    | Azul claro `#dbeafe` / Azul oscuro `#1d4ed8` | Azul sólido `#2563eb` + ícono blanco |
| 🗑 Eliminar       | `.btn-delete`  | Rojo claro `#fee2e2` / Rojo oscuro `#b91c1c` | Rojo sólido `#dc2626` + ícono blanco |
| 🕒 Ver Historial  | `.btn-history` | Morado claro `#ede9fe` / Morado oscuro `#6d28d9` | Morado sólido `#7c3aed` + ícono blanco |
| 📄 Documentos     | `.btn-doc`     | Cian claro `#cffafe` / Cian oscuro `#0e7490` | Cian sólido `#0891b2` + ícono blanco |

Esto mejora la usabilidad: el usuario identifica cada acción por color sin
necesidad de leer el tooltip.

## Archivos modificados

| Archivo | Acción |
|---------|--------|
| `frontend/src/views/EquiposView.vue` | **EDITADO** — 3 cambios en 1 archivo |

## Cómo aplicar

1. Copia el archivo `frontend/src/views/EquiposView.vue` a tu copia local.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador (Ctrl+F5 para limpiar caché).
4. Verás:
   - Placeholder del buscador menciona "núm. serie, núm. material".
   - Columna "Condición" desaparece de la tabla (pero sigue en filtros).
   - Iconos de Acciones con colores pastel identificables.

## Versión
- **Versión**: v0.9.5
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
