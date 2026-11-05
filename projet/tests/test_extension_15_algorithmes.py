"""Extension 15 : les algorithmes natifs, sur les graphes et sur toutes les sortes
d'arbres. Les résultats sont comparés à des cas connus, et entre algorithmes."""

import random
from collections.abc import Callable
from itertools import chain, pairwise, product

import pytest

from outils import lancer
from upea.erreurs import ErreurExecution
from upea.execution.algorithmes_arbres import (
    _ancetre,
    _diametre,
    _infixe,
    _largeur,
    _postfixe,
    _prefixe,
    _profondeur,
    _rau,
    _teitei,
)
from upea.execution.algorithmes_graphes import (
    _bellman_ford,
    _composantes,
    _dijkstra,
    _distance,
    _edmonds_karp,
    _floyd_warshall,
    _kruskal,
    _prim,
    _tarjan,
    _tri_topologique,
)
from upea.execution.arbre_b import _Pupu
from upea.execution.graphes import _graphe, _parcours_graphe, _Upea
from upea.execution.recherche import _Aifaito, _Imi, _Uteere
from upea.execution.tas import _Ahu
from upea.execution.tumu import _tumu


def graphe_aleatoire(graine: int, noeuds: int = 8, arcs: int = 18) -> _Upea:
    hasard = random.Random(graine)
    g = _Upea()
    for _ in range(arcs):
        a, b = hasard.randrange(noeuds), hasard.randrange(noeuds)
        g.relier(a, b, hasard.randrange(1, 20))
    return g


def poids_total(arbre: _Upea) -> int | float:
    return sum(p for _, _, p in arbre.arcs()) / 2  # chaque arête y est deux fois


# --- Chemins --------------------------------------------------------------------------


@pytest.mark.parametrize("graine", range(10))
def test_floyd_warshall_donne_les_distances_de_dijkstra(graine: int) -> None:
    g = graphe_aleatoire(graine)
    distances = _floyd_warshall(g)
    for a, b in product(g._arcs, repeat=2):
        if a == b:
            continue
        chemin = _dijkstra(g, a, b)
        if chemin is None:
            assert b not in distances._arcs.get(a, {})
        else:
            poids = sum(g._arcs[x][y] for x, y in pairwise(chemin))
            assert distances._arcs[a][b] == poids == _distance(g, a, b)


@pytest.mark.parametrize("graine", range(10))
def test_bellman_ford_et_dijkstra_s_accordent_sans_poids_negatif(graine: int) -> None:
    g = graphe_aleatoire(graine)
    for b in g._arcs:
        attendu = _dijkstra(g, 0, b) if 0 in g._arcs else None
        if 0 in g._arcs:
            chemin = _bellman_ford(g, 0, b)
            assert (chemin is None) == (attendu is None)


def test_bellman_ford_suit_les_poids_negatifs() -> None:
    g = _graphe([("A", "B", 4, False), ("A", "C", 2, False), ("C", "B", -3, False)])
    assert _bellman_ford(g, "A", "B") == ["A", "C", "B"]
    assert _distance(g, "A", "B") == -1


def test_un_cycle_negatif_est_refuse() -> None:
    g = _graphe([(1, 2, 1, False), (2, 3, -2, False), (3, 1, -1, False)])
    with pytest.raises(Exception, match="cycle de poids négatif"):
        _bellman_ford(g, 1, 3)
    with pytest.raises(Exception, match="cycle de poids négatif"):
        _floyd_warshall(g)


def test_dijkstra_refuse_les_poids_negatifs() -> None:
    with pytest.raises(Exception, match="poids négatif : utilisez bellman_ford"):
        _dijkstra(_graphe([(1, 2, -1, False)]), 1, 2)


def test_un_noeud_inaccessible_n_a_ni_chemin_ni_distance() -> None:
    g = _graphe([(1, 2, 1, False), (3, 2, 1, False)])
    assert _dijkstra(g, 1, 3) is None
    assert _bellman_ford(g, 1, 3) is None
    assert _distance(g, 1, 3) is None


# --- Structure ------------------------------------------------------------------------


