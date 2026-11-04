"""L'atelier (extension 18) : vérifier, transpiler et formater un source pour un outil
extérieur, le serveur MCP, sans dépendre de lui.

Une erreur du programme n'est pas une panne : c'est un **résultat**, des diagnostics
structurés que l'appelant lit pour corriger. Tout passe par la façade `compilateur`.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

from . import compilateur, erreurs
from .erreurs import (
    Avertissement,
    ErreurExecution,
    ErreurLexicale,
    ErreurSemantique,
    ErreursMultiples,
    ErreurSyntaxe,
    ErreurType,
    ErreurUpea,
    Position,
)
from .prelude import MODULE_PRELUDE

type Sorte = Literal[
    "lexicale", "syntaxe", "semantique", "type", "avertissement", "execution"
]

#: Le nom donné au source dans les rapports.
FICHIER = "programme.upea"

# Les résultats n'ont pas de `slots` : le SDK MCP tire de ces classes le schéma de
# sortie des outils, et pydantic prend les descripteurs de slots pour des valeurs
# par défaut (l'outil perdrait alors son résultat structuré).


@dataclass(frozen=True)
class Diagnostic:
    """Une erreur ou un avertissement ; `None` quand la position est inconnue."""

    sorte: Sorte
    ligne: int | None
    colonne: int | None
    message: str


@dataclass(frozen=True)
class Verification:
    valide: bool  # aucune erreur (il peut rester des avertissements)
    diagnostics: tuple[Diagnostic, ...]
    rapport: str  # les mêmes, mis en forme comme par la CLI


@dataclass(frozen=True)
class Transpilation:
    code: str | None  # None si le programme a des erreurs
    diagnostics: tuple[Diagnostic, ...]
    rapport: str


@dataclass(frozen=True)
class Formatage:
    code: str | None  # None si le programme a des erreurs
    diagnostics: tuple[Diagnostic, ...]
    rapport: str


def sorte(erreur: ErreurUpea) -> Sorte:
    match erreur:
        case ErreurLexicale():
            return "lexicale"
        case ErreurSyntaxe():
            return "syntaxe"
        case ErreurType():  # avant ErreurSemantique, sa classe mère
            return "type"
        case ErreurSemantique():
            return "semantique"
        case Avertissement():
            return "avertissement"
        case ErreurExecution():
            return "execution"
        case _:
            raise ValueError(f"pas un diagnostic du programme : {erreur!r}")


def diagnostics(erreur: ErreurUpea) -> tuple[Diagnostic, ...]:
    """Les diagnostics d'une erreur, ou de chacune d'une `ErreursMultiples`."""
    if isinstance(erreur, ErreursMultiples):
        return tuple(d for e in erreur.erreurs for d in diagnostics(e))
    ligne: int | None = None
    colonne: int | None = None
    match erreur.position:
        case Position(ligne=numero, colonne=rang) if numero >= 1:
            # Une colonne à 0 est inconnue (erreurs d'exécution).
            ligne, colonne = numero, (rang if rang >= 1 else None)
    return (Diagnostic(sorte(erreur), ligne, colonne, erreur.message),)


def rapport(liste: Iterable[ErreurUpea], source: str) -> str:
    """Les erreurs mises en forme comme par la CLI, ou « aucune erreur »."""
    blocs = [erreurs.formater(e, source, FICHIER) for e in liste]
    return "\n".join(blocs) if blocs else "aucune erreur"


def verifier(source: str, *, types: bool = True) -> Verification:
    """Les erreurs de `source`, ou ses avertissements : le compilateur ne connaît
    les avertissements que d'un programme sans erreur."""
    try:
        analyse = compilateur.compiler(source, types=types).analyse
    except ErreursMultiples as echec:
        return Verification(False, diagnostics(echec), rapport([echec], source))
    avertissements = analyse.avertissements
    return Verification(
        True,
        tuple(d for a in avertissements for d in diagnostics(a)),
        rapport(avertissements, source),
    )


def transpiler(
    source: str, backend: str = "python", *, avec_prelude: bool = False
) -> Transpilation:
    """Le Python produit par `backend`. Sans le prélude, le code l'importe, comme
    avec `transpile --prelude externe`."""
    try:
        sortie = compilateur.transpiler(
            source, backend, prelude_externe=not avec_prelude
        )
    except ErreursMultiples as echec:
        return Transpilation(None, diagnostics(echec), rapport([echec], source))
    if avec_prelude:
        note = "le code est autonome : le prélude est recopié en tête"
    else:
        note = (
            f"le code importe le prélude (`from {MODULE_PRELUDE} import *`) : il ne "
            f"se lance qu'à côté d'un {MODULE_PRELUDE}.py ; `python -m upea "
            "transpile programme.upea -o programme.py --prelude externe` écrit les deux"
        )
    return Transpilation(sortie.code, (), note)


def formater(source: str) -> Formatage:
    """La présentation canonique de `source` (les commentaires sont perdus)."""
    try:
        code = compilateur.mettre_en_forme(source)
    except ErreursMultiples as echec:
        return Formatage(None, diagnostics(echec), rapport([echec], source))
    return Formatage(code, (), "aucune erreur")
