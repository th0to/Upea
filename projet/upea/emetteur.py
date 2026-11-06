"""L'émetteur de lignes indentées, partagé par le générateur et le formateur."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager


class Emetteur:
    """Produit des lignes indentées, et note pour chacune la ligne source dont
    elle provient (`correspondances`, d'où vient la source map)."""

    def __init__(self, indentation: str = "    ") -> None:
        self._lignes: list[str] = []
        self._indentation = indentation
        self.niveau = 0
        self._source: int | None = None
        #: Pour chaque ligne produite (numérotée à partir de 1), la ligne source.
        self.correspondances: dict[int, int] = {}

    def ligne(self, texte: str = "") -> None:
        """Ajoute une ligne au niveau d'indentation courant.

        Un texte de plusieurs lignes est indenté ligne par ligne.
        """
        for morceau in texte.split("\n"):
            self._lignes.append(
                self._indentation * self.niveau + morceau if morceau else ""
            )
            if self._source is not None:
                self.correspondances[len(self._lignes)] = self._source

    @contextmanager
    def bloc(self, vide: str | None = "pass") -> Iterator[None]:
        """Indente ce qui est émis dans le `with` ; un bloc resté vide reçoit `vide`."""
        avant = len(self._lignes)
        self.niveau += 1
        try:
            yield
            if len(self._lignes) == avant and vide is not None:
                self.ligne(vide)  # un bloc Python ne peut pas être vide
        finally:
            self.niveau -= 1

    @contextmanager
    def depuis(self, ligne_source: int) -> Iterator[None]:
        """Les lignes émises dans le `with` proviennent de `ligne_source`."""
        precedente = self._source
        self._source = ligne_source
        try:
            yield
        finally:
            self._source = precedente

    def texte(self) -> str:
        """Le texte produit, chaque ligne terminée par un saut de ligne."""
        return "".join(ligne + "\n" for ligne in self._lignes)
