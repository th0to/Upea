"""L'analyse sémantique (étape 7) et la vérification des types (extension 12).

Un visiteur à base de `singledispatchmethod` : une variante par type de nœud,
sans cascade de `isinstance`. Toutes les erreurs sont collectées, puis levées
ensemble dans une `ErreursMultiples`.
"""

from __future__ import annotations

import difflib
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import singledispatchmethod

from .erreurs import (
    Avertissement,
    ErreurSemantique,
    ErreursMultiples,
    ErreurType,
    ErreurUpea,
    Position,
)
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
from .predefinies import PREDEFINIES
from .symboles import Genre, Symbole, TableSymboles
from .typage import (
    AORE,
    COMPOSES,
    INCONNU,
    NUMERA,
    ORDONNES,
    PARAU,
    TIAHAPE,
    TUHAA,
    Compose,
    NomCompose,
    Signature,
    Type,
    commun_de,
    compatible,
    depuis_note,
    element,
    element_de,
    est_cle,
    est_nombre,
    tapura,
    tumu,
    upea,
)

CHAMPS = ("hotu", "amaa")


@dataclass(frozen=True, slots=True)
class Analyse:
    """Ce que l'analyse transmet au générateur."""

    #: Pour chaque fonction, les variables globales qu'elle réaffecte.
    globales_modifiees: dict[str, frozenset[str]] = field(default_factory=dict)
    #: La signature de chaque fonction définie par l'utilisateur.
    signatures: dict[str, Signature] = field(default_factory=dict)
    avertissements: tuple[Avertissement, ...] = ()


@dataclass(slots=True)
class _Fonction:
    """La fonction en cours d'analyse."""

    nom: str
    retour: Type
    locales: dict[str, Position] = field(default_factory=dict)
    globales_lues: dict[str, Position] = field(default_factory=dict)
    globales_modifiees: set[str] = field(default_factory=set)


def _pluriel(n: int, mot: str) -> str:
    return f"{n} {mot}{'s' if n > 1 else ''}"


def toujours_retourne(instructions: tuple[Instr, ...]) -> bool:
    """Vrai si la suite d'instructions se termine par un `hoi` sur tous les chemins.

    Une boucle `tamau tia` sans `faaea` qui la quitte ne se termine jamais d'elle-même :
    on n'en sort que par un `hoi` (ou une erreur), elle compte donc comme un retour.
    """
    for instruction in instructions:
        if isinstance(instruction, Retour):
            return True
        if (
            isinstance(instruction, TantQue)
            and isinstance(instruction.condition, Booleen)
            and instruction.condition.valeur
            and not quitte_la_boucle(instruction.corps.instructions)
        ):
            return True
        if (
            isinstance(instruction, Si)
            and instruction.sinon is not None
            and all(
                toujours_retourne(b.corps.instructions) for b in instruction.branches
            )
            and toujours_retourne(instruction.sinon.instructions)
        ):
            return True
    return False


def quitte_la_boucle(instructions: tuple[Instr, ...]) -> bool:
    """Vrai si un `faaea` de ces instructions quitte la boucle qui les contient :
    ceux des boucles imbriquées ne quittent que celles-ci."""
    for instruction in instructions:
        match instruction:
            case Rupture("faaea"):
                return True
            case Si(branches, sinon):
                blocs = [b.corps for b in branches] + ([] if sinon is None else [sinon])
                if any(quitte_la_boucle(bloc.instructions) for bloc in blocs):
                    return True
    return False


