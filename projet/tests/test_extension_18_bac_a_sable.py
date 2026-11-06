"""Extension 18 : l'exécution isolée, dans un sous-processus (sans MCP)."""

import sys
import time

import pytest

from outils import EXEMPLES, lancer, lire
from upea import bac_a_sable
from upea.atelier import Diagnostic
from upea.bac_a_sable import (
    PLAFOND,
    PLAFOND_MEMOIRE,
    DelaiDepasse,
    EnfantEnPanne,
    executer,
)


def test_un_exemple_donne_sa_sortie_attendue() -> None:
    exemple = EXEMPLES / "05_motu.upea"
    resultat = executer(lire(exemple))
    assert resultat.statut == "succes"
    assert resultat.code_retour == 0
    assert resultat.sortie == lire(exemple.with_suffix(".attendu"))
    assert not resultat.tronquee
    assert resultat.diagnostics == ()


def test_avec_le_backend_ast() -> None:
    exemple = EXEMPLES / "04_tumu.upea"
    resultat = executer(lire(exemple), backend="ast")
    assert resultat.sortie == lire(exemple.with_suffix(".attendu"))


def test_une_erreur_de_compilation() -> None:
    resultat = executer("faaite y;")
    assert resultat.statut == "erreur_compilation"
    assert resultat.code_retour == 1
    assert resultat.sortie == ""
    assert resultat.diagnostics == (
        Diagnostic("semantique", 1, 8, "'y' n'est pas déclaré"),
    )
    assert "programme.upea:1:8" in resultat.rapport


def test_une_erreur_d_execution_et_sa_ligne_upea() -> None:
    resultat = executer('faaite "avant";\nfaaite [1, 2][5];\nfaaite "après";\n')
    assert resultat.statut == "erreur_execution"
    assert resultat.code_retour == 3
    assert resultat.sortie == "avant\n"
    assert resultat.diagnostics == (
        Diagnostic("execution", 2, None, "indice hors limites"),
    )
    assert "programme.upea:2 : erreur d'exécution" in resultat.rapport


def test_une_recursion_sans_fin() -> None:
    resultat = executer("ohipa f(n) { hoi f(n + 1); }\nfaaite f(0);\n")
    assert resultat.statut == "erreur_execution"
    assert resultat.diagnostics[-1].message == (
        "récursion trop profonde (plus de 20 000 appels imbriqués)"
    )


def test_les_avertissements_accompagnent_le_resultat() -> None:
    resultat = executer("tuu inutile = 1;\nfaaite 2;\n")
    assert resultat.statut == "succes"
    assert resultat.sortie == "2\n"
    assert [d.sorte for d in resultat.diagnostics] == ["avertissement"]


def test_une_boucle_sans_fin_est_arretee() -> None:
    debut = time.monotonic()
    with pytest.raises(DelaiDepasse) as arret:
        executer('faaite "début";\ntamau tia { }\n', delai=2)
    assert time.monotonic() - debut < 2 + 3
    assert arret.value.sortie == "début\n"  # la sortie déjà écrite est gardée
    assert not arret.value.tronquee
    assert "2 s" in str(arret.value)


def test_une_sortie_sans_fin_est_plafonnee_et_arretee() -> None:
    with pytest.raises(DelaiDepasse) as arret:
        executer('tamau tia { faaite "Ia ora na"; }', delai=2)
    assert arret.value.tronquee
    assert len(arret.value.sortie.encode("utf-8")) <= PLAFOND
    assert arret.value.sortie.startswith("Ia ora na\n")


def test_une_sortie_enorme_est_tronquee() -> None:
    resultat = executer('tataitahi i roto 0..200000 { faaite "ligne", i; }')
    assert resultat.statut == "succes"
    assert resultat.tronquee
    assert len(resultat.sortie.encode("utf-8")) <= PLAFOND
    assert resultat.sortie.startswith("ligne 0\nligne 1\n")
    assert resultat.octets == sum(len(f"ligne {i}\n") for i in range(200000))
    assert "tronquée" in resultat.rapport


