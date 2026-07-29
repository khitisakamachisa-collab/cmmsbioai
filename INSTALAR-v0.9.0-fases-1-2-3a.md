# CMMS-BioAI v0.9.0-alpha — Fases 1, 2 y 3a

> **⚠️ VERSIÓN EN DESARROLLO.** Esta es una versión parcial de v0.9.0 que incluye las Fases 1 (backend modelo+BD), 2 (backend endpoints) y 3a (frontend: plantilla + ConfiguracionView + Navbar).
>
> **NO incluye aún** la Fase 3b (EquiposView, PreventivoView, HomeDashboard, AyudaView). El frontend de Equipos y Preventivo NO funcionarán correctamente hasta que se aplique la Fase 3b.
>
> **Recomendación**: esta versión es para probar el backend y el Modo TEST. Para uso completo, esperar a la Fase 3b.

---

## 📋 Resumen de cambios

### Fase 1 — Backend (modelo + BD)
- `models/equipos.py`: Modelo Equipo v0.9.0 (sin campos obsoletos, con nuevos campos, FK a Proveedor)
- `models/preventivo.py`: `proxima_fecha` ahora es editable (no auto-calculada)
- `schemas/equipo.py`: Create/Update/Read con validaciones (condicion_origen enum, fechas garantía)
- `schemas/preventivo.py`: Agregado `proxima_fecha` a Create y Update
- `database.py`: 3 usuarios TEST (admin/tech/user) + migración `_migrate_equipo_v090()`
- `utils/meta_json.py`: `build_equipo_meta` actualizado con nuevos campos

### Fase 2 — Backend (endpoints)
- `api/routes/equipos.py`:
  - CRUD con nuevos campos
  - DELETE con verificación de dependencias (OTs, documentos, MP, historial)
  - PUT rechaza cambios en modelo/marca/numero_serie (campos no editables)
  - Import-excel actualizado (nuevas columnas, crea proveedores al vuelo)
  - Plantilla Excel/CSV actualizada (2 filas ejemplo, nuevos campos)
  - **Nuevo endpoint** `/equipos/from-proveedor-nombre` (crear proveedor al vuelo)
  - **Nuevo endpoint** `/equipos/proveedores` (dropdown para formulario)
- `api/routes/preventivo.py`: Eliminado auto-cálculo de `proxima_fecha`
- `api/routes/configuracion.py`:
  - Recuperación Capa 2 actualizada con nuevos campos del modelo Equipo
  - **Nuevo endpoint** `/configuracion/cargar-test` (carga 40 registros de ejemplo)
  - **Nuevo endpoint** `/configuracion/limpiar-bd` (borra todo excepto admin/tech/user y catálogos)

### Fase 3a — Frontend (parcial)
- `frontend/public/plantillas/plantilla_equipos.xlsx` y `.csv`: Regenerados con nuevos campos v0.9.0
- `frontend/src/components/Navbar.vue`: Badge "🧪 MODO TEST" que aparece cuando hay datos TEST cargados
- `frontend/src/views/ConfiguracionView.vue`: Nueva pestaña "🧪 Datos TEST" con botones Cargar/Limpiar

---

## 🚀 Cómo aplicar los cambios

### ⚠️ IMPORTANTE: Borrar la BD vieja

Como v0.9.0 cambia el esquema de la tabla `equipo` (elimina campos, agrega campos, cambia obligatoriedad), **debes borrar la BD vieja** antes de iniciar el backend:

```bash
cd backend
rm cmms_bioai.db
rm -rf uploads/  # opcional, pero recomendable para empezar limpio
```

Si quieres preservar tus datos de v0.8.3:
1. Haz un backup JSON desde Configuración → Capa 3 → Generar Backup → Descargar JSON
2. Borra la BD
3. Aplica v0.9.0
4. Restaura el backup desde Configuración → Capa 3 → Subir y Restaurar
   (Los campos obsoletos se ignoran, los nuevos quedan NULL)

### Pasos

1. **Detén** el backend y el frontend actuales.

2. **Copia los archivos** de esta carpeta a tu proyecto `cmmsbioai/`:
   - `backend/models/equipos.py`
   - `backend/models/preventivo.py`
   - `backend/schemas/equipo.py`
   - `backend/schemas/preventivo.py`
   - `backend/database.py`
   - `backend/utils/meta_json.py`
   - `backend/api/routes/equipos.py`
   - `backend/api/routes/preventivo.py`
   - `backend/api/routes/configuracion.py`
   - `frontend/public/plantillas/plantilla_equipos.xlsx`
   - `frontend/public/plantillas/plantilla_equipos.csv`
   - `frontend/src/components/Navbar.vue`
   - `frontend/src/views/ConfiguracionView.vue`

3. **Borra la BD vieja**:
   ```bash
   cd backend
   rm cmms_bioai.db
   ```

