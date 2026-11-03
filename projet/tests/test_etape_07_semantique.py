"""Étape 7 : l'analyse sémantique, les déclarations et les portées."""

from functools import singledispatchmethod
from pathlib import Path

import pytest

from outils import erreurs_de_compilation, lancer, lire, position, une_erreur
from upea.compilateur import compiler
from upea.erreurs import ErreurSemantique
from upea.parser import parse
from upea.semantique import Analyseur, analyser
from upea.symboles import Genre, Symbole, TableSymboles


def analyse(source: str) -> object:
    return compiler(source).analyse


def test_les_exemples_passent_l_analyse(exemple: Path) -> None:
    resultat = compiler(lire(exemple)).analyse
    assert resultat.avertissements == ()


def test_l_analyseur_utilise_singledispatchmethod() -> None:
    assert isinstance(Analyseur.__dict__["instruction"], singledispatchmethod)
    assert isinstance(Analyseur.__dict__["expression"], singledispatchmethod)


def test_une_portee_est_refermee_meme_si_une_exception_la_traverse() -> None:
    table = TableSymboles()
    with pytest.raises(RuntimeError), table.portee("bloc"):
        assert table.profondeur == 1
        raise RuntimeError
    assert table.profondeur == 0


def test_chercher_remonte_la_pile_des_portees() -> None:
    table = TableSymboles()
    table.declarer(Symbole("x", Genre.VARIABLE, parse("x;").pos))
    with table.portee():
        assert table.chercher("x") is not None
        assert table.chercher("y") is None


@pytest.mark.parametrize(
    ("source", "fragment", "ligne", "colonne"),
    [
        ("faaite y;", "'y' n'est pas déclaré", 1, 8),
        ("tuu x = 1;\ntuu x = 2;", "déjà déclaré dans ce bloc (ligne 1)", 2, 5),
        ("ahani tia { tuu x = 1; }\nfaaite x;", "'x' n'est pas déclaré", 2, 8),
        ("tuu x = x;", "'x' n'est pas déclaré", 1, 9),
        ("hoi 1;", "hoi hors d'une fonction", 1, 1),
        ("inconnue(1);", "'inconnue' n'est pas déclaré", 1, 1),
        ("f();\nohipa f() { }", "'f' n'est pas déclaré", 1, 1),
        ("ohipa f(a) { hoi a; }\nf(1, 2);", "'f' attend 1 argument, 2 donnés", 2, 1),
        ("faaite roa();", "'roa' attend 1 argument, 0 donné", 1, 8),
        ("faaite taati(1);", "'taati' attend 3 ou 4 arguments, 1 donné", 1, 8),
        ("faaite tumu();", "'tumu' attend au moins 1 argument", 1, 8),
        ("tuu roa = 3;", "'roa' est le nom d'une fonction prédéfinie", 1, 5),
        (
            "ohipa f() { }\ntuu f = 1;",
            "'f' est le nom d'une fonction déjà déclarée",
            2,
            5,
        ),
        (
            "ohipa f() { }\nohipa f() { }",
            "'f' est le nom d'une fonction déjà déclarée",
            2,
            7,
        ),
        ("mau pi = 3.14;\npi = 3;", "on ne peut pas affecter la constante 'pi'", 2, 1),
        (
            "tataitahi i roto 0..3 { i = 1; }",
            "on ne peut pas affecter la variable de boucle 'i'",
            1,
            25,
        ),
        ("ohipa f() { }\nf = 2;", "on ne peut pas affecter la fonction 'f'", 2, 1),
        ("faaea;", "faaea hors d'une boucle", 1, 1),
        ("haere;", "haere hors d'une boucle", 1, 1),
        ("ohipa f() { faaea; }", "faaea hors d'une boucle", 1, 13),
        ("ahani tia { ohipa f() { } }", "doit être déclarée au niveau global", 1, 19),
        ("tuu t = tumu(1);\nfaaite t.taille;", "champ inconnu 'taille'", 2, 10),
        ("ohipa f() { }\ntuu g = f;", "'f' est une fonction, pas une valeur", 2, 9),
        ("faaite roa;", "'roa' est une fonction, pas une valeur", 1, 8),
        ("tuu x = 1;\nx(2);", "'x' est une variable, pas une fonction", 2, 1),
        ("ohipa f(a, a) { }", "'a' est déjà déclaré dans ce bloc", 1, 12),
        ("tuu totale = 1;\nfaaite total;", "vouliez-vous dire 'totale'", 2, 8),
    ],
)
def test_chaque_regle_de_la_specification_est_verifiee(
    source: str, fragment: str, ligne: int, colonne: int
) -> None:
    erreur = une_erreur(source)
    assert isinstance(erreur, ErreurSemantique)
    assert fragment in erreur.message
    assert position(erreur) == (ligne, colonne)


