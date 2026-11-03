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
    nom: str
    minimum: int
    maximum: int | None  # None : autant qu'on veut
    typer: Typeur

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


def predefinie(
    nom: str, minimum: int, maximum: int | None = -1
) -> Callable[[Typeur], Typeur]:
    """Enregistre un typeur écrit à la main (maximum par défaut = minimum)."""

    def enregistrer(typer: Typeur) -> Typeur:
        PREDEFINIES[nom] = Predefinie(
            nom, minimum, minimum if maximum == -1 else maximum, typer
        )
        return typer

    return enregistrer


# --- Les patrons ----------------------------------------------------------------------


@dataclass(slots=True)
class Liaison:
    """Le type `T` lié par un patron, et réutilisé par les suivants."""

    element: Type = field(default=INCONNU)


#: Vérifie un argument ; rend un message d'erreur, ou `None` s'il convient.
type Patron = Callable[[Type, Liaison], str | None]


def lie(noms: tuple[NomCompose, ...], description: str) -> Patron:
    """Un patron qui accepte les sortes `noms` et lie leur paramètre à `T`."""

    def patron(recu: Type, liaison: Liaison) -> str | None:
        contenu = element_de(recu, noms)
        if contenu is None:
            return f"{description} attendu, {recu} reçu"
        liaison.element = contenu
        return None

    return patron


def comme_t(description: str) -> Patron:
    """Un patron qui exige une valeur compatible avec le `T` déjà lié."""
    return lambda recu, liaison: (
        None
        if compatible(liaison.element, recu)
        else f"{description} {liaison.element} attendu, {recu} reçu"
    )


def si(condition: Callable[[Type], bool], message: Callable[[Type], str]) -> Patron:
    """Un patron qui accepte les types vérifiant `condition`."""
    return lambda recu, _: None if condition(recu) or recu is INCONNU else message(recu)


_LISTE_OU_ORDONNE: tuple[NomCompose, ...] = ("tapura", *ORDONNES)
_RETIRABLES: tuple[NomCompose, ...] = ("tapura", "upea", *ORDONNES)
_STRUCTURES: tuple[NomCompose, ...] = ("upea", *ARBRES)

GRAPHE = lie(("upea",), "upea")
ARBRE = lie(ARBRES, "arbre")
ORDONNE = lie(ORDONNES, "arbre ordonné (imi, aifaito, uteere, pupu, ahu)")
COLLECTION = lie(_LISTE_OU_ORDONNE, "tapura ou arbre ordonné")
RETIRABLE = lie(_RETIRABLES, "tapura, upea ou arbre ordonné")
STRUCTURE = lie(_STRUCTURES, "arbre ou upea")
NOEUD = comme_t("nœud")
VALEUR = comme_t("élément")
NOMBRE = si(est_nombre, lambda t: f"le poids doit être un nombre, pas un {t}")


def TOUT(recu: Type, liaison: Liaison) -> None:
    """Un patron qui accepte tout."""


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

    PREDEFINIES[nom] = Predefinie(nom, len(patrons) - optionnels, len(patrons), typer)


def fixe(resultat: Type) -> Callable[[Type], Type]:
    """Un type de retour qui ne dépend pas de `T`."""
    return lambda _: resultat


def identite(t: Type) -> Type:
    return t


# --- Les fonctions écrites à la main ------------------------------------------------


@predefinie("roa", 1)
def _roa(args: tuple[Type, ...], signaler: Signaler) -> Type:
    t = args[0]
    if not (t in (PARAU, INCONNU) or isinstance(t, Compose)):
        signaler(0, f"roa : tapura, parau, upea ou arbre attendu, {t} reçu")
    return NUMERA


def _conversion(nom: str, resultat: Base, acceptes: tuple[Base, ...]) -> None:
    signature(
        nom,
        si(lambda t: t in acceptes, lambda t: f"impossible de convertir un {t}"),
        retour=fixe(resultat),
    )


@predefinie("tumu", 1, None)
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

signature("amui", COLLECTION, VALEUR, retour=fixe(AORE))
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
