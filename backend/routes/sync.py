from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Sincronizacion
from ..schemas import SyncIn, SyncOut
from ..services.sync import ErrorSincronizacion, sincronizar

router = APIRouter(prefix="/api/sync", tags=["sincronización"])


@router.post("", response_model=SyncOut)
def ejecutar_sync(datos: SyncIn = SyncIn(), db: Session = Depends(get_db)):
    """Importa/actualiza el catálogo desde la Mock Insurance API sin duplicar registros."""
    try:
        return sincronizar(db, incluir_novedades=datos.incluir_novedades)
    except ErrorSincronizacion as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/historial", response_model=List[SyncOut])
def historial(db: Session = Depends(get_db)):
    return list(db.scalars(select(Sincronizacion).order_by(Sincronizacion.id.desc()).limit(20)))
