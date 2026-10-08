# AUDITORÍA DE CÓDIGO — CMMS-BioAI v1.1.1

**Fecha:** 2026-10-08 · **Alcance:** todo el repo tal como está ahora (post parche v1.1.1)
**Método:** inventario archivo por archivo + cruces de conectividad (endpoint↔UI, modelo↔router, import↔uso), verificación directa de cada hallazgo con cita `archivo:línea`.
**Propósito:** base de decisiones para limpiar código suelto, dar propósito a lo que queda y preparar v1.2 (red LAN) y v1.3 (solicitante + remota).

> **⬆ ACTUALIZACIÓN 2026-10-08 — PAQUETE 1 APLICADO (v1.1.2):** borrados los muertos (A1, A3–A9, F2–F8) y aplicados los fixes I1–I7 (A2 `schemas/user.py` no se borró: fue REVIVIDO por I6 con UserCreate/UserRead reales; `prueba_flujo_ot.py` marcado HISTÓRICO). Verificación: prueba_flujo_v111 51/51 + nueva prueba_v112_limpieza 10/10 + build frontend OK. Quedan pendientes D1–D9 (raíz, esperando decisión archivar/borrar), X1–X3 (commit GitHub) y los Paquetes 2 y 3.

**Cómo usar este documento:**
- Cada hallazgo tiene ID estable (`A1`…, `F1`…, `I1`…, `R1`…, `G1`…, `D1`…, `X1`…) para referenciarlo en el chat ("resolvamos I2 y A3").
- Estado: ☐ pendiente · ✅ resuelto · 🔵 diferido con fecha/paquete · ⛔ descartado con motivo.
- Secciones 7 y 8 son el checklist maestra: se va tachando a medida que se resuelve.

---

## 1. Resumen ejecutivo

| Dimensión | Cifra | Salud |
|---|---|---|
| Backend: routers | 17 archivos → **16 registrados** en `main.py:30-45` + 1 muerto (`dashboard.py`) | 🟢 buena |
| Backend: endpoints | **136 definidos / 135 vivos** (el muerto es `/dashboard/metrics`) | 🟢 buena |
| Backend: modelos | 12 archivos, **16 tablas, TODAS usadas** — cero modelos muertos | 🟢 excelente |
| Backend: schemas | 12 archivos → 11 en uso + **1 muerto completo** (`schemas/user.py`) | 🟡 |
| Backend: módulo ML | ~20 archivos → **10 vivos** (cadena `ia.py`), 2 CLI de tesis (`main_pipeline`, `exportar`), **2 muertos** (`diagnostico.py`, `prueba_inferencia.py`) | 🟢 |
| Scripts de prueba | 6 → 1 canónico (`prueba_flujo_v111.py` 51/51), **2 rotos tras v1.1.1**, 2 tocan BD real | 🟡 |
| Frontend: vistas | 17 archivos en `views/` → **15 vivas** + 2 huérfanas (+1 huérfana en `src/`) | 🟡 |
| Frontend: componentes | 6 → 3 vivos + **3 muertos** (HelloWorld, 2 charts) | 🟡 |
| Builds | 2 builds **stale pre-v1.0.2** (`dist_assets/`, `dist_build/`, `dist_index.html`) | 🟡 |
| Raíz del repo | 18 README versionados + 3 INSTALAR + 3 LEEME + 8 archivos sueltos/históricos + 2 vacíos | 🔴 dispersión |
| Git/respaldo | **208 archivos sin commit; todo v1.0.0→v1.1.1 SIN SEGUIR en git** (ML, ia.py, PredictivoView…) — GitHub sigue en v0.9.x | 🔴 crítico para respaldo |

**5 conclusiones centrales:**

