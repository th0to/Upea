"""Les fonctions prédéfinies d'Upea, vues du compilateur : arité et typage.

Leur code d'exécution est dans le paquet `execution`, sous le même nom préfixé de
`_`. La plupart des signatures s'écrivent en une ligne avec des **patrons** : un
patron vérifie un argument, et peut lier le type `T` des éléments (les nœuds d'un
graphe, les clés d'un arbre) que les arguments suivants et le résultat réutilisent.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .typage import (
    AORE,
    ARBRES,
    INCONNU,
    NUMERA,
    ORDONNES,
    PARAU,
    TIAHAPE,
    TUHAA,
    Base,
    Compose,
    NomCompose,
    Type,
    commun_de,
    compatible,
    element,
    element_de,
    est_nombre,
    tapura,
    tumu,
    upea,
)

#: Signale une erreur de type sur l'argument d'indice donné.
type Signaler = Callable[[int, str], None]
type Typeur = Callable[[tuple[Type, ...], Signaler], Type]


@dataclass(frozen=True, slots=True)
class Predefinie:
    """Une fonction prédéfinie, vue du compilateur : son nombre d'arguments (de
    `minimum` à `maximum`), le typeur qui calcule son type de retour et
    signale les arguments mal typés, et sa signature lisible."""

    nom: str
    minimum: int
    maximum: int | None  # None : autant qu'on veut
    typer: Typeur
    texte: str  # la signature lisible : `pihai(upea[T], T) -> tapura[T]`

    def arite(self) -> str:
        """« 1 argument », « 3 ou 4 arguments », « au moins 1 argument »."""

        def pluriel(n: int) -> str:
            return f"{n} argument{'s' if n > 1 else ''}"

        if self.maximum is None:
            return f"au moins {pluriel(self.minimum)}"
        if self.maximum == self.minimum:
            return pluriel(self.minimum)
        return f"{self.minimum} ou {pluriel(self.maximum)}"


PREDEFINIES: dict[str, Predefinie] = {}

#: Les sortes abrégées dans les signatures, et ce qu'elles recouvrent :
#: `arbre[T]` vaut `tumu[T] | imi[T] | …`. Rempli par `lie`.
ABREVIATIONS: dict[str, str] = {}


def predefinie(
    nom: str, minimum: int, maximum: int | None = -1, *, texte: str
) -> Callable[[Typeur], Typeur]:
    """Enregistre un typeur écrit à la main (maximum par défaut = minimum) ; `texte`
    est sa signature lisible, que rien ne permet de calculer."""

    def enregistrer(typer: Typeur) -> Typeur:
        PREDEFINIES[nom] = Predefinie(
            nom, minimum, minimum if maximum == -1 else maximum, typer, texte
        )
        return typer

    return enregistrer


# --- Les patrons ----------------------------------------------------------------------


@dataclass(slots=True)
class Liaison:
    """Le type `T` lié par un patron, et réutilisé par les suivants."""

    element: Type = field(default=INCONNU)


@dataclass(frozen=True, slots=True)
class Patron:
    """Vérifie un argument ; rend un message d'erreur, ou `None` s'il convient.

    `texte` décrit l'argument dans la signature lisible (`upea[T]`, `T`…).
    """

    texte: str
    verifier: Callable[[Type, Liaison], str | None]

    def __call__(self, recu: Type, liaison: Liaison) -> str | None:
        """Vérifie `recu` ; rend un message d'erreur, ou `None` s'il convient."""
        return self.verifier(recu, liaison)


def lie(
    noms: tuple[NomCompose, ...], description: str, abrege: str | None = None
) -> Patron:
    """Un patron qui accepte les sortes `noms` et lie leur paramètre à `T`.

    Dans les signatures, plusieurs sortes s'écrivent sous le nom `abrege`.
    """

    def patron(recu: Type, liaison: Liaison) -> str | None:
        contenu = element_de(recu, noms)
        if contenu is None:
            return f"{description} attendu, {recu} reçu"
        liaison.element = contenu
        return None

    texte = f"{abrege or noms[0]}[T]"
    if len(noms) > 1:
        ABREVIATIONS[texte] = " | ".join(f"{nom}[T]" for nom in noms)
    return Patron(texte, patron)


def comme_t(description: str) -> Patron:
    """Un patron qui exige une valeur compatible avec le `T` déjà lié."""
    return Patron(
        "T",
        lambda recu, liaison: (
            None
            if compatible(liaison.element, recu)
            else f"{description} {liaison.element} attendu, {recu} reçu"
        ),
    )


def si(
    condition: Callable[[Type], bool], message: Callable[[Type], str], texte: str
) -> Patron:
    """Un patron qui accepte les types vérifiant `condition`."""
    return Patron(
        texte,
        lambda recu, _: None if condition(recu) or recu is INCONNU else message(recu),
    )


_LISTE_OU_ORDONNE: tuple[NomCompose, ...] = ("tapura", *ORDONNES)
_RETIRABLES: tuple[NomCompose, ...] = ("tapura", "upea", *ORDONNES)
_STRUCTURES: tuple[NomCompose, ...] = ("upea", *ARBRES)

GRAPHE = lie(("upea",), "upea")
ARBRE = lie(ARBRES, "arbre", "arbre")
ORDONNE = lie(ORDONNES, "arbre ordonné (imi, aifaito, uteere, pupu, ahu)", "ordonne")
COLLECTION = lie(_LISTE_OU_ORDONNE, "tapura ou arbre ordonné", "collection")
RETIRABLE = lie(_RETIRABLES, "tapura, upea ou arbre ordonné", "retirable")
AJOUTABLE = lie(_RETIRABLES, "tapura, upea ou arbre ordonné", "ajoutable")
STRUCTURE = lie(_STRUCTURES, "arbre ou upea", "structure")
NOEUD = comme_t("nœud")
VALEUR = comme_t("élément")
NOMBRE = si(
    est_nombre, lambda t: f"le poids doit être un nombre, pas un {t}", "numera | tuhaa"
)
#: Un patron qui accepte tout.
TOUT = Patron("?", lambda recu, liaison: None)


def signature(
    nom: str, *patrons: Patron, retour: Callable[[Type], Type], optionnels: int = 0
) -> None:
    """Déclare une prédéfinie par ses patrons ; `retour` reçoit le `T` lié."""

    def typer(arguments: tuple[Type, ...], signaler: Signaler) -> Type:
        liaison = Liaison()
        for i, (patron, recu) in enumerate(zip(patrons, arguments, strict=False)):
            if (message := patron(recu, liaison)) is not None:
                signaler(i, f"{nom} : {message}")
        return retour(liaison.element)

    minimum = len(patrons) - optionnels
    obligatoires = ", ".join(p.texte for p in patrons[:minimum])
    facultatifs = "".join(f"[, {p.texte}" for p in patrons[minimum:]) + "]" * optionnels
    texte = f"{nom}({obligatoires}{facultatifs}) -> {_retour_lisible(retour)}"
    PREDEFINIES[nom] = Predefinie(nom, minimum, len(patrons), typer, texte)


def _retour_lisible(retour: Callable[[Type], Type]) -> str:
    """Le type de retour, sondé : `T` là où il dépend du type lié par les patrons,
    `?` s'il est inconnu du vérificateur."""
    if retour(NUMERA) == retour(PARAU):  # ne dépend pas de T
        return str(retour(INCONNU))
    return str(retour(INCONNU)).replace(str(INCONNU), "T")


