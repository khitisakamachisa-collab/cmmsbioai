# CMMS-BioAI v0.9.11 — Equipos + Contratos + Proveedores (chips/tags integrado)

## Cambios solicitados y aplicados

### 1. Equipos — sub-badges de garantía/contrato en línea
**Problema**: Cuando un equipo tiene tanto "🟢 En garantía" como "📋 En contrato", los badges se mostraban uno debajo del otro generando una tercera fila en la tabla que desordenaba la paginación.

**Fix**: Cambiado `flex-direction: column` a `flex-direction: row` con `flex-wrap: wrap` en `.sub-badges`. Ahora los badges se muestran uno al lado del otro (en línea), ocupando solo una fila adicional compacta.

### 2. Equipos — iconos estilo Proveedores (gris hover)
**Problema**: Los iconos de Equipos tenían colores pastel por defecto (verde/azul/rojo/morado/cian), distinto a Proveedores que los tiene en gris por defecto y solo muestran color en hover.

**Fix**: Reescrito el bloque CSS de `.btn-icon` con `background: #f0f2f5; color: #555;` por defecto (como Proveedores v0.9.7). Solo se mantienen las reglas `:hover` con los colores sólidos (verde/azul/rojo/morado/cian + ícono blanco). Las 5 acciones conservan sus colores en hover:
- 🟢 Ver Detalles → verde `#16a34a`
- 🔵 Editar → azul `#2563eb`
- 🔴 Eliminar → rojo `#dc2626`
- 🟣 Historial → morado `#7c3aed`
- 🩵 Documentos → cian `#0891b2`

### 3. Contratos — mostrar precio en modal "ojo"
**Mejora**: Agregada una caja destacada "Precio del Contrato" en el modal de detalle (ojo), con fondo ámbar `#fef3c7` y borde `#fcd34d`. El precio se muestra grande (1.4rem, bold) en color ámbar oscuro `#92400e`. Lógica:
- Si hay `costo_total` → muestra el monto total con etiqueta "Costo total".
- Si no hay `costo_total` pero hay `costo_periodico` → muestra el monto periódico con etiqueta "Costo {periodicidad}".
- Si no hay ninguno → muestra "—".

### 4. Contratos — chips con color más resaltado
**Problema**: Los chips azules claros (`#dbeafe`/`#1e40af`) eran muy similares al fondo general del modal.

**Fix**: Cambiada la paleta a verde esmeralda sólido:
- Fondo: `#10b981` (verde esmeralda)
- Borde: `#059669` (verde más oscuro)
- Texto: blanco
- Sombra sutil `0 1px 2px rgba(5,150,105,0.2)` para dar profundidad
- Hover: fondo `#059669` + borde `#047857`
- Botón × del chip: blanco semi-transparente, hover invierte colores
- Marca y SN dentro del chip: verde muy claro `#d1fae5` para distinguirlos del nombre principal

### 5. Proveedores — chips/tags para Equipos Asociados
**Implementación completa** (frontend + backend):

**Backend (3 cambios en `proveedores.py`)**:
- Modificado `DELETE /proveedores/{id}` para desasociar equipos (poner `proveedor_principal_id = NULL`) antes de eliminar el proveedor.
- Nuevo `GET /proveedores/{id}/equipos` → lista equipos cuyo `proveedor_principal_id` es este proveedor.
- Nuevo `PUT /proveedores/{id}/equipos` → sincroniza la lista de equipos asociados:
  - Body: `{ "equipos_ids": [1, 2, 3] }`
  - Equipos en la lista que tenían OTRO proveedor → se asignan a este.
  - Equipos que estaban asignados pero NO están en la lista → se desasocian (NULL).
  - Retorna: `{ ok, proveedor_id, equipos_asociados, mensaje }`.

**Frontend (`ProveedoresView.vue`)**:
- Agregada variable `equipos` cargada en `onMounted` con `fetchEquipos()`.
- Agregadas variables `equiposAsignadosIds`, `equiposSearchQuery`, `savingEquipos`.
- Agregados computeds: `equiposSeleccionados` (objetos equipo), `equiposFiltrados` (resultados excluyendo seleccionados).
- Agregadas funciones: `agregarEquipo(eq)`, `quitarEquipo(id)`, `limpiarSeleccionEquipos()`.
- Modificada `openCreateModal` para resetear selección.
- Modificada `openEditModal` para cargar equipos asociados vía `GET /proveedores/{id}/equipos`.
- Modificada `saveProveedor` para sincronizar equipos vía `PUT /proveedores/{id}/equipos` (tanto en alta como en edición), con estado `saving` mientras procesa.
- Agregado bloque "Equipos Asociados" en el modal con chips/tags verde esmeralda (igual a Contratos), buscador interno y lista de resultados.
- Agregados todos los estilos CSS (.chips-container, .chip, .chip-text, .chip-sub-bold, .chip-remove, .equipos-search-wrapper, .equipos-resultados, .equipo-item, etc.).

**Validación backend con TestClient**:
- Crear proveedor → 201 ✓
- GET /proveedores/{id}/equipos vacío → 200, [] ✓
- Crear 2 equipos → 201 ✓
- PUT /proveedores/{id}/equipos asociar 2 → 200, "Se asociaron 2 equipo(s)" ✓
- GET → 200, 2 equipos ✓
- PUT quitar 1 → 200 ✓
- GET → 1 equipo ✓
- DELETE /proveedores/{id} → desasocia eq1 automáticamente ✓

## Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/EquiposView.vue` | sub-badges en línea + iconos gris/hover |
| `frontend/src/views/ContratosView.vue` | precio destacado + chips verde esmeralda |
| `frontend/src/views/ProveedoresView.vue` | selector chips/tags Equipos Asociados |
| `backend/api/routes/proveedores.py` | 2 endpoints nuevos + desasociar en delete |

## Cómo aplicar

1. Copia los 4 archivos a tu copia local del repositorio preservando las rutas.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Reinicia el backend (uvicorn) para que carguen los nuevos endpoints de proveedores.
4. Refresca el navegador con **Ctrl+F5**.
5. Verás:
   - **Equipos**: badges de garantía/contrato uno al lado del otro; iconos grises con color en hover.
   - **Contratos**: modal "ojo" con caja ámbar "Precio del Contrato"; chips de equipos en verde esmeralda.
   - **Proveedores**: modal de crear/editar con nuevo bloque "Equipos Asociados" usando chips/tags.

## Versión
- **Versión**: v0.9.11
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
