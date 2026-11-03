"""Étape 5 : le parser des expressions (Pratt)."""

import pytest

from upea import parser as module_parser
from upea.erreurs import ErreurSyntaxe, Position
from upea.lexer import tokenize
from upea.noeuds import (
    Appel,
    Arete,
    Binaire,
    Booleen,
    Champ,
    Decimal,
    Entier,
    Expr,
    Graphe,
    Index,
    Liste,
    Rien,
    Texte,
    Unaire,
    Variable,
)
from upea.parser import (
    PRECEDENCE_BINAIRE,
    REGLES_INFIXE,
    REGLES_PREFIXE,
    Precedence,
    parse_expression,
)
from upea.tokens import TokenKind as T

a, b, c = Variable("a"), Variable("b"), Variable("c")


def bin(op: str, gauche: Expr, droite: Expr) -> Binaire:
    return Binaire(op, gauche, droite)


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("42", Entier(42)),
        ("3.25", Decimal(3.25)),
        ('"Ia ora na"', Texte("Ia ora na")),
        ("tia", Booleen(True)),
        ("hape", Booleen(False)),
        ("aore", Rien()),
        ("motu", Variable("motu")),
        ("[1, x]", Liste((Entier(1), Variable("x")))),
        ("[]", Liste(())),
        ("upea {}", Graphe(())),
        (
            'upea { "A" -> "B" : 3, 1 <-> 2, }',
            Graphe(
                (
                    Arete(Texte("A"), Texte("B"), False, Entier(3)),
                    Arete(Entier(1), Entier(2), True),
                )
            ),
        ),
    ],
)
def test_chaque_litteral_donne_le_bon_noeud(source: str, arbre: Expr) -> None:
    assert parse_expression(source) == arbre


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("1 + 2 * 3", bin("+", Entier(1), bin("*", Entier(2), Entier(3)))),
        ("1 * 2 + 3", bin("+", bin("*", Entier(1), Entier(2)), Entier(3))),
        ("a + b % c", bin("+", a, bin("%", b, c))),
        ("a ma b anei c", bin("anei", bin("ma", a, b), c)),
        ("a anei b ma c", bin("anei", a, bin("ma", b, c))),
        ("a < b ma b < c", bin("ma", bin("<", a, b), bin("<", b, c))),
        ("a + 1 == b", bin("==", bin("+", a, Entier(1)), b)),
        ("a roto b ma c", bin("ma", bin("roto", a, b), c)),
    ],
)
def test_les_priorites_sont_respectees(source: str, arbre: Expr) -> None:
    assert parse_expression(source) == arbre


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("1 - 2 - 3", bin("-", bin("-", Entier(1), Entier(2)), Entier(3))),
        ("8 / 4 / 2", bin("/", bin("/", Entier(8), Entier(4)), Entier(2))),
        ("a ma b ma c", bin("ma", bin("ma", a, b), c)),
    ],
)
def test_les_operateurs_binaires_sont_associatifs_a_gauche(
    source: str, arbre: Expr
) -> None:
    assert parse_expression(source) == arbre


def test_les_parentheses_changent_l_arbre() -> None:
    assert parse_expression("(1 + 2) * 3") == bin(
        "*", bin("+", Entier(1), Entier(2)), Entier(3)
    )
    assert parse_expression("1 - (2 - 3)") == bin(
        "-", Entier(1), bin("-", Entier(2), Entier(3))
    )