def test_la_troncature_ne_coupe_pas_un_caractere() -> None:
    resultat = executer('faaite "ééé";', plafond=5)
    assert resultat.sortie == "éé"
    assert resultat.tronquee


def test_les_caracteres_non_ascii_et_les_dessins() -> None:
    source = 'faaite "île ʻōmuamua → ü";\nfaaite aifaito [2, 1, 3];\n'
    resultat = executer(source)
    assert resultat.sortie == lancer(source)
    assert "┌─┴─┐" in resultat.sortie


def test_jamais_de_couleurs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORCE_COLOR", "1")
    resultat = executer("faaite aifaito [2, 1, 3];")
    assert "\x1b[" not in resultat.sortie


def test_le_programme_ne_peut_pas_imiter_le_resultat() -> None:
    faux = '{\\"statut\\": \\"succes\\", \\"code_retour\\": 0}'
    resultat = executer(f'faaite "{faux}";\nfaaite 1 / 0;\n')
    assert resultat.statut == "erreur_execution"
    assert resultat.sortie == '{"statut": "succes", "code_retour": 0}\n'


@pytest.mark.skipif(
    sys.platform not in ("win32", "linux"), reason="pas de plafond de mémoire ici"
)
@pytest.mark.parametrize("valeur", ['"x"', "[0]"], ids=["parau", "tapura"])
def test_la_memoire_est_plafonnee(valeur: str) -> None:
    """Sans plafond, ces programmes occupent plusieurs Go avant la fin du délai."""
    source = f"tuu v = {valeur};\ntamau tia {{\n    v = v + v;\n}}\n"
    resultat = executer(source, memoire=PLAFOND_MEMOIRE)
    assert resultat.statut == "erreur_execution"
    [erreur] = resultat.diagnostics
    assert erreur.ligne == 3
    assert erreur.message == "mémoire dépassée : un programme a au plus 512 Mo"


def test_un_programme_raisonnable_tient_sous_le_plafond() -> None:
    source = "tuu l = [];\ntataitahi i roto 0..1000000 { amui(l, i); }\nfaaite roa(l);"
    assert executer(source, memoire=PLAFOND_MEMOIRE).sortie == "1000000\n"


def test_un_enfant_en_panne(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bac_a_sable,
        "COMMANDE",
        [sys.executable, "-c", "import sys; sys.stderr.write('patatras'); sys.exit(7)"],
    )
    with pytest.raises(EnfantEnPanne) as panne:
        executer('faaite "x";')
    assert "7" in str(panne.value)
    assert "patatras" in str(panne.value)


def test_un_backend_qui_ne_s_execute_pas() -> None:
    with pytest.raises(ValueError, match="formateur"):
        executer('faaite "x";', backend="formateur")


# --- L'environnement de l'enfant ------------------------------------------------------


def test_l_enfant_ne_recoit_que_l_environnement_indispensable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("UPEA_SECRET", "jeton-du-serveur")
    environnement = bac_a_sable._environnement()
    assert "UPEA_SECRET" not in environnement
    assert set(environnement) <= {
        "PYTHONPATH",
        "PYTHONUTF8",
        "PYTHONIOENCODING",
        "NO_COLOR",
        "SYSTEMROOT",  # sous Windows seulement
    }


def test_l_enfant_ne_voit_pas_les_variables_du_serveur(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un secret du serveur (un jeton d'API de l'hôte, par exemple) n'arrive pas au
    processus qui exécute le programme : on remplace l'enfant par un script qui
    montre ce qu'il voit, et on passe par `executer` comme le serveur."""
    monkeypatch.setenv("UPEA_SECRET", "jeton-du-serveur")
    montrer = (
        "import os, sys; sys.stderr.write(os.environ.get('UPEA_SECRET', 'absent'))"
    )
    monkeypatch.setattr(
        bac_a_sable, "COMMANDE", [sys.executable, "-c", montrer + "; sys.exit(7)"]
    )
    with pytest.raises(EnfantEnPanne) as panne:
        executer('faaite "x";')
    assert "absent" in str(panne.value)
    assert "jeton-du-serveur" not in str(panne.value)
