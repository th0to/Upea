"""Prélude — les arbres binaires de recherche : l'ABR (`imi`), l'AVL (`aifaito`) et
le rouge-noir (`uteere`, dans la variante « penchée à gauche » de Sedgewick, qui
respecte les invariants rouge-noir avec des rééquilibrages plus courts).

Ce sont des ensembles ordonnés : une clé déjà présente n'est pas ajoutée deux fois.
Les clés sont des valeurs Upea vérifiées à l'exécution (`_verifier_cle`), d'où leur
type `_Any` ici.
"""

from __future__ import annotations

from collections.abc import Iterable as _Iterable
from collections.abc import Iterator as _Iterator
from typing import Any as _Any

from .base import _sorte_upea, _texte, _verifier_cle


class _NoeudBinaire:
    __slots__ = ("cle", "gauche", "droite", "hauteur", "rouge")

    def __init__(self, cle: _Any, rouge: bool = False) -> None:
        self.cle = cle
        self.gauche: _NoeudBinaire | None = None
        self.droite: _NoeudBinaire | None = None
        self.hauteur = 1  # pour l'AVL
        self.rouge = rouge  # pour le rouge-noir


class _NoeudRN(_NoeudBinaire):
    """Un nœud de rouge-noir : un type à part, pour en dessiner la couleur."""

    __slots__ = ()


