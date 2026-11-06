"""Extension 18, lot A0 : le module `aide`, source unique des textes d'aide."""

import re
import subprocess
import sys

import pytest

from outils import PROJET, lancer
from upea import aide
from upea.compilateur import compiler
from upea.tokens import MOTS_CLES

#: Ce qu'on peut tenir, en octets, dans l'aide-mémoire (le budget d'un modèle).
BUDGET_APERCU = 8 * 1024


def test_chaque_mot_cle_a_son_entree() -> None:
    assert [m.mot for m in aide.mots_cles()] == list(MOTS_CLES)
    assert set(aide.EQUIVALENT_PYTHON) == set(MOTS_CLES)


def test_le_sens_est_celui_de_la_specification() -> None:
    texte = (PROJET / "specification.md").read_text(encoding="utf-8")
    for mot in aide.mots_cles():
        ligne = next(
            ligne
            for ligne in texte.splitlines()
            if ligne.startswith(f"| `{mot.mot}` |")
        )
        assert ligne.endswith(f"| {mot.role} |")
        assert mot.role
        assert mot.tahitien


def test_le_tableau_des_mots_cles_les_cite_tous() -> None:
    texte = aide.texte_mots_cles()
    for mot in MOTS_CLES:
        assert f"| `{mot}` |" in texte


def test_les_noms_de_section_sont_uniques() -> None:
    noms = [s.nom for s in aide.sections()]
    assert len(noms) == len(set(noms)) == 27


@pytest.mark.parametrize(
    ("demande", "debut"),
    [
        ("boucle_tataitahi", "### La boucle `tataitahi`"),
        ("La boucle tataitahi", "### La boucle `tataitahi`"),
        ("semantique", "## Sémantique"),
        ("grammaire", "## Grammaire (EBNF)"),
        ("Sémantique", "## Sémantique"),
        ("graphes", "### Graphes (`upea`)"),
    ],
)
def test_une_section_se_demande_par_son_nom(demande: str, debut: str) -> None:
    assert aide.texte_specification(demande).startswith(debut)


def test_un_titre_double_diese_rend_ses_sous_sections() -> None:
    texte = aide.texte_specification("semantique")
    assert "### La boucle `tataitahi`" in texte
    assert "## Types" not in texte


def test_un_nom_de_section_inconnu_rend_la_liste() -> None:
    texte = aide.texte_specification("blabla")
    assert texte.startswith("Pas de section « blabla »")
    assert "`boucle_tataitahi`" in texte


def test_sans_section_la_specification_rend_le_sommaire() -> None:
    sommaire = aide.texte_specification()
    assert "`grammaire`" in sommaire
    assert len(sommaire) < 3000


def test_tout_rend_la_specification_entiere() -> None:
    entiere = (PROJET / "specification.md").read_text(encoding="utf-8")
    assert aide.texte_specification("tout") == entiere


def test_un_exemple_connu_donne_son_programme_et_sa_sortie() -> None:
    texte = aide.exemple("05_motu")
    assert "# Exemple 05_motu" in texte
    assert "```upea" in texte
    assert "## Sa sortie exacte" in texte


@pytest.mark.parametrize("nom", ["99_inconnu", "../specification", "..\\x", ""])
def test_un_exemple_inconnu_donne_la_liste_des_noms(nom: str) -> None:
    with pytest.raises(aide.AideInconnue, match="05_motu"):
        aide.exemple(nom)


def test_la_liste_des_exemples_les_cite_tous() -> None:
    liste = aide.liste_exemples()
    for nom, chemin in aide.exemples_disponibles().items():
        assert f"`{nom}` : {aide.description_exemple(chemin)}" in liste


def test_les_predefinies_sont_celles_du_compilateur() -> None:
    texte = aide.texte_predefinies()
    assert "`pihai(upea[T], T) -> tapura[T]`" in texte
    assert "## Abréviations" in texte


def test_apercu_tient_dans_son_budget() -> None:
    taille = len(aide.APERCU.encode("utf-8"))
    assert taille <= BUDGET_APERCU, f"{taille} octets"


def test_l_exemple_d_apercu_s_execute_et_donne_sa_sortie() -> None:
    blocs = dict(re.findall(r"```(upea|sortie)\n(.*?)```", aide.APERCU, re.DOTALL))
    compiler(blocs["upea"])
    assert lancer(blocs["upea"]) == blocs["sortie"]


def test_la_presentation_renvoie_a_aide_apercu() -> None:
    assert 'aide("apercu")' in aide.PRESENTATION
    assert aide.PRESENTATION.startswith("Upea est un langage")


def test_le_module_s_importe_sans_le_sdk_ni_la_facade() -> None:
    programme = (
        "import sys\n"
        "sys.modules['mcp'] = None\n"
        "import upea.aide\n"
        "assert 'upea.compilateur' not in sys.modules\n"
    )
    resultat = subprocess.run(
        [sys.executable, "-c", programme],
        cwd=PROJET,
        capture_output=True,
        text=True,
        check=False,
    )
    assert resultat.returncode == 0, resultat.stderr
