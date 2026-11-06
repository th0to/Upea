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
    """Un entier littéral : `42`."""

    valeur: int
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Decimal:
    """Un décimal littéral : `3.14`, `1e-05`."""

    valeur: float
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Texte:
    """Un texte littéral : `"Ia ora na"` ; `valeur` est le texte décodé, sans
    guillemets ni échappements."""

    valeur: str
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Booleen:
    """`tia` (vrai) ou `hape` (faux)."""

    valeur: bool
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Rien:
    """`aore`, l'absence de valeur."""

    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Variable:
    """Un nom lu dans une expression : `x`."""

    nom: str
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Liste:
    """Une liste littérale : `[1, 2, 3]`."""

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
    """Un graphe littéral : `upea { "A" -> "B" : 3, "C" }`."""

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
    """Un opérateur préfixe : `-x`, `eiaha fini`."""

    op: OpUnaire
    operande: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Binaire:
    """Un opérateur entre deux opérandes : `a + b`, `a == b`, `x roto l`."""

    op: str  # lexème : "+", "==", "ma", "roto", ...
    gauche: Expr
    droite: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Appel:
    """L'appel d'une fonction, définie par le programme ou prédéfinie :
    `f(a, b)`."""

    nom: str
    arguments: tuple[Expr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Index:
    """Un élément d'une liste : `l[i]`."""

    objet: Expr
    indice: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Champ:
    """Un champ d'un `tumu` : `t.hotu`, `t.amaa`."""

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
    """Des instructions entre accolades : `{ … }`."""

    instructions: tuple[Instr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Declaration:
    """Une déclaration : `tuu x = 1;`, ou `mau x = 1;` pour une constante, avec
    une annotation facultative : `tuu x: numera = 1;`."""

    nom: str
    valeur: Expr
    annotation: TypeNote | None = None
    constante: bool = False
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Affectation:
    """Une affectation : `cible = valeur;`, la cible étant une variable, un
    élément ou un champ."""

    cible: Variable | Index | Champ
    valeur: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class ExprInstr:
    """Une expression employée comme instruction : `amui(l, 3);`."""

    expression: Expr
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Affiche:
    """L'affichage : `faaite a, b;`."""

    valeurs: tuple[Expr, ...]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Branche:
    """Une condition et son bloc : un `ahani`, ou un `taae ahani`."""

    condition: Expr
    corps: Bloc
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Si:
    """Une condition : `ahani c { … } taae ahani d { … } taae { … }`, les
    branches dans l'ordre, puis le bloc `taae` facultatif."""

    branches: tuple[Branche, ...]
    sinon: Bloc | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class TantQue:
    """La boucle `tamau condition { … }`."""

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
    """`faaea;` (sortir de la boucle) ou `haere;` (passer au tour suivant)."""

    genre: Literal["faaea", "haere"]
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Retour:
    """Un retour : `hoi valeur;`, ou `hoi;` sans valeur."""

    valeur: Expr | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Parametre:
    """Un paramètre de fonction, avec son annotation facultative : `n: numera`."""

    nom: str
    annotation: TypeNote | None = None
    pos: Position = _pos()


@dataclass(frozen=True, slots=True)
class Fonction:
    """Une fonction : `ohipa nom(a, b: numera) -> numera { … }`."""

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
    """La racine de l'arbre : les instructions du fichier."""

    instructions: tuple[Instr, ...]
    pos: Position = _pos()


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


def sous_noeuds(noeud: object) -> list[object]:
    """Les nœuds contenus directement dans `noeud`, dans l'ordre de ses champs."""
    return [enfant for _, enfant in _enfants(noeud)]


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
