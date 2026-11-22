"""
Pruebas de integración: endpoints de FastAPI + PostgreSQL real.

Crean una base de datos aparte (medimatch_test) a partir de database/schema.sql, así
no tocan los datos de la demo. La API mock se sustituye leyendo sus mismos archivos
JSON, para probar la sincronización de forma determinista.

Requieren PostgreSQL: se ejecutan dentro de Docker (ver README). Si no hay conexión,
se marcan como "skipped".
"""
import os

import pytest

psycopg = pytest.importorskip("psycopg")
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from conftest import DATA_MOCK, RAIZ  # noqa: E402

from backend.config import DATABASE_URL as URL_BASE  # noqa: E402  (viene de .env / variables de entorno)
URL_TEST = make_url(URL_BASE).set(database="medimatch_test")


def _admin_conninfo():
    url = make_url(URL_BASE)
    return f"host={url.host} port={url.port or 5432} user={url.username} password={url.password} dbname={url.database}"


@pytest.fixture(scope="module")
def client():
    try:
        with psycopg.connect(_admin_conninfo(), autocommit=True, connect_timeout=3) as conn:
            conn.execute("DROP DATABASE IF EXISTS medimatch_test WITH (FORCE)")
            conn.execute("CREATE DATABASE medimatch_test")
    except psycopg.OperationalError as exc:
        pytest.skip(f"PostgreSQL no disponible: {exc}")

    engine = create_engine(URL_TEST.render_as_string(hide_password=False))
    with engine.begin() as conn:
        conn.exec_driver_sql((RAIZ / "database" / "schema.sql").read_text(encoding="utf-8"))

    from fastapi.testclient import TestClient

    from backend import main
    from backend.db import get_db
    from backend.schemas import CatalogoMock
    from backend.services import sync

    Sesion = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def get_db_test():
        db = Sesion()
        try:
            yield db
        finally:
            db.close()

    def catalogo_local(incluir_novedades):
        import json

        datos = json.loads((DATA_MOCK / "catalogo.json").read_text(encoding="utf-8"))
        if incluir_novedades:
            extra = json.loads((DATA_MOCK / "novedades.json").read_text(encoding="utf-8"))
            datos["aseguradoras"] += extra["aseguradoras"]
            datos["planes"] += extra["planes"]
        return CatalogoMock.model_validate({"simulado": True, **datos}), "prueba-local"

    original = sync.obtener_catalogo
    sync.obtener_catalogo = catalogo_local
    main.app.dependency_overrides[get_db] = get_db_test
    with TestClient(main.app) as c:  # sin lifespan-sync: SYNC_ON_STARTUP se desactiva abajo
        yield c
    main.app.dependency_overrides.clear()
    sync.obtener_catalogo = original
    engine.dispose()


@pytest.fixture(autouse=True, scope="module")
def _sin_sync_inicial():
    os.environ["SYNC_ON_STARTUP"] = "false"
    from backend import main

    main.SYNC_ON_STARTUP = False


PREFS_MATERNIDAD = {
    "presupuesto_mensual": 2700,
    "deducible_maximo": 30000,
    "coberturas_obligatorias": ["maternidad"],
}


def test_health(client):
    assert client.get("/health").json()["status"] == "ok"


def test_sync_crea_y_es_idempotente(client):
    primera = client.post("/api/sync", json={}).json()
    assert primera["resultado"] == "ok"
    assert primera["creados"] == 12
    segunda = client.post("/api/sync", json={}).json()
    assert (segunda["creados"], segunda["actualizados"], segunda["sin_cambios"]) == (0, 0, 12)
    planes = client.get("/api/planes").json()
    assert len(planes) == 12
    assert all(p["simulado"] for p in planes)


def test_opciones_salen_del_catalogo(client):
    opciones = client.get("/api/opciones").json()
    assert opciones["planes_activos"] == 12
    assert 30000 in opciones["deducibles"]
    assert {c["codigo"] for c in opciones["coberturas"]} >= {"maternidad", "dental"}


