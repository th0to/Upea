"""Le lexer : du texte source à une suite paresseuse de tokens."""

from __future__ import annotations

import unicodedata
from collections.abc import Iterator

from .erreurs import ErreurLexicale, Position
from .tokens import MOTS_CLES, SYMBOLES, Token, TokenKind

ECHAPPEMENTS = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}

#: Conseils pour des caractères qui ne sont pas des symboles d'Upea.
CONSEILS = {
    "!": " (pour « différent », écrivez '!=')",
    "&": " (pour « et », écrivez 'ma')",
    "|": " (pour « ou », écrivez 'anei')",
    "'": " (les textes s'écrivent entre guillemets droits \")",
}


def _est_debut_identifiant(c: str) -> bool:
    return c.isalpha()


def _est_suite_identifiant(c: str) -> bool:
    return c.isalnum() or c == "_"


def tokenize(source: str) -> Iterator[Token]:
    """Découpe `source` en tokens, le dernier étant toujours `FIN`.

    Lève `ErreurLexicale` (avec la position fautive) sur un caractère inconnu,
    un texte ou un commentaire non terminé, un échappement invalide, un nombre
    ou un identifiant mal formé.
    """
    # Une marque d'ordre des octets (BOM) en tête, laissée par certains éditeurs,
    # est ignorée ; les colonnes de la première ligne ne la comptent pas.
    i = 1 if source.startswith("﻿") else 0
    ligne = 1
    debut_ligne = i
    n = len(source)

    def position(indice: int) -> Position:
        return Position(ligne, indice - debut_ligne + 1)

    while i < n:
        c = source[i]

        # Blancs et sauts de ligne
        if c == "\n":
            i += 1
            ligne += 1
            debut_ligne = i
            continue
        if c in " \t\r":
            i += 1
            continue

        # Commentaires
        if source.startswith("//", i):
            while i < n and source[i] != "\n":
                i += 1
            continue
        if source.startswith("/*", i):
            ouverture = position(i)
            fin = source.find("*/", i + 2)
            if fin < 0:
                raise ErreurLexicale("commentaire /* jamais refermé", ouverture)
            for j in range(i, fin):
                if source[j] == "\n":
                    ligne += 1
                    debut_ligne = j + 1
            i = fin + 2
            continue

        # Nombres
        if c.isdigit() and c.isascii():
            debut = i
            while i < n and source[i].isdigit() and source[i].isascii():
                i += 1
            kind = TokenKind.ENTIER
            if i < n and source[i] == ".":
                suivant = source[i + 1] if i + 1 < n else ""
                if suivant.isdigit() and suivant.isascii():
                    i += 1
                    while i < n and source[i].isdigit() and source[i].isascii():
                        i += 1
                    kind = TokenKind.DECIMAL
                elif suivant != ".":
                    raise ErreurLexicale(
                        "décimal incomplet : il faut un chiffre après le point "
                        f"(écrivez {source[debut:i]}.0)",
                        position(i),
                    )
            if i < n and _est_suite_identifiant(source[i]):
                fin_mot = i
                while fin_mot < n and _est_suite_identifiant(source[fin_mot]):
                    fin_mot += 1
                raise ErreurLexicale(
                    f"nombre mal formé : {source[debut:fin_mot]!r}", position(debut)
                )
            yield Token(kind, source[debut:i], position(debut))
            continue

        # Identifiants et mots-clés
        if _est_debut_identifiant(c):
            debut = i
            while i < n and _est_suite_identifiant(source[i]):
                i += 1
            mot = source[debut:i]
            if not mot.isidentifier():
                raise ErreurLexicale(
                    f"identifiant mal formé : {mot!r}", position(debut)
                )
            if unicodedata.normalize("NFKC", mot) != mot:
                raise ErreurLexicale(
                    f"identifiant non normalisé : {mot!r} (évitez ligatures et "
                    "caractères de compatibilité)",
                    position(debut),
                )
            yield Token(MOTS_CLES.get(mot, TokenKind.IDENT), mot, position(debut))
            continue
        if c == "_":
            raise ErreurLexicale(
                "un identifiant ne commence pas par '_' (réservé au code généré)",
                position(i),
            )

        # Textes
        if c == '"':
            debut = i
            morceaux: list[str] = []
            i += 1
            while True:
                if i >= n or source[i] == "\n":
                    raise ErreurLexicale("texte non terminé", position(debut))
                car = source[i]
                if car == '"':
                    i += 1
                    break
                if car == "\\":
                    code = source[i + 1] if i + 1 < n else ""
                    if code not in ECHAPPEMENTS:
                        lu = "\\" + code if code not in ("", "\n") else "\\"
                        raise ErreurLexicale(
                            f'échappement inconnu : {lu} (permis : \\n \\t \\" \\\\)',
                            position(i),
                        )
                    morceaux.append(ECHAPPEMENTS[code])
                    i += 2
                    continue
                morceaux.append(car)
                i += 1
            yield Token(TokenKind.TEXTE, "".join(morceaux), position(debut), i - debut)
            continue

        # Un point isolé suivi d'un chiffre : un décimal sans partie entière.
        # (Dans `1..5`, les deux points sont lus ensemble par les symboles.)
        if c == "." and i + 1 < n and source[i + 1].isdigit():
            raise ErreurLexicale(
                f"décimal sans partie entière : écrivez 0{source[i : i + 2]}…",
                position(i),
            )

        # Symboles, du plus long au plus court
        for symbole, kind in SYMBOLES:
            if source.startswith(symbole, i):
                yield Token(kind, symbole, position(i))
                i += len(symbole)
                break
        else:
            raise ErreurLexicale(
                f"caractère inattendu : {c!r}{CONSEILS.get(c, '')}", position(i)
            )

    yield Token(TokenKind.FIN, "", position(i))
