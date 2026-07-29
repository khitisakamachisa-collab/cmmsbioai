# CMMS-BioAI v0.8.2 — Plantillas Estáticas

Esta carpeta contiene los archivos modificados para la versión **v0.8.2** del proyecto CMMS-BioAI. La estructura de carpetas reproduce la del proyecto original para que puedas reemplazar los archivos directamente.

## Resumen de cambios en v0.8.2

**Migración de plantillas Excel/CSV del backend a archivos estáticos en el frontend.**

- Las plantillas ya **no se generan dinámicamente** en cada descarga.
- Ahora son **8 archivos estáticos** en `frontend/public/plantillas/` que Vite sirve directamente.
- El frontend descarga desde `/plantillas/<nombre>` **sin llamar al backend** → más rápido, sin carga en el backend, funciona aunque el backend esté caído.
- Los endpoints `/plantilla-excel` y `/plantilla-csv` del backend se **mantienen como respaldo** (con aviso en su docstring) y para documentación Swagger.
- Las plantillas se pueden **editar directamente** en Excel/CSV sin tocar código Python.

## Archivos incluidos (19 archivos)

### Plantillas estáticas (8 archivos nuevos)

| Archivo | Contenido |
|---------|-----------|
| `frontend/public/plantillas/plantilla_equipos.xlsx` | 15 equipos biomédicos de ejemplo + hoja de instrucciones |
| `frontend/public/plantillas/plantilla_equipos.csv` | Igual que el xlsx pero en CSV |
| `frontend/public/plantillas/plantilla_repuestos.xlsx` | 20 repuestos de laboratorio + hoja de instrucciones |
| `frontend/public/plantillas/plantilla_repuestos.csv` | Igual que el xlsx pero en CSV |
| `frontend/public/plantillas/plantilla_herramientas.xlsx` | 10 herramientas de taller + hoja de instrucciones |
| `frontend/public/plantillas/plantilla_herramientas.csv` | Igual que el xlsx pero en CSV |
| `frontend/public/plantillas/plantilla_proveedores.xlsx` | 20 proveedores biomédicos de Bolivia + hoja de instrucciones |
| `frontend/public/plantillas/plantilla_proveedores.csv` | Igual que el xlsx pero en CSV |

### Vistas Vue modificadas (4 archivos)

| Archivo | Cambio |
|---------|--------|
| `frontend/src/views/EquiposView.vue` | `downloadTemplate()` y `downloadTemplateCSV()` ahora descargan desde `/plantillas/` |
| `frontend/src/views/InventarioView.vue` | `downloadTemplate()`, `downloadTemplateCSV()` y `herrDownloadTemplate()` ahora descargan desde `/plantillas/` |
| `frontend/src/views/ProveedoresView.vue` | `descargarPlantillaExcel()` y `descargarPlantillaCSV()` ahora descargan desde `/plantillas/` |
| `frontend/src/views/AyudaView.vue` | Módulos actualizados mencionando plantillas estáticas; sección Archivos incluye `frontend/public/plantillas/` |

### Backend con avisos de respaldo (4 archivos)

| Archivo | Cambio |
|---------|--------|
| `backend/api/routes/equipos.py` | Aviso `[RESPALDO]` en docstring de `/plantilla-csv` y `/plantilla-excel` |
| `backend/api/routes/repuestos.py` | Aviso `[RESPALDO]` en docstring de `/plantilla-csv` y `/plantilla-excel` |
| `backend/api/routes/herramientas.py` | Aviso `[RESPALDO]` en docstring de `/plantilla-excel` |
| `backend/api/routes/proveedores.py` | Aviso `[RESPALDO]` en docstring de `/plantilla-csv` y `/plantilla-excel` |

### Documentación y scripts (3 archivos)

| Archivo | Descripción |
|---------|-------------|
| `README.md` | Versión v0.8.2, estructura de proyecto actualizada con `public/plantillas/`, observación técnica sobre plantillas estáticas, v0.8.2 en historial de versiones |
| `scripts/generar_plantillas_estaticas.py` | Script para regenerar los 8 archivos estáticos cuando se actualicen los modelos |
| `INSTALAR-v0.8.2.md` | Esta guía de instalación |

## Cómo aplicar los cambios en tu PC

### Opción A: Reemplazar archivos individualmente

Copia cada archivo desde esta carpeta a la misma ruta relativa dentro de tu proyecto `cmmsbioai/` local.

### Opción B: Descargar y descomprimir el ZIP completo

Te recomiendo descargar `cmmsbioai-v0.8.2-cambios.zip` y descomprimirlo sobre tu carpeta del proyecto, aceptando sobreescribir los archivos.

## Cómo ejecutar la aplicación después de aplicar los cambios

1. **Detener** el backend y el frontend actuales (`Ctrl+C` en cada terminal).
2. **Reemplazar** los 19 archivos modificados en tu proyecto.
3. **Iniciar el backend**:

   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

4. **Iniciar el frontend** en otra terminal:

   ```bash
   cd frontend
   npm run dev
   ```

