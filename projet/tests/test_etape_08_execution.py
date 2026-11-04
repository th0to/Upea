"""Étape 8 (suite) : ce que fait le prélude à l'exécution — parcours d'arbres et de
graphes, fonctions prédéfinies, et erreurs d'exécution traduites."""

import importlib
import re
import time

import pytest

from outils import lancer
from upea.compilateur import TRADUCTIONS
from upea.erreurs import ErreurExecution
from upea.execution.algorithmes_arbres import _teitei
from upea.execution.algorithmes_graphes import _ea
from upea.execution.base import _texte
from upea.execution.graphes import _graphe
from upea.execution.predefinies import _roa
from upea.execution.tumu import _Tumu, _tumu
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
        # 1 == 1.0 : c'est le même nœud, écrit comme à sa première apparition.
        (
            "tuu g = upea {};\ntaati(g, 1, 2);\ntaati(g, 1.0, 3);\n"
            "faaite roa(g), motu(g), pihai(g, 1), 1.0 roto g;",
            "3 [1, 2, 3] [2, 3] tia",
        ),
        (
            "tuu h = upea { 1.0 -> 2, 1 -> 3 };\nfaaite motu(h), h;",
            "[1.0, 2, 3] upea { 1.0 -> 2, 1.0 -> 3 }",
        ),
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
        ("faaite 1 roto 2.5;", "roto : on ne peut pas chercher dans un tuhaa", 1),
        ("faaite 1 roto tia;", "roto : on ne peut pas chercher dans un tiahape", 1),
        ("faaite 1 roto aore;", "roto : on ne peut pas chercher dans un aore", 1),
        ('faaite 1 roto "abc";', "roto : on ne cherche qu'un parau", 1),
        ("faaite tumu(1, 2);", "les enfants doivent être des tumu", 1),
        ("tuu t = tumu(1);\nt.amaa = 3;\nfaaite roa(t);", "forment une tapura", 2),
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
    assert "opération impossible sur ces valeurs" not in info.value.message
    assert info.value.position is not None
    assert info.value.position.ligne == ligne
    assert isinstance(info.value.__cause__, Exception)


@pytest.mark.parametrize("source", ["faaite 1 roto 5;", 'faaite 1 roto "abc";'])
def test_roto_verifie_lui_meme_ses_operandes(source: str) -> None:
    """`roto` ne dépend pas du texte des `TypeError` de Python, qui change d'une
    version à l'autre : c'est le prélude qui lève l'erreur, déjà rédigée."""
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)
    assert type(info.value.__cause__).__name__ == "_Erreur"


#: Pour chaque motif de `TRADUCTIONS`, dans l'ordre, un programme qui le déclenche.
CANARIS = [
    'faaite 1 + "a";',
    'faaite "a" + 1;',
    'faaite 1 < "a";',
    'faaite -"a";',
    'tuu t = "abc";\nt[0] = "x";',
    'tuu l = [1];\nfaaite l["a"];',
    "tuu x = 5;\nfaaite x[0];",
    "tataitahi i roto 0..2.5 { }",
]


@pytest.mark.parametrize(
    ("motif", "source"),
    list(zip([m for m, _ in TRADUCTIONS], CANARIS, strict=True)),
)
def test_chaque_traduction_reconnait_encore_le_message_de_python(
    motif: re.Pattern[str], source: str
) -> None:
    """Si une version de Python change le texte d'une `TypeError`, ce test dit
    laquelle des traductions ne la reconnaît plus."""
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)
    assert motif.search(str(info.value.__cause__)), str(info.value.__cause__)


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


# --- Un tumu reste un arbre -----------------------------------------------------------


@pytest.mark.parametrize("types", [True, False])
@pytest.mark.parametrize(
    ("source", "ligne"),
    [
        ("tuu t = tumu(1);\namui(t.amaa, t);", 2),
        ("tuu a = tumu(1);\ntuu b = tumu(2, a);\namui(a.amaa, b);", 3),
        ("tuu a = tumu(1, tumu(2));\ntuu b = tumu(3, a);\na.amaa[0] = b;", 3),
        ("tuu a = tumu(1);\na.amaa = [tumu(2, a)];", 2),
    ],
)
def test_un_tumu_ne_devient_pas_sa_propre_branche(
    source: str, ligne: int, types: bool
) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=types)
    assert "un tumu ne peut pas devenir sa propre branche" in info.value.message
    assert info.value.position is not None
    assert info.value.position.ligne == ligne


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("tuu t = tumu(1);\namui(t.amaa, 5);", "doivent être des tumu, pas un numera"),
        ("tuu t = tumu(1);\nt.amaa = 5;", "forment une tapura, pas un numera"),
        ("tuu t = tumu(1);\nt.amaa = [tumu(2), 3];", "doivent être des tumu"),
    ],
)
def test_une_branche_invalide_est_refusee_la_ou_elle_est_ajoutee(
    source: str, fragment: str
) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(source + '\nfaaite "trop tard";', types=False)
    assert fragment in info.value.message
    assert info.value.position is not None
    assert info.value.position.ligne == 2


