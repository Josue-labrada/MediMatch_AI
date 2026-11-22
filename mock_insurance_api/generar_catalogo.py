"""
Genera el catálogo SIMULADO que sirve la Mock Insurance API.

Todas las aseguradoras, planes y precios son ficticios. Los valores se eligieron
para que existan casos de prueba interesantes (ver docs/GUIA_ALGORITMOS.md):
planes baratos con poca cobertura, planes premium caros, coberturas opcionales
con costo extra y reglas de compatibilidad que el CSP debe respetar.

Regla de precios (transparente y reproducible):
    prima_variante = prima_base_del_plan × FACTOR_DEDUCIBLE[deducible]
Un deducible más bajo implica una prima más alta.

Uso:
    python mock_insurance_api/generar_catalogo.py
Escribe data/catalogo.json (catálogo base) y data/novedades.json (productos
nuevos para el escenario D: sincronizar un producto y ver que cambia el resultado).
"""
import json
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"

# Factor multiplicativo sobre la prima base (deducible de referencia: 30,000 MXN).
FACTOR_DEDUCIBLE = {
    10_000: 1.38,
    20_000: 1.18,
    30_000: 1.00,
    50_000: 0.84,
    80_000: 0.70,
}

COBERTURAS = [
    ("hospitalizacion", "Hospitalización y cirugía", "Gastos hospitalarios, honorarios médicos y cirugía."),
    ("emergencia_extranjero", "Emergencia en el extranjero", "Atención de urgencias durante viajes fuera de México."),
    ("cobertura_internacional", "Cobertura internacional", "Tratamientos programados en hospitales fuera de México."),
    ("maternidad", "Maternidad", "Parto, cesárea y complicaciones del embarazo."),
    ("dental", "Dental", "Limpiezas, curaciones y extracciones básicas."),
    ("vision", "Visión", "Examen de la vista y apoyo para lentes."),
    ("salud_mental", "Salud mental", "Consultas de psicología y psiquiatría."),
    ("checkup", "Check-up preventivo", "Revisión médica preventiva anual."),
    ("telemedicina", "Telemedicina 24/7", "Orientación médica por videollamada."),
    ("ambulancia_aerea", "Ambulancia aérea", "Traslado aéreo en emergencias."),
]

ASEGURADORAS = {
    "alfa": "Alfa Salud (simulada)",
    "boreal": "Boreal Seguros (simulada)",
    "cumbre": "Cumbre Médica (simulada)",
    "delta": "Delta Protección (simulada)",
    "faro": "Faro Salud (simulada)",
}

I = "incluida"


def opc(costo):
    """Cobertura opcional con costo extra mensual."""
    return ("opcional", costo)


