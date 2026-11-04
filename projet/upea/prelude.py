"""Ce que les générateurs partagent : le texte du prélude, et le nommage Python."""

from __future__ import annotations

import builtins
import keyword
import re
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
#: `from .base import _x` ou `from .base import (\n  _x,\n  _y,\n)`.
_IMPORT_RELATIF = re.compile(r"^from \.\w* import (?:\([^)]*\)|.*)\n", re.MULTILINE)


def _corps(module: str) -> str:
    """Le code d'un module du prélude, sans ses imports relatifs ni `__future__`."""
    texte = (_DOSSIER / f"{module}.py").read_text(encoding="utf-8")
    return _IMPORT_RELATIF.sub("", texte.replace(_FUTUR, ""))


#: Le prélude recopié en tête de chaque fichier généré : les modules d'`execution`,
#: bout à bout, avec un seul `from __future__` en tête.
PRELUDE: str = (
    "# Prélude d'Upea : arbres, graphes, algorithmes et fonctions prédéfinies.\n"
    + _FUTUR
    + "\n".join(map(_corps, MODULES))
)

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
