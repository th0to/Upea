"""Prélude d'exécution d'Upea : arbres, graphes, affichage et fonctions prédéfinies.

Ce module est recopié tel quel en tête de chaque fichier Python généré, qui reste
ainsi autonome. Tous ses noms commencent par `_` : le lexer d'Upea interdit ce
préfixe, aucun programme ne peut donc les écraser.
"""

from __future__ import annotations

import heapq as _heapq
import re as _re
from collections import deque as _deque
from collections.abc import Iterator as _Iterator


class _Erreur(Exception):
    """Une erreur d'exécution dont le message est déjà rédigé pour l'utilisateur."""


def _sorte(valeur: object) -> str:
    """Le nom Upea de la sorte d'une valeur."""
    if isinstance(valeur, bool):
        return "tiahape"
    if isinstance(valeur, int):
        return "numera"
    if isinstance(valeur, float):
        return "tuhaa"
    if isinstance(valeur, str):
        return "parau"
    if valeur is None:
        return "aore"
    if isinstance(valeur, list):
        return "tapura"
    if isinstance(valeur, _Tumu):
        return "tumu"
    if isinstance(valeur, _Upea):
        return "upea"
    return type(valeur).__name__


# --- Arbres -----------------------------------------------------------------------


class _Tumu:
    """Un nœud d'arbre n-aire : une valeur (`hotu`) et des enfants (`amaa`)."""

    __slots__ = ("hotu", "amaa")

    def __init__(self, hotu: object, amaa: list[_Tumu]) -> None:
        self.hotu = hotu
        self.amaa = amaa

    def __eq__(self, autre: object) -> bool:
        return (
            isinstance(autre, _Tumu)
            and self.hotu == autre.hotu
            and self.amaa == autre.amaa
        )

    def __contains__(self, valeur: object) -> bool:
        return any(noeud.hotu == valeur for noeud in _prefixe(self))

    def __repr__(self) -> str:
        return _texte(self, True)


def _verifier_tumu(valeur: object, fonction: str) -> _Tumu:
    if not isinstance(valeur, _Tumu):
        raise _Erreur(f"{fonction} : tumu attendu, {_sorte(valeur)} reçu")
    return valeur


def _enfants(noeud: _Tumu) -> list[_Tumu]:
    if not isinstance(noeud.amaa, list):
        raise _Erreur(
            f"les branches d'un tumu forment une tapura, pas un {_sorte(noeud.amaa)}"
        )
    for enfant in noeud.amaa:
        if not isinstance(enfant, _Tumu):
            raise _Erreur(
                f"les branches d'un tumu doivent être des tumu, pas un {_sorte(enfant)}"
            )
    return noeud.amaa


def _prefixe(racine: _Tumu) -> _Iterator[_Tumu]:
    """Les nœuds en profondeur, ordre préfixe (sans récursion Python)."""
    pile = [racine]
    while pile:
        noeud = pile.pop()
        yield noeud
        pile.extend(reversed(_enfants(noeud)))


def _largeur(racine: _Tumu) -> _Iterator[_Tumu]:
    file = _deque([racine])
    while file:
        noeud = file.popleft()
        yield noeud
        file.extend(_enfants(noeud))


# --- Graphes --------------------------------------------------------------------------


def _verifier_noeud(noeud: object) -> None:
    if type(noeud) not in (int, float, str):
        raise _Erreur(
            "un nœud de upea doit être un numera, un tuhaa ou un parau, "
            f"pas un {_sorte(noeud)}"
        )


class _Upea:
    """Un graphe orienté pondéré ; les nœuds gardent leur ordre d'apparition."""

    __slots__ = ("_arcs",)

    def __init__(self) -> None:
        self._arcs: dict[object, dict[object, int | float]] = {}

    def relier(self, depart: object, arrivee: object, poids: object = 1) -> None:
        _verifier_noeud(depart)
        _verifier_noeud(arrivee)
        if type(poids) not in (int, float):
            raise _Erreur(
                f"le poids d'un arc doit être un nombre, pas un {_sorte(poids)}"
            )
        assert isinstance(poids, int | float)
        if poids < 0:
            raise _Erreur(
                f"le poids d'un arc doit être positif ou nul, pas {_texte(poids)}"
            )
        self._arcs.setdefault(depart, {})
        self._arcs.setdefault(arrivee, {})
        self._arcs[depart][arrivee] = poids

    def verifier(self, noeud: object) -> None:
        if noeud not in self:
            raise _Erreur(f"le nœud {_texte(noeud, True)} n'est pas dans le graphe")

    def successeurs(self, noeud: object) -> list[object]:
        self.verifier(noeud)
        return list(self._arcs[noeud])

    def __contains__(self, noeud: object) -> bool:
        try:
            return noeud in self._arcs
        except TypeError:  # une valeur non hachable n'est jamais un nœud
            return False

    def __eq__(self, autre: object) -> bool:
        return isinstance(autre, _Upea) and self._arcs == autre._arcs

    def __repr__(self) -> str:
        return _texte(self, True)


