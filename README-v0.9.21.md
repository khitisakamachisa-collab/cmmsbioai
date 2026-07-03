# CMMS-BioAI v0.9.21 — Costos Adicionales múltiples por OT (RF11 - OtCostoAdicional)

## Resumen

Implementación completa del modelo `OtCostoAdicional` (RF11 v0.9.1) que permite registrar **múltiples costos individuales** por cada Orden de Trabajo, con tipo, descripción, monto y total automático. Similar a cómo funcionan los contactos en Proveedores.

## Diagnóstico previo

El modelo `OtCostoAdicional` y su schema **ya existían** desde v0.9.1, pero:
- ❌ **NO existían endpoints API** para gestionar los costos (CRUD)
- ❌ El router no estaba registrado en `main.py`
- ❌ El frontend `OrdenesView.vue` seguía usando los campos **obsoletos** `costo_adicional` y `costos_adicionales` (campos únicos en `OrdenTrabajo`)
- ✅ La documentación de Ayuda ya describía `OtCostoAdicional` correctamente

## Cambios aplicados

### Backend (2 archivos)

#### `backend/api/routes/costos.py` (NUEVO)
Endpoints CRUD completos:
- `POST /costos/` — crear un costo asociado a una OT (valida que la OT exista)
- `GET /costos/?orden_trabajo_id=X` — listar costos de una OT
- `GET /costos/tipos/lista` — listar los 8 tipos de costo válidos
- `GET /costos/{costo_id}` — obtener un costo específico
- `PUT /costos/{costo_id}` — actualizar un costo
- `DELETE /costos/{costo_id}` — eliminar un costo (204)
- `GET /costos/ot/{orden_trabajo_id}/total` — total de costos de una OT

#### `backend/main.py`
- Importado `costos` de `api.routes`
- Registrado `app.include_router(costos.router)`

### Frontend (1 archivo: `OrdenesView.vue`)

#### Variables nuevas
- `tiposCosto`: array con los 8 tipos de costo
- `costosAdicionales` (ref): lista de costos para el modal Crear
- `editCostosAdicionales` (ref): lista de costos para el modal Editar
- `detalleCostos` (ref): lista de costos para el modal Ver
- `costoForm`, `editCostoForm`: mini-formularios para agregar costos
- `totalCostos`, `totalEditCostos`, `totalDetalleCostos`: computed totals
- Funciones: `addCostoToOT`, `removeCostoFromOT`, `addEditCostoToOT`, `removeEditCostoFromOT`
- `sincronizarCostosOT(otId, costosFormulario)`: sincroniza costos con el backend (crea nuevos, actualiza existentes, elimina los que se quitaron)

#### Eliminado
- Campos obsoletos `costo_adicional` y `costos_adicionales` de `formData`, `editFormData`, `openCreateModal`, `saveOrden`, `openEditModal`, `updateOrden`
- Inputs obsoletos "Costo General" y "Costos Adicionales" de los modales Crear y Editar
- Líneas "Costo General" y "Costos Adicionales" del modal Ver

#### Modal NUEVO
Sección "Costos Adicionales" con **fondo rojo claro** (`#fef2f2`):
- Mini-formulario: Tipo (select con 8 tipos), Monto (Bs.), Descripción
- Botón "+ Agregar Costo" (rojo)
- Lista de costos agregados, cada uno con:
  - Badge rojo con el tipo
  - Descripción
  - Monto en rojo oscuro
  - Botón × rojo para quitar
- Total automático al pie de la lista
- Estado vacío: "No hay costos agregados."

Al guardar: después de crear la OT, se llama a `sincronizarCostosOT` que crea cada costo vía `POST /costos/`.

#### Modal EDITAR
Sección "Costos Adicionales" idéntica al modal Crear, pero:
- Al abrir el modal, se cargan los costos existentes de la OT vía `GET /costos/?orden_trabajo_id=X`
- Cada costo cargado conserva su `id` para poder actualizarlo
- Al guardar: después de actualizar la OT, se llama a `sincronizarCostosOT` que:
  - Elimina los costos que están en BD pero no en el formulario
  - Actualiza los costos existentes (con `id`)
  - Crea los costos nuevos (sin `id`)

