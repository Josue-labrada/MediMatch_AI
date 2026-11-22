# Guía de los algoritmos de MediMatch IA

Documento de estudio para explicar y defender la parte de IA ante el profesor.
Archivos clave: `backend/algorithms/csp.py`, `backend/algorithms/ranking.py`,
`backend/algorithms/modelos.py` y `backend/services/recomendador.py`.

---

## 1. La idea en una frase

> El usuario da **restricciones duras** (presupuesto, deducible, coberturas indispensables) y
> **preferencias** (pesos). Un **CSP con backtracking y forward checking** encuentra *todas* las
> configuraciones que cumplen las restricciones, y una **función objetivo ponderada** las ordena
> para elegir la mejor, explicando por qué.

Son dos técnicas del curso que se complementan:

| Pregunta | Técnica | Módulo |
| --- | --- | --- |
| ¿Qué opciones son **válidas**? | CSP: backtracking + forward checking | 04 |
| ¿Cuál válida es la **mejor**? | Búsqueda exhaustiva sobre el conjunto factible con función objetivo | 03 |

---

## 2. Cómo se conectan las piezas

```text
[Formulario React]  ──POST /api/recomendaciones──►  [FastAPI: routes/recomendaciones.py]
                                                         │ Pydantic valida (rechaza "edad", etc.)
                                                         ▼
                                              [services/recomendador.py]
                                                         │
             ┌───────────────────────────────────────────┼─────────────────────────────┐
             ▼                                           ▼                             ▼
 [services/repositorio.py]                    [algorithms/csp.py]            [algorithms/ranking.py]
 PostgreSQL → dataclasses Plan     →    resolver(): soluciones,      →     rankear(): puntaje y orden
                                        descartes, estadísticas            menor_prima(): línea base
                                                         │
                                                         ▼
                                     Respuesta JSON explicada + fila en tabla `consultas`

[Mock Insurance API :8001] ──HTTP──► [services/sync.py] ──upsert──► PostgreSQL   (POST /api/sync)
```

Puntos para remarcar:

- **Los algoritmos no conocen la base de datos.** Reciben dataclasses (`modelos.py`). Por eso se
  prueban con pytest usando datos escritos a mano y se pueden explicar sin infraestructura.
- **Nada está hardcodeado.** Si cambia el catálogo (sincronizar «Faro Materna») o cambian los pesos,
  cambia el resultado sin tocar código: escenario D.
- **El frontend no decide nada.** Solo muestra lo que calcula el backend.

---

## 3. El CSP

### 3.1 Modelado (lo que más preguntan)

**Variables**

| Variable | Significado | Dominio |
| --- | --- | --- |
| `P` | plan | planes activos en PostgreSQL |
| `D` | variante de deducible | variantes **del plan asignado a P** |
| `C_k` | ¿incluir la cobertura k? | `{1}` si viene incluida · `{1,0}` si es opcional · `{0}` si el plan no la ofrece |

Las variables `C_k` son solo las coberturas que importan: **obligatorias + deseadas** del usuario, y
las que éstas **arrastran** por reglas «requiere» (cierre transitivo). Así el espacio queda pequeño.

**Restricciones**

| Nombre en código | Tipo | Condición |
| --- | --- | --- |
| `suma_asegurada` | unaria (P) | suma(P) ≥ mínimo |
| `deducible_maximo` | unaria (D) | deducible(D) ≤ máximo |
| `coaseguro_maximo` | unaria (D) | coaseguro(D) ≤ máximo |
| `cobertura_obligatoria` | unaria (C_k) | C_k = 1 |
| `presupuesto` | global | prima(D) + Σ costo(C_k = 1) ≤ presupuesto |
| `regla_requiere` | binaria (C_a, C_b) | C_a = 1 ⇒ C_b = 1 |
| `regla_excluye` | binaria (C_a, C_b) | no (C_a = 1 y C_b = 1) |
| `regla_deducible_max` | binaria (D, C_a) | C_a = 1 ⇒ deducible(D) ≤ valor |
| `solo_si_requerida` | C_b arrastrada | C_b = 1 solo si alguna C_a = 1 la requiere |

