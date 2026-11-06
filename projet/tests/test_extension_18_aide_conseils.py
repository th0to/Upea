"""Extension 18, lot C : les faux amis dans les messages d'erreur.

Quand l'erreur porte sur un mot d'un autre langage (Python, français…), le message
garde son texte et ajoute, à la fin, un conseil : « 'si' n'est pas un mot-clé d'Upea :
écrivez 'ahani' ».
"""

import re

import pytest

from outils import erreurs_de_compilation, lancer
from upea import aide
from upea.compilateur import compiler
from upea.erreurs import Avertissement, ErreurSemantique, ErreurSyntaxe
from upea.predefinies import PREDEFINIES
from upea.tokens import MOTS_CLES

TOUS_LES_MOTS = [mot for faux in aide.FAUX_AMIS for mot in faux.mots]
AMBIGUS = ["retour", "rien", "non", "pour", "dans", "fonction", "vrai", "faux"]


def messages(source: str) -> list[str]:
    return [e.message for e in erreurs_de_compilation(source)]


def un_message(source: str) -> str:
    (message,) = messages(source)
    return message


# --- La table ---------------------------------------------------------------------


def test_aucun_faux_ami_n_est_un_mot_d_upea() -> None:
    # S'ils l'étaient, ce ne seraient plus des faux amis : et c'est parce que ce sont
    # des identifiants ordinaires qu'une variable `si` reste permise.
    for mot in TOUS_LES_MOTS:
        assert mot not in MOTS_CLES, mot
        assert mot not in PREDEFINIES, mot


def test_chaque_conseil_cite_des_mots_d_upea_qui_existent() -> None:
    for faux in aide.FAUX_AMIS:
        for equivalent in faux.equivalents:
            assert equivalent in MOTS_CLES or equivalent in PREDEFINIES, faux
            assert equivalent in faux.conseil, faux
        assert faux.conseil


def test_la_table_contient_les_mots_demandes() -> None:
    attendus = [
        "if",
        "elif",
        "else",
        "while",
        "for",
        "def",
        "return",
        "break",
        "continue",
        "print",
        "True",
        "False",
        "None",
        "and",
        "or",
        "not",
        "si",
        "sinon",
        "tantque",
        "pour",
        "fonction",
        "retourner",
        "afficher",
        "vrai",
        "faux",
        "et",
        "ou",
        "non",
    ]
    for mot in attendus:
        assert mot in TOUS_LES_MOTS, mot
    assert len(TOUS_LES_MOTS) == len(set(TOUS_LES_MOTS))


def test_les_mots_ambigus_sont_au_conditionnel() -> None:
    ambigus = {mot for faux in aide.FAUX_AMIS if faux.intention for mot in faux.mots}
    assert set(AMBIGUS) <= ambigus


@pytest.mark.parametrize("mot", TOUS_LES_MOTS)
def test_un_faux_ami_non_declare_recoit_son_conseil(mot: str) -> None:
    message = un_message(f"tuu x = {mot};")
    assert message.startswith(f"'{mot}' n'est pas déclaré")
    assert " — " in message
    assert "vouliez-vous dire" not in message
    faux = next(f for f in aide.FAUX_AMIS if mot in f.mots)
    assert message.endswith(aide.conseil_de(faux, mot))


def test_un_conseil_dit_ce_qu_il_faut_ecrire() -> None:
    assert un_message("faaite si;").endswith(
        " — 'si' n'est pas un mot-clé d'Upea : écrivez 'ahani'"
    )
    assert un_message("faaite True;").endswith(
        " — 'True' n'est pas un mot-clé d'Upea : écrivez 'tia'"
    )


def test_un_mot_sans_equivalent_dit_qu_il_n_existe_pas() -> None:
    message = un_message("tuu s = input();")
    assert " — 'input' n'existe pas en Upea : " in message
    assert "clavier" in message


