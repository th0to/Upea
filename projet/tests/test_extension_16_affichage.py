"""Extension 16 : l'affichage lisible des arbres et des graphes — dessins de haut en
bas et en retrait, liste et matrice d'adjacence, couleurs, export Graphviz et
Mermaid, et la forme compacte (sur une ligne) des graphes."""

import random
import re
import shutil
import subprocess
from collections.abc import Callable
from itertools import groupby
from typing import Any

import pytest

from outils import lancer, une_erreur
from upea.compilateur import mettre_en_forme, transpiler
from upea.erreurs import ErreurType
from upea.execution.algorithmes_arbres import _noeuds_largeur
from upea.execution.arbre_b import _pupu
from upea.execution.base import _dessin, _texte
from upea.execution.dessins import _LARGEUR_MAX, _hohoa, _matrice
from upea.execution.exports import _dot, _mermaid
from upea.execution.graphes import _graphe, _Upea
from upea.execution.recherche import _Aifaito, _Imi, _Uteere
from upea.execution.tas import _Ahu
from upea.execution.tumu import _tumu
from upea.execution.vues import _cles
from upea.noeuds import Arete, Entier, Graphe, Texte
from upea.parser import parse_expression

ANSI = re.compile(r"\x1b\[[0-9;]*m")

# --- Les dessins des arbres -----------------------------------------------------------


@pytest.mark.parametrize(
    ("arbre", "dessin"),
    [
        (
            _Aifaito(range(1, 8)),
            "      4\n  ┌───┴───┐\n  2       6\n┌─┴─┐   ┌─┴─┐\n1   3   5   7",
        ),
        (_Imi([5, 3]), "  5\n┌─┘\n3"),
        (_Imi([5, 8]), "5\n└─┐\n  8"),
        (_Imi(["b", "a", "c"]), "  b\n┌─┴─┐\na   c"),
        (_Imi(["a\nb"]), "a\\nb"),
        (_Uteere([1, 2]), "  2 (N)\n┌─┘\n1 (R)"),
        (_Ahu([5, 1, 4, 2, 8]), "     1\n  ┌──┴──┐\n  2     4\n┌─┴─┐\n5   8"),
        (_Ahu([1, 3], nui=True), "  3\n┌─┘\n1"),
    ],
)
def test_un_arbre_binaire_se_dessine_de_haut_en_bas(arbre: object, dessin: str) -> None:
    assert _hohoa(arbre) == dessin


@pytest.mark.parametrize(
    ("arbre", "dessin"),
    [
        (
            _tumu("a", _tumu("b"), _tumu("c", _tumu("d"))),
            "a\n├── b\n└── c\n    └── d",
        ),
        (_pupu([10, 20, 30, 40, 50]), "[20 | 40]\n├── [10]\n├── [30]\n└── [50]"),
        (_tumu(1), "1"),
    ],
)
def test_un_tumu_et_un_arbre_b_se_dessinent_en_retrait(
    arbre: object, dessin: str
) -> None:
    assert _hohoa(arbre) == dessin


def test_un_dessin_trop_large_passe_en_retrait() -> None:
    # Un peigne de n nœuds à deux chiffres fait 2n colonnes de large.
    etroit = _hohoa(_Imi(range(40)))
    assert etroit.startswith("0\n└─┐\n  1\n")
    assert max(map(len, etroit.splitlines())) == _LARGEUR_MAX
    large = _hohoa(_Imi(range(41)))
    assert large.startswith("0\n├── ·\n└── 1\n    ├── ·\n")


def test_un_arbre_vide_n_a_pas_de_dessin() -> None:
    for vide in (_Imi(), _Ahu(), _pupu([]), _Upea()):
        assert _dessin(vide) is None
        assert _hohoa(vide) == "(vide)"


FABRIQUES: dict[str, Callable[[list[int]], object]] = {
    "imi": _Imi,
    "aifaito": _Aifaito,
    "uteere": _Uteere,
    "ahu": _Ahu,
    "ahunui": lambda cles: _Ahu(cles, nui=True),
}


@pytest.mark.parametrize("sorte", FABRIQUES)
@pytest.mark.parametrize("graine", range(10))
def test_chaque_ligne_d_etiquettes_est_un_niveau_de_l_arbre(
    sorte: str, graine: int
) -> None:
    """Une ligne sur deux porte les clés d'un niveau, de gauche à droite : celles
    que donne le parcours en largeur ; les autres ne portent que des traits."""
    hasard = random.Random(graine)
    arbre = FABRIQUES[sorte](hasard.sample(range(100), hasard.randint(1, 14)))
    dessin = _dessin(arbre)
    assert dessin is not None
    lignes = dessin.splitlines()
    assert max(map(len, lignes)) <= _LARGEUR_MAX
    niveaux = [
        [cle for noeud, _ in groupe for cle in _cles(noeud)]
        for _, groupe in groupby(_noeuds_largeur(arbre), key=lambda paire: paire[1])
    ]
    assert len(lignes) == 2 * len(niveaux) - 1
    for ligne, niveau in zip(lignes[::2], niveaux, strict=True):
        assert [int(cle) for cle in re.findall(r"\d+", ligne)] == niveau
    for ligne in lignes[1::2]:
        assert set(ligne) <= set(" ─┌┐└┘┴")


