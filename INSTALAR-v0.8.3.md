# CMMS-BioAI v0.8.3 — Capa 2 Mejorada (Recuperación)

Esta versión **arregla 3 bugs** críticos en el endpoint `/configuracion/recuperar` (Capa 2 — Escaneo y Recuperación) que impedían restaurar correctamente imágenes, OTs y documentos de OTs.

## 🐛 Bugs arreglados

### Bug #1: Imagen del equipo no se recuperaba aunque existiera en `.meta.json`
- **Antes**: Si el equipo ya existía en la BD pero con `imagen_ruta=NULL` (porque la BD se corrompió parcialmente), la recuperación lo saltaba por "ya existir" y nunca restauraba la imagen.
- **Ahora**: Si el registro existe pero le falta `imagen_ruta` y el `.meta.json` lo tiene, se sincroniza automáticamente. El escaneo también reporta estas imágenes faltantes antes de recuperar.

### Bug #2: Las Órdenes de Trabajo no se recuperaban
- **Antes**: El escaneo solo miraba carpetas `EQUIPOS/`, `REPUESTOS/`, `HERRAMIENTAS/`. No miraba el directorio `uploads/OT/` donde están los archivos `.txt` de referencia de cada OT. Resultado: 0 OTs recuperadas.
- **Ahora**: El escaneo lee cada `OTxxxx_Titulo_Modelo_Serie.txt` en `uploads/OT/`, extrae el ID, título, prioridad, descripción de la falla y el equipo asociado, y reconstruye la OT en la BD (con estado "Abierta" por defecto).

### Bug #3: Los documentos de las OTs no se recuperaban
- **Antes**: El escaneo solo miraba la carpeta `DOC/` de cada entidad. No miraba las carpetas `OT/OTxxxx_Titulo_Modelo_Serie/` dentro de cada equipo (donde se guardan los documentos asociados a cada OT). Resultado: los documentos de OTs se perdían en la recuperación.
- **Ahora**: El escaneo también itera sobre las carpetas `OT/OTxxxx/` de cada equipo y lee sus `.meta.json` para recuperar los documentos huérfanos, asociándolos correctamente a la OT correspondiente.

## 📊 Escenario de prueba (verificado)

Con un escenario simulado:
- Equipo ID=1 en BD sin `imagen_ruta`, con `.meta.json` que SÍ la tiene
- Herramienta ID=1 en BD sin `imagen_ruta`, con `.meta.json` que SÍ la tiene
- OT ID=1 NO en BD, pero existe `.txt` + carpeta con `.meta.json` de documento
- 3 documentos en archivos (1 de equipo, 1 de herramienta, 1 de OT), ninguno en BD

**Resultado antes (v0.8.2):**
```
recuperados: {equipos: 0, repuestos: 0, herramientas: 0, documentos: 2}
```
- 0 imágenes sincronizadas
- 0 OTs recuperadas
- El documento de la OT (ID=10) se perdía

**Resultado ahora (v0.8.3):**
```
recuperados: {equipos: 0, repuestos: 0, herramientas: 0, ordenes: 1, documentos: 3, imagenes_sincronizadas: 2}
```
- 2 imágenes sincronizadas (equipo + herramienta)
- 1 OT recuperada con su título, prioridad y equipo asociado
- 3 documentos recuperados (equipo + herramienta + OT) correctamente asociados

## 📁 Archivos modificados (5 archivos en v0.8.3)

| Archivo | Cambio |
|---------|--------|
| `backend/api/routes/configuracion.py` | Endpoints `/escanear` y `/recuperar` reescritos: agregan soporte para OTs (`.txt`), documentos en `OT/OTxxxx/`, sincronización de `imagen_ruta`, y nuevas funciones helper `_parse_ot_txt_referencia`, `_escanear_documentos_carpeta`, `_recuperar_documentos_carpeta` |
| `frontend/src/views/ConfiguracionView.vue` | UI mejorada: muestra "Imágenes faltantes", sección de OTs en detalle, modal de resultados con conteo detallado (equipos/repuestos/herramientas/OTs/documentos/imagenes_sincronizadas), botón "Recuperar / Sincronizar" aparece también cuando solo hay imágenes faltantes |
| `frontend/src/views/AyudaView.vue` | Sección "Capas de Recuperación" actualizada con detalles de qué hace la Capa 2 en v0.8.3 |
| `README.md` | Versión v0.8.3, sección "Capa 2" reescrita con explicación detallada de qué hace el escaneo y limitaciones conocidas, v0.8.3 en historial de versiones |

> **Nota**: Esta entrega también incluye los archivos de v0.8.1 y v0.8.2 por si aún no los aplicaste. Si ya tienes v0.8.2 instalado, solo necesitas actualizar los 4 archivos principales de v0.8.3.

## 🚀 Cómo aplicar los cambios

### Si ya tienes v0.8.2 instalado (actualización mínima)

Solo necesitas copiar **4 archivos**:

