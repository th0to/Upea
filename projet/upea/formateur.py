"""Le formateur (étape 10) : un backend qui réécrit un programme Upea dans une
présentation canonique. Il n'hérite de rien : il a simplement la forme de `Backend`.

Les commentaires ne sont pas dans l'arbre syntaxique : ils sont perdus.
"""

from __future__ import annotations

import decimal
from typing import assert_never

from .backend import Sortie
from .emetteur import Emetteur
from .noeuds import (
    Affectation,
    Affiche,
    Appel,
    Binaire,
    Bloc,
    Booleen,
    Champ,
    Collection,
    Decimal,
    Declaration,
    Entier,
    Expr,
    ExprInstr,
    Fonction,
    Graphe,
    Index,
    Instr,
    Liste,
    Pour,
    Programme,
    Retour,
    Rien,
    Rupture,
    Si,
    TantQue,
    Texte,
    TypeNote,
    Unaire,
    Variable,
)
from .parser import PRECEDENCE_BINAIRE, Precedence
from .semantique import Analyse

#: Précédence d'un littéral, d'une variable, d'une liste : jamais de parenthèses.
ATOME = Precedence.APPEL + 1

#: Au-delà de ce nombre d'arêtes, un `upea` s'écrit sur plusieurs lignes.
ARETES_EN_LIGNE = 2


def texte_upea(valeur: str) -> str:
    """Un littéral texte d'Upea, échappements compris."""
    valeur = valeur.replace("\\", "\\\\").replace('"', '\\"')
    return '"' + valeur.replace("\n", "\\n").replace("\t", "\\t") + '"'


def decimal_upea(valeur: float) -> str:
    """Un littéral décimal relisible par le lexer (jamais de notation `1e+20`)."""
    texte = format(decimal.Decimal(repr(valeur)), "f")
    return texte if "." in texte else texte + ".0"


def precedence(expr: Expr) -> int:
    match expr:
        case Binaire(op):
            return PRECEDENCE_BINAIRE[op]
        case Unaire("-"):
            return Precedence.PREFIXE
        case Unaire("eiaha"):
            return Precedence.EIAHA
        case Appel() | Index() | Champ():
            return Precedence.APPEL
        case _:
            return ATOME


def note(type_: TypeNote) -> str:
    return (
        type_.nom
        if type_.parametre is None
        else f"{type_.nom}[{note(type_.parametre)}]"
    )