class _ArbreBinaire:
    """Ce que partagent les trois arbres : recherche, parcours, minimum, égalité.

    Chaque sous-classe ne fournit que `_ajouter` et `_retirer`, qui rendent la
    nouvelle racine du sous-arbre (rééquilibré s'il y a lieu).
    """

    __slots__ = ("racine", "taille")
    sorte = "?"

    def __init__(self, cles: _Iterable[_Any] = ()) -> None:
        self.racine: _NoeudBinaire | None = None
        self.taille = 0
        for cle in cles:
            self.ajouter(cle)

    def ajouter(self, cle: _Any) -> bool:
        voisine = None if self.racine is None else self.racine.cle
        _verifier_cle(cle, self.sorte, voisine)
        avant = self.taille
        self.racine = self._ajouter(self.racine, cle)
        return self.taille > avant

    def retirer(self, cle: _Any) -> bool:
        if cle not in self:
            return False
        self.racine = self._retirer(self.racine, cle)
        self.taille -= 1
        return True

    def _ajouter(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire:
        raise NotImplementedError

    def _retirer(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire | None:
        raise NotImplementedError

    def __contains__(self, cle: object) -> bool:
        noeud = self.racine
        if noeud is None or type(cle) not in (int, float, str):
            return False
        if isinstance(cle, str) != isinstance(noeud.cle, str):
            return False
        while noeud is not None:
            if cle == noeud.cle:
                return True
            noeud = noeud.gauche if cle < noeud.cle else noeud.droite
        return False

    def __iter__(self) -> _Iterator[_Any]:
        """Les clés dans l'ordre croissant (parcours infixe, sans récursion)."""
        pile: list[_NoeudBinaire] = []
        noeud = self.racine
        while pile or noeud is not None:
            while noeud is not None:
                pile.append(noeud)
                noeud = noeud.gauche
            noeud = pile.pop()
            yield noeud.cle
            noeud = noeud.droite

    def __eq__(self, autre: object) -> bool:
        return (
            isinstance(autre, _ArbreBinaire)
            and type(self) is type(autre)
            and list(self) == list(autre)
        )

    def min(self) -> _Any:
        noeud = self.racine
        assert noeud is not None
        while noeud.gauche is not None:
            noeud = noeud.gauche
        return noeud.cle

    def max(self) -> _Any:
        noeud = self.racine
        assert noeud is not None
        while noeud.droite is not None:
            noeud = noeud.droite
        return noeud.cle

    def __repr__(self) -> str:
        return _texte(self, True)


# --- L'ABR simple (imi), sans rééquilibrage, écrit sans récursion ---------------------


@_sorte_upea("imi")
class _Imi(_ArbreBinaire):
    __slots__ = ()
    sorte = "imi"

    def _ajouter(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire:
        nouveau = _NoeudBinaire(cle)
        if noeud is None:
            self.taille += 1
            return nouveau
        courant = noeud
        while cle != courant.cle:
            if cle < courant.cle:
                if courant.gauche is None:
                    courant.gauche = nouveau
                    self.taille += 1
                    break
                courant = courant.gauche
            else:
                if courant.droite is None:
                    courant.droite = nouveau
                    self.taille += 1
                    break
                courant = courant.droite
        return noeud

    def _retirer(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire | None:
        assert noeud is not None
        parent, courant = None, noeud
        while courant.cle != cle:
            parent = courant
            suivant = courant.gauche if cle < courant.cle else courant.droite
            assert suivant is not None
            courant = suivant
        if courant.gauche is not None and courant.droite is not None:
            # Deux enfants : on prend la clé du successeur, puis on retire celui-ci.
            parent, successeur = courant, courant.droite
            while successeur.gauche is not None:
                parent, successeur = successeur, successeur.gauche
            courant.cle = successeur.cle
            courant = successeur
        enfant = courant.gauche if courant.gauche is not None else courant.droite
        if parent is None:
            return enfant
        if parent.gauche is courant:
            parent.gauche = enfant
        else:
            parent.droite = enfant
        return noeud


# --- L'AVL (aifaito) ------------------------------------------------------------------


def _h(noeud: _NoeudBinaire | None) -> int:
    return 0 if noeud is None else noeud.hauteur


def _mettre_a_jour(noeud: _NoeudBinaire) -> None:
    noeud.hauteur = 1 + max(_h(noeud.gauche), _h(noeud.droite))


def _rotation_droite_avl(noeud: _NoeudBinaire) -> _NoeudBinaire:
    pivot = noeud.gauche
    assert pivot is not None
    noeud.gauche, pivot.droite = pivot.droite, noeud
    _mettre_a_jour(noeud)
    _mettre_a_jour(pivot)
    return pivot


def _rotation_gauche_avl(noeud: _NoeudBinaire) -> _NoeudBinaire:
    pivot = noeud.droite
    assert pivot is not None
    noeud.droite, pivot.gauche = pivot.gauche, noeud
    _mettre_a_jour(noeud)
    _mettre_a_jour(pivot)
    return pivot


def _equilibrer_avl(noeud: _NoeudBinaire) -> _NoeudBinaire:
    _mettre_a_jour(noeud)
    facteur = _h(noeud.gauche) - _h(noeud.droite)
    if facteur > 1:
        assert noeud.gauche is not None
        if _h(noeud.gauche.gauche) < _h(noeud.gauche.droite):
            noeud.gauche = _rotation_gauche_avl(noeud.gauche)  # cas gauche-droite
        return _rotation_droite_avl(noeud)
    if facteur < -1:
        assert noeud.droite is not None
        if _h(noeud.droite.droite) < _h(noeud.droite.gauche):
            noeud.droite = _rotation_droite_avl(noeud.droite)  # cas droite-gauche
        return _rotation_gauche_avl(noeud)
    return noeud


@_sorte_upea("aifaito")
class _Aifaito(_ArbreBinaire):
    __slots__ = ()
    sorte = "aifaito"

    def _ajouter(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire:
        if noeud is None:
            self.taille += 1
            return _NoeudBinaire(cle)
        if cle < noeud.cle:
            noeud.gauche = self._ajouter(noeud.gauche, cle)
        elif cle > noeud.cle:
            noeud.droite = self._ajouter(noeud.droite, cle)
        else:
            return noeud
        return _equilibrer_avl(noeud)

    def _retirer(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire | None:
        assert noeud is not None
        if cle < noeud.cle:
            noeud.gauche = self._retirer(noeud.gauche, cle)
        elif cle > noeud.cle:
            noeud.droite = self._retirer(noeud.droite, cle)
        else:
            if noeud.gauche is None or noeud.droite is None:
                return noeud.gauche if noeud.gauche is not None else noeud.droite
            successeur = noeud.droite
            while successeur.gauche is not None:
                successeur = successeur.gauche
            noeud.cle = successeur.cle
            noeud.droite = self._retirer(noeud.droite, successeur.cle)
        return _equilibrer_avl(noeud)


# --- Le rouge-noir (uteere), penché à gauche ------------------------------------------


def _rouge(noeud: _NoeudBinaire | None) -> bool:
    return noeud is not None and noeud.rouge


def _rotation_gauche_rn(noeud: _NoeudBinaire) -> _NoeudBinaire:
    pivot = noeud.droite
    assert pivot is not None
    noeud.droite, pivot.gauche = pivot.gauche, noeud
    pivot.rouge, noeud.rouge = noeud.rouge, True
    return pivot


def _rotation_droite_rn(noeud: _NoeudBinaire) -> _NoeudBinaire:
    pivot = noeud.gauche
    assert pivot is not None
    noeud.gauche, pivot.droite = pivot.droite, noeud
    pivot.rouge, noeud.rouge = noeud.rouge, True
    return pivot


def _inverser_couleurs(noeud: _NoeudBinaire) -> None:
    assert noeud.gauche is not None and noeud.droite is not None
    noeud.rouge = not noeud.rouge
    noeud.gauche.rouge = not noeud.gauche.rouge
    noeud.droite.rouge = not noeud.droite.rouge


def _equilibrer_rn(noeud: _NoeudBinaire) -> _NoeudBinaire:
    if _rouge(noeud.droite) and not _rouge(noeud.gauche):
        noeud = _rotation_gauche_rn(noeud)
    if (
        _rouge(noeud.gauche)
        and noeud.gauche is not None
        and _rouge(noeud.gauche.gauche)
    ):
        noeud = _rotation_droite_rn(noeud)
    if _rouge(noeud.gauche) and _rouge(noeud.droite):
        _inverser_couleurs(noeud)
    return noeud


def _rouge_a_gauche(noeud: _NoeudBinaire) -> _NoeudBinaire:
    _inverser_couleurs(noeud)
    assert noeud.droite is not None
    if _rouge(noeud.droite.gauche):
        noeud.droite = _rotation_droite_rn(noeud.droite)
        noeud = _rotation_gauche_rn(noeud)
        _inverser_couleurs(noeud)
    return noeud


def _rouge_a_droite(noeud: _NoeudBinaire) -> _NoeudBinaire:
    _inverser_couleurs(noeud)
    assert noeud.gauche is not None
    if _rouge(noeud.gauche.gauche):
        noeud = _rotation_droite_rn(noeud)
        _inverser_couleurs(noeud)
    return noeud


def _retirer_min_rn(noeud: _NoeudBinaire) -> _NoeudBinaire | None:
    if noeud.gauche is None:
        return None
    if not _rouge(noeud.gauche) and not _rouge(noeud.gauche.gauche):
        noeud = _rouge_a_gauche(noeud)
    assert noeud.gauche is not None
    noeud.gauche = _retirer_min_rn(noeud.gauche)
    return _equilibrer_rn(noeud)


@_sorte_upea("uteere")
class _Uteere(_ArbreBinaire):
    __slots__ = ()
    sorte = "uteere"

    def ajouter(self, cle: _Any) -> bool:
        ajoutee = super().ajouter(cle)
        assert self.racine is not None
        self.racine.rouge = False
        return ajoutee

    def _ajouter(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire:
        if noeud is None:
            self.taille += 1
            return _NoeudRN(cle, rouge=True)
        if cle < noeud.cle:
            noeud.gauche = self._ajouter(noeud.gauche, cle)
        elif cle > noeud.cle:
            noeud.droite = self._ajouter(noeud.droite, cle)
        return _equilibrer_rn(noeud)

    def retirer(self, cle: _Any) -> bool:
        racine = self.racine
        if cle not in self or racine is None:
            return False
        if not _rouge(racine.gauche) and not _rouge(racine.droite):
            racine.rouge = True
        self.racine = self._retirer(racine, cle)
        if self.racine is not None:
            self.racine.rouge = False
        self.taille -= 1
        return True

    def _retirer(self, noeud: _NoeudBinaire | None, cle: _Any) -> _NoeudBinaire | None:
        assert noeud is not None
        if cle < noeud.cle:
            assert noeud.gauche is not None
            if not _rouge(noeud.gauche) and not _rouge(noeud.gauche.gauche):
                noeud = _rouge_a_gauche(noeud)
            noeud.gauche = self._retirer(noeud.gauche, cle)
        else:
            if _rouge(noeud.gauche):
                noeud = _rotation_droite_rn(noeud)
            if cle == noeud.cle and noeud.droite is None:
                return None
            assert noeud.droite is not None
            if not _rouge(noeud.droite) and not _rouge(noeud.droite.gauche):
                noeud = _rouge_a_droite(noeud)
            if cle == noeud.cle:
                successeur = noeud.droite
                assert successeur is not None
                while successeur.gauche is not None:
                    successeur = successeur.gauche
                noeud.cle = successeur.cle
                assert noeud.droite is not None
                noeud.droite = _retirer_min_rn(noeud.droite)
            else:
                noeud.droite = self._retirer(noeud.droite, cle)
        return _equilibrer_rn(noeud)


# --- Constructeurs et affichage -------------------------------------------------------


def _imi(cles: list[_Any]) -> _Imi:
    return _Imi(cles)


def _aifaito(cles: list[_Any]) -> _Aifaito:
    return _Aifaito(cles)


def _uteere(cles: list[_Any]) -> _Uteere:
    return _Uteere(cles)


@_texte.register(_ArbreBinaire)
def _(valeur: _ArbreBinaire, imbrique: bool = False) -> str:
    return f"{valeur.sorte} [" + ", ".join(_texte(c, True) for c in valeur) + "]"
