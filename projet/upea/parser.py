"""Le parser : un parser de Pratt pour les expressions (étape 5), une descente
récursive pour les instructions, avec récupération d'erreurs (étape 6)."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from enum import IntEnum

from .erreurs import ErreurLexicale, ErreursMultiples, ErreurSyntaxe, ErreurUpea
from .flux import Flux
from .lexer import tokenize
from .noeuds import (
    Affectation,
    Affiche,
    Appel,
    Arete,
    Binaire,
    Bloc,
    Booleen,
    Branche,
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
    Mode,
    Parametre,
    Pour,
    Programme,
    Retour,
    Rien,
    Rupture,
    Si,
    SorteCollection,
    TantQue,
    Texte,
    TypeNote,
    Unaire,
    Variable,
)
from .tokens import Token
from .tokens import TokenKind as T

#: Au-delà, le parser abandonne : un programme très faux noierait l'utilisateur.
MAX_ERREURS = 20


class Precedence(IntEnum):
    AUCUNE = 0
    ANEI = 1
    MA = 2
    EIAHA = 3
    COMPARAISON = 4
    SOMME = 5
    PRODUIT = 6
    PREFIXE = 7
    APPEL = 8


type ReglePrefixe = Callable[[Parser, Token], Expr]
type RegleInfixe = Callable[[Parser, Expr, Token], Expr]

REGLES_PREFIXE: dict[T, ReglePrefixe] = {}
REGLES_INFIXE: dict[T, tuple[Precedence, RegleInfixe]] = {}

#: La précédence de chaque opérateur binaire, par lexème (partagée avec le formateur).
PRECEDENCE_BINAIRE: dict[str, Precedence] = {}

#: Les opérateurs qui ne s'enchaînent pas.
COMPARATEURS = frozenset(
    {T.EGAL_EGAL, T.DIFFERENT, T.INF, T.INF_EGAL, T.SUP, T.SUP_EGAL, T.ROTO}
)

#: Les littéraux d'arbres ordonnés : `aifaito [5, 3, 8]`.
SORTES_COLLECTION: dict[T, SorteCollection] = {
    T.IMI: "imi",
    T.AIFAITO: "aifaito",
    T.UTEERE: "uteere",
    T.PUPU: "pupu",
    T.AHU: "ahu",
    T.AHUNUI: "ahunui",
}

#: Les tokens qui peuvent nommer un type dans une annotation.
NOMS_DE_TYPE = frozenset({T.IDENT, T.UPEA, T.AORE, *SORTES_COLLECTION} - {T.AHUNUI})

#: Les tokens qui commencent une instruction : on s'y resynchronise.
DEBUTS_INSTRUCTION = frozenset(
    {
        T.TUU,
        T.MAU,
        T.OHIPA,
        T.AHANI,
        T.TAMAU,
        T.TATAITAHI,
        T.FAAEA,
        T.HAERE,
        T.HOI,
        T.FAAITE,
    }
)


def prefixe(*kinds: T) -> Callable[[ReglePrefixe], ReglePrefixe]:
    """Enregistre une règle préfixe pour chacun des `kinds`."""

    def enregistrer(regle: ReglePrefixe) -> ReglePrefixe:
        for kind in kinds:
            REGLES_PREFIXE[kind] = regle
        return regle

    return enregistrer


def infixe(*kinds: T, precedence: Precedence) -> Callable[[RegleInfixe], RegleInfixe]:
    """Enregistre une règle infixe, avec sa précédence, pour chacun des `kinds`."""

    def enregistrer(regle: RegleInfixe) -> RegleInfixe:
        for kind in kinds:
            REGLES_INFIXE[kind] = (precedence, regle)
        return regle

    return enregistrer


def decrire(token: Token) -> str:
    """Le token tel qu'on le cite dans un message d'erreur."""
    match token.kind:
        case T.FIN:
            return "la fin du programme"
        case T.TEXTE:
            return f'le texte "{token.lexeme}"'
        case _:
            return f"'{token.lexeme}'"


class _Abandon(Exception):
    """Trop d'erreurs : on arrête d'analyser."""


class Parser:
    def __init__(self, tokens: Iterable[Token]) -> None:
        self.flux: Flux[Token] = Flux(tokens)
        self.erreurs: list[ErreurUpea] = []
        #: Le dernier token rendu par `avance()`, pour pointer juste après lui.
        self.dernier: Token | None = None
        self._fin: Token | None = None

    # --- Accès aux tokens -------------------------------------------------------

    def regarde(self, decalage: int = 0) -> Token:
        token = self.flux.regarde(decalage)
        if token is None:
            # Au-delà de FIN : on rend FIN indéfiniment.
            assert self._fin is not None
            return self._fin
        if token.kind is T.FIN:
            self._fin = token
        return token

    def avance(self) -> Token:
        """Consomme le token courant ; FIN n'est jamais consommé."""
        token = self.regarde()
        if token.kind is not T.FIN:
            self.flux.avance()
            self.dernier = token
        return token

    def verifie(self, kind: T) -> bool:
        return self.regarde().kind is kind

    def accepte(self, kind: T) -> Token | None:
        """Consomme le token s'il est de type `kind`, sinon ne fait rien."""
        if self.verifie(kind):
            return self.avance()
        return None

    def attend(self, kind: T, contexte: str = "") -> Token:
        """Consomme un token de type `kind`, ou lève une erreur de syntaxe."""
        token = self.regarde()
        if token.kind is kind:
            return self.avance()
        suite = f" {contexte}" if contexte else ""
        message = f"{kind} attendu{suite}, trouvé {decrire(token)}"
        if token.kind is T.EGAL and kind is T.ACC_G:
            message += " (pour comparer, écrivez '==')"
        position = token.position
        if kind is T.POINT_VIRGULE and self.dernier is not None:
            # Un `;` oublié se signale juste après le token qui le précède.
            position = self.dernier.fin
        raise ErreurSyntaxe(message, position)

    # --- Expressions (Pratt) ------------------------------------------------------

    def expression(self, precedence: Precedence = Precedence.AUCUNE) -> Expr:
        token = self.avance()
        regle = REGLES_PREFIXE.get(token.kind)
        if regle is None:
            raise ErreurSyntaxe(
                f"expression attendue, trouvé {decrire(token)}", token.position
            )
        gauche = regle(self, token)
        while True:
            suivant = self.regarde()
            entree = REGLES_INFIXE.get(suivant.kind)
            if entree is None or entree[0] <= precedence:
                return gauche
            self.avance()
            gauche = entree[1](self, gauche, suivant)

    def arguments(self, fermante: T, contexte: str) -> tuple[Expr, ...]:
        """`expression { "," expression }`, jusqu'au token `fermante`."""
        valeurs: list[Expr] = []
        if self.accepte(fermante):
            return ()
        while True:
            valeurs.append(self.expression())
            if not self.accepte(T.VIRGULE):
                break
        self.attend(fermante, contexte)
        return tuple(valeurs)

    # --- Instructions ---------------------------------------------------------------

    def programme(self) -> Programme:
        instructions: list[Instr] = []
        while not self.verifie(T.FIN):
            if self.verifie(T.ACC_D):
                orpheline = self.avance()
                self._noter(
                    ErreurSyntaxe("'}' sans '{' correspondante", orpheline.position)
                )
                continue
            instruction = self._instruction_protegee()
            if instruction is not None:
                instructions.append(instruction)
        return Programme(tuple(instructions))

    def _noter(self, erreur: ErreurUpea) -> None:
        self.erreurs.append(erreur)
        if len(self.erreurs) >= MAX_ERREURS:
            raise _Abandon

    def _instruction_protegee(self) -> Instr | None:
        avant = self.flux.consommes
        try:
            return self.instruction()
        except ErreurSyntaxe as erreur:
            self._noter(erreur)
            self._synchroniser(avant)
            return None

    def _synchroniser(self, avant: int) -> None:
        """Saute des tokens jusqu'au début probable de l'instruction suivante."""
        if self.flux.consommes == avant and not self.verifie(T.FIN):
            self.avance()  # au moins un token, sinon on boucle indéfiniment
        profondeur = 0  # accolades ouvertes pendant la resynchronisation
        while True:
            token = self.regarde()
            if token.kind is T.FIN:
                return
            if profondeur == 0 and (
                token.kind is T.ACC_D or token.kind in DEBUTS_INSTRUCTION
            ):
                return
            self.avance()
            if token.kind is T.ACC_G:
                profondeur += 1
            elif token.kind is T.ACC_D:
                profondeur -= 1
                if profondeur == 0:
                    return  # le bloc de l'instruction fautive est sauté en entier
            elif token.kind is T.POINT_VIRGULE and profondeur == 0:
                return

    def instruction(self) -> Instr:
        token = self.regarde()
        match token.kind:
            case T.TUU | T.MAU:
                return self.declaration()
            case T.OHIPA:
                return self.fonction()
            case T.AHANI:
                return self.si()
            case T.TAMAU:
                return self.tantque()
            case T.TATAITAHI:
                return self.pour()
            case T.FAAEA | T.HAERE:
                return self.rupture()
            case T.HOI:
                return self.retour()
            case T.FAAITE:
                return self.affiche()
            case T.TAAE:
                raise ErreurSyntaxe(
                    "'taae' sans 'ahani' qui le précède", token.position
                )
            case _:
                return self.affectation_ou_expression()

    def bloc(self, contexte: str = "") -> Bloc:
        ouverture = self.attend(T.ACC_G, contexte)
        instructions: list[Instr] = []
        while not self.verifie(T.ACC_D):
            if self.verifie(T.FIN):
                raise ErreurSyntaxe(
                    f"bloc ouvert ligne {ouverture.position.ligne} jamais fermé : "
                    "'}' attendu",
                    self.regarde().position,
                )
            instruction = self._instruction_protegee()
            if instruction is not None:
                instructions.append(instruction)
        self.avance()
        return Bloc(tuple(instructions), ouverture.position)

    def type(self) -> TypeNote:
        token = self.regarde()
        if token.kind not in NOMS_DE_TYPE:
            raise ErreurSyntaxe(
                f"type attendu, trouvé {decrire(token)}", token.position
            )
        self.avance()
        parametre = None
        if self.accepte(T.CRO_G):
            parametre = self.type()
            self.attend(T.CRO_D, "pour fermer le paramètre du type")
        return TypeNote(token.lexeme, parametre, token.position)

    def declaration(self) -> Declaration:
        mot_cle = self.avance()
        nom = self.attend(T.IDENT, f"après '{mot_cle.lexeme}'")
        annotation = self.type() if self.accepte(T.DEUX_POINTS) else None
        self.attend(
            T.EGAL, f"après '{nom.lexeme}' (une déclaration a toujours une valeur)"
        )
        valeur = self.expression()
        self.attend(T.POINT_VIRGULE, "après la déclaration")
        return Declaration(
            nom.lexeme, valeur, annotation, mot_cle.kind is T.MAU, nom.position
        )

    def fonction(self) -> Fonction:
        self.avance()
        nom = self.attend(T.IDENT, "après 'ohipa'")
        self.attend(T.PAR_G, f"après le nom de la fonction '{nom.lexeme}'")
        parametres: list[Parametre] = []
        if not self.accepte(T.PAR_D):
            while True:
                parametre = self.attend(T.IDENT, "pour nommer un paramètre")
                annotation = self.type() if self.accepte(T.DEUX_POINTS) else None
                parametres.append(
                    Parametre(parametre.lexeme, annotation, parametre.position)
                )
                if not self.accepte(T.VIRGULE):
                    break
            self.attend(T.PAR_D, "pour fermer la liste des paramètres")
        retour = self.type() if self.accepte(T.FLECHE) else None
        corps = self.bloc("pour ouvrir le corps de la fonction")
        return Fonction(nom.lexeme, tuple(parametres), corps, retour, nom.position)

    def si(self) -> Si:
        mot_cle = self.avance()
        condition = self.expression()
        branches = [
            Branche(condition, self.bloc("après la condition"), mot_cle.position)
        ]
        sinon = None
        while self.accepte(T.TAAE):
            if (ahani := self.accepte(T.AHANI)) is not None:
                condition = self.expression()
                branches.append(
                    Branche(condition, self.bloc("après la condition"), ahani.position)
                )
            else:
                sinon = self.bloc("après 'taae'")
                break
        return Si(tuple(branches), sinon, mot_cle.position)

    def tantque(self) -> TantQue:
        mot_cle = self.avance()
        condition = self.expression()
        return TantQue(condition, self.bloc("après la condition"), mot_cle.position)

    def pour(self) -> Pour:
        mot_cle = self.avance()
        variable = self.attend(T.IDENT, "après 'tataitahi'").lexeme
        self.attend(T.ROTO, f"après la variable de boucle '{variable}'")
        iterable = self.expression()
        fin: Expr | None = None
        inclusif = False
        depart: Expr | None = None
        mode: Mode | None = None
        if self.verifie(T.POINT_POINT) or self.verifie(T.POINT_POINT_EGAL):
            inclusif = self.avance().kind is T.POINT_POINT_EGAL
            fin = self.expression()
        else:
            if self.accepte(T.MAI):
                depart = self.expression()
            if self.accepte(T.AANO):
                mode = "aano"
            elif self.accepte(T.HOHONU):
                mode = "hohonu"
        corps = self.bloc("pour ouvrir le corps de la boucle")
        return Pour(
            variable, iterable, corps, fin, inclusif, depart, mode, mot_cle.position
        )

    def rupture(self) -> Rupture:
        mot_cle = self.avance()
        self.attend(T.POINT_VIRGULE, f"après '{mot_cle.lexeme}'")
        if mot_cle.kind is T.FAAEA:
            return Rupture("faaea", mot_cle.position)
        return Rupture("haere", mot_cle.position)

    def retour(self) -> Retour:
        mot_cle = self.avance()
        valeur = None if self.verifie(T.POINT_VIRGULE) else self.expression()
        self.attend(T.POINT_VIRGULE, "après 'hoi'")
        return Retour(valeur, mot_cle.position)

    def affiche(self) -> Affiche:
        mot_cle = self.avance()
        valeurs: list[Expr] = []
        if not self.verifie(T.POINT_VIRGULE):
            while True:
                valeurs.append(self.expression())
                if not self.accepte(T.VIRGULE):
                    break
        self.attend(T.POINT_VIRGULE, "après 'faaite'")
        return Affiche(tuple(valeurs), mot_cle.position)

    def affectation_ou_expression(self) -> Affectation | ExprInstr:
        debut = self.regarde()
        expression = self.expression()
        if self.accepte(T.EGAL):
            if not isinstance(expression, Variable | Index | Champ):
                raise ErreurSyntaxe(
                    "on ne peut affecter qu'à une variable, un élément t[i] "
                    "ou un champ t.hotu",
                    debut.position,
                )
            valeur = self.expression()
            self.attend(T.POINT_VIRGULE, "après l'affectation")
            return Affectation(expression, valeur, debut.position)
        self.attend(T.POINT_VIRGULE, "après l'expression")
        return ExprInstr(expression, debut.position)