@pytest.mark.parametrize(
    ("source", "fragment", "ligne", "colonne"),
    [
        (
            "tuu x = 1;\nahani tia { tuu x = 2; }",
            "masquerait la déclaration de la ligne 1",
            2,
            17,
        ),
        ("tuu i = 0;\ntataitahi i roto 0..3 { }", "masquerait", 2, 1),
        (
            "ohipa f(n) { ahani tia { tuu n = 2; } }",
            "masquerait",
            1,
            30,
        ),
        (
            "tuu n = 1;\nohipa f() { faaite n; tuu n = 2; }",
            "'n' désigne la variable globale plus haut dans la fonction (ligne 2)",
            2,
            27,
        ),
        (
            "tuu n = 1;\nohipa f() { ahani tia { tuu n = 2; } faaite n; }",
            "'n' désigne ici la variable globale, mais la fonction déclare aussi",
            2,
            45,
        ),
        (
            "tuu x = 1;\nohipa f() { x = 2; tuu x = 3; }",
            "'x' désigne la variable globale",
            2,
            24,
        ),
    ],
)
def test_ce_qui_changerait_de_sens_en_python_est_refuse(
    source: str, fragment: str, ligne: int, colonne: int
) -> None:
    erreur = une_erreur(source)
    assert fragment in erreur.message
    assert position(erreur) == (ligne, colonne)


def test_toutes_les_erreurs_sont_signalees_ensemble() -> None:
    source = "faaite a;\ntuu b = 1;\ntuu b = 2;\nfaaea;\nfaaite b;"
    erreurs = erreurs_de_compilation(source)
    assert [position(e) for e in erreurs] == [(1, 8), (3, 5), (4, 1)]


def test_deux_blocs_freres_peuvent_declarer_le_meme_nom() -> None:
    source = "ahani tia { tuu x = 1; faaite x; } taae { tuu x = 2; faaite x; }"
    assert lancer(source) == "1\n"


def test_une_fonction_recursive_est_acceptee() -> None:
    source = "ohipa f(n) { ahani n == 0 { hoi 0; } hoi n + f(n - 1); }\nfaaite f(4);"
    assert lancer(source) == "10\n"


def test_un_parametre_peut_porter_le_nom_d_une_globale() -> None:
    source = "tuu n = 1;\nohipa f(n) { hoi n * 10; }\nfaaite f(2), n;"
    assert lancer(source) == "20 1\n"


def test_une_locale_peut_porter_le_nom_d_une_globale_qu_elle_ne_lit_pas() -> None:
    source = "tuu x = 1;\nohipa f() { tuu x = 2; hoi x; }\nfaaite f(), x;"
    assert lancer(source) == "2 1\n"


def test_les_globales_modifiees_sont_notees_et_seulement_elles() -> None:
    source = """
    tuu appels = 0;
    tuu t = [1];
    tuu a = tumu(1);
    tuu lu = 5;
    ohipa f() { appels = appels + 1; t[0] = 2; a.hotu = 3; amui(t, lu); }
    ohipa g(appels) { appels = 1; }
    ohipa h() { tuu t = 0; t = 1; faaite t; }
    """
    modifiees = analyser(parse(source)).globales_modifiees
    assert modifiees == {
        "f": frozenset({"appels"}),
        "g": frozenset(),
        "h": frozenset(),
    }


def test_une_fonction_qui_modifie_une_globale_s_execute() -> None:
    source = "tuu n = 0;\nohipa f() { n = n + 1; }\nf();\nf();\nfaaite n;"
    assert lancer(source) == "2\n"


@pytest.mark.parametrize(
    ("source", "fragment", "ligne", "colonne"),
    [
        ("tuu x = 1;", "'x' est déclarée mais jamais utilisée", 1, 5),
        (
            "ohipa f() { hoi 1; faaite 2; }\nfaaite f();",
            "code jamais exécuté (après 'hoi')",
            1,
            20,
        ),
        (
            "tamau tia { faaea; faaite 1; }",
            "code jamais exécuté (après 'faaea')",
            1,
            20,
        ),
        ("1 + 2;", "expression sans effet", 1, 1),
    ],
)
def test_les_avertissements_n_empechent_pas_la_compilation(
    source: str, fragment: str, ligne: int, colonne: int
) -> None:
    (avertissement,) = compiler(source).analyse.avertissements
    assert fragment in avertissement.message
    assert position(avertissement) == (ligne, colonne)


def test_une_affectation_n_est_pas_une_utilisation() -> None:
    (avertissement,) = compiler("tuu x = 1;\nx = 2;").analyse.avertissements
    assert "jamais utilisée" in avertissement.message
