"""Étape 6 : le parser des instructions, et la récupération d'erreurs."""

import pytest

from outils import position
from upea.erreurs import ErreurLexicale, ErreursMultiples, ErreurSyntaxe
from upea.noeuds import (
    Affectation,
    Affiche,
    Appel,
    Binaire,
    Bloc,
    Branche,
    Champ,
    Decimal,
    Declaration,
    Entier,
    ExprInstr,
    Fonction,
    Index,
    Instr,
    Liste,
    Parametre,
    Pour,
    Retour,
    Rien,
    Rupture,
    Si,
    TantQue,
    Texte,
    TypeNote,
    Variable,
)
from upea.parser import MAX_ERREURS, parse

VIDE = Bloc(())


def une_instruction(source: str) -> Instr:
    instructions = parse(source).instructions
    assert len(instructions) == 1
    return instructions[0]


def erreurs(source: str) -> ErreursMultiples:
    with pytest.raises(ErreursMultiples) as info:
        parse(source)
    return info.value


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("tuu x = 1;", Declaration("x", Entier(1))),
        ("tuu x: numera = 1;", Declaration("x", Entier(1), TypeNote("numera"))),
        ("mau pi = 3.14;", Declaration("pi", Decimal(3.14), None, True)),
        (
            "tuu l: tapura[tumu[parau]] = [];",
            Declaration(
                "l", Liste(()), TypeNote("tapura", TypeNote("tumu", TypeNote("parau")))
            ),
        ),
        ("tuu g: upea = aore;", Declaration("g", Rien(), TypeNote("upea"))),
        ("x = 2;", Affectation(Variable("x"), Entier(2))),
        ("t[0] = 2;", Affectation(Index(Variable("t"), Entier(0)), Entier(2))),
        ("a.hotu = 2;", Affectation(Champ(Variable("a"), "hotu"), Entier(2))),
        ("f(1);", ExprInstr(Appel("f", (Entier(1),)))),
        ("faaite;", Affiche(())),
        ('faaite 1, "a";', Affiche((Entier(1), Texte("a")))),
        ("ahani a { }", Si((Branche(Variable("a"), VIDE),))),
        (
            "ahani a { } taae ahani b { faaite; } taae { }",
            Si(
                (
                    Branche(Variable("a"), VIDE),
                    Branche(Variable("b"), Bloc((Affiche(()),))),
                ),
                VIDE,
            ),
        ),
        ("tamau c { faaea; }", TantQue(Variable("c"), Bloc((Rupture("faaea"),)))),
        (
            "tataitahi i roto 0..n { haere; }",
            Pour("i", Entier(0), Bloc((Rupture("haere"),)), Variable("n")),
        ),
        ("tataitahi i roto 1..=3 { }", Pour("i", Entier(1), VIDE, Entier(3), True)),
        ("tataitahi x roto l { }", Pour("x", Variable("l"), VIDE)),
        (
            'tataitahi m roto g mai "A" aano { }',
            Pour("m", Variable("g"), VIDE, depart=Texte("A"), mode="aano"),
        ),
        (
            'tataitahi m roto g mai "A" { }',
            Pour("m", Variable("g"), VIDE, depart=Texte("A")),
        ),
        (
            "tataitahi n roto t hohonu { }",
            Pour("n", Variable("t"), VIDE, mode="hohonu"),
        ),
        ("ohipa f() { hoi; }", Fonction("f", (), Bloc((Retour(),)))),
        (
            "ohipa f(a: numera, b) -> parau { hoi a; }",
            Fonction(
                "f",
                (Parametre("a", TypeNote("numera")), Parametre("b")),
                Bloc((Retour(Variable("a")),)),
                TypeNote("parau"),
            ),
        ),
        ("ohipa f() -> aore { }", Fonction("f", (), VIDE, TypeNote("aore"))),
    ],
)
def test_chaque_instruction_donne_le_bon_noeud(source: str, arbre: Instr) -> None:
    assert une_instruction(source) == arbre


def test_les_structures_imbriquees_sont_analysees() -> None:
    source = """
    ohipa f(n) {
        ahani n > 0 {
            tataitahi i roto 0..n {
                faaite i;
            }
        }
    }
    """
    boucle = Pour("i", Entier(0), Bloc((Affiche((Variable("i"),)),)), Variable("n"))
    condition = Si((Branche(Binaire(">", Variable("n"), Entier(0)), Bloc((boucle,))),))
    assert une_instruction(source) == Fonction(
        "f", (Parametre("n"),), Bloc((condition,))
    )


