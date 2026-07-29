# CMMS-BioAI v0.9.12 — Fix hover Equipos + Documentos Contratos + chips negros

## Cambios solicitados y aplicados

### 1. 🐛 FIX: Equipos — hover de iconos no cambiaba de color
**Síntoma**: Al pasar el mouse sobre los iconos de Acciones en Equipos, NO cambiaban al color correspondiente (verde/azul/rojo/morado/cian), se quedaban en gris.

**Causa raíz**: Existía una regla de "compatibilidad" `.btn-icon:hover { background: #dfe2e6; color: #000; }` (línea 1469 del archivo original) que venía **después** de las reglas específicas `.btn-view:hover`, `.btn-edit:hover`, etc. Por la cascada de CSS, cuando dos reglas tienen la misma especificidad, gana la última → esa regla genérica pisaba los colores específicos.

**Fix**: Eliminada la regla `.btn-icon:hover` del bloque de compatibilidad. Se dejó un comentario explicando por qué NO se debe agregar. Las reglas `.btn-view:hover`, `.btn-edit:hover`, `.btn-delete:hover`, `.btn-history:hover`, `.btn-doc:hover` ahora funcionan correctamente.

### 2. Contratos — DOCUMENTACIÓN
Se agregó la capacidad de subir y gestionar documentos para contratos (igual que Equipos, OTs, Repuestos y Herramientas).

**Backend (3 archivos)**:
- `models/documentos.py`: agregado campo `contrato_id: Optional[int] = Field(default=None, foreign_key="contrato.id")`.
- `database.py`: agregada migración `_migrate_documento_herramienta_id()` para añadir la columna `contrato_id` a la tabla `documentoadjunto` en BDs existentes. Se ejecuta automáticamente al iniciar el backend.
- `api/routes/documentos.py`:
  - Importado `Contrato` de `models.contratos`.
  - `POST /documentos/` acepta `contrato_id: Optional[int] = Form(None)`.
  - `GET /documentos/` acepta `contrato_id: Optional[int] = Query(None)` como filtro.
  - Los documentos de contratos se guardan en `uploads/CONTRATOS/C0001_Proveedor_Tipo/DOC/`.
  - Respuestas POST y GET incluyen `contrato_id` en el JSON.

**Frontend (2 archivos)**:
- `components/DocumentosAdjuntos.vue`: agregado prop `contratoId: { type: Number, default: null }`. Las funciones `fetchDocumentos`, `uploadFiles` y el `watch` ahora consideran este prop.
- `views/ContratosView.vue`:
  - Importado componente `DocumentosAdjuntos`.
  - Agregadas variables `showDocsModal` y `docsContrato`.
  - Agregada función `abrirDocs(c)` que abre el modal.
  - Agregado botón "📄 Documentos" (clase `.btn-doc`) en la columna Acciones de cada contrato, entre Editar y Eliminar.
  - Agregado estilo `.btn-doc:hover { background: #0891b2; color: #ffffff; }` (cian).
  - Agregado modal "Documentos — Contrato #X" que renderiza `<DocumentosAdjuntos :contrato-id="docsContrato.id" />`.

**Validación backend con TestClient**:
- Crear proveedor → crear contrato → GET /documentos/?contrato_id=X vacío (Count: 0) ✓
- POST /documentos/ con contrato_id=3 → 200, devuelve contrato_id: 3 ✓
- GET /documentos/?contrato_id=3 → 1 documento con contrato_id: 3 ✓

### 3. Contratos — Equipos Asociados en "ver" más llamativos
**Problema**: En el modal "ojo" (detalle), los equipos asociados tenían fondo gris claro (`#f1f5f9`), muy similar al fondo general.

**Fix**:
- Fondo cambiado a **amarillo cálido** `#fef3c7` con borde `#fcd34d`.
- Borde redondeado `border-radius: 6px`.
- **Todo el texto en negro** (`#000000`): nombre, modelo, SN y ubicación.
- Cambiados los `<small class="text-muted">` por `<strong class="equipo-tag-detalle">` con `color: #000000` y `font-weight: 600`.
- Agregada regla `.equipo-tag strong { color: #000000; }` para asegurar que el nombre también sea negro.

### 4. Contratos (y Proveedores) — chips con letras negras
**Problema**: Los chips de equipos seleccionados eran verde esmeralda con texto blanco, lo que dificultaba la lectura.

**Fix** (aplicado en ambos archivos para mantener consistencia):
- Fondo cambiado a **amarillo cálido** `#fde68a` con borde `#f59e0b`.
- **Todo el texto en negro** (`#000000`): nombre, marca y SN.
- Sombra sutil `0 1px 2px rgba(245, 158, 11, 0.25)`.
- Hover: fondo `#fcd34d`, borde `#d97706`.
- Botón × del chip: fondo negro semi-transparente (`rgba(0,0,0,0.15)`), texto negro. Hover invierte: fondo negro, texto blanco.

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/EquiposView.vue` | Eliminada regla problemática `.btn-icon:hover` |
| `frontend/src/views/ContratosView.vue` | Botón Documentos + modal + chips amarillos/negros + equipos-tag llamativos |
| `frontend/src/views/ProveedoresView.vue` | chips amarillos/negros (consistencia) |
| `frontend/src/components/DocumentosAdjuntos.vue` | Prop `contratoId` |
| `backend/models/documentos.py` | Campo `contrato_id` |
| `backend/database.py` | Migración para agregar columna `contrato_id` |
| `backend/api/routes/documentos.py` | Soporte `contrato_id` en POST y GET |

## Cómo aplicar

1. Copia los 7 archivos a tu copia local del repositorio preservando las rutas.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. **Reinicia el backend** (uvicorn) para que:
   - Se ejecute la migración que agrega `contrato_id` a la tabla `documentoadjunto`.
   - Se carguen los endpoints actualizados de documentos.
4. Refresca el navegador con **Ctrl+F5**.
5. Verás:
   - **Equipos**: hover de iconos ahora cambia a color (verde/azul/rojo/morado/cian).
   - **Contratos**: nuevo icono 📄 (cian en hover) que abre modal de documentos.
   - **Contratos (ver)**: equipos asociados con fondo amarillo y texto negro.
   - **Contratos (editar) + Proveedores (editar)**: chips de equipos amarillos con texto negro.

## Versión
- **Versión**: v0.9.12
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
