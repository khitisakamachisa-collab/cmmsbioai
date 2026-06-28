@echo off
REM Script simple para sincronizar con GitHub

REM Cambia al directorio del proyecto
cd /d "D:\cmmsbioai"

echo ==============================
echo 1. Actualizando desde GitHub...
echo ==============================
git pull origin main

echo ==============================
echo 2. Subiendo cambios locales...
echo ==============================
git add .
git commit -m "version 9.0.4 equipos ok - contratos-frontend"
git push origin main

echo ==============================
echo Proceso terminado.
pause