# --- Les dessins des graphes ----------------------------------------------------------


def test_un_graphe_se_dessine_en_liste_d_adjacence() -> None:
    sortie = lancer('faaite upea { "A" -> "B" : 2, "A" -> "Bora Bora", "C" };')
    assert sortie == (
        "upea : 4 nœuds, 2 arcs\n"
        "A         → B (2), Bora Bora\n"
        "B         ·\n"
        "Bora Bora ·\n"
        "C         ·\n"
    )
    assert lancer("faaite upea { 1 };") == "upea : 1 nœud, 0 arc\n1 ·\n"


def test_la_matrice_d_adjacence() -> None:
    graphe = _graphe([("A", "B", 2, False), ("A", "Bora Bora", 1, False)])
    graphe.ajouter("C")
    assert _matrice(graphe) == (
        "          A B Bora Bora C\n"
        "A         · 2         1 ·\n"
        "B         · ·         · ·\n"
        "Bora Bora · ·         · ·\n"
        "C         · ·         · ·"
    )
    assert _matrice(_Upea()) == "(vide)"


# --- faaite : le dessin pour une structure seule --------------------------------------


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        ("faaite imi [2, 1];", "  2\n┌─┘\n1"),
        ('faaite "t :", imi [2, 1];', "t : imi [1, 2]"),
        ("faaite [imi [2, 1]];", "[imi [1, 2]]"),
        ("faaite parau(imi [2, 1]);", "imi [1, 2]"),
        ("faaite hohoa(imi [2, 1]) == parau(imi [2, 1]);", "hape"),
        ("faaite imi [];", "imi []"),
        ("faaite upea {};", "upea {}"),
        ('faaite tumu("a", tumu("b"));', "a\n└── b"),
        ("faaite upea { 1 -> 2 }, 3;", "upea { 1 -> 2 } 3"),
    ],
)
@pytest.mark.parametrize("backend", ["python", "ast"])
def test_faaite_dessine_une_structure_seule(
    source: str, sortie: str, backend: str
) -> None:
    assert lancer(source, backend) == sortie + "\n"


# --- Les couleurs ---------------------------------------------------------------------

COLORE = """
faaite uteere [1, 2];
faaite imi [3, 1, 5, 4];
faaite pupu [1, 2, 3];
faaite tumu("a", tumu("b"));
faaite upea { 1 -> 2 : 3, 4 };
"""


def test_les_couleurs_ne_changent_pas_la_mise_en_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    simple = lancer(COLORE)
    assert "\x1b[" not in simple  # une sortie redirigée n'a pas de couleurs
    monkeypatch.setenv("FORCE_COLOR", "1")
    colore = lancer(COLORE)
    assert "\x1b[31m1 (R)\x1b[0m" in colore
    assert "\x1b[33m(3)\x1b[0m" in colore
    assert ANSI.sub("", colore) == simple


def test_no_color_l_emporte_et_hohoa_n_a_jamais_de_couleurs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert "\x1b[" not in lancer("faaite hohoa(uteere [1, 2]);")
    monkeypatch.setenv("NO_COLOR", "1")
    assert "\x1b[" not in lancer(COLORE)


# --- L'export Graphviz et Mermaid -----------------------------------------------------


def test_dot_d_un_graphe() -> None:
    graphe = _graphe([(1, 2, 5, True), (2, 3, 1, False), ('x"y', None, None, False)])
    assert _dot(graphe) == (
        "digraph {\n"
        '  n0 [label="1"];\n'
        '  n1 [label="2"];\n'
        '  n2 [label="3"];\n'
        '  n3 [label="x\\"y"];\n'
        '  n0 -> n1 [label="5", dir=both];\n'
        "  n1 -> n2;\n"
        "}"
    )


def test_dot_d_un_arbre_garde_les_cotes_et_les_couleurs() -> None:
    assert _dot(_Uteere([1, 2])) == (
        "digraph {\n"
        "  ordering=out;\n"
        '  n0 [label="2"];\n'
        '  n1 [label="1", color=red, fontcolor=red];\n'
        '  n2 [label="", style=invis];\n'
        "  n0 -> n1;\n"
        "  n0 -> n2 [style=invis];\n"
        "}"
    )
    assert '[label="2 | 4", shape=box]' in _dot(_pupu([1, 2, 3, 4, 5]))


