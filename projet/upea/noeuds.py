"""Les nœuds de l'arbre syntaxique d'Upea.

Tout est gelé, les enfants multiples sont des `tuple`, et la position est
exclue de `==` et du `repr` : deux arbres de même structure sont égaux, quelle
que soit la mise en page du source.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Literal

from .erreurs import SANS_POSITION, Position


def _pos() -> Position:
    return field(default=SANS_POSITION, compare=False, repr=False)


# --- Expressions ----------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Entier:
    valeur: int
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Decimal:
    valeur: float
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Texte:
    valeur: str
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Booleen:
    valeur: bool
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Rien:
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Variable:
    nom: str
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Liste:
    elements: tuple[Expr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Arete:
    """Une arête d'un littéral de graphe : `depart -> arrivee : poids`, ou un nœud
    seul (`arrivee` vaut alors `None`)."""

    depart: Expr
    arrivee: Expr | None
    double: bool  # vrai pour `<->`
    poids: Expr | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Graphe:
    aretes: tuple[Arete, ...]
    pos: Position = _pos()


type SorteCollection = Literal["imi", "aifaito", "uteere", "pupu", "ahu", "ahunui"]


@dataclass(frozen=True, slots=True)
class Collection:
    """Un littéral d'arbre ordonné : `aifaito [5, 3, 8]`, `pupu 4 [1, 2]`."""

    sorte: SorteCollection
    elements: tuple[Expr, ...]
    ordre: int | None = None  # l'ordre d'un arbre B, quand il est écrit
    pos: Position = _pos()


type OpUnaire = Literal["-", "eiaha"]


@dataclass(frozen=True, slots=True)
class Unaire:
    op: OpUnaire
    operande: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Binaire:
    op: str  # lexème : "+", "==", "ma", "roto", ...
    gauche: Expr
    droite: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Appel:
    nom: str
    arguments: tuple[Expr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Index:
    objet: Expr
    indice: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Champ:
    objet: Expr
    nom: str
    pos: Position = _pos()


type Expr = (
    Entier
    | Decimal
    | Texte
    | Booleen
    | Rien
    | Variable
    | Liste
    | Graphe
    | Collection
    | Unaire
    | Binaire
    | Appel
    | Index
    | Champ
)

# --- Annotations de type --------------------------------------------------------


@dataclass(frozen=True, slots=True)
class TypeNote:
    """Une annotation telle qu'écrite : `numera`, `tapura[tumu[parau]]`."""

    nom: str
    parametre: TypeNote | None = None
    pos: Position = _pos()


# --- Instructions ---------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Bloc:
    instructions: tuple[Instr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Declaration:
    nom: str
    valeur: Expr
    annotation: TypeNote | None = None
    constante: bool = False
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Affectation:
    cible: Variable | Index | Champ
    valeur: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class ExprInstr:
    expression: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Affiche:
    valeurs: tuple[Expr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Branche:
    condition: Expr
    corps: Bloc
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Si:
    branches: tuple[Branche, ...]
    sinon: Bloc | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class TantQue:
    condition: Expr
    corps: Bloc
    pos: Position = _pos()


type Mode = Literal["aano", "hohonu"]


@dataclass(frozen=True, slots=True)
class Pour:
    """`tataitahi variable roto iterable [..fin | mai depart] [mode] { corps }`."""

    variable: str
    iterable: Expr
    corps: Bloc
    fin: Expr | None = None  # borne haute d'un intervalle
    inclusif: bool = False  # `..=` plutôt que `..`
    depart: Expr | None = None  # `mai depart`
    mode: Mode | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Rupture:
    genre: Literal["faaea", "haere"]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Retour:
    valeur: Expr | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Parametre:
    nom: str
    annotation: TypeNote | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Fonction:
    nom: str
    parametres: tuple[Parametre, ...]
    corps: Bloc
    retour: TypeNote | None = None
    pos: Position = _pos()


type Instr = (
    Declaration
    | Affectation
    | ExprInstr
    | Affiche
    | Si
    | TantQue
    | Pour
    | Rupture
    | Retour
    | Fonction
)


@dataclass(frozen=True, slots=True)
class Programme:
    instructions: tuple[Instr, ...]
    pos: Position = _pos()


type Noeud = Expr | Instr | Programme | Bloc | Branche | Arete | Parametre | TypeNote

# --- Parcours génériques --------------------------------------------------------


def _enfants(noeud: object) -> list[tuple[str, object]]:
    """Les champs de `noeud` qui contiennent des nœuds, avec leur nom."""
    resultat: list[tuple[str, object]] = []
    if not is_dataclass(noeud):
        return resultat
    for f in fields(noeud):
        if f.name == "pos":
            continue
        valeur = getattr(noeud, f.name)
        if is_dataclass(valeur):
            resultat.append((f.name, valeur))
        elif isinstance(valeur, tuple):
            for i, element in enumerate(valeur):
                if is_dataclass(element):
                    resultat.append((f"{f.name}[{i}]", element))
    return resultat


def _attributs(noeud: object) -> str:
    morceaux: list[str] = []
    if not is_dataclass(noeud):
        return ""
    for f in fields(noeud):
        if f.name == "pos":
            continue
        valeur = getattr(noeud, f.name)
        if is_dataclass(valeur) or isinstance(valeur, tuple) or valeur is None:
            continue
        morceaux.append(f"{f.name}={valeur!r}")
    return " ".join(morceaux)


def afficher_arbre(noeud: object) -> str:
    """L'arbre indenté, un nœud par ligne, avec le nom de chaque champ."""
    lignes: list[str] = []

    def entete(n: object) -> str:
        attributs = _attributs(n)
        return type(n).__name__ + (f" {attributs}" if attributs else "")

    def visiter(n: object, prefixe: str) -> None:
        enfants = _enfants(n)
        for i, (nom, enfant) in enumerate(enfants):
            dernier = i == len(enfants) - 1
            lignes.append(
                f"{prefixe}{'└── ' if dernier else '├── '}{nom}: {entete(enfant)}"
            )
            visiter(enfant, prefixe + ("    " if dernier else "│   "))

    lignes.append(entete(noeud))
    visiter(noeud, "")
    return "\n".join(lignes)


def parcourir(noeud: object) -> Iterator[object]:
    """Tous les nœuds d'un arbre, en profondeur, en commençant par `noeud`."""
    yield noeud
    for _, enfant in _enfants(noeud):
        yield from parcourir(enfant)
