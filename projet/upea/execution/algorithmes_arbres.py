"""Prélude — les algorithmes d'arbres, écrits une seule fois pour toutes les sortes
(`tumu`, `imi`, `aifaito`, `uteere`, `pupu`, `ahu`) grâce à la vue de `vues`.

Aucun n'est récursif : un arbre dégénéré (un `imi` rempli dans l'ordre) ne sature
pas la pile de Python.
"""

from __future__ import annotations

from collections import deque as _deque
from collections.abc import Iterable as _Iterable
from collections.abc import Iterator as _Iterator
from itertools import chain as _chain
from typing import Any as _Any

from .base import _attend
from .vues import (
    _ARBRE,
    _cles,
    _deplier,
    _fils,
    _NoeudTas,
    _positions,
    _racine,
)


def _ident(noeud: object) -> int:
    """Une identité stable pour un nœud (les nœuds de tas sont des vues recréées)."""
    return noeud.indice if isinstance(noeud, _NoeudTas) else id(noeud)


def _noeuds_prefixe(arbre: object) -> _Iterator[_Any]:
    """Les nœuds en profondeur, ordre préfixe."""
    racine = _racine(arbre)
    pile = [] if racine is None else [racine]
    while pile:
        noeud = pile.pop()
        yield noeud
        pile.extend(reversed(_fils(noeud)))


def _noeuds_largeur(arbre: object) -> _Iterator[tuple[_Any, int]]:
    """Les nœuds en largeur, chacun avec sa profondeur."""
    racine = _racine(arbre)
    file = _deque([] if racine is None else [(racine, 0)])
    while file:
        noeud, profondeur = file.popleft()
        yield noeud, profondeur
        file.extend((enfant, profondeur + 1) for enfant in _fils(noeud))


def _toutes_les_cles(noeuds: _Iterable[_Any]) -> list[_Any]:
    return list(_chain.from_iterable(map(_cles, noeuds)))


def _taille(arbre: object) -> int:
    return sum(len(_cles(noeud)) for noeud in _noeuds_prefixe(arbre))


# --- Les parcours ---------------------------------------------------------------------


@_attend(_ARBRE)
def _prefixe(arbre: object) -> list[_Any]:
    return _toutes_les_cles(_noeuds_prefixe(arbre))


@_attend(_ARBRE)
def _largeur(arbre: object) -> list[_Any]:
    return _toutes_les_cles(noeud for noeud, _ in _noeuds_largeur(arbre))


@_attend(_ARBRE)
def _postfixe(arbre: object) -> list[_Any]:
    # Le préfixe « miroir » (la racine, puis les enfants de droite à gauche),
    # lu à l'envers, donne les enfants de gauche à droite, puis la racine.
    racine = _racine(arbre)
    pile, miroir = ([] if racine is None else [racine]), []
    while pile:
        noeud = pile.pop()
        miroir.append(noeud)
        pile.extend(_fils(noeud))
    return _toutes_les_cles(reversed(miroir))


@_attend(_ARBRE)
def _infixe(arbre: object) -> list[_Any]:
    racine = _racine(arbre)
    pile: list[tuple[bool, _Any]] = [] if racine is None else [(False, racine)]
    resultat = []
    while pile:
        est_cle, objet = pile.pop()
        if est_cle:
            resultat.append(objet)
        elif objet is not None:
            pile.extend(reversed(_deplier(objet)))
    return resultat


# --- Mesures --------------------------------------------------------------------------


@_attend(_ARBRE)
def _teitei(arbre: object) -> int:
    """La hauteur, en arcs : 0 pour une feuille, -1 pour un arbre vide."""
    return max((profondeur for _, profondeur in _noeuds_largeur(arbre)), default=-1)


@_attend(_ARBRE)
def _rau(arbre: object) -> list[_Any]:
    return _toutes_les_cles(n for n in _noeuds_prefixe(arbre) if not _fils(n))


@_attend(_ARBRE)
def _profondeur(arbre: object, valeur: object) -> int | None:
    trouves = (p for noeud, p in _noeuds_largeur(arbre) if valeur in _cles(noeud))
    return next(trouves, None)


def _hauteurs(arbre: object) -> tuple[list[_Any], dict[int, int]]:
    """Les nœuds en ordre préfixe, et la hauteur de chacun (calculée des feuilles
    vers la racine, en lisant l'ordre préfixe à l'envers)."""
    noeuds = list(_noeuds_prefixe(arbre))
    hauteur: dict[int, int] = {}
    for noeud in reversed(noeuds):
        enfants = [hauteur[_ident(e)] for e in _fils(noeud)]
        hauteur[_ident(noeud)] = 1 + max(enfants, default=-1)
    return noeuds, hauteur


@_attend(_ARBRE)
def _diametre(arbre: object) -> int:
    """Le plus long chemin entre deux nœuds, en arcs."""
    noeuds, hauteur = _hauteurs(arbre)
    meilleur = 0
    for noeud in noeuds:
        branches = sorted((hauteur[_ident(e)] + 1 for e in _fils(noeud)), reverse=True)
        meilleur = max(meilleur, sum(branches[:2]))
    return meilleur


@_attend(_ARBRE)
def _equilibre(arbre: object) -> bool:
    """En chaque nœud, les hauteurs des sous-arbres diffèrent d'au plus 1 (un enfant
    absent d'un arbre binaire compte pour -1)."""
    noeuds, hauteur = _hauteurs(arbre)
    for noeud in noeuds:
        positions = [-1 if e is None else hauteur[_ident(e)] for e in _positions(noeud)]
        if positions and max(positions) - min(positions) > 1:
            return False
    return True


@_attend(_ARBRE)
def _ancetre(arbre: object, a: object, b: object) -> object:
    """Le plus proche ancêtre commun des nœuds qui portent `a` et `b`, ou `None`."""
    parents: dict[int, _Any] = {}
    noeud_a = noeud_b = None
    racine = _racine(arbre)
    file = _deque([] if racine is None else [racine])
    while file:
        noeud = file.popleft()
        cles = _cles(noeud)
        noeud_a = noeud if noeud_a is None and a in cles else noeud_a
        noeud_b = noeud if noeud_b is None and b in cles else noeud_b
        for enfant in _fils(noeud):
            parents[_ident(enfant)] = noeud
            file.append(enfant)
    if noeud_a is None or noeud_b is None:
        return None

    def ascendance(noeud: _Any) -> _Iterator[_Any]:
        while noeud is not None:
            yield noeud
            noeud = parents.get(_ident(noeud))

    ancetres_de_a = {_ident(n) for n in ascendance(noeud_a)}
    commun = next(n for n in ascendance(noeud_b) if _ident(n) in ancetres_de_a)
    cles = _cles(commun)
    return cles[0] if len(cles) == 1 else cles
