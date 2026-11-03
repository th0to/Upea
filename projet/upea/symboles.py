"""La table des symboles : une pile de portées, ouvertes par un context manager."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from enum import Enum

from .erreurs import Position
from .typage import INCONNU, Signature, Type


class Genre(Enum):
    VARIABLE = "variable"
    CONSTANTE = "constante"
    BOUCLE = "variable de boucle"
    PARAMETRE = "paramètre"
    FONCTION = "fonction"
    PREDEFINIE = "fonction prédéfinie"

    @property
    def est_valeur(self) -> bool:
        """Vrai pour ce qui désigne une valeur (pas une fonction)."""
        return self not in (Genre.FONCTION, Genre.PREDEFINIE)


@dataclass(slots=True)
class Symbole:
    nom: str
    genre: Genre
    pos: Position
    type: Type = INCONNU
    signature: Signature | None = None
    utilise: bool = False


@dataclass(slots=True)
class Portee:
    nom: str
    est_fonction: bool = False
    symboles: dict[str, Symbole] = field(default_factory=dict)


class TableSymboles:
    """La pile : les prédéfinies, puis la portée globale, puis les blocs ouverts."""

    def __init__(self) -> None:
        self._portees: list[Portee] = [Portee("prédéfinies"), Portee("globale")]

    @property
    def predefinies(self) -> Portee:
        return self._portees[0]

    @property
    def globale(self) -> Portee:
        return self._portees[1]

    @property
    def courante(self) -> Portee:
        return self._portees[-1]

    @property
    def profondeur(self) -> int:
        """Le nombre de portées ouvertes au-dessus de la portée globale."""
        return len(self._portees) - 2

    @contextmanager
    def portee(self, nom: str = "bloc", *, fonction: bool = False) -> Iterator[Portee]:
        """Ouvre une portée, refermée quoi qu'il arrive à la sortie du `with`."""
        portee = Portee(nom, est_fonction=fonction)
        self._portees.append(portee)
        try:
            yield portee
        finally:
            self._portees.pop()

    def declarer(self, symbole: Symbole) -> None:
        """Range `symbole` dans la portée courante (sans écraser un homonyme)."""
        self.courante.symboles.setdefault(symbole.nom, symbole)

    def chercher_avec_portee(self, nom: str) -> tuple[Symbole, Portee] | None:
        for portee in reversed(self._portees):
            if nom in portee.symboles:
                return portee.symboles[nom], portee
        return None

    def chercher(self, nom: str) -> Symbole | None:
        trouve = self.chercher_avec_portee(nom)
        return None if trouve is None else trouve[0]

    def meme_espace(self, nom: str) -> Symbole | None:
        """Un symbole visible de même nom dans le même espace de noms Python.

        C'est la fonction en cours (ses portées ouvertes depuis la portée de
        fonction), ou, hors de toute fonction, toutes les portées globales.
        """
        for portee in reversed(self._portees[1:]):
            if nom in portee.symboles:
                return portee.symboles[nom]
            if portee.est_fonction:
                return None
        return None
