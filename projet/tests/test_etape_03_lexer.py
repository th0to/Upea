"""Étape 3 : le lexer paresseux, le flux avec regard en avant, et `formater`."""

from collections.abc import Iterator

import pytest

from upea.erreurs import (
    ErreurExecution,
    ErreurLexicale,
    ErreurSemantique,
    ErreursMultiples,
    Position,
    formater,
)
from upea.flux import Flux
from upea.lexer import tokenize
from upea.tokens import Token
from upea.tokens import TokenKind as T


def kinds(source: str) -> list[T]:
    return [t.kind for t in tokenize(source)]


def lexemes(source: str) -> list[str]:
    return [t.lexeme for t in tokenize(source)][:-1]


def test_une_declaration_donne_la_bonne_suite_de_tokens() -> None:
    assert kinds("tuu x = 1..3;") == [
        T.TUU,
        T.IDENT,
        T.EGAL,
        T.ENTIER,
        T.POINT_POINT,
        T.ENTIER,
        T.POINT_VIRGULE,
        T.FIN,
    ]


def test_les_tokens_s_affichent_avec_leur_position() -> None:
    assert [repr(t) for t in tokenize("tuu x = 1..3;")] == [
        "Token(TUU, 'tuu', 1:1)",
        "Token(IDENT, 'x', 1:5)",
        "Token(EGAL, '=', 1:7)",
        "Token(ENTIER, '1', 1:9)",
        "Token(POINT_POINT, '..', 1:10)",
        "Token(ENTIER, '3', 1:12)",
        "Token(POINT_VIRGULE, ';', 1:13)",
        "Token(FIN, '', 1:14)",
    ]


def test_le_dernier_token_est_toujours_fin() -> None:
    assert kinds("") == [T.FIN]
    assert kinds("  // rien\n") == [T.FIN]


def test_lignes_et_colonnes_apres_un_saut_de_ligne() -> None:
    tokens = list(tokenize("tuu x = 1;\n  faaite x;"))
    assert [t.position for t in tokens[5:]] == [
        Position(2, 3),
        Position(2, 10),
        Position(2, 11),
        Position(2, 12),
    ]


@pytest.mark.parametrize(
    ("source", "attendus"),
    [
        ("->", [T.FLECHE]),
        ("-", [T.MOINS]),
        ("<->", [T.DOUBLE_FLECHE]),
        ("<=", [T.INF_EGAL]),
        ("<", [T.INF]),
        ("==", [T.EGAL_EGAL]),
        ("=", [T.EGAL]),
        ("!=", [T.DIFFERENT]),
        (">=", [T.SUP_EGAL]),
        ("..=", [T.POINT_POINT_EGAL]),
        ("..", [T.POINT_POINT]),
        (".", [T.POINT]),
        ("a<-1", [T.IDENT, T.INF, T.MOINS, T.ENTIER]),
        ("x->y", [T.IDENT, T.FLECHE, T.IDENT]),
        ("a<->b", [T.IDENT, T.DOUBLE_FLECHE, T.IDENT]),
        ("a===b", [T.IDENT, T.EGAL_EGAL, T.EGAL, T.IDENT]),
    ],
)
def test_symboles_composes_et_leurs_prefixes(source: str, attendus: list[T]) -> None:
    assert kinds(source) == [*attendus, T.FIN]


@pytest.mark.parametrize(
    ("source", "attendus", "textes"),
    [
        ("1.5", [T.DECIMAL], ["1.5"]),
        ("1..5", [T.ENTIER, T.POINT_POINT, T.ENTIER], ["1", "..", "5"]),
        ("1..=5", [T.ENTIER, T.POINT_POINT_EGAL, T.ENTIER], ["1", "..=", "5"]),
        ("t.hotu", [T.IDENT, T.POINT, T.IDENT], ["t", ".", "hotu"]),
        (
            "0..roa(l)",
            [T.ENTIER, T.POINT_POINT, T.IDENT, T.PAR_G, T.IDENT, T.PAR_D],
            None,
        ),
        ("t[0].amaa", [T.IDENT, T.CRO_G, T.ENTIER, T.CRO_D, T.POINT, T.IDENT], None),
    ],
)
def test_les_jetons_qui_se_ressemblent_ne_se_confondent_pas(
    source: str, attendus: list[T], textes: list[str] | None
) -> None:
    assert kinds(source) == [*attendus, T.FIN]
    if textes is not None:
        assert lexemes(source) == textes


@pytest.mark.parametrize(
    ("source", "valeur"),
    [
        (r'"a\nb"', "a\nb"),
        (r'"\t\"\\"', '\t"\\'),
        ('""', ""),
        ('"Ia ora na"', "Ia ora na"),
    ],
)
def test_les_textes_sont_decodes(source: str, valeur: str) -> None:
    token = next(tokenize(source))
    assert token.kind is T.TEXTE
    assert token.lexeme == valeur


def test_un_texte_garde_sa_taille_dans_le_source() -> None:
    texte, suivant = list(tokenize(r'"a\n" ;'))[:2]
    assert texte.fin == Position(1, 6)
    assert suivant.position == Position(1, 7)


def test_les_commentaires_sont_ignores() -> None:
    source = "// tout\ntuu /* au\nmilieu */ x = 1; // fin"
    assert kinds(source) == [T.TUU, T.IDENT, T.EGAL, T.ENTIER, T.POINT_VIRGULE, T.FIN]


def test_les_lignes_d_un_commentaire_bloc_sont_comptees() -> None:
    token = next(tokenize("/* a\nb */ x"))
    assert token.position == Position(2, 6)


