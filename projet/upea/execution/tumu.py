"""Prélude — les arbres n-aires `tumu`."""

from __future__ import annotations

from collections.abc import Iterable as _Iterable
from typing import Any as _Any
from typing import Self as _Self
from typing import SupportsIndex as _SupportsIndex

from .base import _Erreur, _sorte, _sorte_upea, _texte, _une_fois


@_sorte_upea("tumu")
class _Tumu:
    """Un nœud d'arbre n-aire : une valeur (`hotu`) et des enfants (`amaa`)."""

    __slots__ = ("hotu", "_amaa", "_accroche")

    def __init__(self, hotu: object, amaa: _Iterable[_Tumu] = ()) -> None:
        self.hotu = hotu
        #: Vrai dès que le nœud a été l'enfant d'un autre. Un nœud jamais accroché
        #: n'est le descendant de personne : on s'épargne la recherche d'un cycle.
        self._accroche = False
        self._amaa = _Branches(self)
        # Un nœud neuf ne peut pas être le descendant de ses enfants : on évite
        # le contrôle des cycles, qui rendrait la construction quadratique.
        list.extend(self._amaa, amaa)
        for enfant in self._amaa:
            enfant._accroche = True

    @property
    def amaa(self) -> _Branches:
        return self._amaa

    @amaa.setter
    def amaa(self, enfants: object) -> None:
        """`t.amaa = l` recopie les éléments de `l`, vérifiés : `l` reste à part."""
        if not isinstance(enfants, list):
            raise _Erreur(
                f"les branches d'un tumu forment une tapura, pas un {_sorte(enfants)}"
            )
        branches = _Branches(self)
        branches.extend(enfants)
        self._amaa = branches

    def __eq__(self, autre: object) -> bool:
        """Mêmes valeurs, mêmes enfants dans le même ordre. Une pile explicite, et non
        la récursion de `list.__eq__`, pour qu'un arbre profond se compare aussi."""
        pile: list[tuple[_Tumu, object]] = [(self, autre)]
        while pile:
            a, b = pile.pop()
            if a is b:
                continue
            if (
                not isinstance(b, _Tumu)
                or len(a.amaa) != len(b.amaa)
                or a.hotu != b.hotu
            ):
                return False
            pile.extend(zip(a.amaa, b.amaa, strict=True))
        return True

    def __contains__(self, valeur: object) -> bool:
        pile = [self]
        while pile:
            noeud = pile.pop()
            if noeud.hotu == valeur:
                return True
            pile.extend(noeud.amaa)
        return False

    def __repr__(self) -> str:
        return _texte(self, True)


@_sorte_upea("tapura")
class _Branches(list[_Tumu]):
    """Les enfants d'un `tumu` : une tapura qui n'accepte que des `tumu`, et refuse
    tout ajout qui ferait du nœud son propre descendant. Un `tumu` reste ainsi un
    arbre fini (un sous-arbre peut être partagé, jamais former un cycle)."""

    __slots__ = ("_noeud",)

    def __init__(self, noeud: _Tumu) -> None:
        super().__init__()
        self._noeud = noeud

    def _accepter(self, enfant: object) -> _Tumu:
        if not isinstance(enfant, _Tumu):
            raise _Erreur(
                f"les branches d'un tumu doivent être des tumu, pas un {_sorte(enfant)}"
            )
        noeud = self._noeud
        if enfant is noeud or (noeud._accroche and _descend_de(noeud, enfant)):
            raise _Erreur(
                "un tumu ne peut pas devenir sa propre branche, même indirectement"
            )
        enfant._accroche = True
        return enfant

    def append(self, enfant: object) -> None:
        super().append(self._accepter(enfant))

    def insert(self, indice: _SupportsIndex, enfant: object) -> None:
        super().insert(indice, self._accepter(enfant))

    def extend(self, enfants: _Iterable[object]) -> None:
        for enfant in enfants:
            self.append(enfant)

    def __iadd__(self, enfants: _Iterable[object]) -> _Self:  # type: ignore[override,misc]
        self.extend(enfants)
        return self

    def __setitem__(self, indice: _Any, valeur: _Any) -> None:
        if isinstance(indice, slice):
            super().__setitem__(indice, [self._accepter(e) for e in valeur])
        else:
            super().__setitem__(indice, self._accepter(valeur))


def _descend_de(noeud: _Tumu, ancetre: _Tumu) -> bool:
    """Vrai si `noeud` est `ancetre` lui-même ou l'un de ses descendants."""
    pile, vus = [ancetre], set[int]()
    while pile:
        courant = pile.pop()
        if courant is noeud:
            return True
        if id(courant) not in vus:
            vus.add(id(courant))
            pile.extend(courant.amaa)
    return False


def _tumu(hotu: object, *enfants: object) -> _Tumu:
    branches: list[_Tumu] = []
    for enfant in enfants:
        if not isinstance(enfant, _Tumu):
            raise _Erreur(
                f"tumu : les enfants doivent être des tumu, pas un {_sorte(enfant)}"
            )
        branches.append(enfant)
    return _Tumu(hotu, branches)


@_texte.register(_Tumu)
@_une_fois
def _(valeur: _Tumu, imbrique: bool = False) -> str:
    """`tumu(1, tumu(2), …)`, écrit avec une pile explicite : un arbre profond
    s'écrit aussi. Seules les valeurs (`hotu`) repassent par `_texte`."""
    morceaux: list[str] = []
    pile: list[_Tumu | str] = [valeur]
    while pile:
        element = pile.pop()
        if isinstance(element, str):
            morceaux.append(element)
            continue
        morceaux.append("tumu(" + _texte(element.hotu, True))
        pile.append(")")
        for enfant in reversed(element.amaa):
            pile.extend((enfant, ", "))
    return "".join(morceaux)
