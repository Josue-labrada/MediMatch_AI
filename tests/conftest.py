"""Utilidades compartidas por las pruebas."""
import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from backend.algorithms.modelos import OfertaCobertura, Plan, Regla, Variante  # noqa: E402

DATA_MOCK = RAIZ / "mock_insurance_api" / "data"


def cargar_catalogo_json(*archivos: str):
    """Convierte los JSON de la API mock en dataclasses (sin BD ni HTTP)."""
    planes, nombres = [], {}
    for archivo in archivos:
        datos = json.loads((DATA_MOCK / archivo).read_text(encoding="utf-8"))
        aseguradoras = {a["external_id"]: a["nombre"] for a in datos["aseguradoras"]}
        nombres.update({c["codigo"]: c["nombre"] for c in datos["coberturas"]})
        for p in datos["planes"]:
            planes.append(
                Plan(
                    id=len(planes) + 1,
                    external_id=p["external_id"],
                    nombre=p["nombre"],
                    aseguradora=aseguradoras[p["aseguradora_external_id"]],
                    nivel=p["nivel"],
                    suma_asegurada=p["suma_asegurada"],
                    variantes=tuple(
                        Variante(v["deducible"], v["coaseguro_porcentaje"], v["prima_mensual"]) for v in p["variantes"]
                    ),
                    coberturas=tuple(OfertaCobertura(c["codigo"], c["tipo"], c["costo_extra"]) for c in p["coberturas"]),
                    reglas=tuple(
                        Regla(r["tipo"], r["cobertura"], r["cobertura_objetivo"], r["valor"]) for r in p["reglas"]
                    ),
                )
            )
    return planes, nombres


@pytest.fixture(scope="session")
def catalogo_base():
    return cargar_catalogo_json("catalogo.json")


@pytest.fixture(scope="session")
def catalogo_con_novedades():
    return cargar_catalogo_json("catalogo.json", "novedades.json")
