from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import CuestionarioIn, CuestionarioOut, PreguntaOut
from ..services import cuestionario

router = APIRouter(prefix="/api/cuestionario", tags=["cuestionario (Bayes)"])


@router.get("/preguntas", response_model=List[PreguntaOut])
def listar_preguntas():
    """Preguntas y opciones del cuestionario (fuente única: backend/algorithms/bayes.py)."""
    return cuestionario.preguntas()


@router.post("", response_model=CuestionarioOut)
def evaluar_cuestionario(entrada: CuestionarioIn, db: Session = Depends(get_db)):
    """Estima el nivel de riesgo con la regla de Bayes y devuelve un seguro recomendado."""
    return cuestionario.evaluar(db, entrada)