def test_recomendacion_estructura_y_explicacion(client):
    r = client.post(
        "/api/recomendaciones",
        json={
            "presupuesto_mensual": 5000,
            "deducible_maximo": 30000,
            "coberturas_obligatorias": ["hospitalizacion"],
            "coberturas_deseadas": ["maternidad", "dental"],
        },
    )
    assert r.status_code == 200
    datos = r.json()
    assert datos["simulado"] is True
    assert datos["candidatos_validos"] > 0
    assert datos["ranking"][0]["posicion"] == 1
    assert datos["ranking"][0]["componentes"]
    assert datos["ranking"][0]["restricciones_cumplidas"]
    assert sum(datos["pesos_aplicados"].values()) == pytest.approx(1, abs=1e-3)
    assert {e["algoritmo"] for e in datos["comparacion_algoritmos"]} == {"backtracking", "backtracking_fc"}
    assert datos["descartes"]
    puntajes = [o["puntaje"] for o in datos["ranking"]]
    assert puntajes == sorted(puntajes, reverse=True)


def test_restricciones_incompatibles_devuelven_cero_con_motivos(client):
    datos = client.post(
        "/api/recomendaciones",
        json={
            "presupuesto_mensual": 2000,
            "deducible_maximo": 30000,
            "coberturas_obligatorias": ["cobertura_internacional", "maternidad"],
        },
    ).json()
    assert datos["candidatos_validos"] == 0
    assert datos["ranking"] == []
    assert all(d["motivos"] for d in datos["descartes"])


def test_privacidad_rechaza_campos_no_previstos(client):
    r = client.post("/api/recomendaciones", json={**PREFS_MATERNIDAD, "edad": 34, "padecimientos": ["asma"]})
    assert r.status_code == 422


def test_cobertura_desconocida(client):
    r = client.post("/api/recomendaciones", json={**PREFS_MATERNIDAD, "coberturas_deseadas": ["inventada"]})
    assert r.status_code == 422


def test_escenario_D_sincronizar_producto_nuevo_cambia_resultado(client):
    client.post("/api/sync", json={"incluir_novedades": False})
    antes = client.post("/api/recomendaciones", json=PREFS_MATERNIDAD).json()

    sync = client.post("/api/sync", json={"incluir_novedades": True}).json()
    assert sync["creados"] == 1
    despues = client.post("/api/recomendaciones", json=PREFS_MATERNIDAD).json()
    assert despues["ranking"][0]["plan_external_id"] == "FARO-MATERNA"
    assert despues["candidatos_validos"] > antes["candidatos_validos"]

    # Al quitar la novedad de la API, el plan se desactiva (no se borra) y deja de recomendarse.
    sync = client.post("/api/sync", json={"incluir_novedades": False}).json()
    assert sync["desactivados"] == 1
    final = client.post("/api/recomendaciones", json=PREFS_MATERNIDAD).json()
    assert all(o["plan_external_id"] != "FARO-MATERNA" for o in final["ranking"])


CUESTIONARIO_BASE = {
    "edad": "30-44", "fuma": "no", "actividad": "media", "peso": "sobrepeso", "cronicas": "una",
    "hospitalizaciones": "ninguna", "familiar": "si", "maternidad": "no", "viajes": "no",
    "presupuesto_mensual": 5000,
}


def test_cuestionario_bayes_devuelve_analisis_y_recomendacion(client):
    client.post("/api/sync", json={})
    preguntas = client.get("/api/cuestionario/preguntas").json()
    assert {p["grupo"] for p in preguntas} == {"prior", "evidencia", "necesidad"}
    r = client.post("/api/cuestionario", json=CUESTIONARIO_BASE)
    assert r.status_code == 200
    d = r.json()
    assert sum(d["analisis"]["posterior"].values()) == pytest.approx(1)
    assert len(d["analisis"]["pasos"]) == 6
    assert d["recomendacion"]["candidatos_validos"] > 0
    assert d["preferencias_derivadas"]["coberturas_obligatorias"] == ["hospitalizacion"]


def test_cuestionario_rechaza_campos_extra_y_respuestas_invalidas(client):
    assert client.post("/api/cuestionario", json={**CUESTIONARIO_BASE, "nombre": "Ana"}).status_code == 422
    assert client.post("/api/cuestionario", json={**CUESTIONARIO_BASE, "fuma": "mucho"}).status_code == 422
