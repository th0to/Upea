"""Prélude — les graphes `upea` : orientés, pondérés, aux nœuds rangés dans leur
ordre d'apparition."""

from __future__ import annotations

import math as _math
from collections import deque as _deque
from collections.abc import Callable as _Callable
from functools import wraps as _wraps

from .base import _P, _R, _Erreur, _sorte, _sorte_upea, _texte

type _Poids = int | float


def _verifier_noeud(noeud: object) -> None:
    if type(noeud) not in (int, float, str):
        raise _Erreur(
            "un nœud de upea doit être un numera, un tuhaa ou un parau, "
            f"pas un {_sorte(noeud)}"
        )
    # Un NaN n'est égal à rien, pas même à lui-même : il ferait un nœud par ajout.
    if type(noeud) is float and not _math.isfinite(noeud):
        raise _Erreur(f"un nœud de upea doit être un nombre fini, pas {_texte(noeud)}")


@_sorte_upea("upea")
class _Upea:
    __slots__ = ("_arcs",)

    def __init__(self) -> None:
        self._arcs: dict[object, dict[object, _Poids]] = {}

    def relier(self, depart: object, arrivee: object, poids: object = 1) -> None:
        _verifier_noeud(depart)
        _verifier_noeud(arrivee)
        if type(poids) not in (int, float):
            raise _Erreur(
                f"le poids d'un arc doit être un nombre, pas un {_sorte(poids)}"
            )
        assert isinstance(poids, int | float)
        if not _math.isfinite(poids):
            raise _Erreur(
                f"le poids d'un arc doit être un nombre fini, pas {_texte(poids)}"
            )
        self.ajouter(depart)
        self.ajouter(arrivee)
        self._arcs[depart][arrivee] = poids

    def ajouter(self, noeud: object) -> None:
        _verifier_noeud(noeud)
        self._arcs.setdefault(noeud, {})

    def verifier(self, noeud: object) -> None:
        if noeud not in self:
            raise _Erreur(f"le nœud {_texte(noeud, True)} n'est pas dans le graphe")

    def successeurs(self, noeud: object) -> list[object]:
        self.verifier(noeud)
        return list(self._arcs[noeud])

    def retirer_noeud(self, noeud: object) -> bool:
        if noeud not in self:
            return False
        del self._arcs[noeud]
        for voisins in self._arcs.values():
            voisins.pop(noeud, None)
        return True

    def arcs(self) -> list[tuple[object, object, _Poids]]:
        return [
            (a, b, p) for a, voisins in self._arcs.items() for b, p in voisins.items()
        ]

    def __contains__(self, noeud: object) -> bool:
        try:
            return noeud in self._arcs
        except TypeError:  # une valeur non hachable n'est jamais un nœud
            return False

    def __eq__(self, autre: object) -> bool:
        return isinstance(autre, _Upea) and self._arcs == autre._arcs

    def __repr__(self) -> str:
        return _texte(self, True)


def _graphe(aretes: list[tuple[object, object, object, bool]]) -> _Upea:
    """Construit le graphe d'un littéral `upea { … }` ; un nœud seul y a une
    arrivée `None`."""
    graphe = _Upea()
    for depart, arrivee, poids, double in aretes:
        if arrivee is None:
            graphe.ajouter(depart)
            continue
        graphe.relier(depart, arrivee, poids)
        if double:
            graphe.relier(arrivee, depart, poids)
    return graphe


type _Liaison = tuple[object, object, _Poids | None, bool]


def _liaisons(graphe: _Upea) -> list[_Liaison]:
    """Les liaisons du graphe, comme les écrirait un littéral : un arc et son retour
    de même poids forment une liaison double (`<->`), et un nœud que rien ne relie
    donne `(noeud, None, None, False)`."""
    arrivees = {b for voisins in graphe._arcs.values() for b in voisins}
    faits: set[tuple[object, object]] = set()
    liaisons: list[_Liaison] = []
    for a, voisins in graphe._arcs.items():
        if not voisins and a not in arrivees:
            liaisons.append((a, None, None, False))
        for b, poids in voisins.items():
            if (a, b) in faits:
                continue
            double = a != b and graphe._arcs[b].get(a) == poids
            if double:
                faits.add((b, a))
            liaisons.append((a, b, poids, double))
    return liaisons


