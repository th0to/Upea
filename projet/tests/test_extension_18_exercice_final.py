"""Extension 18, lot E : le scénario de l'exercice final, joué par un client naïf.

La session 1 de l'exercice final (`docs/journal/exercice-final/`) a échoué : l'IA n'a
vu que les outils, dont les descriptions ne disaient rien du langage. Ce test rejoue la
situation avec le `Client` en mémoire du SDK, en ne lui laissant que la liste des
outils : il doit pouvoir apprendre Upea, écrire un programme, le corriger d'après les
messages, et l'exécuter, sans jamais ouvrir une ressource ni un prompt.
"""

import re
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from outils import PROJET
from upea.lexer import tokenize
from upea.predefinies import PREDEFINIES
from upea.serveur_mcp import construire_serveur
from upea.tokens import TokenKind

RACINE = PROJET.parent
JOURNAL = RACINE / "docs" / "journal" / "exercice-final"

#: Le premier jet d'un modèle qui pense en Python : un `si` au lieu de `ahani`. Tout le
#: reste vient de l'exemple de l'aide-mémoire (fonction typée, boucle, liste, graphe).
PREMIER_JET = """\
ohipa pair(n: numera) -> tiahape {
    hoi n % 2 == 0;
}

tuu nombres = [3, 8, 5, 12];
tuu total = 0;
tataitahi n roto nombres {
    si pair(n) {
        total = total + n;
    }
}
faaite "somme des pairs :", total;

tuu iles = upea { "A" <-> "B" : 2, "B" -> "C" : 3 };
faaite distance(iles, "A", "C");
"""
SORTIE_ATTENDUE = "somme des pairs : 20\n5\n"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(construire_serveur()) as connecte:
        yield connecte


def texte(resultat: CallToolResult) -> str:
    return "".join(c.text for c in resultat.content if isinstance(c, TextContent))


@pytest.mark.anyio
async def test_un_client_qui_ne_voit_que_les_outils_apprend_upea_et_reussit(
    client: Client,
) -> None:
    # 1. Il ne lit que la liste des outils (ni ressources, ni prompts, ni instructions).
    outils = (await client.list_tools()).tools
    noms = {outil.name for outil in outils}
    assert {"aide", "exemples", "verifier", "executer"} <= noms

    # 2. Chaque description le renvoie à `aide`.
    for outil in outils:
        assert outil.description is not None
        assert 'aide("apercu")' in outil.description, outil.name
        assert outil.description.startswith("Upea est un langage"), outil.name

    # 3. Il appelle aide("apercu"), et y trouve un exemple complet.
    apercu = texte(await client.call_tool("aide", {"sujet": "apercu"}))
    assert len(apercu.encode("utf-8")) <= 8 * 1024
    assert "```upea" in apercu

    # 4. Son programme n'emploie que ce que l'aide-mémoire lui a montré.
    for jeton in tokenize(PREMIER_JET):
        mot_cle = jeton.kind.est_mot_cle
        predefinie = jeton.kind is TokenKind.IDENT and jeton.lexeme in PREDEFINIES
        if mot_cle or predefinie:
            assert jeton.lexeme in apercu, jeton.lexeme

    # 5. Son premier jet garde un réflexe de Python : `verifier` le lui dit.
    premiere = await client.call_tool("verifier", {"source": PREMIER_JET})
    assert premiere.structured_content is not None
    assert premiere.structured_content["valide"] is False
    [diagnostic] = premiere.structured_content["diagnostics"]
    assert diagnostic["sorte"] == "syntaxe"
    assert "'si' n'est pas un mot-clé d'Upea : écrivez 'ahani'" in diagnostic["message"]

    # 6. Il suit le conseil, et le programme passe.
    corrige = PREMIER_JET.replace("    si pair(n)", "    ahani pair(n)")
    seconde = await client.call_tool("verifier", {"source": corrige})
    assert seconde.structured_content is not None
    assert seconde.structured_content["valide"] is True
    assert seconde.structured_content["diagnostics"] == []

    # 7. Il l'exécute, et obtient ce qu'il attendait.
    execution = await client.call_tool("executer", {"source": corrige})
    assert execution.structured_content is not None
    assert execution.structured_content["statut"] == "succes"
    assert execution.structured_content["sortie"] == SORTIE_ATTENDUE


@pytest.mark.anyio
async def test_l_exemple_d_apercu_est_celui_que_le_client_verifie(
    client: Client,
) -> None:
    apercu = texte(await client.call_tool("aide", {"sujet": "apercu"}))
    [(programme, sortie)] = re.findall(
        r"```upea\n(.*?)```\n\n```sortie\n(.*?)```", apercu, re.DOTALL
    )
    resultat = await client.call_tool("executer", {"source": programme})
    assert resultat.structured_content is not None
    assert resultat.structured_content["sortie"] == sortie


@pytest.mark.anyio
async def test_apres_apercu_le_client_a_de_quoi_aller_plus_loin(
    client: Client,
) -> None:
    apercu = texte(await client.call_tool("aide", {"sujet": "apercu"}))
    for sujet in ("mots_cles", "predefinies", "depuis_python", "specification"):
        assert f'aide("{sujet}")' in apercu, sujet
    assert "exemples()" in apercu


# --- Le journal de l'exercice ---------------------------------------------------------


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def test_le_journal_a_son_dossier_et_son_index() -> None:
    assert (JOURNAL / "index.md").is_file()
    assert (JOURNAL / "session-1-rapport.md").is_file()
    assert not (RACINE / "docs" / "journal" / "exerciceFinal").exists()


def test_le_rapport_de_la_session_1_est_conserve_tel_quel() -> None:
    rapport = lire(JOURNAL / "session-1-rapport.md")
    assert rapport.startswith("# Rapport d'utilisation du serveur MCP Upea")
    assert "Aucune référence du langage accessible (bloquant principal)" in rapport
    assert "mcp__remote-devices__upea__*" in rapport
    assert rapport.rstrip().endswith("de manière économique.")


def test_l_index_presente_la_demarche_et_reserve_les_observations() -> None:
    index = lire(JOURNAL / "index.md")
    assert "session-1-rapport.md" in index
    assert "session-2-rapport.md" in index
    assert "<!-- À RÉDIGER PAR THOMAS -->" in index
    # Ses observations, il les écrit lui-même : la section suit le marqueur, vide.
    apres = index.split("<!-- À RÉDIGER PAR THOMAS -->", 1)[1]
    assert apres.strip() == ""


def test_le_texte_de_la_session_2_ne_donne_pas_la_specification() -> None:
    index = lire(JOURNAL / "index.md")
    texte_session = index.split("````text\n", 1)[1].split("````", 1)[0]
    assert "taquin" in texte_session
    assert "sans documentation" in texte_session
    # Il ne cite aucune construction d'Upea : l'IA doit tout apprendre du serveur.
    for mot in ("tuu ", "ohipa", "ahani", "tataitahi", "faaite "):
        assert mot not in texte_session, mot
    # Il demande le rapport au format de la session 1.
    for titre in re.findall(r"^## .*$", lire(JOURNAL / "session-1-rapport.md"), re.M):
        assert titre in texte_session, titre


def test_la_place_de_la_session_2_existe() -> None:
    assert (JOURNAL / "session-2-rapport.md").is_file()