class Analyseur:
    """Le visiteur de l'analyse sémantique et des types.

    Il parcourt l'arbre une fois : il déclare les noms dans la table des
    symboles, vérifie leurs usages et (si `types`) leurs types, et collecte
    les erreurs et les avertissements.
    """

    def __init__(self, *, types: bool = True) -> None:
        self.verifier_types = types
        self.table = TableSymboles()
        self.erreurs: list[ErreurUpea] = []
        self.avertissements: list[Avertissement] = []
        self.globales_modifiees: dict[str, frozenset[str]] = {}
        self.signatures: dict[str, Signature] = {}
        self._fonction: _Fonction | None = None
        self._boucles = 0
        for nom in PREDEFINIES:
            self.table.predefinies.symboles[nom] = Symbole(
                nom, Genre.PREDEFINIE, Position(0, 0)
            )

    # --- Signalement ----------------------------------------------------------------

    def erreur(self, message: str, position: Position) -> None:
        """Note une erreur sémantique."""
        self.erreurs.append(ErreurSemantique(message, position))

    def erreur_type(self, message: str, position: Position) -> None:
        """Note une erreur de type, sauf si les types ne sont pas vérifiés
        (`--sans-types`)."""
        if self.verifier_types:
            self.erreurs.append(ErreurType(message, position))

    def avertir(self, message: str, position: Position) -> None:
        """Note un avertissement, qui n'empêche pas l'exécution."""
        self.avertissements.append(Avertissement(message, position))

    def exiger(
        self, attendu: Type, recu: Type, contexte: str, position: Position
    ) -> None:
        """Une erreur de type si `recu` ne convient pas là où `attendu` est demandé."""
        if not compatible(attendu, recu):
            self.erreur_type(f"{contexte} : {attendu} attendu, {recu} reçu", position)

    # --- Portées et contexte ----------------------------------------------------------

    @contextmanager
    def portee(self, nom: str, *, fonction: bool = False) -> Iterator[None]:
        """Ouvre une portée, puis signale ce qui y a été déclaré sans servir."""
        with self.table.portee(nom, fonction=fonction) as portee:
            yield
            for symbole in portee.symboles.values():
                self._verifier_utilise(symbole)

    def _verifier_utilise(self, symbole: Symbole) -> None:
        if symbole.genre in (Genre.VARIABLE, Genre.CONSTANTE) and not symbole.utilise:
            self.avertir(
                f"'{symbole.nom}' est déclarée mais jamais utilisée", symbole.pos
            )

    @contextmanager
    def dans_fonction(self, fonction: _Fonction) -> Iterator[None]:
        """Le temps du `with`, l'analyse est dans le corps de `fonction`."""
        precedente, boucles = self._fonction, self._boucles
        self._fonction, self._boucles = fonction, 0
        try:
            yield
        finally:
            self._fonction, self._boucles = precedente, boucles

    @contextmanager
    def dans_boucle(self) -> Iterator[None]:
        """Le temps du `with`, l'analyse est dans une boucle : `faaea` et `haere` y
        sont permis."""
        self._boucles += 1
        try:
            yield
        finally:
            self._boucles -= 1

    def type_de(self, note: TypeNote | None) -> Type:
        """Le type d'une annotation, `INCONNU` s'il n'y en a pas ; une annotation
        invalide est notée comme erreur."""
        if note is None:
            return INCONNU
        try:
            return depuis_note(note)
        except ErreurType as erreur:
            self.erreurs.append(erreur)
            return INCONNU

    # --- Les noms ---------------------------------------------------------------------

    def declarer(
        self, nom: str, genre: Genre, position: Position, type_: Type = INCONNU
    ) -> None:
        """Déclare `nom` dans la portée courante, sauf s'il enfreint une règle de la
        spécification : le nom d'une fonction, une redéclaration dans le même
        bloc, un masquage, ou une locale qui changerait le sens d'une globale
        déjà lue dans la fonction."""
        reserve = self.table.chercher(nom)
        if reserve is not None and not reserve.genre.est_valeur:
            sorte = (
                "prédéfinie" if reserve.genre is Genre.PREDEFINIE else "déjà déclarée"
            )
            self.erreur(f"'{nom}' est le nom d'une fonction {sorte}", position)
            return
        existant = self.table.meme_espace(nom)
        if existant is not None:
            if nom in self.table.courante.symboles:
                self.erreur(
                    f"'{nom}' est déjà déclaré dans ce bloc "
                    f"(ligne {existant.pos.ligne})",
                    position,
                )
            else:
                self.erreur(
                    f"'{nom}' masquerait la déclaration de la ligne "
                    f"{existant.pos.ligne} "
                    "(pas de masquage en Upea)",
                    position,
                )
            return
        fonction = self._fonction
        if fonction is not None and nom in fonction.globales_lues:
            ligne = fonction.globales_lues[nom].ligne
            self.erreur(
                f"'{nom}' désigne la variable globale plus haut dans la fonction "
                f"(ligne {ligne}) : une locale de même nom changerait son sens",
                position,
            )
            return
        self.table.declarer(Symbole(nom, genre, position, type_))
        if fonction is not None:
            fonction.locales.setdefault(nom, position)

    def _non_declare(self, nom: str, position: Position) -> None:
        visibles = [
            n
            for p in (self.table.predefinies, self.table.globale, self.table.courante)
            for n in p.symboles
        ]
        proches = difflib.get_close_matches(nom, visibles, n=1)
        conseil = f" (vouliez-vous dire '{proches[0]}' ?)" if proches else ""
        self.erreur(f"'{nom}' n'est pas déclaré{conseil}", position)

    def _globale(self, symbole: Symbole, est_globale: bool, position: Position) -> None:
        """Note l'usage, dans une fonction, d'une variable globale."""
        fonction = self._fonction
        if fonction is None or not est_globale or not symbole.genre.est_valeur:
            return
        if symbole.nom in fonction.locales:
            ligne = fonction.locales[symbole.nom].ligne
            self.erreur(
                f"'{symbole.nom}' désigne ici la variable globale, mais la fonction "
                f"déclare aussi une locale de ce nom (ligne {ligne}) : renommez-la",
                position,
            )
        fonction.globales_lues.setdefault(symbole.nom, position)

    def lire(self, nom: str, position: Position) -> Symbole | None:
        """Le symbole de `nom`, marqué comme utilisé ; `None` s'il n'est pas déclaré
        (l'erreur propose un nom proche)."""
        trouve = self.table.chercher_avec_portee(nom)
        if trouve is None:
            self._non_declare(nom, position)
            return None
        symbole, portee = trouve
        symbole.utilise = True
        self._globale(symbole, portee is self.table.globale, position)
        return symbole

    # --- Programme et blocs -----------------------------------------------------------

    def programme(self, programme: Programme) -> Analyse:
        """Analyse le programme entier : rend son `Analyse`, ou lève
        `ErreursMultiples` avec toutes les erreurs, triées par ligne."""
        self.instructions(programme.instructions)
        for symbole in self.table.globale.symboles.values():
            self._verifier_utilise(symbole)
        if self.erreurs:
            self.erreurs.sort(key=lambda e: (e.position or Position(0, 0)).ligne)
            raise ErreursMultiples(self.erreurs) from self.erreurs[0]
        return Analyse(
            self.globales_modifiees,
            self.signatures,
            tuple(
                sorted(
                    self.avertissements,
                    key=lambda a: (a.position or Position(0, 0)).ligne,
                )
            ),
        )

    def instructions(self, instructions: tuple[Instr, ...]) -> None:
        """Analyse une suite d'instructions, et signale une fois le code placé après
        `hoi`, `faaea` ou `haere`."""
        mort_signale = False
        for i, instruction in enumerate(instructions):
            self.instruction(instruction)
            if (
                isinstance(instruction, Retour | Rupture)
                and i + 1 < len(instructions)
                and not mort_signale
            ):
                mot = "hoi" if isinstance(instruction, Retour) else instruction.genre
                self.avertir(
                    f"code jamais exécuté (après '{mot}')", instructions[i + 1].pos
                )
                mort_signale = True

    def bloc(self, bloc: Bloc, nom: str = "bloc") -> None:
        """Analyse un bloc, dans sa propre portée."""
        with self.portee(nom):
            self.instructions(bloc.instructions)

    # --- Instructions -----------------------------------------------------------------

    @singledispatchmethod
    def instruction(self, noeud: Instr) -> None:
        """Analyse une instruction : une variante par sorte de nœud, enregistrée par
        `@instruction.register`."""
        raise NotImplementedError(f"instruction non gérée : {type(noeud).__name__}")

    @instruction.register
    def _(self, noeud: Declaration) -> None:
        recu = self.expression(
            noeud.valeur
        )  # avant la déclaration : `tuu x = x;` est faux
        if noeud.annotation is not None:
            type_ = self.type_de(noeud.annotation)
            if not compatible(type_, recu):
                self.erreur_type(
                    f"'{noeud.nom}' est déclaré {type_}, mais reçoit {recu}",
                    noeud.valeur.pos,
                )
        else:
            type_ = INCONNU if recu is AORE else recu  # inférence
        genre = Genre.CONSTANTE if noeud.constante else Genre.VARIABLE
        self.declarer(noeud.nom, genre, noeud.pos, type_)

    @instruction.register
    def _(self, noeud: Affectation) -> None:
        recu = self.expression(noeud.valeur)
        match noeud.cible:
            case Variable(nom, pos):
                trouve = self.table.chercher_avec_portee(nom)
                if trouve is None:
                    self._non_declare(nom, pos)
                    return
                symbole, portee = trouve
                if symbole.genre in (Genre.CONSTANTE, Genre.BOUCLE):
                    self.erreur(
                        f"on ne peut pas affecter la {symbole.genre.value} '{nom}'", pos
                    )
                    return
                if not symbole.genre.est_valeur:
                    self.erreur(f"on ne peut pas affecter la fonction '{nom}'", pos)
                    return
                est_globale = portee is self.table.globale
                self._globale(symbole, est_globale, pos)
                if self._fonction is not None and est_globale:
                    self._fonction.globales_modifiees.add(nom)
                if not compatible(symbole.type, recu):
                    self.erreur_type(
                        f"'{nom}' est de type {symbole.type}, mais reçoit {recu}",
                        noeud.valeur.pos,
                    )
            case Index(objet, indice, pos):
                attendu = self._index(objet, indice, pos)
                self.exiger(attendu, recu, "élément de la tapura", noeud.valeur.pos)
            case Champ():
                attendu = self.expression(noeud.cible)
                self.exiger(attendu, recu, f"champ {noeud.cible.nom}", noeud.valeur.pos)

    @instruction.register
    def _(self, noeud: ExprInstr) -> None:
        self.expression(noeud.expression)
        if not isinstance(noeud.expression, Appel):
            self.avertir("expression sans effet (son résultat est perdu)", noeud.pos)

    @instruction.register
    def _(self, noeud: Affiche) -> None:
        for valeur in noeud.valeurs:
            self.expression(valeur)

    def condition(self, expression: Expr, mot: str) -> None:
        """Analyse la condition d'un `ahani` ou d'un `tamau` (`mot`), qui doit être
        un `tiahape`."""
        recu = self.expression(expression)
        self.exiger(TIAHAPE, recu, f"condition du {mot}", expression.pos)

    @instruction.register
    def _(self, noeud: Si) -> None:
        for branche in noeud.branches:
            self.condition(branche.condition, "ahani")
            self.bloc(branche.corps, "ahani")
        if noeud.sinon is not None:
            self.bloc(noeud.sinon, "taae")

    @instruction.register
    def _(self, noeud: TantQue) -> None:
        self.condition(noeud.condition, "tamau")
        with self.dans_boucle():
            self.bloc(noeud.corps, "tamau")

    @instruction.register
    def _(self, noeud: Pour) -> None:
        variable = self._type_parcouru(noeud)
        with self.portee("tataitahi"), self.dans_boucle():
            self.declarer(noeud.variable, Genre.BOUCLE, noeud.pos, variable)
            self.instructions(noeud.corps.instructions)

    def _type_parcouru(self, noeud: Pour) -> Type:
        """Le type de la variable de boucle, une fois vérifié ce qui est parcouru."""
        parcouru = self.expression(noeud.iterable)
        if noeud.fin is not None:
            fin = self.expression(noeud.fin)
            self.exiger(NUMERA, parcouru, "borne d'un intervalle", noeud.iterable.pos)
            self.exiger(NUMERA, fin, "borne d'un intervalle", noeud.fin.pos)
            return NUMERA
        depart = None if noeud.depart is None else self.expression(noeud.depart)
        position = noeud.iterable.pos
        variable: Type
        if parcouru is INCONNU:
            return INCONNU
        contenu_liste = PARAU if parcouru is PARAU else element(parcouru, "tapura")
        if contenu_liste is not None:
            variable = contenu_liste
            if noeud.depart is not None:
                self.erreur_type(
                    f"'mai' ne s'emploie qu'avec un upea, pas un {parcouru}", position
                )
            if noeud.mode is not None:
                self.erreur_type(
                    f"'{noeud.mode}' ne s'emploie qu'avec un tumu ou un upea, "
                    f"pas un {parcouru}",
                    position,
                )
            return variable
        if (contenu := element(parcouru, "tumu")) is not None:
            if noeud.depart is not None:
                self.erreur_type(
                    "'mai' ne s'emploie qu'avec un upea, pas un tumu", position
                )
            return tumu(contenu)
        if (cle := element_de(parcouru, ORDONNES)) is not None:
            if noeud.depart is not None:
                self.erreur_type(
                    f"'mai' ne s'emploie qu'avec un upea, pas un {parcouru}", position
                )
            return cle  # les clés, dans l'ordre trié
        if (noeud_type := element(parcouru, "upea")) is not None:
            if depart is not None and noeud.depart is not None:
                self.exiger(noeud_type, depart, "nœud de départ", noeud.depart.pos)
            elif noeud.mode is not None:
                self.erreur_type(
                    f"un parcours '{noeud.mode}' d'un upea demande un point "
                    "de départ : "
                    "ajoutez 'mai'",
                    position,
                )
            return noeud_type
        self.erreur_type(f"on ne peut pas parcourir un {parcouru}", position)
        return INCONNU

    @instruction.register
    def _(self, noeud: Rupture) -> None:
        if self._boucles == 0:
            self.erreur(f"{noeud.genre} hors d'une boucle", noeud.pos)

    @instruction.register
    def _(self, noeud: Retour) -> None:
        fonction = self._fonction
        recu = AORE if noeud.valeur is None else self.expression(noeud.valeur)
        if fonction is None:
            self.erreur("hoi hors d'une fonction", noeud.pos)
            return
        if noeud.valeur is None:
            if fonction.retour not in (AORE, INCONNU):
                self.erreur_type(
                    f"la fonction '{fonction.nom}' doit renvoyer un "
                    f"{fonction.retour} : "
                    "'hoi' seul ne suffit pas",
                    noeud.pos,
                )
        elif fonction.retour is AORE:
            self.erreur_type(
                f"la fonction '{fonction.nom}' ne renvoie rien (-> aore)",
                noeud.valeur.pos,
            )
        elif not compatible(fonction.retour, recu):
            self.erreur_type(
                f"la fonction '{fonction.nom}' doit renvoyer un {fonction.retour}, "
                f"mais renvoie un {recu}",
                noeud.valeur.pos,
            )

    @instruction.register
    def _(self, noeud: Fonction) -> None:
        if self._fonction is not None or self.table.profondeur > 0:
            self.erreur(
                f"la fonction '{noeud.nom}' doit être déclarée au niveau global, "
                "pas dans un bloc",
                noeud.pos,
            )
        parametres = tuple(self.type_de(p.annotation) for p in noeud.parametres)
        retour = self.type_de(noeud.retour)
        signature = Signature(parametres, retour)
        # Déclarée avant son corps : l'appel récursif la trouvera.
        avant = len(self.erreurs)
        self.declarer(noeud.nom, Genre.FONCTION, noeud.pos)
        if len(self.erreurs) == avant:
            symbole = self.table.chercher(noeud.nom)
            assert symbole is not None
            symbole.signature = signature
            self.signatures[noeud.nom] = signature
        info = _Fonction(noeud.nom, retour)
        with self.portee(f"ohipa {noeud.nom}", fonction=True), self.dans_fonction(info):
            for parametre, type_ in zip(noeud.parametres, parametres, strict=True):
                self.declarer(parametre.nom, Genre.PARAMETRE, parametre.pos, type_)
            self.instructions(noeud.corps.instructions)
        self.globales_modifiees[noeud.nom] = frozenset(info.globales_modifiees)
        if retour not in (AORE, INCONNU) and not toujours_retourne(
            noeud.corps.instructions
        ):
            self.erreur_type(
                f"la fonction '{noeud.nom}' doit renvoyer un {retour}, "
                "mais peut se terminer sans 'hoi'",
                noeud.pos,
            )

    # --- Expressions ------------------------------------------------------------------

    @singledispatchmethod
    def expression(self, noeud: Expr) -> Type:
        """Le type d'une expression : une variante par sorte de nœud, enregistrée par
        `@expression.register`."""
        raise NotImplementedError(f"expression non gérée : {type(noeud).__name__}")

    @expression.register
    def _(self, noeud: Entier) -> Type:
        return NUMERA

    @expression.register
    def _(self, noeud: Decimal) -> Type:
        return TUHAA

    @expression.register
    def _(self, noeud: Texte) -> Type:
        return PARAU

    @expression.register
    def _(self, noeud: Booleen) -> Type:
        return TIAHAPE

    @expression.register
    def _(self, noeud: Rien) -> Type:
        return AORE

    @expression.register
    def _(self, noeud: Variable) -> Type:
        symbole = self.lire(noeud.nom, noeud.pos)
        if symbole is None:
            return INCONNU
        if not symbole.genre.est_valeur:
            self.erreur(
                f"'{noeud.nom}' est une fonction, pas une valeur : appelez-la avec "
                f"{noeud.nom}(…)",
                noeud.pos,
            )
            return INCONNU
        return symbole.type

    @expression.register
    def _(self, noeud: Liste) -> Type:
        return tapura(commun_de([self.expression(e) for e in noeud.elements]))

    @expression.register
    def _(self, noeud: Graphe) -> Type:
        noeuds: list[Type] = []
        for arete in noeud.aretes:
            for extremite in (arete.depart, arete.arrivee):
                if extremite is None:  # un nœud seul
                    continue
                t = self.expression(extremite)
                if not est_cle(t):
                    self.erreur_type(
                        f"un nœud de upea doit être un numera, un tuhaa ou un parau, "
                        f"pas un {t}",
                        extremite.pos,
                    )
                    t = INCONNU
                noeuds.append(t)
            if arete.poids is not None:
                poids = self.expression(arete.poids)
                if not (est_nombre(poids) or poids is INCONNU):
                    self.erreur_type(
                        f"le poids d'une arête doit être un nombre, pas un {poids}",
                        arete.poids.pos,
                    )
        return upea(commun_de(noeuds))

    @expression.register
    def _(self, noeud: Unaire) -> Type:
        recu = self.expression(noeud.operande)
        if noeud.op == "eiaha":
            self.exiger(TIAHAPE, recu, "opérande de 'eiaha'", noeud.operande.pos)
            return TIAHAPE
        if est_nombre(recu) or recu is INCONNU:
            return recu
        self.erreur_type(
            f"opérande de '-' : nombre attendu, {recu} reçu", noeud.operande.pos
        )
        return INCONNU

    @expression.register
    def _(self, noeud: Binaire) -> Type:
        gauche = self.expression(noeud.gauche)
        droite = self.expression(noeud.droite)
        return REGLES_BINAIRES[noeud.op](self, noeud, gauche, droite)

    @expression.register
    def _(self, noeud: Collection) -> Type:
        if noeud.sorte == "pupu" and noeud.ordre is not None and noeud.ordre < 3:
            self.erreur("l'ordre d'un arbre B (pupu) est au moins 3", noeud.pos)
        cles = [self.expression(e) for e in noeud.elements]
        for expression, t in zip(noeud.elements, cles, strict=True):
            if not est_cle(t):
                self.erreur_type(
                    f"une clé de {noeud.sorte} doit être un numera, un tuhaa ou un "
                    f"parau, pas un {t}",
                    expression.pos,
                )
        if any(map(est_nombre, cles)) and PARAU in cles:
            self.erreur_type(
                f"clés incomparables dans un {noeud.sorte} : nombres et parau",
                noeud.pos,
            )
        sorte: NomCompose = "ahu" if noeud.sorte == "ahunui" else noeud.sorte
        return Compose(sorte, commun_de([t for t in cles if est_cle(t)]))

    @expression.register
    def _(self, noeud: Appel) -> Type:
        arguments = tuple(self.expression(a) for a in noeud.arguments)
        trouve = self.table.chercher_avec_portee(noeud.nom)
        if trouve is None:
            self._non_declare(noeud.nom, noeud.pos)
            return INCONNU
        symbole = trouve[0]
        symbole.utilise = True
        if symbole.genre.est_valeur:
            self.erreur(
                f"'{noeud.nom}' est une {symbole.genre.value}, pas une fonction",
                noeud.pos,
            )
            return INCONNU
        donnes = len(arguments)
        if symbole.genre is Genre.PREDEFINIE:
            predefinie = PREDEFINIES[noeud.nom]
            maximum = predefinie.maximum
            if donnes < predefinie.minimum or (
                maximum is not None and donnes > maximum
            ):
                self.erreur(
                    f"'{noeud.nom}' attend {predefinie.arite()}, "
                    f"{_pluriel(donnes, 'donné')}",
                    noeud.pos,
                )
                return INCONNU

            def signaler(i: int, message: str) -> None:
                self.erreur_type(message, noeud.arguments[i].pos)

            return predefinie.typer(arguments, signaler)
        signature = symbole.signature
        if signature is None:
            return INCONNU
        attendus = len(signature.parametres)
        if donnes != attendus:
            self.erreur(
                f"'{noeud.nom}' attend {_pluriel(attendus, 'argument')}, "
                f"{_pluriel(donnes, 'donné')}",
                noeud.pos,
            )
            return signature.retour
        for i, (attendu, recu) in enumerate(
            zip(signature.parametres, arguments, strict=True)
        ):
            self.exiger(
                attendu,
                recu,
                f"argument {i + 1} de '{noeud.nom}'",
                noeud.arguments[i].pos,
            )
        return signature.retour

    def _index(self, objet: Expr, indice: Expr, position: Position) -> Type:
        contenant = self.expression(objet)
        type_indice = self.expression(indice)
        self.exiger(NUMERA, type_indice, "indice", indice.pos)
        if contenant is PARAU:
            return PARAU
        contenu = element(contenant, "tapura")
        if contenu is None:
            self.erreur_type(
                f"on ne peut indexer qu'une tapura ou un parau, pas un {contenant}",
                position,
            )
            return INCONNU
        return contenu

    @expression.register
    def _(self, noeud: Index) -> Type:
        return self._index(noeud.objet, noeud.indice, noeud.pos)

    @expression.register
    def _(self, noeud: Champ) -> Type:
        objet = self.expression(noeud.objet)
        if noeud.nom not in CHAMPS:
            self.erreur(
                f"champ inconnu '{noeud.nom}' : un tumu n'a que hotu et amaa", noeud.pos
            )
            return INCONNU
        contenu = element(objet, "tumu")
        if contenu is None:
            self.erreur_type(
                f"seul un tumu a le champ {noeud.nom}, pas un {objet}", noeud.pos
            )
            return INCONNU
        return contenu if noeud.nom == "hotu" else tapura(tumu(contenu))


