"""La façade du compilateur (étape 9) : la CLI, le REPL et les tests passent par ici.

Plus rien d'autre n'appelle directement le lexer, le parser ou les générateurs.
"""

from __future__ import annotations

import re
import traceback
from collections.abc import Iterator
from dataclasses import dataclass
from types import CodeType

from .backend import Backend, Sortie
from .erreurs import ErreurExecution, ErreurUpea, Position
from .formateur import Formateur
from .generateur import GenerateurPython
from .generateur_ast import GenerateurAst, compiler_module, correspondance_identite
from .lexer import tokenize
from .noeuds import Instr, Programme
from .parser import parse
from .prelude import PRELUDE
from .semantique import Analyse, analyser
from .sourcemap import SourceMap
from .tokens import Token

#: Le nom de fichier du code généré, pour reconnaître ses lignes dans un traceback.
NOM_FICHIER = "<upea>"
NOM_PRELUDE = "<upea-prelude>"

BACKENDS: dict[str, Backend] = {
    b.nom: b for b in (GenerateurPython(), GenerateurAst(), Formateur())
}


@dataclass(frozen=True, slots=True)
class Compilation:
    programme: Programme
    analyse: Analyse


def choisir_backend(nom: str) -> Backend:
    try:
        return BACKENDS[nom]
    except KeyError:
        disponibles = ", ".join(sorted(BACKENDS))
        raise ErreurUpea(
            f"backend inconnu : '{nom}' (disponibles : {disponibles})"
        ) from None


def compiler(source: str, *, types: bool = True) -> Compilation:
    """Analyse syntaxique puis sémantique. Lève `ErreursMultiples`."""
    programme = parse(source)
    return Compilation(programme, analyser(programme, types=types))


def transpiler(source: str, backend: str = "python", *, types: bool = True) -> Sortie:
    """Le code produit par `backend`, et la correspondance de ses lignes."""
    generateur = choisir_backend(backend)
    compilation = compiler(source, types=types)
    return generateur.generer(compilation.programme, compilation.analyse)


def executer(source: str, backend: str = "python", *, types: bool = True) -> None:
    """Compile et exécute `source` ; l'affichage va sur `sys.stdout`.

    Lève `ErreursMultiples` (compilation) ou `ErreurExecution` (exécution).
    """
    generateur = choisir_backend(backend)
    if not generateur.executable:
        raise ErreurUpea(f"le backend '{backend}' ne produit pas de Python exécutable")
    sortie = transpiler(source, backend, types=types)
    executer_code(sortie.code, sortie.sourcemap)


def executer_arbre(source: str, *, types: bool = True) -> None:
    """Exécute source en compilant directement l'arbre st, sans texte."""
    compilation = compiler(source, types=types)
    module = GenerateurAst().module(compilation.programme, compilation.analyse)
    code = compiler_module(module, NOM_FICHIER)
    executer_code(
        code, correspondance_identite(module), nouvel_espace(avec_prelude=True)
    )


def tokens(source: str) -> Iterator[Token]:
    """Les tokens de source (pour le REPL et les outils)."""
    return tokenize(source)


def traduire_suite(
    instructions: tuple[Instr, ...], analyse: Analyse
) -> tuple[str, SourceMap]:
    """Le Python de quelques instructions, sans prélude (pour le REPL)."""
    return GenerateurPython().traduire(instructions, analyse)


def nouvel_espace(avec_prelude: bool = False) -> dict[str, object]:
    """Un espace de noms d'exécution, éventuellement déjà muni du prélude."""
    espace: dict[str, object] = {"__name__": "__main__"}
    if avec_prelude:
        exec(compile(PRELUDE, NOM_PRELUDE, "exec"), espace)
    return espace


def executer_code(
    code: str | CodeType, sourcemap: SourceMap, espace: dict[str, object] | None = None
) -> None:
    """Exécute du code généré ; une exception Python devient une `ErreurExecution`."""
    objet = code if isinstance(code, CodeType) else compile(code, NOM_FICHIER, "exec")
    try:
        exec(objet, nouvel_espace() if espace is None else espace)
    except Exception as exc:
        ligne = ligne_fautive(exc, sourcemap)
        position = None if ligne is None else Position(ligne, 0)
        raise ErreurExecution(traduire(exc), position) from exc


