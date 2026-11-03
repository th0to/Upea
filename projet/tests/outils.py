"""Outils communs aux tests."""

import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from upea.compilateur import compiler, executer
from upea.erreurs import ErreursMultiples, ErreurUpea, Position

PROJET = Path(__file__).resolve().parent.parent
EXEMPLES = PROJET / "exemples"
LISTE_EXEMPLES = sorted(EXEMPLES.glob("*.upea"))


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def lancer(source: str, backend: str = "python", *, types: bool = True) -> str:
    """Exécute `source` et renvoie ce qu'il a affiché."""
    tampon = io.StringIO()
    with redirect_stdout(tampon):
        executer(source, backend, types=types)
    return tampon.getvalue()


def erreurs_de_compilation(source: str, *, types: bool = True) -> list[ErreurUpea]:
    """Les erreurs (syntaxe, sémantique, types) que la compilation de `source` lève."""
    with pytest.raises(ErreursMultiples) as info:
        compiler(source, types=types)
    return info.value.erreurs


def une_erreur(source: str, *, types: bool = True) -> ErreurUpea:
    """L'unique erreur que la compilation de `source` doit lever."""
    erreurs = erreurs_de_compilation(source, types=types)
    assert len(erreurs) == 1, [str(e) for e in erreurs]
    return erreurs[0]


def position(erreur: ErreurUpea) -> tuple[int, int]:
    assert isinstance(erreur.position, Position)
    return erreur.position.ligne, erreur.position.colonne
