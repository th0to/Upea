"""Conseil, lot M4 : `amui(g, v)` ajoute le nœud `v` au graphe `g` (sans effet s'il y
est déjà). Un graphe construit à partir d'une liste de nœuds et d'une liste d'arêtes
garde ses nœuds isolés."""

import pytest

from outils import lancer, une_erreur
from upea.erreurs import ErreurExecution, ErreurType

LISTE_DE_NOEUDS = """\
tuu noeuds = ["a", "b", "c", "d"];
tuu aretes = [["a", "b"]];
tuu g = upea {};
tataitahi n roto noeuds { amui(g, n); }
tataitahi a roto aretes { taati(g, a[0], a[1]); }
faaite roa(composantes(g)), composantes(g);
"""

#: La copie d'un graphe faite à la main (GRAPH-11) : avec `amui`, elle est fidèle.
COPIE = """\
ohipa copie(g) {
    tuu h = upea {};
    tataitahi n roto motu(g) { amui(h, n); }
    tataitahi n roto motu(g) {
        tataitahi m roto pihai(g, n) { taati(h, n, m, teiaha(g, n, m)); }
    }
    hoi h;
}
tuu g = upea { "a" -> "b" : 3, "c" };
faaite g == copie(g), motu(copie(g));
"""


def test_une_liste_de_noeuds_et_une_liste_d_aretes() -> None:
    assert lancer(LISTE_DE_NOEUDS) == '3 [["a", "b"], ["c"], ["d"]]\n'


def test_la_copie_d_un_graphe_est_fidele() -> None:
    assert lancer(COPIE) == 'tia ["a", "b", "c"]\n'


def test_un_noeud_deja_present_ne_change_rien() -> None:
    source = 'tuu g = upea { "A" -> "B" };\namui(g, "A");\nfaaite roa(g), parau(g);\n'
    assert lancer(source) == '2 upea { "A" -> "B" }\n'


def test_le_noeud_ajoute_vient_en_dernier() -> None:
    source = 'tuu g = upea { "A" -> "B" };\namui(g, "C");\nfaaite parau(g);\n'
    assert lancer(source) == 'upea { "A" -> "B", "C" }\n'


def test_le_type_du_noeud_est_verifie() -> None:
    erreur = une_erreur('tuu g = upea { "A" -> "B" };\namui(g, 1);\n')
    assert isinstance(erreur, ErreurType)
    assert erreur.message == "amui : élément parau attendu, numera reçu"


def test_une_liste_n_est_pas_un_noeud() -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer("tuu g = upea {};\namui(g, [1]);\n", types=False)
    assert info.value.message == (
        "un nœud de upea doit être un numera, un tuhaa ou un parau, pas un tapura"
    )


def test_amui_sur_autre_chose() -> None:
    erreur = une_erreur("amui(3, 1);")
    assert erreur.message == (
        "amui : tapura, upea ou arbre ordonné attendu, numera reçu"
    )
    with pytest.raises(ErreurExecution) as info:
        lancer("amui(3, 1);", types=False)
    assert info.value.message == (
        "amui : tapura, upea ou arbre ordonné attendu, numera reçu"
    )
