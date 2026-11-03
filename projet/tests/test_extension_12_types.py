"""Extension 12 : le typage statique graduel."""

import pytest

from outils import erreurs_de_compilation, lancer, position, une_erreur
from upea.compilateur import compiler, transpiler
from upea.erreurs import ErreurSemantique, ErreurType
from upea.noeuds import TypeNote
from upea.typage import (
    AORE,
    INCONNU,
    NUMERA,
    PARAU,
    TIAHAPE,
    TUHAA,
    Type,
    commun,
    compatible,
    depuis_note,
    tapura,
    tumu,
    upea,
)


@pytest.mark.parametrize(
    ("attendu", "recu", "resultat"),
    [
        (NUMERA, NUMERA, True),
        (TUHAA, NUMERA, True),
        (NUMERA, TUHAA, False),
        (INCONNU, PARAU, True),
        (PARAU, INCONNU, True),
        (AORE, NUMERA, False),
        (TIAHAPE, NUMERA, False),
        (tapura(NUMERA), tapura(INCONNU), True),
        (tapura(TUHAA), tapura(NUMERA), True),
        (tapura(NUMERA), tumu(NUMERA), False),
        (upea(PARAU), upea(PARAU), True),
        (upea(PARAU), upea(NUMERA), False),
        (tapura(tumu(INCONNU)), tapura(tumu(PARAU)), True),
    ],
)
def test_la_regle_de_compatibilite(attendu: Type, recu: Type, resultat: bool) -> None:
    assert compatible(attendu, recu) is resultat


@pytest.mark.parametrize(
    ("a", "b", "resultat"),
    [
        (NUMERA, NUMERA, NUMERA),
        (NUMERA, TUHAA, TUHAA),
        (PARAU, NUMERA, INCONNU),
        (tapura(NUMERA), tapura(TUHAA), tapura(TUHAA)),
        (tapura(NUMERA), tumu(NUMERA), INCONNU),
    ],
)
def test_le_type_commun(a: Type, b: Type, resultat: Type) -> None:
    assert commun(a, b) == resultat


def test_une_annotation_designe_son_type() -> None:
    note = TypeNote("tapura", TypeNote("tumu", TypeNote("parau")))
    assert depuis_note(note) == tapura(tumu(PARAU))
    assert depuis_note(TypeNote("upea")) == upea(INCONNU)
    assert str(depuis_note(note)) == "tapura[tumu[parau]]"


@pytest.mark.parametrize(
    "source",
    [
        "tuu x: tuhaa = 1;\nfaaite x;",
        "ohipa f(a: numera, b: tuhaa) -> tuhaa { hoi a + b; }\nfaaite f(1, 2);",
        "tuu l: tapura[numera] = [];\namui(l, 3);",
        'tuu g: upea[parau] = upea { "a" -> "b" };\n'
        'tataitahi m roto g mai "a" { faaite m + "!"; }',
        "tuu t = tumu(1, tumu(2));\n"
        "tuu v: numera = t.hotu + t.amaa[0].hotu;\nfaaite v;",
        'ohipa f(x) { hoi x; }\ntuu y: numera = f("a");\nfaaite y;',
        "ohipa f() -> numera { ahani tia { hoi 1; } taae { hoi 2; } }\nfaaite f();",
        "ohipa f() -> aore { hoi; }\nf();",
        'tuu x = aore;\nx = 3;\nx = "a";\nfaaite x;',
        "tuu p = ea(upea { 1 -> 2 }, 1, 2);\nahani p != aore { faaite p; }",
        'tuu l = [];\namui(l, 1);\namui(l, "a");',
        'tuu n: tapura[parau] = motu(upea { "a" -> "b" });\nfaaite n;',
        "tuu r: tapura[numera] = rau(tumu(1, tumu(2)));\nfaaite r;",
        'faaite "a" roto "abc", 1 roto [1, 2], 1 roto tumu(1), 1 roto upea { 1 -> 2 };',
    ],
)
def test_des_programmes_bien_types_sont_acceptes(source: str) -> None:
    compiler(source)