def fixe(resultat: Type) -> Callable[[Type], Type]:
    """Un type de retour qui ne dépend pas de `T`."""
    return lambda _: resultat


def identite(t: Type) -> Type:
    """Un type de retour égal au type `T` lié par les patrons."""
    return t


# --- Les fonctions écrites à la main ------------------------------------------------


@predefinie("roa", 1, texte="roa(tapura[T] | parau | upea[T] | arbre[T]) -> numera")
def _roa(args: tuple[Type, ...], signaler: Signaler) -> Type:
    t = args[0]
    if not (t in (PARAU, INCONNU) or isinstance(t, Compose)):
        signaler(0, f"roa : tapura, parau, upea ou arbre attendu, {t} reçu")
    return NUMERA


def _conversion(nom: str, resultat: Base, acceptes: tuple[Base, ...]) -> None:
    signature(
        nom,
        si(
            lambda t: t in acceptes,
            lambda t: f"impossible de convertir un {t}",
            " | ".join(map(str, acceptes)),
        ),
        retour=fixe(resultat),
    )


@predefinie("tumu", 1, None, texte="tumu(T[, tumu[T]...]) -> tumu[T]")
def _tumu(args: tuple[Type, ...], signaler: Signaler) -> Type:
    valeurs = [args[0]]
    for i, enfant in enumerate(args[1:], start=1):
        contenu = element(enfant, "tumu")
        if contenu is None:
            signaler(i, f"tumu : les enfants doivent être des tumu, pas un {enfant}")
        valeurs.append(INCONNU if contenu is None else contenu)
    return tumu(commun_de(valeurs))


