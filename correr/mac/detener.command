#!/bin/bash
# MediMatch IA — detiene los contenedores (doble clic en macOS).
# El script vive en correr/mac/: sube dos niveles a la raíz del proyecto.
cd "$(dirname "$0")/../.." || exit 1
export PATH="$PATH:/usr/local/bin:/opt/homebrew/bin:/Applications/Docker.app/Contents/Resources/bin"

docker compose down && echo "MediMatch IA detenida."
echo
read -n 1 -s -r -p "Presiona cualquier tecla para cerrar..."
echo