# Cada plan: variantes = [(deducible, coaseguro %)], coberturas = {codigo: incluida | opc(costo)},
# reglas = [(tipo, cobertura, objetivo_o_valor)].
PLANES_BASE = [
    # ---------------- Alfa Salud ----------------
    dict(id="ALFA-ESENCIAL", aseguradora="alfa", nombre="Alfa Esencial", nivel="Básico",
         suma=5_000_000, base=1450, variantes=[(30_000, 20), (50_000, 20), (80_000, 20)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": opc(120),
                     "dental": opc(180), "emergencia_extranjero": opc(150)},
         reglas=[]),
    dict(id="ALFA-PLUS", aseguradora="alfa", nombre="Alfa Plus", nivel="Intermedio",
         suma=15_000_000, base=2600, variantes=[(20_000, 10), (30_000, 10), (50_000, 15)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": I, "emergencia_extranjero": I,
                     "maternidad": opc(650), "dental": opc(190), "vision": opc(110), "salud_mental": opc(240)},
         reglas=[("deducible_max", "maternidad", 30_000)]),
    dict(id="ALFA-PREMIUM", aseguradora="alfa", nombre="Alfa Premium", nivel="Premium",
         suma=50_000_000, base=4900, variantes=[(10_000, 10), (20_000, 10), (30_000, 10)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": I, "emergencia_extranjero": I,
                     "maternidad": I, "salud_mental": I, "cobertura_internacional": opc(1100),
                     "ambulancia_aerea": opc(260), "dental": opc(210), "vision": opc(120)},
         reglas=[("requiere", "cobertura_internacional", "ambulancia_aerea")]),
    # ---------------- Boreal Seguros ----------------
    dict(id="BOREAL-BASICO", aseguradora="boreal", nombre="Boreal Básico", nivel="Básico",
         suma=4_000_000, base=1180, variantes=[(50_000, 20), (80_000, 20)],
         coberturas={"hospitalizacion": I, "telemedicina": opc(60), "checkup": opc(110),
                     "emergencia_extranjero": opc(170)},
         reglas=[]),
    dict(id="BOREAL-FAMILIAR", aseguradora="boreal", nombre="Boreal Familiar", nivel="Intermedio",
         suma=12_000_000, base=2350, variantes=[(20_000, 10), (30_000, 10), (50_000, 15), (80_000, 20)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": I, "maternidad": opc(520),
                     "dental": opc(160), "vision": opc(100), "salud_mental": opc(210)},
         reglas=[("deducible_max", "maternidad", 30_000), ("excluye", "dental", "vision")]),
    dict(id="BOREAL-GLOBAL", aseguradora="boreal", nombre="Boreal Global", nivel="Premium",
         suma=40_000_000, base=4300, variantes=[(20_000, 10), (30_000, 10), (50_000, 10)],
         coberturas={"hospitalizacion": I, "emergencia_extranjero": I, "telemedicina": I, "checkup": I,
                     "cobertura_internacional": opc(950), "maternidad": opc(700),
                     "ambulancia_aerea": opc(230), "salud_mental": opc(220)},
         reglas=[("deducible_max", "cobertura_internacional", 30_000), ("deducible_max", "maternidad", 30_000)]),
    # ---------------- Cumbre Médica ----------------
    dict(id="CUMBRE-PRACTICO", aseguradora="cumbre", nombre="Cumbre Práctico", nivel="Básico",
         suma=6_000_000, base=1620, variantes=[(30_000, 15), (50_000, 20)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "salud_mental": I, "checkup": opc(100),
                     "emergencia_extranjero": opc(140)},
         reglas=[]),
    dict(id="CUMBRE-INTEGRAL", aseguradora="cumbre", nombre="Cumbre Integral", nivel="Intermedio",
         suma=20_000_000, base=3100, variantes=[(10_000, 10), (20_000, 10), (30_000, 10), (50_000, 10)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": I, "emergencia_extranjero": I,
                     "salud_mental": I, "maternidad": opc(600), "dental": opc(170), "vision": opc(95),
                     "cobertura_internacional": opc(1200)},
         reglas=[("deducible_max", "maternidad", 20_000)]),
    dict(id="CUMBRE-ELITE", aseguradora="cumbre", nombre="Cumbre Élite", nivel="Premium",
         suma=80_000_000, base=6200, variantes=[(10_000, 10), (20_000, 10)],
         coberturas={c[0]: I for c in COBERTURAS},
         reglas=[]),
    # ---------------- Delta Protección ----------------
    dict(id="DELTA-JOVEN", aseguradora="delta", nombre="Delta Joven", nivel="Básico",
         suma=3_000_000, base=980, variantes=[(50_000, 20), (80_000, 25)],
         coberturas={"hospitalizacion": I, "telemedicina": I},
         reglas=[]),
    dict(id="DELTA-BALANCE", aseguradora="delta", nombre="Delta Balance", nivel="Intermedio",
         suma=10_000_000, base=2050, variantes=[(20_000, 15), (30_000, 15), (50_000, 20)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": opc(90), "maternidad": opc(480),
                     "emergencia_extranjero": opc(130), "dental": opc(150), "salud_mental": opc(200)},
         reglas=[("requiere", "maternidad", "checkup"), ("deducible_max", "maternidad", 30_000)]),
    dict(id="DELTA-VIAJERO", aseguradora="delta", nombre="Delta Viajero", nivel="Intermedio",
         suma=15_000_000, base=2900, variantes=[(30_000, 10), (50_000, 15)],
         coberturas={"hospitalizacion": I, "emergencia_extranjero": I, "telemedicina": I,
                     "cobertura_internacional": opc(780), "ambulancia_aerea": opc(210), "dental": opc(150)},
         reglas=[("requiere", "cobertura_internacional", "ambulancia_aerea"),
                 ("deducible_max", "cobertura_internacional", 30_000)]),
]

# Producto "nuevo" para el escenario D: solo aparece si se sincroniza con novedades.
PLANES_NOVEDADES = [
    dict(id="FARO-MATERNA", aseguradora="faro", nombre="Faro Materna", nivel="Intermedio",
         suma=12_000_000, base=1900, variantes=[(20_000, 10), (30_000, 10)],
         coberturas={"hospitalizacion": I, "telemedicina": I, "checkup": I, "maternidad": I,
                     "dental": opc(140)},
         reglas=[]),
]


def _plan_json(p):
    variantes = [
        {
            "deducible": deducible,
            "coaseguro_porcentaje": coaseguro,
            "prima_mensual": round(p["base"] * FACTOR_DEDUCIBLE[deducible] / 10) * 10,
        }
        for deducible, coaseguro in p["variantes"]
    ]
    coberturas = []
    for codigo, oferta in p["coberturas"].items():
        tipo, costo = (I, 0) if oferta == I else oferta
        coberturas.append({"codigo": codigo, "tipo": tipo, "costo_extra": costo})
    reglas = []
    for tipo, cobertura, objetivo in p["reglas"]:
        regla = {"tipo": tipo, "cobertura": cobertura, "cobertura_objetivo": None, "valor": None}
        if tipo == "deducible_max":
            regla["valor"] = objetivo
        else:
            regla["cobertura_objetivo"] = objetivo
        reglas.append(regla)
    return {
        "external_id": p["id"],
        "aseguradora_external_id": p["aseguradora"],
        "nombre": p["nombre"],
        "nivel": p["nivel"],
        "suma_asegurada": p["suma"],
        "moneda": "MXN",
        "variantes": variantes,
        "coberturas": coberturas,
        "reglas": reglas,
    }


def _catalogo_json(planes):
    usadas = sorted({p["aseguradora"] for p in planes})
    return {
        "aseguradoras": [{"external_id": a, "nombre": ASEGURADORAS[a]} for a in usadas],
        "coberturas": [{"codigo": c, "nombre": n, "descripcion": d} for c, n, d in COBERTURAS],
        "planes": [_plan_json(p) for p in planes],
    }


def main():
    DATA_DIR.mkdir(exist_ok=True)
    for nombre, planes in (("catalogo.json", PLANES_BASE), ("novedades.json", PLANES_NOVEDADES)):
        destino = DATA_DIR / nombre
        destino.write_text(json.dumps(_catalogo_json(planes), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{destino}: {len(planes)} planes")


if __name__ == "__main__":
    main()
