"""Le serveur MCP d'Upea (extension 18) : `python -m upea mcp`, en stdio.

Il apprend le langage à une IA (spécification, exemples, fonctions prédéfinies) et
lui prête le compilateur pour vérifier, exécuter et corriger ce qu'elle écrit. Seul
module à dépendre du SDK `mcp` (groupe de dépendances facultatif) : la CLI ne
l'importe qu'à la demande.

Sur stdio, la sortie standard est le canal du protocole : rien d'autre que le
JSON-RPC ne doit y être écrit. Les diagnostics vont sur la sortie d'erreur.
"""

from __future__ import annotations

import inspect
import sys
import threading
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from typing import Annotated, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import atelier, bac_a_sable

NOM = "upea"

#: La taille maximale d'un source reçu par un outil (en octets UTF-8).
TAILLE_MAX_SOURCE = 100 * 1024
#: Le nombre d'exécutions simultanées ; les suivantes attendent leur tour.
EXECUTIONS_SIMULTANEES = 2
#: Ce qu'un délai dépassé montre au plus de la sortie du programme (en caractères).
FIN_DE_SORTIE = 2000

# Les arguments des outils, et leur description pour le modèle.
Source = Annotated[
    str,
    Field(
        description=(
            "Le programme Upea complet, tel qu'il serait écrit dans un fichier "
            f".upea (au plus {TAILLE_MAX_SOURCE // 1024} Kio)."
        )
    ),
]
Types = Annotated[
    bool,
    Field(
        description=(
            "Vérifier aussi les types (typage graduel). false seulement pour voir ce "
            "qu'un programme mal typé ferait à l'exécution."
        )
    ),
]
Backend = Annotated[
    Literal["python", "ast"],
    Field(
        description=(
            'Le générateur de Python : "python" (le texte, par défaut) ou "ast" (le '
            "module ast de Python) ; les deux produisent le même programme."
        )
    ),
]
AvecPrelude = Annotated[
    bool,
    Field(
        description=(
            "Recopier le prélude (environ 2 500 lignes) en tête du code, pour un "
            "fichier Python autonome."
        )
    ),
]

#: Ni effet de bord, ni accès au monde extérieur : le client peut appeler sans crainte.
SANS_EFFET = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, open_world_hint=False
)

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


def construire_serveur(
    *, proteger_stdout: bool = False, delai: float = bac_a_sable.DELAI
) -> MCPServer[None]:
    """Le serveur, avec ses outils, ses ressources et ses prompts.

    Construit à la demande, pas à l'import : le SDK configure la journalisation dès
    la création du serveur. `proteger_stdout` est pour le service en stdio, `delai`
    celui de chaque exécution (attente de son tour non comprise).
    """
    serveur = MCPServer(
        NOM,
        title="Upea",
        description="Le langage Upea : sa spécification, et son compilateur.",
        instructions=INSTRUCTIONS,
        lifespan=_stdout_vers_stderr if proteger_stdout else None,
    )
    _outils_sans_execution(serveur)
    _outil_executer(serveur, delai)
    return serveur


def _limiter(source: str) -> None:
    """Refuse un source trop long : c'est une panne de l'outil, pas du programme."""
    taille = len(source.encode("utf-8"))
    if taille > TAILLE_MAX_SOURCE:
        raise ToolError(
            f"source trop longue : {taille} octets en UTF-8, au plus "
            f"{TAILLE_MAX_SOURCE} ; raccourcis le programme"
        )


# --- Les outils -----------------------------------------------------------------------
# Leur docstring est la description que lit le modèle : elle dit quand s'en servir,
# ce qu'ils rendent, et leurs pièges.


def _outil[F: Callable[..., object]](
    serveur: MCPServer[None], titre: str, annotations: ToolAnnotations = SANS_EFFET
) -> Callable[[F], F]:
    """`serveur.tool`, avec la docstring sans son indentation pour description."""

    def enregistrer(fonction: F) -> F:
        description = inspect.cleandoc(fonction.__doc__ or "")
        decorer = serveur.tool(
            title=titre, description=description, annotations=annotations
        )
        return decorer(fonction)

    return enregistrer