def _verifier_upea(valeur: object, fonction: str) -> _Upea:
    if not isinstance(valeur, _Upea):
        raise _Erreur(f"{fonction} : upea attendu, {_sorte(valeur)} reçu")
    return valeur


def _graphe(aretes: list[tuple[object, object, object, bool]]) -> _Upea:
    """Construit le graphe d'un littéral `upea { … }`."""
    graphe = _Upea()
    for depart, arrivee, poids, double in aretes:
        graphe.relier(depart, arrivee, poids)
        if double:
            graphe.relier(arrivee, depart, poids)
    return graphe


def _parcours_graphe(graphe: _Upea, depart: object, largeur: bool) -> list[object]:
    graphe.verifier(depart)
    vus: set[object] = set()
    ordre: list[object] = []
    if largeur:
        vus.add(depart)
        file = _deque([depart])
        while file:
            noeud = file.popleft()
            ordre.append(noeud)
            for suivant in graphe._arcs[noeud]:
                if suivant not in vus:
                    vus.add(suivant)
                    file.append(suivant)
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


# --- Affichage ------------------------------------------------------------------------


def _echappe(texte: str) -> str:
    texte = texte.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + texte.replace("\n", "\\n").replace("\t", "\\t") + '"'


def _texte(valeur: object, imbrique: bool = False) -> str:
    """Le texte d'une valeur, tel que l'affiche `faaite`.

    `imbrique` est vrai à l'intérieur d'une liste, d'un arbre ou d'un graphe :
    les textes y sont alors écrits entre guillemets.
    """
    if valeur is True:
        return "tia"
    if valeur is False:
        return "hape"
    if valeur is None:
        return "aore"
    if isinstance(valeur, str):
        return _echappe(valeur) if imbrique else valeur
    if isinstance(valeur, int | float):
        return repr(valeur)
    if isinstance(valeur, list):
        return "[" + ", ".join(_texte(e, True) for e in valeur) + "]"
    if isinstance(valeur, _Tumu):
        morceaux = [_texte(valeur.hotu, True)]
        morceaux.extend(_texte(enfant, True) for enfant in valeur.amaa)
        return "tumu(" + ", ".join(morceaux) + ")"
    if isinstance(valeur, _Upea):
        arcs = []
        for depart, voisins in valeur._arcs.items():
            for arrivee, poids in voisins.items():
                arc = f"{_texte(depart, True)} -> {_texte(arrivee, True)}"
                arcs.append(arc if poids == 1 else f"{arc} : {_texte(poids)}")
        return "upea { " + ", ".join(arcs) + " }" if arcs else "upea {}"
    return str(valeur)


def _affiche(*valeurs: object) -> None:
    print(" ".join(_texte(v) for v in valeurs))


# --- La boucle tataitahi --------------------------------------------------------------

_SANS = object()


def _parcours(
    valeur: object, depart: object = _SANS, mode: str | None = None
) -> list[object]:
    """Ce que parcourt `tataitahi`, fixé au début de la boucle."""
    if isinstance(valeur, _Upea):
        if depart is _SANS:
            if mode is not None:
                raise _Erreur(
                    f"un parcours '{mode}' d'un upea demande un point de départ : "
                    "ajoutez 'mai'"
                )
            return list(valeur._arcs)
        return _parcours_graphe(valeur, depart, mode == "aano")
    if depart is not _SANS:
        raise _Erreur(f"'mai' ne s'emploie qu'avec un upea, pas un {_sorte(valeur)}")
    if isinstance(valeur, _Tumu):
        return list(_largeur(valeur) if mode == "aano" else _prefixe(valeur))
    if isinstance(valeur, list | str):
        if mode is not None:
            raise _Erreur(
                f"'{mode}' ne s'emploie qu'avec un tumu ou un upea, "
                f"pas un {_sorte(valeur)}"
            )
        return list(valeur)
    raise _Erreur(f"on ne peut pas parcourir un {_sorte(valeur)}")


# --- Fonctions prédéfinies ------------------------------------------------------------


def _roa(valeur: object) -> int:
    if isinstance(valeur, str | list):
        return len(valeur)
    if isinstance(valeur, _Tumu):
        return sum(1 for _ in _prefixe(valeur))
    if isinstance(valeur, _Upea):
        return len(valeur._arcs)
    raise _Erreur(f"roa : impossible de mesurer un {_sorte(valeur)}")


def _amui(liste: object, valeur: object) -> None:
    if not isinstance(liste, list):
        raise _Erreur(f"amui : tapura attendue, {_sorte(liste)} reçu")
    liste.append(valeur)


