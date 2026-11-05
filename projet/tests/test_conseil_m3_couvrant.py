"""Conseil, lot M3 : `kruskal` et `prim` gardent les nœuds isolés. Une forêt couvrante
couvre tous les nœuds du graphe."""

import pytest

from outils import EXEMPLES, lancer, lire

GRAPHE = 'tuu g = upea { "A" <-> "B" : 2, "B" <-> "C" : 1, "D", "E" -> "E" };\n'


@pytest.mark.parametrize(
    ("fonction", "compacte"),
    [
        ("kruskal", 'upea { "B" <-> "C", "B" <-> "A" : 2, "D", "E" }'),
        ("prim", 'upea { "A" <-> "B" : 2, "B" <-> "C", "D", "E" }'),
    ],
)
def test_la_foret_couvre_tous_les_noeuds(fonction: str, compacte: str) -> None:
    sortie = lancer(
        GRAPHE
        + f"tuu f = {fonction}(g);\n"
        + "faaite roa(f), parau(f);\n"
        + "faaite composantes(f), composantes(g);\n"
    )
    assert sortie == (
        f"5 {compacte}\n"
        '[["B", "C", "A"], ["D"], ["E"]] [["A", "B", "C"], ["D"], ["E"]]\n'
        if fonction == "kruskal"
        else f"5 {compacte}\n"
        '[["A", "B", "C"], ["D"], ["E"]] [["A", "B", "C"], ["D"], ["E"]]\n'
    )


def test_un_graphe_sans_arc() -> None:
    assert lancer('faaite parau(kruskal(upea { "X", "Y" }));') == 'upea { "X", "Y" }\n'


def test_un_graphe_connexe_ne_change_pas() -> None:
    """L'exemple 08 (Kruskal et Prim sur les îles) garde sa sortie exacte."""
    exemple = EXEMPLES / "08_algorithmes_graphes.upea"
    assert lancer(lire(exemple)) == lire(exemple.with_suffix(".attendu"))
