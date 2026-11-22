@echo off
REM MediMatch IA - detiene los contenedores (doble clic en Windows).
REM El script vive en correr\windows\: sube dos niveles a la raiz del proyecto.
cd /d "%~dp0..\.."
docker compose down
echo MediMatch IA detenida.
pause
