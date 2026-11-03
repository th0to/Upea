"""Étape 2 : les types de token et la classe Token."""

import dataclasses

import pytest

from upea.erreurs import Position
from upea.tokens import MOTS_CLES, SYMBOLES, Token, TokenKind

MOTS_CLES_ATTENDUS = [
    "tuu", "mau", "ohipa", "hoi", "ahani", "taae", "tamau", "tataitahi",
    "roto", "mai", "aano", "hohonu", "faaea", "haere", "faaite", "upea",
    "tia", "hape", "aore", "ma", "anei", "eiaha",
]  # fmt: skip


def test_position_lisible() -> None:
    assert str(Position(3, 7)) == "ligne 3, colonne 7"


def test_position_sans_colonne() -> None:
    assert str(Position(3, 0)) == "ligne 3"


def test_position_decalee() -> None:
    assert Position(2, 5).decale(3) == Position(2, 8)


def test_un_token_est_immuable() -> None:
    token = Token(TokenKind.TUU, "tuu", Position(1, 1))
    with pytest.raises(dataclasses.FrozenInstanceError):
        token.lexeme = "mau"  # type: ignore[misc]


def test_un_token_est_hachable() -> None:
    tokens = {Token(TokenKind.TUU, "tuu", Position(1, 1))} | {
        Token(TokenKind.TUU, "tuu", Position(1, 1))
    }
    assert len(tokens) == 1


def test_deux_tokens_identiques_sont_egaux() -> None:
    a = Token(TokenKind.IDENT, "x", Position(2, 3))
    assert a == Token(TokenKind.IDENT, "x", Position(2, 3))
    assert a != Token(TokenKind.IDENT, "x", Position(2, 4))


def test_repr_tient_sur_une_ligne() -> None:
    texte = repr(Token(TokenKind.TUU, "tuu", Position(1, 1)))
    assert texte == "Token(TUU, 'tuu', 1:1)"
    assert "\n" not in texte


def test_la_table_des_mots_cles_est_complete() -> None:
    assert set(MOTS_CLES) == set(MOTS_CLES_ATTENDUS)
    assert all(MOTS_CLES[mot].value == mot for mot in MOTS_CLES)


def test_les_symboles_ne_contiennent_aucun_mot_cle() -> None:
    lexemes = {lexeme for lexeme, _ in SYMBOLES}
    assert lexemes.isdisjoint(MOTS_CLES)
    assert {"(", "->", "<->", "..=", "==", "!=", ";"} <= lexemes


def test_les_mots_cles_ne_contiennent_aucun_symbole() -> None:
    assert all(mot.isalpha() for mot in MOTS_CLES)


def test_chaque_prefixe_vient_apres_le_symbole_plus_long() -> None:
    ordre = [lexeme for lexeme, _ in SYMBOLES]
    for i, court in enumerate(ordre):
        for j, long in enumerate(ordre):
            if long != court and long.startswith(court):
                assert j < i, f"{long!r} doit précéder {court!r}"


@pytest.mark.parametrize(
    ("kind", "texte"),
    [
        (TokenKind.POINT_VIRGULE, "';'"),
        (TokenKind.ACC_D, "'}'"),
        (TokenKind.TUU, "'tuu'"),
        (TokenKind.DOUBLE_FLECHE, "'<->'"),
        (TokenKind.IDENT, "<identifiant>"),
        (TokenKind.FIN, "<fin>"),
    ],
)
def test_str_d_un_type_de_token(kind: TokenKind, texte: str) -> None:
    assert str(kind) == texte


def test_un_symbole_entre_chevrons_reste_fixe() -> None:
    # `<->` commence par `<` et finit par `>`, comme `<entier>` : ce n'est
    # pourtant pas une description.
    assert TokenKind.DOUBLE_FLECHE.est_fixe
    assert not TokenKind.ENTIER.est_fixe


def test_fin_d_un_token_texte_compte_les_guillemets() -> None:
    token = Token(TokenKind.TEXTE, "a", Position(1, 5), taille=3)
    assert token.fin == Position(1, 8)
