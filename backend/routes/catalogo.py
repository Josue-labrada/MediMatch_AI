from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db import get_db
from ..schemas import CoberturaOut, OpcionesOut, PlanOut
from ..services import repositorio

router = APIRouter(prefix="/api", tags=["catálogo"])


@router.get("/planes", response_model=List[PlanOut])
def listar_planes(solo_activos: bool = False, db: Session = Depends(get_db)):
    """Catálogo persistido en PostgreSQL (datos simulados)."""
    return repositorio.listar_planes(db, solo_activos)


@router.get("/coberturas", response_model=List[CoberturaOut])
def listar_coberturas(db: Session = Depends(get_db)):
    return repositorio.listar_coberturas(db)


@router.get("/opciones", response_model=OpcionesOut)
def opciones(db: Session = Depends(get_db)):
    """Valores existentes en el catálogo para construir el formulario."""
    return repositorio.opciones_formulario(db)
