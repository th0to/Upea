"""La génération de Python sous forme de texte (étape 8)."""

from __future__ import annotations

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
    Unaire,
    Variable,
)
from .prelude import OPERATEURS_PYTHON, PRELUDE, SEPARATEUR, nom_fonction, nom_python
from .semantique import Analyse
from .sourcemap import SourceMap
from .typage import INCONNU, vers_python


class _Traducteur:
    def __init__(self, analyse: Analyse) -> None:
        self.analyse = analyse
        self.e = Emetteur()

    def bloc(self, bloc: Bloc) -> None:
        with self.e.bloc():
            for instruction in bloc.instructions:
                self.instruction(instruction)

    def instruction(self, instr: Instr) -> None:
        e = self.e
        with e.depuis(instr.pos.ligne):
            match instr:
                case Declaration(nom, valeur):
                    e.ligne(f"{nom_python(nom)} = {self.expr(valeur)}")
                case Affectation(cible, valeur):
                    e.ligne(f"{self.expr(cible)} = {self.expr(valeur)}")
                case ExprInstr(expression):
                    e.ligne(self.expr(expression))
                case Affiche(valeurs):
                    e.ligne(f"_affiche({', '.join(self.expr(v) for v in valeurs)})")
                case Si(branches, sinon):
                    for i, branche in enumerate(branches):
                        with e.depuis(branche.pos.ligne):
                            mot = "if" if i == 0 else "elif"
                            e.ligne(f"{mot} {self.expr(branche.condition)}:")
                        self.bloc(branche.corps)
                    if sinon is not None:
                        with e.depuis(sinon.pos.ligne):
                            e.ligne("else:")
                        self.bloc(sinon)
                case TantQue(condition, corps):
                    e.ligne(f"while {self.expr(condition)}:")
                    self.bloc(corps)
                case Pour(variable, iterable, corps, fin, inclusif, depart, mode):
                    if fin is not None:
                        borne = self.expr(fin)
                        if inclusif:
                            borne = f"{borne} + 1"
                        source = f"range({self.expr(iterable)}, {borne})"
                    else:
                        arguments = [self.expr(iterable)]
                        if depart is not None:
                            arguments.append(self.expr(depart))
                        if mode is not None:
                            arguments.append(f"mode={mode!r}")
                        source = f"_parcours({', '.join(arguments)})"
                    e.ligne(f"for {nom_python(variable)} in {source}:")
                    self.bloc(corps)
                case Rupture(genre):
                    e.ligne("break" if genre == "faaea" else "continue")
                case Retour(valeur):
                    e.ligne(
                        "return" if valeur is None else f"return {self.expr(valeur)}"
                    )
                case Fonction(nom, _, corps):
                    e.ligne(f"def {self.signature(instr)}:")
                    with e.bloc():
                        globales = sorted(self.analyse.globales_modifiees.get(nom, ()))
                        if globales:
                            e.ligne(
                                f"global {', '.join(nom_python(g) for g in globales)}"
                            )
                        for sous_instruction in corps.instructions:
                            self.instruction(sous_instruction)
                case _:
                    assert_never(instr)

    def signature(self, fonction: Fonction) -> str:
        """`nom(a: int, b) -> str`, avec les annotations connues."""
        signature = self.analyse.signatures.get(fonction.nom)
        types = (
            signature.parametres if signature else (INCONNU,) * len(fonction.parametres)
        )
        morceaux = []
        for parametre, type_ in zip(fonction.parametres, types, strict=True):
            annotation = vers_python(type_)
            nom = nom_python(parametre.nom)
            morceaux.append(nom if annotation is None else f"{nom}: {annotation}")
        texte = f"{nom_python(fonction.nom)}({', '.join(morceaux)})"
        retour = vers_python(signature.retour) if signature else None
        return texte if retour is None else f"{texte} -> {retour}"

    def expr(self, expr: Expr) -> str:
        """Le texte Python d'une expression ; toute opération est parenthésée."""
        match expr:
            case Entier(valeur):
                return str(valeur)
            case Decimal(valeur):
                return repr(valeur)
            case Texte(valeur):
                return repr(valeur)  # jamais le contenu d'un texte ne devient du code
            case Booleen(valeur):
                return "True" if valeur else "False"
            case Rien():
                return "None"
            case Variable(nom):
                return nom_python(nom)
            case Liste(elements):
                return f"[{', '.join(self.expr(e) for e in elements)}]"
            case Graphe(aretes):
                morceaux = []
                for arete in aretes:
                    if arete.arrivee is None:
                        seul = self.expr(arete.depart)
                        morceaux.append(f"({seul}, None, None, False)")
                        continue
                    poids = "1" if arete.poids is None else self.expr(arete.poids)
                    morceaux.append(
                        f"({self.expr(arete.depart)}, {self.expr(arete.arrivee)}, "
                        f"{poids}, {arete.double})"
                    )
                return f"_graphe([{', '.join(morceaux)}])"
            case Collection(sorte, elements, ordre):
                arguments = [f"[{', '.join(self.expr(e) for e in elements)}]"]
                if ordre is not None:
                    arguments.append(str(ordre))
                return f"_{sorte}({', '.join(arguments)})"
            case Unaire(op, operande):
                if op == "-":
                    return f"(-{self.expr(operande)})"
                return f"(not {self.expr(operande)})"
            case Binaire(op, gauche, droite):
                operateur = OPERATEURS_PYTHON.get(op, op)
                return f"({self.expr(gauche)} {operateur} {self.expr(droite)})"
            case Appel(nom, arguments):
                return (
                    f"{nom_fonction(nom)}({', '.join(self.expr(a) for a in arguments)})"
                )
            case Index(objet, indice):
                return f"{self.expr(objet)}[{self.expr(indice)}]"
            case Champ(objet, nom):
                texte = self.expr(objet)
                if isinstance(objet, Entier):
                    texte = f"({texte})"  # `1.hotu` serait lu comme un décimal
                return f"{texte}.{nom}"
            case _:
                assert_never(expr)


class GenerateurPython:
    """Le backend principal : du texte Python, précédé du prélude."""

    nom = "python"
    extension = ".py"
    executable = True

    def traduire(
        self, instructions: tuple[Instr, ...], analyse: Analyse
    ) -> tuple[str, SourceMap]:
        """Le code des seules `instructions`, sans prélude (sert aussi au REPL)."""
        traducteur = _Traducteur(analyse)
        for instruction in instructions:
            traducteur.instruction(instruction)
        return traducteur.e.texte(), SourceMap(
            lignes=dict(traducteur.e.correspondances)
        )

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        code, sourcemap = self.traduire(programme.instructions, analyse)
        entete = PRELUDE + "\n\n" + SEPARATEUR
        return Sortie(entete + code, sourcemap.decaler(entete.count("\n")))