# --- Les règles des opérateurs binaires ----------------------------------------------
#
# Comme les règles de Pratt du parser : une fonction par famille d'opérateurs,
# rangée dans une table par un décorateur paramétré.

type RegleBinaire = Callable[[Analyseur, Binaire, Type, Type], Type]

REGLES_BINAIRES: dict[str, RegleBinaire] = {}


def regle(*operateurs: str) -> Callable[[RegleBinaire], RegleBinaire]:
    """Enregistre la règle de typage de chacun des `operateurs`."""

    def enregistrer(fonction: RegleBinaire) -> RegleBinaire:
        REGLES_BINAIRES.update(dict.fromkeys(operateurs, fonction))
        return fonction

    return enregistrer


def _incompatibles(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    a.erreur_type(
        f"opérandes de '{noeud.op}' incompatibles : {gauche} et {droite}", noeud.pos
    )
    return INCONNU


@regle("ma", "anei")
def _logique(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    for operande, recu in ((noeud.gauche, gauche), (noeud.droite, droite)):
        a.exiger(TIAHAPE, recu, f"opérande de '{noeud.op}'", operande.pos)
    return TIAHAPE


@regle("==", "!=")
def _egalite(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    if not (compatible(gauche, droite) or compatible(droite, gauche)):
        a.erreur_type(
            f"comparer un {gauche} et un {droite} n'a pas de sens ('{noeud.op}')",
            noeud.pos,
        )
    return TIAHAPE


@regle("<", "<=", ">", ">=")
def _ordre(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    ordonnes = (est_nombre(gauche) and est_nombre(droite)) or gauche == droite == PARAU
    if not (INCONNU in (gauche, droite) or ordonnes):
        a.erreur_type(
            f"comparaison '{noeud.op}' impossible entre {gauche} et {droite}",
            noeud.pos,
        )
    return TIAHAPE


@regle("roto")
def _appartenance(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    if droite is PARAU:
        a.exiger(PARAU, gauche, "élément cherché dans un parau", noeud.gauche.pos)
        return TIAHAPE
    contenu = element_de(droite, COMPOSES)
    if contenu is None:
        a.erreur_type(
            "roto attend une tapura, un parau, un upea ou un arbre à droite, "
            f"pas un {droite}",
            noeud.droite.pos,
        )
    elif not (compatible(contenu, gauche) or compatible(gauche, contenu)):
        a.erreur_type(f"on cherche un {gauche} dans un {droite}", noeud.gauche.pos)
    return TIAHAPE


@regle("-", "*", "/", "%")
def _arithmetique(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    if not all(est_nombre(t) or t is INCONNU for t in (gauche, droite)):
        return _incompatibles(a, noeud, gauche, droite)
    if noeud.op == "/":
        return TUHAA
    if INCONNU in (gauche, droite):
        return INCONNU
    return NUMERA if gauche is droite is NUMERA else TUHAA


@regle("+")
def _plus(a: Analyseur, noeud: Binaire, gauche: Type, droite: Type) -> Type:
    if gauche == droite == PARAU:
        return PARAU
    if isinstance(gauche, Compose) or isinstance(droite, Compose):
        contenus = [element(gauche, "tapura"), element(droite, "tapura")]
        if None in contenus:
            return _incompatibles(a, noeud, gauche, droite)
        return tapura(commun_de([c for c in contenus if c is not None]))
    if PARAU in (gauche, droite) and INCONNU in (gauche, droite):
        return INCONNU
    return _arithmetique(a, noeud, gauche, droite)


def analyser(programme: Programme, *, types: bool = True) -> Analyse:
    """Vérifie `programme` ; lève `ErreursMultiples` s'il y a des erreurs."""
    return Analyseur(types=types).programme(programme)
