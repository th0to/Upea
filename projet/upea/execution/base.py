"""Prélude — la base : erreurs, sortes, affichage, vérification des arguments."""

from __future__ import annotations

import io as _io
import os as _os
import sys as _sys
from collections.abc import Callable as _Callable
from functools import singledispatch as _singledispatch
from functools import wraps as _wraps
from typing import ParamSpec as _ParamSpec
from typing import TypeVar as _TypeVar

_P = _ParamSpec("_P")
_R = _TypeVar("_R")
_C = _TypeVar("_C", bound=type)

#: Le nombre d'appels qu'un programme peut imbriquer (`specification.md`, *Limites
#: assumées*) : de quoi parcourir récursivement un ABR dégénéré de 10 000 clés. La
#: limite de Python, 1 000 par défaut, est relevée ici, une seule fois : le prélude
#: est exécuté par `run`, par le REPL et par le fichier autonome.
_PROFONDEUR_MAX = 20_000
_sys.setrecursionlimit(max(_sys.getrecursionlimit(), _PROFONDEUR_MAX))

# Les entiers d'Upea ont une précision illimitée, à l'affichage aussi : Python refuse
# par défaut de convertir en texte un entier de plus de 4 300 chiffres. Cette garde
# vise les serveurs qui convertissent des nombres reçus d'inconnus ; ici, un million
# de chiffres se convertit en moins d'une seconde.
_sys.set_int_max_str_digits(0)


class _Erreur(Exception):
    """Une erreur d'exécution dont le message est déjà rédigé pour l'utilisateur."""


#: Le nom Upea de la sorte de chaque classe ; chaque structure y ajoute la sienne.
_SORTES: dict[type, str] = {
    bool: "tiahape",
    int: "numera",
    float: "tuhaa",
    str: "parau",
    type(None): "aore",
    list: "tapura",
}


def _sorte_upea(nom: str) -> _Callable[[_C], _C]:
    """Décorateur de classe : la classe représente la sorte Upea `nom`."""

    def enregistrer(classe: _C) -> _C:
        _SORTES[classe] = nom
        return classe

    return enregistrer


def _sorte(valeur: object) -> str:
    """Le nom Upea de la sorte d'une valeur."""
    return _SORTES.get(type(valeur), type(valeur).__name__)


#: Une sorte attendue : une classe, ou une description et les classes qu'elle couvre.
type _Attendu = type | tuple[str, tuple[type, ...]] | None


def _conforme(valeur: object, attendu: _Attendu) -> bool:
    if attendu is None:
        return True
    return isinstance(valeur, attendu[1] if isinstance(attendu, tuple) else attendu)


def _description(attendu: _Attendu) -> str:
    if isinstance(attendu, tuple):
        return attendu[0]
    return "?" if attendu is None else _SORTES.get(attendu, attendu.__name__)