_ENTIER = _re.compile(r"[+-]?[0-9]+")
_DECIMAL = _re.compile(r"[+-]?[0-9]+(\.[0-9]+)?")


def _numera(valeur: object) -> int:
    if isinstance(valeur, bool | int):
        return int(valeur)
    if isinstance(valeur, float):
        if valeur != valeur or valeur in (float("inf"), float("-inf")):
            raise _Erreur(
                f"conversion impossible : {_texte(valeur)} n'est pas un numera"
            )
        return int(valeur)
    if isinstance(valeur, str) and _ENTIER.fullmatch(valeur.strip()):
        return int(valeur.strip())
    if isinstance(valeur, str):
        raise _Erreur(f"conversion impossible : {_echappe(valeur)} n'est pas un numera")
    raise _Erreur(
        f"conversion impossible : un {_sorte(valeur)} ne devient pas un numera"
    )


def _tuhaa(valeur: object) -> float:
    if isinstance(valeur, int | float) and not isinstance(valeur, bool):
        return float(valeur)
    if isinstance(valeur, str) and _DECIMAL.fullmatch(valeur.strip()):
        return float(valeur.strip())
    if isinstance(valeur, str):
        raise _Erreur(f"conversion impossible : {_echappe(valeur)} n'est pas un tuhaa")
    raise _Erreur(
        f"conversion impossible : un {_sorte(valeur)} ne devient pas un tuhaa"
    )


def _parau(valeur: object) -> str:
    return _texte(valeur)


def _tumu(hotu: object, *enfants: object) -> _Tumu:
    branches: list[_Tumu] = []
    for enfant in enfants:
        if not isinstance(enfant, _Tumu):
            raise _Erreur(
                f"tumu : les enfants doivent être des tumu, pas un {_sorte(enfant)}"
            )
        branches.append(enfant)
    return _Tumu(hotu, branches)


def _teitei(arbre: object) -> int:
    racine = _verifier_tumu(arbre, "teitei")
    hauteur = 0
    pile = [(racine, 0)]
    while pile:
        noeud, profondeur = pile.pop()
        hauteur = max(hauteur, profondeur)
        pile.extend((enfant, profondeur + 1) for enfant in _enfants(noeud))
    return hauteur


def _rau(arbre: object) -> list[object]:
    racine = _verifier_tumu(arbre, "rau")
    return [noeud.hotu for noeud in _prefixe(racine) if not noeud.amaa]


def _taati(graphe: object, depart: object, arrivee: object, poids: object = 1) -> None:
    _verifier_upea(graphe, "taati").relier(depart, arrivee, poids)


def _pihai(graphe: object, noeud: object) -> list[object]:
    return _verifier_upea(graphe, "pihai").successeurs(noeud)


def _motu(graphe: object) -> list[object]:
    return list(_verifier_upea(graphe, "motu")._arcs)


def _teiaha(graphe: object, depart: object, arrivee: object) -> int | float:
    g = _verifier_upea(graphe, "teiaha")
    g.verifier(depart)
    g.verifier(arrivee)
    if arrivee not in g._arcs[depart]:
        raise _Erreur(
            f"pas d'arc de {_texte(depart, True)} vers {_texte(arrivee, True)}"
        )
    return g._arcs[depart][arrivee]


def _tae(graphe: object, depart: object, arrivee: object) -> bool:
    g = _verifier_upea(graphe, "tae")
    g.verifier(arrivee)
    return arrivee in _parcours_graphe(g, depart, True)


def _ea(graphe: object, depart: object, arrivee: object) -> list[object] | None:
    """Le plus court chemin pondéré (Dijkstra), ou `None` s'il n'y en a pas."""
    g = _verifier_upea(graphe, "ea")
    g.verifier(depart)
    g.verifier(arrivee)
    distances: dict[object, int | float] = {depart: 0}
    precedents: dict[object, object] = {}
    compteur = 0  # départage les égalités dans l'ordre d'insertion
    tas: list[tuple[int | float, int, object]] = [(0, compteur, depart)]
    finis: set[object] = set()
    while tas:
        distance, _, noeud = _heapq.heappop(tas)
        if noeud in finis:
            continue
        finis.add(noeud)
        if noeud == arrivee:
            break
        for suivant, poids in g._arcs[noeud].items():
            candidate = distance + poids
            if suivant not in distances or candidate < distances[suivant]:
                distances[suivant] = candidate
                precedents[suivant] = noeud
                compteur += 1
                _heapq.heappush(tas, (candidate, compteur, suivant))
    if arrivee not in finis:
        return None
    chemin = [arrivee]
    while chemin[-1] != depart:
        chemin.append(precedents[chemin[-1]])
    chemin.reverse()
    return chemin
