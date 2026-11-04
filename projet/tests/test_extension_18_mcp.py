"""Extension 18 : le serveur MCP (`python -m upea mcp`)."""

import asyncio
import json
import queue
import subprocess
import sys
import threading
import time
from collections.abc import AsyncIterator
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest
from mcp import Client
from mcp.shared.exceptions import MCPError
from mcp.types import CallToolResult, TextContent, TextResourceContents

from outils import EXEMPLES, LISTE_EXEMPLES, PROJET, lire
from upea import atelier, bac_a_sable
from upea.bac_a_sable import Execution
from upea.cli import ERREUR_USAGE, OK, main
from upea.predefinies import PREDEFINIES
from upea.serveur_mcp import TAILLE_MAX_SOURCE, construire_serveur


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    """Un client branché en mémoire sur le serveur."""
    async with Client(construire_serveur()) as connecte:
        yield connecte


def texte(resultat: CallToolResult) -> str:
    """Le texte d'un résultat d'outil, tel que le modèle le lit."""
    return "".join(c.text for c in resultat.content if isinstance(c, TextContent))


def en_json(valeur: object) -> object:
    """Une valeur telle qu'elle passe dans le protocole (les tuples deviennent des
    listes)."""
    return json.loads(json.dumps(valeur))


#: Ce qu'un client envoie pour ouvrir une session (l'ancienne poignée de main, celle
#: des clients d'avant la révision 2026-07-28 du protocole).
INITIALISER: dict[str, object] = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "tests", "version": "0"},
    },
}
INITIALISE: dict[str, object] = {
    "jsonrpc": "2.0",
    "method": "notifications/initialized",
}


#: Le plus long qu'on attende une réponse du serveur, en secondes.
PATIENCE = 60


def dialoguer(
    commande: list[str], messages: list[dict[str, object]]
) -> tuple[list[dict[str, object]], str]:
    """Envoie `messages` à un serveur lancé en stdio, attend la réponse à chaque
    requête, puis ferme son entrée et attend sa fin.

    Fermer l'entrée plus tôt clôt la session, et une requête encore en cours
    resterait sans réponse. Rend les messages lus sur sa sortie (chaque ligne doit
    être un message JSON-RPC) et sa sortie d'erreur.
    """
    attendus = {m["id"] for m in messages if "id" in m}
    serveur = subprocess.Popen(
        commande,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=PROJET,
    )
    sortie, sortie_erreur = serveur.stdout, serveur.stderr
    assert serveur.stdin and sortie and sortie_erreur
    lignes: queue.Queue[bytes] = queue.Queue()
    erreurs: list[bytes] = []

    def lire_la_sortie() -> None:
        for ligne in sortie:
            lignes.put(ligne)

    def lire_les_erreurs() -> None:
        erreurs.append(sortie_erreur.read())

    lecteurs = [
        threading.Thread(target=lire_la_sortie),
        threading.Thread(target=lire_les_erreurs),
    ]
    for lecteur in lecteurs:
        lecteur.start()
    recus: list[dict[str, object]] = []
    try:
        for message in messages:
            serveur.stdin.write(json.dumps(message).encode("utf-8") + b"\n")
        serveur.stdin.flush()
        limite = time.monotonic() + PATIENCE
        while attendus - {r.get("id") for r in recus}:
            restant = limite - time.monotonic()
            recus.append(json.loads(lignes.get(timeout=max(restant, 0.001))))
        serveur.stdin.close()
        serveur.wait(timeout=PATIENCE)
    finally:
        serveur.kill()
        for lecteur in lecteurs:
            lecteur.join(timeout=PATIENCE)
    while not lignes.empty():
        recus.append(json.loads(lignes.get()))
    for recu in recus:
        assert recu["jsonrpc"] == "2.0", recu
    return recus, b"".join(erreurs).decode("utf-8", errors="replace")


# --- La sous-commande -----------------------------------------------------------------


