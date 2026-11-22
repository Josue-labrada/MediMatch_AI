# MediMatch IA — Contexto y especificación del proyecto

> **Estado:** propuesta de arquitectura y alcance. Ninguna funcionalidad debe considerarse implementada hasta que exista código, pruebas y evidencia de ejecución.

## 1. Contexto académico

- **Materia:** Fundamentos de Inteligencia Artificial, ITESO, otoño 2026.
- **Trabajo:** Proyecto 4 — Final, aplicaciones de IA.
- **Modalidad:** equipo de 3 integrantes.
- **Entrega:** lunes 23 de noviembre de 2026, 07:00 h.
- **Presentación:** lunes 23 de noviembre de 2026, hasta 10 minutos.
- **Lenguaje obligatorio:** Python 3.9 o superior.
- **Finalidad:** solución funcional que aplique al menos un enfoque de IA visto durante el curso.
- **Nota:** el documento de la actividad admite búsquedas, teoría de juegos, razonamiento probabilístico, aprendizaje automático u otros enfoques del curso; no exige implementarlos todos.

## 2. Idea del producto

**MediMatch IA** es un prototipo educativo de plataforma web de comparación y recomendación explicable de seguros de gastos médicos mayores. El usuario introduce restricciones y preferencias, y el sistema identifica configuraciones compatibles, ordena alternativas y explica los resultados.

**Límite del producto:** no cotiza ni emite seguros reales, no procesa pagos, no afirma elegibilidad de contratación y no sustituye asesoría profesional. Los planes, precios y aseguradoras de la demo deben estar marcados como simulados; no atribuir datos inventados a entidades reales.

## 3. Qué temas del curso se aplican

| Módulo | Relación con el proyecto | Estado |
| --- | --- | --- |
| 01 Introducción a la IA | Formulación de un problema de decisión y función objetivo | Conceptual |
| 02 Agentes inteligentes | Entradas/percepciones, criterio de decisión y salida/acción | Conceptual; evitar declarar que existe un agente autónomo si no se implementa |
| 03 Búsqueda | Enumeración y evaluación de alternativas para hallar la mejor válida | Obligatorio en nuestro diseño |
| 04 CSP | Variables, dominios, restricciones, backtracking y, de ser viable, forward checking | Obligatorio en nuestro diseño |
| 05 Búsqueda adversarial | No se necesita; no inventar un adversario | Fuera de alcance |
| 06 Razonamiento probabilístico | Simulación de escenarios usando probabilidades y supuestos explícitos | Opcional, solo después del MVP |

### Distinción conceptual obligatoria

Un `filter()` sobre planes precargados no demuestra por sí solo un solucionador CSP con backtracking. Para hablar de **CSP implementado**, modelar variables (plan, variante de deducible, selección de coberturas), dominios, restricciones y una búsqueda de asignaciones consistentes, idealmente con podas/forward checking. Si el alcance se reduce a filtros simples, describirlo honestamente como **filtrado por restricciones** y justificar el algoritmo de búsqueda real por separado.

La **optimización** puede usar búsqueda exhaustiva porque el espacio de alternativas es pequeño. Una puntuación ponderada es una función objetivo diseñada por el equipo, no un modelo entrenado ni una probabilidad empírica. No usar A* o Minimax si no corresponde al problema.

## 4. Funcionalidades mínimas (MVP)

1. Pantalla de inicio, formulario de preferencias y vista de recomendaciones.
2. Catálogo de aseguradoras y planes simulados en PostgreSQL.
3. API mock HTTP separada que entrega JSON con planes/configuraciones de prueba.
4. Sincronización manual desde la API mock hacia PostgreSQL, evitando duplicados.
5. Motor CSP en Python que obtiene combinaciones factibles bajo restricciones duras.
6. Motor de búsqueda/optimización en Python que ordena alternativas válidas según criterios ponderados configurables.
7. Resultados explicables: restricciones satisfechas, razones de descarte, contribuciones a puntuación y alternativas.
8. Pruebas automatizadas de algoritmos y endpoints importantes.
9. README que permita ejecutar toda la aplicación localmente y repetir casos de demostración.