1. **El núcleo funcional está sano y entrelazado**: los 16 routers vivos tienen sus modelos y schemas; las 15 vistas usan la API; los 9 endpoints de `/reportes` tienen UI; la cadena ML viva está completa. No hay "medio módulo" roto.
2. **La suciedad es de bordes, no de núcleo**: ~12 archivos muertos (≈3.400 líneas), 2 builds stale, 18 READMEs históricos y archivos de sesión viejos en la raíz. Nada de eso afecta al usuario final hoy, pero confunde al desarrollo futuro.
3. **Hay 3 bugs pequeños de coherencia post-v1.1.1** visibles al usuario (KPI de OTs pendientes cuenta Canceladas; calendario ignora "En Monitoreo"; mensajes que recomiendan un endpoint eliminado) + 1 de seguridad barata de tapar (`GET /users/` devuelve `hashed_password`).
4. **El mayor riesgo no es de código sino de respaldo**: GitHub no tiene ni el módulo IA. El `.db` no se versiona (correcto), pero el código sí debería.
5. La deuda que ya conocíamos (auth real H7, baseURL hardcodeada, pytest, paginación) está confirmada con evidencia exacta y se mantiene planificada — nada nuevo urgente salvo lo del punto 3.

---

## 2. Inventario — Backend

### 2.1 Routers y endpoints (17 archivos, 136 endpoints)

| Router (archivo) | Prefix | Endpoints | Estado |
|---|---|---|---|
| auth.py | /token | 1 | ✅ vivo (único emisor JWT) |
| users.py | /users | 2 | ✅ vivo (⚠ ver I6) |
| equipos.py | /equipos | 13 | ✅ vivo |
| ordenes.py | /ordenes | 16 | ✅ vivo — núcleo flujo R1–R8 |
| estados.py | /estados-equipo | 4 | ✅ vivo pero **SIN UI** (G9) |
| repuestos.py | /repuestos | 10 | ✅ vivo |
| preventivo.py | /preventivo | 6 | ✅ vivo |
| historial.py | /historial | 6 | ✅ vivo |
| reportes.py | /reportes | 9 | ✅ vivo — todos con UI |
| documentos.py | /documentos | 5 | ✅ vivo |
| herramientas.py | /herramientas | 9 | ✅ vivo |
| configuracion.py | /configuracion | 12 | ✅ vivo (archivo más grande: 1.672 l) |
| proveedores.py | /proveedores | 9 | ✅ vivo |
| contratos.py | /contratos | 9 | ✅ vivo |
| costos.py | /costos | 7 | ✅ vivo |
| ia.py | /ia | 11 | ✅ vivo — RF07 |
| **dashboard.py** | /dashboard | 1 | ⛔ **MUERTO**: no está en `main.py:7,30-45`; además busca estados "Pendiente"/"En Progreso" (`dashboard.py:40,43`) que no existen en el seed → devolvería ceros (A1) |

### 2.2 Modelos (12 archivos / 16 tablas — todos usados)

`Usuario`, `Equipo` (con `tipo_equipo`+`criticidad` RF07), `EstadoEquipo` (11 seed), `EstadoOT` (6 seed con En Monitoreo), `OrdenTrabajo` (sellos R5 + `parent_ot_id`/`failure_sequence` v1.1.1), `BitacoraOT`, `Repuesto`+`OtRepuestoUtilizado` (PK compuesta), `TareaPreventiva`+`TareaRepuesto`, `EventoHistorial`, `DocumentoAdjunto`, `Herramienta`, `Proveedor`+`ContactoProveedor`, `OtCostoAdicional`, `Contrato`+`ContratoEquipo`. Cero modelos muertos — el entrelazado aquí está completo.

### 2.3 Schemas (12 archivos)

11 en uso. ⛔ **`schemas/user.py` (`UserCreate`/`UserRead`) nunca importado** (F1): `POST /users/` recibe un `dict` crudo (`users.py:15`) y `GET /users/` devuelve el ORM con `hashed_password` (`users.py:12`) — ver I6.

### 2.4 Módulo ML (~20 archivos)

```
ia.py (router vivo) ──► predictor ──► preprocesamiento, metrics_logger, xai, config
                    ├─► entrenar ──► pln, rul, xai, metrics_logger, config
                    ├─► ablation ──► pln, rul, validacion
                    ├─► validacion ──► preprocesamiento
                    └─► config, metrics_logger
CLI tesis: main_pipeline ──► data/generar_dataset + exportar    (python -m ml.main_pipeline)
MUERTOS:  diagnostico.py (ejecuta a nivel de import, diagnostico.py:7)
          prueba_inferencia.py (demo manual, 0 referencias)
Muerto menor: config.py:32-33 VECTORIZADOR_N1/N2 (nadie carga ese joblib)
Datos: dataset_ot_bombas.csv (220 OTs) → leído por entrenar.py:31-34 ✔
```

