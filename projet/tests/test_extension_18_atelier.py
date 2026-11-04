"""Extension 18 : l'atelier, ce que le serveur MCP fait du compilateur (sans MCP)."""

import pytest

from upea.atelier import Diagnostic, diagnostics, formater, transpiler, verifier
from upea.erreurs import ErreurExecution, Position

# --- Les diagnostics ------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "attendu"),
    [
        (
            "tuu x = 3 @ 2;",
            Diagnostic("lexicale", 1, 11, "caractère inattendu : '@'"),
        ),
        ('faaite "Ia ora na;', Diagnostic("lexicale", 1, 8, "texte non terminé")),
        (
            "tuu x = 1\nfaaite x;",
            Diagnostic(
                "syntaxe", 1, 10, "';' attendu après la déclaration, trouvé 'faaite'"
            ),
        ),
        (
            "tuu a = 1; tuu b = 2; tuu c = 3;\nahani a < b < c { }",
            Diagnostic(
                "syntaxe",
                2,
                13,
                "les comparaisons ne s'enchaînent pas : écrivez par exemple "
                "a < b ma b < c",
            ),
        ),
        ("faaite y;", Diagnostic("semantique", 1, 8, "'y' n'est pas déclaré")),
        (
            'tuu x: numera = "a";',
            Diagnostic("type", 1, 17, "'x' est déclaré numera, mais reçoit parau"),
        ),
    ],
    ids=["lexicale", "texte", "syntaxe", "comparaisons", "semantique", "type"],
)
def test_chaque_sorte_d_erreur(source: str, attendu: Diagnostic) -> None:
    resultat = verifier(source)
    assert not resultat.valide
    assert resultat.diagnostics == (attendu,)


def test_toutes_les_erreurs_d_une_phase() -> None:
    resultat = verifier("faaite y;\nfaaite z;\n")
    assert [(d.sorte, d.ligne) for d in resultat.diagnostics] == [
        ("semantique", 1),
        ("semantique", 2),
    ]


def test_le_rapport_montre_la_ligne_et_le_chapeau() -> None:
    rapport = verifier("faaite y;").rapport
    assert rapport.splitlines() == [
        "programme.upea:1:8 : erreur sémantique : 'y' n'est pas déclaré",
        "    faaite y;",
        "           ^",
    ]


def test_un_avertissement_n_empeche_pas_d_etre_valide() -> None:
    resultat = verifier("tuu inutile = 1;")
    assert resultat.valide
    [avertissement] = resultat.diagnostics
    assert avertissement.sorte == "avertissement"
    assert avertissement.ligne == 1
    assert "inutile" in avertissement.message


def test_un_programme_juste() -> None:
    resultat = verifier('faaite "Ia ora na";')
    assert resultat.valide
    assert resultat.diagnostics == ()
    assert resultat.rapport == "aucune erreur"


def test_sans_types() -> None:
    assert verifier('tuu x: numera = "a"; faaite x;', types=False).valide


def test_une_position_inconnue_vaut_none() -> None:
    sans_colonne = ErreurExecution("indice hors limites", Position(3, 0))
    assert diagnostics(sans_colonne) == (
        Diagnostic("execution", 3, None, "indice hors limites"),
    )
    sans_position = ErreurExecution("division par zéro")
    assert diagnostics(sans_position) == (
        Diagnostic("execution", None, None, "division par zéro"),
    )


# --- Transpiler -----------------------------------------------------------------------

FIBONACCI = """\
ohipa fibo(n: numera) -> numera {
    ahani n < 2 { hoi n; }
    hoi fibo(n - 1) + fibo(n - 2);
}
faaite fibo(10);
"""


def test_transpiler_sans_le_prelude() -> None:
    resultat = transpiler(FIBONACCI)
    assert resultat.code is not None
    assert resultat.code.startswith("from upea_prelude import *\n")
    assert len(resultat.code.splitlines()) < 100
    assert "upea_prelude" in resultat.rapport


def test_transpiler_avec_le_prelude() -> None:
    resultat = transpiler(FIBONACCI, avec_prelude=True)
    assert resultat.code is not None
    assert "from upea_prelude" not in resultat.code
    assert len(resultat.code.splitlines()) > 1000


def test_transpiler_avec_le_backend_ast() -> None:
    resultat = transpiler(FIBONACCI, "ast")
    assert resultat.code is not None
    assert "def fibo(n" in resultat.code


def test_transpiler_un_programme_faux() -> None:
    resultat = transpiler("faaite y;")
    assert resultat.code is None
    assert [d.sorte for d in resultat.diagnostics] == ["semantique"]


# --- Formater -------------------------------------------------------------------------


def test_formater() -> None:
    resultat = formater("tuu   x=1 ;faaite x ;")
    assert resultat.code == "tuu x = 1;\nfaaite x;\n"
    assert resultat.diagnostics == ()
    assert formater(resultat.code).code == resultat.code


def test_formater_un_programme_faux() -> None:
    resultat = formater("tuu x = ;")
    assert resultat.code is None
    assert [d.sorte for d in resultat.diagnostics] == ["syntaxe"]