### Fuera de alcance inicialmente

- Contratación y emisión de pólizas reales, pasarelas de pago o enlaces de compra ficticios.
- Scraping productivo, integración con aseguradoras reales, precios en tiempo real.
- Entrenamiento de modelos de ML que no aporten a la demostración.
- Registro de historiales clínicos, diagnósticos o datos personales sensibles.
- Implementación adversarial o probabilística solo para sumar algoritmos.

## 5. Arquitectura propuesta

```text
React + Vite + Tailwind (localhost:5173)
          |
          v
FastAPI principal (localhost:8000)
     |          |             |
 PostgreSQL   Motor IA     Cliente HTTP
  (local)    CSP + search      |
                              v
                     Mock Insurance API
                      (localhost:8001)
```

**Importante:** la API mock es una simulación explícita. El backend sincroniza su catálogo hacia PostgreSQL. Las recomendaciones deben usar datos de PostgreSQL, no arrays de respuestas fijas en el frontend.

### Tecnologías propuestas

- Frontend: React, Vite, Tailwind CSS.
- Backend: Python 3.9+, FastAPI, Pydantic, SQLAlchemy, psycopg, httpx.
- Persistencia: PostgreSQL local.
- API de pruebas externa simulada: otro servicio FastAPI con catálogo JSON.
- Pruebas: pytest (y cliente de pruebas HTTP).
- Configuración: `.env.example`, sin contraseñas reales en el repositorio.

## 6. Esquema relacional inicial

- `aseguradoras`: `id`, `nombre`, `es_simulada`.
- `planes`: `id`, `aseguradora_id`, `external_id`, `nombre`, `prima_mensual`, `moneda`, `activo`, `updated_at`.
- `variantes_deducible`: `id`, `plan_id`, `deducible`, `coaseguro_porcentaje`, `prima_ajustada`.
- `coberturas`: `id`, `codigo`, `nombre`, `descripcion`.
- `plan_coberturas`: `plan_id`, `cobertura_id`, `disponible`, `costo_extra`.
- `consultas`: `id`, `preferencias_json`, `created_at` (sin datos sensibles).
- `recomendaciones`: `id`, `consulta_id`, `plan_id`, `variante_id`, `score`, `explicacion_json`.
- `sincronizaciones`: `id`, `fecha`, `origen`, `registros_creados`, `registros_actualizados`, `resultado`.

Agregar claves foráneas, índices y restricciones de unicidad, especialmente en `(aseguradora_id, external_id)`; revisar y ajustar el esquema en la etapa de implementación.

## 7. Diseño de algoritmos

### CSP (principal)

**Variables de ejemplo:** plan, variante de deducible, coberturas opcionales seleccionadas.

**Dominios:** productos y opciones disponibles en la base de datos.

**Restricciones duras:** prima total menor o igual al presupuesto, deducible menor o igual al máximo, coberturas obligatorias incluidas, combinaciones válidas de opciones, disponibilidad de variante.

**Implementación:** backtracking, comprobación de consistencia parcial y, si es posible, forward checking; registrar estados explorados, podas y combinaciones factibles.

### Búsqueda y optimización (principal)

Evaluar cada combinación factible con una función objetivo explícita de componentes normalizados, por ejemplo costo, deducible y coberturas preferidas. Los pesos de preferencia deben sumar 1 y ser ajustables; definir cómo se manejan componentes desconocidos. Elegir la máxima puntuación, con desempate determinista. No utilizar criterios ocultos.

**Comparación experimental:** contrastar resultado de menor prima contra resultado multi-criterio y mostrar cuándo cambian las recomendaciones.

### Probabilístico (solo extra)

