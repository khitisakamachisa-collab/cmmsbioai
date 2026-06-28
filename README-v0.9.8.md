# CMMS-BioAI v0.9.8 — Página Contratos alineada con Equipos/Proveedores

## Estado al revisar
Al inspeccionar el archivo `ContratosView.vue` y el backend `contratos.py`, se detectó que **las funcionalidades ya estaban implementadas** (con marcadores `v0.9.8`) pero el frontend NO había sido compilado. Por eso el usuario no veía los cambios en su navegador.

## Funcionalidades ya presentes en el archivo

### 1. Botón "Cargar Excel" (estilo Equipos)
- Un solo botón verde "Cargar Excel" con icono en la barra superior derecha.
- Al hacer clic abre un modal con **drop-zone** (arrastrar archivo o clic para seleccionar).
- Validación de extensión (.xlsx / .csv) y tamaño máximo 5MB.
- **Spinner de progreso** mientras se procesa el archivo.
- Cards de resultados: Nuevos / Actualizados / Fallidos / Total.
- Lista detallada de errores (fila, mensaje).
- Botones "Plantilla Excel" y "Plantilla CSV" dentro del modal.
- Botón "Importar otro archivo" para resetear.

### 2. Buscador separado de filtros (estilo Equipos)
- El input de búsqueda está en la barra superior derecha, al lado de los botones de acción.
- Los filtros (Vigencia / Tipo / Proveedor) están en su propia tarjeta debajo, **separados del buscador**.
- Botón "Limpiar" y contador "X de Y" cuando hay filtros activos.

### 3. Iconos grises por defecto, color en hover (estilo Proveedores v0.9.7)
- Por defecto: fondo gris claro `#f0f2f5`, ícono gris oscuro `#555`.
- Al pasar el mouse:
  - 🟢 Ver Detalle → verde sólido `#16a34a` + blanco
  - 🔵 Editar → azul sólido `#2563eb` + blanco
  - 🔴 Eliminar → rojo sólido `#dc2626` + blanco

### 4. Selector de Equipos Asociados con buscador interno
- Dentro del modal de Nuevo/Editar Contrato, el selector de equipos tiene:
  - **Buscador interno** que filtra por nombre, modelo, serie o marca.
  - Contador "X seleccionados de Y" en el label.
  - Checkbox grid con ítems resaltados cuando están seleccionados.
  - Estados vacíos: "No hay equipos registrados" o "No se encontraron equipos con '<búsqueda>'".
- Esto permite manejar listas de 100+ equipos sin que el modal se vuelva inmanejable.

### 5. Backend: endpoint `/contratos/import-excel`
- Recibe archivo .xlsx o .csv (máx 5MB).
- Columnas esperadas: `proveedor_nombre*`, `tipo_contrato*`, `fecha_inicio*`, `fecha_fin*`, `costo_total`, `costo_periodico`, `periodicidad_costo`, `moneda`, `tiempo_respuesta`, `horario_servicio`, `cobertura_detalle`, `notas`, `equipos_series`.
- `proveedor_nombre`: si no existe, se CREA automáticamente el proveedor.
- `equipos_series`: lista de numero_serie separados por `;` — se asocian los equipos cuyo numero_serie coincida.
- Comportamiento **upsert**: si ya existe un contrato con mismo `proveedor_id + tipo_contrato + fecha_inicio`, se actualiza.
- Retorna: `{ exitosos, actualizados, fallidos, total_procesados, errores[] }`.

### 6. Plantillas
- `plantilla_contratos.xlsx` y `plantilla_contratos.csv` ya existen en `frontend/public/plantillas/`.

## Archivos incluidos en este ZIP

| Archivo | Estado |
|---------|--------|
| `frontend/src/views/ContratosView.vue` | Ya tenía v0.9.8 implementado |
| `backend/api/routes/contratos.py` | Ya tenía endpoint `/import-excel` |
| `frontend/public/plantillas/plantilla_contratos.xlsx` | Ya existía |
| `frontend/public/plantillas/plantilla_contratos.csv` | Ya existía |

## Cómo aplicar

1. Copia los archivos a tu copia local del repositorio preservando las rutas.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Reinicia el backend (uvicorn) para que cargue el nuevo endpoint `/contratos/import-excel`.
4. Refresca el navegador con **Ctrl+F5** (limpiar caché).
5. Verás:
   - Botón "Cargar Excel" en la barra superior.
   - Buscador separado de los filtros.
   - Iconos grises por defecto, color en hover.
   - Dentro del modal de Nuevo Contrato, buscador interno en Equipos Asociados.

## ⚠️ Pendiente de discusión: UX del selector de Equipos Asociados
El usuario solicitó conversar sobre opciones para hacer el selector más práctico cuando hay muchos equipos (100+). La implementación actual usa **buscador interno + checkbox grid**, que es UNA opción válida. Ver opciones propuestas en el chat para elegir la definitiva.

## Versión
- **Versión**: v0.9.8
- **Fecha**: 2026-06-28
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
