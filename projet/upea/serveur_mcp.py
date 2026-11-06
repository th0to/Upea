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
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp.types import ToolAnnotations
from pydantic import Field

from . import aide, atelier, bac_a_sable

NOM = "upea"

MARKDOWN = "text/markdown"

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
#: Le délai le plus court qu'on puisse demander à `executer`. Le démarrage de Python
#: en prend déjà une demi-seconde environ : un délai si court arrête presque tout.
DELAI_MINIMAL = 0.1
Delai = Annotated[
    float,
    Field(
        ge=DELAI_MINIMAL,
        le=bac_a_sable.DELAI,
        description=(
            "La durée maximale de l'exécution, en secondes, démarrage de Python "
            f"compris (une demi-seconde environ) : de {DELAI_MINIMAL:g} à "
            f"{bac_a_sable.DELAI:g}."
        ),
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
et exécute-le avec executer. Pour comprendre une erreur lexicale ou de syntaxe, \
tokenize montre les tokens du programme, et parse son arbre syntaxique."""


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
    le plus long que puisse demander chaque exécution (attente de son tour non
    comprise) : les tests le raccourcissent.
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
    _ressources(serveur)
    _prompts(serveur)
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
    @_outil(serveur, "Découper un programme Upea en tokens")
    def tokenize(source: Source) -> atelier.Decoupage:
        """Découpe un programme Upea en tokens (l'analyse lexicale seule), sans
        l'exécuter.

        Quand s'en servir : pour comprendre une erreur lexicale, ou pour voir comment
        le compilateur lit un passage (un mot-clé, un nombre, un texte). Pour
        vérifier un programme, verifier suffit.

        Résultat :
        - `valide` : vrai s'il n'y a aucune erreur lexicale ;
        - `jetons` : des objets {sorte, texte, ligne, colonne}, dans l'ordre du
          source ; sorte est le nom du token (TUU, IDENT, ENTIER, TEXTE,
          POINT_VIRGULE…), et le dernier est toujours FIN. Le texte d'un TEXTE est sa
          valeur, sans guillemets. Sur une erreur lexicale, ce sont les tokens lus
          avant elle ;
        - `diagnostics` et `rapport` comme pour verifier.

        Les espaces et les commentaires ne donnent pas de token.
        """
        _limiter(source)
        return atelier.decouper(source)

    @_outil(serveur, "Voir l'arbre syntaxique d'un programme Upea")
    def parse(source: Source) -> atelier.AnalyseSyntaxique:
        """Analyse la syntaxe d'un programme Upea et rend son arbre syntaxique, sans
        analyser les noms ni les types, et sans l'exécuter.

        Quand s'en servir : pour comprendre comment le compilateur lit une
        construction (la priorité des opérateurs, par exemple), ou pour voir toutes
        les erreurs de syntaxe d'un coup. Un programme accepté par parse peut encore
        être refusé par verifier (un nom non déclaré, un type faux) : c'est verifier
        qu'il faut appeler avant executer.

        Résultat :
        - `valide` : vrai s'il n'y a aucune erreur lexicale ni de syntaxe ;
        - `arbre` : l'arbre (null s'il y a des erreurs). Chaque nœud est un objet
          dont la clé `type` nomme la construction (Programme, Declaration, Affiche,
          Binaire, Variable…), suivie de ses champs, puis de `ligne` et `colonne`
          quand elles sont connues ;
        - `diagnostics` et `rapport` comme pour verifier.
        """
        _limiter(source)
        return atelier.analyser_syntaxe(source)

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


def _outil_executer(serveur: MCPServer[None], delai_maximal: float) -> None:
    # Le SDK appelle un outil synchrone dans un fil de travail : un sémaphore de
    # fils suffit. On attend son tour avant de lancer l'enfant, et le délai ne
    # court qu'à partir de son lancement. `delai_maximal` est celui du serveur : le
    # délai demandé ne le dépasse jamais.
    places = threading.BoundedSemaphore(EXECUTIONS_SIMULTANEES)

    @_outil(serveur, "Exécuter un programme Upea")
    def executer(
        source: Source,
        types: Types = True,
        backend: Backend = "python",
        delai: Delai = bac_a_sable.DELAI,
    ) -> bac_a_sable.Execution:
        """Exécute un programme Upea et rend ce qu'il a affiché.

        Quand s'en servir : une fois le programme passé par verifier sans erreur,
        pour voir sa sortie et la comparer à ce qui est attendu. Le programme tourne
        dans un processus séparé, avec au plus `delai` secondes (5 s par défaut, et
        5 s au plus ; démarrage compris), 512 Mo de mémoire, et 64 Kio de sortie
        gardés. Un programme Upea ne lit ni clavier, ni fichier, ni réseau : il ne
        peut qu'afficher (faaite).

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
                    source,
                    types=types,
                    backend=backend,
                    delai=min(delai, delai_maximal),
                )
            except bac_a_sable.DelaiDepasse as arret:
                raise ToolError(_delai_depasse(arret)) from None
            except bac_a_sable.PanneDuBacASable as panne:
                raise ToolError(str(panne)) from None


def _ressources(serveur: MCPServer[None]) -> None:
    def ressource[F: Callable[..., object]](uri: str, titre: str) -> Callable[[F], F]:
        """`serveur.resource` en Markdown, décrite par la docstring."""

        def enregistrer(fonction: F) -> F:
            description = inspect.cleandoc(fonction.__doc__ or "")
            decorer = serveur.resource(
                uri, title=titre, description=description, mime_type=MARKDOWN
            )
            return decorer(fonction)

        return enregistrer

    @ressource("upea://specification", "Spécification d'Upea")
    def specification() -> str:
        """La spécification complète du langage Upea : vocabulaire tahitien,
        grammaire, sémantique, types, fonctions prédéfinies, algorithmes d'arbres et
        de graphes, dessins, messages d'erreur. À lire en entier avant d'écrire le
        moindre programme Upea : le langage ne ressemble à aucun autre."""
        return aide.texte_specification("tout")

    @ressource("upea://exemples", "Exemples de programmes Upea")
    def exemples() -> str:
        """La liste des programmes d'exemple, chacun avec ce qu'il montre. Chaque
        exemple se lit à upea://exemples/<nom>, avec sa sortie exacte."""
        lignes = [
            f"- `upea://exemples/{nom}` : {aide.description_exemple(chemin)}"
            for nom, chemin in aide.exemples_disponibles().items()
        ]
        return (
            "# Les exemples d'Upea\n\n"
            "Des programmes complets, chacun avec sa sortie exacte. Pour en lire un : "
            "`upea://exemples/<nom>`.\n\n" + "\n".join(lignes) + "\n"
        )

    @ressource("upea://exemples/{nom}", "Un exemple de programme Upea")
    def exemple(nom: str) -> str:
        """Un programme d'exemple complet (01_ia_ora_na, 05_motu…), et la sortie
        exacte qu'il affiche. La liste des noms est dans upea://exemples."""
        return _exemple(nom)

    # Chaque exemple est aussi une ressource fixe : un client les liste ainsi.
    for nom, chemin in aide.exemples_disponibles().items():
        serveur.resource(
            f"upea://exemples/{nom}",
            name=f"exemple_{nom}",
            title=f"Exemple {nom}",
            description=aide.description_exemple(chemin),
            mime_type=MARKDOWN,
        )(_lecteur(nom))

    @ressource("upea://predefinies", "Fonctions prédéfinies d'Upea")
    def predefinies() -> str:
        """Toutes les fonctions prédéfinies d'Upea (roa, amui, tumu, pihai, ea,
        dijkstra, hohoa…), avec leur nombre d'arguments et leur signature typée,
        tirées du compilateur lui-même. À consulter pour savoir quelle fonction
        existe et ce qu'elle accepte."""
        return aide.texte_predefinies()


def _exemple(nom: str) -> str:
    """Un exemple pour la ressource : un nom inconnu est une ressource introuvable."""
    try:
        return aide.exemple(nom)
    except aide.AideInconnue as inconnu:
        raise ResourceNotFoundError(str(inconnu)) from None


def _lecteur(nom: str) -> Callable[[], str]:
    """La fonction, sans paramètre, qui lit l'exemple `nom`."""

    def lire() -> str:
        return _exemple(nom)

    return lire


# --- Les prompts ----------------------------------------------------------------------

Tache = Annotated[
    str,
    Field(
        description=(
            "Ce que le programme doit faire, en langage courant (par exemple : "
            "« le plus court trajet entre deux îles d'un graphe pondéré »)."
        )
    ),
]
CodePython = Annotated[str, Field(description="Le programme Python complet.")]
SourceACorriger = Annotated[
    str, Field(description="Le programme Upea à corriger, en entier.")
]
ErreursRecues = Annotated[
    str,
    Field(
        description=(
            "Les erreurs reçues, telles quelles : le rapport de verifier ou "
            "d'executer, ou ce qui ne va pas dans la sortie."
        )
    ),
]

#: La démarche commune aux prompts : apprendre, écrire, vérifier, exécuter.
DEMARCHE = """\
Upea est un langage aux mots-clés tahitiens que tu ne connais pas : ne devine pas \
sa syntaxe. Procède ainsi :

1. Lis la ressource upea://specification en entier. Consulte upea://predefinies \
pour les fonctions disponibles, et un exemple proche dans upea://exemples (chacun \
avec sa sortie exacte).
2. Écris le programme complet.
3. Passe-le à l'outil verifier. Tant que `valide` est faux, corrige chaque erreur \
à la ligne et à la colonne indiquées, puis vérifie de nouveau. Tiens compte aussi \
des avertissements.
4. Exécute-le avec l'outil executer. Si le statut est une erreur, ou si la sortie \
n'est pas celle attendue, corrige le programme et reprends à l'étape 3. Si l'outil \
signale un délai dépassé, cherche une boucle qui ne se termine pas.
5. Donne le programme final dans un bloc de code, puis la sortie que l'outil \
executer a réellement produite.
"""

#: Ce qui change le plus quand on passe de Python à Upea.
PIEGES_DE_PYTHON = """\
Les pièges d'une traduction depuis Python :
- toute variable se déclare avant usage, une seule fois, avec `tuu` (ou `mau` pour \
une constante) ; on ne redéclare pas un nom encore visible ;
- les instructions finissent par `;` et les blocs sont entre accolades ; \
l'indentation ne compte pas ;
- pas de dictionnaires, ni de fonctions imbriquées, ni de fonctions comme valeurs, \
ni de récursion croisée ; une fonction (`ohipa`) se déclare au niveau global, avant \
son premier appel ;
- les comparaisons ne s'enchaînent pas : `a < b ma b < c` au lieu de `a < b < c` ;
- `ma`, `anei`, `eiaha` pour and, or, not ; `tia`, `hape`, `aore` pour True, False, \
None ;
- `for i in range(a, b)` devient `tataitahi i roto a..b`, `len(x)` devient \
`roa(x)`, `l.append(x)` devient `amui(l, x)` ;
- `faaite a, b;` affiche comme `print(a, b)` ; `"a" + parau(1)` pour coller un \
nombre à un texte ;
- un programme Upea ne lit ni clavier ni fichier : remplace les entrées par des \
valeurs écrites dans le programme, et dis-le ;
- pour un arbre ou un graphe, préfère les structures et les algorithmes d'Upea \
(`upea { "A" -> "B" : 3 }`, `tumu`, `aifaito`, `dijkstra`, `bfs`…) à une \
réimplémentation avec des listes.
"""


def _prompts(serveur: MCPServer[None]) -> None:
    def prompt[F: Callable[..., object]](titre: str) -> Callable[[F], F]:
        """`serveur.prompt`, décrit par la docstring."""

        def enregistrer(fonction: F) -> F:
            description = inspect.cleandoc(fonction.__doc__ or "")
            return serveur.prompt(title=titre, description=description)(fonction)

        return enregistrer

    @prompt("Écrire un programme Upea")
    def ecrire_programme(tache: Tache) -> str:
        """Écrire un programme Upea qui accomplit une tâche, en apprenant le langage
        dans la spécification, puis en le vérifiant (verifier) et en l'exécutant
        (executer) jusqu'à ce qu'il soit juste."""
        return f"Écris un programme Upea qui fait ceci :\n\n{tache}\n\n{DEMARCHE}"

    @prompt("Traduire un programme Python en Upea")
    def traduire_depuis_python(code: CodePython) -> str:
        """Traduire un programme Python en Upea, qui affiche la même chose, en
        apprenant le langage dans la spécification, puis en le vérifiant (verifier)
        et en l'exécutant (executer) jusqu'à ce qu'il soit juste."""
        fin = "" if code.endswith("\n") else "\n"
        return (
            "Traduis ce programme Python en Upea, en gardant ce qu'il affiche :\n\n"
            f"```python\n{code}{fin}```\n\n{DEMARCHE}\n{PIEGES_DE_PYTHON}\n"
            "À l'étape 4, compare la sortie à celle du programme Python."
        )

    @prompt("Corriger un programme Upea")
    def corriger_programme(source: SourceACorriger, erreurs: ErreursRecues) -> str:
        """Corriger un programme Upea d'après les erreurs reçues, en apprenant le
        langage dans la spécification, puis en le vérifiant (verifier) et en
        l'exécutant (executer) jusqu'à ce qu'il soit juste."""
        fin = "" if source.endswith("\n") else "\n"
        fin_erreurs = "" if erreurs.endswith("\n") else "\n"
        return (
            "Corrige ce programme Upea :\n\n"
            f"```upea\n{source}{fin}```\n\n"
            f"Voici les erreurs reçues :\n\n```text\n{erreurs}{fin_erreurs}```\n\n"
            "Chaque erreur donne sa ligne et, quand elle est connue, sa colonne. "
            "Corrige-les toutes, sans changer ce que le programme doit faire. À "
            "l'étape 2, écris le programme corrigé en entier.\n\n"
            f"{DEMARCHE}"
        )


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
