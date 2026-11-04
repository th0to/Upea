"""Outils communs aux tests."""

import ast
import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from upea.compilateur import compiler, executer
from upea.erreurs import ErreursMultiples, ErreurUpea, Position
from upea.generateur import GenerateurPython
from upea.generateur_ast import GenerateurAst

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


class _Aplatir(ast.NodeTransformer):
    """`(a and b) and c` devient `a and b and c` : le backend ast range une suite de
    `ma` dans un seul `BoolOp`, le backend texte les parenthèse deux par deux."""

    def visit_BoolOp(self, noeud: ast.BoolOp) -> ast.BoolOp:
        self.generic_visit(noeud)
        premier = noeud.values[0]
        if isinstance(premier, ast.BoolOp) and type(premier.op) is type(noeud.op):
            noeud.values = [*premier.values, *noeud.values[1:]]
        return noeud


def arbres_python(source: str, *, types: bool = True) -> tuple[str, str]:
    """L'arbre Python du programme seul (sans prélude), tel que le produit chacun
    des deux backends, sans les positions : le texte du backend python relu, et le
    module du backend ast. Ils doivent être identiques."""
    compilation = compiler(source, types=types)
    texte, _ = GenerateurPython().traduire(
        compilation.programme.instructions, compilation.analyse
    )
    module = GenerateurAst().module(compilation.programme, compilation.analyse)
    du_texte, de_l_arbre = (
        ast.dump(_Aplatir().visit(arbre)) for arbre in (ast.parse(texte), module)
    )
    return du_texte, de_l_arbre


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
