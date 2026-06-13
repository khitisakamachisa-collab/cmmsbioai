# CMMS-BioAI — Lista de Pendientes

## Estado del Proyecto (14 Junio 2026)

### Completados
- [x] **Paso B/B2**: Importación desde Excel
- [x] **Paso C**: Gráficos (Chart.js)
- [x] **Paso D**: Generar OT desde Preventivo
- [x] **Paso E**: Historial de mantenimiento
- [x] **Paso F**: Reportes
- [x] **Paso G**: Documentos Adjuntos
- [x] EQUIPOS: 19 estados biomédicos con colores
- [x] EQUIPOS: Campo imagen_ruta + endpoint upload_imagen + thumbnails
- [x] EQUIPOS: Campo numero_material (opcional, variante del modelo)
- [x] EQUIPOS: Campo fecha_fin_garantia + badge "En Garantía"
- [x] EQUIPOS: Calibracion_proxima mantenida (no reemplazada)
- [x] EQUIPOS: Nombre en tabla ya NO es clickeable (solo icono ojo)
- [x] EQUIPOS: Búsqueda combinada (nombre/marca/modelo + N. Serie + Ubicación) con lógica AND
- [x] ORDENES: Buscador implementado
- [x] ORDENES: Título como select (16 tipos de OT)
- [x] ORDENES: Modal Editar reordenado (Estado+Prioridad, Técnico+Tiempo lado a lado)
- [x] ORDENES: Modal Ver expandido con grid
- [x] ORDENES: "Esp. Repuesto" (sin "Bloqueado")
- [x] ORDENES: Campo costos_adicionales
- [x] ORDENES: Selector unidad_tiempo (horas/días)
- [x] ORDENES: Labels "Costo General" + "Costos Adicionales"
- [x] ORDENES: Decimales corregidos (step=1, display .toFixed(2))
- [x] INVENTARIO: Herramientas (RF09) — Backend + Frontend + Tab dentro de Inventario

---

### Módulos del Sistema (RF)

| RF | Nombre | Estado | Notas |
|----|--------|--------|-------|
| RF01 | Gestión de Activos (Equipos) | ✅ Completado | CRUD, Excel, imágenes, documentos, historial |
| RF02 | Gestión de Órdenes de Trabajo | ✅ Completado | CRUD, 16 tipos OT, costos, repuestos utilizados |
| RF03 | Mantenimiento Preventivo | ✅ Completado | CRUD, generar OT, badges de vencimiento |
| RF04 | Gestión de Inventario (Repuestos) | ✅ Completado | CRUD, Excel, imágenes, documentos |
| RF05 | Historial de Mantenimiento | ✅ Completado | Timeline por equipo, eventos automático |
| RF06 | Reporting y Estadísticas | ✅ Completado | 6 tabs con Chart.js, filtros por fecha |
| RF07 | Módulo IA | ❌ Pendiente | Ver sección Futuro |
| RF08 | Autenticación | ✅ Completado | JWT, bcrypt, roles definidos |
| RF09 | Herramientas y Materiales | ✅ Completado | Tab dentro de Inventario, CRUD, Excel, badges |
| RF10 | Calendario Preventivo | 🔶 Planificado | Vista calendario para tareas preventivas |
| RF11 | (Integrado en RF06) | — | Reportes ya implementados en RF06 |
| RF12 | Gestión de Proveedores | 🔶 Planificado | Nuevo módulo independiente |

---

### Pendientes — Prioridad Alta

1. **Buscador en Preventivos** — La pantalla de Preventivos no tiene barra de búsqueda. Agregar búsqueda por equipo, título, frecuencia
2. **Roles de usuario** — Actualmente todos los roles acceden a todo. Implementar permisos por rol (admin/tecnico/visualizador)
3. **Reporte Costos** — Clarificar qué costos se reportan (mano de obra vs. repuestos vs. costos generales)

---

### Pendientes — Prioridad Media

