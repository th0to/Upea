"""La ligne de commande : `python -m upea run|transpile|check|fmt|repl|mcp`."""

from __future__ import annotations

import argparse
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path

from .compilateur import (
    BACKENDS,
    choisir_backend,
    compiler,
    executer,
    mettre_en_forme,
    transpiler,
)
from .erreurs import ErreurExecution, ErreursMultiples, ErreurUpea, formater
from .execution.base import _en_utf8
from .prelude import MODULE_PRELUDE, module_prelude
from .repl import repl

OK, ERREUR_COMPILATION, ERREUR_USAGE, ERREUR_EXECUTION = 0, 1, 2, 3

BANNIERE = (
    "Upea — :aide pour l'aide, Ctrl-D (Ctrl-Z puis Entrée sous Windows) pour quitter."
)


def _erreur(message: str) -> None:
    print(message, file=sys.stderr)


def _lire(fichier: str) -> str | None:
    try:
        return Path(fichier).read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        _erreur(f"upea : fichier introuvable : {fichier}")
    except IsADirectoryError:
        _erreur(f"upea : {fichier} est un dossier, pas un fichier")
    except UnicodeDecodeError:
        _erreur(f"upea : {fichier} n'est pas un texte UTF-8")
    except OSError as erreur:
        _erreur(f"upea : impossible de lire {fichier} ({erreur.strerror})")
    return None


def _avertissements(source: str, fichier: str, types: bool) -> None:
    """Affiche les avertissements ; lève `ErreursMultiples` s'il y a des erreurs."""
    for avertissement in compiler(source, types=types).analyse.avertissements:
        _erreur(formater(avertissement, source, fichier))


def commande_run(args: argparse.Namespace) -> int:
    source = _lire(args.fichier)
    if source is None:
        return ERREUR_COMPILATION
    try:
        backend = choisir_backend(args.backend)
        if not backend.executable:
            _erreur(
                f"upea : le backend '{args.backend}' "
                "ne produit pas de Python exécutable"
            )
            return ERREUR_USAGE
        _avertissements(source, args.fichier, args.types)
        executer(source, args.backend, types=args.types)
    except ErreursMultiples as erreurs:
        _erreur(formater(erreurs, source, args.fichier))
        return ERREUR_COMPILATION
    except ErreurExecution as erreur:
        sys.stdout.flush()
        if args.trace and erreur.__cause__ is not None:
            cause = erreur.__cause__
            _erreur("".join(traceback.format_exception(cause)).rstrip())
        _erreur(formater(erreur, source, args.fichier))
        return ERREUR_EXECUTION
    except ErreurUpea as erreur:
        _erreur(f"upea : {erreur.message}")
        return ERREUR_USAGE
    return OK


def commande_transpile(args: argparse.Namespace) -> int:
    if args.sourcemap and args.sortie is None:
        _erreur("upea : --sourcemap demande un fichier de sortie (-o)")
        return ERREUR_USAGE
    externe = args.prelude == "externe"
    if externe and args.sortie is None:
        _erreur("upea : --prelude externe demande un fichier de sortie (-o)")
        return ERREUR_USAGE
    if externe and Path(args.sortie).name == f"{MODULE_PRELUDE}.py":
        _erreur(
            f"upea : le fichier de sortie ne peut pas s'appeler {MODULE_PRELUDE}.py, "
            "le nom du prélude"
        )
        return ERREUR_USAGE
    source = _lire(args.fichier)
    if source is None:
        return ERREUR_COMPILATION
    try:
        sortie = transpiler(
            source, args.backend, types=args.types, prelude_externe=externe
        )
    except ErreursMultiples as erreurs:
        _erreur(formater(erreurs, source, args.fichier))
        return ERREUR_COMPILATION
    except ErreurUpea as erreur:
        _erreur(f"upea : {erreur.message}")
        return ERREUR_USAGE
    if args.sortie is None:
        sys.stdout.write(sortie.code)
        return OK
    destination = Path(args.sortie)
    destination.write_text(sortie.code, encoding="utf-8")
    if externe:
        prelude = destination.with_name(f"{MODULE_PRELUDE}.py")
        prelude.write_text(module_prelude(), encoding="utf-8")
    if args.sourcemap:
        carte = destination.with_name(destination.name + ".map.json")
        sortie.sourcemap.nommer(args.fichier).ecrire(carte)
    return OK


def commande_check(args: argparse.Namespace) -> int:
    source = _lire(args.fichier)
    if source is None:
        return ERREUR_COMPILATION
    try:
        _avertissements(source, args.fichier, args.types)
    except ErreursMultiples as erreurs:
        _erreur(formater(erreurs, source, args.fichier))
        return ERREUR_COMPILATION
    print(f"{args.fichier} : aucune erreur")
    return OK