def test_la_sous_commande_est_dans_l_aide(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == OK
    assert "mcp" in capsys.readouterr().out


def test_sans_le_sdk_un_message_clair_et_pas_de_traceback(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # Un module à None dans sys.modules fait échouer son import ; les sous-modules
    # déjà chargés (mcp.server…) seraient sinon trouvés sans passer par `mcp`.
    for nom in [m for m in sys.modules if m.partition(".")[0] == "mcp"]:
        monkeypatch.setitem(sys.modules, nom, None)
    monkeypatch.delitem(sys.modules, "upea.serveur_mcp")
    assert main(["mcp"]) == ERREUR_USAGE
    sortie = capsys.readouterr()
    assert sortie.out == ""
    assert "uv sync --group mcp" in sortie.err
    assert "Traceback" not in sortie.err


def test_le_serveur_se_presente() -> None:
    serveur = construire_serveur()
    assert serveur.name == "upea"
    assert serveur.instructions is not None
    assert "upea://specification" in serveur.instructions


# --- En stdio -------------------------------------------------------------------------


def test_en_stdio_le_serveur_repond_a_initialize() -> None:
    recus, _ = dialoguer(
        [sys.executable, "-m", "upea", "mcp"], [INITIALISER, INITIALISE]
    )
    assert [r.get("id") for r in recus] == [1]
    resultat = recus[0]["result"]
    assert isinstance(resultat, dict)
    assert resultat["serverInfo"]["name"] == "upea"


SERVEUR_BAVARD = """\
import sys
sys.path.insert(0, {projet!r})
from upea.serveur_mcp import construire_serveur

serveur = construire_serveur(proteger_stdout=True)


@serveur.tool()
def bavard() -> str:
    \"\"\"Écrit sur stdout sans vider le tampon.\"\"\"
    print("parasite")
    return "fini"


serveur.run()
"""


def test_un_print_egare_ne_va_pas_sur_stdout(tmp_path: Path) -> None:
    """Le SDK détourne le descripteur 1, mais ce qui reste dans le tampon de
    `sys.stdout` y serait écrit à la fin du processus : `proteger_stdout` l'évite."""
    script = tmp_path / "serveur_bavard.py"
    script.write_text(SERVEUR_BAVARD.format(projet=str(PROJET)), encoding="utf-8")
    appel: dict[str, object] = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "bavard", "arguments": {}},
    }
    recus, erreurs = dialoguer(
        [sys.executable, str(script)], [INITIALISER, INITIALISE, appel]
    )
    assert [r.get("id") for r in recus] == [1, 2]
    assert "parasite" in erreurs


# --- Les outils sans exécution : verifier, formater, transpiler -----------------------


@pytest.mark.anyio
async def test_les_outils_sont_decrits(client: Client) -> None:
    outils = {outil.name: outil for outil in (await client.list_tools()).tools}
    assert {"verifier", "formater", "transpiler"} <= set(outils)
    for nom in ("verifier", "formater", "transpiler"):
        outil = outils[nom]
        assert outil.description and len(outil.description) > 200, nom
        assert "\n    " not in outil.description, nom  # sans l'indentation du code
        assert outil.output_schema is not None, nom  # un résultat structuré
        assert outil.annotations is not None
        assert outil.annotations.read_only_hint
        source = outil.input_schema["properties"]["source"]
        assert "Upea" in source["description"]
    backend = outils["transpiler"].input_schema["properties"]["backend"]
    assert backend["enum"] == ["python", "ast"]


@pytest.mark.anyio
async def test_verifier_rend_des_diagnostics_structures(client: Client) -> None:
    resultat = await client.call_tool("verifier", {"source": "faaite y;"})
    assert not resultat.is_error  # une erreur du programme est un résultat
    attendu = asdict(atelier.verifier("faaite y;"))
    assert resultat.structured_content == en_json(attendu)
    assert resultat.structured_content["diagnostics"] == [
        {
            "sorte": "semantique",
            "ligne": 1,
            "colonne": 8,
            "message": "'y' n'est pas déclaré",
        }
    ]
    assert "n'est pas déclaré" in texte(resultat)


@pytest.mark.anyio
async def test_verifier_sans_types(client: Client) -> None:
    source = 'tuu x: numera = "a"; faaite x;'
    avec = await client.call_tool("verifier", {"source": source})
    sans = await client.call_tool("verifier", {"source": source, "types": False})
    assert avec.structured_content is not None and sans.structured_content is not None
    assert not avec.structured_content["valide"]
    assert sans.structured_content["valide"]


@pytest.mark.anyio
async def test_formater(client: Client) -> None:
    resultat = await client.call_tool("formater", {"source": "tuu   x=1 ;faaite x ;"})
    assert not resultat.is_error
    assert resultat.structured_content is not None
    assert resultat.structured_content["code"] == "tuu x = 1;\nfaaite x;\n"