@pytest.mark.parametrize(
    ("source", "fragment", "ligne", "colonne"),
    [
        ('tuu x: numera = "a";', "'x' est déclaré numera, mais reçoit parau", 1, 17),
        ('tuu x = 1;\nx = "deux";', "'x' est de type numera, mais reçoit parau", 2, 5),
        ("tuu x: numera = 1.5;", "déclaré numera, mais reçoit tuhaa", 1, 17),
        ('faaite 1 + "a";', "opérandes de '+' incompatibles : numera et parau", 1, 10),
        ("faaite tia * 2;", "opérandes de '*' incompatibles", 1, 12),
        ("faaite [1] + 2;", "opérandes de '+' incompatibles", 1, 12),
        ("ahani 1 { }", "condition du ahani : tiahape attendu, numera reçu", 1, 7),
        ('tamau "x" { }', "condition du tamau", 1, 7),
        (
            'ohipa f(n: numera) { }\nf("a");',
            "argument 1 de 'f' : numera attendu, parau reçu",
            2,
            3,
        ),
        (
            'ohipa f() -> numera { hoi "a"; }',
            "doit renvoyer un numera, mais renvoie un parau",
            1,
            27,
        ),
        ("ohipa f() -> numera { hoi; }", "'hoi' seul ne suffit pas", 1, 23),
        (
            "ohipa f() -> numera { ahani tia { hoi 1; } }",
            "peut se terminer sans 'hoi'",
            1,
            7,
        ),
        ("ohipa f() -> aore { hoi 1; }", "ne renvoie rien", 1, 25),
        (
            "faaite eiaha 1;",
            "opérande de 'eiaha' : tiahape attendu, numera reçu",
            1,
            14,
        ),
        ("faaite 1 ma tia;", "opérande de 'ma' : tiahape attendu", 1, 8),
        ('faaite 1 < "a";', "comparaison '<' impossible entre numera et parau", 1, 10),
        ('faaite 1 == "a";', "comparer un numera et un parau n'a pas de sens", 1, 10),
        ("faaite tia == 1;", "comparer un tiahape et un numera", 1, 12),
        ('faaite -"a";', "opérande de '-' : nombre attendu, parau reçu", 1, 9),
        ('faaite [1]["a"];', "indice : numera attendu, parau reçu", 1, 12),
        (
            "faaite 5[0];",
            "on ne peut indexer qu'une tapura ou un parau, pas un numera",
            1,
            9,
        ),
        (
            "tuu x = 3;\nfaaite x.hotu;",
            "seul un tumu a le champ hotu, pas un numera",
            2,
            10,
        ),
        (
            'tuu t = tumu(1);\nt.hotu = "a";',
            "champ hotu : numera attendu, parau reçu",
            2,
            10,
        ),
        (
            "tuu l = [1];\nl[0] = tia;",
            "élément de la tapura : numera attendu, tiahape",
            2,
            8,
        ),
        (
            "tataitahi i roto 0..1.5 { }",
            "borne d'un intervalle : numera attendu, tuhaa",
            1,
            21,
        ),
        ("tataitahi x roto 5 { }", "on ne peut pas parcourir un numera", 1, 18),
        ("tataitahi x roto [1] mai 1 { }", "'mai' ne s'emploie qu'avec un upea", 1, 18),
        (
            "tataitahi x roto tumu(1) mai 1 { }",
            "'mai' ne s'emploie qu'avec un upea",
            1,
            18,
        ),
        (
            "tataitahi x roto [1] aano { }",
            "'aano' ne s'emploie qu'avec un tumu ou un upea",
            1,
            18,
        ),
        (
            "tataitahi x roto upea { 1 -> 2 } aano { }",
            "demande un point de départ",
            1,
            18,
        ),
        (
            'tataitahi x roto upea { 1 -> 2 } mai "a" { }',
            "nœud de départ : numera attendu, parau reçu",
            1,
            38,
        ),
        ("faaite upea { [1] -> 2 };", "un nœud de upea doit être un numera", 1, 15),
        (
            'faaite upea { 1 -> 2 : "lourd" };',
            "le poids d'une arête doit être un nombre",
            1,
            24,
        ),
        (
            'tuu l = [1];\namui(l, "a");',
            "amui : élément numera attendu, parau reçu",
            2,
            9,
        ),
        (
            "faaite roa(5);",
            "roa : tapura, parau, tumu ou upea attendu, numera reçu",
            1,
            12,
        ),
        (
            'faaite pihai(upea { 1 -> 2 }, "a");',
            "pihai : nœud numera attendu, parau reçu",
            1,
            31,
        ),
        ("faaite tumu(1, 2);", "tumu : les enfants doivent être des tumu", 1, 16),
        ("faaite teitei([1]);", "teitei : tumu attendu, tapura[numera] reçu", 1, 15),
        ('faaite "z" roto [1];', "on cherche un parau dans un tapura[numera]", 1, 8),
        (
            "faaite 1 roto 5;",
            "roto attend une tapura, un parau, un tumu ou un upea",
            1,
            15,
        ),
        (
            'faaite taati(upea { 1 -> 2 }, 1, 2, "x");',
            "le poids doit être un nombre",
            1,
            37,
        ),
        (
            "faaite numera([1]);",
            "numera : impossible de convertir un tapura[numera]",
            1,
            15,
        ),
        ("faaite motu([1]);", "motu : upea attendu, tapura[numera] reçu", 1, 13),
    ],
)
def test_chaque_erreur_de_type_est_signalee_a_sa_position(
    source: str, fragment: str, ligne: int, colonne: int
) -> None:
    erreur = une_erreur(source)
    assert isinstance(erreur, ErreurType)
    assert fragment in erreur.message
    assert position(erreur) == (ligne, colonne)


