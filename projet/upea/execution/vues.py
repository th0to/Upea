"""Prélude — une vue commune à toutes les sortes d'arbres.

Chaque sorte s'enregistre (`functools.singledispatch`) auprès de trois fonctions :

- `_racine(arbre)` : le nœud racine, ou `None` pour un arbre vide ;
- `_deplier(noeud)` : le contenu d'un nœud dans l'ordre infixe, une suite de
  couples (est_une_cle, objet) ; un enfant absent d'un arbre binaire vaut `None` ;
- `_etiquette(noeud)` : ce que les dessins (`hohoa`) écrivent pour ce nœud.

Les algorithmes d'arbres (`algorithmes_arbres`) ne connaissent que cette vue :
ils sont écrits une seule fois, pour toutes les sortes.
"""

from __future__ import annotations

from functools import singledispatch as _singledispatch
from typing import Any as _Any

from .arbre_b import _NoeudB, _Pupu
from .base import _Erreur, _peint, _sorte, _texte
from .recherche import _ArbreBinaire, _NoeudBinaire, _NoeudRN
from .tas import _Ahu
from .tumu import _enfants, _Tumu

#: Les sortes d'arbres, pour vérifier les arguments (`_attend`).
_ARBRE = ("arbre", (_Tumu, _ArbreBinaire, _Pupu, _Ahu))
_ORDONNE = ("arbre ordonné", (_ArbreBinaire, _Pupu, _Ahu))

type _Contenu = list[tuple[bool, _Any]]


class _NoeudTas:
    """Un nœud de tas vu comme un arbre : la case `indice` de la liste."""

    __slots__ = ("valeurs", "indice")

    def __init__(self, valeurs: list[_Any], indice: int) -> None:
        self.valeurs = valeurs
        self.indice = indice


@_singledispatch
def _racine(arbre: object) -> object:
    raise _Erreur(f"arbre attendu, {_sorte(arbre)} reçu")


@_racine.register(_Tumu)
def _(arbre: _Tumu) -> object:
    return arbre


@_racine.register(_ArbreBinaire)
def _(arbre: _ArbreBinaire) -> object:
    return arbre.racine


@_racine.register(_Pupu)
def _(arbre: _Pupu) -> object:
    return arbre.racine if arbre.racine.cles else None


@_racine.register(_Ahu)
def _(arbre: _Ahu) -> object:
    return _NoeudTas(arbre.valeurs, 0) if arbre.valeurs else None


@_singledispatch
def _deplier(noeud: object) -> _Contenu:
    raise _Erreur(f"nœud d'arbre attendu, {_sorte(noeud)} reçu")


@_deplier.register(_Tumu)
def _(noeud: _Tumu) -> _Contenu:
    """Le premier enfant, la valeur, puis les autres enfants."""
    enfants = _enfants(noeud)
    if not enfants:
        return [(True, noeud.hotu)]
    return [(False, enfants[0]), (True, noeud.hotu), *((False, e) for e in enfants[1:])]


@_deplier.register(_NoeudBinaire)
def _(noeud: _NoeudBinaire) -> _Contenu:
    return [(False, noeud.gauche), (True, noeud.cle), (False, noeud.droite)]


@_deplier.register(_NoeudB)
def _(noeud: _NoeudB) -> _Contenu:
    contenu: _Contenu = []
    for i, cle in enumerate(noeud.cles):
        if noeud.fils:
            contenu.append((False, noeud.fils[i]))
        contenu.append((True, cle))
    if noeud.fils:
        contenu.append((False, noeud.fils[-1]))
    return contenu


@_deplier.register(_NoeudTas)
def _(noeud: _NoeudTas) -> _Contenu:
    def enfant(j: int) -> _NoeudTas | None:
        return _NoeudTas(noeud.valeurs, j) if j < len(noeud.valeurs) else None

    i = noeud.indice
    return [
        (False, enfant(2 * i + 1)),
        (True, noeud.valeurs[i]),
        (False, enfant(2 * i + 2)),
    ]


def _cles(noeud: object) -> list[_Any]:
    """Les clés d'un nœud (une seule, sauf dans un arbre B)."""
    return [objet for est_cle, objet in _deplier(noeud) if est_cle]


def _positions(noeud: object) -> list[_Any]:
    """Les enfants d'un nœud ; `None` pour un enfant absent d'un arbre binaire."""
    return [objet for est_cle, objet in _deplier(noeud) if not est_cle]


def _fils(noeud: object) -> list[_Any]:
    """Les enfants présents d'un nœud."""
    return [objet for objet in _positions(noeud) if objet is not None]


def _mot(cle: object) -> str:
    """Une clé dans un dessin : sans guillemets, mais sur une seule ligne."""
    return _texte(cle).replace("\n", "\\n").replace("\t", "\\t")


@_singledispatch
def _etiquette(noeud: object, couleur: bool = False) -> str:
    """Ce que les dessins écrivent pour ce nœud ; `couleur` y ajoute les codes ANSI."""
    return " | ".join(map(_mot, _cles(noeud)))


@_etiquette.register(_NoeudRN)
def _(noeud: _NoeudRN, couleur: bool = False) -> str:
    if noeud.rouge:
        return _peint(f"{_mot(noeud.cle)} (R)", "rouge", couleur)
    return f"{_mot(noeud.cle)} (N)"


@_etiquette.register(_NoeudB)
def _(noeud: _NoeudB, couleur: bool = False) -> str:
    return "[" + " | ".join(map(_mot, noeud.cles)) + "]"
