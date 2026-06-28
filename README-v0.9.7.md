# CMMS-BioAI v0.9.7 — Ajustes en Proveedores (modales + iconos)

## Cambios solicitados y aplicados

### 1. Cerrar modal padre al abrir el de "Nuevo/Editar Contacto"
Antes, al hacer clic en **"+ Agregar Contacto"** o en el botón de **editar contacto**, el modal de gestión de contactos se quedaba abierto detrás del modal de edición, obligando al usuario a cerrarlo manualmente. Ahora:

- **`openCreateContacto`** y **`openEditContacto`** ahora cierran automáticamente `showContactosModal` y `showDetailModal` antes de abrir `showContactoModal`. De esta forma, el modal de "Nuevo/Editar Contacto" queda al frente sin obstrucciones.
- **`saveContacto`** ahora **reabre** el modal de gestión de contactos (`showContactosModal = true`) después de guardar exitosamente, para que el usuario vuelva a ver la lista actualizada de contactos en lugar de quedar sin contexto.

### 2. Iconos grises por defecto, color solo en hover
Antes los iconos de Acciones mostraban colores pastel desde el inicio. Ahora vuelven al estilo sobrio:

- **Estado por defecto**: fondo gris claro `#f0f2f5`, ícono gris oscuro `#555` (como era originalmente).
- **Estado hover**: el fondo se vuelve sólido del color correspondiente y el ícono se pone blanco:

| Acción            | Clase            | Hover (fondo / ícono)               |
|-------------------|------------------|--------------------------------------|
| 👁 Ver Detalle    | `.btn-view`      | Verde sólido `#16a34a` + blanco     |
| ✏️ Editar Empresa | `.btn-edit`      | Azul sólido `#2563eb` + blanco      |
| 👤 Contactos      | `.btn-contactos` | Naranja sólido `#ea580c` + blanco   |
| 🗑 Eliminar       | `.btn-delete`    | Rojo sólido `#dc2626` + blanco      |

Los iconos pequeños dentro del modal de contactos (`.btn-edit-sm`, `.btn-delete-sm`) también vuelven a gris por defecto y muestran color solo en hover (azul / rojo respectivamente).

## Archivos modificados

| Archivo | Acción |
|---------|--------|
| `frontend/src/views/ProveedoresView.vue` | **EDITADO** — 2 cambios en 1 archivo |

## Cómo aplicar

1. Copia el archivo `frontend/src/views/ProveedoresView.vue` a tu copia local.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador (Ctrl+F5 para limpiar caché).
4. Verás:
   - Al hacer clic en **"+ Agregar Contacto"** o en editar contacto, el modal de gestión se cierra y abre el de edición.
   - Al guardar, vuelve a abrir el modal de gestión con la lista actualizada.
   - Los iconos de Acciones están grises por defecto y solo muestran color al pasar el mouse.

## Versión
- **Versión**: v0.9.7
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