# --- Les règles des expressions ------------------------------------------------


@prefixe(T.ENTIER)
def _entier(p: Parser, t: Token) -> Expr:
    return Entier(int(t.lexeme), t.position)


@prefixe(T.DECIMAL)
def _decimal(p: Parser, t: Token) -> Expr:
    return Decimal(float(t.lexeme), t.position)


@prefixe(T.TEXTE)
def _texte(p: Parser, t: Token) -> Expr:
    return Texte(t.lexeme, t.position)


@prefixe(T.TIA, T.HAPE)
def _booleen(p: Parser, t: Token) -> Expr:
    return Booleen(t.kind is T.TIA, t.position)


@prefixe(T.AORE)
def _rien(p: Parser, t: Token) -> Expr:
    return Rien(t.position)


@prefixe(T.IDENT)
def _variable(p: Parser, t: Token) -> Expr:
    return Variable(t.lexeme, t.position)


@prefixe(T.PAR_G)
def _groupe(p: Parser, t: Token) -> Expr:
    expression = p.expression()
    p.attend(T.PAR_D, f"pour fermer la parenthèse ouverte ligne {t.position.ligne}")
    return expression


@prefixe(T.CRO_G)
def _liste(p: Parser, t: Token) -> Expr:
    return Liste(p.arguments(T.CRO_D, "pour fermer la liste"), t.position)


