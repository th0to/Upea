"""Prélude — les dessins des arbres et des graphes : `hohoa`, `matrice`, et ce que
`faaite` écrit pour une structure seule (`_dessin`).

Les arbres binaires (`imi`, `aifaito`, `uteere`, `ahu`) se dessinent de haut en bas ;
les `tumu`, les arbres B et un arbre binaire trop large se dessinent en retrait, et
un graphe en liste d'adjacence. La mise en page se calcule sur le texte sans
couleur : les codes ANSI ne s'ajoutent qu'à la fin, et ne décalent rien.
"""

from __future__ import annotations

from typing import Any as _Any

from .arbre_b import _Pupu
from .base import _attend, _dessin, _peint, _texte
from .graphes import _sur_graphe, _Upea
from .recherche import _ArbreBinaire, _NoeudRN
from .tas import _Ahu
from .tumu import _Tumu
from .vues import _ARBRE, _etiquette, _mot, _positions, _racine

#: Au-delà de cette largeur, un arbre binaire se dessine en retrait.
_LARGEUR_MAX = 80
#: L'espace entre les sous-arbres gauche et droit d'un dessin de haut en bas.
_ECART = 3

_STRUCTURE = ("arbre ou upea", (*_ARBRE[1], _Upea))


# --- Le dessin en retrait -------------------------------------------------------------


def _dessin_retrait(racine: object, couleur: bool) -> str:
    """Le dessin en retrait ; dans un arbre binaire, `·` marque un enfant absent."""
    lignes: list[str] = []
    # (nœud, début de sa ligne, début des lignes de ses enfants)
    pile: list[tuple[_Any, str, str]] = [(racine, "", "")]
    while pile:
        noeud, ligne, suite = pile.pop()
        debut = _peint(ligne, "terne", couleur)
        if noeud is None:
            lignes.append(debut + _peint("·", "terne", couleur))
            continue
        lignes.append(debut + _etiquette(noeud, couleur))
        positions = _positions(noeud)
        if all(p is None for p in positions):
            continue
        dernier = len(positions) - 1
        pile.extend(
            reversed(
                [
                    (
                        enfant,
                        suite + ("└── " if i == dernier else "├── "),
                        suite + ("    " if i == dernier else "│   "),
                    )
                    for i, enfant in enumerate(positions)
                ]
            )
        )
    return "\n".join(lignes)


# --- Le dessin de haut en bas ---------------------------------------------------------


class _Bloc:
    """Le dessin d'un sous-arbre binaire : des lignes de même largeur, la colonne de
    sa racine, et la place (ligne, colonne, nœud) de chaque étiquette."""

    __slots__ = ("lignes", "centre", "places")

    def __init__(
        self, lignes: list[str], centre: int, places: list[tuple[int, int, _Any]]
    ) -> None:
        self.lignes = lignes
        self.centre = centre
        self.places = places

    @property
    def largeur(self) -> int:
        return len(self.lignes[0])

    def ligne(self, i: int) -> str:
        return self.lignes[i] if i < len(self.lignes) else " " * self.largeur


def _milieu(noeud: object, etiquette: str) -> int:
    """La colonne de l'étiquette où arrivent les traits : le milieu de la clé, sans
    la marque `(R)` / `(N)` du rouge-noir."""
    largeur = len(_mot(noeud.cle)) if isinstance(noeud, _NoeudRN) else len(etiquette)
    return (largeur - 1) // 2


def _assembler(noeud: object, gauche: _Bloc | None, droite: _Bloc | None) -> _Bloc:
    """Le bloc d'un nœud : son étiquette, la ligne qui le relie à ses enfants
    (`┌─┴─┐`, ou `┌─┘` et `└─┐` pour un enfant seul), puis les blocs des enfants."""
    etiquette = _etiquette(noeud)
    milieu = _milieu(noeud, etiquette)
    if gauche is None and droite is None:
        return _Bloc([etiquette], milieu, [(0, 0, noeud)])
    # Les colonnes sont comptées depuis le premier bloc ; le bloc droit commence en x.
    x = 0 if gauche is None else gauche.largeur + _ECART
    if gauche is not None and droite is not None:
        a, b = gauche.centre, x + droite.centre
        racine = (a + b) // 2
        traits = {a: "┌", racine: "┴", b: "┐"}
    elif gauche is not None:
        a = gauche.centre
        racine = b = a + 2
        traits = {a: "┌", racine: "┘"}
    else:
        assert droite is not None
        b = droite.centre
        racine = a = b - 2
        traits = {a: "└", b: "┐"}
    debut = racine - milieu
    d = max(0, -debut)  # le décalage qui garde l'étiquette dans le bloc
    largeur = d + max(
        0 if gauche is None else gauche.largeur,
        0 if droite is None else x + droite.largeur,
        debut + len(etiquette),
    )
    liaison = [" "] * largeur
    for colonne in range(a, b + 1):
        liaison[d + colonne] = traits.get(colonne, "─")
    lignes = [(" " * (d + debut) + etiquette).ljust(largeur), "".join(liaison)]
    hauteur = max(len(bloc.lignes) for bloc in (gauche, droite) if bloc is not None)
    for i in range(hauteur):
        texte = "" if gauche is None else gauche.ligne(i)
        if droite is not None:
            texte = texte.ljust(x) + droite.ligne(i)
        lignes.append((" " * d + texte).ljust(largeur))
    places: list[tuple[int, int, _Any]] = [(0, d + debut, noeud)]
    for decalage, bloc in ((d, gauche), (d + x, droite)):
        if bloc is not None:
            places.extend((rang + 2, c + decalage, n) for rang, c, n in bloc.places)
    return _Bloc(lignes, d + racine, places)


