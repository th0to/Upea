"""Extension 18 : l'atelier, ce que le serveur MCP fait du compilateur (sans MCP)."""

import json
from pathlib import Path

import pytest

from outils import LISTE_EXEMPLES, lire
from upea.atelier import (
    Diagnostic,
    Jeton,
    analyser_syntaxe,
    decouper,
    diagnostics,
    formater,
    noeud_json,
    transpiler,
    verifier,
)
from upea.erreurs import ErreurExecution, Position
from upea.noeuds import Texte, Variable

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


# --- Découper en tokens ---------------------------------------------------------------


def test_decouper_rend_chaque_token_et_sa_position() -> None:
    resultat = decouper('tuu x = 1;\nfaaite "é";')
    assert resultat.valide
    assert resultat.diagnostics == ()
    assert resultat.jetons == (
        Jeton("TUU", "tuu", 1, 1),
        Jeton("IDENT", "x", 1, 5),
        Jeton("EGAL", "=", 1, 7),
        Jeton("ENTIER", "1", 1, 9),
        Jeton("POINT_VIRGULE", ";", 1, 10),
        Jeton("FAAITE", "faaite", 2, 1),
        Jeton("TEXTE", "é", 2, 8),  # la valeur du texte, sans ses guillemets
        Jeton("POINT_VIRGULE", ";", 2, 11),
        Jeton("FIN", "", 2, 12),
    )


def test_decouper_garde_les_tokens_lus_avant_une_erreur_lexicale() -> None:
    resultat = decouper("tuu x = 3 @ 2;")
    assert not resultat.valide
    assert [j.sorte for j in resultat.jetons] == ["TUU", "IDENT", "EGAL", "ENTIER"]
    assert resultat.diagnostics == (
        Diagnostic("lexicale", 1, 11, "caractère inattendu : '@'"),
    )
    assert "programme.upea:1:11" in resultat.rapport


# --- L'arbre syntaxique en JSON -------------------------------------------------------


def test_noeud_json_garde_le_type_les_champs_et_la_position() -> None:
    resultat = analyser_syntaxe("faaite 1 + x;")
    assert resultat.arbre == {
        "type": "Programme",
        "instructions": [
            {
                "type": "Affiche",
                "valeurs": [
                    {
                        "type": "Binaire",
                        "op": "+",
                        "gauche": {
                            "type": "Entier",
                            "valeur": 1,
                            "ligne": 1,
                            "colonne": 8,
                        },
                        "droite": {
                            "type": "Variable",
                            "nom": "x",
                            "ligne": 1,
                            "colonne": 12,
                        },
                        "ligne": 1,
                        "colonne": 10,
                    }
                ],
                "ligne": 1,
                "colonne": 1,
            }
        ],
    }


def test_noeud_json_distingue_deux_noeuds_de_meme_forme() -> None:
    assert noeud_json(Variable("x")) == {"type": "Variable", "nom": "x"}
    assert noeud_json(Texte("x")) == {"type": "Texte", "valeur": "x"}


@pytest.mark.parametrize("exemple", LISTE_EXEMPLES, ids=lambda p: p.stem)
def test_l_arbre_de_chaque_exemple_s_ecrit_en_json(exemple: Path) -> None:
    resultat = analyser_syntaxe(lire(exemple))
    assert resultat.valide
    assert json.loads(json.dumps(resultat.arbre)) == resultat.arbre


@pytest.mark.parametrize("valeur", [object(), {1, 2}, [Variable("x")]])
def test_noeud_json_refuse_une_valeur_inattendue(valeur: object) -> None:
    with pytest.raises(TypeError, match="inattendue"):
        noeud_json(valeur)


# --- L'analyse syntaxique seule -------------------------------------------------------


def test_analyser_syntaxe_rend_toutes_les_erreurs_de_syntaxe() -> None:
    resultat = analyser_syntaxe("tuu = 1;\nfaaite (2;\n")
    assert not resultat.valide
    assert resultat.arbre is None
    assert [(d.sorte, d.ligne, d.colonne) for d in resultat.diagnostics] == [
        ("syntaxe", 1, 5),
        ("syntaxe", 2, 10),
    ]


def test_analyser_syntaxe_ne_fait_pas_l_analyse_semantique() -> None:
    assert analyser_syntaxe("faaite y;").valide
    assert not verifier("faaite y;").valide


def test_analyser_syntaxe_signale_une_erreur_lexicale() -> None:
    resultat = analyser_syntaxe("faaite 1 @ 2;")
    assert [d.sorte for d in resultat.diagnostics] == ["lexicale"]