class _Ecrivain:
    def __init__(self) -> None:
        self.e = Emetteur()

    def programme(self, programme: Programme) -> None:
        precedente: Instr | None = None
        for instruction in programme.instructions:
            if precedente is not None and (
                isinstance(instruction, Fonction) or isinstance(precedente, Fonction)
            ):
                self.e.ligne()
            self.instruction(instruction)
            precedente = instruction

    def bloc(self, entete: str, bloc: Bloc, fin: str = "}") -> None:
        self.e.ligne(f"{entete} {{")
        with self.e.bloc(vide=None):
            for instruction in bloc.instructions:
                self.instruction(instruction)
        if fin:
            self.e.ligne(fin)

    def instruction(self, instr: Instr) -> None:
        e = self.e
        match instr:
            case Declaration(nom, valeur, annotation, constante):
                mot = "mau" if constante else "tuu"
                type_ = "" if annotation is None else f": {note(annotation)}"
                e.ligne(f"{mot} {nom}{type_} = {self.expr(valeur)};")
            case Affectation(cible, valeur):
                e.ligne(f"{self.expr(cible)} = {self.expr(valeur)};")
            case ExprInstr(expression):
                e.ligne(f"{self.expr(expression)};")
            case Affiche(valeurs):
                if valeurs:
                    e.ligne(f"faaite {', '.join(self.expr(v) for v in valeurs)};")
                else:
                    e.ligne("faaite;")
            case Si(branches, sinon):
                # Chaque bloc est refermé par l'en-tête du suivant : `} taae ahani … {`.
                for i, branche in enumerate(branches):
                    mot = "ahani" if i == 0 else "} taae ahani"
                    derniere = i == len(branches) - 1 and sinon is None
                    entete = f"{mot} {self.expr(branche.condition)}"
                    self.bloc(entete, branche.corps, fin="}" if derniere else "")
                if sinon is not None:
                    self.bloc("} taae", sinon)
            case TantQue(condition, corps):
                self.bloc(f"tamau {self.expr(condition)}", corps)
            case Pour(variable, iterable, corps, fin, inclusif, depart, mode):
                entete = f"tataitahi {variable} roto {self.expr(iterable)}"
                if fin is not None:
                    entete += f"{'..=' if inclusif else '..'}{self.expr(fin)}"
                if depart is not None:
                    entete += f" mai {self.expr(depart)}"
                if mode is not None:
                    entete += f" {mode}"
                self.bloc(entete, corps)
            case Rupture(genre):
                e.ligne(f"{genre};")
            case Retour(valeur):
                e.ligne("hoi;" if valeur is None else f"hoi {self.expr(valeur)};")
            case Fonction(nom, parametres, corps, retour):
                morceaux = [
                    p.nom if p.annotation is None else f"{p.nom}: {note(p.annotation)}"
                    for p in parametres
                ]
                fleche = "" if retour is None else f" -> {note(retour)}"
                self.bloc(f"ohipa {nom}({', '.join(morceaux)}){fleche}", corps)
            case _:
                assert_never(instr)

    def operande(self, expr: Expr, minimum: int) -> str:
        """`expr`, entre parenthèses si sa précédence est inférieure à `minimum`."""
        texte = self.expr(expr)
        return f"({texte})" if precedence(expr) < minimum else texte

    def expr(self, expr: Expr) -> str:
        match expr:
            case Entier(valeur):
                return str(valeur)
            case Decimal(valeur):
                return decimal_upea(valeur)
            case Texte(valeur):
                return texte_upea(valeur)
            case Booleen(valeur):
                return "tia" if valeur else "hape"
            case Rien():
                return "aore"
            case Variable(nom):
                return nom
            case Liste(elements):
                return f"[{', '.join(self.expr(x) for x in elements)}]"
            case Collection(sorte, elements, ordre):
                ecrit = sorte if ordre is None else f"{sorte} {ordre}"
                return f"{ecrit} [{', '.join(self.expr(e) for e in elements)}]"
            case Graphe(aretes):
                morceaux = []
                for arete in aretes:
                    if arete.arrivee is None:
                        morceaux.append(self.expr(arete.depart))
                        continue
                    fleche = "<->" if arete.double else "->"
                    texte = (
                        f"{self.expr(arete.depart)} {fleche} {self.expr(arete.arrivee)}"
                    )
                    if arete.poids is not None:
                        texte += f" : {self.expr(arete.poids)}"
                    morceaux.append(texte)
                if not morceaux:
                    return "upea {}"
                if len(morceaux) <= ARETES_EN_LIGNE:
                    return f"upea {{ {', '.join(morceaux)} }}"
                lignes = "".join(f"\n    {m}," for m in morceaux)
                return f"upea {{{lignes}\n}}"
            case Unaire("-", operande):
                return f"-{self.operande(operande, Precedence.PREFIXE)}"
            case Unaire("eiaha", operande):
                return f"eiaha {self.operande(operande, Precedence.EIAHA)}"
            case Unaire():
                raise AssertionError(f"opérateur unaire inconnu : {expr.op}")
            case Binaire(op, gauche, droite):
                niveau = PRECEDENCE_BINAIRE[op]
                # À gauche, une comparaison dans une comparaison garde ses parenthèses
                # (elles ne s'enchaînent pas) ; à droite, l'associativité à gauche
                # impose les parenthèses dès la précédence égale.
                minimum_gauche = (
                    niveau + 1 if niveau == Precedence.COMPARAISON else niveau
                )
                return (
                    f"{self.operande(gauche, minimum_gauche)} {op} "
                    f"{self.operande(droite, niveau + 1)}"
                )
            case Appel(nom, arguments):
                return f"{nom}({', '.join(self.expr(a) for a in arguments)})"
            case Index(objet, indice):
                return f"{self.operande(objet, Precedence.APPEL)}[{self.expr(indice)}]"
            case Champ(objet, nom):
                texte = self.operande(objet, Precedence.APPEL)
                if isinstance(objet, Entier):
                    texte = f"({texte})"  # `1.hotu` serait refusé par le lexer
                return f"{texte}.{nom}"
            case _:
                assert_never(expr)


class Formateur:
    nom = "formateur"
    extension = ".upea"
    executable = False

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        ecrivain = _Ecrivain()
        ecrivain.programme(programme)
        return Sortie(ecrivain.e.texte())
