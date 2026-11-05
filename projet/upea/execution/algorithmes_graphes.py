"""Prélude — les algorithmes de graphes : plus courts chemins, structure, arbres
couvrants et flots.

Partout, à égalité, l'ordre d'insertion des nœuds et des arcs décide : les
résultats sont toujours les mêmes, et se calculent à la main.
"""

from __future__ import annotations

import heapq as _heapq
from collections import deque as _deque
from collections.abc import Iterator as _Iterator
from itertools import count as _count
from itertools import pairwise as _pairwise
from itertools import product as _product

from .base import _Erreur
from .graphes import _Poids, _sur_graphe, _Upea

type _Distances = dict[object, _Poids]
type _Precedents = dict[object, object]

_INFINI = float("inf")


def _rangs(graphe: _Upea) -> dict[object, int]:
    """Le rang d'apparition de chaque nœud, pour trier de façon déterministe."""
    return {noeud: i for i, noeud in enumerate(graphe._arcs)}


def _chemin(precedents: _Precedents, depart: object, arrivee: object) -> list[object]:
    chemin = [arrivee]
    while chemin[-1] != depart:
        chemin.append(precedents[chemin[-1]])
    return chemin[::-1]


def _poids_chemin(graphe: _Upea, chemin: list[object]) -> _Poids:
    return sum(graphe._arcs[a][b] for a, b in _pairwise(chemin))


# --- Plus courts chemins --------------------------------------------------------------


def _dijkstra_depuis(graphe: _Upea, depart: object) -> tuple[_Distances, _Precedents]:
    if any(poids < 0 for _, _, poids in graphe.arcs()):
        raise _Erreur("dijkstra : poids négatif : utilisez bellman_ford")
    distances: _Distances = {depart: 0}
    precedents: _Precedents = {}
    ordre = _count()  # départage les égalités dans l'ordre d'ajout au tas
    tas: list[tuple[_Poids, int, object]] = [(0, next(ordre), depart)]
    finis: set[object] = set()
    while tas:
        distance, _, noeud = _heapq.heappop(tas)
        if noeud in finis:
            continue
        finis.add(noeud)
        for suivant, poids in graphe._arcs[noeud].items():
            candidate = distance + poids
            if suivant not in distances or candidate < distances[suivant]:
                distances[suivant] = candidate
                precedents[suivant] = noeud
                _heapq.heappush(tas, (candidate, next(ordre), suivant))
    return distances, precedents


def _bellman_ford_depuis(
    graphe: _Upea, depart: object
) -> tuple[_Distances, _Precedents]:
    distances: _Distances = {depart: 0}
    precedents: _Precedents = {}
    arcs = graphe.arcs()
    for _ in range(len(graphe._arcs) - 1):
        change = False
        for a, b, poids in arcs:
            if a in distances and distances[a] + poids < distances.get(b, _INFINI):
                distances[b] = distances[a] + poids
                precedents[b] = a
                change = True
        if not change:
            break
    if any(a in distances and distances[a] + p < distances[b] for a, b, p in arcs):
        raise _Erreur("bellman_ford : cycle de poids négatif atteignable")
    return distances, precedents


@_sur_graphe(1, 2)
def _dijkstra(graphe: _Upea, depart: object, arrivee: object) -> list[object] | None:
    distances, precedents = _dijkstra_depuis(graphe, depart)
    return _chemin(precedents, depart, arrivee) if arrivee in distances else None


_ea = _dijkstra  # le nom tahitien (ʻeʻa, chemin) du plus court chemin


@_sur_graphe(1, 2)
def _bellman_ford(
    graphe: _Upea, depart: object, arrivee: object
) -> list[object] | None:
    distances, precedents = _bellman_ford_depuis(graphe, depart)
    return _chemin(precedents, depart, arrivee) if arrivee in distances else None


@_sur_graphe(1, 2)
def _distance(graphe: _Upea, depart: object, arrivee: object) -> _Poids | None:
    """Le poids du plus court chemin (Bellman-Ford s'il y a des poids négatifs)."""
    negatifs = any(poids < 0 for _, _, poids in graphe.arcs())
    calcul = _bellman_ford_depuis if negatifs else _dijkstra_depuis
    distances, precedents = calcul(graphe, depart)
    if arrivee not in distances:
        return None
    return _poids_chemin(graphe, _chemin(precedents, depart, arrivee))


@_sur_graphe()
def _floyd_warshall(graphe: _Upea) -> _Upea:
    """Le graphe des distances : un arc a -> b pour chaque b atteignable depuis a."""
    noeuds = list(graphe._arcs)
    distance: dict[object, dict[object, _Poids]] = {
        a: {b: 0 if a == b else graphe._arcs[a].get(b, _INFINI) for b in noeuds}
        for a in noeuds
    }
    for k, i, j in _product(noeuds, repeat=3):  # k change le moins vite
        if distance[i][k] + distance[k][j] < distance[i][j]:
            distance[i][j] = distance[i][k] + distance[k][j]
    if any(distance[n][n] < 0 for n in noeuds):
        raise _Erreur("floyd_warshall : cycle de poids négatif")
    resultat = _Upea()
    for i, j in _product(noeuds, repeat=2):
        if i != j and distance[i][j] != _INFINI:
            resultat.relier(i, j, distance[i][j])
    return resultat


