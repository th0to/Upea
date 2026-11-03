"""Les source maps (extension 13) : ligne du Python généré → ligne Upea."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, TypedDict

VERSION: Literal[1] = 1


class SourceMapJSON(TypedDict):
    version: Literal[1]
    source: str
    lignes: dict[str, int]  # JSON n'a que des clés texte


@dataclass(slots=True)
class SourceMap:
    source: str = "<source>"
    lignes: dict[int, int] = field(default_factory=dict)  # ligne Python -> ligne source

    def ligne_source(self, ligne_python: int) -> int | None:
        return self.lignes.get(ligne_python)

    def decaler(self, decalage: int) -> SourceMap:
        """La même correspondance, quand `decalage` lignes sont ajoutées devant."""
        return SourceMap(
            self.source,
            {python + decalage: source for python, source in self.lignes.items()},
        )

    def nommer(self, source: str) -> SourceMap:
        return SourceMap(source, dict(self.lignes))

    def vers_json(self) -> SourceMapJSON:
        return {
            "version": VERSION,
            "source": self.source,
            "lignes": {
                str(python): source for python, source in sorted(self.lignes.items())
            },
        }

    @classmethod
    def depuis_json(cls, donnees: SourceMapJSON) -> SourceMap:
        version = donnees.get("version")
        if version != VERSION:
            raise ValueError(
                f"version de source map inconnue : {version!r} (attendu : {VERSION})"
            )
        return cls(
            donnees["source"],
            {int(python): source for python, source in donnees["lignes"].items()},
        )

    def ecrire(self, chemin: Path) -> None:
        chemin.write_text(json.dumps(self.vers_json(), indent=2), encoding="utf-8")

    @classmethod
    def lire(cls, chemin: Path) -> SourceMap:
        donnees: SourceMapJSON = json.loads(chemin.read_text(encoding="utf-8"))
        return cls.depuis_json(donnees)