def commande_fmt(args: argparse.Namespace) -> int:
    source = _lire(args.fichier)
    if source is None:
        return ERREUR_COMPILATION
    try:
        resultat = mettre_en_forme(source)
    except ErreursMultiples as erreurs:
        _erreur(formater(erreurs, source, args.fichier))
        return ERREUR_COMPILATION
    if args.ecrire:
        Path(args.fichier).write_text(resultat, encoding="utf-8")
    else:
        sys.stdout.write(resultat)
    return OK


def commande_repl(args: argparse.Namespace) -> int:
    session = repl(types=args.types)
    reponse = next(session)
    print(BANNIERE)
    while True:
        try:
            ligne = input(reponse.invite)
        except EOFError:
            print()
            return OK
        except KeyboardInterrupt:
            print()
            continue
        reponse = session.send(ligne)
        print(reponse.sortie, end="")


#: Les modules dont l'absence signifie « le SDK MCP n'est pas installé ».
MODULES_DU_SDK = frozenset({"mcp", "mcp_types", "pydantic"})


def commande_mcp(args: argparse.Namespace) -> int:
    try:
        from .serveur_mcp import lancer
    except ModuleNotFoundError as absent:
        if (absent.name or "").partition(".")[0] not in MODULES_DU_SDK:
            raise
        _erreur(
            "upea : le serveur MCP demande le SDK Python `mcp` (version 2), "
            "absent de cet environnement.\n"
            "  Pour l'installer, depuis la racine du dépôt : uv sync --group mcp"
        )
        return ERREUR_USAGE
    return lancer()


def construire_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="upea",
        description="Upea : un langage aux mots-clés tahitiens, transpilé en Python.",
    )
    sous = parser.add_subparsers(dest="commande", required=True, metavar="commande")
    backends = sorted(BACKENDS)

    def ajouter(nom: str, aide: str) -> argparse.ArgumentParser:
        commande = sous.add_parser(nom, help=aide, description=aide)
        commande.add_argument("fichier", help="le programme Upea (.upea)")
        return commande

    def sans_types(commande: argparse.ArgumentParser) -> None:
        commande.add_argument(
            "--sans-types",
            dest="types",
            action="store_false",
            help="ne pas vérifier les types (extension 12)",
        )

    run = ajouter("run", "exécute un programme")
    run.add_argument("--backend", default="python", choices=backends)
    run.add_argument(
        "--trace", action="store_true", help="affiche aussi le traceback Python"
    )
    sans_types(run)
    run.set_defaults(action=commande_run)

    transpile = ajouter("transpile", "affiche ou écrit le code généré")
    transpile.add_argument("--backend", default="python", choices=backends)
    transpile.add_argument("-o", dest="sortie", help="le fichier à écrire")
    transpile.add_argument(
        "--sourcemap", action="store_true", help="écrit aussi <sortie>.map.json"
    )
    transpile.add_argument(
        "--prelude",
        default="inclus",
        choices=["inclus", "externe"],
        help=(
            "inclus : le prélude est recopié en tête du fichier (par défaut) ; "
            f"externe : il est écrit à côté, dans {MODULE_PRELUDE}.py, et importé"
        ),
    )
    sans_types(transpile)
    transpile.set_defaults(action=commande_transpile)

    check = ajouter("check", "vérifie un programme sans l'exécuter")
    sans_types(check)
    check.set_defaults(action=commande_check)

    fmt = ajouter(
        "fmt",
        "réécrit un programme dans sa présentation canonique "
        "(les commentaires sont perdus)",
    )
    fmt.add_argument(
        "--ecrire", action="store_true", help="réécrit le fichier en place"
    )
    fmt.set_defaults(action=commande_fmt)

    session = sous.add_parser("repl", help="session interactive")
    sans_types(session)
    session.set_defaults(action=commande_repl)

    serveur = sous.add_parser(
        "mcp",
        help="serveur MCP en stdio, pour qu'une IA écrive et vérifie de l'Upea",
        description=(
            "Serveur MCP (Model Context Protocol) en stdio : la spécification, les "
            "exemples, et les outils verifier, executer, transpiler et formater. "
            "Demande le SDK `mcp` : uv sync --group mcp."
        ),
    )
    serveur.set_defaults(action=commande_mcp)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    # Les dessins et les lignes de source citées dans les erreurs ne passent pas
    # toujours dans l'encodage d'une sortie redirigée (cp1252 sous Windows).
    _en_utf8(sys.stdout)
    _en_utf8(sys.stderr)
    parser = construire_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as sortie:  # argparse : --help, ou erreur d'utilisation
        return sortie.code if isinstance(sortie.code, int) else ERREUR_USAGE
    action = args.action
    assert callable(action)
    code = action(args)
    assert isinstance(code, int)
    return code
