# CMMS-BioAI v0.9.17 — Proveedores: ver Equipos Asociados en el "ojo"

## ✅ Verificación previa (sincronización con GitHub)

Antes de aplicar los cambios, verifiqué que mi workspace local estuviera sincronizado con la última versión de GitHub:

**Comparación MD5 de los 15 archivos `.vue`:**
- 14 archivos: ✅ Idénticos a GitHub
- 1 archivo (`EquiposView.vue`): ❌ Mi local estaba desactualizado (330 bytes menos)

**Acción correctiva**: Copié `EquiposView.vue` desde GitHub a mi local. Las diferencias eran las mejoras de v0.9.5, v0.9.11 y v0.9.12 que estaban en GitHub pero no en mi workspace:
- Placeholder del buscador con "núm. serie, núm. material..."
- Columna "Condición" eliminada de la tabla
- colspan 7 (no 8) en fila vacía
- Iconos con clases `btn-view`, `btn-edit`, `btn-delete`, `btn-history`, `btn-doc` (hover de color)
- Sub-badges de garantía/contrato en línea (`flex-direction: row`)
- Estilo gris por defecto con hover color (sin la regla problemática `.btn-icon:hover`)

Después de la corrección: **15/15 archivos sincronizados con GitHub**.

## Cambios solicitados y aplicados

### Proveedores: ver Equipos Asociados en el modal "ojo"

**Problema**: En la página de Proveedores, al hacer clic en el "ojo" (Ver Detalle) de un proveedor, se veían los contactos asociados pero **NO se veían los equipos asociados**. Sin embargo, en el modal de Editar sí se podían gestionar (agregar/quitar). El usuario reportó: "en el ojo no se ven, deben poder verse".

**Causa**: La función `openDetailModal(prov)` solo asignaba `selectedProveedor.value = prov` y abría el modal, pero no consultaba el endpoint `/proveedores/{id}/equipos` para traer los equipos asociados.

**Solución aplicada**:

#### 1. Nuevas variables en `<script setup>`
```javascript
const detalleEquipos = ref([])           // lista de equipos del proveedor en el detalle
const detalleCargandoEquipos = ref(false) // estado de carga
```

#### 2. Función `openDetailModal` modificada (ahora es `async`)
Antes:
```javascript
const openDetailModal = (prov) => {
  selectedProveedor.value = prov
  showDetailModal.value = true
}
```

Ahora:
```javascript
const openDetailModal = async (prov) => {
  selectedProveedor.value = prov
  detalleEquipos.value = []
  detalleCargandoEquipos.value = true
  showDetailModal.value = true
  try {
    const res = await apiClient.get(`/proveedores/${prov.id}/equipos`)
    if (Array.isArray(res.data)) {
      detalleEquipos.value = res.data
    }
  } catch (e) {
    console.error('Error cargando equipos del proveedor en detalle:', e)
  } finally {
    detalleCargandoEquipos.value = false
  }
}
```

#### 3. Nueva sección "Equipos Asociados" en el modal de detalle
Se agregó después de la sección "Contactos Asociados" y antes de los botones de acción. La sección incluye:

- **Encabezado** con contador: "Equipos Asociados (N)"
- **Estado de carga**: "Cargando equipos..." mientras se obtienen del backend
- **Estado vacío**: "Este proveedor no tiene equipos asociados." si no hay ninguno
- **Lista de equipos**: cada equipo se muestra en una tarjeta (mismo estilo que los contactos) con:
  - **Nombre corto** (o modelo) en negrita
  - **Marca** con icono SVG de etiqueta
  - **Modelo** con icono SVG de cuadro
  - **Número de serie** con icono SVG de barra
  - **Ubicación actual** con icono SVG de pin de mapa

La sección es **SOLO LECTURA** (igual que los contactos en el "ojo" desde v0.9.6). Para agregar/quitar/editar equipos asociados, el usuario debe usar el botón de editar (lápiz) que abre el modal de edición con el selector chips/tags.

## Archivos modificados (2 archivos)

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/ProveedoresView.vue` | Modal "ojo" ahora muestra Equipos Asociados (solo lectura) |
| `frontend/src/views/EquiposView.vue` | Sincronizado desde GitHub (sin cambios funcionales, solo sincronización) |

**Nota**: El archivo `EquiposView.vue` se incluye en el ZIP porque lo sincronicé desde GitHub en esta sesión. Si tu PC ya tiene la versión correcta de GitHub (con las mejoras v0.9.5/v0.9.11/v0.9.12), **no necesitas reemplazarlo** — solo reemplaza `ProveedoresView.vue`.

## Cómo aplicar

1. Copia `ProveedoresView.vue` a tu PC en `D:\cmmsbioai\frontend\src\views\` (reemplazando el existente).
2. (Opcional) Copia también `EquiposView.vue` si quieres asegurar sincronización.
3. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
4. Refresca el navegador con **Ctrl+F5**.
5. Verás:
   - Al hacer clic en el "ojo" de un proveedor → se cargan y muestran los equipos asociados en una nueva sección "Equipos Asociados (N)".
   - Si el proveedor no tiene equipos → muestra "Este proveedor no tiene equipos asociados."
   - Mientras carga → muestra "Cargando equipos..."
   - Cada equipo se ve con nombre, marca, modelo, SN y ubicación (iconos SVG).

## Validación backend

El endpoint `GET /proveedores/{id}/equipos` ya existía desde v0.9.11. Retorna:
```json
[
  {
    "id": 1,
    "nombre_corto": "Monitor UCI 02",
    "modelo": "XYZ-1000",
    "marca": "Philips",
    "numero_serie": "SN12345",
    "ubicacion_actual": "UCI Box 5"
  }
]
```

No se requieren cambios en el backend.

## Versión
- **Versión**: v0.9.17
- **Fecha**: 2026-07-02
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
