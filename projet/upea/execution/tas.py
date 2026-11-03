"""Prélude — le tas binaire (`ahu`, tas min ; `ahunui`, tas max), une file de
priorité rangée dans une liste : les enfants de l'indice i sont en 2i + 1 et 2i + 2.

Les deux tas ne diffèrent que par la relation qui dit qui passe devant : elle est
donnée en paramètre (`operator.lt` ou `operator.gt`).
"""

from __future__ import annotations

import operator as _operator
from collections.abc import Callable as _Callable
from collections.abc import Iterable as _Iterable
from collections.abc import Iterator as _Iterator
from functools import reduce as _reduce
from typing import Any as _Any

from .base import _sorte_upea, _texte, _verifier_cle


@_sorte_upea("ahu")
class _Ahu:
    __slots__ = ("valeurs", "nui", "_devant")

    def __init__(self, cles: _Iterable[_Any] = (), nui: bool = False) -> None:
        self.valeurs: list[_Any] = []
        self.nui = nui
        self._devant: _Callable[[_Any, _Any], bool] = (
            _operator.gt if nui else _operator.lt
        )
        for cle in cles:
            self.ajouter(cle)

    @property
    def sorte(self) -> str:
        return "ahunui" if self.nui else "ahu"

    def ajouter(self, cle: _Any) -> bool:
        _verifier_cle(cle, self.sorte, self.valeurs[0] if self.valeurs else None)
        self.valeurs.append(cle)
        self._monter(len(self.valeurs) - 1)
        return True

    def sommet(self) -> _Any:
        return self.valeurs[0]

    def iriti(self) -> _Any:
        """Retire et rend le sommet (le plus petit, ou le plus grand pour `ahunui`)."""
        return self._retirer_indice(0)

    def retirer(self, cle: _Any) -> bool:
        try:
            i = self.valeurs.index(cle)
        except ValueError:
            return False
        self._retirer_indice(i)
        return True

    def _retirer_indice(self, i: int) -> _Any:
        valeur, dernier = self.valeurs[i], self.valeurs.pop()
        if i < len(self.valeurs):
            self.valeurs[i] = dernier
            self._monter(i)
            self._descendre(i)
        return valeur

    def _monter(self, i: int) -> None:
        while i > 0 and self._devant(self.valeurs[i], self.valeurs[(i - 1) // 2]):
            parent = (i - 1) // 2
            self.valeurs[i], self.valeurs[parent] = (
                self.valeurs[parent],
                self.valeurs[i],
            )
            i = parent

    def _descendre(self, i: int) -> None:
        n, v = len(self.valeurs), self.valeurs
        while True:
            enfants = [j for j in (2 * i + 1, 2 * i + 2) if j < n]
            # Celui qui passe devant, entre le nœud et ses enfants.
            meilleur = _reduce(
                lambda m, j: j if self._devant(v[j], v[m]) else m, enfants, i
            )
            if meilleur == i:
                return
            self.valeurs[i], self.valeurs[meilleur] = (
                self.valeurs[meilleur],
                self.valeurs[i],
            )
            i = meilleur

    def min(self) -> _Any:
        return self.sommet() if not self.nui else min(self.valeurs)

    def max(self) -> _Any:
        return self.sommet() if self.nui else max(self.valeurs)

    def __contains__(self, cle: object) -> bool:
        return cle in self.valeurs

    def __iter__(self) -> _Iterator[_Any]:
        """Les clés dans l'ordre de priorité, sans toucher au tas."""
        return iter(sorted(self.valeurs, reverse=self.nui))

    def __eq__(self, autre: object) -> bool:
        return (
            isinstance(autre, _Ahu)
            and self.nui == autre.nui
            and list(self) == list(autre)
        )

    def __repr__(self) -> str:
        return _texte(self, True)


def _ahu(cles: list[_Any]) -> _Ahu:
    return _Ahu(cles)


def _ahunui(cles: list[_Any]) -> _Ahu:
    return _Ahu(cles, nui=True)


@_texte.register(_Ahu)
def _(valeur: _Ahu, imbrique: bool = False) -> str:
    return f"{valeur.sorte} [" + ", ".join(_texte(c, True) for c in valeur) + "]"
