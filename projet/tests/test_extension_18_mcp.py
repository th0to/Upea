"""Extension 18 : le serveur MCP (`python -m upea mcp`)."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

from outils import PROJET
from upea.cli import ERREUR_USAGE, OK, main
from upea.serveur_mcp import construire_serveur

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


def dialoguer(
    commande: list[str], messages: list[dict[str, object]]
) -> tuple[list[dict[str, object]], str]:
    """Envoie `messages` à un serveur lancé en stdio, ferme son entrée et attend sa fin.

    Rend les messages lus sur sa sortie (chaque ligne doit être un message JSON-RPC)
    et sa sortie d'erreur.
    """
    entree = "".join(json.dumps(m, ensure_ascii=False) + "\n" for m in messages)
    fini = subprocess.run(
        commande,
        input=entree.encode("utf-8"),
        capture_output=True,
        cwd=PROJET,
        timeout=60,
    )
    lignes = fini.stdout.decode("utf-8").splitlines()
    recus = [json.loads(ligne) for ligne in lignes]
    for recu in recus:
        assert recu["jsonrpc"] == "2.0", recu
    return recus, fini.stderr.decode("utf-8", errors="replace")


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
