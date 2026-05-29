# CMMS-BioAI — Registro de Pendientes y Mejoras

---

## PRIORIDAD ALTA — Problemas de uso real (resolver antes de IA)

### 1. UI/UX — Orden y estetica de pantallas
- [ ] Reordenar pantallas para que sean agradables a la vista
- [ ] Limitar/estandarizar el tamano de las ventanas emergentes (modales)
- [ ] Estandarizar tamano de modales: modal Ver (ojo) es mas pequeno que modal Editar (lapiz)
- [ ] Verificar que TODOS los modales tengan scrollbar vertical cuando el contenido excede
- [ ] Evaluar altura maxima uniforme (`max-height: 85vh`) para consistencia visual

### 2. Buscadores faltantes
- [ ] Agregar buscador en ORDENES de trabajo (no tiene, las otras paginas si)
- [ ] Agregar buscador en PREVENTIVOS (no tiene, las otras paginas si)

### 3. Roles de usuario — Definir e implementar
- [ ] Definir que puede hacer cada rol (admin vs tecnico vs otro?)
- [ ] Actualmente TODOS los usuarios tienen acceso a todo — corregir
- [ ] Implementar restricciones por rol en el frontend (ocultar/mostrar elementos)
- [ ] Implementar restricciones por rol en el backend (proteger endpoints)
- [ ] Considerar roles: admin (control total), tecnico (OTs y equipos), visitante (solo lectura)?
- [ ] Route guards en Vue Router segun rol

### 4. Reporte de COSTOS — Revisar logica
- [ ] **PROBLEMA:** El reporte de costos existe pero NO se ingresan precios en el sistema
- [ ] Definir de donde salen los costos: costo_adicional en OTs? precio de repuestos? ambos?
- [ ] Agregar campo de precio/costo a repuestos si es necesario
- [ ] Evaluar con IA de diseno como deberia funcionar el reporte de costos
- [ ] Revisar el endpoint `/reportes/costos` — que datos usa realmente?

### 5. Documentos Adjuntos — Ajustes pendientes
- [ ] Agregar "informe" a la lista de categorias de documentos
- [ ] Verificar que los nombres de archivos originales se preserven (sin prefijos numericos)
- [ ] Considerar icono de cuaderno en columna Acciones para acceso directo a documentos

---

## PRIORIDAD MEDIA — Nuevas funcionalidades

### 6. Nueva pagina: Configuracion
- [ ] Crear pagina de Configuracion accesible solo para admin
- [ ] Crear tabla `configuracion` en BD para rutas de almacenamiento configurables
- [ ] Permitir al admin cambiar ruta de uploads
- [ ] Permitir al admin cambiar ruta de la base de datos
- [ ] Hacer configurable la ruta de la base de datos SQLite (no hardcodeada)
- [ ] Hacer configurable la ruta de la carpeta de uploads (no hardcodeada)
- [ ] Otras configuraciones del sistema (nombre del laboratorio, logo, etc.)

### 7. Nueva pagina: Ayuda
- [ ] Crear pagina de Ayuda que describa el funcionamiento del sistema
- [ ] Explicar cada modulo (Equipos, Ordenes, Inventario, Preventivo, Historial, Reportes, Documentos)
- [ ] Guia rapida para nuevos usuarios
- [ ] FAQ / Preguntas frecuentes
- [ ] Considerar un tour guiado o tooltips informativos

### 8. Inventario — Herramientas y materiales no consumibles
- [ ] **PROBLEMA:** Actualmente el inventario solo maneja repuestos que se DESCUENTAN al usarse
- [ ] Agregar soporte para herramientas que se ASIGNAN a un trabajo (no se descuentan)
- [ ] Agregar soporte para materiales reutilizables
- [ ] Definir modelo: quizas un campo `tipo_item` (consumible / reutilizable / herramienta)
- [ ] Ajustar la logica de OT: herramientas se asignan y se devuelven, repuestos se consumen
- [ ] Considerar modulo de control de herramientas prestadas/devueltas

