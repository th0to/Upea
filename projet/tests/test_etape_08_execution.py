"""Étape 8 (suite) : ce que fait le prélude à l'exécution — parcours d'arbres et de
graphes, fonctions prédéfinies, et erreurs d'exécution traduites."""

import importlib
import re

import pytest

from outils import lancer
from upea.erreurs import ErreurExecution
from upea.execution.algorithmes_arbres import _teitei
from upea.execution.algorithmes_graphes import _ea
from upea.execution.graphes import _graphe
from upea.execution.predefinies import _roa
from upea.execution.tumu import _tumu
from upea.noeuds import SorteCollection
from upea.predefinies import PREDEFINIES
from upea.prelude import MODULES, PRELUDE


def espace_du_prelude() -> dict[str, object]:
    espace: dict[str, object] = {}
    exec(compile(PRELUDE, "<prelude>", "exec"), espace)
    return espace


@pytest.mark.parametrize("module", MODULES)
def test_tous_les_noms_du_prelude_commencent_par_un_souligne(module: str) -> None:
    noms = vars(importlib.import_module(f"upea.execution.{module}"))
    publics = {n for n in noms if not n.startswith("_")}
    assert publics == {"annotations"}


def test_le_prelude_concatene_est_autonome() -> None:
    assert not re.search(r"^from \.", PRELUDE, re.MULTILINE)
    assert PRELUDE.count("from __future__ import annotations") == 1
    noms = {n for n in espace_du_prelude() if not n.startswith("__")}
    assert {n for n in noms if not n.startswith("_")} == {"annotations"}


def test_chaque_predefinie_existe_dans_le_prelude() -> None:
    espace = espace_du_prelude()
    assert [n for n in PREDEFINIES if f"_{n}" not in espace] == []


def test_chaque_litteral_d_arbre_a_son_constructeur() -> None:
    espace = espace_du_prelude()
    sortes = SorteCollection.__value__.__args__
    assert [s for s in sortes if not callable(espace.get(f"_{s}"))] == []


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        # Arbres
        (
            "tuu t = tumu(1, tumu(2, tumu(4)), tumu(3, tumu(5), tumu(6)));\n"
            "tuu p = [];\ntataitahi n roto t { amui(p, n.hotu); }\n"
            "tuu l = [];\ntataitahi n roto t aano { amui(l, n.hotu); }\nfaaite p, l;",
            "[1, 2, 4, 3, 5, 6] [1, 2, 3, 4, 5, 6]",
        ),
        (
            "tuu f = tumu(7);\nfaaite teitei(f), rau(f), roa(f), 7 roto f;",
            "0 [7] 1 tia",
        ),
        (
            "faaite tumu(1, tumu(2)) == tumu(1, tumu(2)), tumu(1) == tumu(2);",
            "tia hape",
        ),
        # Graphes
        (
            "tuu g = upea { 3 -> 1, 1 -> 2 };\ntuu l = [];\n"
            "tataitahi m roto g { amui(l, m); }\nfaaite l;",
            "[3, 1, 2]",
        ),
        (
            'tuu g = upea { "A" -> "B" : 10, "A" -> "C" : 1, "C" -> "B" : 1 };\n'
            'faaite ea(g, "A", "B"), ea(g, "A", "A"), tae(g, "B", "B");',
            '["A", "C", "B"] ["A"] tia',
        ),
        (
            "faaite upea { 1 -> 2, 3 -> 4 } == upea { 3 -> 4, 1 -> 2 }, "
            "upea { 1 -> 2 } == upea { 1 -> 2 : 3 };",
            "tia hape",
        ),
        (
            "tuu g = upea { 1 -> 2 };\ntaati(g, 1, 2, 7);\ntaati(g, 2, 3);\n"
            "faaite teiaha(g, 1, 2), motu(g), pihai(g, 2), g;",
            "7 [1, 2, 3] [3] upea { 1 -> 2 : 7, 2 -> 3 }",
        ),
        ("faaite 2 roto upea { 1 -> 2 }, 3 roto upea { 1 -> 2 };", "tia hape"),
        # Listes et textes
        (
            "tuu l = [1, 2];\ntataitahi x roto l { amui(l, x); }\nfaaite l;",
            "[1, 2, 1, 2]",
        ),
        (
            'tuu l = [];\ntataitahi c roto "abc" { amui(l, c); }\nfaaite l;',
            '["a", "b", "c"]',
        ),
        ("tuu l = [];\nfaaite amui(l, 1), l;", "aore [1]"),
        # Conversions
        (
            'faaite numera("  -12 "), numera(3.9), numera(-3.9), numera(tia);',
            "-12 3 -3 1",
        ),
        ('faaite tuhaa("2.5"), tuhaa(3), parau(1.0), parau(aore);', "2.5 3.0 1.0 aore"),
    ],
)
def test_le_prelude_fait_ce_que_dit_la_specification(source: str, sortie: str) -> None:
    assert lancer(source) == sortie + "\n"


