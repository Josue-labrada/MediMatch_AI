# Imagen de desarrollo del frontend (Vite con recarga en caliente).
FROM node:20.18.1-alpine

WORKDIR /app

# Instalar dependencias primero aprovecha la caché de Docker:
# solo se reinstalan cuando cambia package.json / package-lock.json.
COPY package.json package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY . .

EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
