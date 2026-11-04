"""Ce que les générateurs partagent : le texte du prélude, et le nommage Python."""

from __future__ import annotations

import ast
import builtins
import keyword
from functools import cache
from pathlib import Path

from . import execution
from .predefinies import PREDEFINIES

#: Les modules du prélude, dans l'ordre où ils dépendent les uns des autres.
MODULES = (
    "base",
    "tumu",
    "recherche",
    "arbre_b",
    "tas",
    "vues",
    "algorithmes_arbres",
    "graphes",
    "algorithmes_graphes",
    "dessins",
    "exports",
    "predefinies",
)

_DOSSIER = Path(execution.__file__).parent
_FUTUR = "from __future__ import annotations\n"


def _a_retirer(noeud: ast.AST) -> bool:
    """Un import relatif (`from .base import _x`), ou `from __future__`."""
    return isinstance(noeud, ast.ImportFrom) and (
        noeud.level > 0 or noeud.module == "__future__"
    )


def sans_imports_relatifs(texte: str, module: str) -> str:
    """Le code d'un module du prélude, sans `from __future__` ni ses imports relatifs :
    une fois les modules mis bout à bout, ce qu'ils importent est déjà défini plus haut.

    Les lignes sont repérées avec `ast`, quelle que soit la forme de l'import
    (parenthèses, `\\`, commentaires). Un import relatif ailleurs qu'en tête de
    module, ou qui partage sa ligne avec autre chose, laisserait un fichier généré
    cassé : c'est une erreur.
    """
    arbre = ast.parse(texte)
    retirees: set[int] = set()
    for noeud in arbre.body:
        if _a_retirer(noeud):
            assert noeud.end_lineno is not None
            retirees.update(range(noeud.lineno, noeud.end_lineno + 1))
    for instruction in ast.walk(arbre):
        if not isinstance(instruction, ast.stmt) or instruction.end_lineno is None:
            continue
        lignes = set(range(instruction.lineno, instruction.end_lineno + 1))
        mal_place = _a_retirer(instruction) and instruction not in arbre.body
        if mal_place or (not _a_retirer(instruction) and lignes <= retirees):
            raise ValueError(
                f"{module}.py:{instruction.lineno} : import relatif hors de la tête "
                "du module, ou sur la ligne d'une autre instruction"
            )
    gardees = enumerate(texte.splitlines(keepends=True), 1)
    return "".join(ligne for numero, ligne in gardees if numero not in retirees)


def _corps(module: str) -> str:
    texte = (_DOSSIER / f"{module}.py").read_text(encoding="utf-8")
    return sans_imports_relatifs(texte, module)


#: Le prélude recopié en tête de chaque fichier généré : les modules d'`execution`,
#: bout à bout, avec un seul `from __future__` en tête.
PRELUDE: str = (
    "# Prélude d'Upea : arbres, graphes, algorithmes et fonctions prédéfinies.\n"
    + _FUTUR
    + "\n".join(map(_corps, MODULES))
)

#: Le module où `transpile --prelude externe` écrit le prélude, à côté du programme.
MODULE_PRELUDE = "upea_prelude"

#: Ce qui remplace le prélude en tête d'un programme qui l'importe.
IMPORT_PRELUDE = f"from {MODULE_PRELUDE} import *\n"


def _noms_definis(code: str) -> set[str]:
    """Les noms que définit le premier niveau d'un module."""
    noms: set[str] = set()
    for instruction in ast.parse(code).body:
        match instruction:
            case ast.FunctionDef(name=nom) | ast.ClassDef(name=nom):
                noms.add(nom)
            case ast.Assign(targets=cibles):
                noms.update(c.id for c in cibles if isinstance(c, ast.Name))
            case ast.AnnAssign(target=ast.Name(id=nom)) | ast.TypeAlias(
                name=ast.Name(id=nom)
            ):
                noms.add(nom)
            case ast.Import(names=alias) | ast.ImportFrom(names=alias):
                noms.update((a.asname or a.name).split(".")[0] for a in alias)
    return noms


@cache
def module_prelude() -> str:
    """Le texte de `upea_prelude.py` : le prélude, et son `__all__`. Tous ses noms
    commencent par `_` : sans `__all__`, `import *` n'en importerait aucun."""
    noms = sorted(_noms_definis(PRELUDE) - {"annotations", "_"})
    exportes = "".join(f"    {nom!r},\n" for nom in noms)
    return PRELUDE + f"\n\n__all__ = [\n{exportes}]\n"


#: La ligne qui sépare le prélude du programme dans le fichier généré.
SEPARATEUR = (
    "# --- programme Upea ---------------------------------------------------\n"
)

#: Les noms qu'une variable Upea ne peut pas porter telle quelle en Python.
RESERVES = (
    frozenset(keyword.kwlist) | frozenset(keyword.softkwlist) | frozenset(dir(builtins))
)


@cache
def nom_python(nom: str) -> str:
    """Le nom Python d'un identifiant Upea : `print` devient `_v_print`."""
    return f"_v_{nom}" if nom in RESERVES else nom


def nom_fonction(nom: str) -> str:
    """Le nom Python d'une fonction : les prédéfinies sont dans le prélude."""
    return f"_{nom}" if nom in PREDEFINIES else nom_python(nom)


#: Les opérateurs dont l'écriture Python diffère (`roto` devient un appel à `_roto`).
OPERATEURS_PYTHON = {"ma": "and", "anei": "or"}
