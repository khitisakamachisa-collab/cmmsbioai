@echo off
REM === Script mejorado para sincronizar con GitHub ===

REM Cambia al directorio del proyecto
cd /d "D:\cmmsbioai"

echo ==============================
echo 1. Actualizando desde GitHub...
echo ==============================
git pull origin main

echo ==============================
echo 2. Verificando cambios locales...
echo ==============================
git status

echo ==============================
echo 3. Preparando archivos para commit...
echo ==============================
git add -A

echo ==============================
echo 4. Escribe el mensaje del commit:
echo ==============================
set /p commitmsg=Mensaje: 
git commit -m "%commitmsg%"

echo ==============================
echo 5. Subiendo cambios a GitHub...
echo ==============================
git push origin main

echo ==============================
echo Proceso terminado.
pause