### 9. Proveedores — Nuevo modulo
- [ ] **NECESIDAD:** El sistema debe manejar proveedores de mantenimiento correctivo
- [ ] Crear modelo `Proveedor` en la BD (nombre, contacto, especialidad, telefono, email, etc.)
- [ ] Crear CRUD de proveedores en el backend
- [ ] Crear vista de gestion de proveedores en el frontend
- [ ] Permitir asignar un proveedor a una OT de mantenimiento correctivo
- [ ] Considerar: proveedores de repuestos vs proveedores de servicio de mantenimiento
- [ ] Relacionar proveedores con equipos (proveedor principal de servicio, proveedor de repuestos)

---

## PRIORIDAD BAJA — Mejoras futuras (post v1.0)

### 10. Configuracion y despliegue
- [ ] Compilar frontend (`npm run build`) y servir desde FastAPI (un solo servidor/puerto)
- [ ] Empaquetar backend con PyInstaller (.exe sin necesidad de Python)
- [ ] Instalador profesional con Inno Setup / NSIS (wizard de instalacion)
- [ ] JWT secret en variable de entorno (.env)
- [ ] CORS restringido para produccion

### 11. Reportes y exportacion
- [ ] Exportacion de reportes a PDF
- [ ] Revisar y mejorar los 6 reportes existentes segun datos reales disponibles

### 12. Notificaciones y alertas
- [ ] Sistema de notificaciones (vencimiento de OTs, stock bajo, calibraciones proximas)
- [ ] Alertas por email (opcional)

### 13. Normalizacion
- [ ] Normalizacion de equipos con estandares UMDNS / GMDN
- [ ] Interfaz para gestion de estados (crear, editar colores) desde la UI

### 14. Offline y rendimiento
- [ ] Modo offline mejorado con Service Worker
- [ ] Optimizar consultas de BD para grandes volumenes de datos

---

## Roadmap — Paso H: Sugerencias de IA (RF07) — MAS ADELANTE

**NOTA:** La IA se implementara DESPUES de resolver los pendientes de prioridad alta.

### Capacidades planificadas
- [ ] Alertas de mantenimiento preventivo vencido o proximo
- [ ] Deteccion de patrones de falla por equipo (OTs recurrentes)
- [ ] Recomendacion de repuestos criticos (stock bajo segun historial de uso)
- [ ] Sugerencia de prioridad para OTs nuevas
- [ ] Prediccion de disponibilidad de equipos

### Pantallas que se veran afectadas
- HomeDashboard.vue → Panel "Sugerencias IA"
- EquiposView.vue → Boton "Insights IA" + indicador de salud
- OrdenesView.vue → Sugerencia automatica de prioridad al crear OT
- InventarioView.vue → Badge "IA: Reponer" en repuestos criticos
- PreventivoView.vue → Icono de alerta en tareas vencidas
- ReportesView.vue → Nueva pestana "Analisis Predictivo IA"

---

## Consultas abiertas (requieren decision)

| # | Consulta | Estado | Notas |
|---|----------|--------|-------|
| 1 | Como funciona el reporte de COSTOS si no hay precios? | Pendiente | Revisar endpoint, evaluar agregar precio a repuestos |
| 2 | Que roles definir? (admin, tecnico, visitante, otros?) | Pendiente | Definir permisos por rol |
| 3 | Como manejar herramientas/materiales no consumibles? | Pendiente | Nuevo campo tipo_item? Tabla separada? |
| 4 | Proveedores: solo servicio o tambien repuestos? | Pendiente | Definir alcance del modulo |
| 5 | Precios de repuestos: campo nuevo en modelo? | Pendiente | Necesario para reporte de costos real |

---

## Registro de Cambios Recientes

### v0.6.x — Mejoras UI implementadas
- Scrollbars verticales en modales cuando contenido excede
- Acceso a documentos desde columna de Acciones
- Nombres de archivos originales preservados en uploads
- Categoria "informe" agregada a documentos

### v0.6.0 — Documentos Adjuntos
- Modulo completo de gestion documental
- Componente DocumentosAdjuntos.vue con drag-and-drop
- Categorias: manual, fotografia, reporte, garantia, calibracion, informe, otro

### v0.5.0 — Reportes y Estadisticas
- 6 reportes con graficos interactivos
- ReportesView.vue con 6 pestanas

### v0.4.0 — Historial de Mantenimiento
- Timeline visual de eventos
- Registro automatico al completar OT

---

*Ultima actualizacion: 2026-05-27*