# --- Les erreurs de syntaxe -----------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "mot", "conseil"),
    [
        ("si x > 1 { faaite x; }", "si", "écrivez 'ahani'"),
        ("tuu x = 2;\nif x > 1 { faaite x; }", "if", "écrivez 'ahani'"),
        ("tuu i = 0;\nwhile i < 3 { i = i + 1; }", "while", "écrivez 'tamau'"),
        ("tuu i = 0;\ntant que i < 3 { i = i + 1; }", "tant que", "écrivez 'tamau'"),
        ("tuu i = 0;\ntantque i < 3 { i = i + 1; }", "tantque", "écrivez 'tamau'"),
        ("def f(x) { hoi x; }", "def", "écrivez 'ohipa'"),
        ("fonction f(x) { hoi x; }", "fonction", "écrivez 'ohipa'"),
        ("ohipa f(x) { return x; }", "return", "écrivez 'hoi'"),
        ("for x in [1, 2] { faaite x; }", "for", "écrivez 'tataitahi x roto liste'"),
        (
            "pour i in range(3) { faaite i; }",
            "pour",
            "écrivez 'tataitahi x roto liste'",
        ),
        (
            "tuu x = 1;\nahani x > 1 { faaite x; } elif x < 0 { faaite 0; }",
            "elif",
            "écrivez 'taae ahani'",
        ),
        (
            "tuu x = 1;\nahani x > 1 { faaite x; } else { faaite 0; }",
            "else",
            "écrivez 'taae'",
        ),
        (
            "tuu x = 2;\nahani x > 1 { faaite x; } sinon { faaite 0; }",
            "sinon",
            "écrivez 'taae'",
        ),
        ("tuu a = tia;\nahani a and a { faaite 1; }", "and", "écrivez 'ma'"),
        ("tuu a = tia;\nahani not a { faaite 1; }", "not", "écrivez 'eiaha'"),
        ("tuu l = [];\nl.append(1);", "append", "écrivez 'amui(liste, x)'"),
        ("print(1, 2);", "print", "écrivez 'faaite'"),
    ],
)
def test_une_erreur_de_syntaxe_conseille_le_mot_d_un_autre_langage(
    source: str, mot: str, conseil: str
) -> None:
    erreurs = erreurs_de_compilation(source)
    assert any(
        f"'{mot}' n'est pas un mot-clé d'Upea" in e.message
        or f"'{mot}' n'existe pas" in e.message
        for e in erreurs
    ), [e.message for e in erreurs]
    assert any(conseil in e.message for e in erreurs)


def test_le_message_d_origine_est_conserve_devant_le_conseil() -> None:
    message = un_message("si x > 1 { faaite x; }")
    assert message.startswith("';' attendu après l'expression, trouvé 'x' — ")


def test_le_conseil_s_ajoute_au_message_dans_le_rapport_complet() -> None:
    (erreur,) = erreurs_de_compilation("si x > 1 { faaite x; }")
    assert isinstance(erreur, ErreurSyntaxe)
    assert "ahani" in str(erreur)


@pytest.mark.parametrize("operateur", ["+", "-", "*", "/", "%"])
def test_une_affectation_composee_est_expliquee(operateur: str) -> None:
    message = un_message(f"tuu x = 1;\nx {operateur}= 2;")
    assert message.startswith("expression attendue, trouvé '='")
    assert f"Upea n'a pas d'affectation composée : écrivez 'x = x {operateur} …;'" in (
        message
    )


def test_un_egal_apres_un_operateur_separe_n_est_pas_une_affectation_composee() -> None:
    message = un_message("tuu x = 1;\nx = x + = 2;")
    assert "composée" not in message


# --- Une variable déclarée n'est jamais accusée ---------------------------------------


@pytest.mark.parametrize("mot", ["si", "et", "ou", "pour", "retour", "print", "for"])
def test_une_variable_qui_porte_ce_nom_reste_permise_sans_conseil(mot: str) -> None:
    source = f"tuu {mot} = 1;\nfaaite {mot};"
    compiler(source)
    assert lancer(source) == "1\n"


def test_un_parametre_ou_une_fonction_ou_une_boucle_a_ce_nom() -> None:
    for source in (
        "ohipa f(et) { hoi et; }\nfaaite f(1);",
        "ohipa retour() { hoi 1; }\nfaaite retour();",
        "tataitahi pour roto 1..3 { faaite pour; }",
        "ohipa f(a: numera, ou: numera) -> numera { hoi a + ou; }",
    ):
        compiler(source)


@pytest.mark.parametrize("mot", ["si", "et", "pour", "retour", "print", "ou", "dans"])
def test_une_erreur_voisine_n_accuse_pas_une_variable_declaree(mot: str) -> None:
    for source in (
        f"tuu {mot} = 1;\nfaaite {mot} x;",
        f"tuu {mot} = 1;\nfaaite 1 {mot} 2;",
        f"tuu {mot} = 1;\nahani {mot} faaite 1;",
    ):
        for erreur in erreurs_de_compilation(source):
            assert "mot-clé d'Upea" not in erreur.message, source
            assert "n'existe pas en Upea" not in erreur.message, source
            assert "si vous vouliez" not in erreur.message, source


def test_une_variable_declaree_dans_un_autre_bloc_n_est_pas_accusee_non_plus() -> None:
    source = "ahani tia { tuu si = 1; faaite si; }\nfaaite si;"
    message = un_message(source)
    assert message.startswith("'si' n'est pas déclaré")
    assert "mot-clé d'Upea" not in message


# --- Rien d'autre ne change -----------------------------------------------------------


