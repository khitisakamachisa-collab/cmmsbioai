@echo off
REM Script simple para sincronizar con GitHub

REM Cambia al directorio del proyecto
cd /d "D:\Maestria\Modulo 6\CMMS\cmmsbioai"

echo ==============================
echo 1. Actualizando desde GitHub...
echo ==============================
git pull origin main

echo ==============================
echo 2. Subiendo cambios locales...
echo ==============================
git add .
git commit -m "calendario y proveedores"
git push origin main

echo ==============================
echo Proceso terminado.
pause
