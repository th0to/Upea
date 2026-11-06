"""Les types d'Upea (extension 12) : types simples, types paramétrés, compatibilité."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import reduce
from typing import Literal

from .erreurs import ErreurType
from .noeuds import TypeNote


class Base(Enum):
    """Les types simples d'Upea, et `INCONNU` (`?`) : le type que le typage
    graduel ne connaît pas."""

    NUMERA = "numera"
    TUHAA = "tuhaa"
    PARAU = "parau"
    TIAHAPE = "tiahape"
    AORE = "aore"
    INCONNU = "?"

    def __str__(self) -> str:
        return self.value


type NomCompose = Literal[
    "tapura", "upea", "tumu", "imi", "aifaito", "uteere", "pupu", "ahu"
]

#: Les arbres ordonnés : arbres de recherche, arbre B et tas.
ORDONNES: tuple[NomCompose, ...] = ("imi", "aifaito", "uteere", "pupu", "ahu")
#: Toutes les sortes d'arbres, sur lesquelles marchent les algorithmes d'arbres.
ARBRES: tuple[NomCompose, ...] = ("tumu", *ORDONNES)
COMPOSES: tuple[NomCompose, ...] = ("tapura", "upea", *ARBRES)


@dataclass(frozen=True, slots=True)
class Compose:
    """Un type paramétré : `tapura[numera]`, `tumu[parau]`, `aifaito[?]`."""

    nom: NomCompose
    element: Type

    def __str__(self) -> str:
        return f"{self.nom}[{self.element}]"


type Type = Base | Compose

NUMERA = Base.NUMERA
TUHAA = Base.TUHAA
PARAU = Base.PARAU
TIAHAPE = Base.TIAHAPE
AORE = Base.AORE
INCONNU = Base.INCONNU


def tapura(element: Type = INCONNU) -> Compose:
    """Le type d'une liste : `tapura[T]`."""
    return Compose("tapura", element)


def tumu(element: Type = INCONNU) -> Compose:
    """Le type d'un arbre : `tumu[T]`."""
    return Compose("tumu", element)


def upea(element: Type = INCONNU) -> Compose:
    """Le type d'un graphe : `upea[T]`."""
    return Compose("upea", element)


@dataclass(frozen=True, slots=True)
class Signature:
    """Le type d'une fonction définie par l'utilisateur."""

    parametres: tuple[Type, ...]
    retour: Type


def compatible(attendu: Type, recu: Type) -> bool:
    """Peut-on ranger une valeur de type `recu` là où `attendu` est demandé ?"""
    if INCONNU in (attendu, recu) or attendu == recu:
        return True
    if attendu is TUHAA and recu is NUMERA:
        return True
    if isinstance(attendu, Compose) and isinstance(recu, Compose):
        return attendu.nom == recu.nom and compatible(attendu.element, recu.element)
    return False


def commun(a: Type, b: Type) -> Type:
    """Le type commun de deux valeurs (pour les éléments d'une liste, par exemple)."""
    if a == b:
        return a
    if {a, b} == {NUMERA, TUHAA}:
        return TUHAA
    if isinstance(a, Compose) and isinstance(b, Compose) and a.nom == b.nom:
        return Compose(a.nom, commun(a.element, b.element))
    return INCONNU


def commun_de(types: list[Type]) -> Type:
    """Le type commun d'une suite de valeurs (`INCONNU` si elle est vide)."""
    return reduce(commun, types) if types else INCONNU


def est_nombre(t: Type) -> bool:
    """Vrai pour `numera` et `tuhaa`."""
    return t is NUMERA or t is TUHAA


def est_cle(t: Type) -> bool:
    """Une clé d'arbre ordonné, ou un nœud de graphe : un nombre ou un texte."""
    return est_nombre(t) or t in (PARAU, INCONNU)


def element_de(t: Type, noms: tuple[NomCompose, ...]) -> Type | None:
    """Le paramètre de `t` s'il est de l'une des sortes `noms`, `INCONNU` si `t` est
    inconnu, et `None` si `t` est connu et d'une autre sorte."""
    if t is INCONNU:
        return INCONNU
    if isinstance(t, Compose) and t.nom in noms:
        return t.element
    return None


def element(t: Type, nom: NomCompose) -> Type | None:
    """Le paramètre de `t` s'il est de la sorte `nom` (voir `element_de`)."""
    return element_de(t, (nom,))


SIMPLES: dict[str, Base] = {b.value: b for b in Base if b is not INCONNU}


def depuis_note(note: TypeNote) -> Type:
    """Le type désigné par une annotation ; lève `ErreurType` s'il n'existe pas."""
    if note.nom in SIMPLES:
        if note.parametre is not None:
            raise ErreurType(
                f"le type {note.nom} n'a pas de paramètre", note.parametre.pos
            )
        return SIMPLES[note.nom]
    nom = next((n for n in COMPOSES if n == note.nom), None)
    if nom is None:
        connus = ", ".join([*SIMPLES, *COMPOSES])
        raise ErreurType(f"type inconnu : '{note.nom}' (types : {connus})", note.pos)
    parametre = INCONNU if note.parametre is None else depuis_note(note.parametre)
    return Compose(nom, parametre)


PYTHON_SIMPLES: dict[Base, str | None] = {
    NUMERA: "int",
    TUHAA: "float",
    PARAU: "str",
    TIAHAPE: "bool",
    AORE: "None",
    INCONNU: None,
}
#: La classe Python qui représente chaque sorte composée.
PYTHON_COMPOSES: dict[NomCompose, str] = {
    "tapura": "list",
    "upea": "_Upea",
    "tumu": "_Tumu",
    "imi": "_Imi",
    "aifaito": "_Aifaito",
    "uteere": "_Uteere",
    "pupu": "_Pupu",
    "ahu": "_Ahu",
}


def vers_python(t: Type) -> str | None:
    """L'annotation Python correspondante, ou `None` pour le type inconnu."""
    if isinstance(t, Compose):
        return PYTHON_COMPOSES[t.nom]
    return PYTHON_SIMPLES[t]
