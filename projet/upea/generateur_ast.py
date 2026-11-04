"""Un second générateur Python (extension 11), qui construit l'arbre Python lui-même
avec le module `ast`. `ast.unparse` en tire un code aux parenthèses minimales, et
`compile` peut l'exécuter directement, sans passer par le texte."""

from __future__ import annotations

import ast
import warnings
from functools import cache
from itertools import chain
from types import CodeType
from typing import assert_never

from .backend import Sortie
from .erreurs import Position
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
from .prelude import PRELUDE, nom_fonction, nom_python
from .semantique import Analyse
from .sourcemap import SourceMap
from .typage import INCONNU, Type, vers_python

OPERATEURS: dict[str, type[ast.operator]] = {
    "+": ast.Add,
    "-": ast.Sub,
    "*": ast.Mult,
    "/": ast.Div,
    "%": ast.Mod,
}
COMPARATEURS: dict[str, type[ast.cmpop]] = {
    "==": ast.Eq,
    "!=": ast.NotEq,
    "<": ast.Lt,
    "<=": ast.LtE,
    ">": ast.Gt,
    ">=": ast.GtE,
}
BOOLEENS: dict[str, type[ast.boolop]] = {"ma": ast.And, "anei": ast.Or}


def _placer[N: ast.stmt | ast.expr](noeud: N, pos: Position) -> N:
    """Donne au nœud Python la position du nœud Upea dont il provient."""
    ligne = max(pos.ligne, 1)
    colonne = max(pos.colonne - 1, 0)
    noeud.lineno = ligne
    noeud.col_offset = colonne
    noeud.end_lineno = ligne
    noeud.end_col_offset = colonne
    return noeud


def _nom(identifiant: str, contexte: ast.expr_context | None = None) -> ast.Name:
    return ast.Name(id=identifiant, ctx=contexte or ast.Load())


def _appel(fonction: str, arguments: list[ast.expr], **nommes: ast.expr) -> ast.Call:
    mots = [ast.keyword(arg=nom, value=valeur) for nom, valeur in nommes.items()]
    return ast.Call(func=_nom(fonction), args=arguments, keywords=mots)


def _annotation(type_: Type) -> ast.expr | None:
    texte = vers_python(type_)
    if texte is None:
        return None
    return ast.Constant(None) if texte == "None" else _nom(texte)