@pytest.mark.parametrize("graine", range(10))
def test_tarjan_regroupe_les_noeuds_mutuellement_accessibles(graine: int) -> None:
    g = graphe_aleatoire(graine, arcs=12)
    accessibles = {a: set(_parcours_graphe(g, a, True)) for a in g._arcs}
    composantes = _tarjan(g)
    assert sorted(map(repr, chain.from_iterable(composantes))) == sorted(
        map(repr, g._arcs)
    )
    for composante in composantes:
        for a, b in product(composante, repeat=2):
            assert b in accessibles[a]
    representant = {n: i for i, c in enumerate(composantes) for n in c}
    for a, b in product(g._arcs, repeat=2):
        if b in accessibles[a] and a in accessibles[b]:
            assert representant[a] == representant[b]


@pytest.mark.parametrize("graine", range(10))
def test_le_tri_topologique_respecte_chaque_arc(graine: int) -> None:
    hasard = random.Random(graine)
    g = _Upea()
    for _ in range(15):  # un graphe sans cycle : les arcs vont vers les plus grands
        a = hasard.randrange(9)
        g.relier(a, hasard.randrange(a + 1, 10))
    ordre = _tri_topologique(g)
    assert ordre is not None
    rang = {n: i for i, n in enumerate(ordre)}
    assert all(rang[a] < rang[b] for a, b, _ in g.arcs())


def test_les_composantes_ignorent_le_sens_des_arcs() -> None:
    g = _graphe([(1, 2, 1, False), (3, 2, 1, False), (4, 5, 1, False)])
    assert _composantes(g) == [[1, 2, 3], [4, 5]]


# --- Arbres couvrants et flots --------------------------------------------------------


@pytest.mark.parametrize("graine", range(10))
def test_prim_et_kruskal_ont_le_meme_poids(graine: int) -> None:
    g = graphe_aleatoire(graine)
    k, p = _kruskal(g), _prim(g)
    assert poids_total(k) == poids_total(p)
    # Une forêt couvrante : autant de nœuds, une arête de moins par composante.
    aretes = len(k.arcs()) // 2
    assert aretes == len(k._arcs) - len(_composantes(k))
    # … et les nœuds et les composantes du graphe de départ (M3).
    for couvrant in (k, p):
        assert set(couvrant._arcs) == set(g._arcs)
        assert len(_composantes(couvrant)) == len(_composantes(g))


def test_kruskal_prend_le_poids_le_plus_petit_des_deux_sens() -> None:
    g = _graphe([("a", "b", 5, False), ("b", "a", 2, False)])
    assert _kruskal(g)._arcs == {"a": {"b": 2}, "b": {"a": 2}}


def test_le_flot_maximal_du_reseau_classique() -> None:
    # Le réseau de flot de Cormen et al. (Introduction to Algorithms) : flot 23.
    g = _graphe(
        [
            ("s", "v1", 16, False),
            ("s", "v2", 13, False),
            ("v1", "v3", 12, False),
            ("v2", "v1", 4, False),
            ("v2", "v4", 14, False),
            ("v3", "v2", 9, False),
            ("v3", "t", 20, False),
            ("v4", "v3", 7, False),
            ("v4", "t", 4, False),
        ]
    )
    assert _edmonds_karp(g, "s", "t") == 23
    assert _edmonds_karp(g, "s", "s") == 0
    assert _edmonds_karp(g, "t", "s") == 0


# --- Algorithmes d'arbres : les mêmes fonctions sur les six sortes --------------------

CLES = [4, 2, 6, 1, 3, 5, 7]
SORTES: dict[str, Callable[[], object]] = {
    "tumu": lambda: _tumu(
        4, _tumu(2, _tumu(1), _tumu(3)), _tumu(6, _tumu(5), _tumu(7))
    ),
    "imi": lambda: _Imi(CLES),
    "aifaito": lambda: _Aifaito(CLES),
    "uteere": lambda: _Uteere(CLES),
    "pupu": lambda: _Pupu(CLES, 3),
    "ahu": lambda: _Ahu(CLES),
}