@_texte.register(_Upea)
def _(valeur: _Upea, imbrique: bool = False) -> str:
    morceaux = []
    for depart, arrivee, poids, double in _liaisons(valeur):
        if arrivee is None:
            morceaux.append(_texte(depart, True))
            continue
        fleche = "<->" if double else "->"
        arc = f"{_texte(depart, True)} {fleche} {_texte(arrivee, True)}"
        morceaux.append(arc if poids == 1 else f"{arc} : {_texte(poids)}")
    return "upea { " + ", ".join(morceaux) + " }" if morceaux else "upea {}"


def _sur_graphe(*noeuds: int) -> _Callable[[_Callable[_P, _R]], _Callable[_P, _R]]:
    """Décorateur paramétré des fonctions sur les graphes : le premier argument doit
    être un `upea`, et les arguments d'indices `noeuds` des nœuds de ce graphe."""

    def decorer(fonction: _Callable[_P, _R]) -> _Callable[_P, _R]:
        nom = fonction.__name__.lstrip("_")

        @_wraps(fonction)
        def verifiee(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            graphe = args[0]
            if not isinstance(graphe, _Upea):
                raise _Erreur(f"{nom} : upea attendu, {_sorte(graphe)} reçu")
            for i in noeuds:
                graphe.verifier(args[i])
            return fonction(*args, **kwargs)

        return verifiee

    return decorer


def _parcours_graphe(graphe: _Upea, depart: object, largeur: bool) -> list[object]:
    """Les nœuds atteignables depuis `depart`, en largeur ou en profondeur (préfixe)."""
    graphe.verifier(depart)
    vus: set[object] = set()
    ordre: list[object] = []
    if largeur:
        vus.add(depart)
        file = _deque([depart])
        while file:
            noeud = file.popleft()
            ordre.append(noeud)
            nouveaux = [s for s in graphe._arcs[noeud] if s not in vus]
            vus.update(nouveaux)
            file.extend(nouveaux)
        return ordre
    pile = [depart]
    while pile:
        noeud = pile.pop()
        if noeud in vus:
            continue
        vus.add(noeud)
        ordre.append(noeud)
        pile.extend(reversed(list(graphe._arcs[noeud])))
    return ordre


# --- Les opérations de base -----------------------------------------------------------


@_sur_graphe()
def _taati(graphe: _Upea, depart: object, arrivee: object, poids: object = 1) -> None:
    graphe.relier(depart, arrivee, poids)


@_sur_graphe(1)
def _pihai(graphe: _Upea, noeud: object) -> list[object]:
    return graphe.successeurs(noeud)


@_sur_graphe()
def _motu(graphe: _Upea) -> list[object]:
    return list(graphe._arcs)


@_sur_graphe(1, 2)
def _teiaha(graphe: _Upea, depart: object, arrivee: object) -> _Poids:
    if arrivee not in graphe._arcs[depart]:
        raise _Erreur(
            f"pas d'arc de {_texte(depart, True)} vers {_texte(arrivee, True)}"
        )
    return graphe._arcs[depart][arrivee]


@_sur_graphe(1, 2)
def _tae(graphe: _Upea, depart: object, arrivee: object) -> bool:
    return arrivee in _parcours_graphe(graphe, depart, True)


@_sur_graphe(1)
def _bfs(graphe: _Upea, depart: object) -> list[object]:
    return _parcours_graphe(graphe, depart, True)


@_sur_graphe(1)
def _dfs(graphe: _Upea, depart: object) -> list[object]:
    return _parcours_graphe(graphe, depart, False)