Simular gastos posibles con parámetros ficticios declarados y calcular costo esperado del usuario para diferentes configuraciones. No presentar las probabilidades como predicción individual ni como datos actuariales reales.

## 8. Endpoints propuestos

**API mock (`:8001`):**
- `GET /api/v1/planes`: catálogo JSON simulado.
- `GET /health`: comprobación del servicio.

**Backend (`:8000`):**
- `POST /api/sync`: importar/actualizar catálogo desde mock.
- `GET /api/planes`: consultar catálogo persistido.
- `POST /api/recomendaciones`: validar perfil, ejecutar CSP y ranking y devolver razones.
- `GET /health`: estado básico.

La respuesta de recomendación debe incluir `candidatos_evaluados`, `candidatos_validos`, `descartes`, `ranking`, `puntajes_desglosados` y `algoritmo_utilizado`, según corresponda.

## 9. Evidencias y escenarios de prueba

- A: presupuesto reducido, pocos planes compatibles.
- B: múltiples planes compatibles, cambian pesos y cambia ranking.
- C: restricciones incompatibles, 0 resultados con explicación.
- D: sincronizar un nuevo producto mock y comprobar que afecta los resultados sin editar el algoritmo.
- E: probar combinaciones inválidas de coberturas/deducibles y comprobar podas del CSP.
- F: pruebas unitarias de puntuación, límites y desempates.

Guardar capturas de pantallas, respuestas JSON, resultados de pytest y observaciones cuantitativas. No inventar resultados de pruebas antes de ejecutarlas.

## 10. Rúbrica y entregables oficiales

Se requiere reporte con estos **ocho** apartados:

1. Selección y evaluación de proyecto.
2. Claridad en la definición y modelado del problema.
3. Elección y justificación del enfoque de IA utilizado.
4. Diseño lógico y desarrollo básico funcional de la solución.
5. Análisis de resultados obtenidos.
6. Consideración ética y/o social.
7. Siguientes pasos del proyecto para su continuación.
8. Conclusiones.

**Ponderación:** documento de ocho puntos (40%), códigos legibles y fuentes (40%), orden/comentarios/conclusiones (10%) y One Page View (10%).

**Entrega:** un archivo ZIP por equipo en Canvas, reporte Word y PDF con carátula, archivos `.py`, dependencias/instrucciones para ejecución y Anexo 1 (One Page View; formato facilitado en PPT). Exposición de máximo 10 minutos. Equipo de 3 integrantes.

## 11. Reglas de desarrollo para colaboradores y asistentes de IA

1. **No declarar funciones implementadas sin código y pruebas.**
2. Mantener la lógica CSP/optimización en archivos Python independientes y legibles.
3. No devolver recomendaciones inventadas desde el frontend, ni `if` fijos por presupuesto que seleccionen un plan específico.
4. Todo dato ficticio debe identificarse como tal en API, interfaz y reporte.
5. No afirmar cotizaciones oficiales ni venta real de pólizas.
6. Priorizar el MVP funcional sobre nuevas funciones no pedidas.
7. Implementar por etapas, explicando archivos, comandos y cómo comprobar cada avance.
8. Añadir comentarios técnicos que expliquen reglas y decisiones; no comentarios redundantes.
9. Evitar dependencias innecesarias, guardar secretos en variables de entorno y trabajar con PostgreSQL local.
10. Preparar pruebas y resultados reproducibles para la exposición y la documentación.

## 12. Fases sugeridas

1. Modelo de datos, PostgreSQL, migración/esquema y datos de prueba.
2. API mock, endpoints y sincronización.
3. CSP con backtracking y pruebas.
4. Optimización, explicación del ranking y pruebas.
5. React y conexión con FastAPI.
6. Pruebas integradas, evidencia, reporte de ocho puntos, One Page View y presentación.

**Criterio de éxito:** la misma consulta debe poder producir un resultado diferente cuando cambie el catálogo o las preferencias, por efecto del algoritmo y no porque se modifique código de respuesta fija.
