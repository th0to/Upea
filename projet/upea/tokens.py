"""Les types de token d'Upea, et la classe `Token`."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .erreurs import Position


class TokenKind(Enum):
    """Tous les types de token.

    La valeur d'un token fixe (mot-clé, symbole) est son lexème ; celle des
    autres est une description entre chevrons.
    """

    # Littéraux et noms
    ENTIER = "<entier>"
    DECIMAL = "<décimal>"
    TEXTE = "<texte>"
    IDENT = "<identifiant>"

    # Mots-clés
    TUU = "tuu"
    MAU = "mau"
    OHIPA = "ohipa"
    HOI = "hoi"
    AHANI = "ahani"
    TAAE = "taae"
    TAMAU = "tamau"
    TATAITAHI = "tataitahi"
    ROTO = "roto"
    MAI = "mai"
    AANO = "aano"
    HOHONU = "hohonu"
    FAAEA = "faaea"
    HAERE = "haere"
    FAAITE = "faaite"
    UPEA = "upea"
    TIA = "tia"
    HAPE = "hape"
    AORE = "aore"
    MA = "ma"
    ANEI = "anei"
    EIAHA = "eiaha"
    IMI = "imi"
    AIFAITO = "aifaito"
    UTEERE = "uteere"
    PUPU = "pupu"
    AHU = "ahu"
    AHUNUI = "ahunui"

    # Symboles
    PAR_G = "("
    PAR_D = ")"
    ACC_G = "{"
    ACC_D = "}"
    CRO_G = "["
    CRO_D = "]"
    VIRGULE = ","
    POINT_VIRGULE = ";"
    DEUX_POINTS = ":"
    POINT = "."
    POINT_POINT = ".."
    POINT_POINT_EGAL = "..="
    FLECHE = "->"
    DOUBLE_FLECHE = "<->"
    PLUS = "+"
    MOINS = "-"
    ETOILE = "*"
    BARRE = "/"
    POURCENT = "%"
    EGAL = "="
    EGAL_EGAL = "=="
    DIFFERENT = "!="
    INF = "<"
    INF_EGAL = "<="
    SUP = ">"
    SUP_EGAL = ">="

    FIN = "<fin>"

    @property
    def est_fixe(self) -> bool:
        """Vrai pour un mot-clé ou un symbole, dont le lexème ne varie pas."""
        valeur = self.value
        description = (
            len(valeur) > 2
            and valeur[0] == "<"
            and valeur[-1] == ">"
            and valeur[1:-1].isalpha()
        )
        return not description

    @property
    def est_mot_cle(self) -> bool:
        return self.est_fixe and self.value.isalpha()

    def __str__(self) -> str:
        return f"'{self.value}'" if self.est_fixe else self.value


#: Les mots réservés, indexés par leur orthographe.
MOTS_CLES: dict[str, TokenKind] = {k.value: k for k in TokenKind if k.est_mot_cle}

#: Les symboles, du plus long au plus court : `->` est essayé avant `-`.
SYMBOLES: list[tuple[str, TokenKind]] = sorted(
    ((k.value, k) for k in TokenKind if k.est_fixe and not k.est_mot_cle),
    key=lambda paire: -len(paire[0]),
)


@dataclass(frozen=True, slots=True)
class Token:
    kind: TokenKind
    lexeme: str
    position: Position
    #: Nombre de caractères occupés dans le source, quand il diffère du lexème
    #: (un texte décodé est plus court que son écriture avec guillemets).
    taille: int = field(default=-1, compare=False)

    @property
    def fin(self) -> Position:
        """La position juste après le token."""
        taille = self.taille if self.taille >= 0 else len(self.lexeme)
        return self.position.decale(taille)

    def __repr__(self) -> str:
        p = self.position
        return f"Token({self.kind.name}, {self.lexeme!r}, {p.ligne}:{p.colonne})"
