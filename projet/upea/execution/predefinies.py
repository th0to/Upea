"""Prélude — les fonctions prédéfinies communes à plusieurs sortes, les conversions,
et ce que parcourt la boucle `tataitahi`."""

from __future__ import annotations

import re as _re
from typing import Any as _Any

from .algorithmes_arbres import (
    _largeur,
    _noeuds_largeur,
    _noeuds_prefixe,
    _prefixe,
    _taille,
)
from .arbre_b import _Pupu
from .base import _attend, _echappe, _Erreur, _sorte, _texte
from .graphes import _parcours_graphe, _Upea
from .recherche import _ArbreBinaire
from .tas import _Ahu
from .tumu import _Tumu
from .vues import _ARBRE, _ORDONNE

_ORDONNES = _ORDONNE[1]
_COLLECTION = ("tapura ou arbre ordonné", (list, *_ORDONNES))
_RETIRABLE = ("tapura, upea ou arbre ordonné", (list, _Upea, *_ORDONNES))
_AJOUTABLE = _RETIRABLE  # `amui` ajoute un élément, une clé, ou un nœud

# --- Mesure et collections ------------------------------------------------------------


def _roa(valeur: object) -> int:
    if isinstance(valeur, str | list):
        return len(valeur)
    if isinstance(valeur, _Upea):
        return len(valeur._arcs)
    if isinstance(valeur, _ARBRE[1]):
        return _taille(valeur)
    raise _Erreur(f"roa : impossible de mesurer un {_sorte(valeur)}")


@_attend(_AJOUTABLE)
def _amui(collection: _Any, valeur: object) -> None:
    """Ajoute à la fin d'une liste, dans un arbre ordonné, ou un nœud à un graphe
    (sans effet s'il y est déjà, comme pour la clé d'un arbre de recherche)."""
    if isinstance(collection, list):
        collection.append(valeur)
    else:
        collection.ajouter(valeur)


@_attend(_RETIRABLE)
def _tatara(collection: _Any, valeur: object) -> bool:
    if isinstance(collection, list):
        if valeur not in collection:
            return False
        collection.remove(valeur)
        return True
    if isinstance(collection, _Upea):
        return collection.retirer_noeud(valeur)
    retiree: bool = collection.retirer(valeur)
    return retiree


#: Là où `roto` cherche : un élément, une valeur de nœud, un nœud ou une clé.
_CONTENEURS = (list, _Tumu, _Upea, *_ORDONNES)


def _roto(valeur: object, conteneur: object) -> bool:
    """`valeur roto conteneur`. Les sortes sont vérifiées ici, et non d'après le
    message de la `TypeError` de Python, qui change d'une version à l'autre."""
    if isinstance(conteneur, str):
        if not isinstance(valeur, str):
            raise _Erreur(
                "roto : on ne cherche qu'un parau dans un parau, "
                f"pas un {_sorte(valeur)}"
            )
        return valeur in conteneur
    if isinstance(conteneur, _CONTENEURS):
        return valeur in conteneur
    raise _Erreur(f"roto : on ne peut pas chercher dans un {_sorte(conteneur)}")


def _non_vide(collection: _Any, fonction: str) -> None:
    if _roa(collection) == 0:
        raise _Erreur(f"{fonction} : le {_sorte(collection)} est vide")


@_attend(_ORDONNE)
def _iriti(collection: _Any) -> _Any:
    """Le sommet d'un tas, ou la plus petite clé d'un arbre, que l'on retire."""
    _non_vide(collection, "iriti")
    if isinstance(collection, _Ahu):
        return collection.iriti()
    plus_petite = collection.min()
    collection.retirer(plus_petite)
    return plus_petite


@_attend(_COLLECTION)
def _iti(collection: _Any) -> _Any:
    _non_vide(collection, "iti")
    return min(collection) if isinstance(collection, list) else collection.min()


@_attend(_COLLECTION)
def _rahi(collection: _Any) -> _Any:
    _non_vide(collection, "rahi")
    return max(collection) if isinstance(collection, list) else collection.max()


# --- Conversions ----------------------------------------------------------------------

_ENTIER = _re.compile(r"[+-]?[0-9]+")
_DECIMAL = _re.compile(r"[+-]?[0-9]+(\.[0-9]+)?")


def _numera(valeur: object) -> int:
    if isinstance(valeur, bool | int):
        return int(valeur)
    if isinstance(valeur, float):
        if valeur != valeur or valeur in (float("inf"), float("-inf")):
            raise _Erreur(
                f"conversion impossible : {_texte(valeur)} n'est pas un numera"
            )
        return int(valeur)
    if isinstance(valeur, str) and _ENTIER.fullmatch(valeur.strip()):
        return int(valeur.strip())
    if isinstance(valeur, str):
        raise _Erreur(f"conversion impossible : {_echappe(valeur)} n'est pas un numera")
    raise _Erreur(
        f"conversion impossible : un {_sorte(valeur)} ne devient pas un numera"
    )


def _tuhaa(valeur: object) -> float:
    if isinstance(valeur, int | float) and not isinstance(valeur, bool):
        return float(valeur)
    if isinstance(valeur, str) and _DECIMAL.fullmatch(valeur.strip()):
        return float(valeur.strip())
    if isinstance(valeur, str):
        raise _Erreur(f"conversion impossible : {_echappe(valeur)} n'est pas un tuhaa")
    raise _Erreur(
        f"conversion impossible : un {_sorte(valeur)} ne devient pas un tuhaa"
    )


def _parau(valeur: object) -> str:
    return _texte(valeur)


# --- La boucle tataitahi --------------------------------------------------------------

_SANS = object()


def _parcours(
    valeur: object, depart: object = _SANS, mode: str | None = None
) -> list[object]:
    """Ce que parcourt `tataitahi`, fixé au début de la boucle."""
    if isinstance(valeur, _Upea):
        if depart is _SANS:
            if mode is not None:
                raise _Erreur(
                    f"un parcours '{mode}' d'un upea demande un point de départ : "
                    "ajoutez 'mai'"
                )
            return list(valeur._arcs)
        return _parcours_graphe(valeur, depart, mode == "aano")
    if depart is not _SANS:
        raise _Erreur(f"'mai' ne s'emploie qu'avec un upea, pas un {_sorte(valeur)}")
    if isinstance(valeur, _Tumu):  # les nœuds (sous-arbres) eux-mêmes
        if mode == "aano":
            return [noeud for noeud, _ in _noeuds_largeur(valeur)]
        return list(_noeuds_prefixe(valeur))
    if isinstance(valeur, _ArbreBinaire | _Pupu | _Ahu):  # les clés
        if mode == "aano":
            return _largeur(valeur)
        if mode == "hohonu":
            return _prefixe(valeur)
        return list(valeur)  # dans l'ordre trié (ou de priorité, pour un tas)
    if isinstance(valeur, list | str):
        if mode is not None:
            raise _Erreur(
                f"'{mode}' ne s'emploie qu'avec un tumu, un upea ou un arbre ordonné, "
                f"pas un {_sorte(valeur)}"
            )
        return list(valeur)
    raise _Erreur(f"on ne peut pas parcourir un {_sorte(valeur)}")