@pytest.mark.parametrize("mot", ["iaora", "tuu_x", "Tuu", "maia", "hapetia", "upea2"])
def test_un_mot_cle_n_est_pas_le_prefixe_d_un_identifiant(mot: str) -> None:
    assert kinds(mot) == [T.IDENT, T.FIN]


def test_chaque_mot_cle_est_reconnu() -> None:
    assert kinds("ahani taae tamau tataitahi roto") == [
        T.AHANI,
        T.TAAE,
        T.TAMAU,
        T.TATAITAHI,
        T.ROTO,
        T.FIN,
    ]


def test_les_accents_ne_decalent_pas_les_colonnes() -> None:
    tokens = list(tokenize("déjà = île;"))
    assert [(t.lexeme, t.position.colonne) for t in tokens] == [
        ("déjà", 1),
        ("=", 6),
        ("île", 8),
        (";", 11),
        ("", 12),
    ]


def test_une_marque_d_ordre_des_octets_est_ignoree() -> None:
    tokens = list(tokenize("﻿tuu x"))
    assert tokens[0].kind is T.TUU
    assert tokens[0].position == Position(1, 1)


@pytest.mark.parametrize(
    ("source", "ligne", "colonne", "fragment"),
    [
        ("tuu x = 3 @ 2;", 1, 11, "caractère inattendu : '@'"),
        ('faaite "Ia ora na;', 1, 8, "texte non terminé"),
        ('"abc\ndef"', 1, 1, "texte non terminé"),
        (r'"a\qb"', 1, 3, r"échappement inconnu : \q"),
        ("/* sans fin", 1, 1, "jamais refermé"),
        ("12abc", 1, 1, "nombre mal formé"),
        ("x²", 1, 1, "identifiant mal formé"),
        ("tuu x = 1.;", 1, 10, "décimal incomplet"),
        ("tuu x = .5;", 1, 9, "sans partie entière"),
        ("_cache", 1, 1, "ne commence pas par '_'"),
        ("a ! b", 1, 3, "'!='"),
        ("a && b", 1, 3, "'ma'"),
        ("tuu a = 1;\n\n  @", 3, 3, "caractère inattendu"),
    ],
)
def test_chaque_erreur_lexicale_a_sa_position(
    source: str, ligne: int, colonne: int, fragment: str
) -> None:
    with pytest.raises(ErreurLexicale) as info:
        list(tokenize(source))
    assert info.value.position == Position(ligne, colonne)
    assert fragment in info.value.message


def test_tokenize_est_un_generateur_paresseux() -> None:
    tokens = tokenize("1 + 2 @")
    assert [next(tokens).kind for _ in range(3)] == [T.ENTIER, T.PLUS, T.ENTIER]
    with pytest.raises(ErreurLexicale):
        next(tokens)


# --- Flux ---------------------------------------------------------------------------


def _source_espionnee(elements: list[int], tires: list[int]) -> Iterator[int]:
    for element in elements:
        tires.append(element)
        yield element


def test_regarde_ne_consomme_rien() -> None:
    flux = Flux([1, 2, 3])
    assert flux.regarde() == 1
    assert flux.regarde(2) == 3
    assert flux.regarde() == 1
    assert flux.avance() == 1
    assert flux.regarde() == 2
    assert flux.consommes == 1


def test_le_flux_ne_tire_que_le_necessaire() -> None:
    tires: list[int] = []
    flux = Flux(_source_espionnee([1, 2, 3, 4], tires))
    assert tires == []
    flux.regarde()
    assert tires == [1]
    flux.regarde(1)
    assert tires == [1, 2]
    flux.avance()
    flux.avance()
    assert tires == [1, 2]


def test_regarde_au_dela_de_la_fin_rend_none() -> None:
    flux = Flux("a")
    assert flux.regarde(5) is None
    flux.avance()
    assert flux.regarde() is None
    assert flux.fini()
    with pytest.raises(IndexError):
        flux.avance()


def test_le_flux_accepte_des_tokens() -> None:
    flux: Flux[Token] = Flux(tokenize("tuu x"))
    assert flux.regarde(1) is not None
    assert flux.avance().kind is T.TUU


# --- formater -----------------------------------------------------------------------


def test_formater_place_le_chapeau_sous_la_colonne() -> None:
    erreur = ErreurSemantique("'y' n'est pas déclaré", Position(2, 8))
    assert formater(erreur, "tuu x = 1;\nfaaite y;", "p.upea") == (
        "p.upea:2:8 : erreur sémantique : 'y' n'est pas déclaré\n"
        "    faaite y;\n"
        "           ^"
    )


def test_formater_recopie_les_tabulations() -> None:
    erreur = ErreurSemantique("message", Position(1, 9))
    dernier = formater(erreur, "\tfaaite y;", "p").splitlines()[-1]
    assert dernier == "    \t       ^"


def test_formater_une_erreur_d_execution_sans_colonne() -> None:
    erreur = ErreurExecution("division par zéro", Position(1, 0))
    assert formater(erreur, "faaite 1 / 0;", "p") == (
        "p:1 : erreur d'exécution : division par zéro\n    faaite 1 / 0;"
    )


def test_formater_affiche_chaque_erreur_d_un_groupe() -> None:
    groupe = ErreursMultiples(
        [ErreurSemantique("a", Position(1, 1)), ErreurSemantique("b", Position(2, 1))]
    )
    texte = formater(groupe, "x;\ny;", "p")
    assert texte.count("erreur sémantique") == 2
    assert texte.index("p:1:1") < texte.index("p:2:1")


def test_formater_sans_position() -> None:
    assert formater(ErreurLexicale("oups"), "", "p") == "p : erreur lexicale : oups"