@prefixe(T.MOINS)
def _moins(p: Parser, t: Token) -> Expr:
    return Unaire("-", p.expression(Precedence.PREFIXE), t.position)


@prefixe(T.EIAHA)
def _eiaha(p: Parser, t: Token) -> Expr:
    return Unaire("eiaha", p.expression(Precedence.EIAHA), t.position)


@prefixe(T.UPEA)
def _graphe(p: Parser, t: Token) -> Expr:
    p.attend(T.ACC_G, "après 'upea'")
    aretes: list[Arete] = []
    while not p.verifie(T.ACC_D):
        depart = p.expression()
        fleche = p.regarde()
        if fleche.kind in (T.VIRGULE, T.ACC_D):  # un nœud seul
            aretes.append(Arete(depart, None, False, None, depart.pos))
            if not p.accepte(T.VIRGULE):
                break
            continue
        if fleche.kind not in (T.FLECHE, T.DOUBLE_FLECHE):
            raise ErreurSyntaxe(
                f"'->', '<->', ',' ou '}}' attendu dans un upea, "
                f"trouvé {decrire(fleche)}",
                fleche.position,
            )
        p.avance()
        arrivee = p.expression()
        poids = p.expression() if p.accepte(T.DEUX_POINTS) else None
        aretes.append(
            Arete(
                depart, arrivee, fleche.kind is T.DOUBLE_FLECHE, poids, fleche.position
            )
        )
        if not p.accepte(T.VIRGULE):
            break
    p.attend(T.ACC_D, "pour fermer le upea")
    return Graphe(tuple(aretes), t.position)