def _attend(
    *attendus: _Attendu,
) -> _Callable[[_Callable[_P, _R]], _Callable[_P, _R]]:
    """Décorateur paramétré : vérifie la sorte des premiers arguments d'une
    fonction prédéfinie, et signale l'erreur avec le nom Upea de la fonction."""

    def decorer(fonction: _Callable[_P, _R]) -> _Callable[_P, _R]:
        nom = fonction.__name__.lstrip("_")

        @_wraps(fonction)
        def verifiee(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            for valeur, attendu in zip(args, attendus, strict=False):
                if not _conforme(valeur, attendu):
                    raise _Erreur(
                        f"{nom} : {_description(attendu)} attendu, "
                        f"{_sorte(valeur)} reçu"
                    )
            return fonction(*args, **kwargs)

        return verifiee

    return decorer


# --- Les clés des structures ordonnées ------------------------------------------------


def _verifier_cle(cle: object, sorte: str, voisine: object = None) -> None:
    """Une clé est un nombre ou un texte, comparable aux clés déjà présentes."""
    if type(cle) not in (int, float, str):
        raise _Erreur(
            f"une clé de {sorte} doit être un numera, un tuhaa ou un parau, "
            f"pas un {_sorte(cle)}"
        )
    if voisine is not None and isinstance(voisine, str) != isinstance(cle, str):
        raise _Erreur(
            f"clés incomparables dans un {sorte} : {_sorte(voisine)} et {_sorte(cle)}"
        )


# --- Affichage ------------------------------------------------------------------------


def _echappe(texte: str) -> str:
    texte = texte.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + texte.replace("\n", "\\n").replace("\t", "\\t") + '"'


#: Les structures que `_texte` est en train d'écrire (par leur `id`).
_EN_COURS: set[int] = set()


def _une_fois[V](
    ecrire: _Callable[[V, bool], str],
) -> _Callable[[V, bool], str]:
    """Décorateur des variantes de `_texte` qui écrivent une structure : une valeur
    qui se contient elle-même donne une erreur claire, et non une récursion sans
    fin. Une valeur simplement partagée (`[l, l]`) s'écrit normalement."""

    @_wraps(ecrire)
    def gardee(valeur: V, imbrique: bool = False) -> str:
        cle = id(valeur)
        if cle in _EN_COURS:
            raise _Erreur(
                f"{_sorte(valeur)} impossible à écrire : "
                "la valeur se contient elle-même"
            )
        _EN_COURS.add(cle)
        try:
            return ecrire(valeur, imbrique)
        finally:
            _EN_COURS.discard(cle)

    return gardee


@_singledispatch
def _texte(valeur: object, imbrique: bool = False) -> str:
    """Le texte d'une valeur, tel que l'affiche `faaite`.

    `imbrique` est vrai à l'intérieur d'une liste, d'un arbre ou d'un graphe :
    les textes y sont alors écrits entre guillemets. Chaque structure enregistre
    sa propre variante (`@_texte.register`).
    """
    return str(valeur)


@_texte.register(str)
def _(valeur: str, imbrique: bool = False) -> str:
    return _echappe(valeur) if imbrique else valeur


@_texte.register(bool)
def _(valeur: bool, imbrique: bool = False) -> str:
    return "tia" if valeur else "hape"


@_texte.register(int)
@_texte.register(float)
def _(valeur: float, imbrique: bool = False) -> str:
    return repr(valeur)


@_texte.register(type(None))
def _(valeur: None, imbrique: bool = False) -> str:
    return "aore"


@_texte.register(list)
@_une_fois
def _(valeur: list[object], imbrique: bool = False) -> str:
    return "[" + ", ".join(_texte(e, True) for e in valeur) + "]"


@_singledispatch
def _dessin(valeur: object, couleur: bool = False) -> str | None:
    """Le dessin sur plusieurs lignes d'un arbre ou d'un graphe, que `faaite` écrit
    quand on lui donne la structure seule ; `None` pour les autres valeurs, et pour
    une structure vide. Chaque structure enregistre le sien (`dessins`)."""
    return None


#: Les codes ANSI des couleurs du terminal.
_CODES = {"rouge": "31", "jaune": "33", "gras": "1", "terne": "2"}


def _peint(texte: str, nom: str, couleur: bool) -> str:
    """`texte` en couleur, si `couleur` est vrai."""
    return f"\x1b[{_CODES[nom]}m{texte}\x1b[0m" if couleur and texte else texte


def _couleurs_actives() -> bool:
    """Les couleurs ne vont qu'à un vrai terminal ; `NO_COLOR` les coupe et
    `FORCE_COLOR` les force (conventions no-color.org et force-color.org)."""
    if _os.environ.get("NO_COLOR"):
        return False
    if _os.environ.get("FORCE_COLOR"):
        return True
    return _sys.stdout.isatty()


def _en_utf8(flux: object) -> None:
    """Passe un flux de texte en UTF-8. Sous Windows, une sortie redirigée vers un
    fichier est en cp1252, qui n'a ni les traits des dessins (`┌─┴─┐`, `→`) ni
    bien des lettres (`ʻ`) : `print` y lèverait `UnicodeEncodeError`."""
    if isinstance(flux, _io.TextIOWrapper) and flux.encoding.lower() not in (
        "utf-8",
        "utf8",
    ):
        flux.reconfigure(encoding="utf-8")


_en_utf8(_sys.stdout)


def _affiche(*valeurs: object) -> None:
    """`faaite` : une structure seule est dessinée, le reste écrit sur une ligne."""
    if len(valeurs) == 1:
        dessin = _dessin(valeurs[0], _couleurs_actives())
        if dessin is not None:
            print(dessin)
            return
    print(" ".join(_texte(v) for v in valeurs))
