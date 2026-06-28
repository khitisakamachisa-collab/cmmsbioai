# CMMS-BioAI v0.9.9 — Contratos: chips/tags + acciones horizontal + botones de color

## Cambios solicitados y aplicados

### 1. Selector de Equipos Asociados: chips/tags (Opción B)
Se reemplazó el checkbox grid por un selector moderno tipo "chips/tags" que escala bien para listas de 100+ equipos:

**Flujo de uso:**
1. El usuario escribe en el buscador (nombre, modelo, serie o marca).
2. Aparece una lista desplegable de equipos que coinciden y NO están seleccionados.
3. Al hacer clic en un equipo de la lista (o en su botón "+ Agregar"), se agrega como **chip** arriba.
4. La lista de resultados se oculta automáticamente tras agregar.
5. Para quitar un equipo, se hace clic en la "×" del chip.
6. Botón **"Limpiar selección"** (al lado del contador) para quitar todos de una vez.

**Elementos visuales:**
- **Chips container** (caja superior con scroll si hay muchos): muestra los equipos seleccionados como chips azules con "×" para quitar.
- **Buscador**: input con icono lupa y botón "×" para limpiar.
- **Resultados**: lista desplegable debajo del buscador con hover verde y botón "+ Agregar" por ítem.
- **Contador**: "X seleccionados de Y" + botón "Limpiar selección".
- Estados vacíos: "No hay equipos seleccionados" o "No se encontraron equipos con '<búsqueda>'".

### 2. Acciones en horizontal
Antes los iconos de Acciones (ojo, lápiz, papelera) se mostraban en vertical dentro de la celda. Ahora están en **horizontal** gracias a la clase `actions-cell` agregada al `<td>`, que aplica `display: flex; gap: 0.5rem; align-items: center; justify-content: flex-end;`.

### 3. Botones de exportar con color sólido armónico
Antes los botones "📤 Excel" y "📄 CSV" usaban la clase `btn-secondary` (gris claro). Ahora tienen colores sólidos que combinan con el verde de "Cargar Excel" y el azul de "+ Nuevo Contrato":

| Botón              | Clase                | Color por defecto | Color en hover |
|--------------------|----------------------|-------------------|----------------|
| 📤 Exportar Excel  | `.btn-export-excel`  | Ámbar `#f59e0b`   | `#d97706`      |
| 📄 Exportar CSV    | `.btn-export-csv`    | Cian `#0891b2`    | `#0e7490`      |
| 📥 Cargar Excel    | `.btn-import`        | Verde `#27ae60`   | `#219a52`      |
| + Nuevo Contrato   | `.btn-primary`       | Azul `#3b82f6`    | `#2563eb`      |

Los 4 botones forman una paleta armónica: verde (importar), ámbar (exportar Excel), cian (exportar CSV), azul (crear). Todos son distinguibles a primera vista.

## Archivos modificados

| Archivo | Acción |
|---------|--------|
| `frontend/src/views/ContratosView.vue` | **EDITADO** — 3 cambios en 1 archivo |

## Cómo aplicar

1. Copia el archivo `frontend/src/views/ContratosView.vue` a tu copia local.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5** (limpiar caché).
4. Verás:
   - En "+ Nuevo Contrato" → modal con selector chips/tags para Equipos Asociados.
   - En la tabla → iconos de Acciones en horizontal.
   - En la barra superior → botones de exportar ámbar (Excel) y cian (CSV), sólidos.

## Versión
- **Versión**: v0.9.9
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