4. **Inicia el backend**:
   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```
   Verás en la consola:
   ```
   ✅ Seed: Usuario 'admin' creado (admin / admin)
   ✅ Seed: Usuario 'tech' creado (tech / tech)
   ✅ Seed: Usuario 'user' creado (user / user)
   ✅ Seed: 19 estados de equipo creados
   ✅ Seed: 5 estados de orden de trabajo creados
   ```

5. **Inicia el frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

6. **Entra** a http://localhost:5173 con `admin` / `admin`.

---

## ✅ Cómo probar el Modo TEST

1. Ve a **Configuración** → pestaña **🧪 Datos TEST**.
2. Haz clic en **🧪 Cargar datos TEST**.
3. Confirma el diálogo.
4. Verás un resumen con los registros creados (5 proveedores, 8 equipos, 5 repuestos, etc.).
5. El badge **🧪 MODO TEST** aparecerá en el navbar (esquina superior izquierda).
6. Ve a **Equipos**, **Proveedores**, **Ordenes**, **Preventivo** para ver los datos cargados.
7. Para limpiar: vuelve a **Configuración → Datos TEST → 🔴 Limpiar BD**, escribe "LIMPIAR" para confirmar.
8. El badge **🧪 MODO TEST** debería desaparecer del navbar.

---

## ⚠️ Limitaciones conocidas de esta versión

### Frontend NO actualizado (Fase 3b pendiente)

Las siguientes vistas **NO funcionarán correctamente** porque aún no se han actualizado para v0.9.0:

| Vista | Problema |
|-------|----------|
| `EquiposView.vue` | El formulario sigue mostrando campos obsoletos (registro_sanitario_bolivia, calibracion_proxima, responsable_tecnico_id) y no muestra los nuevos campos (observaciones, fecha_inicio_garantia, condicion_origen, proveedor_principal_id). Al guardar, el backend rechazará los campos obsoletos. |
| `PreventivoView.vue` | El formulario sigue auto-calculando `proxima_fecha` en el frontend (aunque el backend ya no lo hace). El campo `proxima_fecha` no es editable en el UI. |
| `HomeDashboard.vue` | No tiene el widget "MPs próximos a vencer" basado en `proxima_fecha`. |
| `AyudaView.vue` | No refleja los cambios del RF01 v0.9.0. |

### Workaround temporal

Mientras se aplica la Fase 3b:
- **Equipos**: puedes crear equipos vía API (Swagger UI en http://localhost:8000/docs) o vía import-excel con la nueva plantilla. NO uses el formulario de la UI.
- **Preventivo**: las MPs se crean correctamente vía API, pero el formulario de la UI sigue calculando `proxima_fecha` automáticamente.
- **Modo TEST**: funciona perfectamente para cargar y limpiar datos.

---

## 📦 Archivos incluidos (14 archivos)

### Backend (9 archivos)
1. `backend/models/equipos.py`
2. `backend/models/preventivo.py`
3. `backend/schemas/equipo.py`
4. `backend/schemas/preventivo.py`
5. `backend/database.py`
6. `backend/utils/meta_json.py`
7. `backend/api/routes/equipos.py`
8. `backend/api/routes/preventivo.py`
9. `backend/api/routes/configuracion.py`

### Frontend (4 archivos)
10. `frontend/public/plantillas/plantilla_equipos.xlsx`
11. `frontend/public/plantillas/plantilla_equipos.csv`
12. `frontend/src/components/Navbar.vue`
13. `frontend/src/views/ConfiguracionView.vue`

### Scripts (1 archivo)
14. `scripts/regenerar_plantilla_equipos_v090.py` (para regenerar la plantilla si se actualizan los campos)

---

## 🔑 Usuarios TEST

| Username | Password | Rol | Uso |
|----------|----------|-----|-----|
| `admin` | `admin` | admin | Administrador del sistema |
| `tech` | `tech` | tecnico | Técnico biomédico (se le asignan OTs y MPs) |
| `user` | `user` | tecnico | Usuario regular |

> **Nota**: Las contraseñas son simples intencionalmente para facilitar el TEST. En producción, el administrador debe cambiarlas.

---

## 📋 Próximos pasos — Fase 3b

La Fase 3b (pendiente) actualizará:

1. `EquiposView.vue` — Formulario con nuevos campos, dropdown de proveedor con "crear nuevo", filtros (ubicacion/estado/condicion_origen), badges de garantía, advertencia ROJA para campos no editables
2. `PreventivoView.vue` — Formulario con `proxima_fecha` editable (date picker)
3. `HomeDashboard.vue` — Widget "MPs próximos a vencer"
4. `AyudaView.vue` — RF01 actualizado, Modo TEST documentado

Una vez aplicada la Fase 3b, el sistema será completamente funcional con v0.9.0.