def test_la_mise_en_page_ne_change_pas_l_arbre() -> None:
    assert parse("tuu x=1;ahani x>0{faaite x;}") == parse(
        "tuu x = 1;\nahani x > 0 {\n    faaite x;\n}\n"
    )


@pytest.mark.parametrize("source", ["1 = 2;", "f(x) = 3;", "a + b = 3;", "[a] = [1];"])
def test_une_affectation_a_une_cible_invalide_est_refusee(source: str) -> None:
    groupe = erreurs(source)
    assert len(groupe.erreurs) == 1
    assert "on ne peut affecter qu'à une variable" in groupe.erreurs[0].message
    assert position(groupe.erreurs[0]) == (1, 1)


def test_un_point_virgule_oublie_est_signale_en_fin_de_ligne() -> None:
    source = (
        "tuu total = 0;\ntataitahi i roto 1..4 {\n"
        "    total = totale + i\n}\nfaaite total;"
    )
    (erreur,) = erreurs(source).erreurs
    assert erreur.message == "';' attendu après l'affectation, trouvé '}'"
    assert position(erreur) == (3, 23)


def test_un_point_virgule_oublie_apres_un_texte() -> None:
    (erreur,) = erreurs('faaite "a\\n"\nfaaite 2;').erreurs
    assert position(erreur) == (1, 13)


def test_toutes_les_erreurs_sont_signalees_ensemble() -> None:
    source = "tuu = 1;\nfaaite 1 +;\ntuu y = 2\nfaaite y;"
    groupe = erreurs(source)
    assert [position(e) for e in groupe.erreurs] == [(1, 5), (2, 11), (3, 10)]
    assert all(isinstance(e, ErreurSyntaxe) for e in groupe.erreurs)


def test_une_erreur_dans_un_bloc_n_empeche_pas_d_analyser_la_suite() -> None:
    source = "ahani tia {\n    tuu = 1;\n    faaite 2 +;\n}\nfaaite 3 *;"
    assert [position(e) for e in erreurs(source).erreurs] == [(2, 9), (3, 15), (5, 11)]


def test_une_accolade_orpheline_est_signalee() -> None:
    (erreur,) = erreurs("faaite 1;\n}\nfaaite 2;").erreurs
    assert erreur.message == "'}' sans '{' correspondante"
    assert position(erreur) == (2, 1)


def test_un_bloc_jamais_ferme_est_signale() -> None:
    (erreur,) = erreurs("ahani tia {\n    faaite 1;\n").erreurs
    assert "bloc ouvert ligne 1 jamais fermé" in erreur.message
    assert position(erreur) == (3, 1)


def test_taae_sans_ahani_est_signale() -> None:
    (erreur,) = erreurs("taae { }").erreurs
    assert "'taae' sans 'ahani'" in erreur.message


def test_une_comparaison_ecrite_avec_egal_donne_un_conseil() -> None:
    (erreur,) = erreurs("ahani x = 3 { faaite 1; }\nfaaite 2;").erreurs
    assert "(pour comparer, écrivez '==')" in erreur.message
    assert position(erreur) == (1, 9)


def test_l_erreur_regroupee_est_chainee_a_la_premiere() -> None:
    groupe = erreurs("faaite 1 +;\nfaaite 2 *;")
    assert groupe.__cause__ is groupe.erreurs[0]


def test_une_erreur_lexicale_arrive_dans_le_groupe() -> None:
    groupe = erreurs("faaite 1 +;\nfaaite @;")
    premiere, lexicale = groupe.erreurs
    assert isinstance(premiere, ErreurSyntaxe)
    assert isinstance(lexicale, ErreurLexicale)
    assert position(lexicale) == (2, 8)
    assert groupe.__cause__ is premiere


def test_une_erreur_lexicale_seule_est_la_cause() -> None:
    groupe = erreurs('faaite "jamais fermé;')
    assert isinstance(groupe.erreurs[0], ErreurLexicale)
    assert groupe.__cause__ is groupe.erreurs[0]


def test_des_points_virgules_seuls_ne_bouclent_pas() -> None:
    # Le premier `;` est fautif ; la resynchronisation consomme le deuxième
    # comme fin de cette instruction, et le troisième est fautif à son tour.
    assert [position(e) for e in erreurs(";;;").erreurs] == [(1, 1), (1, 3)]


def test_le_nombre_d_erreurs_est_limite() -> None:
    assert len(erreurs("faaite +;\n" * 30).erreurs) == MAX_ERREURS


def test_un_programme_vide_est_valide() -> None:
    assert parse("// rien\n").instructions == ()
