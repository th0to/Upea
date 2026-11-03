"""Positions dans le source, hiérarchie des erreurs d'Upea, et leur mise en forme."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Position:
    """Une position dans le source, numérotée à partir de 1 comme dans un éditeur.

    Une colonne à 0 signifie « colonne inconnue » (erreurs d'exécution).
    """

    ligne: int
    colonne: int

    def __str__(self) -> str:
        if self.colonne == 0:
            return f"ligne {self.ligne}"
        return f"ligne {self.ligne}, colonne {self.colonne}"

    def decale(self, colonnes: int) -> Position:
        """La position située `colonnes` caractères plus loin sur la même ligne."""
        return Position(self.ligne, self.colonne + colonnes)


#: Position par défaut des nœuds construits à la main (dans les tests).
SANS_POSITION = Position(0, 0)


class ErreurUpea(Exception):
    """Racine de toutes les erreurs signalées à l'utilisateur."""

    genre = "erreur"

    def __init__(self, message: str, position: Position | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.position = position

    def __str__(self) -> str:
        if self.position is None:
            return f"{self.genre} : {self.message}"
        return f"{self.position} : {self.genre} : {self.message}"


class ErreurLexicale(ErreurUpea):
    genre = "erreur lexicale"


class ErreurSyntaxe(ErreurUpea):
    genre = "erreur de syntaxe"


class ErreurSemantique(ErreurUpea):
    genre = "erreur sémantique"


class ErreurType(ErreurSemantique):
    genre = "erreur de type"


class Avertissement(ErreurUpea):
    """Pas une erreur : un problème probable qui n'empêche pas l'exécution."""

    genre = "avertissement"


class ErreurExecution(ErreurUpea):
    genre = "erreur d'exécution"


class ErreursMultiples(ErreurUpea):
    """Regroupe toutes les erreurs d'une phase, pour les signaler en une fois."""

    def __init__(self, erreurs: list[ErreurUpea]) -> None:
        nombre = len(erreurs)
        super().__init__(f"{nombre} erreur{'s' if nombre > 1 else ''}")
        self.erreurs = erreurs

    def __str__(self) -> str:
        return "\n".join(str(erreur) for erreur in self.erreurs)


def formater(erreur: ErreurUpea, source: str = "", fichier: str = "<source>") -> str:
    """Le message prêt à afficher : `fichier:ligne:colonne : genre : message`.

    Il est suivi de la ligne fautive et d'un `^` sous la colonne. Une
    `ErreursMultiples` donne un bloc par erreur.
    """
    if isinstance(erreur, ErreursMultiples):
        return "\n".join(formater(e, source, fichier) for e in erreur.erreurs)
    position = erreur.position
    if position is None or position.ligne < 1:
        return f"{fichier} : {erreur.genre} : {erreur.message}"
    lignes = source.splitlines()
    if position.colonne == 0:
        entete = f"{fichier}:{position.ligne} : {erreur.genre} : {erreur.message}"
    else:
        entete = (
            f"{fichier}:{position.ligne}:{position.colonne} : "
            f"{erreur.genre} : {erreur.message}"
        )
    if position.ligne > len(lignes):
        return entete
    ligne = lignes[position.ligne - 1]
    resultat = f"{entete}\n    {ligne}"
    if position.colonne > 0:
        # On recopie les tabulations pour que le ^ tombe au bon endroit.
        avant = "".join(c if c == "\t" else " " for c in ligne[: position.colonne - 1])
        resultat += f"\n    {avant}^"
    return resultat
