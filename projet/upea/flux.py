"""Un flux avec regard en avant, qui ne tire de sa source que le nécessaire."""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable, Iterator


class Flux[T]:
    """Un flux avec regard en avant : `regarde(n)` montre l'élément situé `n`
    places plus loin sans le consommer, `avance()` consomme le suivant."""

    def __init__(self, source: Iterable[T]) -> None:
        self._source: Iterator[T] = iter(source)
        self._tampon: deque[T] = deque()
        self._epuise = False
        #: Nombre d'éléments consommés par `avance` depuis le début.
        self.consommes = 0

    def _remplir(self, taille: int) -> bool:
        """Tire de la source jusqu'à avoir `taille` éléments en tampon."""
        while len(self._tampon) < taille:
            if self._epuise:
                return False
            try:
                self._tampon.append(next(self._source))
            except StopIteration:
                self._epuise = True
                return False
        return True

    def regarde(self, decalage: int = 0) -> T | None:
        """L'élément situé `decalage` crans plus loin, sans le consommer."""
        if not self._remplir(decalage + 1):
            return None
        return self._tampon[decalage]

    def avance(self) -> T:
        """Consomme et renvoie l'élément courant."""
        if not self._remplir(1):
            raise IndexError("le flux est épuisé")
        self.consommes += 1
        return self._tampon.popleft()

    def fini(self) -> bool:
        """Vrai quand il ne reste plus rien à lire."""
        return self.regarde() is None
