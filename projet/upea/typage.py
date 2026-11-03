"""Les types d'Upea (extension 12) : types simples, types paramétrés, compatibilité."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Literal

from .erreurs import ErreurType
from .noeuds import TypeNote


class Base(Enum):
    NUMERA = "numera"
    TUHAA = "tuhaa"
    PARAU = "parau"
    TIAHAPE = "tiahape"
    AORE = "aore"
    INCONNU = "?"

    def __str__(self) -> str:
        return self.value


type NomCompose = Literal["tapura", "tumu", "upea"]


@dataclass(frozen=True, slots=True)
class Compose:
    """Un type paramétré : `tapura[numera]`, `tumu[parau]`, `upea[?]`."""

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
    return Compose("tapura", element)


def tumu(element: Type = INCONNU) -> Compose:
    return Compose("tumu", element)


def upea(element: Type = INCONNU) -> Compose:
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
    if not types:
        return INCONNU
    resultat = types[0]
    for t in types[1:]:
        resultat = commun(resultat, t)
    return resultat


def est_nombre(t: Type) -> bool:
    return t is NUMERA or t is TUHAA


def element(t: Type, nom: NomCompose) -> Type | None:
    """Le paramètre de `t` s'il est de la sorte `nom`, `INCONNU` si `t` est inconnu,
    et `None` si `t` est connu et d'une autre sorte."""
    if t is INCONNU:
        return INCONNU
    if isinstance(t, Compose) and t.nom == nom:
        return t.element
    return None


SIMPLES: dict[str, Base] = {b.value: b for b in Base if b is not INCONNU}
COMPOSES: tuple[NomCompose, ...] = ("tapura", "tumu", "upea")


def depuis_note(note: TypeNote) -> Type:
    """Le type désigné par une annotation ; lève `ErreurType` s'il n'existe pas."""
    if note.nom in SIMPLES:
        if note.parametre is not None:
            raise ErreurType(
                f"le type {note.nom} n'a pas de paramètre", note.parametre.pos
            )
        return SIMPLES[note.nom]
    for nom in COMPOSES:
        if note.nom == nom:
            parametre = (
                INCONNU if note.parametre is None else depuis_note(note.parametre)
            )
            return Compose(nom, parametre)
    connus = ", ".join([*SIMPLES, *COMPOSES])
    raise ErreurType(f"type inconnu : '{note.nom}' (types : {connus})", note.pos)


def vers_python(t: Type) -> str | None:
    """L'annotation Python correspondante, ou `None` pour le type inconnu."""
    match t:
        case Base.NUMERA:
            return "int"
        case Base.TUHAA:
            return "float"
        case Base.PARAU:
            return "str"
        case Base.TIAHAPE:
            return "bool"
        case Base.AORE:
            return "None"
        case Base.INCONNU:
            return None
        case Compose("tapura", _):
            return "list"
        case Compose("tumu", _):
            return "_Tumu"
        case Compose("upea", _):
            return "_Upea"
        case _:
            return None