def test_mermaid_d_un_graphe_et_d_un_arbre() -> None:
    graphe = _graphe([("A", "B", 2, True), ("B", "C", 1, False)])
    assert _mermaid(graphe) == (
        'flowchart LR\n  n0["A"]\n  n1["B"]\n  n2["C"]\n  n0 <-->|2| n1\n  n1 --> n2'
    )
    assert _mermaid(_Uteere([1, 2])) == (
        "flowchart TD\n"
        '  n0["2"]\n'
        '  n1["1"]\n'
        '  n2[" "]\n'
        "  style n2 fill:none,stroke:none\n"
        "  n0 --> n1\n"
        "  n0 ~~~ n2\n"
        "  classDef rouge fill:#fdd,stroke:#c00,color:#c00\n"
        "  class n1 rouge"
    )
    assert '["a#quot;b"]' in _mermaid(_Imi(['a"b']))


def test_dot_et_mermaid_dans_un_programme() -> None:
    assert lancer("faaite dot(imi [1]);") == (
        'digraph {\n  ordering=out;\n  n0 [label="1"];\n}\n'
    )
    assert lancer("faaite mermaid(upea { 1 });") == 'flowchart LR\n  n0["1"]\n'
    erreur = une_erreur("faaite dot(5);")
    assert isinstance(erreur, ErreurType)
    assert "dot : arbre ou upea attendu, numera reçu" in erreur.message


@pytest.mark.skipif(shutil.which("dot") is None, reason="Graphviz n'est pas installé")
@pytest.mark.parametrize(
    "structure",
    [
        _Uteere(range(10)),
        _pupu(list(range(12))),
        _tumu('"a"', _tumu("b")),
        _graphe([("A", "B", 2.5, True), ("B", "A", -1, False)]),
    ],
)
def test_graphviz_accepte_le_texte_produit(structure: object) -> None:
    resultat = subprocess.run(
        ["dot", "-Tsvg"], input=_dot(structure), capture_output=True, text=True
    )
    assert resultat.returncode == 0, resultat.stderr


# --- La forme compacte des graphes ----------------------------------------------------


@pytest.mark.parametrize(
    ("graphe", "texte"),
    [
        (_graphe([(1, 2, 4, True)]), "upea { 1 <-> 2 : 4 }"),
        (_graphe([(1, 2, 1, False), (2, 1, 3, False)]), "upea { 1 -> 2, 2 -> 1 : 3 }"),
        (_graphe([(1, 1, 1, False)]), "upea { 1 -> 1 }"),
        (_graphe([("A", None, None, False), (1, 2, 1, False)]), 'upea { "A", 1 -> 2 }'),
    ],
)
def test_la_forme_compacte_regroupe_les_aller_retour(graphe: _Upea, texte: str) -> None:
    assert _texte(graphe) == texte


@pytest.mark.parametrize("graine", range(20))
def test_la_forme_compacte_d_un_graphe_se_relit(graine: int) -> None:
    hasard = random.Random(graine)
    graphe = _Upea()
    for _ in range(hasard.randint(0, 12)):
        a, b = hasard.randrange(6), hasard.randrange(6)
        poids = hasard.choice([1, 2, -1, 2.5])
        graphe.relier(a, b, poids)
        if hasard.random() < 0.4:
            graphe.relier(b, a, poids)
    for noeud in hasard.sample(range(8), 2):
        graphe.ajouter(noeud)
    if graphe._arcs and hasard.random() < 0.5:
        graphe.retirer_noeud(next(iter(graphe._arcs)))
    espace: dict[str, Any] = {}
    exec(transpiler(f"tuu g = {_texte(graphe)};").code, espace)
    # Le prélude exécuté a sa propre classe `_Upea` : on compare les arcs.
    assert espace["g"]._arcs == graphe._arcs


# --- Le nœud seul dans un littéral upea -----------------------------------------------


def test_un_litteral_upea_accepte_un_noeud_seul() -> None:
    assert parse_expression('upea { "A", 1 -> 2, }') == Graphe(
        (Arete(Texte("A"), None, False), Arete(Entier(1), Entier(2), False))
    )
    source = 'faaite upea { "A", "B" -> "C" };\n'
    assert mettre_en_forme(source) == source
    assert mettre_en_forme(mettre_en_forme(source)) == source
    for backend in ("python", "ast"):
        sortie = lancer("faaite parau(upea { 3, 1 -> 2 }), roa(upea { 3 });", backend)
        assert sortie == "upea { 3, 1 -> 2 } 1\n"


def test_un_noeud_seul_est_verifie_comme_les_autres() -> None:
    erreur = une_erreur("tuu g = upea { [1] };")
    assert isinstance(erreur, ErreurType)
    assert "un nœud de upea doit être un numera, un tuhaa ou un parau" in erreur.message


def test_tatara_laisse_des_noeuds_isoles_visibles() -> None:
    source = "tuu g = upea { 1 -> 2, 2 -> 3 };\ntatara(g, 2);\nfaaite g;"
    assert lancer(source) == "upea : 2 nœuds, 0 arc\n1 ·\n3 ·\n"
