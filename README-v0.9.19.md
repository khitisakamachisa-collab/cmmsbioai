# CMMS-BioAI v0.9.19 — ORDENES: fix repuestos al crear + iconos color + repuestos amarillo + modal Ver redimensionado

## Cambios solicitados y aplicados

### 1. 🐛 FIX: Repuestos no se guardaban al CREAR OT
**Problema**: Al crear una OT nueva y agregar repuestos, la OT se creaba pero los repuestos NO se asociaban. En Editar sí funcionaba.

**Causa raíz**: 
- El schema `OrdenTrabajoCreate` era `pass` (no tenía campo `repuestos_utilizados`).
- El endpoint `POST /ordenes/` solo hacía `OrdenTrabajo(**orden.model_dump())` y NO procesaba repuestos.

**Fix backend (2 archivos)**:

`backend/schemas/orden_trabajo.py`:
```python
class OrdenTrabajoCreate(OrdenTrabajoBase):
    # v0.9.19: permitir recibir repuestos_utilizados al crear la OT
    repuestos_utilizados: Optional[List[dict]] = None
    costo_adicional: Optional[float] = None
    costos_adicionales: Optional[float] = None
```

`backend/api/routes/ordenes.py` — endpoint `POST /ordenes/` ahora:
1. Extrae `repuestos_utilizados` del dict antes de crear la OT.
2. Crea la OT con los campos restantes.
3. Si hay repuestos, los procesa igual que el PUT: valida stock, descuenta de `Repuesto.cantidad_disponible`, crea registros `OtRepuestoUtilizado`.

**Validación con TestClient**:
- POST con `repuestos_utilizados: [{repuesto_id: 2, cantidad: 3}]` → 200 OK ✓
- GET /ordenes/{id} → `repuestos_usados` tiene 1 elemento con `repuesto_id=2, cantidad_utilizada=3` ✓
- Stock del repuesto: 10 → 7 (descontó 3 correctamente) ✓

### 2. ✅ Iconos con colores de fondo como en EQUIPOS
**Problema**: Los iconos de Acciones (ojo, lápiz, basurero, documento) en ORDENES usaban clases antiguas (`btn-edit-icon`, `btn-danger-icon`, `btn-doc-icon`) con hover en gris/amarillo claro, distinto a EQUIPOS que usa hover de color sólido.

**Fix**:
- Cambiadas las clases del template: `btn-edit-icon` → `btn-edit`, `btn-danger-icon` → `btn-delete`, `btn-doc-icon` → `btn-doc`, y el botón Ver ahora tiene `btn-view`.
- Actualizado el CSS:
  ```css
  .btn-icon { background: #f0f2f5; ... display: inline-flex; ... transition: all 0.2s; }
  .btn-view:hover { background: #16a34a; color: #ffffff; }   /* verde */
  .btn-edit:hover { background: #2563eb; color: #ffffff; }   /* azul */
  .btn-delete:hover { background: #dc2626; color: #ffffff; } /* rojo */
  .btn-doc:hover { background: #0891b2; color: #ffffff; }    /* cian */
  ```
- Eliminada la regla problemática `.btn-icon:hover { background: #dfe2e6; }` que pisaba los colores específicos.

Ahora los 4 iconos de ORDENES tienen el mismo comportamiento que EQUIPOS: grises por defecto, color sólido + ícono blanco al hover.

### 3. ✅ Lista de repuestos con fondo amarillo (Crear y Editar)
**Problema**: Los repuestos seleccionados se mostraban en una lista gris clara, poco visible.

**Fix** — CSS `.repuesto-lista` cambiado a fondo amarillo cálido:
```css
.repuesto-lista { list-style: none; padding: 0; background: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; margin-top: 8px; }
.repuesto-lista li { padding: 8px 12px; border-bottom: 1px solid #fde68a; font-size: 0.9rem; color: #1e293b; font-weight: 500; }
.repuesto-lista li:last-child { border-bottom: none; }
```

Aplicado tanto en el modal NUEVO como en el modal EDITAR (ambos usan la misma clase `.repuesto-lista`).

### 4. ✅ Redimensionar modal Ver + Repuestos con fondo amarillo
**Problema**: El modal Ver era muy ancho (700px) y activaba scroll horizontal innecesario. Las cajas de "Descripción de Falla" y "Acciones Realizadas" eran muy largas.

**Fix**:
- Ancho del modal Ver reducido de 700px a **600px** con `max-width: 95vw` para evitar scroll horizontal en pantallas pequeñas.
- `.detail-full-view`: agregado `box-sizing: border-box` y `overflow-x: hidden` para evitar desbordamiento.
- `.description-box`: agregado `box-sizing: border-box` y estilos inline `max-height: 120px; overflow-y: auto; word-wrap: break-word; white-space: pre-wrap;` para que el texto largo haga wrap en lugar de activar scroll horizontal.
- Repuestos en modal Ver ahora con **fondo amarillo** (clase nueva `.repuesto-detail-yellow`):
  ```css
  .repuesto-detail-yellow { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 4px; padding: 0.5rem 1rem; }
  .repuesto-detail-yellow li { padding: 6px 0; color: #1e293b; font-weight: 500; border-bottom: 1px solid #fde68a; }
  ```

## Archivos modificados (3 archivos)

| Archivo | Cambios |
|---------|---------|
| `backend/schemas/orden_trabajo.py` | `OrdenTrabajoCreate` ahora acepta `repuestos_utilizados`, `costo_adicional`, `costos_adicionales` |
| `backend/api/routes/ordenes.py` | Endpoint `POST /ordenes/` procesa repuestos (valida stock, descuenta, crea OtRepuestoUtilizado) |
| `frontend/src/views/OrdenesView.vue` | Iconos con hover color + repuestos amarillo + modal Ver redimensionado + repuestos amarillo en Ver |

## Cómo aplicar

1. Copia los 3 archivos a tu PC preservando las rutas.
2. En la carpeta `frontend/`, ejecuta:
   ```bash
   npm run build
   ```
3. **Reinicia el backend** (uvicorn) para que carguen los cambios en el schema y el endpoint POST.
4. Refresca el navegador con **Ctrl+F5**.
5. Verás:
   - **Crear OT con repuestos**: ahora los repuestos SÍ se asocian a la OT al crear (y se descuenta el stock).
   - **Iconos**: ojo/lápiz/basurero/documento con hover verde/azul/rojo/cian (igual que EQUIPOS).
   - **Lista de repuestos** (en Crear y Editar): fondo amarillo cálido, texto negro, muy visible.
   - **Modal Ver**: más angosto (600px), sin scroll horizontal innecesario, descripciones con wrap, repuestos con fondo amarillo.

## ⚠️ Importante
El fix del bug de repuestos al crear OT requiere **reiniciar el backend** para que el endpoint `POST /ordenes/` cargue la nueva lógica. Si solo reemplazas el frontend, el bug persistirá.

## Versión
- **Versión**: v0.9.19
- **Fecha**: 2026-07-02
- **Stack**: FastAPI + Vue 3 + Vite + SQLite