Las reglas viven en la tabla `reglas_compatibilidad`. Ejemplos reales del catálogo:
- Delta Balance: maternidad **requiere** check-up.
- Boreal Familiar: dental **excluye** visión.
- Delta Viajero: cobertura internacional **requiere** ambulancia aérea y **solo con deducible ≤ $30,000**.

### 3.2 ¿Por qué es un CSP y no un `filter()`?

Un filtro revisa cada plan de forma aislada con condiciones fijas. Aquí:
1. Hay **variables relacionadas entre sí**: el dominio de `D` depende de `P`, y una cobertura
   depende del deducible (`regla_deducible_max`) o de otra cobertura (`requiere`/`excluye`).
2. El presupuesto es una restricción **global** sobre la suma de varias variables.
3. Se construyen **asignaciones parciales** y se podan antes de completarlas.
4. La salida no es «plan sí o no». Son **configuraciones** (plan + deducible + coberturas), y una
   regla puede **agregar** una cobertura con su costo, como ambulancia aérea.

### 3.3 Backtracking (`_backtrack`)

```text
BACKTRACK(i, asignación, dominios):
    si i == número de variables:  guardar solución; regresar
    X ← orden[i]                       # orden fijo: D, C_1, …, C_n (P ya asignado)
    para cada valor v en dominios[X]:
        nodos_explorados += 1
        asignación[X] ← v
        si CONSISTENTE(X, asignación):           # solo restricciones ya evaluables
            (con FC) nuevos ← FORWARD_CHECK(...)
            si nada quedó vacío: BACKTRACK(i+1, asignación, nuevos)
            si no: registrar poda
        si no: registrar poda
        quitar X                                  # ← esto es el "backtrack"
    si ningún valor llevó a solución: backtracks += 1
```

`CONSISTENTE` (`_consistente`) revisa solo las restricciones que involucran a `X` y cuyas otras
variables **ya tienen valor**. Si una variable aún no está asignada, la restricción no se puede
evaluar y no se considera violada.

**Enumeramos todas las soluciones, no solo la primera,** porque el ranking necesita compararlas.

### 3.4 Forward checking (`_forward_checking` y `_dominios_iniciales`)

Después de cada asignación revisa los dominios de las variables **pendientes** y elimina los
valores que ya son incompatibles con lo asignado. Si un dominio queda **vacío**, la rama se poda
**antes** de bajar por ella.

Podas concretas que hace:
1. **Al fijar P:** quita las variantes con deducible o coaseguro por encima del máximo, y quita el 0
   de las coberturas obligatorias. Si una obligatoria no se ofrece, su dominio `{0}` queda vacío y
   el plan completo se descarta sin explorar nada.
2. **Al fijar D:** quita el valor 1 de las coberturas con `deducible_max` < deducible(D), y quita el 1
   de las opcionales que ya no caben en el presupuesto.
3. **Al fijar C_a = 1:** quita el 0 de las coberturas que `C_a` requiere y quita el 1 de las que excluye.
4. **Cota de presupuesto:** si lo asignado + el costo de lo que es forzosamente 1 ya supera el
   presupuesto, poda.

**Ejemplo para la exposición:** escenario E, Delta Viajero, con internacional obligatoria.
Con `D = $50,000`, FC revisa `C_internacional`. La regla exige deducible ≤ $30,000, así que se
quita el 1, y el 0 ya se había quitado por ser obligatoria. El dominio queda vacío y la rama se poda.
El backtracking simple habría probado las combinaciones de coberturas una por una.

### 3.5 Resultados medidos (catálogo real, `tests/test_escenarios.py`)

Ambos algoritmos encuentran **exactamente las mismas soluciones**; esto lo verifican las pruebas.
FC explora menos nodos:

| Escenario | Backtracking (nodos) | Backtracking + FC (nodos) | Soluciones |
| --- | --- | --- | --- |
| A · presupuesto $1,300 | 51 | 51 | 6 |
| B · $5,000, 3 deseadas | 225 | 191 | 66 |
| C · incompatible | 47 | 22 | 0 |
| D · maternidad $2,700 | 57 | 30 | 1 |
| E · internacional obligatoria | 101 | 46 | 11 |