@pytest.mark.parametrize(
    ("source", "attendu"),
    [
        ("faaite y;", "'y' n'est pas déclaré"),
        ("blabla;", "'blabla' n'est pas déclaré"),
        ("tuu x = 1\nfaaite x;", "';' attendu après la déclaration, trouvé 'faaite'"),
        ("ahani a < b < c { }", "les comparaisons ne s'enchaînent pas"),
        ("faaea;", "faaea hors d'une boucle"),
    ],
)
def test_les_messages_sans_faux_ami_sont_inchanges(source: str, attendu: str) -> None:
    messages_obtenus = messages(source)
    assert any(attendu in m for m in messages_obtenus)
    assert all("—" not in m for m in messages_obtenus)


def test_les_suggestions_des_autres_mots_sont_conservees() -> None:
    message = un_message("tuu liste = [1];\nfaaite lite;")
    assert message == "'lite' n'est pas déclaré (vouliez-vous dire 'liste' ?)"


def test_le_format_de_la_suggestion_est_celui_que_le_conseil_remplace() -> None:
    # `aide` retire la suggestion d'un message de `semantique` : son motif doit suivre
    # le format réel.
    message = un_message("tuu liste = [1];\nfaaite lite;")
    assert aide.SUGGESTION.search(message)


def test_un_programme_valide_n_a_aucun_conseil() -> None:
    compiler("tuu si = 1;\nfaaite si;")  # ne lève rien


def test_les_avertissements_ne_recoivent_pas_de_conseil() -> None:
    analyse = compiler("tuu si = 1;").analyse
    (avertissement,) = analyse.avertissements
    assert isinstance(avertissement, Avertissement)
    assert "mot-clé" not in avertissement.message


def test_les_erreurs_de_type_ne_recoivent_pas_de_conseil() -> None:
    message = un_message('tuu x: numera = "a";')
    assert "mot-clé" not in message and "—" not in message


# --- Une affectation à un nom non déclaré (l'habitude de Python) ----------------------


def test_affecter_un_nom_non_declare_conseille_de_le_declarer() -> None:
    message = un_message("compteur = 0;")
    assert message == (
        "'compteur' n'est pas déclaré — déclarez-la d'abord : tuu compteur = …;"
    )


def test_la_regle_de_declaration_passe_avant_les_faux_amis() -> None:
    message = un_message("si = 3;")
    assert message == "'si' n'est pas déclaré — déclarez-la d'abord : tuu si = …;"


def test_retour_affecte_dans_une_fonction_conseille_de_declarer() -> None:
    source = "ohipa f(x) {\n    retour = x * 2;\n    hoi retour;\n}\nfaaite f(1);"
    erreurs = erreurs_de_compilation(source)
    premiere = erreurs[0].message
    assert premiere == (
        "'retour' n'est pas déclaré — déclarez-la d'abord : tuu retour = …;"
    )
    for erreur in erreurs:
        assert "écrivez 'hoi'" not in erreur.message
        assert "vouliez-vous dire" not in premiere


def test_hoi_retour_non_declare_ne_conseille_pas_hoi() -> None:
    message = un_message("ohipa f(x) {\n    hoi retour;\n}\nfaaite f(1);")
    assert message.startswith("'retour' n'est pas déclaré")
    assert "hoi" not in message.replace("'retour' n'est pas déclaré", "")
    assert "mot-clé" not in message


def test_retour_lu_ailleurs_reste_au_conditionnel() -> None:
    message = un_message("faaite retour;")
    assert message.endswith(
        " — 'retour' n'est pas un mot-clé d'Upea ; "
        "si vous vouliez renvoyer une valeur, écrivez 'hoi'"
    )


@pytest.mark.parametrize("mot", AMBIGUS)
def test_un_mot_ambigu_lu_est_au_conditionnel(mot: str) -> None:
    message = un_message(f"faaite {mot};")
    assert "; si vous vouliez " in message
    assert re.search(r", écrivez '[^']+'", message)


@pytest.mark.parametrize("mot", AMBIGUS)
def test_un_mot_ambigu_affecte_conseille_de_declarer(mot: str) -> None:
    message = un_message(f"{mot} = 1;")
    assert message.endswith(f"déclarez-la d'abord : tuu {mot} = …;")
    assert "si vous vouliez" not in message


def test_un_mot_non_ambigu_n_est_pas_au_conditionnel() -> None:
    assert "si vous vouliez" not in un_message("faaite si;")
    assert "si vous vouliez" not in un_message("faaite if;")
    assert "si vous vouliez" not in un_message("faaite len;")


def test_affecter_un_indice_d_un_nom_non_declare_ne_propose_pas_de_declarer() -> None:
    message = un_message("nombres[0] = 1;")
    assert "déclarez-la" not in message


def test_les_erreurs_semantiques_aussi_sont_des_erreurs_de_la_sorte_d_origine() -> None:
    erreurs = erreurs_de_compilation("compteur = 0;")
    assert isinstance(erreurs[0], ErreurSemantique)
