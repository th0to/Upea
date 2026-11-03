"""Le contrat d'un backend (étape 10) : un `Protocol`, sans héritage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .noeuds import Programme
from .semantique import Analyse
from .sourcemap import SourceMap


@dataclass(frozen=True, slots=True)
class Sortie:
    code: str
    sourcemap: SourceMap = field(default_factory=SourceMap)


class Backend(Protocol):
    nom: str
    extension: str
    executable: bool  # le code produit est-il du Python exécutable ?

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie: ...