@pytest.mark.parametrize(
    ("source", "fragment", "ligne"),
    [
        ("faaite 1;\nfaaite 1 / 0;", "division par zéro", 2),
        ("faaite 5 % 0;", "division par zéro", 1),
        ("faaite [1, 2][5];", "indice hors limites", 1),
        (
            'faaite numera("abc");',
            'conversion impossible : "abc" n\'est pas un numera',
            1,
        ),
        ('faaite tuhaa("1,5");', "n'est pas un tuhaa", 1),
        ('faaite "a" + 1;', "opération '+' impossible entre parau et numera", 1),
        ('faaite 1 + "a";', "opération '+' impossible entre numera et parau", 1),
        ('faaite [1] + "a";', "opération '+' impossible entre tapura et parau", 1),
        ('faaite 1 < "a";', "comparaison '<' impossible entre numera et parau", 1),
        ('faaite -"a";', "opérande de '-' invalide : parau", 1),
        (
            'tuu g = upea { "A" -> "B" };\nfaaite pihai(g, "X");',
            'le nœud "X" n\'est pas dans le graphe',
            2,
        ),
        (
            'tuu g = upea { "A" -> "B" };\nfaaite teiaha(g, "B", "A");',
            'pas d\'arc de "B" vers "A"',
            2,
        ),
        (
            'faaite ea(upea { "A" -> "B" : -1 }, "A", "B");',
            "poids négatif : utilisez bellman_ford",
            1,
        ),
        ("faaite upea { [1] -> 2 };", "un nœud de upea doit être", 1),
        ("tataitahi x roto 5 { }", "on ne peut pas parcourir un numera", 1),
        ("tataitahi x roto [1] mai 1 { }", "'mai' ne s'emploie qu'avec un upea", 1),
        ("tataitahi x roto [1] aano { }", "'aano' ne s'emploie qu'avec un tumu", 1),
        ("tataitahi x roto upea { 1 -> 2 } aano { }", "demande un point de départ", 1),
        ("tataitahi x roto upea { 1 -> 2 } mai 3 { }", "le nœud 3 n'est pas", 1),
        ("tataitahi i roto 0..2.5 { }", "bornes d'un intervalle", 1),
        ("tuu x = 3;\nfaaite x.hotu;", "seul un tumu a les champs hotu et amaa", 2),
        ('tuu t = "abc";\nt[0] = "x";', "un parau ne se modifie pas", 2),
        (
            'tuu l = [1];\nfaaite l["a"];',
            "un indice doit être un numera, pas un parau",
            2,
        ),
        ("faaite 1 roto 5;", "roto : on ne peut pas chercher dans un numera", 1),
        ('faaite 1 roto "abc";', "roto : on ne cherche qu'un parau", 1),
        ("faaite tumu(1, 2);", "les enfants doivent être des tumu", 1),
        ("tuu t = tumu(1);\nt.amaa = 3;\nfaaite roa(t);", "forment une tapura", 3),
        (
            "faaite amui(3, 1);",
            "amui : tapura ou arbre ordonné attendu, numera reçu",
            1,
        ),
        ("faaite teitei([1]);", "teitei : arbre attendu, tapura reçu", 1),
        ("ohipa f(n) { hoi f(n + 1); }\nfaaite f(1);", "récursion trop profonde", 1),
    ],
)
def test_une_erreur_d_execution_est_traduite_et_situee(
    source: str, fragment: str, ligne: int
) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)  # sans types : l'erreur arrive à l'exécution
    assert fragment in info.value.message
    assert info.value.position is not None
    assert info.value.position.ligne == ligne
    assert isinstance(info.value.__cause__, Exception)


def test_une_valeur_non_hachable_n_est_jamais_un_noeud() -> None:
    assert lancer("faaite [1] roto upea { 1 -> 2 };", types=False) == "hape\n"


def test_la_sortie_produite_avant_l_erreur_est_conservee(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from upea.compilateur import executer

    with pytest.raises(ErreurExecution):
        executer("faaite 1;\nfaaite 1 / 0;")
    assert capsys.readouterr().out == "1\n"


def test_dijkstra_departage_les_egalites_dans_l_ordre_d_ajout() -> None:
    graphe = _graphe(
        [
            ("A", "B", 1, False),
            ("A", "C", 1, False),
            ("B", "D", 1, False),
            ("C", "D", 1, False),
        ]
    )
    assert _ea(graphe, "A", "D") == ["A", "B", "D"]


def test_le_parcours_d_un_arbre_profond_ne_sature_pas_la_pile() -> None:
    arbre = _tumu(0)
    for i in range(1, 5000):
        arbre = _tumu(i, arbre)
    assert _teitei(arbre) == 4999
    assert _roa(arbre) == 5000
