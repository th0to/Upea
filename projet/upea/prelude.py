"""Ce que les générateurs partagent : le texte du prélude, et le nommage Python."""

from __future__ import annotations

import builtins
import keyword
from pathlib import Path

from . import execution
from .predefinies import PREDEFINIES

#: Le code du module `execution`, recopié en tête de chaque fichier généré.
PRELUDE: str = Path(execution.__file__).read_text(encoding="utf-8")

#: La ligne qui sépare le prélude du programme dans le fichier généré.
SEPARATEUR = (
    "# --- programme Upea ---------------------------------------------------\n"
)

#: Les noms qu'une variable Upea ne peut pas porter telle quelle en Python.
RESERVES = (
    frozenset(keyword.kwlist) | frozenset(keyword.softkwlist) | frozenset(dir(builtins))
)


def nom_python(nom: str) -> str:
    """Le nom Python d'un identifiant Upea : `print` devient `_v_print`."""
    return f"_v_{nom}" if nom in RESERVES else nom


def nom_fonction(nom: str) -> str:
    """Le nom Python d'une fonction : les prédéfinies sont dans le prélude."""
    return f"_{nom}" if nom in PREDEFINIES else nom_python(nom)


#: Les opérateurs dont l'écriture Python diffère.
OPERATEURS_PYTHON = {"ma": "and", "anei": "or", "roto": "in"}