class _Constructeur:
    def __init__(self, analyse: Analyse) -> None:
        self.analyse = analyse

    def suite(self, instructions: tuple[Instr, ...]) -> list[ast.stmt]:
        """Une instruction Upea donne une ou plusieurs instructions Python."""
        return list(chain.from_iterable(map(self.instruction, instructions)))

    def bloc(self, bloc: Bloc) -> list[ast.stmt]:
        instructions = self.suite(bloc.instructions)
        return instructions or [ast.Pass()]

    def instruction(self, instr: Instr) -> list[ast.stmt]:
        noeuds = self._instruction(instr)
        for noeud in noeuds:
            _placer(noeud, instr.pos)
        return noeuds

    def _instruction(self, instr: Instr) -> list[ast.stmt]:
        match instr:
            case Declaration(nom, valeur):
                return [
                    ast.Assign(
                        targets=[_nom(nom_python(nom), ast.Store())],
                        value=self.expr(valeur),
                    )
                ]
            case Affectation(cible, valeur):
                return [
                    ast.Assign(targets=[self.cible(cible)], value=self.expr(valeur))
                ]
            case ExprInstr(expression):
                return [ast.Expr(value=self.expr(expression))]
            case Affiche(valeurs):
                return [
                    ast.Expr(value=_appel("_affiche", [self.expr(v) for v in valeurs]))
                ]
            case Si(branches, sinon):
                # `elif` n'existe pas dans l'arbre : c'est un If seul
                # dans le orelse du précédent.
                suite = [] if sinon is None else self.bloc(sinon)
                for branche in reversed(branches):
                    si = ast.If(
                        test=self.expr(branche.condition),
                        body=self.bloc(branche.corps),
                        orelse=suite,
                    )
                    suite = [_placer(si, branche.pos)]
                return suite
            case TantQue(condition, corps):
                return [
                    ast.While(
                        test=self.expr(condition), body=self.bloc(corps), orelse=[]
                    )
                ]
            case Pour(variable, iterable, corps, fin, inclusif, depart, mode):
                if fin is not None:
                    borne = self.expr(fin)
                    if inclusif:
                        borne = ast.BinOp(
                            left=borne, op=ast.Add(), right=ast.Constant(1)
                        )
                    source: ast.expr = _appel("range", [self.expr(iterable), borne])
                else:
                    arguments = [self.expr(iterable)]
                    if depart is not None:
                        arguments.append(self.expr(depart))
                    nommes = {} if mode is None else {"mode": ast.Constant(mode)}
                    source = _appel("_parcours", arguments, **nommes)
                compteur = _nom(nom_python(variable), ast.Store())
                return [
                    ast.For(
                        target=compteur, iter=source, body=self.bloc(corps), orelse=[]
                    )
                ]
            case Rupture(genre):
                return [ast.Break() if genre == "faaea" else ast.Continue()]
            case Retour(valeur):
                return [ast.Return(value=None if valeur is None else self.expr(valeur))]
            case Fonction():
                return [self.fonction(instr)]
            case _:
                assert_never(instr)

    def fonction(self, fonction: Fonction) -> ast.FunctionDef:
        signature = self.analyse.signatures.get(fonction.nom)
        types = (
            signature.parametres if signature else (INCONNU,) * len(fonction.parametres)
        )
        parametres = [
            ast.arg(arg=nom_python(p.nom), annotation=_annotation(t))
            for p, t in zip(fonction.parametres, types, strict=True)
        ]
        corps: list[ast.stmt] = []
        globales = sorted(self.analyse.globales_modifiees.get(fonction.nom, ()))
        if globales:
            corps.append(
                _placer(
                    ast.Global(names=[nom_python(g) for g in globales]), fonction.pos
                )
            )
        corps.extend(self.suite(fonction.corps.instructions))
        return ast.FunctionDef(
            name=nom_python(fonction.nom),
            args=ast.arguments(
                posonlyargs=[],
                args=parametres,
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
            ),
            body=corps or [ast.Pass()],
            decorator_list=[],
            returns=None if signature is None else _annotation(signature.retour),
            type_params=[],
        )

    def cible(self, cible: Variable | Index | Champ) -> ast.expr:
        match cible:
            case Variable(nom):
                return _placer(_nom(nom_python(nom), ast.Store()), cible.pos)
            case Index(objet, indice):
                return _placer(
                    ast.Subscript(
                        value=self.expr(objet), slice=self.expr(indice), ctx=ast.Store()
                    ),
                    cible.pos,
                )
            case Champ(objet, nom):
                return _placer(
                    ast.Attribute(value=self.expr(objet), attr=nom, ctx=ast.Store()),
                    cible.pos,
                )
            case _:
                assert_never(cible)

    def expr(self, expr: Expr) -> ast.expr:
        noeud = self._expr(expr)
        return _placer(noeud, expr.pos) if expr.pos.ligne > 0 else noeud

    def _expr(self, expr: Expr) -> ast.expr:
        match expr:
            case Entier(valeur) | Decimal(valeur) | Texte(valeur) | Booleen(valeur):
                return ast.Constant(valeur)
            case Rien():
                return ast.Constant(None)
            case Variable(nom):
                return _nom(nom_python(nom))
            case Liste(elements):
                return ast.List(elts=[self.expr(e) for e in elements], ctx=ast.Load())
            case Graphe(aretes):
                triplets: list[ast.expr] = []
                for arete in aretes:
                    if arete.arrivee is None:
                        vides = map(ast.Constant, (None, None, False))
                        seul = [self.expr(arete.depart), *vides]
                        triplets.append(ast.Tuple(elts=seul, ctx=ast.Load()))
                        continue
                    poids = (
                        ast.Constant(1)
                        if arete.poids is None
                        else self.expr(arete.poids)
                    )
                    extremites = [self.expr(arete.depart), self.expr(arete.arrivee)]
                    champs = [*extremites, poids, ast.Constant(arete.double)]
                    triplets.append(ast.Tuple(elts=champs, ctx=ast.Load()))
                return _appel("_graphe", [ast.List(elts=triplets, ctx=ast.Load())])
            case Collection(sorte, elements, ordre):
                cles = ast.List(elts=[self.expr(e) for e in elements], ctx=ast.Load())
                ordres = [] if ordre is None else [ast.Constant(ordre)]
                return _appel(f"_{sorte}", [cles, *ordres])
            case Unaire(op, operande):
                unaire = ast.USub() if op == "-" else ast.Not()
                return ast.UnaryOp(op=unaire, operand=self.expr(operande))
            case Binaire(op, gauche, droite):
                g, d = self.expr(gauche), self.expr(droite)
                if op == "roto":
                    return _appel("_roto", [g, d])
                if op in BOOLEENS:
                    operateur = BOOLEENS[op]
                    # `a ma b ma c` : Python range les trois dans un seul BoolOp.
                    if isinstance(g, ast.BoolOp) and isinstance(g.op, operateur):
                        return ast.BoolOp(op=operateur(), values=[*g.values, d])
                    return ast.BoolOp(op=operateur(), values=[g, d])
                if op in COMPARATEURS:
                    return ast.Compare(
                        left=g, ops=[COMPARATEURS[op]()], comparators=[d]
                    )
                return ast.BinOp(left=g, op=OPERATEURS[op](), right=d)
            case Appel(nom, arguments):
                return _appel(nom_fonction(nom), [self.expr(a) for a in arguments])
            case Index(objet, indice):
                return ast.Subscript(
                    value=self.expr(objet), slice=self.expr(indice), ctx=ast.Load()
                )
            case Champ(objet, nom):
                return ast.Attribute(value=self.expr(objet), attr=nom, ctx=ast.Load())
            case _:
                assert_never(expr)


