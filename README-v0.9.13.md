# CMMS-BioAI v0.9.13 — Activar página Planificación en el menú

## Problema detectado
La página `PlanificacionView.vue` **existía como archivo** (569 líneas con calendario mensual, filtros, modal detalle) pero **NO estaba registrada en el router ni en el menú Navbar**, por lo que era inaccesible desde la interfaz. Era una feature "huérfana".

## Cambios aplicados (solo 2 archivos)

### 1. `frontend/src/router/index.js`
- Importado `PlanificacionView` desde `'../views/PlanificacionView.vue'`.
- Agregada ruta `{ path: '/planificacion', name: 'planificacion', component: PlanificacionView }` entre `/preventivo` y `/historial` (orden lógico del flujo de trabajo).

### 2. `frontend/src/components/Navbar.vue`
- Agregado `{ path: '/planificacion', label: 'Planificación' }` al array `navLinks`, entre "Preventivo" e "Historial".

## NOTA IMPORTANTE
**No necesitas reemplazar `PlanificacionView.vue`** — tú ya lo tienes en `D:\cmmsbioai\frontend\src\views\PlanificacionView.vue`. Lo incluyo en el ZIP solo como respaldo, pero si tu archivo local tiene algún cambio personalizado, **conserva el tuyo**.

Solo necesitas aplicar los cambios en:
- `frontend/src/router/index.js`
- `frontend/src/components/Navbar.vue`

## Cómo aplicar

1. Copia estos 2 archivos a tu PC:
   - `frontend/src/router/index.js`
   - `frontend/src/components/Navbar.vue`
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5**.
4. Verás **"Planificación"** en el menú, entre "Preventivo" e "Historial".

## ¿Qué hace la página Planificación?
Según el código del archivo (569 líneas), es un **calendario mensual unificado** que muestra:
- **Órdenes de Trabajo (OT)** con fechas relevantes.
- **Mantenimientos Preventivos (MP)** con `proxima_fecha`.
- **Filtros**: tipo (OT/MP), equipo, ubicación, responsable.
- **Colores del ciclo MP**: 🟢 Programada / 🟡 Recordatorio / 🔴 Vencida.
- **Colores de OT**: por estado.
- **Leyenda visual**.
- **Modal detalle** al hacer clic en un evento.
- Navegación entre meses (anterior/siguiente).

## Versión
- **Versión**: v0.9.13
- **Fecha**: 2026-06-29
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
