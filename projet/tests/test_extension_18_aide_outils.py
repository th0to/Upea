"""Extension 18, lot A : l'aide sous forme d'outils (`aide` et `exemples`).

Seuls les outils sont appelés par le modèle de lui-même : une ressource est choisie par
l'application, un prompt par l'utilisateur. Tout ce qu'une IA doit pouvoir consulter
seule est donc un outil.
"""

import re
from collections.abc import AsyncIterator

import pytest
from mcp import Client
from mcp.types import CallToolResult, TextContent

from outils import LISTE_EXEMPLES, PROJET
from upea import aide
from upea.compilateur import analyser_syntaxe
from upea.erreurs import ErreursMultiples
from upea.serveur_mcp import construire_serveur


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(construire_serveur()) as connecte:
        yield connecte


def texte(resultat: CallToolResult) -> str:
    return "".join(c.text for c in resultat.content if isinstance(c, TextContent))


async def demander(client: Client, outil: str, **arguments: object) -> str:
    resultat = await client.call_tool(outil, dict(arguments))
    assert not resultat.is_error, texte(resultat)
    return texte(resultat)


# --- Les outils sont déclarés ---------------------------------------------------------


@pytest.mark.anyio
async def test_il_y_a_huit_outils(client: Client) -> None:
    noms = [o.name for o in (await client.list_tools()).tools]
    assert sorted(noms) == sorted(
        [
            "tokenize",
            "parse",
            "verifier",
            "formater",
            "transpiler",
            "executer",
            "aide",
            "exemples",
        ]
    )


@pytest.mark.anyio
@pytest.mark.parametrize("nom", ["aide", "exemples"])
async def test_les_outils_d_aide_ne_touchent_a_rien(client: Client, nom: str) -> None:
    outil = next(o for o in (await client.list_tools()).tools if o.name == nom)
    assert outil.annotations is not None
    assert outil.annotations.read_only_hint is True
    assert outil.annotations.idempotent_hint is True
    assert outil.annotations.open_world_hint is False
    assert outil.description
    assert "\n    " not in outil.description


@pytest.mark.anyio
async def test_le_schema_de_aide_montre_les_sujets(client: Client) -> None:
    outil = next(o for o in (await client.list_tools()).tools if o.name == "aide")
    proprietes = outil.input_schema["properties"]
    assert proprietes["sujet"]["enum"] == list(aide.SUJETS)
    assert outil.input_schema["required"] == ["sujet"]
    assert "section" in proprietes
    for sujet in aide.SUJETS:
        assert sujet in (outil.description or ""), sujet


@pytest.mark.anyio
async def test_le_schema_de_exemples_n_a_rien_d_obligatoire(client: Client) -> None:
    outil = next(o for o in (await client.list_tools()).tools if o.name == "exemples")
    assert "required" not in outil.input_schema or not outil.input_schema["required"]
    assert "nom" in outil.input_schema["properties"]


# --- Les sujets de aide ---------------------------------------------------------------


@pytest.mark.anyio
async def test_apercu_rend_l_aide_memoire(client: Client) -> None:
    resultat = await demander(client, "aide", sujet="apercu")
    assert resultat == aide.APERCU
    assert len(resultat.encode("utf-8")) <= 8 * 1024


@pytest.mark.anyio
@pytest.mark.parametrize("sujet", aide.SUJETS)
async def test_chaque_sujet_rend_un_texte(client: Client, sujet: str) -> None:
    resultat = await demander(client, "aide", sujet=sujet)
    assert resultat.startswith("# ")
    assert len(resultat) > 500


@pytest.mark.anyio
async def test_mots_cles_donne_les_mots_et_les_faux_amis(client: Client) -> None:
    resultat = await demander(client, "aide", sujet="mots_cles")
    for mot in aide.mots_cles():
        assert f"| `{mot.mot}` |" in resultat
    assert "## Les mots d'un autre langage" in resultat
    assert "| `if` | Python | écrivez 'ahani' |" in resultat


@pytest.mark.anyio
async def test_predefinies_donne_le_catalogue_de_la_ressource(client: Client) -> None:
    resultat = await demander(client, "aide", sujet="predefinies")
    assert resultat == aide.texte_predefinies()
    [contenu] = (await client.read_resource("upea://predefinies")).contents
    assert getattr(contenu, "text", None) == resultat


@pytest.mark.anyio
async def test_la_specification_sans_section_rend_le_sommaire(client: Client) -> None:
    resultat = await demander(client, "aide", sujet="specification")
    assert resultat == aide.sommaire_specification()
    assert len(resultat) < 3000


