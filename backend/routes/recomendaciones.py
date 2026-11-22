from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import PreferenciasIn, RecomendacionOut
from ..services.recomendador import recomendar

router = APIRouter(prefix="/api", tags=["recomendaciones"])


@router.post("/recomendaciones", response_model=RecomendacionOut)
def crear_recomendacion(preferencias: PreferenciasIn, db: Session = Depends(get_db)):
    """Valida el perfil, ejecuta el CSP y el ranking, y devuelve resultados explicados."""
    return recomendar(db, preferencias)
