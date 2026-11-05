"""La façade du compilateur (étape 9) : la CLI, le REPL et les tests passent par ici.

Plus rien d'autre n'appelle directement le lexer, le parser ou les générateurs.
"""

from __future__ import annotations

import re
import traceback
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from types import CodeType

from .backend import Backend, Sortie
from .erreurs import (
    ErreurExecution,
    ErreursMultiples,
    ErreurSyntaxe,
    ErreurUpea,
    Position,
)
from .execution.base import _PROFONDEUR_MAX
from .formateur import Formateur
from .generateur import GenerateurPython
from .generateur_ast import GenerateurAst, compiler_module, correspondance_identite
from .lexer import tokenize
from .noeuds import Instr, Programme
from .parser import TROP_IMBRIQUE, parse
from .predefinies import ABREVIATIONS, PREDEFINIES, Predefinie
from .prelude import IMPORT_PRELUDE, PRELUDE
from .semantique import Analyse, analyser
from .sourcemap import SourceMap
from .tokens import Token
from .typage import PYTHON_COMPOSES

#: Le message d'une récursion du programme qui dépasse la limite du prélude.
RECURSION_PROFONDE = (
    f"récursion trop profonde (plus de {_PROFONDEUR_MAX:,} appels imbriqués)".replace(
        ",", " "
    )
)

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


@contextmanager
def _sans_debordement() -> Iterator[None]:
    """Seconde barrière : un `RecursionError` du compilateur devient une erreur de
    compilation. Les limites du parser l'empêchent ; la limite de récursion du
    processus, elle, peut être plus basse que prévu."""
    try:
        yield
    except RecursionError:
        raise ErreursMultiples([ErreurSyntaxe(TROP_IMBRIQUE)]) from None


def compiler(source: str, *, types: bool = True) -> Compilation:
    """Analyse syntaxique puis sémantique. Lève `ErreursMultiples`."""
    with _sans_debordement():
        programme = parse(source)
        return Compilation(programme, analyser(programme, types=types))


def transpiler(
    source: str,
    backend: str = "python",
    *,
    types: bool = True,
    prelude_externe: bool = False,
) -> Sortie:
    """Le code produit par `backend`, et la correspondance de ses lignes.

    Avec `prelude_externe`, le code importe le prélude (`upea_prelude.py`, à écrire
    à côté : `module_prelude()`) au lieu de le recopier.
    """
    generateur = choisir_backend(backend)
    if prelude_externe:
        generateur = importer_le_prelude(generateur)
    compilation = compiler(source, types=types)
    with _sans_debordement():
        return generateur.generer(compilation.programme, compilation.analyse)


def importer_le_prelude(generateur: Backend) -> Backend:
    """Le même backend, dont le code importe le prélude au lieu de le recopier."""
    match generateur:
        case GenerateurPython() | GenerateurAst():
            return type(generateur)(prelude=IMPORT_PRELUDE)
        case _:
            raise ErreurUpea(
                f"le backend '{generateur.nom}' ne produit pas de Python : "
                "il n'a pas de prélude"
            )


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


def fonctions_predefinies() -> tuple[Predefinie, ...]:
    """Les fonctions prédéfinies, dans l'ordre de leur déclaration (pour les outils)."""
    return tuple(PREDEFINIES.values())


def abreviations() -> dict[str, str]:
    """Les sortes abrégées dans leurs signatures (`arbre[T]`), et leur sens."""
    return dict(ABREVIATIONS)


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
    """Exécute du code généré ; une exception Python devient une `ErreurExecution`.

    Lève `ErreursMultiples` si CPython refuse de compiler le code (trop imbriqué).
    """
    objet = code if isinstance(code, CodeType) else _compiler_le_python(code, sourcemap)
    try:
        exec(objet, nouvel_espace() if espace is None else espace)
    except Exception as exc:
        lignes = lignes_du_programme(exc, sourcemap)
        position = Position(lignes[-1], 0) if lignes else None
        message = traduire(exc)
        # Une récursion du programme remplit la pile de ses propres appels ; une
        # liste trop imbriquée, elle, déborde dans le prélude (`specification.md`).
        if isinstance(exc, RecursionError) and len(lignes) > _PROFONDEUR_MAX // 2:
            message = RECURSION_PROFONDE
        raise ErreurExecution(message, position) from exc


