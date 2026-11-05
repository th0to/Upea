"""Conseil, lot M1 : une fonction peut s'appeler elle-même 20 000 fois en chaîne.

La limite est relevée une seule fois, dans le prélude : elle vaut pour `run`, pour le
REPL et pour le fichier autonome. Les tests qui exécutent passent par le bac à sable
(un processus neuf, à la limite de Python par défaut tant que le prélude n'a pas
parlé) ou par un sous-processus.
"""

import subprocess
import sys
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
from mcp import Client
from test_conseil_l1_imbrication import TROP_IMBRIQUES

from upea import bac_a_sable
from upea.cli import ERREUR_COMPILATION, OK, main
from upea.compilateur import compiler
from upea.erreurs import ErreursMultiples, ErreurSyntaxe
from upea.execution.base import _PROFONDEUR_MAX
from upea.repl import repl
from upea.serveur_mcp import construire_serveur

RECURSION_PROFONDE = "récursion trop profonde (plus de 20 000 appels imbriqués)"

SOMME = """\
ohipa somme(n) {
    ahani n == 0 { hoi 0; }
    hoi n + somme(n - 1);
}
faaite somme(15000);
"""

#: L'ABR écrit à la main, rempli dans l'ordre : il devient un peigne (GRAPH-01).
ABR_PEIGNE = """\
ohipa inserer(t, v) {
    ahani roa(t.amaa) == 0 { amui(t.amaa, tumu(v)); hoi t; }
    inserer(t.amaa[0], v);
    hoi t;
}
tuu racine = tumu(0);
tataitahi i roto 1..1200 { inserer(racine, i); }
faaite roa(racine);
"""

HAUTEUR = """\
ohipa hauteur(t) {
    ahani roa(t.amaa) == 0 { hoi 0; }
    hoi 1 + hauteur(t.amaa[0]);
}
tuu t = tumu(0);
tuu bout = t;
tataitahi i roto 1..15000 { tuu f = tumu(i); amui(bout.amaa, f); bout = f; }
faaite hauteur(t), teitei(t);
"""

SANS_FIN = "ohipa f(n) { hoi f(n + 1); }\nfaaite f(0);\n"

LISTE_IMBRIQUEE = (
    "tuu l = [];\ntataitahi i roto 0..2000 { l = [l]; }\nfaaite parau(l);\n"
)


def test_la_limite_est_celle_de_la_specification() -> None:
    assert _PROFONDEUR_MAX == 20_000
    assert sys.getrecursionlimit() >= _PROFONDEUR_MAX


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        (SOMME, "112507500\n"),
        (ABR_PEIGNE, "1200\n"),
        (HAUTEUR, "14999 14999\n"),
    ],
    ids=["somme", "abr_peigne", "hauteur"],
)
def test_une_recursion_profonde_reussit(source: str, sortie: str) -> None:
    resultat = bac_a_sable.executer(source, delai=20)
    assert resultat.statut == "succes", resultat.rapport
    assert resultat.sortie == sortie


def test_une_recursion_sans_fin_dit_la_limite() -> None:
    resultat = bac_a_sable.executer(SANS_FIN, delai=20)
    assert resultat.statut == "erreur_execution"
    assert resultat.diagnostics[-1].message == RECURSION_PROFONDE
    assert resultat.diagnostics[-1].ligne == 1


def test_une_liste_trop_imbriquee_garde_son_message() -> None:
    """Ce n'est pas une récursion du programme : « plus de 20 000 appels » y serait
    faux."""
    resultat = bac_a_sable.executer(LISTE_IMBRIQUEE, delai=20)
    assert resultat.statut == "erreur_execution"
    assert resultat.diagnostics[-1].message == "récursion trop profonde"


@pytest.mark.parametrize("prelude", ["inclus", "externe"])
def test_le_fichier_autonome_releve_la_limite(prelude: str, tmp_path: Path) -> None:
    source = tmp_path / "somme.upea"
    source.write_text(SOMME, encoding="utf-8")
    sortie = tmp_path / "somme.py"
    code = main(["transpile", str(source), "-o", str(sortie), "--prelude", prelude])
    assert code == OK
    resultat = subprocess.run(
        [sys.executable, str(sortie)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert resultat.stdout == "112507500\n", resultat.stderr[-2000:]


def test_le_repl_suit_une_recursion_profonde() -> None:
    session = repl()
    next(session)
    for ligne in SOMME.splitlines()[:-1]:
        session.send(ligne)
    assert session.send("faaite somme(15000);").sortie == "112507500\n"


# --- Après la hausse, les programmes trop imbriqués restent des erreurs propres ----


@pytest.mark.parametrize("nom", TROP_IMBRIQUES)
def test_trop_imbrique_reste_une_erreur_de_syntaxe(nom: str) -> None:
    assert sys.getrecursionlimit() >= _PROFONDEUR_MAX
    with pytest.raises(ErreursMultiples) as info:
        compiler(TROP_IMBRIQUES[nom])
    (erreur,) = info.value.erreurs
    assert isinstance(erreur, ErreurSyntaxe)
    assert erreur.message != "programme trop imbriqué pour être compilé"


@pytest.mark.parametrize("nom", ["somme201", "blocs100", "parentheses500", "boucles22"])
def test_trop_imbrique_dans_le_bac_a_sable(nom: str) -> None:
    resultat = bac_a_sable.executer(TROP_IMBRIQUES[nom])
    assert resultat.statut == "erreur_compilation"
    assert resultat.code_retour == ERREUR_COMPILATION


# --- Le serveur MCP, dans son fil de travail, à la limite de 20 000 ---------------


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def client() -> AsyncIterator[Client]:
    async with Client(construire_serveur()) as connecte:
        yield connecte


@pytest.mark.anyio
async def test_le_serveur_mcp_signale_l_imbrication_et_survit(client: Client) -> None:
    assert sys.getrecursionlimit() >= _PROFONDEUR_MAX
    for nom in ("somme201", "somme1000", "blocs100", "parentheses500", "boucles22"):
        source = TROP_IMBRIQUES[nom]
        verification = await client.call_tool("verifier", {"source": source})
        assert not verification.is_error, nom
        assert verification.structured_content is not None
        assert not verification.structured_content["valide"], nom
        (diagnostic,) = verification.structured_content["diagnostics"]
        assert diagnostic["sorte"] == "syntaxe", nom
        execution = await client.call_tool("executer", {"source": source})
        assert not execution.is_error, nom
        assert execution.structured_content is not None
        assert execution.structured_content["statut"] == "erreur_compilation", nom
    # Le serveur répond toujours, et un programme correct s'exécute.
    suivant = await client.call_tool("executer", {"source": SOMME})
    assert suivant.structured_content is not None
    assert suivant.structured_content["statut"] == "succes"
    assert suivant.structured_content["sortie"] == "112507500\n"
    verification = await client.call_tool("verifier", {"source": "faaite 1;"})
    assert verification.structured_content is not None
    assert verification.structured_content["valide"]