def _colorer(bloc: _Bloc) -> list[str]:
    """Les lignes du bloc avec leurs couleurs : les étiquettes colorées remplacent
    les simples, de droite à gauche pour ne pas décaler les suivantes."""
    lignes = [ligne.rstrip() for ligne in bloc.lignes]
    for rang, c, noeud in sorted(bloc.places, key=lambda place: -place[1]):
        fin = c + len(_etiquette(noeud))
        lignes[rang] = lignes[rang][:c] + _etiquette(noeud, True) + lignes[rang][fin:]
    # Une ligne sur deux ne porte que des traits.
    return [
        _peint(ligne, "terne", True) if i % 2 else ligne
        for i, ligne in enumerate(lignes)
    ]


def _dessin_vertical(racine: object, couleur: bool) -> str | None:
    """Le dessin de haut en bas d'un arbre binaire, ou `None` s'il dépasse
    `_LARGEUR_MAX` colonnes. Les blocs s'assemblent des feuilles vers la racine,
    sans récursion : un arbre dégénéré ne sature pas la pile."""
    ordre: list[tuple[_Any, list[_Any]]] = []  # préfixe : un parent avant ses enfants
    pile = [racine]
    while pile:
        noeud = pile.pop()
        positions = _positions(noeud)
        ordre.append((noeud, positions))
        pile.extend(p for p in positions if p is not None)
    blocs: dict[int, _Bloc] = {}
    for noeud, positions in reversed(ordre):
        gauche, droite = (None if p is None else blocs.pop(id(p)) for p in positions)
        bloc = _assembler(noeud, gauche, droite)
        if bloc.largeur > _LARGEUR_MAX:
            return None
        blocs[id(noeud)] = bloc
    bloc = blocs[id(racine)]
    lignes = _colorer(bloc) if couleur else [ligne.rstrip() for ligne in bloc.lignes]
    return "\n".join(lignes)


# --- Les dessins de chaque sorte ------------------------------------------------------


@_dessin.register(_ArbreBinaire)
@_dessin.register(_Ahu)
def _(arbre: object, couleur: bool = False) -> str | None:
    racine = _racine(arbre)
    if racine is None:
        return None
    return _dessin_vertical(racine, couleur) or _dessin_retrait(racine, couleur)


@_dessin.register(_Tumu)
@_dessin.register(_Pupu)
def _(arbre: object, couleur: bool = False) -> str | None:
    racine = _racine(arbre)
    return None if racine is None else _dessin_retrait(racine, couleur)


def _compte(nombre: int, mot: str) -> str:
    return f"{nombre} {mot}{'s' if nombre > 1 else ''}"


@_dessin.register(_Upea)
def _(graphe: _Upea, couleur: bool = False) -> str | None:
    """La liste d'adjacence : une ligne par nœud, ses successeurs et leurs poids."""
    if not graphe._arcs:
        return None
    noms = {noeud: _mot(noeud) for noeud in graphe._arcs}
    largeur = max(map(len, noms.values()))
    arcs = sum(map(len, graphe._arcs.values()))
    lignes = [f"upea : {_compte(len(noms), 'nœud')}, {_compte(arcs, 'arc')}"]
    for noeud, voisins in graphe._arcs.items():
        nom = _peint(noms[noeud], "gras", couleur) + " " * (largeur - len(noms[noeud]))
        if not voisins:
            lignes.append(f"{nom} {_peint('·', 'terne', couleur)}")
            continue
        suite = ", ".join(
            noms[voisin]
            + (
                ""
                if poids == 1
                else " " + _peint(f"({_texte(poids)})", "jaune", couleur)
            )
            for voisin, poids in voisins.items()
        )
        lignes.append(f"{nom} {_peint('→', 'terne', couleur)} {suite}")
    return "\n".join(lignes)


# --- Les fonctions prédéfinies --------------------------------------------------------


@_attend(_STRUCTURE)
def _hohoa(structure: object) -> str:
    """Le dessin d'un arbre ou d'un graphe, sans couleur ; `(vide)` s'il est vide."""
    return _dessin(structure) or "(vide)"


@_sur_graphe()
def _matrice(graphe: _Upea) -> str:
    """La matrice d'adjacence : le poids de l'arc de chaque ligne vers chaque
    colonne, `·` s'il n'y en a pas."""
    if not graphe._arcs:
        return "(vide)"
    noeuds = list(graphe._arcs)
    noms = [_mot(noeud) for noeud in noeuds]
    cases = [
        [_texte(graphe._arcs[a][b]) if b in graphe._arcs[a] else "·" for b in noeuds]
        for a in noeuds
    ]
    largeurs = [
        max(len(nom), *(len(ligne[j]) for ligne in cases)) for j, nom in enumerate(noms)
    ]
    marge = max(map(len, noms))

    def ligne(debut: str, textes: list[str]) -> str:
        return debut.ljust(marge) + "".join(
            f" {texte:>{taille}}"
            for texte, taille in zip(textes, largeurs, strict=True)
        )

    rangees = (ligne(nom, rangee) for nom, rangee in zip(noms, cases, strict=True))
    return "\n".join([ligne("", noms), *rangees])
