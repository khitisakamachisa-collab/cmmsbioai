@echo off
REM === Script para respaldar en GitHub con comentario personalizado ===

REM Cambia al directorio del proyecto
cd /d "D:\cmmsbioai"

echo ==============================
echo 1. Actualizando desde GitHub...
echo ==============================
git pull origin main

echo ==============================
echo 2. Preparando archivos para commit...
echo ==============================
git add -A

echo ==============================
echo 3. Escribe el mensaje del commit:
echo ==============================
set /p commitmsg=Mensaje: 

git commit -m "%commitmsg%"

echo ==============================
echo 4. Subiendo cambios a GitHub...
echo ==============================
git push origin main

echo ==============================
echo Proceso terminado.
pause
