"""
Solucionador CSP (Constraint Satisfaction Problem) para configuraciones de seguros.

MODELADO
--------
Variables
    P     plan                                   dominio: planes activos del catálogo
    D     variante de deducible                  dominio: variantes del plan asignado a P
    C_k   ¿incluir la cobertura k? ∈ {0, 1}      una por cada cobertura relevante:
          obligatorias + deseadas del usuario + las que éstas arrastran por reglas "requiere"

    Los dominios de D y C_k dependen del valor de P (CSP condicionado), por eso P se
    asigna primero y cada plan abre su propio subproblema.

Dominio de C_k según cómo lo ofrece el plan
    incluida → {1}      opcional → {1, 0}      no la ofrece → {0}

Restricciones
    suma_asegurada        (unaria sobre P)   suma asegurada ≥ mínimo del usuario
    deducible_maximo      (unaria sobre D)   deducible ≤ máximo del usuario
    coaseguro_maximo      (unaria sobre D)   coaseguro ≤ máximo del usuario
    cobertura_obligatoria (unaria sobre C_k) C_k = 1 si el usuario la marcó obligatoria
    presupuesto           (global)           prima(D) + Σ costo_extra(C_k = 1) ≤ presupuesto
    regla_requiere        (binaria C_a, C_b) C_a = 1 ⇒ C_b = 1
    regla_excluye         (binaria C_a, C_b) ¬(C_a = 1 ∧ C_b = 1)
    regla_deducible_max   (binaria D, C_a)   C_a = 1 ⇒ deducible(D) ≤ valor
    solo_si_requerida     (C_b arrastrada)   C_b = 1 solo si alguna C_a = 1 la requiere
                                             (evita soluciones dominadas: pagar algo no pedido)

ALGORITMOS
----------
backtracking
    Asigna variables en orden (P, D, C_1 … C_n). Tras cada asignación verifica las
    restricciones cuyas variables ya tienen valor; si alguna falla, poda esa rama y
    prueba el siguiente valor. Al agotar un dominio, regresa (backtrack).

backtracking + forward checking
    Además, después de cada asignación revisa los dominios de las variables AÚN NO
    asignadas y elimina los valores que ya son incompatibles. Si un dominio queda
    vacío, la rama se poda antes de bajar por ella. Incluye una cota de presupuesto:
    si lo ya asignado + el costo de lo que obligatoriamente falta excede el
    presupuesto, se poda de inmediato.

Ambos encuentran exactamente las mismas soluciones; forward checking explora menos nodos.
Se enumeran TODAS las soluciones porque el ranking (ranking.py) elige entre ellas.
"""
from time import perf_counter
from typing import Dict, List, Mapping, Optional, Sequence, Set, Tuple

from .modelos import (
    INCLUIDA,
    Configuracion,
    Descarte,
    EstadisticasCSP,
    Motivo,
    Plan,
    Preferencias,
    Regla,
    ResultadoCSP,
    Variante,
)

ALGORITMO_BT = "backtracking"
ALGORITMO_FC = "backtracking_fc"

VAR_DEDUCIBLE = "D"
MAX_MOTIVOS_POR_PLAN = 5

# Descripción legible de cada restricción (se muestra en la interfaz y en el reporte).
RESTRICCIONES: Dict[str, str] = {
    "suma_asegurada": "Suma asegurada mínima",
    "deducible_maximo": "Deducible máximo",
    "coaseguro_maximo": "Coaseguro máximo",
    "cobertura_obligatoria": "Cobertura obligatoria",
    "presupuesto": "Presupuesto mensual",
    "regla_requiere": "Regla: cobertura requiere otra",
    "regla_excluye": "Regla: coberturas incompatibles",
    "regla_deducible_max": "Regla: cobertura limitada por deducible",
    "solo_si_requerida": "Cobertura no pedida sin necesidad",
}


def mxn(valor: float) -> str:
    return f"${valor:,.0f}"


def resolver(
    planes: Sequence[Plan],
    preferencias: Preferencias,
    forward_checking: bool = True,
    nombres: Optional[Mapping[str, str]] = None,
) -> ResultadoCSP:
    """
    Resuelve el CSP para todos los planes y devuelve todas las configuraciones
    consistentes, los planes descartados con sus motivos y estadísticas de búsqueda.

    `nombres` traduce códigos de cobertura a nombres legibles para las explicaciones.
    """
    inicio = perf_counter()
    stats = EstadisticasCSP(algoritmo=ALGORITMO_FC if forward_checking else ALGORITMO_BT)
    soluciones: List[Configuracion] = []
    descartes: List[Descarte] = []

    # Variable P: cada plan del dominio abre una rama del árbol de búsqueda.
    for plan in planes:
        sub = _SubproblemaPlan(plan, preferencias, stats, forward_checking, nombres or {})
        stats.espacio_busqueda += sub.tamano_espacio()
        antes = len(soluciones)
        sub.resolver(soluciones)
        if len(soluciones) == antes:
            descartes.append(Descarte(plan=plan, motivos=sub.motivos))

    stats.tiempo_ms = round((perf_counter() - inicio) * 1000, 3)
    return ResultadoCSP(soluciones=soluciones, descartes=descartes, estadisticas=stats)