En A no hay diferencia porque no hay variables de cobertura que podar: FC no es magia y su ventaja
crece con el número de restricciones entre variables. La pantalla de resultados y la de algoritmos
muestran esta comparación para cada búsqueda.

---

## 4. La optimización (`ranking.py`)

### 4.1 Función objetivo

```
puntaje(x) = Σ_i  w_i · n_i(x)        con Σ w_i = 1  y  0 ≤ n_i ≤ 1   →  se muestra × 100
```

| Criterio | Valor original | Normalización (min-max dentro del conjunto factible F) |
| --- | --- | --- |
| costo | prima total | menor es mejor: (max − x) / (max − min) |
| deducible | deducible | menor es mejor |
| coaseguro | % | menor es mejor |
| suma_asegurada | MXN | mayor es mejor: (x − min) / (max − min) |
| coberturas | fracción de deseadas incluidas | ya está entre 0 y 1 |

### 4.2 Decisiones documentadas (preguntas típicas)

- **¿Por qué normalizar?** Para comparar pesos y pesos mexicanos con porcentajes en la misma escala.
- **¿Si todos tienen el mismo deducible?** Si max = min, n = 1 para todos. Ese criterio no afecta el orden.
- **¿Sin coberturas deseadas?** Ese criterio no aplica y su peso se reparte de forma proporcional.
- **¿Pesos en 0?** Se usan pesos iguales.
- **¿Empates?** Orden determinista: puntaje ↓, prima ↑, deducible ↑, `external_id` ↑.
- **¿Por qué búsqueda exhaustiva?** F tiene decenas o cientos de elementos, así que evaluarlo
  completo es instantáneo y **garantiza el óptimo global**. A* o búsqueda local no aportan aquí.
- **¿Por qué la normalización es relativa?** Porque un puntaje depende de las demás opciones.
  Agregar un plan puede cambiar los puntajes; por ejemplo, en el escenario D Delta Balance pasa de
  100 a 0 puntos cuando aparece Faro Materna, que es mejor en todo. Es una limitación que se
  menciona en el reporte.
- **¿Es machine learning?** **No.** No hay entrenamiento ni datos históricos. Es una función objetivo
  diseñada por el equipo, con pesos que define el usuario.

### 4.3 Línea base: menor prima

`menor_prima()` elige la opción válida más barata (un solo criterio). La interfaz compara esa opción
contra la mejor multicriterio. Ejemplo medido (escenario B, $5,000, deseadas maternidad, dental y
salud mental):

- Pesos «ahorro» (costo 60%): gana **Cumbre Práctico, $1,620**.
- Pesos «protección» (coberturas 50%): gana **Cumbre Integral con dental y maternidad, $4,430**.
- La menor prima siempre es **Alfa Esencial, $1,450**.

Esto demuestra que **cambiar las preferencias cambia la recomendación** por efecto del algoritmo.

---

## 5. Escenarios de demostración

