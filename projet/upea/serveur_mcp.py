"""Le serveur MCP d'Upea (extension 18) : `python -m upea mcp`, en stdio.

Il apprend le langage à une IA (spécification, exemples, fonctions prédéfinies) et
lui prête le compilateur pour vérifier, exécuter et corriger ce qu'elle écrit. Seul
module à dépendre du SDK `mcp` (groupe de dépendances facultatif) : la CLI ne
l'importe qu'à la demande.

Sur stdio, la sortie standard est le canal du protocole : rien d'autre que le
JSON-RPC ne doit y être écrit. Les diagnostics vont sur la sortie d'erreur.
"""

from __future__ import annotations

import sys
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from mcp.server import MCPServer

NOM = "upea"

INSTRUCTIONS = """\
Upea est un petit langage impératif aux mots-clés tahitiens (tuu, ohipa, ahani, \
tataitahi, faaite…), où les arbres (tumu) et les graphes (upea) sont des valeurs de \
première classe. Il est transpilé en Python 3.12. Tu ne le connais pas encore : \
avant d'écrire du code Upea, lis la ressource upea://specification, et consulte \
upea://predefinies et les exemples (upea://exemples). Puis écris le programme, \
vérifie-le avec l'outil verifier, corrige-le jusqu'à ce qu'il n'ait plus d'erreur, \
et exécute-le avec executer."""


@asynccontextmanager
async def _stdout_vers_stderr(_: MCPServer[None]) -> AsyncIterator[None]:
    """Pendant le service, `print` écrit sur la sortie d'erreur.

    Le transport stdio du SDK a déjà pris pour lui le descripteur 1 quand ce
    contexte s'ouvre ; mais ce qui resterait dans le tampon de `sys.stdout` serait
    écrit sur le canal du protocole à la fin du processus.
    """
    sortie = sys.stdout
    sys.stdout = sys.stderr
    try:
        yield
    finally:
        sys.stdout = sortie


def construire_serveur(*, proteger_stdout: bool = False) -> MCPServer[None]:
    """Le serveur, avec ses outils, ses ressources et ses prompts.

    Construit à la demande, pas à l'import : le SDK configure la journalisation dès
    la création du serveur. `proteger_stdout` est pour le service en stdio.
    """
    return MCPServer(
        NOM,
        title="Upea",
        description="Le langage Upea : sa spécification, et son compilateur.",
        instructions=INSTRUCTIONS,
        lifespan=_stdout_vers_stderr if proteger_stdout else None,
    )


def lancer() -> int:
    """Sert jusqu'à la fin de l'entrée standard (ou Ctrl-C)."""
    with suppress(KeyboardInterrupt):
        construire_serveur(proteger_stdout=True).run()
    return 0