@prefixe(*SORTES_COLLECTION)
def _collection(p: Parser, t: Token) -> Expr:
    """`aifaito [5, 3, 8]`, et pour l'arbre B un ordre facultatif : `pupu 4 [1, 2]`."""
    ordre = None
    if t.kind is T.PUPU and (nombre := p.accepte(T.ENTIER)) is not None:
        ordre = int(nombre.lexeme)
    p.attend(T.CRO_G, f"après '{t.lexeme}'")
    cles = p.arguments(T.CRO_D, f"pour fermer le {t.lexeme}")
    return Collection(SORTES_COLLECTION[t.kind], cles, ordre, t.position)


def _binaire(precedence: Precedence, *kinds: T) -> None:
    """Une règle commune aux opérateurs binaires associatifs à gauche."""

    @infixe(*kinds, precedence=precedence)
    def regle(p: Parser, gauche: Expr, t: Token) -> Expr:
        return Binaire(t.lexeme, gauche, p.expression(precedence), t.position)

    for kind in kinds:
        PRECEDENCE_BINAIRE[kind.value] = precedence


_binaire(Precedence.ANEI, T.ANEI)
_binaire(Precedence.MA, T.MA)
_binaire(Precedence.SOMME, T.PLUS, T.MOINS)
_binaire(Precedence.PRODUIT, T.ETOILE, T.BARRE, T.POURCENT)


