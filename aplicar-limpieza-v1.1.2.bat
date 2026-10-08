@echo off
REM ============================================================
REM  CMMS-BioAI - Limpieza v1.1.2 (Auditoria Paquete 1)
REM  Borra los archivos muertos identificados en
REM  AUDITORIA-CODIGO-v1.1.1.md (IDs A1-A9 y F2-F8).
REM  Ejecutar desde la RAIZ del repo (ej. D:\cmmsbioai).
REM  NO toca flujo, NO toca modelos, NO borra datos.
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0" 2>nul

echo.
echo  CMMS-BioAI v1.1.2 - Limpieza de archivos muertos
echo  Se borraran 20 items (backend y frontend). Ejemplos:
echo    - backend\api\routes\dashboard.py   (router no registrado)
echo    - frontend\src\OrdenesView.vue      (prototipo viejo)
echo    - frontend\dist_build\              (build stale pre-v1.0.2)
echo.
choice /C SN /M "Continuar [S] o No [N]"
if errorlevel 2 goto :fin

set BORRADOS=0
set FALTAN=0

echo.
echo --- BACKEND ---
call :del_file "backend\api\routes\dashboard.py"
call :del_file "backend\ml\diagnostico.py"
call :del_file "backend\ml\prueba_inferencia.py"
call :del_dir  "backend\routes"
call :del_file "backend\config.txt"
call :del_dir  "backend\D:\uploads"

echo.
echo --- FRONTEND ---
call :del_file "frontend\src\OrdenesView.vue"
call :del_file "frontend\src\views\EquiposView_.vue"
call :del_file "frontend\src\views\Sidebar.vue"
call :del_file "frontend\src\components\HelloWorld.vue"
call :del_file "frontend\src\components\WorkOrdersChart.vue"
call :del_file "frontend\src\components\EquipmentStatusChart.vue"
call :del_file "frontend\src\assets\vue.svg"
call :del_file "frontend\src\assets\vite.svg"
call :del_file "frontend\src\assets\hero.png"
call :del_file "frontend\public\icons.svg"
call :del_file "frontend\src\style.css"
call :del_file "frontend\src\style - copia.css"
call :del_file "frontend\dist_index.html"
call :del_dir  "frontend\dist_assets"
call :del_dir  "frontend\dist_build"

echo.
echo ============================================
echo  Resumen: %BORRADOS% borrado(s), %FALTAN% ya no existia(n)
echo  Listo. Ahora sobrescribe los archivos del parche,
echo  corre prueba_flujo_v111.py (51/51) y prueba_v112_limpieza.py
echo  (10/10), y haz "npm run build" en frontend.
echo ============================================
goto :fin

:del_file
if exist "%~1" (
    del /f /q "%~1" && echo   [BORRADO]    %~1 && set /a BORRADOS+=1
) else (
    echo   [no existe]  %~1 && set /a FALTAN+=1
)
goto :eof

:del_dir
if exist "%~1" (
    rmdir /s /q "%~1" && echo   [BORRADO]    %~1\ && set /a BORRADOS+=1
) else (
    echo   [no existe]  %~1\ && set /a FALTAN+=1
)
goto :eof

:fin
echo.
pause
endlocal