# --- Structure ------------------------------------------------------------------------


@_sur_graphe()
def _tri_topologique(graphe: _Upea) -> list[object] | None:
    """L'ordre de Kahn (les sources dans l'ordre d'apparition), ou `None` s'il y a
    un cycle."""
    degres = dict.fromkeys(graphe._arcs, 0)
    for _, arrivee, _ in graphe.arcs():
        degres[arrivee] += 1
    file = _deque(n for n, d in degres.items() if d == 0)
    ordre = []
    while file:
        noeud = file.popleft()
        ordre.append(noeud)
        for suivant in graphe._arcs[noeud]:
            degres[suivant] -= 1
            if degres[suivant] == 0:
                file.append(suivant)
    return ordre if len(ordre) == len(degres) else None


@_sur_graphe()
def _cycle(graphe: _Upea) -> bool:
    return _tri_topologique(graphe) is None


def _voisins_non_orientes(graphe: _Upea) -> dict[object, dict[object, None]]:
    """Pour chaque nœud, ses voisins quand on oublie le sens des arcs (dans l'ordre)."""
    voisins: dict[object, dict[object, None]] = {n: {} for n in graphe._arcs}
    for a, b, _ in graphe.arcs():
        voisins[a][b] = None
        voisins[b][a] = None
    return voisins


@_sur_graphe()
def _composantes(graphe: _Upea) -> list[list[object]]:
    """Les composantes connexes (sans tenir compte du sens des arcs)."""
    voisins, rangs = _voisins_non_orientes(graphe), _rangs(graphe)
    vus: set[object] = set()
    composantes = []
    for depart in graphe._arcs:
        if depart in vus:
            continue
        vus.add(depart)
        file, composante = _deque([depart]), []
        while file:
            noeud = file.popleft()
            composante.append(noeud)
            nouveaux = [v for v in voisins[noeud] if v not in vus]
            vus.update(nouveaux)
            file.extend(nouveaux)
        composantes.append(sorted(composante, key=rangs.__getitem__))
    return composantes


@_sur_graphe()
def _tarjan(graphe: _Upea) -> list[list[object]]:
    """Les composantes fortement connexes (algorithme de Tarjan, sans récursion).

    Chaque composante est rangée dans l'ordre d'apparition de ses nœuds, et les
    composantes selon leur premier nœud.
    """
    indice: dict[object, int] = {}
    bas: dict[object, int] = {}
    pile: list[object] = []
    sur_pile: set[object] = set()
    composantes: list[list[object]] = []
    numero = _count()
    # Chaque cadre : un nœud, et l'itérateur de ses successeurs pas encore vus.
    cadres: list[tuple[object, _Iterator[object]]] = []

    def entrer(noeud: object) -> None:
        indice[noeud] = bas[noeud] = next(numero)
        pile.append(noeud)
        sur_pile.add(noeud)
        cadres.append((noeud, iter(graphe._arcs[noeud])))

    for racine in graphe._arcs:
        if racine in indice:
            continue
        entrer(racine)
        while cadres:
            noeud, successeurs = cadres[-1]
            suivant = next(successeurs, None)
            if suivant is not None:
                if suivant not in indice:
                    entrer(suivant)
                elif suivant in sur_pile:
                    bas[noeud] = min(bas[noeud], indice[suivant])
                continue
            cadres.pop()
            if cadres:
                parent = cadres[-1][0]
                bas[parent] = min(bas[parent], bas[noeud])
            if bas[noeud] == indice[noeud]:
                composante = []
                while True:
                    membre = pile.pop()
                    sur_pile.discard(membre)
                    composante.append(membre)
                    if membre == noeud:
                        break
                composantes.append(composante)
    rangs = _rangs(graphe)
    triees = [sorted(c, key=rangs.__getitem__) for c in composantes]
    return sorted(triees, key=lambda c: rangs[c[0]])


@_sur_graphe()
def _biparti(graphe: _Upea) -> bool:
    """Peut-on colorer les nœuds en deux couleurs, sans arc entre deux nœuds de même
    couleur (sans tenir compte du sens des arcs) ?"""
    voisins = _voisins_non_orientes(graphe)
    couleur: dict[object, bool] = {}
    for depart in graphe._arcs:
        if depart in couleur:
            continue
        couleur[depart] = True
        file = _deque([depart])
        while file:
            noeud = file.popleft()
            for voisin in voisins[noeud]:
                if voisin not in couleur:
                    couleur[voisin] = not couleur[noeud]
                    file.append(voisin)
                elif couleur[voisin] == couleur[noeud]:
                    return False
    return True


