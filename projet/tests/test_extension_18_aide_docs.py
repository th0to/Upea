"""Extension 18, lot D : les pages d'aide de `docs/` sont produites par `upea.aide`.

`docs/aide-memoire.md` et `docs/depuis-python.md` sont des fichiers générés : un test
échoue s'ils ne correspondent plus au module (`uv run python -m upea.aide --ecrire`
les réécrit). Les programmes qu'ils contiennent sont exécutés, comme ceux de toute la
documentation, par `test_livraison_documentation.py` ; ils le sont aussi ici, depuis le
module, pour que l'outil `aide` dise vrai sans passer par un fichier.
"""

import ast
import re
import subprocess
import sys
from pathlib import Path

import pytest

from outils import PROJET, lancer
from upea import aide

RACINE = PROJET.parent
DOCS = RACINE / "docs"
COMMANDE = "uv run python -m upea.aide --ecrire"


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


# --- Les pages générées ---------------------------------------------------------------


@pytest.mark.parametrize("nom", ["aide-memoire.md", "depuis-python.md"])
def test_la_page_correspond_au_module(nom: str) -> None:
    attendu = aide.pages()[nom]
    assert lire(DOCS / nom) == attendu, f"page périmée : lancez `{COMMANDE}`"


def test_les_pages_disent_qu_elles_sont_generees() -> None:
    for nom, texte in aide.pages().items():
        assert texte.startswith("<!-- Fichier généré par"), nom
        assert COMMANDE in texte.splitlines()[0], nom


def test_la_page_d_aide_memoire_est_l_apercu() -> None:
    assert aide.pages()["aide-memoire.md"].endswith(aide.APERCU)


def test_ecrire_puis_verifier(tmp_path: Path) -> None:
    assert sorted(aide.pages_perimees(tmp_path)) == [
        "aide-memoire.md",
        "depuis-python.md",
    ]
    aide.ecrire_pages(tmp_path)
    assert aide.pages_perimees(tmp_path) == []
    (tmp_path / "depuis-python.md").write_text("à la main\n", encoding="utf-8")
    assert aide.pages_perimees(tmp_path) == ["depuis-python.md"]


def test_la_commande_verifier_echoue_sur_une_page_perimee(tmp_path: Path) -> None:
    aide.ecrire_pages(tmp_path)
    (tmp_path / "aide-memoire.md").write_text("périmée\n", encoding="utf-8")
    resultat = subprocess.run(
        [sys.executable, "-m", "upea.aide", "--verifier", "--dossier", str(tmp_path)],
        cwd=PROJET,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert resultat.returncode == 1
    assert "aide-memoire.md" in resultat.stderr
    assert COMMANDE in resultat.stderr
    assert "Traceback" not in resultat.stderr


def test_la_commande_verifier_reussit_sur_le_depot() -> None:
    resultat = subprocess.run(
        [sys.executable, "-m", "upea.aide", "--verifier"],
        cwd=PROJET,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert resultat.returncode == 0, resultat.stderr


def test_la_commande_ecrire_ecrit_les_pages(tmp_path: Path) -> None:
    resultat = subprocess.run(
        [sys.executable, "-m", "upea.aide", "--ecrire", "--dossier", str(tmp_path)],
        cwd=PROJET,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    assert resultat.returncode == 0, resultat.stderr
    assert lire(tmp_path / "aide-memoire.md") == aide.pages()["aide-memoire.md"]


# --- Ce que depuis_python enseigne est vrai -------------------------------------------

TEXTES = {"apercu": aide.APERCU, "depuis_python": aide.texte_depuis_python()}


def programmes_avec_sortie(texte: str) -> list[tuple[str, str]]:
    """Les blocs `upea` suivis (à une ligne vide près) d'un bloc `sortie`."""
    return re.findall(
        r"```upea\n(.*?)```\n\n```sortie\n(.*?)```", texte, flags=re.DOTALL
    )


@pytest.mark.parametrize("sujet", sorted(TEXTES))
def test_chaque_programme_donne_sa_sortie(sujet: str) -> None:
    programmes = programmes_avec_sortie(TEXTES[sujet])
    assert programmes
    for source, sortie in programmes:
        assert lancer(source) == sortie, source


def test_tous_les_blocs_upea_ont_une_sortie() -> None:
    for sujet, texte in TEXTES.items():
        nombre = len(re.findall(r"^```upea$", texte, flags=re.MULTILINE))
        assert nombre == len(programmes_avec_sortie(texte)), sujet


def test_les_blocs_python_sont_du_python() -> None:
    blocs = re.findall(r"```python\n(.*?)```", TEXTES["depuis_python"], re.DOTALL)
    assert len(blocs) >= 3
    for bloc in blocs:
        ast.parse(bloc)


def test_depuis_python_traite_ce_qu_upea_n_a_pas() -> None:
    texte = TEXTES["depuis_python"]
    for sujet in (
        "dictionnaire",
        "ensemble",
        "hasard",
        "clavier",
        "liste de paires",
        "arbre ordonné",
        "générateur pseudo-aléatoire",
        "constantes",
    ):
        assert sujet in texte, sujet


def test_depuis_python_a_son_tableau_d_equivalences() -> None:
    texte = TEXTES["depuis_python"]
    assert "| Python | Upea |" in texte
    assert "| `while True:` | `tamau tia { … }` |" in texte
    assert "compteur = 0;" in texte  # le piège : déclarer


# --- Les autres pages y renvoient -----------------------------------------------------


@pytest.mark.parametrize("document", ["README.md", "docs/tutoriel.md", "docs/mcp.md"])
def test_les_documents_renvoient_aux_deux_pages(document: str) -> None:
    texte = lire(RACINE / document)
    assert "aide-memoire.md" in texte, document
    assert "depuis-python.md" in texte, document


def test_l_architecture_presente_le_module_aide() -> None:
    texte = lire(DOCS / "architecture.md")
    assert "`aide.py`" in texte
    assert "aide-memoire.md" in texte


def test_mcp_presente_aide_et_exemples_et_les_clients_outils_seuls() -> None:
    texte = lire(DOCS / "mcp.md")
    assert "`aide`" in texte
    assert "`exemples`" in texte
    assert "seuls les outils" in texte.lower()
    # L'ancienne affirmation : l'IA ne « lit » pas les ressources de son propre chef.
    assert (
        "Les instructions du serveur lui disent par où commencer : lire la" not in texte
    )