def test_un_sous_arbre_peut_etre_partage() -> None:
    source = (
        "tuu f = tumu(3);\ntuu t = tumu(1, f, f);\namui(t.amaa, f);\nfaaite roa(t), t;"
    )
    assert lancer(source) == "4 tumu(1, tumu(3), tumu(3), tumu(3))\n"


def test_affecter_amaa_recopie_la_liste() -> None:
    source = (
        "tuu l = [tumu(2)];\ntuu t = tumu(1);\nt.amaa = l;\n"
        "amui(l, tumu(3));\nfaaite roa(t), roa(l), t.amaa == l;"
    )
    assert lancer(source) == "2 2 hape\n"


def test_amaa_reste_une_tapura() -> None:
    source = "tuu t = tumu(1, tumu(2));\nfaaite t.amaa, parau(t.amaa), roa(t.amaa);"
    assert lancer(source) == "[tumu(2)] [tumu(2)] 1\n"
    with pytest.raises(ErreurExecution) as info:
        lancer("tuu t = tumu(1);\nfaaite t.amaa < 1;", types=False)
    assert "comparaison '<' impossible entre tapura et numera" in info.value.message


@pytest.mark.parametrize(
    "source",
    [
        "tuu l = [];\namui(l, l);\nfaaite l;",
        "tuu l = [1];\ntuu m = [l];\namui(l, m);\nfaaite parau(m);",
        "tuu t = tumu(1);\nt.hotu = t;\nfaaite parau(t);",
    ],
)
def test_une_valeur_qui_se_contient_ne_s_affiche_pas(source: str) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)
    assert "se contient elle-même" in info.value.message


def test_une_valeur_partagee_s_affiche_normalement() -> None:
    assert lancer("tuu l = [1];\nfaaite [l, l], [[l], l];") == (
        "[[1], [1]] [[[1]], [1]]\n"
    )


#: Un tumu de 3 000 nœuds, construit par `amui` en partant de la racine (on accroche
#: une feuille au dernier nœud) ou des feuilles (on accroche l'arbre à une racine).
CONSTRUCTIONS = {
    "depuis la racine": (
        "tuu racine = tumu(0);\ntuu bout = racine;\n"
        "tataitahi i roto 1..3000 { tuu f = tumu(i); amui(bout.amaa, f); bout = f; }\n"
        "faaite roa(racine);"
    ),
    "depuis les feuilles": (
        "tuu t = tumu(0);\n"
        "tataitahi i roto 1..3000 { tuu r = tumu(i); amui(r.amaa, t); t = r; }\n"
        "faaite roa(t);"
    ),
}


@pytest.mark.parametrize("construction", CONSTRUCTIONS)
def test_construire_un_grand_tumu_par_amui_reste_rapide(construction: str) -> None:
    debut = time.perf_counter()
    assert lancer(CONSTRUCTIONS[construction]) == "3000\n"
    assert time.perf_counter() - debut < 1.0


def chaine(profondeur: int) -> _Tumu:
    """`tumu(n - 1, tumu(n - 2, … tumu(0)))` : un arbre profond de `n` nœuds."""
    arbre = _tumu(0)
    for i in range(1, profondeur):
        arbre = _tumu(i, arbre)
    return arbre


def test_comparer_et_ecrire_un_arbre_profond_ne_sature_pas_la_pile() -> None:
    assert chaine(5000) == chaine(5000)
    assert chaine(5000) != chaine(4999)
    attendu = "".join(f"tumu({i}, " for i in range(4999, 0, -1)) + "tumu(0" + ")" * 5000
    assert _texte(chaine(5000)) == attendu


def test_un_arbre_profond_se_compare_et_s_ecrit_dans_un_programme() -> None:
    source = (
        "tuu t = tumu(0);\ntuu u = tumu(0);\n"
        "tataitahi i roto 1..3000 { t = tumu(i, t); u = tumu(i, u); }\n"
        "faaite t == u, roa(parau(t)) > 3000;"
    )
    assert lancer(source) == "tia tia\n"


def test_l_ordre_des_enfants_et_les_valeurs_comptent_toujours() -> None:
    assert _tumu(1, _tumu(2), _tumu(3)) != _tumu(1, _tumu(3), _tumu(2))
    assert _tumu(1, _tumu(2)) != _tumu(1, _tumu(2), _tumu(2))
    assert _tumu([1, _tumu(2)]) == _tumu([1, _tumu(2)])
    assert _texte(_tumu("a", _tumu(2), _tumu(3, _tumu(4)))) == (
        'tumu("a", tumu(2), tumu(3, tumu(4)))'
    )


def test_le_parcours_d_un_arbre_profond_ne_sature_pas_la_pile() -> None:
    arbre = _tumu(0)
    for i in range(1, 5000):
        arbre = _tumu(i, arbre)
    assert _teitei(arbre) == 4999
    assert _roa(arbre) == 5000
