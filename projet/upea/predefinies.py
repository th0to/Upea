"""Les fonctions prédéfinies d'Upea, vues du compilateur : arité et typage.

Leur code d'exécution est dans `execution.py`, sous le même nom préfixé de `_`.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .typage import (
    AORE,
    INCONNU,
    NUMERA,
    PARAU,
    TIAHAPE,
    TUHAA,
    Base,
    Compose,
    Type,
    commun_de,
    compatible,
    element,
    est_nombre,
    tapura,
    tumu,
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
    """Enregistre le typeur d'une fonction prédéfinie (maximum par défaut = minimum)."""

    def enregistrer(typer: Typeur) -> Typeur:
        PREDEFINIES[nom] = Predefinie(
            nom, minimum, minimum if maximum == -1 else maximum, typer
        )
        return typer

    return enregistrer


def _graphe(nom: str, args: tuple[Type, ...], signaler: Signaler) -> Type | None:
    """Le type des nœuds du graphe passé en premier argument."""
    noeud = element(args[0], "upea")
    if noeud is None:
        signaler(0, f"{nom} : upea attendu, {args[0]} reçu")
    return noeud


def _noeuds(
    nom: str, noeud: Type | None, args: tuple[Type, ...], signaler: Signaler
) -> None:
    """Vérifie que les arguments 1, 2… sont des nœuds du bon type."""
    if noeud is None:
        return
    for i in range(1, len(args)):
        if not compatible(noeud, args[i]):
            signaler(i, f"{nom} : nœud {noeud} attendu, {args[i]} reçu")


@predefinie("roa", 1)
def _roa(args: tuple[Type, ...], signaler: Signaler) -> Type:
    t = args[0]
    if not (t in (PARAU, INCONNU) or isinstance(t, Compose)):
        signaler(0, f"roa : tapura, parau, tumu ou upea attendu, {t} reçu")
    return NUMERA


@predefinie("amui", 2)
def _amui(args: tuple[Type, ...], signaler: Signaler) -> Type:
    contenu = element(args[0], "tapura")
    if contenu is None:
        signaler(0, f"amui : tapura attendue, {args[0]} reçu")
    elif not compatible(contenu, args[1]):
        signaler(1, f"amui : élément {contenu} attendu, {args[1]} reçu")
    return AORE


def _conversion(nom: str, resultat: Base, acceptes: tuple[Base, ...]) -> None:
    @predefinie(nom, 1)
    def typer(args: tuple[Type, ...], signaler: Signaler) -> Type:
        if args[0] not in (*acceptes, INCONNU):
            signaler(0, f"{nom} : impossible de convertir un {args[0]}")
        return resultat


_conversion("numera", NUMERA, (NUMERA, TUHAA, PARAU, TIAHAPE))
_conversion("tuhaa", TUHAA, (NUMERA, TUHAA, PARAU))


@predefinie("parau", 1)
def _parau(args: tuple[Type, ...], signaler: Signaler) -> Type:
    return PARAU


@predefinie("tumu", 1, None)
def _tumu(args: tuple[Type, ...], signaler: Signaler) -> Type:
    valeurs = [args[0]]
    for i, enfant in enumerate(args[1:], start=1):
        contenu = element(enfant, "tumu")
        if contenu is None:
            signaler(i, f"tumu : les enfants doivent être des tumu, pas un {enfant}")
            valeurs.append(INCONNU)
        else:
            valeurs.append(contenu)
    return tumu(commun_de(valeurs))


@predefinie("teitei", 1)
def _teitei(args: tuple[Type, ...], signaler: Signaler) -> Type:
    if element(args[0], "tumu") is None:
        signaler(0, f"teitei : tumu attendu, {args[0]} reçu")
    return NUMERA


@predefinie("rau", 1)
def _rau(args: tuple[Type, ...], signaler: Signaler) -> Type:
    contenu = element(args[0], "tumu")
    if contenu is None:
        signaler(0, f"rau : tumu attendu, {args[0]} reçu")
        return tapura()
    return tapura(contenu)


@predefinie("taati", 3, 4)
def _taati(args: tuple[Type, ...], signaler: Signaler) -> Type:
    noeud = _graphe("taati", args, signaler)
    _noeuds("taati", noeud, args[:3], signaler)
    if len(args) == 4 and not (est_nombre(args[3]) or args[3] is INCONNU):
        signaler(3, f"taati : le poids doit être un nombre, pas un {args[3]}")
    return AORE


@predefinie("pihai", 2)
def _pihai(args: tuple[Type, ...], signaler: Signaler) -> Type:
    noeud = _graphe("pihai", args, signaler)
    _noeuds("pihai", noeud, args, signaler)
    return tapura(INCONNU if noeud is None else noeud)


@predefinie("motu", 1)
def _motu(args: tuple[Type, ...], signaler: Signaler) -> Type:
    noeud = _graphe("motu", args, signaler)
    return tapura(INCONNU if noeud is None else noeud)


@predefinie("teiaha", 3)
def _teiaha(args: tuple[Type, ...], signaler: Signaler) -> Type:
    _noeuds("teiaha", _graphe("teiaha", args, signaler), args, signaler)
    return INCONNU  # numera ou tuhaa, selon les poids


@predefinie("tae", 3)
def _tae(args: tuple[Type, ...], signaler: Signaler) -> Type:
    _noeuds("tae", _graphe("tae", args, signaler), args, signaler)
    return TIAHAPE


@predefinie("ea", 3)
def _ea(args: tuple[Type, ...], signaler: Signaler) -> Type:
    _noeuds("ea", _graphe("ea", args, signaler), args, signaler)
    return INCONNU  # une tapura, ou aore
