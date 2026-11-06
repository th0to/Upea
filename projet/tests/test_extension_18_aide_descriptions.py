"""Extension 18, lot B : des descriptions d'outils qui suffisent seules.

Les descriptions des outils sont le seul texte garanti d'arriver jusqu'à une IA, quel
que soit son client (un pont peut ne transmettre que les outils). Chacune commence donc
par la même phrase : Upea est un langage aux mots-clés tahitiens, et `aide("apercu")` en
donne les bases.
"""

from collections.abc import AsyncIterator

import pytest
from mcp import Client
from mcp.types import TextContent

from upea import aide
from upea.serveur_mcp import construire_serveur

#: Ce qu'une description peut compter au plus : elles doivent rester concises.
LONGUEUR_MAX = 1600


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(construire_serveur()) as connecte:
        yield connecte


def test_la_phrase_d_en_tete_est_celle_du_plan() -> None:
    assert aide.PRESENTATION == (
        "Upea est un langage aux mots-clés tahitiens, transpilé en Python. "
        'Si tu ne le connais pas, appelle d\'abord aide("apercu").'
    )


@pytest.mark.anyio
async def test_chaque_description_commence_par_la_phrase(client: Client) -> None:
    outils = (await client.list_tools()).tools
    assert len(outils) == 8
    for outil in outils:
        assert outil.description is not None
        assert outil.description.startswith(aide.PRESENTATION + "\n\n"), outil.name
        # ...suivie du texte propre à l'outil, qui n'est pas vide.
        assert len(outil.description) > len(aide.PRESENTATION) + 100, outil.name


@pytest.mark.anyio
async def test_chaque_description_renvoie_a_aide(client: Client) -> None:
    for outil in (await client.list_tools()).tools:
        assert 'aide("apercu")' in (outil.description or ""), outil.name


@pytest.mark.anyio
async def test_les_descriptions_restent_concises(client: Client) -> None:
    for outil in (await client.list_tools()).tools:
        assert outil.description is not None
        taille = len(outil.description)
        assert taille <= LONGUEUR_MAX, f"{outil.name} : {taille} caractères"


@pytest.mark.anyio
async def test_les_instructions_disent_la_meme_chose(client: Client) -> None:
    instructions = client.instructions
    assert instructions is not None
    assert instructions.startswith(aide.PRESENTATION)
    for outil in ("aide", "exemples", "verifier", "executer"):
        assert outil in instructions
    assert "lis la ressource" not in instructions
    # Les clients qui affichent les ressources les trouvent toujours.
    assert "upea://specification" in instructions


@pytest.mark.anyio
async def test_les_prompts_renvoient_aussi_a_aide_apercu(client: Client) -> None:
    for nom, arguments in (
        ("ecrire_programme", {"tache": "t"}),
        ("traduire_depuis_python", {"code": "print(1)"}),
        ("corriger_programme", {"source": "faaite 1;", "erreurs": "e"}),
    ):
        [message] = (await client.get_prompt(nom, arguments)).messages
        assert isinstance(message.content, TextContent)
        assert 'aide("apercu")' in message.content.text, nom
        # Le chemin par les ressources reste indiqué.
        assert "upea://specification" in message.content.text, nom