@pytest.mark.anyio
async def test_transpiler(client: Client) -> None:
    resultat = await client.call_tool(
        "transpiler", {"source": "faaite 1 + 2;", "backend": "ast"}
    )
    assert not resultat.is_error
    assert resultat.structured_content is not None
    code = resultat.structured_content["code"]
    assert code.startswith("from upea_prelude import *\n")
    complet = await client.call_tool(
        "transpiler", {"source": "faaite 1 + 2;", "avec_prelude": True}
    )
    assert complet.structured_content is not None
    assert len(complet.structured_content["code"]) > len(code)


@pytest.mark.anyio
@pytest.mark.parametrize("outil", ["verifier", "formater", "transpiler"])
async def test_un_source_trop_long_est_refuse(client: Client, outil: str) -> None:
    source = "// " + "é" * (TAILLE_MAX_SOURCE // 2) + "\nfaaite 1;\n"
    resultat = await client.call_tool(outil, {"source": source})
    assert resultat.is_error
    assert "source trop longue" in texte(resultat)


@pytest.mark.anyio
async def test_un_backend_inconnu_est_une_erreur_d_outil(client: Client) -> None:
    resultat = await client.call_tool(
        "transpiler", {"source": "faaite 1;", "backend": "formateur"}
    )
    assert resultat.is_error


# --- L'outil executer -----------------------------------------------------------------


@pytest.mark.anyio
async def test_executer_est_decrit(client: Client) -> None:
    outils = {outil.name: outil for outil in (await client.list_tools()).tools}
    outil = outils["executer"]
    assert outil.description and "5 s" in outil.description
    assert outil.output_schema is not None
    assert set(outil.input_schema["properties"]) == {"source", "types", "backend"}


@pytest.mark.anyio
async def test_executer_un_exemple(client: Client) -> None:
    exemple = EXEMPLES / "05_motu.upea"
    resultat = await client.call_tool("executer", {"source": lire(exemple)})
    assert not resultat.is_error
    assert resultat.structured_content is not None
    assert resultat.structured_content["statut"] == "succes"
    assert resultat.structured_content["sortie"] == lire(
        exemple.with_suffix(".attendu")
    )


@pytest.mark.anyio
async def test_executer_une_erreur_d_execution_est_un_resultat(client: Client) -> None:
    source = 'faaite "avant";\nfaaite [1, 2][5];\n'
    resultat = await client.call_tool("executer", {"source": source})
    assert not resultat.is_error
    contenu = resultat.structured_content
    assert contenu is not None
    assert contenu["statut"] == "erreur_execution"
    assert contenu["code_retour"] == 3
    assert contenu["sortie"] == "avant\n"
    assert contenu["diagnostics"] == [
        {
            "sorte": "execution",
            "ligne": 2,
            "colonne": None,
            "message": "indice hors limites",
        }
    ]


@pytest.mark.anyio
async def test_executer_une_boucle_sans_fin_est_une_erreur_d_outil() -> None:
    async with Client(construire_serveur(delai=2)) as client:
        source = 'faaite "début";\ntamau tia { }\n'
        resultat = await client.call_tool("executer", {"source": source})
    assert resultat.is_error
    message = texte(resultat)
    assert "délai de 2 s dépassé" in message
    assert "début" in message  # la fin de ce qu'il avait affiché


@pytest.mark.anyio
async def test_executer_une_sortie_tronquee(client: Client) -> None:
    source = 'tataitahi i roto 0..100000 { faaite "ligne", i; }'
    resultat = await client.call_tool("executer", {"source": source})
    assert resultat.structured_content is not None
    assert resultat.structured_content["tronquee"]
    assert "tronquée" in resultat.structured_content["rapport"]


@pytest.mark.anyio
async def test_executer_un_source_trop_long(client: Client) -> None:
    source = "// " + "x" * TAILLE_MAX_SOURCE
    resultat = await client.call_tool("executer", {"source": source})
    assert resultat.is_error
    assert "source trop longue" in texte(resultat)


@pytest.mark.anyio
async def test_au_plus_deux_executions_a_la_fois(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Les suivantes attendent leur tour, et l'attente ne compte pas dans le délai."""
    verrou = threading.Lock()
    en_cours = 0
    au_plus = 0
    delais: list[float] = []

    def executer_lentement(source: str, **options: Any) -> Execution:
        nonlocal en_cours, au_plus
        with verrou:
            en_cours += 1
            au_plus = max(au_plus, en_cours)
            delais.append(options["delai"])
        time.sleep(0.3)
        with verrou:
            en_cours -= 1
        return Execution("succes", 0, "", False, 0, (), "aucune erreur")

    monkeypatch.setattr(bac_a_sable, "executer", executer_lentement)
    async with Client(construire_serveur(delai=0.5)) as client:
        appels = [
            client.call_tool("executer", {"source": f"faaite {i};"}) for i in range(6)
        ]
        resultats = await asyncio.gather(*appels)
    assert not any(r.is_error for r in resultats)
    assert au_plus == 2
    # Six appels de 0,3 s, deux à la fois : les derniers attendent 0,6 s, plus que le
    # délai de 0,5 s, mais reçoivent le délai entier.
    assert delais == [0.5] * 6


@pytest.mark.anyio
async def test_des_executions_simultanees_reelles(client: Client) -> None:
    appels = [
        client.call_tool("executer", {"source": f"faaite {i} * 2;"}) for i in range(3)
    ]
    resultats = await asyncio.gather(*appels)
    sorties = [
        r.structured_content["sortie"] for r in resultats if r.structured_content
    ]
    assert sorties == ["0\n", "2\n", "4\n"]


# --- Les ressources -------------------------------------------------------------------


async def lire_ressource(client: Client, uri: str) -> str:
    [contenu] = (await client.read_resource(uri)).contents
    assert isinstance(contenu, TextResourceContents)
    return contenu.text


@pytest.mark.anyio
async def test_les_ressources_sont_listees(client: Client) -> None:
    ressources = {str(r.uri): r for r in (await client.list_resources()).resources}
    for uri in ("upea://specification", "upea://exemples", "upea://predefinies"):
        assert uri in ressources
        assert ressources[uri].description, uri
        assert ressources[uri].mime_type == "text/markdown"
    for exemple in LISTE_EXEMPLES:  # chacun aussi en ressource fixe (D8)
        assert f"upea://exemples/{exemple.stem}" in ressources
    gabarits = (await client.list_resource_templates()).resource_templates
    assert [g.uri_template for g in gabarits] == ["upea://exemples/{nom}"]


@pytest.mark.anyio
async def test_la_specification(client: Client) -> None:
    texte_lu = await lire_ressource(client, "upea://specification")
    assert texte_lu == lire(PROJET / "specification.md")


@pytest.mark.anyio
async def test_la_liste_des_exemples(client: Client) -> None:
    liste = await lire_ressource(client, "upea://exemples")
    for exemple in LISTE_EXEMPLES:
        assert f"upea://exemples/{exemple.stem}" in liste
    # La première ligne de commentaire de chaque exemple le décrit.
    assert "Graphes : le littéral upea" in liste


@pytest.mark.anyio
@pytest.mark.parametrize("exemple", LISTE_EXEMPLES, ids=lambda p: p.stem)
async def test_chaque_exemple_et_sa_sortie(client: Client, exemple: Path) -> None:
    texte_lu = await lire_ressource(client, f"upea://exemples/{exemple.stem}")
    assert lire(exemple) in texte_lu
    assert lire(exemple.with_suffix(".attendu")) in texte_lu


@pytest.mark.anyio
async def test_un_exemple_inconnu(client: Client) -> None:
    with pytest.raises(MCPError) as absent:
        await client.read_resource("upea://exemples/99_inconnu")
    assert "01_ia_ora_na" in str(absent.value)  # la liste des noms disponibles


@pytest.mark.anyio
async def test_pas_de_chemin_dans_un_nom_d_exemple(client: Client) -> None:
    with pytest.raises(MCPError):
        await client.read_resource("upea://exemples/..%2Fspecification")


@pytest.mark.anyio
async def test_les_predefinies(client: Client) -> None:
    texte_lu = await lire_ressource(client, "upea://predefinies")
    for nom, predefinie in PREDEFINIES.items():
        assert f"`{predefinie.texte}`" in texte_lu, nom
        assert predefinie.arite() in texte_lu, nom
    assert "`arbre[T]` : `tumu[T] | imi[T]" in texte_lu