class GenerateurAst:
    nom = "ast"
    extension = ".py"
    executable = True

    def module(self, programme: Programme, analyse: Analyse) -> ast.Module:
        """L'arbre Python du programme seul (sans prélude), aux lignes d'Upea."""
        constructeur = _Constructeur(analyse)
        corps = constructeur.suite(programme.instructions)
        return ast.fix_missing_locations(ast.Module(body=corps, type_ignores=[]))

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        prelude = _texte_prelude()
        utilisateur = self.module(programme, analyse)
        # Le programme tel qu'`ast.unparse` l'écrirait à la suite du prélude.
        suite = "".join(_avant(i) + ast.unparse(i) for i in utilisateur.body)
        # Le texte produit n'a plus les numéros de ligne d'Upea : on relit le
        # programme seul, et l'on apparie ses instructions à celles de l'arbre
        # d'origine, en comptant les lignes du prélude.
        decalage = prelude.count("\n")
        relu = ast.parse(suite)
        lignes: dict[int, int] = {}
        for original, nouveau in zip(utilisateur.body, relu.body, strict=True):
            for a, b in zip(ast.walk(original), ast.walk(nouveau), strict=True):
                if isinstance(a, ast.stmt) and isinstance(b, ast.stmt):
                    lignes.setdefault(b.lineno + decalage, a.lineno)
        return Sortie(prelude + suite + "\n", SourceMap(lignes=lignes))


@cache
def _texte_prelude() -> str:
    """Le prélude tel que l'écrit `ast.unparse`, calculé une seule fois (l'analyser
    et le réécrire coûte une cinquantaine de millisecondes). On garde un texte, et
    non des nœuds : aucune génération ne peut modifier ce qui est en cache."""
    return ast.unparse(ast.parse(PRELUDE))


def _avant(instruction: ast.stmt) -> str:
    """Ce qui précède une instruction de premier niveau dans le texte
    d'`ast.unparse` : un saut de ligne, et une ligne vide avant une fonction."""
    return "\n\n" if isinstance(instruction, ast.FunctionDef) else "\n"


def compiler_module(module: ast.Module | str, nom_fichier: str) -> CodeType:
    """Compile le code généré : l'arbre Python directement, ou son texte.

    Les `SyntaxWarning` de CPython (`(3)[0]` : « perhaps you missed a comma? »)
    sont tus : le programme a déjà été vérifié, et l'erreur, s'il y en a une,
    arrivera à l'exécution, traduite. Les autres avertissements passent.
    """
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", SyntaxWarning)
        return compile(module, nom_fichier, "exec")


def correspondance_identite(module: ast.Module) -> SourceMap:
    """Les lignes d'un module construit ici sont déjà celles d'Upea."""
    return SourceMap(
        lignes={n.lineno: n.lineno for n in ast.walk(module) if isinstance(n, ast.stmt)}
    )
