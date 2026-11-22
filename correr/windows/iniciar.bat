@echo off
REM MediMatch IA - inicio con doble clic en Windows.
REM Requiere Docker Desktop. Construye y levanta los contenedores y abre el navegador.
setlocal
REM El script vive en correr\windows\: sube dos niveles a la raiz del proyecto.
cd /d "%~dp0..\.."
title MediMatch IA
set "URL=http://localhost:5173"

echo ==============================================
echo   MediMatch IA - prototipo academico
echo   (catalogo y precios 100%% simulados)
echo ==============================================

where docker >nul 2>&1
if errorlevel 1 (
  echo ERROR: Docker no esta instalado.
  echo Instala Docker Desktop: https://www.docker.com/products/docker-desktop/
  pause
  exit /b 1
)

docker info >nul 2>&1
if not errorlevel 1 goto docker_listo

echo Iniciando Docker Desktop...
if exist "%ProgramFiles%\Docker\Docker\Docker Desktop.exe" start "" "%ProgramFiles%\Docker\Docker\Docker Desktop.exe"
set /a INTENTOS=0
:esperar_docker
timeout /t 2 /nobreak >nul
docker info >nul 2>&1
if not errorlevel 1 goto docker_listo
set /a INTENTOS+=1
if %INTENTOS% lss 90 goto esperar_docker
echo ERROR: Docker no respondio. Abre Docker Desktop manualmente y vuelve a intentar.
pause
exit /b 1

:docker_listo
if not exist .env copy .env.example .env >nul

echo Construyendo y levantando servicios (la primera vez tarda unos minutos)...
docker compose up -d --build --renew-anon-volumes
if errorlevel 1 (
  echo ERROR al levantar los servicios. Revisa: docker compose logs
  pause
  exit /b 1
)

echo Esperando a que la aplicacion responda en %URL% ...
set /a INTENTOS=0
:esperar_web
curl -fs %URL% >nul 2>&1
if not errorlevel 1 goto web_lista
set /a INTENTOS+=1
if %INTENTOS% geq 60 goto web_lenta
timeout /t 2 /nobreak >nul
goto esperar_web

:web_lenta
echo La aplicacion tarda en responder. Revisa: docker compose logs frontend
pause
exit /b 1

:web_lista
start "" %URL%
echo.
echo Listo: MediMatch IA corre en %URL%
echo Para detenerla, haz doble clic en detener.bat
pause