def _outils_sans_execution(serveur: MCPServer[None]) -> None:
    @_outil(serveur, "Vérifier un programme Upea")
    def verifier(source: Source, types: Types = True) -> atelier.Verification:
        """Vérifie un programme Upea sans l'exécuter : analyse lexicale, syntaxique,
        sémantique et (par défaut) vérification des types.

        Quand s'en servir : après chaque écriture ou modification d'un programme, et
        avant executer, jusqu'à ce que `valide` soit vrai. C'est rapide et sans effet.

        Résultat :
        - `valide` : vrai s'il n'y a aucune erreur (il peut rester des avertissements) ;
        - `diagnostics` : des objets {sorte, ligne, colonne, message}, où sorte vaut
          "lexicale", "syntaxe", "semantique", "type" ou "avertissement" ; ligne et
          colonne comptent à partir de 1 (null si inconnues) ;
        - `rapport` : les mêmes, mis en forme comme par le compilateur, avec la
          ligne fautive et un ^ sous la colonne.

        Une erreur du programme n'est pas une panne de l'outil : lis les
        diagnostics, corrige le programme, et vérifie-le de nouveau. Toutes les
        erreurs d'une phase sont signalées en une fois, la syntaxe d'abord, puis les
        noms et les types : une fois la syntaxe corrigée, d'autres erreurs peuvent
        apparaître. Les avertissements (variable jamais utilisée, code placé après
        hoi, faaea ou haere) ne sont signalés que pour un programme sans erreur.
        """
        _limiter(source)
        return atelier.verifier(source, types=types)

    @_outil(serveur, "Formater un programme Upea")
    def formater(source: Source) -> atelier.Formatage:
        """Réécrit un programme Upea dans sa présentation canonique (indentation,
        espaces, une instruction par ligne), sans en changer le sens.

        Quand s'en servir : pour rendre lisible un programme avant de le montrer.
        Attention : les commentaires (// et /* */) sont perdus, car ils ne font pas
        partie de l'arbre syntaxique ; ne formate pas un programme dont les
        commentaires comptent.

        Seule la syntaxe est analysée, pas les noms ni les types. Résultat : `code`,
        le programme réécrit (null s'il a des erreurs de syntaxe), et `diagnostics`
        et `rapport` comme pour verifier.
        """
        _limiter(source)
        return atelier.formater(source)

    @_outil(serveur, "Voir le Python produit par Upea")
    def transpiler(
        source: Source, backend: Backend = "python", avec_prelude: AvecPrelude = False
    ) -> atelier.Transpilation:
        """Montre le Python 3.12 qu'Upea produit pour un programme, sans l'exécuter.

        Quand s'en servir : pour comprendre ce que devient une construction d'Upea,
        ou pour livrer un programme sous forme de Python. Inutile pour vérifier ou
        exécuter un programme : verifier et executer le font directement.

        Par défaut, le code n'inclut pas le prélude (environ 2 500 lignes : arbres,
        graphes, algorithmes et fonctions prédéfinies, dont les noms Python
        commencent par _) : il commence par `from upea_prelude import *`, et ne se
        lance qu'à côté d'un fichier upea_prelude.py. Avec avec_prelude=true, le
        prélude est recopié en tête, et le code se lance seul.

        Résultat : `code` (null si le programme a des erreurs), et `diagnostics` et
        `rapport` comme pour verifier.
        """
        _limiter(source)
        return atelier.transpiler(source, backend, avec_prelude=avec_prelude)


def _outil_executer(serveur: MCPServer[None], delai: float) -> None:
    # Le SDK appelle un outil synchrone dans un fil de travail : un sémaphore de
    # fils suffit. On attend son tour avant de lancer l'enfant, et le délai ne
    # court qu'à partir de son lancement.
    places = threading.BoundedSemaphore(EXECUTIONS_SIMULTANEES)

    @_outil(serveur, "Exécuter un programme Upea")
    def executer(
        source: Source, types: Types = True, backend: Backend = "python"
    ) -> bac_a_sable.Execution:
        """Exécute un programme Upea et rend ce qu'il a affiché.

        Quand s'en servir : une fois le programme passé par verifier sans erreur,
        pour voir sa sortie et la comparer à ce qui est attendu. Le programme tourne
        dans un processus séparé, avec au plus 5 s (démarrage compris), 512 Mo de
        mémoire, et 64 Kio de sortie gardés. Un programme Upea ne lit ni clavier,
        ni fichier, ni réseau : il ne peut qu'afficher (faaite).

        Résultat :
        - `statut` : "succes", "erreur_compilation" ou "erreur_execution" ;
        - `code_retour` : 0, 1 (compilation) ou 3 (exécution), comme la commande
          `python -m upea run` ;
        - `sortie` : ce que le programme a affiché, même s'il s'est arrêté sur une
          erreur ;
        - `tronquee` et `octets` : la sortie dépassait 64 Kio, et sa taille entière ;
        - `diagnostics` et `rapport` comme pour verifier : les avertissements, puis
          l'erreur éventuelle. Une erreur d'exécution donne sa ligne Upea (sa
          colonne est inconnue) et un message en termes d'Upea, par exemple
          « indice hors limites » ou « mémoire dépassée ».

        Une erreur de compilation ou d'exécution n'est pas une panne de l'outil :
        c'est un résultat à lire pour corriger le programme. L'outil échoue
        seulement si le programme dépasse son délai (une boucle sans fin, le plus
        souvent : le message montre la fin de ce qu'il avait affiché) ou si le
        source est trop long.
        """
        _limiter(source)
        with places:
            try:
                return bac_a_sable.executer(
                    source, types=types, backend=backend, delai=delai
                )
            except bac_a_sable.DelaiDepasse as arret:
                raise ToolError(_delai_depasse(arret)) from None
            except bac_a_sable.PanneDuBacASable as panne:
                raise ToolError(str(panne)) from None


def _delai_depasse(arret: bac_a_sable.DelaiDepasse) -> str:
    """Le message d'un délai dépassé, avec la fin de ce que le programme a affiché."""
    if not arret.sortie:
        return f"{arret} ; il n'avait rien affiché"
    fin = arret.sortie[-FIN_DE_SORTIE:]
    coupe = "…" if len(fin) < len(arret.sortie) else ""
    return f"{arret} ; la fin de ce qu'il avait affiché :\n{coupe}{fin}"


def lancer() -> int:
    """Sert jusqu'à la fin de l'entrée standard (ou Ctrl-C)."""
    with suppress(KeyboardInterrupt):
        construire_serveur(proteger_stdout=True).run()
    return 0
