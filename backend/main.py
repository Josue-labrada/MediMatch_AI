"""
Backend principal de MediMatch IA (puerto 8000).

Arranque:  uvicorn backend.main:app --reload
Documentación interactiva: http://localhost:8000/docs
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select

from .config import CORS_ORIGINS, SYNC_ON_STARTUP
from .db import SessionLocal
from .models import PlanDB
from .routes import catalogo, cuestionario, estado, recomendaciones, sync
from .services.sync import ErrorSincronizacion, sincronizar

log = logging.getLogger("medimatch")


def _sincronizar_si_vacio(intentos: int = 10) -> None:
    """Primera ejecución: llena PostgreSQL desde la API mock (que puede tardar en arrancar)."""
    for intento in range(1, intentos + 1):
        with SessionLocal() as db:
            try:
                if db.scalar(select(func.count()).select_from(PlanDB)):
                    return
                registro = sincronizar(db)
                log.warning("Catálogo inicial sincronizado: %s planes creados", registro.creados)
                return
            except (ErrorSincronizacion, Exception) as exc:  # noqa: BLE001
                log.warning("Sincronización inicial %s/%s falló: %s", intento, intentos, exc)
        time.sleep(2)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if SYNC_ON_STARTUP:
        _sincronizar_si_vacio()
    yield


app = FastAPI(
    title="MediMatch IA — Backend",
    description="Prototipo académico. Recomendación explicable sobre un catálogo SIMULADO de seguros.",
    version="1.0.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(estado.router)
app.include_router(catalogo.router)
app.include_router(sync.router)
app.include_router(recomendaciones.router)
app.include_router(cuestionario.router)
