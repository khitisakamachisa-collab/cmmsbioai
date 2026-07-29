# CMMS-BioAI v0.9.4 — Reparación del módulo Contratos (frontend)

## Problema detectado
El módulo de Contratos existía en el backend (`backend/models/contratos.py`,
`backend/schemas/contrato.py`, `backend/api/routes/contratos.py`) y estaba
registrado en `main.py`, pero en el frontend se habían perdido los 3 archivos
necesarios para que apareciera en el menú y fuera usable:

- ❌ `frontend/src/views/ContratosView.vue` — faltaba
- ❌ Ruta `/contratos` en `frontend/src/router/index.js` — faltaba
- ❌ Enlace "Contratos" en `frontend/src/components/Navbar.vue` — faltaba
- ❌ `frontend/src/services/export.js` — faltaba (RF13)

Como consecuencia, el menú lateral no mostraba "Contratos" y la página
no era accesible aunque el backend estuviera funcionando.

## Archivos modificados / creados

| Archivo | Acción |
|---------|--------|
| `frontend/src/views/ContratosView.vue` | **NUEVO** — Vista CRUD completa |
| `frontend/src/services/export.js` | **NUEVO** — Funciones `exportToExcelHTML` y `exportToCSV` (RF13) |
| `frontend/src/router/index.js` | **EDITADO** — Agrega ruta `/contratos` |
| `frontend/src/components/Navbar.vue` | **EDITADO** — Agrega enlace "Contratos" entre Proveedores y Ordenes |

## Cómo aplicar

1. Copia los 4 archivos a tu copia local del repositorio preservando la ruta.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm install   # (solo si es la primera vez)
   npm run build
   ```
3. Reinicia el backend (uvicorn) para que se cree la tabla `contrato` si
   aún no existe. El backend usa `SQLModel.metadata.create_all(engine)`
   que crea las tablas faltantes de forma idempotente.
4. Inicia sesión y verás **Contratos** en el menú, entre Proveedores y Ordenes.

## Funcionalidades incluidas en ContratosView

- **Tabla paginada** (10 por página) con: ID, Proveedor, Tipo, Vigencia,
  Estado, Costo, Equipos asociados, Acciones.
- **Stats cards** en la parte superior: Total / Vigentes / Vencen ≤30d / Vencidos.
- **Filtros**: búsqueda libre, vigencia (vigente/próximo/programado/vencido),
  tipo de contrato, proveedor.
- **Modal Crear/Editar** con todos los campos del modelo:
  - Proveedor (select), Tipo, Fechas inicio/fin, Costo total, Costo periódico,
    Periodicidad, Moneda, Tiempo de respuesta, Horario de servicio,
    Cobertura, Notas, Equipos asociados (checkbox grid).
- **Modal Detalle** con todos los datos + lista de equipos asociados.
- **Eliminar** con confirmación.
- **Exportar**: botones Excel (.xls) y CSV (UTF-8 con BOM) que respetan los
  filtros activos.
- **Cálculo de vigencia en runtime** (no se guarda en BD):
  - Vigente: `fecha_inicio ≤ hoy ≤ fecha_fin`
  - Vence pronto: vigente y `dias_restantes ≤ 30`
  - Programado: `fecha_inicio > hoy`
  - Vencido: `fecha_fin < hoy`

## Estado de la tabla `contrato`

Si tu BD actual no tiene las tablas `contrato` y `contrato_equipo`,
**no necesitas borrar la BD**. El backend las crea automáticamente al
iniciar (gracias a `SQLModel.metadata.create_all`). Solo reinicia el
servicio backend y las tablas aparecerán vacías, listas para usar.

Si ya tenías contratos creados en otra BD (v0.9.2 anterior) y quieres
migrarlos, exporta desde la BD vieja e impórtalos vía la API o crea
los registros nuevamente desde el frontend.

## Versión
- **Versión**: v0.9.4
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