def ligne_fautive(exc: BaseException, sourcemap: SourceMap) -> int | None:
    """La ligne Upea de la frame la plus profonde qui provient du programme."""
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        if frame.filename == NOM_FICHIER and frame.lineno is not None:
            ligne = sourcemap.ligne_source(frame.lineno)
            if ligne is not None:
                return ligne
    return None


# --- Traduction des exceptions Python -------------------------------------------------

SORTES = {
    "int": "numera",
    "float": "tuhaa",
    "str": "parau",
    "bool": "tiahape",
    "NoneType": "aore",
    "list": "tapura",
    "_Tumu": "tumu",
    "_Upea": "upea",
}


def _sorte(nom_python: str) -> str:
    return SORTES.get(nom_python, nom_python)


def _type_error(message: str) -> str:
    if m := re.search(
        r"unsupported operand type\(s\) for (\S+): '(\w+)' and '(\w+)'", message
    ):
        return f"opération '{m[1]}' impossible entre {_sorte(m[2])} et {_sorte(m[3])}"
    if m := re.search(r'can only concatenate (\w+) \(not "(\w+)"\) to', message):
        return f"opération '+' impossible entre {_sorte(m[1])} et {_sorte(m[2])}"
    if m := re.search(
        r"'(\S+)' not supported between instances of '(\w+)' and '(\w+)'", message
    ):
        return f"comparaison '{m[1]}' impossible entre {_sorte(m[2])} et {_sorte(m[3])}"
    if m := re.search(r"bad operand type for unary (\S+): '(\w+)'", message):
        operateur = "eiaha" if m[1] == "not" else m[1]
        return f"opérande de '{operateur}' invalide : {_sorte(m[2])}"
    if m := re.search(r"'(\w+)' object does not support item assignment", message):
        return f"un {_sorte(m[1])} ne se modifie pas élément par élément"
    if m := re.search(
        r"indices must be integers(?: or slices)?, not '?(\w+)'?", message
    ):
        return f"un indice doit être un numera, pas un {_sorte(m[1])}"
    if m := re.search(r"'(\w+)' object is not subscriptable", message):
        return f"on ne peut pas indexer un {_sorte(m[1])}"
    if m := re.search(r"argument of type '(\w+)' is not iterable", message):
        return f"roto : on ne peut pas chercher dans un {_sorte(m[1])}"
    if m := re.search(
        r"'in <string>' requires string as left operand, not (\w+)", message
    ):
        return f"roto : on ne cherche qu'un parau dans un parau, pas un {_sorte(m[1])}"
    if "cannot be interpreted as an integer" in message:
        return "les bornes d'un intervalle doivent être des numera"
    return f"opération impossible sur ces valeurs ({message})"


def traduire(exc: BaseException) -> str:
    """Le message, en français et en termes d'Upea, d'une exception Python."""
    if type(exc).__name__ == "_Erreur":  # levée par le prélude, déjà rédigée
        return str(exc)
    match exc:
        case ZeroDivisionError():
            return "division par zéro"
        case IndexError():
            return "indice hors limites"
        case RecursionError():
            return "récursion trop profonde"
        case AttributeError():
            m = re.search(r"'(\w+)' object has no attribute", str(exc))
            sorte = f", pas un {_sorte(m[1])}" if m else ""
            return f"seul un tumu a les champs hotu et amaa{sorte}"
        case TypeError():
            return _type_error(str(exc))
        case OverflowError():
            return "nombre trop grand"
        case _:
            return f"erreur inattendue ({type(exc).__name__} : {exc})"


def mettre_en_forme(source: str) -> str:
    """Le source réécrit dans sa présentation canonique (sans analyse sémantique)."""
    return Formateur().generer(parse(source), Analyse()).code