def test_une_comparaison_entre_parentheses_peut_etre_comparee() -> None:
    assert parse_expression("(a < b) == c") == bin("==", bin("<", a, b), c)


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("-a * b", bin("*", Unaire("-", a), b)),
        ("eiaha a == b", Unaire("eiaha", bin("==", a, b))),
        ("eiaha a ma b", bin("ma", Unaire("eiaha", a), b)),
        ("- -a", Unaire("-", Unaire("-", a))),
        ("-t.hotu", Unaire("-", Champ(Variable("t"), "hotu"))),
        ("a - -b", bin("-", a, Unaire("-", b))),
    ],
)
def test_les_operateurs_unaires_lient_comme_le_dit_la_specification(
    source: str, arbre: Expr
) -> None:
    assert parse_expression(source) == arbre


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("f()", Appel("f", ())),
        ("f(1, a)", Appel("f", (Entier(1), a))),
        ("f(x)[0]", Index(Appel("f", (Variable("x"),)), Entier(0))),
        ("t[i + 1]", Index(Variable("t"), bin("+", Variable("i"), Entier(1)))),
        ("m[0][1]", Index(Index(Variable("m"), Entier(0)), Entier(1))),
        (
            "t.amaa[0].hotu",
            Champ(Index(Champ(Variable("t"), "amaa"), Entier(0)), "hotu"),
        ),
        ("pihai(g, a)[0]", Index(Appel("pihai", (Variable("g"), a)), Entier(0))),
    ],
)
def test_appels_indices_et_champs_se_combinent(source: str, arbre: Expr) -> None:
    assert parse_expression(source) == arbre


def test_les_decorateurs_ont_rempli_les_tables() -> None:
    assert REGLES_PREFIXE[T.ENTIER] is module_parser._entier
    assert REGLES_PREFIXE[T.UPEA] is module_parser._graphe
    assert REGLES_INFIXE[T.PLUS][0] is Precedence.SOMME
    assert REGLES_INFIXE[T.PLUS][1] is REGLES_INFIXE[T.MOINS][1]
    assert REGLES_INFIXE[T.PAR_G] == (Precedence.APPEL, module_parser._appel)
    assert REGLES_INFIXE[T.ROTO][0] is Precedence.COMPARAISON
    assert T.PAR_G in REGLES_PREFIXE  # `(` a les deux rôles


def test_la_table_des_precedences_couvre_tous_les_operateurs_binaires() -> None:
    assert set(PRECEDENCE_BINAIRE) == {
        "anei", "ma", "==", "!=", "<", "<=", ">", ">=", "roto",
        "+", "-", "*", "/", "%",
    }  # fmt: skip


def test_une_regle_decoree_reste_appelable_directement() -> None:
    p = module_parser.Parser(iter(()))
    token = next(tokenize("7"))
    assert module_parser._entier(p, token) == Entier(7)


def test_chaque_noeud_porte_la_position_de_son_token() -> None:
    arbre = parse_expression("1 +\n  f(x)")
    assert isinstance(arbre, Binaire)
    assert arbre.pos == Position(1, 3)
    assert arbre.gauche.pos == Position(1, 1)
    assert arbre.droite.pos == Position(2, 3)


def test_un_champ_porte_la_position_de_son_nom() -> None:
    assert parse_expression("arbre.hotu").pos == Position(1, 7)


@pytest.mark.parametrize(
    ("source", "colonne", "fragment"),
    [
        ("1 +", 4, "expression attendue, trouvé la fin du programme"),
        ("(1 + 2", 7, "')' attendu pour fermer la parenthèse"),
        ("* 2", 1, "expression attendue, trouvé '*'"),
        ("1 2", 3, "fin de l'expression attendue"),
        ("f(1)(2)", 5, "seule une fonction nommée"),
        ("(1)(2)", 4, "seule une fonction nommée"),
        ("[1, 2", 6, "']' attendu pour fermer la liste"),
        ("t.", 3, "<identifiant> attendu après le point"),
        ("upea { 1 2 }", 10, "'->', '<->', ',' ou '}' attendu"),
        ("upea 1", 6, "'{' attendu après 'upea'"),
        ("a < b < c", 7, "les comparaisons ne s'enchaînent pas"),
        ("a == b != c", 8, "les comparaisons ne s'enchaînent pas"),
        ("x roto l roto m", 10, "les comparaisons ne s'enchaînent pas"),
    ],
)
def test_les_erreurs_de_syntaxe_sont_a_la_bonne_position(
    source: str, colonne: int, fragment: str
) -> None:
    with pytest.raises(ErreurSyntaxe) as info:
        parse_expression(source)
    assert info.value.position == Position(1, colonne)
    assert fragment in info.value.message
