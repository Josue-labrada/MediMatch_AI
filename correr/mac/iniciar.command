#!/bin/bash
# MediMatch IA — inicio con doble clic en macOS.
# Requiere Docker Desktop. Construye y levanta los contenedores y abre el navegador.

# El script vive en correr/mac/: sube dos niveles a la raíz del proyecto.
cd "$(dirname "$0")/../.." || exit 1
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin"
URL="http://localhost:5173"

pausar() { echo; read -n 1 -s -r -p "Presiona cualquier tecla para cerrar..."; echo; }

echo "=============================================="
echo "  MediMatch IA · prototipo académico"
echo "  (catálogo y precios 100% simulados)"
echo "=============================================="

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker no está instalado."
  echo "Instala Docker Desktop: https://www.docker.com/products/docker-desktop/"
  pausar; exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Iniciando Docker Desktop..."
  open -a Docker
  for _ in $(seq 1 90); do
    docker info >/dev/null 2>&1 && break
    sleep 2
  done
  if ! docker info >/dev/null 2>&1; then
    echo "ERROR: Docker no respondió. Abre Docker Desktop manualmente y vuelve a intentar."
    pausar; exit 1
  fi
fi

[ -f .env ] || { cp .env.example .env && echo "Creado .env a partir de .env.example"; }

echo "Construyendo y levantando servicios (la primera vez tarda unos minutos)..."
# --renew-anon-volumes: si cambian las dependencias, node_modules se regenera.
if ! docker compose up -d --build --renew-anon-volumes; then
  echo "ERROR al levantar los servicios. Revisa: docker compose logs"
  pausar; exit 1
fi

echo "Esperando a que la aplicación responda en $URL ..."
for _ in $(seq 1 60); do
  curl -fs "$URL" >/dev/null 2>&1 && break
  sleep 2
done

if curl -fs "$URL" >/dev/null 2>&1; then
  open "$URL"
  echo
  echo "Listo: MediMatch IA corre en $URL"
  echo "Para detenerla, haz doble clic en detener.command"
else
  echo "La aplicación tarda en responder. Revisa: docker compose logs frontend"
fi
pausar
