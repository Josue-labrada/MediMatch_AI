FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# El paquete "backend" y las pruebas se montan como volúmenes en docker-compose
# (recarga en caliente); se copian también para que la imagen funcione sola.
COPY backend backend
COPY tests tests

EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "backend"]