@pytest.mark.anyio
async def test_une_section_de_la_specification(client: Client) -> None:
    resultat = await demander(
        client, "aide", sujet="specification", section="boucle_tataitahi"
    )
    assert resultat.startswith("### La boucle `tataitahi`")
    assert "tataitahi i roto a..b" in resultat


@pytest.mark.anyio
async def test_tout_rend_la_specification_entiere(client: Client) -> None:
    resultat = await demander(client, "aide", sujet="specification", section="tout")
    assert resultat == (PROJET / "specification.md").read_text(encoding="utf-8")


@pytest.mark.anyio
async def test_une_section_inconnue_rend_la_liste_sans_erreur(client: Client) -> None:
    resultat = await demander(client, "aide", sujet="specification", section="blabla")
    assert resultat.startswith("Pas de section « blabla »")
    assert "`grammaire`" in resultat


@pytest.mark.anyio
async def test_un_sujet_inconnu_est_refuse_avec_la_liste(client: Client) -> None:
    resultat = await client.call_tool("aide", {"sujet": "blabla"})
    assert resultat.is_error
    assert "apercu" in texte(resultat)


# --- Les exemples ---------------------------------------------------------------------


@pytest.mark.anyio
async def test_exemples_sans_argument_liste_tout(client: Client) -> None:
    resultat = await demander(client, "exemples")
    assert resultat == aide.liste_exemples()
    for exemple in LISTE_EXEMPLES:
        assert f"`{exemple.stem}` : " in resultat


@pytest.mark.anyio
async def test_un_exemple_donne_son_source_et_sa_sortie(client: Client) -> None:
    resultat = await demander(client, "exemples", nom="05_motu")
    assert resultat == aide.exemple("05_motu")
    source = (PROJET / "exemples" / "05_motu.upea").read_text(encoding="utf-8")
    sortie = (PROJET / "exemples" / "05_motu.attendu").read_text(encoding="utf-8")
    assert source in resultat
    assert sortie in resultat
    [ressource] = (await client.read_resource("upea://exemples/05_motu")).contents
    assert getattr(ressource, "text", None) == resultat


@pytest.mark.anyio
@pytest.mark.parametrize(
    "nom", ["99_inconnu", "../specification", "..\\specification", "05_motu/../x"]
)
async def test_un_nom_inconnu_rend_la_liste_des_noms(client: Client, nom: str) -> None:
    resultat = await demander(client, "exemples", nom=nom)
    assert f"pas d'exemple « {nom} »" in resultat
    assert "05_motu" in resultat
    assert "Spécification d'Upea" not in resultat  # aucun fichier n'a été lu


# --- Les ressources et les prompts n'ont pas changé -----------------------------------


@pytest.mark.anyio
async def test_les_ressources_et_les_prompts_sont_toujours_la(client: Client) -> None:
    ressources = {str(r.uri) for r in (await client.list_resources()).resources}
    assert {"upea://specification", "upea://exemples", "upea://predefinies"} <= (
        ressources
    )
    prompts = {p.name for p in (await client.list_prompts()).prompts}
    assert prompts == {
        "ecrire_programme",
        "corriger_programme",
        "traduire_depuis_python",
    }


# --- Ce que l'aide enseigne est vrai --------------------------------------------------


@pytest.mark.anyio
async def test_le_programme_d_apercu_passe_verifier_et_executer(client: Client) -> None:
    apercu = await demander(client, "aide", sujet="apercu")
    blocs = dict(re.findall(r"```(upea|sortie)\n(.*?)```", apercu, re.DOTALL))
    verification = await client.call_tool("verifier", {"source": blocs["upea"]})
    assert verification.structured_content is not None
    assert verification.structured_content["valide"] is True
    execution = await client.call_tool("executer", {"source": blocs["upea"]})
    assert execution.structured_content is not None
    assert execution.structured_content["statut"] == "succes"
    assert execution.structured_content["sortie"] == blocs["sortie"]


def _est_un_programme(upea: str) -> bool:
    """Le fragment, tel quel ou terminé par `;`, passe l'analyse syntaxique."""
    for candidat in (upea, upea + ";"):
        try:
            analyser_syntaxe(candidat)
        except ErreursMultiples:
            continue
        return True
    return False


def test_chaque_equivalence_complete_de_depuis_python_est_un_programme() -> None:
    cellules = re.findall(
        r"^\| `([^`|]*)` \| `([^`|]*)` \|$", aide.texte_depuis_python(), re.MULTILINE
    )
    assert len(cellules) >= 25
    for _python, upea in cellules:
        if "…" in upea:
            continue  # un squelette, pas un programme
        assert _est_un_programme(upea), upea