@pytest.mark.parametrize(
    ("source", "fragment", "colonne"),
    [
        ("tuu x: entier = 1;", "type inconnu : 'entier'", 8),
        ("tuu x: numera[parau] = 1;", "le type numera n'a pas de paramètre", 15),
        ("ohipa f(a: liste) { }", "type inconnu : 'liste'", 12),
    ],
)
def test_une_annotation_qui_ne_designe_aucun_type_est_refusee(
    source: str, fragment: str, colonne: int
) -> None:
    erreur = une_erreur(source)
    assert fragment in erreur.message
    assert position(erreur) == (1, colonne)


def test_une_erreur_de_type_est_une_erreur_semantique() -> None:
    erreur = une_erreur('tuu x: numera = "a";')
    assert isinstance(erreur, ErreurSemantique)
    assert erreur.genre == "erreur de type"


def test_une_erreur_n_en_provoque_pas_d_autres_en_cascade() -> None:
    erreurs = erreurs_de_compilation('tuu x = (1 + "a") * 2;\nfaaite x - 1;')
    assert len(erreurs) == 1


def test_une_valeur_non_annotee_ne_declenche_pas_d_erreur() -> None:
    compiler('ohipa double(x) { hoi x * 2; }\nfaaite double("ab") + 1, double(2) + 1;')


def test_l_inference_donne_un_type_aux_variables() -> None:
    assert "numera" in une_erreur('tuu n = roa("abc");\nn = "x";').message
    assert "tapura[parau]" in une_erreur('tuu l = ["a"];\nl = 3;').message


def test_toutes_les_erreurs_de_type_sont_signalees_ensemble() -> None:
    erreurs = erreurs_de_compilation('tuu x: numera = "a";\nahani x { faaite x; }')
    assert [position(e) for e in erreurs] == [(1, 17), (2, 7)]


def test_sans_types_les_erreurs_de_type_disparaissent_mais_pas_les_autres() -> None:
    compiler('tuu x: numera = "a";\nfaaite x;', types=False)
    assert lancer('tuu x: numera = "a";\nfaaite x;', types=False) == "a\n"
    erreur = une_erreur('tuu x: numera = "a";\nfaaite y;', types=False)
    assert "'y' n'est pas déclaré" in erreur.message


def test_les_annotations_sont_reportees_dans_le_python_genere() -> None:
    source = (
        "ohipa f(a: tapura[numera], t: tumu[parau], g: upea, x) -> tiahape { hoi tia; }"
    )
    code = transpiler(source).code
    assert "def f(a: list, t: _Tumu, g: _Upea, x) -> bool:" in code
