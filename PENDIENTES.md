# CMMS-BioAI — Lista de Pendientes

## Estado del Proyecto (29 Mayo 2026)

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
- [x] ORDENES: Buscador implementado
- [x] ORDENES: Título como select (16 tipos de OT)
- [x] ORDENES: Modal Editar reordenado (Estado+Prioridad, Técnico+Tiempo lado a lado)
- [x] ORDENES: Modal Ver expandido con grid
- [x] ORDENES: "Esp. Repuesto" (sin "Bloqueado")
- [x] ORDENES: Campo costos_adicionales
- [x] ORDENES: Selector unidad_tiempo (horas/días)
- [x] ORDENES: Labels "Costo General" + "Costos Adicionales"
- [x] ORDENES: Decimales corregidos (step=1, display .toFixed(2))

---

### Pendientes — Prioridad Alta

1. **Buscador en Preventivos** — La pantalla de Preventivos no tiene barra de búsqueda
2. **Roles de usuario** — Actualmente todos los roles acceden a todo. Implementar permisos por rol
3. **Reporte Costos** — Clarificar qué costos se reportan

### Pendientes — Prioridad Media

4. **Página Configuración** — Nueva página para configurar ruta de uploads, tema visual, etc.
5. **Página Ayuda** — Nueva página con referencia de estados, tipos de OT, guías de uso
6. **Inventario: Herramientas** — Manejo de herramientas (se asignan, no se descuentan)
7. **Módulo Proveedores** — Nueva sección para gestión de proveedores
8. **numero_material en Repuestos** — Similar a equipos, agregar número de material a repuestos

### Pendientes — Prioridad Baja

9. **Documentos Adjuntos UI**: Mostrar nombre original del archivo
10. **Documentos Adjuntos UI**: Agregar categoría "informe" al subir
11. **Deployment**: Config table + servir frontend desde FastAPI + PyInstaller

### Futuro (Paso H/I)

12. **IA**: Alertas preventivo, patrones de falla, repuestos críticos, sugerencia prioridad, predicción disponibilidad
13. **Seguridad**: Autenticación robusta, HTTPS, backup automático

---

## Estructura del Proyecto

```
cmmsbioai/
├── backend/
│   ├── api/routes/      # Endpoints API (11 endpoints)
│   ├── models/          # Modelos SQLModel (8 modelos)
│   ├── schemas/         # Schemas Pydantic (7 schemas)
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
└── REFERENCIA_ESTADOS.md  # Doc de referencia (19 estados + 16 tipos OT)
```