class _SubproblemaPlan:
    """Variables D y C_k una vez fijado P = plan."""

    def __init__(
        self,
        plan: Plan,
        prefs: Preferencias,
        stats: EstadisticasCSP,
        forward_checking: bool,
        nombres: Mapping[str, str],
    ):
        self.plan = plan
        self.prefs = prefs
        self.stats = stats
        self.fc = forward_checking
        self.nombres = nombres
        self.obligatorias: Set[str] = set(prefs.coberturas_obligatorias)
        self.arrastradas: Set[str] = set()
        self.coberturas: List[str] = self._variables_cobertura()
        self.orden: List[str] = [VAR_DEDUCIBLE] + self.coberturas
        self.motivos: List[Motivo] = []

    # ------------------------------------------------------------------ modelado
    def _variables_cobertura(self) -> List[str]:
        """Obligatorias y deseadas, más el cierre transitivo de las reglas 'requiere'."""
        orden: List[str] = []
        for codigo in list(self.prefs.coberturas_obligatorias) + list(self.prefs.coberturas_deseadas):
            if codigo not in orden:
                orden.append(codigo)
        i = 0
        while i < len(orden):
            for regla in self.plan.reglas:
                if regla.tipo == "requiere" and regla.cobertura == orden[i] and regla.objetivo not in orden:
                    orden.append(regla.objetivo)
                    self.arrastradas.add(regla.objetivo)
            i += 1
        return orden

    def _dominio_cobertura(self, codigo: str) -> List[int]:
        oferta = self.plan.oferta(codigo)
        if oferta is None:
            return [0]
        if oferta.tipo == INCLUIDA:
            return [1]
        return [1, 0]  # opcional: primero se prueba incluirla

    def tamano_espacio(self) -> int:
        """Tamaño del espacio sin podar: |D| × Π |dom(C_k)|."""
        total = len(self.plan.variantes)
        for codigo in self.coberturas:
            total *= len(self._dominio_cobertura(codigo))
        return total

    # ------------------------------------------------------------------ búsqueda
    def resolver(self, soluciones: List[Configuracion]) -> None:
        self.stats.nodos_explorados += 1  # asignación P = plan
        motivo = self._verificar_plan()
        if motivo:
            self._podar(motivo)
            return
        dominios = self._dominios_iniciales()
        if dominios is None:
            return
        self._backtrack(0, {}, dominios, soluciones)

    def _verificar_plan(self) -> Optional[Motivo]:
        minimo = self.prefs.suma_asegurada_minima
        if minimo is not None and self.plan.suma_asegurada < minimo:
            return Motivo(
                "suma_asegurada",
                f"Suma asegurada de {mxn(self.plan.suma_asegurada)}, menor al mínimo de {mxn(minimo)}.",
            )
        return None

    def _dominios_iniciales(self) -> Optional[Dict[str, list]]:
        """
        Dominios de D y C_k condicionados a P. Con forward checking se eliminan aquí
        los valores que violan restricciones unarias (consistencia de nodo); sin él,
        esas violaciones se descubren más tarde, al asignar cada variable.
        """
        dominios: Dict[str, list] = {VAR_DEDUCIBLE: list(self.plan.variantes)}
        for codigo in self.coberturas:
            dominios[codigo] = self._dominio_cobertura(codigo)
        if not self.fc:
            return dominios

        for var in self.orden:
            conservados = []
            for valor in dominios[var]:
                motivo = self._viola_unaria(var, valor)
                if motivo:
                    self._podar(motivo)
                else:
                    conservados.append(valor)
            if not conservados:
                return None  # dominio vacío: el plan completo se descarta sin explorar
            dominios[var] = conservados
        return dominios

    def _backtrack(
        self,
        i: int,
        asignacion: Dict[str, object],
        dominios: Dict[str, list],
        soluciones: List[Configuracion],
    ) -> bool:
        if i == len(self.orden):
            soluciones.append(self._configuracion(asignacion))
            return True

        var = self.orden[i]
        encontro = False
        for valor in dominios[var]:
            self.stats.nodos_explorados += 1
            asignacion[var] = valor
            motivo = self._consistente(var, asignacion)
            nuevos = dominios
            if motivo is None and self.fc:
                nuevos, motivo = self._forward_checking(asignacion, dominios)
            if motivo:
                self._podar(motivo)
            elif self._backtrack(i + 1, asignacion, nuevos, soluciones):
                encontro = True
            del asignacion[var]

        if not encontro:
            self.stats.backtracks += 1  # callejón sin salida: se regresa a la variable anterior
        return encontro

    def _forward_checking(
        self, asignacion: Dict[str, object], dominios: Dict[str, list]
    ) -> Tuple[Dict[str, list], Optional[Motivo]]:
        """
        Filtra los dominios de las variables pendientes contra lo ya asignado.
        Devuelve los dominios reducidos o el motivo por el que alguno quedó vacío.
        """
        nuevos = dict(dominios)
        pendientes = [v for v in self.orden if v not in asignacion]
        for var in pendientes:
            conservados = []
            ultimo_motivo: Optional[Motivo] = None
            for valor in dominios[var]:
                asignacion[var] = valor
                motivo = self._consistente(var, asignacion)
                del asignacion[var]
                if motivo:
                    self._podar(motivo)
                    ultimo_motivo = motivo
                else:
                    conservados.append(valor)
            if not conservados:
                return nuevos, ultimo_motivo
            nuevos[var] = conservados

        # Cota de presupuesto: lo asignado + lo que ya es forzosamente 1 en lo pendiente.
        forzoso = sum(self._costo(c) for c in pendientes if c != VAR_DEDUCIBLE and nuevos[c] == [1])
        minimo = self._costo_parcial(asignacion) + forzoso
        if forzoso > 0 and minimo > self.prefs.presupuesto_mensual:
            return nuevos, Motivo(
                "presupuesto",
                f"Con deducible de {mxn(asignacion[VAR_DEDUCIBLE].deducible)}, la prima mínima posible "
                f"({mxn(minimo)}) supera el presupuesto de {mxn(self.prefs.presupuesto_mensual)}.",
            )
        return nuevos, None

    # ------------------------------------------------------------- restricciones
    def _consistente(self, var: str, a: Dict[str, object]) -> Optional[Motivo]:
        """Revisa las restricciones que involucran a `var` y cuyas variables ya tienen valor."""
        motivo = self._viola_unaria(var, a[var])
        if motivo:
            return motivo

        if var in self.arrastradas and a[var] == 1:
            requirentes = [r.cobertura for r in self.plan.reglas if r.tipo == "requiere" and r.objetivo == var]
            valores = [self._valor(c, a) for c in requirentes]
            if None not in valores and 1 not in valores:
                return Motivo(
                    "solo_si_requerida", f"«{self._n(var)}» no se pidió y nada la requiere.", explicativo=False
                )

        for regla in self.plan.reglas:
            if self._involucra(regla, var):
                motivo = self._viola_regla(regla, a)
                if motivo:
                    return motivo

        if VAR_DEDUCIBLE in a:
            costo = self._costo_parcial(a)
            if costo > self.prefs.presupuesto_mensual:
                return Motivo(
                    "presupuesto",
                    f"Con deducible de {mxn(a[VAR_DEDUCIBLE].deducible)}, la prima sería de {mxn(costo)} "
                    f"y supera el presupuesto de {mxn(self.prefs.presupuesto_mensual)}.",
                )
        return None

    def _viola_unaria(self, var: str, valor: object) -> Optional[Motivo]:
        p = self.prefs
        if var == VAR_DEDUCIBLE:
            v: Variante = valor  # type: ignore[assignment]
            if v.deducible > p.deducible_maximo:
                return Motivo(
                    "deducible_maximo",
                    f"Deducible de {mxn(v.deducible)}, mayor al máximo de {mxn(p.deducible_maximo)}.",
                )
            if p.coaseguro_maximo is not None and v.coaseguro_porcentaje > p.coaseguro_maximo:
                return Motivo(
                    "coaseguro_maximo",
                    f"Coaseguro de {v.coaseguro_porcentaje:g}% (deducible {mxn(v.deducible)}), "
                    f"mayor al máximo de {p.coaseguro_maximo:g}%.",
                )
        elif var in self.obligatorias and valor == 0:
            if self.plan.oferta(var) is None:
                detalle = f"No ofrece «{self._n(var)}», que marcaste como obligatoria."
                return Motivo("cobertura_obligatoria", detalle)
            return Motivo(
                "cobertura_obligatoria", f"«{self._n(var)}» es obligatoria y no puede omitirse.", explicativo=False
            )
        return None

    @staticmethod
    def _involucra(regla: Regla, var: str) -> bool:
        if var == VAR_DEDUCIBLE:
            return regla.tipo == "deducible_max"
        return regla.cobertura == var or regla.objetivo == var

    def _viola_regla(self, regla: Regla, a: Dict[str, object]) -> Optional[Motivo]:
        va = self._valor(regla.cobertura, a)
        if regla.tipo == "requiere":
            vb = self._valor(regla.objetivo, a)
            if va == 1 and vb == 0:
                extra = "" if self.plan.oferta(regla.objetivo) else ", que este plan no ofrece"
                return Motivo(
                    "regla_requiere",
                    f"«{self._n(regla.cobertura)}» requiere «{self._n(regla.objetivo)}»{extra}.",
                )
        elif regla.tipo == "excluye":
            vb = self._valor(regla.objetivo, a)
            if va == 1 and vb == 1:
                return Motivo(
                    "regla_excluye",
                    f"«{self._n(regla.cobertura)}» y «{self._n(regla.objetivo)}» no pueden contratarse juntas.",
                )
        elif regla.tipo == "deducible_max":
            variante = a.get(VAR_DEDUCIBLE)
            if va == 1 and variante is not None and variante.deducible > regla.valor:
                return Motivo(
                    "regla_deducible_max",
                    f"«{self._n(regla.cobertura)}» solo está disponible con deducible de hasta {mxn(regla.valor)}.",
                )
        return None

    # ------------------------------------------------------------------ utilidades
    def _valor(self, codigo: str, a: Dict[str, object]) -> Optional[int]:
        """Valor de C_k: asignado, None si es variable pendiente, o el implícito por el plan."""
        if codigo in a:
            return a[codigo]  # type: ignore[return-value]
        if codigo in self.coberturas:
            return None
        oferta = self.plan.oferta(codigo)
        return 1 if oferta is not None and oferta.tipo == INCLUIDA else 0

    def _costo(self, codigo: str) -> float:
        oferta = self.plan.oferta(codigo)
        return oferta.costo_extra if oferta is not None and oferta.tipo != INCLUIDA else 0.0

    def _costo_parcial(self, a: Dict[str, object]) -> float:
        total = a[VAR_DEDUCIBLE].prima_mensual if VAR_DEDUCIBLE in a else 0.0  # type: ignore[union-attr]
        return total + sum(self._costo(c) for c in self.coberturas if a.get(c) == 1)

    def _configuracion(self, a: Dict[str, object]) -> Configuracion:
        opcionales = frozenset(c for c in self.coberturas if a[c] == 1 and self._costo(c) > 0)
        return Configuracion(plan=self.plan, variante=a[VAR_DEDUCIBLE], opcionales=opcionales)  # type: ignore[arg-type]

    def _podar(self, motivo: Motivo) -> None:
        self.stats.registrar_poda(motivo.restriccion)
        if not motivo.explicativo:
            return
        ya = any(m.detalle == motivo.detalle for m in self.motivos)
        if not ya and len(self.motivos) < MAX_MOTIVOS_POR_PLAN:
            self.motivos.append(motivo)

    def _n(self, codigo: Optional[str]) -> str:
        return self.nombres.get(codigo or "", codigo or "")


