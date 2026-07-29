# CMMS-BioAI v0.8.1 — Archivos Modificados

Esta carpeta contiene **únicamente los archivos modificados** en la versión v0.8.1 del proyecto CMMS-BioAI. La estructura de carpetas reproduce la del proyecto original para que puedas reemplazar los archivos directamente.

## Resumen de cambios

1. **Menú lateral reordenado** — Nuevo orden: Inicio → Equipos → Repuestos → Proveedores → Ordenes → Preventivo → Historial → Reportes → Usuarios → ? → ⚙️
2. **Campo `ciudad` añadido a Proveedor (RF10)** — Modelo, schema, migración automática, formulario, columna en tabla, modal de detalle.
3. **Importación masiva Excel/CSV de Proveedores** — Endpoints `/proveedores/plantilla-excel`, `/proveedores/plantilla-csv`, `/proveedores/import-excel` + botones en la UI + modal de resultados.
4. **Página de Ayuda actualizada** — RF10 con el nuevo campo `ciudad`, descripción completa, sección "RF10 - Relaciones con otros RF" explicando los vínculos futuros con RF01/RF04/RF09/RF03+RF05.
5. **README.md actualizado** — Versión v0.8.1, RF10 en módulos completados, tablas de `proveedor` y `contactoproveedor` con el campo `ciudad`, endpoints de Proveedores documentados, sección "RF10 — Gestión de Proveedores y Contactos" añadida, v0.8.1 en historial de versiones, roadmap actualizado.

## Archivos modificados (8 archivos)

| # | Ruta en el proyecto | Descripción |
|---|---------------------|-------------|
| 1 | `frontend/src/components/Navbar.vue` | Reorden del menú lateral |
| 2 | `frontend/src/views/ProveedoresView.vue` | Columna Ciudad, botones Importar/Plantilla, modal de resultados |
| 3 | `frontend/src/views/AyudaView.vue` | RF10 actualizado, sección de relaciones con otros RF |
| 4 | `backend/models/proveedores.py` | Campo `ciudad` añadido a `Proveedor` |
| 5 | `backend/schemas/proveedor.py` | Campo `ciudad` en Create/Update/Read |
| 6 | `backend/database.py` | Migración `_migrate_proveedor_ciudad()` |
| 7 | `backend/api/routes/proveedores.py` | Endpoints `plantilla-csv`, `plantilla-excel`, `import-excel` |
| 8 | `README.md` | Documentación completa de v0.8.1 y RF10 |

## Archivo adicional

- `Proveedores_Ejemplo.xlsx` (en `/home/z/my-project/download/`) — Excel de ejemplo con 20 proveedores biomédicos de Bolivia y 27 contactos asociados (datos inventados). Útil para probar la importación.

## Cómo aplicar los cambios en tu PC

### Opción A: Reemplazar archivos individualmente

Copia cada archivo desde esta carpeta a la misma ruta relativa dentro de tu proyecto `cmmsbioai/` local.

