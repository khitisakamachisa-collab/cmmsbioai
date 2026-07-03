# CMMS-BioAI v0.9.22 — ORDENES: ajustes visuales (líneas, fondos, orden, títulos)

## Cambios solicitados y aplicados

### 1. ✅ Eliminar líneas separadoras `<hr>`
En los modales NUEVO y EDITAR existían líneas `<hr>` antes de "Costos Adicionales" y antes de "Repuestos Utilizados". Eliminadas para que las secciones fluyan sin separadores visuales.

### 2. ✅ Repuestos Utilizados con fondo amarillo claro (igual que Costos en rojo)
Antes el selector de repuestos y la lista estaban sin contenedor visual (solo la lista tenía fondo amarillo). Ahora toda la sección "Repuestos Utilizados" está envuelta en un contenedor `.repuestos-section` con:
- Fondo amarillo cálido `#fef3c7`
- Borde `#fcd34d`
- Border-radius `6px`
- Padding `1rem`

Esto crea uniformidad visual con la sección de Costos (que tiene fondo rojo claro `#fef2f2`).

### 3. ✅ En el ojo, Costos encima de Repuestos
Antes el orden en el modal Ver era:
1. Información General + Asignación (2 columnas)
2. **Costos Adicionales**
3. Descripción de Falla
4. Acciones Realizadas
5. **Repuestos Utilizados**

Ahora el orden es:
1. Información General + Asignación (2 columnas)
2. Descripción de Falla
3. Acciones Realizadas
4. **Costos Adicionales** (con fondo rojo claro)
5. **Repuestos Utilizados** (con fondo amarillo claro)

Así el orden coincide con los modales NUEVO y EDITAR (Costos primero, Repuestos después).

### 4. ✅ Títulos "Costos Adicionales" y "Repuestos Utilizados" FUERA del cuadro
Antes los títulos `<h4>` estaban dentro de los contenedores `.costos-section` y `.detail-full-view`. Ahora están **fuera** del cuadro, usando la clase `.section-title`:

```css
.section-title {
  margin: 1rem 0 0.5rem 0;
  padding: 0;
  font-size: 1rem;
  font-weight: 700;
  color: #1e293b;
  border: none;
  background: none;
}
```

Esto se aplica en los 3 modales (NUEVO, EDITAR, VER), creando uniformidad: el título está afuera, el contenido con color de fondo está adentro.

### 5. ✅ Estado vacío de Repuestos
Agregado `<p v-else class="repuesto-empty">No hay repuestos agregados.</p>` en NUEVO y EDITAR, y `"Sin repuestos registrados."` en VER, con color marrón `#92400e` (acorde al tema amarillo).

## Uniformidad visual lograda

| Sección | Título | Contenedor | Color de fondo |
|---------|--------|-----------|----------------|
| Costos Adicionales | Fuera (`.section-title`) | `.costos-section` | Rojo claro `#fef2f2` |
| Repuestos Utilizados | Fuera (`.section-title`) | `.repuestos-section` | Amarillo claro `#fef3c7` |

Mismo patrón en los 3 modales (NUEVO, EDITAR, VER).

## Archivo modificado (1)

| Archivo | Cambios |
|---------|---------|
| `frontend/src/views/OrdenesView.vue` | Eliminar `<hr>`, envolver repuestos en contenedor amarillo, reordenar modal Ver, títulos fuera del cuadro |

## Cómo aplicar

1. Copia `OrdenesView.vue` a tu PC en `D:\cmmsbioai\frontend\src\views\` (reemplazando el existente).
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. Refresca el navegador con **Ctrl+F5**.
4. Verás:
   - **NUEVO y EDITAR**: sin líneas `<hr>`, sección Costos (rojo claro) y Repuestos (amarillo claro) como bloques visuales, títulos afuera.
   - **VER**: Costos Adicionales encima de Repuestos Utilizados (mismo orden que NUEVO/EDITAR), ambos con título fuera del cuadro de color.

## Versión
- **Versión**: v0.9.22
- **Fecha**: 2026-07-03
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
