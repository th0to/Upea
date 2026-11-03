"""Prélude — l'export des arbres et des graphes vers Graphviz (`dot`) et Mermaid
(`mermaid`) : un texte que ces outils transforment en image.

Les nœuds s'appellent `n0`, `n1`… et leur texte va dans une étiquette, ce qui évite
qu'un nœud `1` et un nœud `"1"` se confondent.
"""

from __future__ import annotations

from itertools import count as _count
from typing import Any as _Any

from .arbre_b import _NoeudB
from .base import _attend, _texte
from .dessins import _STRUCTURE
from .graphes import _liaisons, _Upea
from .recherche import _NoeudRN
from .vues import _etiquette, _mot, _positions, _racine

#: Un nœud exporté : son nom, et le nœud d'arbre (`None` : une place vide).
type _Place = tuple[str, _Any]


def _plan_arbre(arbre: object) -> tuple[list[_Place], list[tuple[str, str, bool]]]:
    """Les nœuds de l'arbre et ses liens (départ, arrivée, visible). Un enfant
    absent d'un nœud binaire qui a l'autre devient une place invisible : l'enfant
    présent garde ainsi son côté, gauche ou droit."""
    noms = (f"n{i}" for i in _count())
    places: list[_Place] = []
    liens: list[tuple[str, str, bool]] = []
    racine = _racine(arbre)
    pile: list[_Place] = [] if racine is None else [(next(noms), racine)]
    while pile:
        nom, noeud = pile.pop()
        places.append((nom, noeud))
        if noeud is None:
            continue
        positions = _positions(noeud)
        if all(p is None for p in positions):
            continue
        enfants = [(next(noms), p) for p in positions]
        liens.extend((nom, enfant, p is not None) for enfant, p in enfants)
        pile.extend(reversed(enfants))
    return places, liens


def _rouge(noeud: object) -> bool:
    return isinstance(noeud, _NoeudRN) and noeud.rouge


def _noms_graphe(graphe: _Upea) -> dict[object, str]:
    return {noeud: f"n{i}" for i, noeud in enumerate(graphe._arcs)}


def _poids(poids: object) -> str | None:
    """Le texte d'un poids, ou `None` pour le poids 1, qui ne s'écrit pas."""
    return None if poids == 1 else _texte(poids)


# --- Graphviz -------------------------------------------------------------------------


def _chaine_dot(texte: str) -> str:
    return (
        '"' + texte.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'
    )


def _attributs(**valeurs: str | None) -> str:
    morceaux = [
        f"{nom}={valeur}" for nom, valeur in valeurs.items() if valeur is not None
    ]
    return f" [{', '.join(morceaux)}]" if morceaux else ""


def _dot_arbre(arbre: object) -> list[str]:
    places, liens = _plan_arbre(arbre)
    lignes = ["  ordering=out;"]
    for nom, noeud in places:
        if noeud is None:
            lignes.append(f'  {nom} [label="", style=invis];')
            continue
        rouge = "red" if _rouge(noeud) else None
        lignes.append(
            f"  {nom}"
            + _attributs(
                label=_chaine_dot(_texte_noeud(noeud)),
                shape="box" if isinstance(noeud, _NoeudB) else None,
                color=rouge,
                fontcolor=rouge,
            )
            + ";"
        )
    lignes.extend(
        f"  {a} -> {b}{'' if visible else _attributs(style='invis')};"
        for a, b, visible in liens
    )
    return lignes


def _dot_graphe(graphe: _Upea) -> list[str]:
    noms = _noms_graphe(graphe)
    lignes = [f"  {nom} [label={_chaine_dot(_mot(n))}];" for n, nom in noms.items()]
    for a, b, poids, double in _liaisons(graphe):
        if b is None:
            continue
        texte = _poids(poids)
        lignes.append(
            f"  {noms[a]} -> {noms[b]}"
            + _attributs(
                label=None if texte is None else _chaine_dot(texte),
                dir="both" if double else None,
            )
            + ";"
        )
    return lignes


# --- Mermaid --------------------------------------------------------------------------


def _chaine_mermaid(texte: str) -> str:
    return '"' + texte.replace('"', "#quot;").replace("\n", "<br>") + '"'


def _mermaid_arbre(arbre: object) -> list[str]:
    places, liens = _plan_arbre(arbre)
    lignes = ["flowchart TD"]
    for nom, noeud in places:
        if noeud is None:
            lignes.append(f'  {nom}[" "]')
            lignes.append(f"  style {nom} fill:none,stroke:none")
        else:
            lignes.append(f"  {nom}[{_chaine_mermaid(_texte_noeud(noeud))}]")
    lignes.extend(f"  {a} {'-->' if visible else '~~~'} {b}" for a, b, visible in liens)
    rouges = [nom for nom, noeud in places if _rouge(noeud)]
    if rouges:
        lignes.append("  classDef rouge fill:#fdd,stroke:#c00,color:#c00")
        lignes.append(f"  class {','.join(rouges)} rouge")
    return lignes


def _mermaid_graphe(graphe: _Upea) -> list[str]:
    noms = _noms_graphe(graphe)
    lignes = ["flowchart LR"]
    lignes.extend(f"  {nom}[{_chaine_mermaid(_mot(n))}]" for n, nom in noms.items())
    for a, b, poids, double in _liaisons(graphe):
        if b is None:
            continue
        texte = _poids(poids)
        fleche = ("<-->" if double else "-->") + ("" if texte is None else f"|{texte}|")
        lignes.append(f"  {noms[a]} {fleche} {noms[b]}")
    return lignes


# --- Les fonctions prédéfinies --------------------------------------------------------


def _texte_noeud(noeud: object) -> str:
    """Le texte d'un nœud exporté : celui des dessins, sans la marque de couleur
    du rouge-noir (la couleur de l'image la remplace) ni les crochets d'un nœud
    d'arbre B (la boîte les remplace)."""
    if isinstance(noeud, _NoeudRN):
        return _mot(noeud.cle)
    if isinstance(noeud, _NoeudB):
        return " | ".join(map(_mot, noeud.cles))
    return _etiquette(noeud)


@_attend(_STRUCTURE)
def _dot(structure: object) -> str:
    """Le texte Graphviz d'un arbre ou d'un graphe (`dot -Tsvg` en fait une image)."""
    if isinstance(structure, _Upea):
        corps = _dot_graphe(structure)
    else:
        corps = _dot_arbre(structure)
    return "\n".join(["digraph {", *corps, "}"])


@_attend(_STRUCTURE)
def _mermaid(structure: object) -> str:
    """Le texte Mermaid d'un arbre ou d'un graphe."""
    if isinstance(structure, _Upea):
        return "\n".join(_mermaid_graphe(structure))
    return "\n".join(_mermaid_arbre(structure))
