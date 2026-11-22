"""Configuración leída de variables de entorno (ver .env.example)."""
import os

# Sin contraseña en el código: viene de DATABASE_URL o de las variables POSTGRES_* (.env).
DATABASE_URL = os.getenv("DATABASE_URL") or (
    "postgresql+psycopg://"
    f"{os.getenv('POSTGRES_USER', 'medimatch')}:{os.getenv('POSTGRES_PASSWORD', '')}"
    f"@localhost:{os.getenv('DB_HOST_PORT', '5433')}/{os.getenv('POSTGRES_DB', 'medimatch')}"
)
MOCK_API_URL = os.getenv("MOCK_API_URL", "http://localhost:8001")
# Si la BD está vacía al arrancar, sincroniza el catálogo automáticamente.
SYNC_ON_STARTUP = os.getenv("SYNC_ON_STARTUP", "true").lower() == "true"
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
