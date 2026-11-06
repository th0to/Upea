"""Extension 18, correctifs après la session 2 : la version, les classes, la division
entière, le délai, et le dépannage d'un serveur qui garde l'ancien code chargé."""

import re
import tomllib
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp import Client
from mcp.types import TextContent

import upea
from outils import PROJET, lancer
from upea import aide
from upea.serveur_mcp import construire_serveur

RACINE = PROJET.parent


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(construire_serveur()) as connecte:
        yield connecte


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


# --- La version -----------------------------------------------------------------------


def test_la_version_est_celle_de_pyproject() -> None:
    projet = tomllib.loads(lire(RACINE / "pyproject.toml"))["project"]
    assert projet["version"] == "1.0.0"
    assert upea.__version__ == projet["version"]


@pytest.mark.anyio
async def test_le_serveur_annonce_sa_version(client: Client) -> None:
    assert client.server_info is not None
    assert client.server_info.version == upea.__version__ == "1.0.0"


@pytest.mark.anyio
async def test_la_premiere_ligne_d_apercu_donne_la_version(client: Client) -> None:
    resultat = await client.call_tool("aide", {"sujet": "apercu"})
    texte = "".join(c.text for c in resultat.content if isinstance(c, TextContent))
    premiere = texte.splitlines()[0]
    assert "Upea 1.0.0" in premiere
    assert premiere == "# Upea 1.0.0 : l'aide-mémoire (à lire en premier)"
    assert texte == aide.APERCU


# --- L'aide-mémoire -------------------------------------------------------------------


def test_apercu_dit_que_les_classes_et_la_division_entiere_manquent() -> None:
    manque = aide.APERCU.split("## Ce qu'Upea n'a pas", 1)[1]
    assert "classes" in manque
    assert "`//`" in manque
    assert "commentaire" in manque
    assert "numera(a / b)" in manque
    assert "tronque vers zéro" in manque
    assert "arrondit vers le bas" in manque


def test_apercu_montre_comment_ajouter_un_enfant() -> None:
    assert "amui(a.amaa, tumu(4))" in aide.APERCU


def test_ajouter_un_enfant_marche() -> None:
    source = (
        "tuu a = tumu(1);\namui(a.amaa, tumu(4));\nfaaite roa(a.amaa), a.amaa[0].hotu;"
    )
    assert lancer(source) == "1 4\n"


def test_apercu_tient_dans_8_kio() -> None:
    assert len(aide.APERCU.encode("utf-8")) <= 8 * 1024


# --- De Python à Upea -----------------------------------------------------------------


def recette(texte: str, titre: str) -> str:
    """Le texte de la recette `### titre`, jusqu'à la suivante."""
    return texte.split(f"### {titre}", 1)[1].split("\n### ", 1)[0]


def test_la_recette_de_classe_est_executee() -> None:
    texte = aide.texte_depuis_python()
    classe = recette(texte, "Une classe : un état et des fonctions")
    assert "class " in classe
    blocs = re.findall(r"```upea\n(.*?)```\n\n```sortie\n(.*?)```", classe, re.DOTALL)
    assert len(blocs) == 2
    for source, sortie in blocs:
        assert lancer(source) == sortie


def test_la_division_entiere_est_exacte_pour_les_deux_signes() -> None:
    texte = aide.texte_depuis_python()
    division = recette(texte, "La division entière : `//`")
    fonction = re.search(r"```upea\n(ohipa div_ent.*?)\n\n", division, re.DOTALL)
    assert fonction is not None
    couples = [(a, b) for a in range(-9, 10) for b in range(-4, 5) if b != 0]
    appels = "\n".join(f"faaite div_ent({a}, {b});" for a, b in couples)
    obtenu = lancer(f"{fonction[1]}\n\n{appels}\n").split()
    assert obtenu == [str(a // b) for a, b in couples]


def test_la_division_entiere_est_documentee_avec_son_exemple() -> None:
    division = recette(aide.texte_depuis_python(), "La division entière : `//`")
    assert "tronque vers zéro" in division
    assert "arrondit vers le bas" in division
    assert "```sortie" in division
    assert "-7 // 2" in division


def test_le_delai_de_5_secondes_est_dit() -> None:
    texte = aide.texte_depuis_python()
    assert "5 s" in texte
    assert "exploration exponentielle" in texte
    assert "réduisez la profondeur" in texte


def test_le_tableau_d_equivalences_cite_la_division() -> None:
    assert "| `a // b` | `div_ent(a, b)` |" in aide.texte_depuis_python()


def test_les_pages_generees_sont_a_jour() -> None:
    assert aide.pages_perimees() == []


# --- Le dépannage ---------------------------------------------------------------------


def test_mcp_explique_qu_un_serveur_garde_son_code_charge() -> None:
    texte = lire(RACINE / "docs" / "mcp.md")
    depannage = texte.split("## 8. Dépannage", 1)[1].split("\n## ", 1)[0]
    depannage = " ".join(depannage.split())  # sans les retours à la ligne
    assert "garde le code chargé" in depannage
    assert "Quitter" in depannage
    assert "icône" in depannage
    assert "barre des tâches" in depannage
    assert "`aide` et `exemples`" in depannage
    assert 'aide("apercu")' in depannage
    assert "Upea 1.0.0" in depannage