5. **Entrar a la aplicación** en http://localhost:5173 con `admin` / `admin123`.

6. **Verificar los cambios**:
   - Entra a **Equipos** → clic en **Plantilla Excel** → debe descargar `CMMS-BioAI_Plantilla_Equipos.xlsx` (sin demora, ya que es archivo estático).
   - Entra a **Equipos** → clic en **Plantilla CSV** → debe descargar `CMMS-BioAI_Plantilla_Equipos.csv`.
   - Entra a **Repuestos** → mismo comportamiento con las 2 plantillas.
   - Entra a **Herramientas** (dentro de Inventario) → clic en **Plantilla Excel** → descarga.
   - Entra a **Proveedores** → clic en **Plantilla** → descarga `CMMS-BioAI_Plantilla_Proveedores.xlsx`.
   - Entra a **Ayuda** → pestaña **Archivos** → debe aparecer la fila `frontend/public/plantillas/` con la descripción "Plantillas Excel/CSV descargables desde la UI".

## ¿Cómo saber si está funcionando?

**Forma rápida de verificar que las plantillas estáticas funcionan:**

1. Abre el **Inspector del navegador** (F12) → pestaña **Network** (Red).
2. Entra a `Equipos` y haz clic en `Plantilla Excel`.
3. Debes ver una petición a `http://localhost:5173/plantillas/plantilla_equipos.xlsx` (NO a `http://127.0.0.1:8000/equipos/plantilla-excel`).
4. La descarga debe ser **instantánea** (no hay delay por la llamada al backend).

## Cómo modificar una plantilla en el futuro

Tienes dos opciones:

### Opción 1: Editar el archivo directamente

1. Abre `frontend/public/plantillas/plantilla_<entidad>.xlsx` en Excel/LibreOffice.
2. Modifica los datos demo o agrega filas nuevas.
3. Guarda el archivo. **Listo.** La próxima vez que un usuario descargue la plantilla, recibirá la versión modificada.

> ⚠️ **No cambies los encabezados de columna en la fila 1** — el endpoint de importación los usa para mapear los campos. Si necesitas agregar un campo nuevo, primero actualiza el modelo en el backend, luego el endpoint de importación, y finalmente la plantilla.

### Opción 2: Regenerar todos los archivos con el script

Si haces cambios en los modelos del backend y quieres que las plantillas reflejen los nuevos campos:

1. Edita el script `scripts/generar_plantillas_estaticas.py` (cambia encabezados, datos demo, anchos de columna).
2. Ejecútalo:

   ```bash
   python scripts/generar_plantillas_estaticas.py
   ```

3. Los 8 archivos en `frontend/public/plantillas/` se regeneran automáticamente.

> El script está pensado para que sea **la única fuente de verdad** de las plantillas. Si en el futuro agregas un campo al modelo `Proveedor` (por ejemplo `pais`), solo tienes que: (a) agregarlo a la lista `PROV_HEADERS`, (b) agregarlo a cada fila de `PROV_DATOS`, (c) ejecutar el script.

## Verificación post-instalación

| Item a verificar | Resultado esperado |
|------------------|-------------------|
| Botón "Plantilla Excel" en Equipos | Descarga instantánea sin llamada al backend |
| Botón "Plantilla CSV" en Equipos | Descarga instantánea sin llamada al backend |
| Botón "Plantilla Excel" en Repuestos | Descarga instantánea sin llamada al backend |
| Botón "Plantilla Excel" en Herramientas | Descarga instantánea sin llamada al backend |
| Botón "Plantilla" en Proveedores | Descarga instantánea sin llamada al backend |
| Ayuda → Archivos | Fila `frontend/public/plantillas/` visible |
| README.md | Versión v0.8.2, mención de plantillas estáticas |
| Backend `/docs` (Swagger) | Endpoints `/plantilla-excel` y `/plantilla-csv` siguen visibles con aviso `[RESPALDO]` |

## ¿Problemas?

**Si la plantilla no descarga o descarga un archivo vacío/corrupto:**

1. Verifica que el archivo existe en `frontend/public/plantillas/`.
2. Verifica que Vite está corriendo (`npm run dev`).
3. Abre la URL directamente en el navegador: `http://localhost:5173/plantillas/plantilla_equipos.xlsx`. Debe descargar el archivo.
4. Si no descarga, revisa la consola del navegador (F12) por errores 404.

**Si descarga la plantilla vieja (con datos antiguos):**

1. Reinicia Vite (`Ctrl+C` y `npm run dev` otra vez) — a veces el navegador cachea los archivos estáticos.
2. Fuerza recarga con `Ctrl+Shift+R` o `Cmd+Shift+R`.

## Pendientes siguientes (roadmap)

- [ ] **Capa 2 — Escaneo no recupera imágenes** — diagnosticar por qué
- [ ] **Revisión de campos de RF01** — tú estabas analizando
- [ ] **Migración a FK de proveedores** (RF10 → RF01/RF04/RF09) — convertir `proveedor_principal` y `proveedor_ultimo` en FK a `Proveedor.id`