4. **Página Configuración** — Nueva página para configurar ruta de uploads, tema visual, etc.
5. **Página Ayuda** — Nueva página con referencia de estados, tipos de OT, guías de uso
6. **numero_material en Repuestos** — Similar a equipos, agregar número de material a repuestos
7. **RF10 — Calendario Preventivo** — Agregar vista de calendario (mensual/semanal) al módulo Preventivo existente. Mostrar tareas programadas con colores por estado (vencida, próxima, OK). Posibilidad de hacer clic en una tarea para ver detalle o generar OT
8. **RF12 — Módulo Proveedores** — Nuevo módulo independiente para gestión de proveedores. CRUD con campos: nombre, NIT, contacto, teléfono, email, dirección, categoría (fabricante/distribuidor/servicio), observaciones. Vinculación con equipos, repuestos y herramientas. Podría ser un tab dentro de Inventario (3er tab: Repuestos / Herramientas / Proveedores) o una sección propia en el navbar

---

### Pendientes — Prioridad Baja

9. **Documentos Adjuntos UI**: Mostrar nombre original del archivo
10. **Documentos Adjuntos UI**: Agregar categoría "informe" al subir
11. **Deployment**: Config table + servir frontend desde FastAPI + PyInstaller

---

### Futuro (Paso H/I)

12. **IA (RF07)**: Alertas preventivo, patrones de falla, repuestos críticos, sugerencia prioridad, predicción disponibilidad
13. **Seguridad**: Autenticación robusta, HTTPS, backup automático

---

## Detalle de Nuevos RFs

### RF10 — Calendario Preventivo
**Objetivo**: Transformar la vista actual de Preventivo (solo tabla) en una experiencia visual con calendario.

**Alcance**:
- Vista calendario mensual y semanal con las tareas preventivas
- Colores por estado: rojo (vencida), amarillo (próxima en 7 días), verde (OK)
- Click en tarea para ver detalle rápido o generar OT
- Toggle entre vista tabla (actual) y vista calendario
- Filtros: por equipo, por estado de vencimiento
- Exportar calendario o lista filtrada

**Tecnología sugerida**:
- Librería JS: FullCalendar (open source) o calendario custom con CSS Grid
- No requiere cambios de backend (los datos ya existen en TareaPreventiva)

**Dependencias**: Ninguna — usa los endpoints existentes de `/preventivo/`

---

### RF12 — Gestión de Proveedores
**Objetivo**: Centralizar la gestión de proveedores, reemplazando los campos de texto libre en Equipo, Repuesto y Herramienta.

**Alcance**:
- Modelo `Proveedor` con campos: id, nombre, nit, contacto_nombre, telefono, email, direccion, categoria (Fabricante/Distribuidor/Servicio/Importador), observaciones, activo
- CRUD completo (API + frontend)
- Relación: Equipo.proveedor_principal → FK a Proveedor (migración de texto a FK)
- Relación: Repuesto.proveedor_ultimo → FK a Proveedor
- Relación: Herramienta.proveedor_ultimo → FK a Proveedor
- Búsqueda por nombre, NIT, categoría
- Vista: Tab dentro de Inventario (3er tab) o sección propia

**Decisión pendiente**: ¿Tab dentro de Inventario (3er tab junto a Repuestos y Herramientas) o sección propia en navbar?

**Dependencias**: Migración de datos (campos de texto existentes → FK)

---

## Estructura del Proyecto

```
cmmsbioai/
├── backend/
│   ├── api/routes/      # Endpoints API (12 rutas)
│   ├── models/          # Modelos SQLModel (9 modelos)
│   ├── schemas/         # Schemas Pydantic (8 schemas)
│   ├── utils/           # Utilidades (security)
│   ├── uploads/         # Archivos subidos
│   ├── database.py      # DB engine + seed (19 estados equipo + 5 estados OT)
│   ├── main.py          # FastAPI app
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── views/       # Vistas principales (9 vistas)
│   │   ├── components/  # Componentes reutilizables (3 componentes)
│   │   ├── services/    # API client
│   │   └── router/      # Vue Router
│   ├── package.json
│   └── vite.config.js
├── PENDIENTES.md
├── REFERENCIA_ESTADOS.md
└── README.md
```
