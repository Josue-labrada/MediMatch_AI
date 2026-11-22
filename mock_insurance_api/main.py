"""
Mock Insurance API (puerto 8001).

Simula un proveedor externo de catálogo de seguros. NO es una aseguradora real:
lee archivos JSON generados por generar_catalogo.py y los entrega por HTTP para
que el backend practique una integración real (petición HTTP → validación →
sincronización con PostgreSQL).

Los archivos se leen en cada petición, así que editar data/*.json cambia la
respuesta sin reiniciar el servicio.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, HTTPException

DATA_DIR = Path(__file__).parent / "data"

app = FastAPI(
    title="Mock Insurance API (simulada)",
    description="Catálogo ficticio de seguros de gastos médicos mayores para pruebas académicas.",
    version="1.0.0",
)


def _leer(nombre: str) -> dict:
    ruta = DATA_DIR / nombre
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=500, detail=f"No se pudo leer {nombre}: {exc}") from exc


def _combinar(base: dict, extra: dict) -> dict:
    """Une dos catálogos sin duplicar aseguradoras ni coberturas."""
    aseguradoras = {a["external_id"]: a for a in base["aseguradoras"] + extra["aseguradoras"]}
    coberturas = {c["codigo"]: c for c in base["coberturas"] + extra["coberturas"]}
    return {
        "aseguradoras": list(aseguradoras.values()),
        "coberturas": list(coberturas.values()),
        "planes": base["planes"] + extra["planes"],
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "servicio": "mock_insurance_api"}


@app.get("/api/v1/planes")
def listar_planes(incluir_novedades: bool = False) -> dict:
    """
    Catálogo simulado completo.
    incluir_novedades=true agrega los productos de data/novedades.json
    (escenario D: un producto nuevo cambia las recomendaciones).
    """
    catalogo = _leer("catalogo.json")
    if incluir_novedades:
        catalogo = _combinar(catalogo, _leer("novedades.json"))
    return {
        "simulado": True,
        "aviso": "Datos ficticios con fines académicos. No representan productos reales.",
        "generado_en": datetime.now(timezone.utc).isoformat(),
        **catalogo,
    }
