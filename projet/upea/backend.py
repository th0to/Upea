"""Le contrat d'un backend (étape 10) : un `Protocol`, sans héritage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .noeuds import Programme
from .semantique import Analyse
from .sourcemap import SourceMap


@dataclass(frozen=True, slots=True)
class Sortie:
    """Ce que produit un backend : le code, et la correspondance de ses lignes
    avec celles du source."""

    code: str
    sourcemap: SourceMap = field(default_factory=SourceMap)


class Backend(Protocol):
    """Le contrat d'un backend : son nom (pour `--backend`), l'extension de ses
    fichiers, s'il produit du Python exécutable, et `generer`. Aucun héritage :
    toute classe qui a cette forme convient."""

    nom: str
    extension: str
    executable: bool  # le code produit est-il du Python exécutable ?

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        """Le code du programme, d'après son arbre et son analyse sémantique."""
        ...