Para cada escenario: llena el formulario en http://localhost:5173/buscar, o envía el JSON a
`POST http://localhost:8000/api/recomendaciones` (puedes probarlo en http://localhost:8000/docs).

| | Presupuesto | Deducible máx. | Obligatorias | Deseadas | Qué demuestra |
| --- | --- | --- | --- | --- | --- |
| A | 1,300 | 80,000 | hospitalización | — | Pocos planes compatibles |
| B | 5,000 | 30,000 | hospitalización | maternidad, dental, salud mental | Cambiar los pesos (Ahorro ↔ Protección) cambia el ganador |
| C | 2,000 | 30,000 | internacional, maternidad | — | 0 resultados, con el motivo de cada descarte |
| D | 2,700 | 30,000 | maternidad | — | Sincroniza en Admin con «Incluir productos nuevos» y repite: gana Faro Materna |
| E | 6,000 | 50,000 | internacional | dental | Reglas «requiere» y «deducible máx.» y menos nodos con FC |

---

## 6. Cómo verificar y guardar evidencia

```bash
# Todas las pruebas (37): algoritmos, escenarios A–E e integración con PostgreSQL
docker compose exec backend python -m pytest tests -v

# Solo los algoritmos, sin Docker (Python 3.9+ y pytest)
python3 -m pytest tests/test_csp.py tests/test_ranking.py tests/test_escenarios.py -v
```

Pruebas que conviene mencionar:
- `test_completitud_contra_fuerza_bruta`: el CSP encuentra **exactamente** las mismas soluciones que
  enumerar todo el espacio. Es correcto y completo.
- `test_todas_las_soluciones_cumplen_todas_las_restricciones`: verificación independiente de cada
  solución contra las restricciones originales.
- `test_forward_checking_mismas_soluciones_menos_nodos`.
- `test_privacidad_rechaza_campos_no_previstos`: enviar «edad» o «padecimientos» devuelve 422.

---

## 7. Preguntas probables del profesor y respuesta corta

1. **¿Dónde está la IA?** En la formulación como CSP y su resolución con búsqueda con retroceso
   y propagación (forward checking), más la optimización sobre el espacio factible.
2. **¿Por qué no un modelo de ML?** No hay datos reales de usuarios ni etiquetas. Inventarlos sería
   deshonesto. El problema es de decisión con restricciones explícitas, y eso es justo lo que resuelve un CSP.
3. **¿Garantizan el óptimo?** Sí, respecto a la función objetivo: el CSP es completo (lo prueba la
   comparación contra fuerza bruta) y la evaluación de F es exhaustiva.
4. **¿Qué heurísticas de orden usan?** Orden fijo de variables (D antes que coberturas, obligatorias
   primero) y valor 1 antes que 0. MRV o LCV serían un siguiente paso; con este tamaño de problema
   no cambian el resultado, solo el número de nodos.
5. **¿Por qué FC y no AC-3?** FC basta para dominios de tamaño 1 o 2. AC-3 propagaría también entre
   variables pendientes; es una mejora futura.
6. **¿Complejidad?** El peor caso es exponencial en el número de coberturas variables (2ⁿ por
   variante), pero n ≤ 10 y las podas lo reducen mucho (ver tabla 3.5).
7. **¿Datos reales?** No. Aseguradoras, planes y precios son simulados y están etiquetados así en la
   API, la BD (`es_simulada CHECK TRUE`), la interfaz y el reporte.

---

## 8. Cuestionario de riesgo con la regla de Bayes (`backend/algorithms/bayes.py`)

**Qué hace.** La pantalla *Cuestionario* estima el nivel de riesgo de salud de la persona
(`bajo`, `medio`, `alto`) y, con ese resultado, reutiliza el CSP y el ranking para recomendar un seguro.

```
respuestas ─► bayes.analizar ─► posterior P(nivel | respuestas)
                              ─► bayes.derivar_criterios ─► PreferenciasIn ─► CSP + ranking (sección 3 y 4)
```

**Bayes.**  `P(H | E) = P(E | H) · P(H) / P(E)`

| Elemento | En el proyecto |
| --- | --- |
| Hipótesis H | nivel de riesgo: bajo / medio / alto |
| Prior P(H) | según el rango de edad (la persona de 60+ parte con más probabilidad de riesgo alto) |
| Evidencia E | cada respuesta: fuma, actividad, peso, crónicas, hospitalizaciones, antecedentes |
| Verosimilitud P(E \| H) | tabla en `bayes.py`: p. ej. P(fuma «sí» \| alto) = 0.35 y P(fuma «sí» \| bajo) = 0.05 |
| P(E) | probabilidad total: Σ P(E \| H) · P(H) (`ReglaDeBayes.probabilidad_evidencia`) |
| Posterior | `ReglaDeBayes.posteriores`; `actualizar` lo convierte en el prior de la siguiente respuesta |

- **Clases del profesor:** `ReglaDeBayes` (varias hipótesis) y `PruebaDiagnostica` (dos hipótesis).
  El cuestionario usa `ReglaDeBayes` con tres hipótesis; `PruebaDiagnostica` queda incluida y probada
  con sus ejemplos (bacteria 4.72 %, cáncer 9/108).
- **Probabilidad total aplicada:** `P(hospitalización) = Σ P(hosp | nivel) · P(nivel | respuestas)`,
  y las *frecuencias naturales* («de cada 1000 personas como tú…») igual que `frecuencias_naturales`.
- **Supuesto de Bayes ingenuo:** dado el nivel, las respuestas son independientes. Es una simplificación.
- **Del riesgo al seguro:** índice `r = P(medio)·0.5 + P(alto)`. Mayor `r` ⇒ deducible máximo más bajo,
  coaseguro acotado, suma asegurada mínima más alta y pesos que migran de «ahorrar» a «protegerse».
  Si nada cabe en el presupuesto, se relajan por pasos las exigencias no obligatorias y se informa.
- **Honestidad:** todas las probabilidades son **inventadas e ilustrativas** (igual que el catálogo).
  No hay datos reales con los que calibrarlas; no es un diagnóstico.
- **Privacidad:** son datos de salud sensibles, así que el endpoint `/api/cuestionario` los usa solo
  durante la petición y **no los guarda**; rechaza campos no previstos (422). `/api/recomendaciones`
  sigue rechazando datos personales.

Pruebas: `tests/test_bayes.py` (suma 1, ejemplos del profesor, encadenamiento de posteriores,
monotonía del riesgo) y dos pruebas de API en `tests/test_api.py`.

### 8.1 Ejemplo completo, paso a paso (valores reales del código)

Persona de 45 a 59 años: fuma con frecuencia, actividad baja, sobrepeso, una enfermedad crónica,
sin hospitalizaciones, sin antecedentes familiares. Prior (por edad): bajo 0.35 · medio 0.40 · alto 0.25.

| Paso | Respuesta | P(E) | Bajo | Medio | Alto |
| --- | --- | --- | --- | --- | --- |
| prior | edad 45-59 | , | 0.350 | 0.400 | 0.250 |
| 1 | fuma: sí, con frecuencia | 0.1650 | 0.106 | 0.364 | 0.530 |
| 2 | actividad: baja | 0.4167 | 0.038 | 0.262 | 0.700 |
| 3 | peso: sobrepeso | 0.3443 | 0.022 | 0.266 | 0.712 |
| 4 | crónicas: una | 0.3798 | 0.005 | 0.245 | 0.749 |
| 5 | hospitalizaciones: ninguna | 0.4265 | 0.011 | 0.374 | 0.615 |
| 6 | antecedentes: no | 0.5292 | 0.018 | 0.459 | 0.523 |

**Cómo se calcula el paso 1** (el que conviene saber hacer en el pizarrón):

```text
numerador   = P(E|H) · P(H)         bajo: 0.05·0.35 = 0.0175   medio: 0.15·0.40 = 0.0600   alto: 0.35·0.25 = 0.0875
P(E)        = suma de los tres     = 0.1650            (probabilidad total)
posterior   = numerador / P(E)      bajo 0.106 · medio 0.364 · alto 0.530
```

**Qué se aprende del ejemplo**

- Las respuestas que **más mueven** la creencia son las que más separan los niveles (fumar y actividad baja
  la llevan de 0.25 a 0.70 en riesgo alto). Una respuesta que se parece en los tres niveles casi no cambia nada.
- Una respuesta **tranquilizadora** también cuenta: «sin hospitalizaciones» y «sin antecedentes» **bajan** el
  riesgo alto (0.749 → 0.615 → 0.523). El resultado final es `alto` por poco margen (0.523 vs 0.459): es
  una *probabilidad*, no una certeza.
- Resultado: índice `r = 0.459·0.5 + 0.523 = 0.753`, así que se aplica la rama «riesgo alto» de `derivar_criterios`.
- **Probabilidad total aplicada:** `P(hosp) = 0.03·0.018 + 0.10·0.459 + 0.28·0.523 = 0.193`. En frecuencias
  naturales: de cada 1000 personas como ésta, unas **193** tendrían una hospitalización mayor en 12 meses.
- Contraste: con fuma «no», actividad alta, peso normal y sin crónicas, el posterior queda en
  bajo 0.902 · medio 0.097 · alto 0.001 (índice 0.05) y se recomienda un plan más barato con deducible alto.

### 8.2 Del riesgo a la recomendación (`derivar_criterios`)

| Índice de riesgo r | Deducible máximo | Coaseguro | Suma asegurada mínima |
| --- | --- | --- | --- |
| r < 0.25 (bajo) | el más alto del catálogo | sin tope | sin mínimo |
| 0.25 ≤ r < 0.55 (medio) | intermedio | sin tope | moderada (percentil 20) |
| r ≥ 0.55 (alto) | bajo (percentil 20) | acotado | amplia (percentil 45) |

- **Pesos:** se interpolan linealmente entre dos perfiles. Con r = 0 pesa sobre todo el costo (70 %); con r = 1
  pesan más la suma asegurada, el deducible, el coaseguro y las coberturas (costo baja a 10 %).
- **Coberturas deseadas:** maternidad y viajes (preguntas de *necesidad*, que **no** entran a Bayes),
  más telemedicina y checkup si hay crónicas o r ≥ 0.55. Solo se piden las que existen en el catálogo.
- **Relajación:** si el CSP no encuentra nada dentro del presupuesto, se relajan por pasos las exigencias no
  obligatorias y se avisa al usuario (no se devuelve una lista vacía sin explicación).
- Los umbrales 0.25 y 0.55 y los perfiles de pesos son **decisiones de diseño** del equipo, no resultados estadísticos.

### 8.3 Por qué Bayes y no otra técnica

- **Es explicable:** cada paso muestra su prior, su verosimilitud y su posterior; la interfaz lo despliega.
- **No necesita datos históricos ni entrenamiento**, a diferencia de un clasificador de machine learning.
  Con la edad como prior y tablas de verosimilitud basta para ilustrar el razonamiento bajo incertidumbre.
- **Complementa al CSP:** Bayes maneja lo *incierto* (¿qué tan riesgoso soy?) y el CSP lo *exacto*
  (¿qué configuraciones cumplen las restricciones?). Bayes decide los parámetros y el CSP/ranking los aplica.

### 8.4 Preguntas probables y cómo responder

1. **¿Qué es el prior y de dónde sale?** Es la creencia antes de ver evidencia: P(nivel) según el rango de edad.
   Los números son ilustrativos; en un sistema real vendrían de datos actuariales.
2. **¿Qué es la verosimilitud?** `P(respuesta | nivel)`: qué tan común es la respuesta entre quienes tienen ese
   nivel. Para cada nivel, las de todas las opciones de una pregunta suman 1 (lo verifica `validar_modelo`).
3. **¿Por qué se divide entre P(E)?** Para normalizar: los numerandos no suman 1; al dividir entre su suma
   (probabilidad total) el resultado sí es una distribución.
4. **¿Qué supuesto hace el modelo?** Independencia condicional (Bayes ingenuo): dado el nivel, fumar y el
   peso no se influyen. Es falso en la realidad (están correlacionados) y **tiende a sobreestimar la
   confianza**; se acepta por simplicidad y se declara.
5. **¿Importa el orden de las preguntas?** No en el resultado final: multiplicar verosimilitudes es
   conmutativo. Solo cambian los posteriores intermedios que se muestran.
6. **¿Es un diagnóstico médico?** No. Probabilidades inventadas, sin validación clínica ni actuarial.
7. **¿Qué pasa con los datos de salud?** Se usan solo durante la petición y no se guardan.
8. **¿Qué mejorarías?** Calibrar con datos reales, modelar dependencias entre variables (red bayesiana),
   y estimar la incertidumbre del propio posterior.

### 8.5 Cómo probarlo en vivo

```bash
# Pruebas del algoritmo (suma 1, ejemplos del profesor, encadenamiento, monotonía)
docker compose exec backend pytest tests/test_bayes.py -v
```

En la web: **Cuestionario** muestra el posterior después de cada respuesta; **Algoritmos → 4 · Regla de Bayes**
trae la fórmula y un ejemplo numérico.
