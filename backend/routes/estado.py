import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from ..config import MOCK_API_URL
from ..db import get_db
from ..models import Aseguradora, Cobertura, Consulta, PlanDB, Sincronizacion, VarianteDB
from ..schemas import EstadoOut, EstadoServicio, SyncOut

router = APIRouter(tags=["estado"])


@router.get("/health")
def health():
    return {"status": "ok", "servicio": "backend"}


@router.get("/api/estado", response_model=EstadoOut)
def estado(db: Session = Depends(get_db)):
    """Estado de los servicios y conteos del catálogo (panel administrativo)."""
    try:
        db.execute(text("SELECT 1"))
        bd = EstadoServicio(ok=True, detalle="PostgreSQL conectado")
    except Exception as exc:  # noqa: BLE001 - se reporta tal cual en el panel
        return EstadoOut(
            backend=EstadoServicio(ok=True, detalle="FastAPI en ejecución"),
            base_datos=EstadoServicio(ok=False, detalle=str(exc)[:200]),
            mock_api=EstadoServicio(ok=False, detalle="No verificado"),
            catalogo={},
            ultima_sincronizacion=None,
        )

    try:
        r = httpx.get(f"{MOCK_API_URL}/health", timeout=3)
        mock = EstadoServicio(ok=r.status_code == 200, detalle=f"{MOCK_API_URL} respondió {r.status_code}")
    except httpx.HTTPError as exc:
        mock = EstadoServicio(ok=False, detalle=f"Sin respuesta de {MOCK_API_URL}: {exc}")

    def contar(modelo, *condiciones):
        return db.scalar(select(func.count()).select_from(modelo).where(*condiciones)) or 0

    ultima = db.scalars(select(Sincronizacion).order_by(Sincronizacion.id.desc()).limit(1)).first()
    return EstadoOut(
        backend=EstadoServicio(ok=True, detalle="FastAPI en ejecución"),
        base_datos=bd,
        mock_api=mock,
        catalogo={
            "aseguradoras": contar(Aseguradora),
            "planes_activos": contar(PlanDB, PlanDB.activo.is_(True)),
            "planes_inactivos": contar(PlanDB, PlanDB.activo.is_(False)),
            "variantes": contar(VarianteDB),
            "coberturas": contar(Cobertura),
            "consultas": contar(Consulta),
        },
        ultima_sincronizacion=SyncOut.model_validate(ultima, from_attributes=True) if ultima else None,
    )