```
cmmsbioai-modificado/backend/api/routes/configuracion.py  → backend/api/routes/
cmmsbioai-modificado/frontend/src/views/ConfiguracionView.vue  → frontend/src/views/
cmmsbioai-modificado/frontend/src/views/AyudaView.vue  → frontend/src/views/
cmmsbioai-modificado/README.md  → (raíz del proyecto)
```

### Si vienes de v0.8.0 o anterior (actualización completa)

Descomprime todo el contenido de `cmmsbioai-v0.8.3-cambios.zip` sobre la raíz de tu proyecto `cmmsbioai/`, aceptando sobrescribir los archivos.

### Después de aplicar los cambios

1. **Detén** el backend y el frontend actuales.
2. **Reemplaza** los archivos.
3. **Inicia el backend**:

   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

4. **Inicia el frontend**:

   ```bash
   cd frontend
   npm run dev
   ```

5. **Entra** a http://localhost:5173 con `admin` / `admin123`.

## ✅ Cómo verificar que los bugs están arreglados

### Verificar Bug #1 (sincronización de imágenes)

1. Ve a **Configuración** → pestaña **Capa 2**.
2. Haz clic en **🔍 Escanear .meta.json**.
3. Si tienes equipos/repuestos/herramientas con `.meta.json` que tengan `imagen_ruta` pero la BD no, verás una tarjeta amarilla de **"Imágenes faltantes"** con el conteo.
4. En el detalle por tipo (equipos, repuestos, herramientas), verás una lista naranja indicando qué registros tienen imagen faltante y qué ruta debería tener.
5. Haz clic en **🔄 Recuperar / Sincronizar**.
6. En el resultado, verás **"X imágenes sincronizadas"**.
7. Ve a **Equipos** → el equipo afectado → debería mostrar la imagen.

### Verificar Bug #2 (recuperación de OTs)

1. Ve a **Configuración** → pestaña **Capa 2** → **🔍 Escanear .meta.json**.
2. Verás una nueva sección **"ordenes"** en el detalle.
3. Si tienes archivos `.txt` en `uploads/OT/` cuyas OTs no están en BD, aparecerán como huérfanas.
4. Haz clic en **🔄 Recuperar / Sincronizar**.
5. En el resultado, verás **"X OTs creadas"**.
6. Ve a **Órdenes** → las OTs recuperadas aparecerán con estado "Abierta".

### Verificar Bug #3 (documentos de OTs)

1. Ve a **Configuración** → pestaña **Capa 2** → **🔍 Escanear .meta.json**.
2. En el detalle de **"documentos"**, los documentos asociados a OTs (carpeta `OT/OTxxxx/`) ahora aparecen listados.
3. Haz clic en **🔄 Recuperar / Sincronizar**.
4. En el resultado, verás **"X documentos creados"** (incluyendo los de OTs).
5. Ve a **Órdenes** → abre una OT recuperada → sus documentos aparecerán en el modal.

## ⚠️ Limitaciones conocidas (no son bugs)

Estas son limitaciones del diseño actual de los `.meta.json`/`.txt`, no bugs:

1. **Estado de OTs recuperadas**: siempre se crean con estado "Abierta" (no se puede saber el estado original desde el `.txt`).
2. **Campos de cierre de OT**: `acciones_realizadas`, `tiempo_real_invertido`, `costo_adicional`, `costos_adicionales` no se restauran (no están en el `.txt`).
3. **Repuestos utilizados** (`OtRepuestoUtilizado`): no se recuperan (no hay `.meta.json` para esta relación N:M).
4. **Historial de mantenimiento** (`EventoHistorial`): no se recupera (no tiene `.meta.json`).

Si en el futuro quieres mejorar esto, se podría:
- Agregar más campos al `.txt` de referencia de OT (estado, acciones, tiempo, costos).
- Crear `.meta.json` para `OtRepuestoUtilizado` y `EventoHistorial`.

## 📦 Archivos para descargar

Ubicación: `/home/z/my-project/download/`

1. **`cmmsbioai-v0.8.3-cambios.zip`** (140 KB aprox) — ZIP con todos los archivos modificados (v0.8.1 + v0.8.2 + v0.8.3) + esta guía.
2. **`cmmsbioai-modificado/`** — Carpeta con los archivos sueltos (misma estructura que el ZIP).
3. **`Proveedores_Ejemplo.xlsx`** — Excel con 20 proveedores de ejemplo (de v0.8.1, sigue disponible).

## 📋 Pendientes para la próxima sesión

| # | Pendiente | Notas |
|---|-----------|-------|
| 3 | **Revisión de campos de RF01** | Tú estabas analizando — cuando me pases tus notas atacamos |
| 4 | **Migración a FK de proveedores** (RF10 → RF01/RF04/RF09) | Convertir `proveedor_principal` y `proveedor_ultimo` en FK a `Proveedor.id` |
| 5 | **Mejorar .txt de OT** | Agregar estado, acciones, tiempo y costos para recuperar OTs más completas |
| 6 | **`.meta.json` para OtRepuestoUtilizado** | Permitir recuperar los repuestos utilizados en cada OT |
| 7 | **`.meta.json` para EventoHistorial** | Permitir recuperar el historial de mantenimiento |