@pytest.mark.parametrize("sorte", SORTES)
def test_chaque_algorithme_marche_sur_chaque_sorte(sorte: str) -> None:
    arbre = SORTES[sorte]()
    for parcours in (_prefixe, _infixe, _postfixe, _largeur):
        assert sorted(parcours(arbre)) == sorted(CLES)
    assert set(_rau(arbre)) <= set(CLES)
    assert 0 <= _teitei(arbre) <= 3
    assert _diametre(arbre) <= 2 * _teitei(arbre)
    assert _profondeur(arbre, _prefixe(arbre)[0]) == 0
    assert _profondeur(arbre, 99) is None
    assert _ancetre(arbre, 99, 1) is None


@pytest.mark.parametrize("sorte", ["tumu", "imi", "aifaito", "uteere", "pupu"])
def test_l_infixe_d_un_arbre_de_recherche_est_trie(sorte: str) -> None:
    assert _infixe(SORTES[sorte]()) == sorted(CLES)


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        (
            "tuu a = imi [4, 2, 6, 1, 3, 5, 7];\n"
            "faaite prefixe(a), postfixe(a), largeur(a);",
            "[4, 2, 1, 3, 6, 5, 7] [1, 3, 2, 5, 7, 6, 4] [4, 2, 6, 1, 3, 5, 7]",
        ),
        (
            "tuu a = imi [4, 2, 6, 1, 3];\nfaaite ancetre(a, 1, 3), ancetre(a, 1, 6), "
            "ancetre(a, 3, 2), diametre(a), equilibre(a);",
            "2 4 2 3 tia",
        ),
        ("faaite equilibre(imi [1, 2, 3]), equilibre(tumu(1, tumu(2)));", "hape tia"),
        # La racine de cet arbre B est [2 | 4] : un ancêtre à plusieurs clés.
        ("faaite ancetre(pupu [1, 2, 3, 4, 5], 4, 5);", "[2, 4]"),
        ("faaite ancetre(pupu 4 [1, 2, 3], 1, 2);", "[1, 2, 3]"),
        ("faaite ancetre(pupu [1, 2, 3, 4], 1, 2);", "2"),
        (
            "faaite teitei(ahu [1]), diametre(ahu [1]), rau(ahu [3, 1, 2]);",
            "0 0 [3, 2]",
        ),
    ],
)
def test_les_algorithmes_d_arbres_dans_un_programme(source: str, sortie: str) -> None:
    assert lancer(source) == sortie + "\n"


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        (
            'tuu g = upea { "a" -> "b" : 1, "b" -> "c" : -5, "a" -> "c" : 2 };\n'
            'faaite bellman_ford(g, "a", "c"), distance(g, "a", "c");',
            '["a", "b", "c"] -4',
        ),
        ("faaite tri_topologique(upea { 1 -> 2, 2 -> 1 });", "aore"),
        (
            "tuu g = upea { 1 -> 2, 1 -> 3, 2 -> 4 };\nfaaite bfs(g, 1), dfs(g, 1);",
            "[1, 2, 3, 4] [1, 2, 4, 3]",
        ),  # fmt: skip
        (
            "faaite prim(upea { 1 <-> 2 : 3 }), kruskal(upea {});",
            "upea { 1 <-> 2 : 3 } upea {}",
        ),
    ],
)
def test_les_algorithmes_de_graphes_dans_un_programme(source: str, sortie: str) -> None:
    assert lancer(source) == sortie + "\n"
    assert lancer(source, "ast") == sortie + "\n"


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        (
            "faaite dijkstra(upea { 1 -> 2 : -1 }, 1, 2);",
            "poids négatif : utilisez bellman_ford",
        ),
        (
            "faaite bellman_ford(upea { 1 -> 2 : -1, 2 -> 1 : -1 }, 1, 2);",
            "cycle de poids négatif",
        ),
        ("faaite tarjan([1]);", "tarjan : upea attendu, tapura reçu"),
        ("faaite bfs(upea { 1 -> 2 }, 9);", "le nœud 9 n'est pas dans le graphe"),
        (
            "faaite edmonds_karp(upea { 1 -> 2 : -3 }, 1, 2);",
            "capacité ne peut pas être négative",
        ),
        ("faaite hohoa(5);", "hohoa : arbre ou upea attendu, numera reçu"),
        ("faaite matrice(imi [1]);", "matrice : upea attendu, imi reçu"),
    ],
)
def test_les_erreurs_des_algorithmes(source: str, fragment: str) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)
    assert fragment in info.value.message
