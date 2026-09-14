@echo off
title CineStress Addon para Stremio (Servidor Local)
color 0B
cd /d "%~dp0"

echo =======================================================
echo     CineStress Stremio Addon (Servidor Local)
echo =======================================================
echo.
echo Iniciando servidor en http://127.0.0.1:7000 ...
echo.
echo 1. Abre Stremio.
echo 2. En la barra de busqueda de complementos pega:
echo    http://127.0.0.1:7000/manifest.json
echo 3. Pulsa "Instalar".
echo.
echo Para cerrar el servidor, simplemente cierra esta ventana.
echo =======================================================
echo.

python api\index.py
pause