### 2.5 Scripts de prueba (6 en `backend/`)

| Script | BD | Vigencia tras v1.1.1 |
|---|---|---|
| `prueba_flujo_v111.py` (51 checks) | temporal | ✅ **CANÓNICA** |
| `prueba_flujo_ot.py` (37 checks, v1.1.0) | temporal | ❌ roto: llama `POST /ordenes/{id}/reabrir` (:144,146,156) que ya no existe y espera bitácora "reabierta" (:190-192) → fallaría (I4) |
| `prueba_api_ia.py` (10 escenarios) | **REAL** sin limpieza | ❌ roto: crea OTs con `estado_id: 4` (:48) y R1 ahora responde 400; además contamina la BD real |
| `prueba_mtbf.py` | REAL con autolimpieza | ✅ vigente (riesgo moderado) |
| `limpiar_datos_prueba.py` | REAL | ✅ utilitario vigente |
| `verificar_entorno_ia.py` | no toca BD | ✅ vigente |

### 2.6 database.py

8 migraciones artesanales idempotentes (`_migrate_*`) + `seed_database()`: 11 estados de equipo, 5 estados OT base + "En Monitoreo" idempotente (:258-262). Docstring desactualizado: dice "19 estados"/"5 estados" (:194-195) — ver I5.

---

## 3. Inventario — Frontend

### 3.1 Router y vistas

15 rutas (index.js:20-94), **sin lazy loading ni guards** (G3). Todas las vistas mapeadas existen. La cadena de layout real es `App.vue:4 → components/Navbar.vue:5 → components/Sidebar.vue`.