Ejemplo (asumiendo que tu proyecto está en `D:\Maestria\Modulo 6\CMMS\CMMS\`):

```
cmmsbioai-modificado/frontend/src/components/Navbar.vue
    → D:\Maestria\Modulo 6\CMMS\CMMS\frontend\src\components\Navbar.vue

cmmsbioai-modificado/backend/api/routes/proveedores.py
    → D:\Maestria\Modulo 6\CMMS\CMMS\backend\api\routes\proveedores.py

... (igual con los demás)
```

### Opción B: Descargar y descomprimir el ZIP completo

Te recomiendo descargar `cmmsbioai-v0.8.1-cambios.zip` (incluido en `/home/z/my-project/download/`) y descomprimirlo sobre tu carpeta del proyecto, aceptando sobreescribir los archivos.

## Cómo ejecutar la aplicación después de aplicar los cambios

1. **Detener** el backend y el frontend actuales (`Ctrl+C` en cada terminal).
2. **Reemplazar** los 8 archivos modificados en tu proyecto.
3. **NO borrar la base de datos** — la migración `ciudad` se aplica automáticamente al iniciar el backend. Todos los proveedores existentes quedarán con `ciudad = NULL`, pero podrás editarlos uno por uno o re-importarlos desde Excel.
4. **Iniciar el backend**:

   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

   En la consola deberías ver:
   ```
   ✅ Migración: columna 'ciudad' agregada a tabla 'proveedor'
   ```

   (Este mensaje aparece solo la primera vez, cuando la migración se aplica. En inicios posteriores no aparecerá porque la columna ya existe.)

5. **Iniciar el frontend** en otra terminal:

   ```bash
   cd frontend
   npm run dev
   ```

6. **Entrar a la aplicación** en http://localhost:5173 con `admin` / `admin123`.

7. **Verificar los cambios**:
   - El menú lateral debe tener el nuevo orden.
   - En `Proveedores`, deben aparecer los botones `📥 Plantilla` y `📤 Importar` junto a `+ Nuevo Proveedor`.
   - En la tabla, debe aparecer la columna `Ciudad` entre `Empresa` y `Telefono`.
   - En el modal `Nuevo Proveedor` / `Editar Proveedor`, debe aparecer el campo `Ciudad` (junto a Teléfono).
   - En `Ayuda` → pestaña `Requisitos RF`, debe aparecer la sección "RF10 - Proveedores: Relaciones con otros RF" al final.

## Cómo probar la importación de proveedores

1. Entra a `Proveedores` en el menú lateral.
2. Haz clic en `📥 Plantilla` para descargar la plantilla Excel oficial del sistema (con 20 proveedores de ejemplo) **O** usa el archivo `Proveedores_Ejemplo.xlsx` que está en esta carpeta de descarga.
3. Haz clic en `📤 Importar`, selecciona el archivo `.xlsx` y pulsa `Importar`.
4. Deberías ver un modal con:
   - **Creados: 20** (si la BD está vacía) o **Actualizados: 20** (si ya existían).
   - **Fallidos: 0**.
5. Cierra el modal y verás los 20 proveedores cargados en la tabla, con sus respectivas ciudades.
6. Para añadir contactos a un proveedor, haz clic en el icono de ojo (👁) en su fila → botón `+ Agregar Contacto`.

## Verificación post-instalación

| Item a verificar | Resultado esperado |
|------------------|-------------------|
| Menú lateral ordenado | Inicio → Equipos → Repuestos → Proveedores → Ordenes → Preventivo → Historial → Reportes → Usuarios → ? → ⚙️ |
| Página Proveedores | Botones Plantilla / Importar / + Nuevo Proveedor |
| Columna Ciudad en tabla | Visible entre Empresa y Teléfono |
| Formulario Nuevo/Editar Proveedor | Campo Ciudad presente |
| Modal Detalle del Proveedor | Campo Ciudad visible (si está seteado) |
| Importación de Excel | Carga 20 proveedores sin errores |
| Página Ayuda → RF | Sección "RF10 - Proveedores: Relaciones con otros RF" visible |
| Página Ayuda → Entidades → Proveedor | Campo `ciudad` listado entre los campos del RF10 |
| README.md | Versión v0.8.1, RF10 Completado, sección RF10 completa |

## ¿Problemas?

Si la migración no se aplica automáticamente (no ves el mensaje `✅ Migración: columna 'ciudad' agregada a tabla 'proveedor'`):

1. Detén el backend.
2. Verifica que el archivo `backend/database.py` sea el nuevo (con la función `_migrate_proveedor_ciudad`).
3. Reinicia el backend.

Si tienes proveedores antiguos sin ciudad, puedes:
- Editarlos uno por uno desde la UI (botón ✏️).
- O re-importarlos desde Excel si ya tienes un listado.