#### Modal VER
Sección "Costos Adicionales (N)" con **fondo rojo claro**:
- Lista de costos (solo lectura, sin botones de quitar)
- Cada costo muestra: tipo (badge rojo), descripción, monto
- Total automático al pie
- Estado vacío: "Sin costos registrados."

### Estilos CSS (fondo rojo claro)
```css
.costos-section { background: #fef2f2; border: 1px solid #fecaca; border-radius: 6px; padding: 1rem; }
.costo-form { background: #fff5f5; border: 1px dashed #fca5a5; }
.btn-add-costo { background: #dc2626; color: white; }
.costo-lista li { background: #fee2e2; border: 1px solid #fecaca; }
.costo-tipo { background: #dc2626; color: white; border-radius: 10px; }
.costo-monto { color: #991b1b; font-weight: 700; }
.costo-remove { background: #dc2626; color: white; border-radius: 50%; }
.costo-total { background: #fecaca; font-weight: 700; }
.costos-detail-view { background: #fef2f2; border: 1px solid #fecaca; }
```

## Validación backend con TestClient

- `GET /costos/tipos/lista` → 200, 8 tipos ✓
- `POST /costos/` → 201, crea costo ✓
- `GET /costos/?orden_trabajo_id=X` → 200, lista costos ✓
- `GET /costos/ot/{id}/total` → total correcto (950.5 con 2 costos) ✓
- `DELETE /costos/{id}` → 204 ✓
- Total después de eliminar → 800.0 (1 costo) ✓

## Archivos modificados (3)

| Archivo | Cambios |
|---------|---------|
| `backend/api/routes/costos.py` | **NUEVO** — CRUD completo para OtCostoAdicional |
| `backend/main.py` | Registrar router `costos` |
| `frontend/src/views/OrdenesView.vue` | Sección Costos Adicionales en Crear, Editar y Ver |

## Cómo aplicar

1. Copia los 3 archivos a tu PC preservando las rutas.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. **Reinicia el backend** (uvicorn) para que cargue el nuevo router de costos.
4. Refresca el navegador con **Ctrl+F5**.
5. Verás:
   - **Nueva OT**: sección "Costos Adicionales" con fondo rojo claro, puedes agregar N costos.
   - **Editar OT**: carga los costos existentes, puedes agregar/quitar/modificar.
   - **Ver OT**: sección "Costos Adicionales (N)" con fondo rojo claro, total automático.
   - Cada costo tiene: tipo (badge rojo), descripción, monto (Bs.).
   - Los costos se guardan en la tabla `otcostoadicional` (RF11).

## ⚠️ Notas importantes

- Los campos obsoletos `costo_adicional` y `costos_adicionales` de la tabla `ordentrabajo` **siguen existiendo** en la BD (no se eliminan por compatibilidad), pero ya no se usan desde el frontend. Los costos se gestionan exclusivamente vía `OtCostoAdicional`.
- El modelo `OtCostoAdicional` ya existía desde v0.9.1, así que **no se requiere migración** de base de datos. La tabla `otcostoadicional` ya debería existir.
- La página Ayuda ya describe correctamente `OtCostoAdicional` (RF11), no requiere cambios.

## Sobre el punto 4 de tu mensaje anterior

Has mencionado que los costos también deberían aplicarse a contratos y mantenimientos preventivos para saber cuánto se ha invertido en un equipo. Ese es un tema más amplio que requiere análisis de las tablas existentes. Por ahora, esta v0.9.21 implementa los costos múltiples para **OT** (que es donde más se necesitan). En una versión futura podemos extender el modelo a contratos y MP.

## Versión
- **Versión**: v0.9.21
- **Fecha**: 2026-07-02
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
