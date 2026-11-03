"""Prélude — les arbres n-aires `tumu`."""

from __future__ import annotations

from .base import _Erreur, _sorte, _sorte_upea, _texte


@_sorte_upea("tumu")
class _Tumu:
    """Un nœud d'arbre n-aire : une valeur (`hotu`) et des enfants (`amaa`)."""

    __slots__ = ("hotu", "amaa")

    def __init__(self, hotu: object, amaa: list[_Tumu]) -> None:
        self.hotu = hotu
        self.amaa = amaa

    def __eq__(self, autre: object) -> bool:
        return (
            isinstance(autre, _Tumu)
            and self.hotu == autre.hotu
            and self.amaa == autre.amaa
        )

    def __contains__(self, valeur: object) -> bool:
        pile = [self]
        while pile:
            noeud = pile.pop()
            if noeud.hotu == valeur:
                return True
            pile.extend(_enfants(noeud))
        return False

    def __repr__(self) -> str:
        return _texte(self, True)


def _enfants(noeud: _Tumu) -> list[_Tumu]:
    """Les enfants d'un nœud, après avoir vérifié qu'ils sont bien des `tumu`."""
    if not isinstance(noeud.amaa, list):
        raise _Erreur(
            f"les branches d'un tumu forment une tapura, pas un {_sorte(noeud.amaa)}"
        )
    for enfant in noeud.amaa:
        if not isinstance(enfant, _Tumu):
            raise _Erreur(
                f"les branches d'un tumu doivent être des tumu, pas un {_sorte(enfant)}"
            )
    return noeud.amaa


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
def _(valeur: _Tumu, imbrique: bool = False) -> str:
    morceaux = [_texte(valeur.hotu, True)]
    morceaux.extend(_texte(enfant, True) for enfant in valeur.amaa)
    return "tumu(" + ", ".join(morceaux) + ")"