def _compiler_le_python(code: str, sourcemap: SourceMap) -> CodeType:
    """`compile()`, avec un filet : les limites du parser évitent que CPython refuse
    le code généré, mais si cela arrive, c'est une erreur de compilation."""
    try:
        return compiler_module(code, NOM_FICHIER)
    except (SyntaxError, RecursionError) as exc:
        if isinstance(exc, SyntaxError) and not (exc.msg or "").startswith("too many"):
            raise  # un défaut du générateur, pas une limite : on veut le voir
        ligne = getattr(exc, "lineno", None)
        source = None if ligne is None else sourcemap.ligne_source(ligne)
        position = None if source is None else Position(source, 0)
        raise ErreursMultiples([ErreurSyntaxe(TROP_IMBRIQUE, position)]) from None


def lignes_du_programme(exc: BaseException, sourcemap: SourceMap) -> list[int]:
    """Les lignes Upea des frames du programme dans le traceback de `exc`, de la plus
    externe à la plus profonde (sans `extract_tb`, qui lirait 20 000 frames en détail
    pour une récursion trop profonde)."""
    lignes: list[int] = []
    for frame, numero in traceback.walk_tb(exc.__traceback__):
        if frame.f_code.co_filename == NOM_FICHIER and numero is not None:
            ligne = sourcemap.ligne_source(numero)
            if ligne is not None:
                lignes.append(ligne)
    return lignes


def ligne_fautive(exc: BaseException, sourcemap: SourceMap) -> int | None:
    """La ligne Upea de la frame la plus profonde qui provient du programme."""
    lignes = lignes_du_programme(exc, sourcemap)
    return lignes[-1] if lignes else None


# --- Traduction des exceptions Python -------------------------------------------------

#: Le nom Upea des sortes, d'après le nom de leur classe Python.
SORTES = {
    "int": "numera",
    "float": "tuhaa",
    "str": "parau",
    "bool": "tiahape",
    "NoneType": "aore",
    "_Branches": "tapura",  # les enfants d'un tumu (`t.amaa`)
} | {classe: sorte for sorte, classe in PYTHON_COMPOSES.items()}


def _sorte(nom_python: str) -> str:
    return SORTES.get(nom_python, nom_python)


type Traduction = Callable[[re.Match[str]], str]

#: Les messages des `TypeError` de Python, et leur traduction en termes d'Upea.
#: Ils dépendent de la version de CPython : chacun a son programme témoin dans
#: `test_etape_08_execution.py` (`CANARIS`). `roto` n'en dépend plus (`_roto`).
TRADUCTIONS: list[tuple[re.Pattern[str], Traduction]] = [
    (
        re.compile(r"unsupported operand type\(s\) for (\S+): '(\w+)' and '(\w+)'"),
        lambda m: (
            f"opération '{m[1]}' impossible entre {_sorte(m[2])} et {_sorte(m[3])}"
        ),
    ),
    (
        re.compile(r'can only concatenate (\w+) \(not "(\w+)"\) to'),
        lambda m: f"opération '+' impossible entre {_sorte(m[1])} et {_sorte(m[2])}",
    ),
    (
        re.compile(r"'(\S+)' not supported between instances of '(\w+)' and '(\w+)'"),
        lambda m: (
            f"comparaison '{m[1]}' impossible entre {_sorte(m[2])} et {_sorte(m[3])}"
        ),
    ),
    (
        re.compile(r"bad operand type for unary (\S+): '(\w+)'"),
        lambda m: (
            f"opérande de '{'eiaha' if m[1] == 'not' else m[1]}' invalide : "
            f"{_sorte(m[2])}"
        ),
    ),
    (
        re.compile(r"'(\w+)' object does not support item assignment"),
        lambda m: f"un {_sorte(m[1])} ne se modifie pas élément par élément",
    ),
    (
        re.compile(r"indices must be integers(?: or slices)?, not '?(\w+)'?"),
        lambda m: f"un indice doit être un numera, pas un {_sorte(m[1])}",
    ),
    (
        re.compile(r"'(\w+)' object is not subscriptable"),
        lambda m: f"on ne peut pas indexer un {_sorte(m[1])}",
    ),
    (
        re.compile(r"cannot be interpreted as an integer"),
        lambda _: "les bornes d'un intervalle doivent être des numera",
    ),
]


def _type_error(message: str) -> str:
    """La première traduction dont le motif reconnaît le message."""
    return next(
        (
            traduction(trouve)
            for motif, traduction in TRADUCTIONS
            if (trouve := motif.search(message))
        ),
        f"opération impossible sur ces valeurs ({message})",
    )


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
    with _sans_debordement():
        return Formateur().generer(parse(source), Analyse()).code
