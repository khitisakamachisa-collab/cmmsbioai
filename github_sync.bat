@echo off
chcp 65001 >nul 2>&1
title CMMS-BioAI - GitHub Sync
color 0A

:MENU
cls
echo ═════════════════════════════════════════
echo        CMMS-BioAI - GitHub Sync
echo ═════════════════════════════════════════
echo.
echo  [1] Subir cambios a GitHub (Push)
echo  [2] Bajar cambios de GitHub (Pull)
echo  [3] Ver estado actual (Status)
echo  [4] Salir
echo.
set /p OPCION=Seleccione una opcion (1-4):

if "%OPCION%"=="1" goto PUSH
if "%OPCION%"=="2" goto PULL
if "%OPCION%"=="3" goto STATUS
if "%OPCION%"=="4" goto FIN
echo Opcion invalida.
pause
goto MENU

:STATUS
cls
echo ─── Estado del repositorio ───
echo.
git status
echo.
echo ─── Ultimos 5 commits ───
git log --oneline -5
echo.
pause
goto MENU

:PUSH
cls
echo ─── Subir cambios a GitHub ───
echo.

REM Verificar si hay cambios
git diff --quiet 2>nul
if %ERRORLEVEL%==0 (
    git diff --cached --quiet 2>nul
    if %ERRORLEVEL%==0 (
        echo No hay cambios para subir.
        echo.
        pause
        goto MENU
    )
)

echo Cambios detectados:
echo.
git status -s
echo.

set /p MENSAJE=Ingrese mensaje del commit (o ENTER para mensaje auto):

REM Agregar todos los cambios
git add -A

REM Hacer commit
if "%MENSAJE%"=="" (
    for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set FECHA=%%a-%%b-%%c
    for /f "tokens=1-2 delims=: " %%a in ('time /t') do set HORA=%%a:%%b
    set MENSAJE=Actualizacion %FECHA% %HORA%
)

git commit -m "%MENSAJE%"
if %ERRORLEVEL% neq 0 (
    echo.
    echo Error al hacer commit.
    pause
    goto MENU
)

echo.
echo Subiendo a GitHub...
git push origin main
if %ERRORLEVEL% neq 0 (
    echo.
    echo ══════════════════════════════════════════════
    echo  ERROR: No se pudo subir a GitHub.
    echo.
    echo  Posibles causas:
    echo  - No esta autenticado (configure git credentials)
    echo  - No tiene permisos al repositorio
    echo  - No hay conexion a internet
    echo.
    echo  Para configurar autenticacion con token:
    echo    git remote set-url origin https://USUARIO:TOKEN@github.com/khitisakamachisa-collab/cmmsbioai.git
    echo ══════════════════════════════════════════════
) else (
    echo.
    echo ✓ Cambios subidos exitosamente a GitHub!
)

echo.
pause
goto MENU

:PULL
cls
echo ─── Bajar cambios de GitHub ───
echo.

echo Bajando cambios del repositorio...
git pull origin main
if %ERRORLEVEL% neq 0 (
    echo.
    echo ══════════════════════════════════════════════
    echo  ERROR: No se pudo bajar de GitHub.
    echo.
    echo  Posibles causas:
    echo  - No esta autenticado (configure git credentials)
    echo  - Conflictos con cambios locales
    echo  - No hay conexion a internet
    echo ══════════════════════════════════════════════
) else (
    echo.
    echo ✓ Cambios bajados exitosamente de GitHub!
)

echo.
pause
goto MENU

:FIN
echo.
echo Hasta luego!
exit /b 0