_conversion("numera", NUMERA, (NUMERA, TUHAA, PARAU, TIAHAPE))
_conversion("tuhaa", TUHAA, (NUMERA, TUHAA, PARAU))
signature("parau", TOUT, retour=fixe(PARAU))

# --- Collections : listes et arbres ordonnés ------------------------------------------

signature("amui", AJOUTABLE, VALEUR, retour=fixe(AORE))
signature("tatara", RETIRABLE, VALEUR, retour=fixe(TIAHAPE))
signature("iriti", ORDONNE, retour=identite)
signature("iti", COLLECTION, retour=identite)
signature("rahi", COLLECTION, retour=identite)

# --- Algorithmes d'arbres : toutes les sortes d'arbres --------------------------------

for _nom in ("prefixe", "infixe", "postfixe", "largeur", "rau"):
    signature(_nom, ARBRE, retour=tapura)
for _nom in ("teitei", "diametre"):
    signature(_nom, ARBRE, retour=fixe(NUMERA))
signature("equilibre", ARBRE, retour=fixe(TIAHAPE))
signature("profondeur", ARBRE, VALEUR, retour=fixe(INCONNU))  # numera, ou aore
signature("ancetre", ARBRE, VALEUR, VALEUR, retour=fixe(INCONNU))

# --- Affichage : arbres et graphes ----------------------------------------------------

for _nom in ("hohoa", "dot", "mermaid"):
    signature(_nom, STRUCTURE, retour=fixe(PARAU))
signature("matrice", GRAPHE, retour=fixe(PARAU))

# --- Graphes --------------------------------------------------------------------------

signature("taati", GRAPHE, NOEUD, NOEUD, NOMBRE, retour=fixe(AORE), optionnels=1)
signature("pihai", GRAPHE, NOEUD, retour=tapura)
signature("motu", GRAPHE, retour=tapura)
signature("teiaha", GRAPHE, NOEUD, NOEUD, retour=fixe(INCONNU))  # selon les poids
signature("tae", GRAPHE, NOEUD, NOEUD, retour=fixe(TIAHAPE))
for _nom in ("bfs", "dfs"):
    signature(_nom, GRAPHE, NOEUD, retour=tapura)
# Un chemin (une tapura), ou aore ; une distance (un nombre), ou aore.
for _nom in ("ea", "dijkstra", "bellman_ford", "distance", "edmonds_karp"):
    signature(_nom, GRAPHE, NOEUD, NOEUD, retour=fixe(INCONNU))
for _nom in ("floyd_warshall", "prim", "kruskal"):
    signature(_nom, GRAPHE, retour=upea)
signature("tri_topologique", GRAPHE, retour=fixe(INCONNU))  # une tapura, ou aore
for _nom in ("cycle", "biparti"):
    signature(_nom, GRAPHE, retour=fixe(TIAHAPE))
for _nom in ("composantes", "tarjan"):
    signature(_nom, GRAPHE, retour=lambda t: tapura(tapura(t)))
