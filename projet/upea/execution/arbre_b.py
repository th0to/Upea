"""Prélude — l'arbre B (`pupu`) d'ordre m : au plus m enfants et m - 1 clés par
nœud, au moins ⌈m/2⌉ - 1 clés hors de la racine, toutes les feuilles au même niveau.

L'insertion éclate un nœud plein en remontant sa clé médiane ; le retrait emprunte
une clé à un frère, ou fusionne deux frères.
"""

from __future__ import annotations

import bisect as _bisect
from collections.abc import Iterable as _Iterable
from collections.abc import Iterator as _Iterator
from typing import Any as _Any

from .base import _Erreur, _sorte_upea, _texte, _verifier_cle


class _NoeudB:
    __slots__ = ("cles", "fils")

    def __init__(self, cles: list[_Any], fils: list[_NoeudB]) -> None:
        self.cles = cles
        self.fils = fils  # vide pour une feuille

    @property
    def feuille(self) -> bool:
        return not self.fils


@_sorte_upea("pupu")
class _Pupu:
    __slots__ = ("ordre", "racine", "taille")
    sorte = "pupu"

    def __init__(self, cles: _Iterable[_Any] = (), ordre: int = 3) -> None:
        if type(ordre) is not int or ordre < 3:
            raise _Erreur(f"l'ordre d'un arbre B (pupu) est au moins 3, pas {ordre}")
        self.ordre = ordre
        self.racine = _NoeudB([], [])
        self.taille = 0
        for cle in cles:
            self.ajouter(cle)

    @property
    def minimum(self) -> int:
        """Le nombre minimal de clés d'un nœud qui n'est pas la racine."""
        return (self.ordre + 1) // 2 - 1

    # --- Recherche et parcours ------------------------------------------------------

    def __contains__(self, cle: object) -> bool:
        if not self.racine.cles or type(cle) not in (int, float, str):
            return False
        if isinstance(cle, str) != isinstance(self.racine.cles[0], str):
            return False
        noeud = self.racine
        while True:
            i = _bisect.bisect_left(noeud.cles, cle)
            if i < len(noeud.cles) and noeud.cles[i] == cle:
                return True
            if noeud.feuille:
                return False
            noeud = noeud.fils[i]

    def __iter__(self) -> _Iterator[_Any]:
        def infixe(noeud: _NoeudB) -> _Iterator[_Any]:
            for i, cle in enumerate(noeud.cles):
                if not noeud.feuille:
                    yield from infixe(noeud.fils[i])
                yield cle
            if not noeud.feuille:
                yield from infixe(noeud.fils[-1])

        return infixe(self.racine)

    def __eq__(self, autre: object) -> bool:
        return (
            isinstance(autre, _Pupu)
            and self.ordre == autre.ordre
            and list(self) == list(autre)
        )

    def min(self) -> _Any:
        noeud = self.racine
        while not noeud.feuille:
            noeud = noeud.fils[0]
        return noeud.cles[0]

    def max(self) -> _Any:
        noeud = self.racine
        while not noeud.feuille:
            noeud = noeud.fils[-1]
        return noeud.cles[-1]

    def __repr__(self) -> str:
        return _texte(self, True)

    # --- Insertion --------------------------------------------------------------------

    def ajouter(self, cle: _Any) -> bool:
        voisine = self.racine.cles[0] if self.racine.cles else None
        _verifier_cle(cle, self.sorte, voisine)
        if cle in self:
            return False
        promue = self._ajouter(self.racine, cle)
        if promue is not None:  # la racine a éclaté : l'arbre grandit d'un niveau
            mediane, droite = promue
            self.racine = _NoeudB([mediane], [self.racine, droite])
        self.taille += 1
        return True

    def _ajouter(self, noeud: _NoeudB, cle: _Any) -> tuple[_Any, _NoeudB] | None:
        """Ajoute `cle` sous `noeud` ; rend (médiane, nœud droit) si `noeud` éclate."""
        i = _bisect.bisect_left(noeud.cles, cle)
        if noeud.feuille:
            noeud.cles.insert(i, cle)
        else:
            promue = self._ajouter(noeud.fils[i], cle)
            if promue is not None:
                mediane, droite = promue
                noeud.cles.insert(i, mediane)
                noeud.fils.insert(i + 1, droite)
        if len(noeud.cles) < self.ordre:
            return None
        milieu = len(noeud.cles) // 2
        mediane = noeud.cles[milieu]
        droite = _NoeudB(noeud.cles[milieu + 1 :], noeud.fils[milieu + 1 :])
        noeud.cles, noeud.fils = noeud.cles[:milieu], noeud.fils[: milieu + 1]
        return mediane, droite

    # --- Retrait ----------------------------------------------------------------------

    def retirer(self, cle: _Any) -> bool:
        if cle not in self:
            return False
        self._retirer(self.racine, cle)
        if not self.racine.cles and self.racine.fils:
            self.racine = self.racine.fils[0]  # l'arbre perd un niveau
        self.taille -= 1
        return True

    def _retirer(self, noeud: _NoeudB, cle: _Any) -> None:
        i = _bisect.bisect_left(noeud.cles, cle)
        if i < len(noeud.cles) and noeud.cles[i] == cle:
            if noeud.feuille:
                del noeud.cles[i]
                return
            # Un nœud interne : on remplace la clé par son prédécesseur.
            predecesseur = noeud.fils[i]
            while not predecesseur.feuille:
                predecesseur = predecesseur.fils[-1]
            noeud.cles[i] = predecesseur.cles[-1]
            self._retirer(noeud.fils[i], noeud.cles[i])
        else:
            self._retirer(noeud.fils[i], cle)
        self._reparer(noeud, i)

    def _reparer(self, parent: _NoeudB, i: int) -> None:
        """Le fils `i` a peut-être trop peu de clés : emprunt, sinon fusion."""
        fils = parent.fils[i]
        if len(fils.cles) >= self.minimum:
            return
        gauche = parent.fils[i - 1] if i > 0 else None
        droite = parent.fils[i + 1] if i + 1 < len(parent.fils) else None
        if gauche is not None and len(gauche.cles) > self.minimum:
            fils.cles.insert(0, parent.cles[i - 1])
            parent.cles[i - 1] = gauche.cles.pop()
            if gauche.fils:
                fils.fils.insert(0, gauche.fils.pop())
        elif droite is not None and len(droite.cles) > self.minimum:
            fils.cles.append(parent.cles[i])
            parent.cles[i] = droite.cles.pop(0)
            if droite.fils:
                fils.fils.append(droite.fils.pop(0))
        elif gauche is not None:
            gauche.cles += [parent.cles.pop(i - 1), *fils.cles]
            gauche.fils += fils.fils
            parent.fils.pop(i)
        elif droite is not None:
            fils.cles += [parent.cles.pop(i), *droite.cles]
            fils.fils += droite.fils
            parent.fils.pop(i + 1)


def _pupu(cles: list[_Any], ordre: int = 3) -> _Pupu:
    return _Pupu(cles, ordre)


@_texte.register(_Pupu)
def _(valeur: _Pupu, imbrique: bool = False) -> str:
    cles = ", ".join(_texte(c, True) for c in valeur)
    return f"pupu {valeur.ordre} [{cles}]"
