# CMMS-BioAI v0.9.6 — Página Proveedores rediseñada

## Cambios solicitados y aplicados

### 1. Botones "Plantilla" e "Importar" ahora idénticos a Equipos
- Se eliminan los 2 botones antiguos (`📥 Plantilla` y `📤 Importar`) de la barra superior.
- Se reemplazan por un único botón verde **"Cargar Excel"** con icono (igual a Equipos).
- Las plantillas se descargan **desde dentro del modal de importación** (botones "Plantilla Excel" y "Plantilla CSV" outline).
- El modal de importar ahora tiene:
  - **Drop-zone con drag & drop** (arrastrar archivo o clic para seleccionar).
  - **Validación de extensión** (.xlsx / .csv).
  - **Spinner de progreso** mientras procesa.
  - **Cards de resultados** con 4 columnas: Nuevos / Actualizados / Fallidos / Total.
  - **Lista de errores detallada** (fila, empresa, mensaje).
  - **Botón "Importar otro archivo"** para resetear y volver a empezar.

### 2. Modal "Ver Detalle" (ojo) → SOLO LECTURA
- Se eliminan del modal los botones de **editar y eliminar contactos**.
- Se elimina el botón **"Editar Empresa"** del pie del modal.
- Se elimina el botón **"+ Agregar Contacto"** del encabezado de contactos.
- Solo queda un botón **"Cerrar"**. El "ojo" ahora cumple su función semántica: **visualizar sin modificar**.

### 3. Nuevo icono "Contactos" (persona) para gestión CRUD separada
- Se agrega un nuevo botón en la columna **Acciones** de cada proveedor, entre Editar y Eliminar.
- Icono: persona (cabecera + hombros) de Bootstrap Icons.
- Color: **naranja** (`#ffedd5` fondo / `#c2410c` ícono).
- Al hacer clic abre un **modal "Gestionar Contactos"** nuevo con:
  - Lista completa de contactos del proveedor.
  - Botón **"+ Agregar Contacto"**.
  - Cada contacto con botones de **editar (azul)** y **eliminar (rojo)**.
  - Soporta múltiples contactos por proveedor (N:M con la entidad `contactoproveedor`).
  - Al guardar/eliminar, se refresca automáticamente el modal y la tabla principal.

### 4. Iconos de Acciones con colores por defecto
Antes todos los botones eran grises (`#f0f2f5`) y solo mostraban color al hacer hover. Ahora cada acción tiene su color identificable desde el inicio:

| Acción            | Clase            | Color por defecto (fondo / ícono)     | Color en hover                     |
|-------------------|------------------|---------------------------------------|-------------------------------------|
| 👁 Ver Detalle    | `.btn-view`      | Verde claro `#dcfce7` / `#15803d`     | Verde sólido `#16a34a` + blanco     |
| ✏️ Editar Empresa | `.btn-edit`      | Azul claro `#dbeafe` / `#1d4ed8`      | Azul sólido `#2563eb` + blanco      |
| 👤 Contactos      | `.btn-contactos` | Naranja claro `#ffedd5` / `#c2410c`   | Naranja sólido `#ea580c` + blanco   |
| 🗑 Eliminar       | `.btn-delete`    | Rojo claro `#fee2e2` / `#b91c1c`      | Rojo sólido `#dc2626` + blanco      |

Los iconos pequeños dentro del modal de contactos (editar/eliminar contacto) también tienen la misma paleta azul/roja.

## Archivos modificados

| Archivo | Acción |
|---------|--------|
| `frontend/src/views/ProveedoresView.vue` | **EDITADO** — 4 cambios en 1 archivo |

## Cómo aplicar

1. Copia el archivo `frontend/src/views/ProveedoresView.vue` a tu copia local.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador (Ctrl+F5 para limpiar caché).
4. Verás:
   - Un solo botón verde "Cargar Excel" (reemplaza a Plantilla + Importar).
   - Modal de importar con drop-zone y spinner.
   - 4 iconos de color en cada fila: ojo (verde) / lápiz (azul) / persona (naranja) / papelera (roja).
   - El "ojo" ya NO permite editar ni eliminar (solo visualizar).
   - El icono "persona" abre el modal de gestión de contactos con CRUD completo.

## Validación backend (TestClient)
- `GET /proveedores/con-contactos` → 200 ✓
- `POST /proveedores/` → 201 ✓
- `POST /proveedores/{id}/contactos` → 201 ✓ (crea contacto)
- `GET /proveedores/{id}/contactos` → 200 ✓ (lista contactos del proveedor)
- `DELETE /proveedores/{id}` → 204 ✓ (elimina en cascada contactos + proveedor)

## Versión
- **Versión**: v0.9.6
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
