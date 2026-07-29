# CMMS-BioAI v0.9.15 — Contratos: Vigencia negrita + inputs alineados + Moneda solo BOB

## Cambios solicitados y aplicados

### 1. Vigencia: ambas fechas en negrita
**Problema**: En la columna "Vigencia" de la tabla de Contratos, la fecha de inicio se mostraba en negro normal, pero la fecha de fin ("→ fecha") estaba en color gris claro (`text-muted`) y con tamaño más pequeño, lo que hacía que se viera desigual.

**Fix**:
- Reemplazada la clase `text-muted` por una nueva clase `vigencia-fin` en el segundo `<div>` de la celda Vigencia.
- Agregado el estilo:
  ```css
  .vigencia-fin {
    font-weight: 600;
    color: #1e293b;  /* negro azulado, igual que la fecha de inicio */
  }
  ```
- Ahora ambas fechas se ven con el mismo peso visual y color.

### 2. Cuadros de texto alineados en Nuevo/Editar Contrato
**Problema**: Los inputs del formulario (text, date, number, select, textarea) tenían alturas diferentes porque cada tipo de control nativo del navegador usa su propio padding y sizing. Esto hacía que el formulario se viera "desencuadrado".

**Fix**: Mejorado el CSS de la clase `.input` con:
- `box-sizing: border-box` para que el padding se incluya en el ancho total.
- `min-height: 38px` para una altura mínima uniforme.
- `line-height: 1.4` y `color: #1e293b` para consistencia.
- Padding ajustado de `0.45rem 0.6rem` a `0.5rem 0.7rem`.

**Reglas específicas añadidas**:
- `select.input`: `appearance: none` + icono de flecha SVG personalizado + `padding-right: 2rem` para que la flecha no solape el texto. Esto normaliza el aspecto de los selects entre navegadores.
- `input.input[type="date"]`, `input.input[type="number"]`, etc.: `height: 38px` para que coincidan con los demás inputs.
- `input.input[type="date"]::-webkit-calendar-picker-indicator { cursor: pointer }` para mejor UX.
- `textarea.input`: `min-height: 60px` (más alto que los inputs de una línea) + `resize: vertical`.
- Eliminado el `textarea.input` duplicado que existía más abajo en el CSS.

### 3. Moneda: solo BOB en todo el proyecto
**Objetivo**: El sistema debe operar exclusivamente en Bolivianos (BOB). Verificado en todos los módulos:

**Cambios en backend (3 archivos)**:
- `models/contratos.py`: `moneda: str = "BOB"` (era `"USD"`).
- `schemas/contrato.py`:
  - `MONEDAS = {'BOB'}` (antes tenía 10 monedas).
  - `ContratoCreate.moneda: str = "BOB"` (era `"USD"`).
  - Validadores `validate_moneda` ahora solo aceptan BOB.
- `api/routes/contratos.py`: `listar_monedas()` ahora retorna `['BOB']`.

**Cambios en frontend (3 archivos)**:
- `views/ContratosView.vue`:
  - `const monedas = ['BOB']` (antes tenía 10 monedas).
  - `resetForm()`: `moneda: 'BOB'` (era `'USD'`).
  - `abrirEditar(c)`: `moneda: 'BOB'` (antes tomaba `c.moneda || 'USD'` — ahora SIEMPRE BOB, ignorando el valor anterior que pudiera tener un contrato viejo).
  - Campo "Moneda" en el formulario reemplazado de `<select>` a `<input type="text" readonly>` con clase `input-readonly` (fondo gris claro, no editable). Mensaje tooltip: "El sistema opera únicamente en Bolivianos (BOB)".
- `views/AyudaView.vue`: actualizada la descripción del campo `moneda` en la documentación interna.

**Verificación de otros módulos** (sin cambios, ya usaban Bs.):
- `InventarioView.vue` (Repuestos y Herramientas): ya usa `Bs.` en `formatPrecio()` ✓
- `OrdenesView.vue`: ya usa `Bs.` en costos ✓
- `ConfiguracionView.vue`: ya muestra `BOB` por defecto ✓

**Validación con TestClient**:
- `GET /contratos/monedas/lista` → `['BOB']` ✓
- POST contrato con `moneda: 'BOB'` → 201, devuelve `moneda: 'BOB'` ✓
- POST contrato con `moneda: 'USD'` → **422 rechazado** (validación funciona) ✓
- POST contrato sin especificar moneda → 201, default `BOB` ✓

## Archivos modificados (5 archivos)

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/ContratosView.vue` | Vigencia negrita + inputs alineados + Moneda BOB readonly |
| `frontend/src/views/AyudaView.vue` | Descripción del campo moneda actualizada |
| `backend/models/contratos.py` | Default moneda `BOB` |
| `backend/schemas/contrato.py` | `MONEDAS = {'BOB'}` + default `BOB` + validadores |
| `backend/api/routes/contratos.py` | `listar_monedas()` retorna solo `['BOB']` |

## Cómo aplicar

1. Copia los 5 archivos a tu copia local del repositorio preservando las rutas.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. **Reinicia el backend** (uvicorn) para que carguen los nuevos schemas y validadores.
4. Refresca el navegador con **Ctrl+F5**.
5. Verás:
   - En la tabla de Contratos → ambas fechas de Vigencia en negrita.
   - En Nuevo/Editar Contrato → todos los inputs con la misma altura (38px), selects con flecha personalizada consistente.
   - En el campo "Moneda" → input gris de solo lectura con valor "BOB" fijo.
   - No es posible crear/editar contratos con otra moneda (la API rechaza con 422).

## ⚠️ Nota sobre contratos existentes
Si ya tienes contratos creados con `moneda='USD'` (de versiones anteriores), esos registros **siguen existiendo** en la BD con ese valor. Al editarlos desde el frontend, el formulario mostrará 'BOB' (porque forzamos el valor en `abrirEditar`) y al guardar se actualizará a BOB. **No se hace migración automática de datos históricos**, pero cualquier edición los convertirá a BOB.

Si quieres migrar TODOS los contratos existentes a BOB de una sola vez (sin editar uno por uno), avísame y te genero un script SQL o un endpoint de migración.

## Versión
- **Versión**: v0.9.15
- **Fecha**: 2026-06-30
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