# --- Arbres couvrants et flots --------------------------------------------------------


def _aretes_non_orientees(graphe: _Upea) -> list[tuple[object, object, _Poids]]:
    """Une arête par paire de nœuds reliés, de poids le plus petit des deux sens."""
    aretes: dict[frozenset[object], tuple[object, object, _Poids]] = {}
    for a, b, poids in graphe.arcs():
        if a == b:
            continue
        paire = frozenset((a, b))
        if paire not in aretes:
            aretes[paire] = (a, b, poids)
        elif poids < aretes[paire][2]:
            aretes[paire] = (*aretes[paire][:2], poids)
    return list(aretes.values())


class _Ensembles:
    """Union-find, avec compression des chemins et union par rang."""

    def __init__(self) -> None:
        self.parent: dict[object, object] = {}
        self.rang: dict[object, int] = {}

    def trouver(self, x: object) -> object:
        self.parent.setdefault(x, x)
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def unir(self, a: object, b: object) -> bool:
        ra, rb = self.trouver(a), self.trouver(b)
        if ra == rb:
            return False
        rang_a, rang_b = self.rang.get(ra, 0), self.rang.get(rb, 0)
        if rang_a < rang_b:
            ra, rb = rb, ra
        self.parent[rb] = ra
        if rang_a == rang_b:
            self.rang[ra] = rang_a + 1
        return True


def _couvrant(graphe: _Upea, aretes: list[tuple[object, object, _Poids]]) -> _Upea:
    """La forêt de ces arêtes, puis les nœuds du graphe qu'aucune ne touche (dans
    l'ordre d'apparition) : une forêt couvrante couvre tous les nœuds."""
    arbre = _Upea()
    for a, b, poids in aretes:
        arbre.relier(a, b, poids)
        arbre.relier(b, a, poids)
    for noeud in graphe._arcs:
        arbre.ajouter(noeud)
    return arbre


@_sur_graphe()
def _kruskal(graphe: _Upea) -> _Upea:
    """L'arbre (ou la forêt) couvrant de poids minimal, arcs pris sans orientation."""
    ensembles = _Ensembles()
    # `sorted` est stable : à poids égal, l'ordre d'apparition des arêtes décide.
    aretes = sorted(_aretes_non_orientees(graphe), key=lambda arete: arete[2])
    return _couvrant(graphe, [(a, b, p) for a, b, p in aretes if ensembles.unir(a, b)])


@_sur_graphe()
def _prim(graphe: _Upea) -> _Upea:
    """L'arbre (ou la forêt) couvrant de poids minimal, grandi depuis chaque nœud
    pas encore atteint, dans l'ordre d'apparition."""
    voisins: dict[object, list[tuple[object, _Poids]]] = {n: [] for n in graphe._arcs}
    for a, b, poids in _aretes_non_orientees(graphe):
        voisins[a].append((b, poids))
        voisins[b].append((a, poids))
    atteints: set[object] = set()
    choisies = []
    ordre = _count()
    for depart in graphe._arcs:
        if depart in atteints:
            continue
        atteints.add(depart)
        tas = [(p, next(ordre), depart, v) for v, p in voisins[depart]]
        _heapq.heapify(tas)
        while tas:
            poids, _, a, b = _heapq.heappop(tas)
            if b in atteints:
                continue
            atteints.add(b)
            choisies.append((a, b, poids))
            for v, p in voisins[b]:
                if v not in atteints:
                    _heapq.heappush(tas, (p, next(ordre), b, v))
    return _couvrant(graphe, choisies)


@_sur_graphe(1, 2)
def _edmonds_karp(graphe: _Upea, source: object, puits: object) -> _Poids:
    """Le flot maximal de `source` à `puits` ; les poids sont les capacités."""
    if any(poids < 0 for _, _, poids in graphe.arcs()):
        raise _Erreur("edmonds_karp : une capacité ne peut pas être négative")
    residuel: dict[object, dict[object, _Poids]] = {n: {} for n in graphe._arcs}
    for a, b, poids in graphe.arcs():
        residuel[a][b] = residuel[a].get(b, 0) + poids
        residuel[b].setdefault(a, 0)
    flot: _Poids = 0
    while source != puits:
        precedents: _Precedents = {source: source}
        file = _deque([source])
        while file and puits not in precedents:
            noeud = file.popleft()
            for suivant, capacite in residuel[noeud].items():
                if capacite > 0 and suivant not in precedents:
                    precedents[suivant] = noeud
                    file.append(suivant)
        if puits not in precedents:
            break
        chemin = _chemin(precedents, source, puits)
        goulot = min(residuel[a][b] for a, b in _pairwise(chemin))
        for a, b in _pairwise(chemin):
            residuel[a][b] -= goulot
            residuel[b][a] += goulot
        flot += goulot
    return flot