def explicar_cumplimiento(
    config: Configuracion, prefs: Preferencias, nombres: Optional[Mapping[str, str]] = None
) -> List[str]:
    """Lista legible de las restricciones duras que cumple una solución."""
    nombres = nombres or {}
    v = config.variante
    textos = [
        f"Prima total de {mxn(config.prima_total)} ≤ presupuesto de {mxn(prefs.presupuesto_mensual)}",
        f"Deducible de {mxn(v.deducible)} ≤ máximo de {mxn(prefs.deducible_maximo)}",
    ]
    if prefs.coaseguro_maximo is not None:
        textos.append(f"Coaseguro de {v.coaseguro_porcentaje:g}% ≤ máximo de {prefs.coaseguro_maximo:g}%")
    if prefs.suma_asegurada_minima is not None:
        textos.append(
            f"Suma asegurada de {mxn(config.plan.suma_asegurada)} ≥ mínimo de {mxn(prefs.suma_asegurada_minima)}"
        )
    for codigo in prefs.coberturas_obligatorias:
        textos.append(f"Incluye la cobertura obligatoria «{nombres.get(codigo, codigo)}»")
    tiene = config.coberturas_totales
    for regla in config.plan.reglas:
        if regla.cobertura not in tiene:
            continue
        a = nombres.get(regla.cobertura, regla.cobertura)
        if regla.tipo == "requiere":
            textos.append(f"Regla respetada: «{a}» requiere «{nombres.get(regla.objetivo, regla.objetivo)}»")
        elif regla.tipo == "excluye":
            textos.append(f"Regla respetada: «{a}» excluye «{nombres.get(regla.objetivo, regla.objetivo)}»")
        elif regla.tipo == "deducible_max":
            textos.append(f"Regla respetada: «{a}» exige deducible ≤ {mxn(regla.valor or 0)}")
    return textos