@infixe(*COMPARATEURS, precedence=Precedence.COMPARAISON)
def _comparaison(p: Parser, gauche: Expr, t: Token) -> Expr:
    droite = p.expression(Precedence.COMPARAISON)
    suivant = p.regarde()
    if suivant.kind in COMPARATEURS:
        raise ErreurSyntaxe(
            "les comparaisons ne s'enchaînent pas : écrivez par exemple a < b ma b < c",
            suivant.position,
        )
    return Binaire(t.lexeme, gauche, droite, t.position)


for _kind in COMPARATEURS:
    PRECEDENCE_BINAIRE[_kind.value] = Precedence.COMPARAISON


@infixe(T.PAR_G, precedence=Precedence.APPEL)
def _appel(p: Parser, gauche: Expr, t: Token) -> Expr:
    if not isinstance(gauche, Variable):
        raise ErreurSyntaxe("seule une fonction nommée peut être appelée", t.position)
    return Appel(gauche.nom, p.arguments(T.PAR_D, "pour fermer l'appel"), gauche.pos)


@infixe(T.CRO_G, precedence=Precedence.APPEL)
def _index(p: Parser, gauche: Expr, t: Token) -> Expr:
    indice = p.expression()
    p.attend(T.CRO_D, "pour fermer l'indice")
    return Index(gauche, indice, t.position)


@infixe(T.POINT, precedence=Precedence.APPEL)
def _champ(p: Parser, gauche: Expr, t: Token) -> Expr:
    nom = p.attend(T.IDENT, "après le point (un champ : hotu ou amaa)")
    return Champ(gauche, nom.lexeme, nom.position)


# --- Points d'entrée --------------------------------------------------------------


def parse(source: str) -> Programme:
    """Analyse un programme complet.

    Lève une seule `ErreursMultiples` contenant toutes les erreurs trouvées,
    chaînée (`__cause__`) à la première.
    """
    parser = Parser(tokenize(source))
    programme = Programme(())
    try:
        programme = parser.programme()
    except ErreurLexicale as erreur:
        parser.erreurs.append(erreur)  # le lexer ne peut pas reprendre
    except _Abandon:
        pass
    if parser.erreurs:
        raise ErreursMultiples(parser.erreurs) from parser.erreurs[0]
    return programme


def parse_expression(source: str) -> Expr:
    """Analyse une expression seule, et vérifie qu'il ne reste rien derrière.

    Lève directement l'`ErreurSyntaxe` (ou l'`ErreurLexicale`) rencontrée.
    """
    parser = Parser(tokenize(source))
    expression = parser.expression()
    reste = parser.regarde()
    if reste.kind is not T.FIN:
        raise ErreurSyntaxe(
            f"fin de l'expression attendue, trouvé {decrire(reste)}", reste.position
        )
    return expression
