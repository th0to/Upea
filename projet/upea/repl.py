"""Le REPL : un générateur qui reçoit des saisies par `send` et rend des réponses."""

from __future__ import annotations

import io
from collections.abc import Generator
from contextlib import redirect_stdout
from dataclasses import dataclass

from .compilateur import (
    compiler,
    executer_code,
    nouvel_espace,
    tokens,
    traduire_suite,
)
from .erreurs import ErreurLexicale, ErreurUpea, formater
from .noeuds import afficher_arbre
from .parser import DEBUTS_INSTRUCTION
from .sourcemap import SourceMap
from .tokens import TokenKind

INVITE = "upea> "
SUITE = "....> "
#: La réponse à un Ctrl-C pendant une évaluation.
INTERROMPU = "interrompu\n"
FICHIER = "<repl>"
AIDE = """\
Commandes :
  :tokens <code>   les tokens du code
  :arbre <code>    l'arbre syntaxique du code
  :python <code>   le Python généré pour le code
  :aide            cette aide
Une expression seule (sans ';' final) est affichée. Ctrl-D (Ctrl-Z sous Windows) quitte.
"""


@dataclass(frozen=True, slots=True)
class Reponse:
    """Ce que le REPL rend après chaque saisie : ce qu'il faut afficher, et
    l'invite suivante (`INVITE`, ou `SUITE` si la saisie est incomplète)."""

    sortie: str
    invite: str


def accolades_ouvertes(saisie: str) -> int:
    """Le nombre d'accolades ouvertes et pas encore fermées, comptées par le lexer
    (une accolade dans un texte ne compte pas)."""
    ouvertes = 0
    try:
        for token in tokens(saisie):
            if token.kind is TokenKind.ACC_G:
                ouvertes += 1
            elif token.kind is TokenKind.ACC_D:
                ouvertes -= 1
    except ErreurLexicale:
        return 0  # la saisie est complète, et fautive : l'analyse le dira
    return ouvertes


def envelopper(saisie: str) -> str:
    """Une expression seule devient une instruction d'affichage.

    Une saisie est une instruction si elle finit par `;`, ou si elle commence
    par un mot-clé d'instruction (`ahani … { }`) ; sinon c'est une expression, même
    terminée par `}` (`upea { 1 -> 2 }`).
    """
    texte = saisie.strip().lstrip("﻿")
    if texte.endswith(";"):
        return saisie
    try:
        premier = next(tokens(texte))
    except ErreurLexicale:
        return saisie  # l'analyse signalera l'erreur
    if premier.kind in DEBUTS_INSTRUCTION or premier.kind is TokenKind.FIN:
        return saisie
    return f"faaite {texte};"


class _Session:
    """L'état gardé d'une saisie à l'autre."""

    def __init__(self, types: bool) -> None:
        self.types = types
        self.acceptees = ""  # le source des saisies acceptées
        self.executees = 0  # le nombre d'instructions déjà exécutées
        self.espace = nouvel_espace(avec_prelude=True)
        # Chaque saisie est compilée sous son propre nom de fichier ; celles qui sont
        # retenues gardent leur carte : une fonction déclarée plus tôt garde ainsi
        # les lignes de sa saisie.
        self.saisies = 0
        self.cartes: dict[str, SourceMap] = {}

    def evaluer(self, saisie: str) -> str:
        source = self.acceptees + envelopper(saisie) + "\n"
        try:
            compilation = compiler(source, types=self.types)
        except ErreurUpea as erreur:
            return formater(erreur, source, FICHIER) + "\n"
        nouvelles = compilation.programme.instructions[self.executees :]
        code, sourcemap = traduire_suite(nouvelles, compilation.analyse)
        self.saisies += 1
        nom = f"<upea-{self.saisies}>"
        tampon = io.StringIO()
        try:
            with redirect_stdout(tampon):
                executer_code(code, sourcemap, self.espace, nom=nom, cartes=self.cartes)
        except ErreurUpea as erreur:  # d'exécution, ou de compilation (le filet)
            return tampon.getvalue() + formater(erreur, source, FICHIER) + "\n"
        except KeyboardInterrupt:
            # Ctrl-C arrête le programme, pas la session : comme une erreur, la
            # saisie n'est pas retenue, et ce qui a été déclaré avant reste.
            return tampon.getvalue() + INTERROMPU
        self.cartes[nom] = sourcemap
        self.acceptees = source
        self.executees = len(compilation.programme.instructions)
        return tampon.getvalue()

    def commande(self, ligne: str) -> str:
        nom, _, code = ligne.strip().partition(" ")
        try:
            match nom:
                case ":tokens":
                    return "".join(f"{t!r}\n" for t in tokens(code))
                case ":arbre":
                    source = envelopper(code)
                    return (
                        afficher_arbre(compiler(source, types=False).programme) + "\n"
                    )
                case ":python":
                    source = self.acceptees + envelopper(code) + "\n"
                    compilation = compiler(source, types=self.types)
                    nouvelles = compilation.programme.instructions[self.executees :]
                    return traduire_suite(nouvelles, compilation.analyse)[0]
                case ":aide":
                    return AIDE
                case _:
                    return f"commande inconnue : {nom} (essayez :aide)\n"
        except ErreurUpea as erreur:
            return formater(erreur, code, FICHIER) + "\n"


def repl(*, types: bool = True) -> Generator[Reponse, str, None]:
    """La session : chaque `send(ligne)` rend la sortie produite et l'invite suivante.

    L'état (déclarations, valeurs) survit d'une saisie à l'autre, et aux erreurs.
    Tant qu'un bloc n'est pas refermé, la saisie continue sur la ligne suivante.
    """
    session = _Session(types)
    tampon: list[str] = []
    sortie = ""
    while True:
        ligne = yield Reponse(sortie, SUITE if tampon else INVITE)
        sortie = ""
        if not tampon and ligne.strip().startswith(":"):
            sortie = session.commande(ligne)
            continue
        tampon.append(ligne)
        saisie = "\n".join(tampon)
        if accolades_ouvertes(saisie) > 0:
            continue
        tampon = []
        if saisie.strip():
            try:
                sortie = session.evaluer(saisie)
            except KeyboardInterrupt:  # pendant la compilation
                sortie = INTERROMPU
