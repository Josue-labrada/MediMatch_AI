# MediMatch IA

Prototipo académico (ITESO · Fundamentos de IA, 2026) que compara planes **simulados** de seguros de
gastos médicos mayores. Un **CSP con backtracking + forward checking** encuentra todas las
configuraciones que cumplen las restricciones del usuario, y una **función objetivo ponderada** las
ordena y explica. No cotiza, no vende pólizas y no usa datos de aseguradoras reales.

> Explicación detallada de los algoritmos: [`docs/GUIA_ALGORITMOS.md`](docs/GUIA_ALGORITMOS.md)

## Ejecutar (requiere Docker Desktop)

| Sistema | Iniciar | Detener |
| --- | --- | --- |
| macOS | doble clic en `correr/mac/iniciar.command` | `correr/mac/detener.command` |
| Windows | doble clic en `correr/windows/iniciar.bat` | `correr/windows/detener.bat` |

O desde la terminal, en la raíz del proyecto (primero `cp .env.example .env`; los scripts de doble clic lo hacen solos):

```bash
cp .env.example .env                                # solo la primera vez
docker compose up -d --build --renew-anon-volumes   # iniciar
docker compose down                                 # detener
docker compose down -v                              # detener y BORRAR la base de datos
```

| Servicio | URL |
| --- | --- |
| Aplicación web | http://localhost:5173 |
| Backend (docs interactivas) | http://localhost:8000/docs |
| Mock Insurance API | http://localhost:8001/api/v1/planes |
| PostgreSQL | `localhost:5433` · usuario `medimatch` · contraseña definida en tu `.env` |

La primera vez, el backend llena PostgreSQL automáticamente desde la API mock (12 planes simulados).

## Pruebas

```bash
docker compose exec backend python -m pytest tests -v
```

37 pruebas: CSP (incluida la comparación contra fuerza bruta), función objetivo, escenarios A–E sobre
el catálogo real e integración con FastAPI + PostgreSQL (sincronización, privacidad y escenario D).

## Arquitectura

```
frontend/              React + TypeScript + Vite + Tailwind (Liquid Glass)
  src/services/api.ts  única capa que habla con el backend
backend/
  algorithms/          ← IA: modelos.py · csp.py · ranking.py · bayes.py (Python puro, sin BD)
  services/            repositorio.py (BD → dataclasses) · sync.py · recomendador.py
  routes/              endpoints FastAPI
mock_insurance_api/    servicio FastAPI que simula un proveedor externo (catálogo JSON)
database/schema.sql    esquema PostgreSQL
tests/                 pytest
docs/                  guía de algoritmos
correr/                scripts de inicio con doble clic
```

### Endpoints principales

| Método | Ruta | Descripción |
| --- | --- | --- |
| POST | `/api/recomendaciones` | Ejecuta el CSP y el ranking y devuelve resultados explicados |
| POST | `/api/sync` | Sincroniza el catálogo desde la API mock (`{"incluir_novedades": true}` = escenario D) |
| GET | `/api/planes` · `/api/opciones` · `/api/estado` | Catálogo, opciones del formulario y estado |

## Regenerar el catálogo simulado

```bash
python3 mock_insurance_api/generar_catalogo.py
```
