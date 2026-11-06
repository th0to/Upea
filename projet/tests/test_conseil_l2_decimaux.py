"""Conseil, lot L2 : les décimaux s'écrivent aussi avec un exposant (`1e-05`), ce qui
rend relisible la forme compacte des très grands et très petits décimaux ; un
littéral infini est refusé, et un infini ou un NaN ne peut être ni un nœud, ni un
poids, ni une clé."""

import pytest

from outils import lancer, une_erreur
from upea.compilateur import mettre_en_forme
from upea.erreurs import (
    ErreurExecution,
    ErreurLexicale,
    ErreursMultiples,
    ErreurSyntaxe,
)
from upea.lexer import tokenize
from upea.tokens import TokenKind as T


def jetons(source: str) -> list[tuple[T, str]]:
    return [(t.kind, t.lexeme) for t in tokenize(source)][:-1]


# --- Le lexer -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "attendu"),
    [
        ("1..5", [(T.ENTIER, "1"), (T.POINT_POINT, ".."), (T.ENTIER, "5")]),
        ("1..=5", [(T.ENTIER, "1"), (T.POINT_POINT_EGAL, "..="), (T.ENTIER, "5")]),
        ("t.hotu", [(T.IDENT, "t"), (T.POINT, "."), (T.IDENT, "hotu")]),
        ("0..e5", [(T.ENTIER, "0"), (T.POINT_POINT, ".."), (T.IDENT, "e5")]),
        ("x.e5", [(T.IDENT, "x"), (T.POINT, "."), (T.IDENT, "e5")]),
    ],
)
def test_ce_qui_etait_valide_ne_change_pas(source: str, attendu: list[object]) -> None:
    assert jetons(source) == attendu


@pytest.mark.parametrize("source", ["1e5", "1.5e-07", "1e+16", "2E3", "5e-324"])
def test_un_exposant_fait_un_decimal(source: str) -> None:
    assert jetons(source) == [(T.DECIMAL, source)]


@pytest.mark.parametrize(
    ("source", "cite"),
    [("1e", "1e"), ("1e+", "1e"), ("1ex", "1ex"), ("1e5x", "1e5x"), ("1.5e", "1.5e")],
)
def test_un_exposant_incomplet_est_refuse(source: str, cite: str) -> None:
    with pytest.raises(ErreurLexicale) as info:
        jetons(source)
    assert info.value.message == f"nombre mal formé : {cite!r}"


def test_un_point_sans_chiffre_reste_refuse() -> None:
    with pytest.raises(ErreurLexicale) as info:
        jetons("1.e5")
    assert "décimal incomplet" in info.value.message


# --- Relire la forme compacte -------------------------------------------------------


def test_la_forme_compacte_se_relit() -> None:
    sortie = lancer("faaite parau([10000000000000000.0, 0.00001, 1.5e-07]);")
    assert sortie == "[1e+16, 1e-05, 1.5e-07]\n"
    relu = lancer(f"faaite {sortie.strip()} == [1e16, 0.00001, 0.00000015];")
    assert relu == "tia\n"
    graphe = lancer("faaite parau(upea { 0.00001 -> 1 });").strip()
    assert graphe == "upea { 1e-05 -> 1 }"
    assert lancer(f"faaite {graphe} == upea {{ 0.00001 -> 1 }};") == "tia\n"


def test_les_deux_backends_lisent_l_exposant() -> None:
    source = "faaite 1e16, 1.5e-07 * 2, 2E3;"
    assert lancer(source) == lancer(source, "ast") == "1e+16 3e-07 2000.0\n"


def test_un_tres_petit_decimal_vaut_zero() -> None:
    assert lancer("faaite 1e-400;") == "0.0\n"


# --- Les non-finis ------------------------------------------------------------------


@pytest.mark.parametrize("litteral", ["1e999", "1" + "0" * 400 + ".0"])
def test_un_litteral_infini_est_une_erreur_de_syntaxe(litteral: str) -> None:
    erreur = une_erreur(f"faaite [{litteral}];")
    assert isinstance(erreur, ErreurSyntaxe)
    assert erreur.message.startswith("décimal trop grand : ")
    with pytest.raises(ErreursMultiples):
        mettre_en_forme(f"faaite [{litteral}];")


#: Un infini et un NaN, obtenus par le calcul (sans exposant : le test vaut aussi
#: sans la notation exponentielle).
NON_FINIS = (
    "tuu inf = 1.5;\n"
    "tataitahi i roto 0..400 { inf = inf * 10.0; }\n"
    "tuu nan = inf - inf;\n"
)


NOEUD = "un nœud de upea doit être un nombre fini, pas "
POIDS = "le poids d'un arc doit être un nombre fini, pas "


def cle(sorte: str) -> str:
    return f"une clé de {sorte} doit être un nombre fini, pas "


@pytest.mark.parametrize(
    ("instruction", "message"),
    [
        ("taati(upea {}, inf, 1);", NOEUD + "inf"),
        ("taati(upea {}, 1, nan);", NOEUD + "nan"),
        ("faaite upea { inf -> 1 };", NOEUD + "inf"),
        ("amui(upea {}, nan);", NOEUD + "nan"),
        ("taati(upea {}, 1, 2, nan);", POIDS + "nan"),
        ("faaite upea { 1 -> 2 : inf };", POIDS + "inf"),
        ("amui(aifaito [5.0], nan);", cle("aifaito") + "nan"),
        ("faaite imi [inf];", cle("imi") + "inf"),
        ("amui(pupu [1.0], nan);", cle("pupu") + "nan"),
        ("amui(ahu [], inf);", cle("ahu") + "inf"),
    ],
)
def test_un_non_fini_est_refuse(instruction: str, message: str) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(NON_FINIS + instruction, types=False)
    assert info.value.message == message
    assert info.value.position is not None and info.value.position.ligne == 4


def test_bellman_ford_ne_recoit_plus_de_poids_nan() -> None:
    """Il laissait fuir un `KeyError` (GRAPH-08)."""
    source = (
        NON_FINIS
        + 'tuu g = upea { "A" -> "B" : nan };\nfaaite bellman_ford(g, "A", "B");'
    )
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)
    assert "nombre fini" in info.value.message


def test_un_non_fini_s_affiche_encore() -> None:
    assert lancer(NON_FINIS + "faaite inf, nan, [inf];") == "inf nan [inf]\n"