| Viva (15) | Uso API principal | Huérfana (3) | Motivo |
|---|---|---|---|
| LoginView | POST /token | `src/OrdenesView.vue` (raíz, 211 l) | prototipo v0.9 con `tecnico_asignado_id: 1` hardcodeado (:17); nadie la importa (F2) |
| HomeDashboard | 6 GET (equipos, ordenes, estados, repuestos, preventivo) | `views/EquiposView_.vue` (1.227 l) | versión vieja; llama endpoints que el vivo ya no usa (F3) |
| EquiposView | CRUD + estados + proveedores + historial + contratos | `views/Sidebar.vue` (397 l) | copia anterior SIN ítem Predictivo; la activa es components/ (F4) |
| OrdenesView (1.360 l) | CRUD OT + 8 acciones flujo + bitácora + bitacora-csv | | |
| PlanificacionView | ordenes, equipos, users, preventivo, estados | | |
| PreventivoView | CRUD preventivo + generar-ot | | |
| InventarioView | CRUD repuestos+herramientas + import-excel | | |
| ProveedoresView | CRUD proveedores + contactos | | |
| ContratosView | CRUD contratos + import + export.js | | |
| HistorialView | CRUD historial | | |
| ReportesView | 8 GET /reportes/* | | |
| PredictivoView | 8 GET /ia/* + POST /ia/entrenar | | |
| UsuariosView | GET/POST /users | | |
| ConfiguracionView | 11 endpoints /configuracion/* | | |
| AyudaView | (sin API; docs embebidas) | | |

### 3.2 Componentes y archivos sueltos

| Archivo | Estado |
|---|---|
| components/Navbar.vue | ✅ vivo (⚠ R4: alertas MOCK hardcodeadas :22-44; llama /proveedores/ y /configuracion/ propias) |
| components/Sidebar.vue | ✅ vivo (14 links) |
| components/DocumentosAdjuntos.vue | ✅ vivo (5 vistas) |
| components/HelloWorld.vue | ⛔ muerto — residuo plantilla Vite (F5) |
| components/WorkOrdersChart.vue + EquipmentStatusChart.vue | ⛔ muertos — HomeDashboard dibuja con chart.js directo (F6) |
| src/style.css (0 bytes) + "src/style - copia.css" (296 l) | ⛔ muertos — main.js no importa CSS global (F7) |
| src/assets/vue.svg, vite.svg, hero.png + public/icons.svg | ⛔ muertos en cadena (solo HelloWorld los usa) |
| frontend/dist_index.html + dist_assets/ + dist_build/ | ⛔ 2 builds stale pre-v1.0.2 (sin mtbf/etapas/reincidencia); el outDir real `dist/` no existe en el repo (F8) |

### 3.3 api.js y servicios

- `api.js` (23 l): única export = instancia axios; `baseURL: 'http://127.0.0.1:8000'` **hardcodeada** (api.js:4) y repetida en ReportesView.vue:149,173 y PredictivoView.vue:142 → **4 sitios** (G2, ya planificado v1.2 Fase A).
- Interceptores: solo request (Bearer token). **Sin interceptor de respuesta** (no hay manejo global de 401) (G3).
- `export.js`: 2 funciones; único consumidor ContratosView → **3 patrones de exportación distintos** en la app (R3).
- `console.log`: 0. `console.error/warn`: ~70, todos legítimos en catches. `TODO/FIXME`: 0 reales. 🟢

---

## 4. Mapa de conectividad backend ↔ frontend

**Cobertura UI de reportes: 9/9 endpoints `/reportes` tienen pestaña o botón** (mtbf y etapas + bitácora-csv con export CSV; 6 pestañas sin export — G8).

**Endpoints vivos SIN UI (el frontend nunca los llama):**

| Grupo | Endpoints sin UI | Observación |
|---|---|---|
| /estados-equipo (completo) | 4 | el frontend usa `GET /equipos/estados` (duplicado, R2) |
| IA | GET /ia/h1, /ia/logs, POST /ia/predict | predict manual es el instrumento H2 → reservado tesis, NO borrar |
| Contratos | /tipos, /monedas, /periodicidades, GET /{id} | ContratosView hardcodea los catálogos (:38-39) (R5) |
| Costos | /tipos/lista, /ot/{id}/total, GET /{id} | totales calculados en cliente |
| Equipos | POST /equipos/estados, plantilla-csv, plantilla-excel | plantillas estáticas sustituyeron al backend (README:1117 lo documenta como respaldo Swagger) |
| Repuestos/Herramientas | plantilla-* | ídem |
| Órdenes | POST /ordenes/estados/ | crear estado OT desde UI no existe |
| Historial | PUT /historial/{id}, GET /{id} | edición de eventos desde UI no existe |
| Configuración | GET /configuracion/backup/descargar | backup se descarga por otra vía |
| Dashboard | GET /dashboard/metrics | ⛔ ni siquiera registrado (A1) |

**Veredicto:** no hay endpoints "rotos" de conexión; los sin-UI son o respaldo documentado, o instrumentos de tesis (H2), o features futuras — se decide caso a caso en §6.

---

## 5. Hallazgos (con ID, prioridad y evidencia)

Prioridad: 🔴 alta (decide pronto o rompe algo) · 🟡 media (limpieza/consistencia) · ⚪ baja (cosmético o diferido).

### A — Código muerto BACKEND (borrable/archivable)

| ID | Pri | Hallazgo | Evidencia |
|---|---|---|---|
| A1 | 🟡 | `api/routes/dashboard.py` completo: router no registrado + busca estados inexistentes ("Pendiente"/"En Progreso") | dashboard.py:9-11,40,43; main.py:7,30-45 |
| A2 | 🟡 | `schemas/user.py` muerto completo (UserCreate/UserRead sin importadores) | users.py:15 recibe dict |
| A3 | 🟡 | `ml/diagnostico.py` — script debug, 0 referencias, y ejecuta a nivel de import (peligro si alguien lo importa) | diagnostico.py:7 |
| A4 | 🟡 | `ml/prueba_inferencia.py` — demo manual, 0 referencias | — |
| A5 | 🟡 | `backend/routes/__init__.py` — paquete huérfano vacío ("Vacío por ahora"), nadie importa `routes` | routes/__init__.py:1 |
| A6 | ⚪ | `ml/config.py:32-33` constantes VECTORIZADOR_N1/N2 sin uso | — |
| A7 | ⚪ | `preventivo.py:151` expresión residual `if False` dentro de dict | — |
| A8 | 🟡 | `backend/config.txt` — nadie lo lee; difiere del config.json activo (confunde) | config.txt:4 |
| A9 | 🟡 | Carpeta fantasma `backend/D:\uploads/` creada por `config.json` con `uploads_base` Windows en un entorno no-Windows; **además está sin seguimiento en git** | config.json:6 |

### F — Código muerto FRONTEND

| ID | Pri | Hallazgo | Evidencia |
|---|---|---|---|
| F1 | ⚪ | (reservado — ver A2) | — |
| F2 | 🟡 | `src/OrdenesView.vue` raíz (211 l): prototipo con estado libre y técnico fijo | src/OrdenesView.vue:12-17 |
| F3 | 🟡 | `views/EquiposView_.vue` (1.227 l): versión antigua huérfana | sin importadores |
| F4 | 🟡 | `views/Sidebar.vue`: copia vieja sin ítem Predictivo | Navbar.vue:5 usa components/ |
| F5 | ⚪ | `components/HelloWorld.vue` + assets vue.svg/vite.svg/hero.png + public/icons.svg: residuo plantilla Vite | HelloWorld.vue:3-5,31 |
| F6 | ⚪ | WorkOrdersChart.vue + EquipmentStatusChart.vue muertos | HomeDashboard.vue:5-8 |
| F7 | 🟡 | `style.css` (0 bytes) y `style - copia.css` (296 l) sin importar | main.js:1-8 |
| F8 | 🔴 | `dist_index.html` + `dist_assets/` + `dist_build/`: 2 builds stale pre-v1.0.2 → riesgo de servir frontend viejo; el `dist/` real ni existe | hashes sin marcadores v1.1.1; vite.config.js |

### I — Inconsistencias / bugs de coherencia

| ID | Pri | Hallazgo | Evidencia |
|---|---|---|---|
| I1 | 🔴 | **KPI "OTs pendientes" del dashboard cuenta las CANCELADAS como pendientes**: el set de cerrados contiene `'cerrada'` (no existe) y omite `'cancelada'` | HomeDashboard.vue:58 |
| I2 | 🔴 | **Calendario ignora "En Monitoreo"**: `tieneOt` chequea `estado_id 1|2|3` y el nuevo estado activo es id 6 → un MP con OT en monitoreo aparece como "sin OT" | PlanificacionView.vue:146 |
| I3 | 🟡 | **Mensajes que recomiendan `/reabrir` (endpoint eliminado en v1.1.1)**: PUT de OT cerrada y /asignar dicen "Use la acción /reabrir" → hoy devolvería 404 | ordenes.py:364, 427 |
| I4 | 🟡 | `prueba_flujo_ot.py` (37 checks) roto tras v1.1.1 (reabrir) — confunde al usuario si lo corre | prueba_flujo_ot.py:144-156,190-192 |
| I5 | ⚪ | Docstrings del seed desactualizados ("19 estados"/"5 estados"; son 11 y 6) | database.py:194-196 |
| I6 | 🔴 | **`GET /users/` devuelve `hashed_password` de todos los usuarios** (ORM crudo) + POST recibe dict crudo sin schema | users.py:9-15 |
| I7 | ⚪ | StreamingResponse importado 2 veces en reportes.py | reportes.py:2, 445 |
| I8 | 🟡 | `DELETE /ordenes/{id}` borra la OT dejando bitácora/repuestos/costos huérfanos y **sin revertir stock** (contrasta con DELETE /equipos que valida dependencias) | ordenes.py:670-678 |
| I9 | 🟡 | `crear_orden`/`actualizar_orden` no agregan cantidades por repuesto ni protegen la transición como el helper R8 → duplicar un repuesto en el payload dispara IntegrityError (PK compuesta) | ordenes.py:272-291, 375-403 vs 105-166 |

### R — Redundancias (unificar con propósito, no urgente)

| ID | Pri | Hallazgo | Evidencia |
|---|---|---|---|
| R1 | ⚪ | Gestión de repuestos/stock en 3 sitios dentro de ordenes.py con reglas divergentes (ver I9) | ordenes.py |
| R2 | ⚪ | Catálogo de estados de equipo servido 2 veces (`/equipos/estados` y `/estados-equipo/`) — el frontend solo usa una | equipos.py:33,40 vs estados.py |
| R3 | ⚪ | 3 patrones de export CSV (export.js, window.open hardcodeado, axios-blob) + 3 builds inline de StreamingResponse en reportes.py | export.js:93,125; reportes.py:591,784,837 |
| R4 | 🟡 | Navbar con **alertas/mensajes MOCK hardcodeados** y 2 llamadas API propias (/proveedores/, /configuracion/) | Navbar.vue:22-44,124,140 |
| R5 | ⚪ | ContratosView hardcodea tipos/monedas/periodicidades que el backend ya expone | ContratosView.vue:38-39 |

### G — Faltas / deuda técnica (la mayoría ya en roadmap)

| ID | Pri | Hallazgo | Evidencia | Plan |
|---|---|---|---|---|
| G1 | 🔴 | Sin verificación de JWT ni roles en NINGÚN endpoint; CORS `*`+credentials; SECRET_KEY hardcodeada | security.py:6; main.py:22-28; README:1125-1126 | H7 (v1.2/v1.3) |
| G2 | 🔴 | baseURL hardcodeada en 4 sitios | api.js:4; ReportesView:149,173; PredictivoView:142 | v1.2 Fase A |
| G3 | 🟡 | Sin guards de router (URLs internas accesibles sin login), sin lazy loading, sin interceptor 401 | router/index.js:97-100; api.js:11-22 | v1.2 Fase B |
| G4 | 🟡 | Sin pytest: solo scripts ad-hoc, 2 rotos, 2 sobre BD real | §2.5 | v1.3 o antes |
| G5 | ⚪ | Sin paginación backend (`.all()` en todos los listados) | ordenes.py:316, equipos.py:124… | diferir |
| G6 | ⚪ | Sin logging estructurado (`print()` disperso) | database.py, config.py:178-180… | diferir |
| G7 | ⚪ | Migraciones artesanales sin control de versiones (Alembic) | database.py:20-160 | aceptar como diseño offline-first, documentar |
| G8 | ⚪ | 6 pestañas de reportes sin export CSV | ReportesView | v1.3 |
| G9 | ⚪ | `/estados-equipo` completo sin UI (duplicado de /equipos/estados) | §4 | decidir con R2 |
| G10 | ⚪ | index.html `title="frontend"` `lang="en"`; package.json name/version genéricos | index.html:2,7 | cosmético v1.2 |
| G11 | 🟡 | `requirements.txt`: `passlib[bcrypt]` listado pero no importado (código usa bcrypt directo); `httpx2` en vez del estándar `httpx` para TestClient | requirements.txt:9,23 | v1.2 |
| G12 | ⚪ | Sin ruta 404 catch-all en router | router/index.js | cosmético |

### D — Raíz del repo / documentación

| ID | Pri | Hallazgo | Estado recomendado |
|---|---|---|---|
| D1 | 🟡 | 18 `README-v0.9.x.md` + `README-v0.9.23` + `README-v1.0.0.md` + 3 `INSTALAR-v0.8.x/0.9` | archivar en `docs/historico/` (GitHub ya guarda la historia en commits) |
| D2 | 🔴 | **`README.md` principal congelado en v0.9.3**: badge y "Versión actual: v0.9.3" (:3,38); Roadmap pone RF07 IA como "Prioridad Baja Post v1.0" (:1149) cuando ya está implementado y validado | actualizar a v1.1.1 (es la cara de GitHub) |
| D3 | 🔴 | **`PENDIENTES.md` congelado el 14-jun-2026**: dice RF07 ❌ pendiente, RF10/RF12 planificados — todo eso ya está hecho | actualizar o retirar (la Hoja de Ruta de AyudaView ya cumple esa función) |
| D4 | 🟡 | Históricos de sesión: `Readme.txt` (v0.8, dice IA pendiente), `user.md`, `user.txt`, `subir.txt`, `ruta.md`, `ideas.txt`, `modificaciones.txt` | archivar en docs/historico/ (ideas.txt y modificaciones.txt tienen valor de especificación histórica) |
| D5 | ⚪ | Archivos vacíos `git` y `main` en raíz (accidentales) | borrar |
| D6 | ⚪ | `package.json` en raíz con solo chart.js/vue-chartjs (residuo de instalación fuera de frontend/) | borrar |
| D7 | ⚪ | `gitignore - copia.txt` | borrar |
| D8 | 🟡 | `BD.xlsx`, `BD 2022.xlsx`, `BD.csv`, `Proveedores_Ejemplo.xlsx` en raíz — datos fuente (¿tesis? ¿seed demo?) | **decisión del usuario**: mover a docs/datos/ o fuera del repo |
| D9 | 🟡 | `versiones.txt` — ✅ al día hasta v1.1.1, convive bien | mantener |
| D10 | 🟡 | `LEEME-PATCH-v1.0.2/1.1/1.1.txt` — cadena de instrucciones por parche | mantener (son la guía de instalación incremental) |

### X — Git / respaldo (estado del repositorio)

| ID | Pri | Hallazgo | Evidencia |
|---|---|---|---|
| X1 | 🔴 | **208 archivos con cambios sin commit (194 modificados, 2.199 inserciones) y 14 sin seguimiento — TODO el trabajo v1.0.0→v1.1.1 (backend/ml/, ia.py, PredictivoView.vue, scripts de prueba, LEEMEs) NO está en GitHub**. Último commit: b242220 "mejoras en la presentacion mas formal" (v0.9.x). Si se pierde D:\cmmsbioai, se pierde el RF07 | git status |
| X2 | 🟡 | `.gitignore` no cubre la carpeta fantasma `backend/D:\uploads/` ni builds manuales (`dist_assets/`, `dist_build/`, `dist_index.html`) — hoy "untracked" ruido | .gitignore |
| X3 | 🟡 | Churn de binarios: 15+ .xlsx marcados "modificados" en cada snapshot (BD.xlsx, RF specs) → infla la historia de GitHub | git status |

---

## 6. Plan de acción sugerido (3 paquetes)

**PAQUETE 1 — "Limpieza v1.1.2" (~1,5–2 h, riesgo bajo)** *— dejar el terreno limpio antes de los nuevos flujos que están simulando*
- Borrar muertos: A1, A3, A4, A5, A8, A9 (carpeta), F2, F3, F4, F5, F6, F7, F8 (+ assets asociados).
- Fixes de coherencia: I1 (canceladas), I2 (En Monitoreo), I3 (mensajes /reabrir → /reincidencia), I7 (import duplicado), I5 (docstrings).
- Seguridad barata: I6 (schema UserRead sin hashed_password en respuesta de /users/).
- Condicional al archivo roto: I4 → opción A: actualizar prueba_flujo_ot.py a la era v1.1.1; opción B: marcarlo como "histórico v1.1.0" en su cabecera (la canónica es v111).
- Raíz: D5, D6, D7 (borrar); D1, D4 (mover a docs/historico/).
- NO toca flujo, NO toca modelos, NO requiere migración. Prueba: correr `prueba_flujo_v111.py` (51/51) + build frontend.

**PAQUETE 2 — "Con v1.2 Fase A (red LAN)"** *— lo que ya era plan y la auditoría confirma*
- G2 baseURL dinámica (única fuente en api.js; matar las 3 hardcodeadas de Reportes/Predictivo).
- X1 commit + push de TODO lo pendiente (v1.1.2 incluido) + X2 .gitignore ampliado + X3: mover BD*.xlsx a docs/datos/ (o fuera) para frenar churn.
- D2 README.md a v1.1.1 · D3 PENDIENTES.md.
- G11 requirements (httpx + quitar passlib).
- R4 Navbar: quitar MOCKs (o alimentarlos de /ia/resumen).

**PAQUETE 3 — "Diferidos v1.3+ / con H7"**
- G1 auth real + roles (H7) · G3 guards+lazy+interceptor 401 (v1.2 Fase B) · G4 pytest · G5 paginación · G6 logging · R1/R2/R3 unificaciones · G8 CSV en 6 reportes · G9/G10/G12 · I8 (borrado de OT con limpieza y reversión) · I9/R1 (unificar gestión de repuestos en un solo helper).

---

## 7. Checklist maestra de resolución

**Paquete 1 (v1.1.2 limpieza) — ✔ APLICADO 2026-10-08**
- [x] A1 dashboard.py fuera
- [x] A3 ml/diagnostico.py fuera · [x] A4 ml/prueba_inferencia.py fuera
- [x] A5 backend/routes/ fuera · [x] A8 config.txt fuera · [x] A9 carpeta `D:\uploads` fuera
- [x] A2 schemas/user.py — RESUELTO reviviéndolo (I6): ahora UserCreate/UserRead reales usados por users.py
- [x] A6 constantes VECTORIZADOR_N1/N2 fuera · [x] A7 residuo `if False` fuera
- [x] F2 src/OrdenesView.vue fuera · [x] F3 EquiposView_.vue fuera · [x] F4 views/Sidebar.vue fuera
- [x] F5 HelloWorld+assets fuera · [x] F6 charts muertos fuera · [x] F7 CSS muertos fuera · [x] F8 builds stale fuera
- [x] I1 KPI canceladas · [x] I2 calendario En Monitoreo (por nombre, no id) · [x] I3 mensajes /reincidencia · [x] I7 import · [x] I5 docstrings
- [x] I6 /users/ sin hashed_password (UserRead) + POST validado (UserCreate) · prueba_v112_limpieza.py 10/10
- [x] I4 prueba_flujo_ot.py marcado HISTÓRICO v1.1.0 — NO EJECUTAR (canónica: prueba_flujo_v111.py)
- [ ] D5-D7 borrar · [ ] D1+D4 → docs/historico/  *(PENDIENTE decisión del usuario: archivar vs borrar)*

**Paquete 2 (v1.2 Fase A)**
- [ ] G2 baseURL única · [ ] X1 commit+push completo · [ ] X2 .gitignore · [ ] X3 datos xlsx fuera del código
- [ ] D2 README.md v1.1.1 · [ ] D3 PENDIENTES.md · [ ] G11 requirements · [ ] R4 Navbar sin MOCKs

**Paquete 3 (diferidos)**
- [ ] G1 H7 auth/roles · [ ] G3 guards/lazy/401 · [ ] G4 pytest · [ ] G5 paginación · [ ] G6 logging
- [ ] R1 helper único de repuestos (con I9) · [ ] R2 catálogo estados único (con G9) · [ ] R3 export CSV unificado
- [ ] G8 CSV 6 reportes · [ ] I8 borrado OT seguro · [ ] G10/G12 cosméticos

---

## 8. Lo que NO hay que tocar (decisiones ya tomadas que funcionan)

- **Máquina de estados R1–R8 y sus 6 estados OT** — validada por el usuario; las migraciones v1.1.0/v1.1.1 son idempotentes y están bien.
- **`POST /ia/predict` (manual) y `/ia/h1`, `/ia/logs`** — sin UI pero son instrumento de tesis H2/auditoría; NO considerarlos muertos.
- **Plantillas estáticas en `/plantillas/`** — decisión documentada (README:1117); los endpoints plantilla-* del backend quedan como respaldo Swagger.
- **`BD.xlsx` / specs RF** — no mover sin tu OK (ver D8).
- **Estados de equipo en seed (11)** — reflejan tu especificación de modificaciones.txt.
- **worklog, versiones.txt, LEEME-PATCH-*, Hoja de Ruta de AyudaView** — documentación viva del hilo.

---

## 9. Decisiones abiertas para ti (cierre de auditoría)

1. **¿Paquete 1 ahora como v1.1.2 o lo meto dentro de v1.2?** — Recomiendo: ahora, 1,5–2 h, riesgo bajo, y deja el repo limpio justo antes de que me pases los flujos simulados.
2. **Históricos: ¿archivar en `docs/historico/` o borrar directo?** — Recomiendo archivar los con valor (READMEs 0.9, ideas.txt, modificaciones.txt, user*.txt, ruta.md) y borrar solo basura (git, main, copias, dist stale).
3. **¿`BD.xlsx` / `BD 2022.xlsx` son datos vivos de la tesis?** — Si sí: los muevo a `docs/datos/`. Si ya no: fuera del repo (peso y churn).
4. **`prueba_flujo_ot.py`: ¿lo actualizo a la era v1.1.1 o lo marco como histórico?** — Recomiendo marcar histórico (la canónica es prueba_flujo_v111.py) y no mantener dos baterías.
5. **dashboard.py**: ¿borrar (recomendado, HomeDashboard ya cubre la función) o registrar+actualizar?
