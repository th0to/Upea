"""L'aide d'Upea (extension 18) : la source unique des textes qui apprennent le
langage à une IA (ou à quelqu'un qui vient de Python).

Ce module ne dépend pas du SDK `mcp` : les outils du serveur (`aide`, `exemples`), les
ressources et les pages de `docs/` sont tous produits à partir de lui. Il ne dépend que
de `tokens` et de `predefinies`, pas de la façade `compilateur` (qui, elle, l'importera
pour les conseils des messages d'erreur : un cycle serait fatal).

Le sens des mots-clés n'est jamais recopié : il est lu dans la table « Vocabulaire » de
la spécification, qui seule en décide. Seul l'équivalent Python de chaque mot est écrit
ici.
"""

from __future__ import annotations

import argparse
import io
import re
import sys
import unicodedata
from contextlib import suppress
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from . import __version__
from .erreurs import (
    ErreurLexicale,
    ErreurSemantique,
    ErreursMultiples,
    ErreurSyntaxe,
    ErreurUpea,
)
from .lexer import tokenize
from .predefinies import ABREVIATIONS, PREDEFINIES
from .tokens import MOTS_CLES, Token
from .tokens import TokenKind as T

#: Le dossier `projet/` : la spécification et les exemples.
DOSSIER = Path(__file__).resolve().parent.parent
SPECIFICATION = DOSSIER / "specification.md"
EXEMPLES = DOSSIER / "exemples"

#: La phrase qui ouvre chaque description d'outil, et les instructions du serveur :
#: c'est le seul texte sûr d'arriver jusqu'à une IA, quel que soit son client.
PRESENTATION = (
    "Upea est un langage aux mots-clés tahitiens, transpilé en Python. "
    'Si tu ne le connais pas, appelle d\'abord aide("apercu").'
)

#: Les sujets de l'outil `aide`.
SUJETS = ("apercu", "mots_cles", "predefinies", "depuis_python", "specification")


class AideInconnue(LookupError):
    """Un exemple ou un sujet inconnu de l'aide ; le message dit quoi choisir."""


def _lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


# --- Les mots-clés --------------------------------------------------------------------

#: L'équivalent Python de chaque mot-clé, ou « aucun » : seule donnée écrite à la
#: main. Les mots-clés viennent de `tokens.MOTS_CLES`, leur sens de la spécification.
EQUIVALENT_PYTHON: dict[str, str] = {
    "tuu": "`x = 1`",
    "mau": "`PI = 3.14` (une constante, par convention)",
    "ohipa": "`def`",
    "hoi": "`return`",
    "ahani": "`if`",
    "taae": "`else` ; `taae ahani` : `elif`",
    "tamau": "`while`",
    "tataitahi": "`for`",
    "roto": "`in`",
    "mai": "aucun",
    "aano": "aucun",
    "hohonu": "aucun",
    "faaea": "`break`",
    "haere": "`continue`",
    "faaite": "`print`",
    "upea": "aucun",
    "tia": "`True`",
    "hape": "`False`",
    "aore": "`None`",
    "ma": "`and`",
    "anei": "`or`",
    "eiaha": "`not`",
    "imi": "aucun",
    "aifaito": "aucun",
    "uteere": "aucun",
    "pupu": "aucun",
    "ahu": "`heapq` (un tas min)",
    "ahunui": "`heapq` avec des clés négatives (un tas max)",
}


@dataclass(frozen=True)
class MotCle:
    """Un mot-clé d'Upea : son orthographe, le mot tahitien et le rôle que la
    spécification lui donne, et son équivalent Python."""

    mot: str
    tahitien: str
    role: str
    python: str


@cache
def _vocabulaire() -> dict[str, tuple[str, str]]:
    """La table « Vocabulaire » de la spécification : mot-clé → (mot tahitien, rôle)."""
    texte = _lire(SPECIFICATION)
    debut = texte.index("\n## Vocabulaire")
    fin = texte.index("\n## ", debut + 1)
    lignes = re.finditer(
        r"^\|\s*`(\w+)`\s*\|([^|]*)\|([^|]*)\|\s*$", texte[debut:fin], re.MULTILINE
    )
    return {m[1]: (m[2].strip(), m[3].strip()) for m in lignes}


def mots_cles() -> tuple[MotCle, ...]:
    """Les mots-clés d'Upea, dans l'ordre de `tokens.py`.

    Lève `KeyError` si la spécification ne décrit pas l'un d'eux (un test l'attrape).
    """
    vocabulaire = _vocabulaire()
    return tuple(
        MotCle(mot, *vocabulaire[mot], EQUIVALENT_PYTHON[mot]) for mot in MOTS_CLES
    )


def texte_mots_cles() -> str:
    """Le sujet `mots_cles` : tous les mots réservés, leur sens et leur équivalent."""
    lignes = "\n".join(
        f"| `{m.mot}` | {m.tahitien} | {m.role} | {m.python} |" for m in mots_cles()
    )
    return (
        "# Les mots-clés d'Upea\n\n"
        f"Les {len(MOTS_CLES)} mots réservés, dans l'ordre du compilateur. Le sens est "
        "celui de la table « Vocabulaire » de la spécification ; il est approximatif. "
        "Les noms des types et des fonctions prédéfinies (`numera`, `parau`, `tumu`, "
        "`roa`…) ne sont **pas** des mots-clés.\n\n"
        "| Mot-clé | Mot tahitien | Rôle dans Upea | Équivalent Python |\n"
        "|---|---|---|---|\n"
        f"{lignes}\n"
    )


# --- Les exemples ---------------------------------------------------------------------


def exemples_disponibles() -> dict[str, Path]:
    """Les exemples, par nom (`05_motu`)."""
    return {chemin.stem: chemin for chemin in sorted(EXEMPLES.glob("*.upea"))}


def description_exemple(chemin: Path) -> str:
    """Le commentaire en tête d'un exemple, sur une seule ligne."""
    lignes: list[str] = []
    for ligne in _lire(chemin).splitlines():
        if not ligne.startswith("//"):
            break
        lignes.append(ligne.removeprefix("//").strip())
    return " ".join(lignes)


def _bloc(langage: str, texte: str) -> str:
    fin = "" if texte.endswith("\n") else "\n"
    return f"```{langage}\n{texte}{fin}```\n"


def liste_exemples() -> str:
    """La liste des exemples, chacun avec ce qu'il montre."""
    lignes = "\n".join(
        f"- `{nom}` : {description_exemple(chemin)}"
        for nom, chemin in exemples_disponibles().items()
    )
    return (
        "# Les exemples d'Upea\n\n"
        "Des programmes complets, chacun avec sa sortie exacte. Pour en lire un : "
        'exemples("<nom>") (ressource `upea://exemples/<nom>`).\n\n'
        f"{lignes}\n"
    )


def exemple(nom: str) -> str:
    """Un exemple, avec sa sortie exacte. Lève `AideInconnue` si le nom est inconnu
    (rien n'est lu dans ce cas : un nom qui est un chemin n'ouvre aucun fichier)."""
    exemples = exemples_disponibles()
    if nom not in exemples:
        raise AideInconnue(
            f"pas d'exemple « {nom} » ; les exemples : {', '.join(exemples)}"
        )
    chemin = exemples[nom]
    return (
        f"# Exemple {nom}\n\n{description_exemple(chemin)}\n\n"
        f"## Le programme ({chemin.name})\n\n{_bloc('upea', _lire(chemin))}\n"
        "## Sa sortie exacte\n\n"
        f"{_bloc('text', _lire(chemin.with_suffix('.attendu')))}"
    )


# --- Les fonctions prédéfinies --------------------------------------------------------


def texte_predefinies() -> str:
    """Le sujet `predefinies` : la signature de chaque fonction prédéfinie, tirée du
    compilateur lui-même."""
    signatures = "\n".join(f"- `{p.texte}` ({p.arite()})" for p in PREDEFINIES.values())
    abreviations = "\n".join(
        f"- `{abrege}` : `{sens}`" for abrege, sens in ABREVIATIONS.items()
    )
    return (
        "# Les fonctions prédéfinies d'Upea\n\n"
        "Tirées du compilateur : la signature de chaque fonction, telle que le "
        "vérificateur de types la connaît. Ce que fait chaque fonction est décrit "
        'dans la spécification (aide("specification", section="...") ou la '
        "ressource upea://specification ; sections « Fonctions prédéfinies », "
        "« Algorithmes d'arbres », « Algorithmes de graphes » et « Dessins »).\n\n"
        "Notation : `T` est le type des éléments (les nœuds d'un graphe, les clés "
        "ou les valeurs d'un arbre), le même dans toute une signature ; `?` est un "
        "type que le vérificateur ne connaît pas d'avance (souvent une valeur, ou "
        "`aore`) ; `[, x]` est un argument facultatif, et `x...` peut se répéter.\n\n"
        f"## Signatures\n\n{signatures}\n\n## Abréviations\n\n{abreviations}\n"
    )


# --- La spécification, par sections ---------------------------------------------------


@dataclass(frozen=True)
class Section:
    """Une section de la spécification : un titre `##` (avec ses sous-sections) ou un
    titre `###`."""

    nom: str
    titre: str
    niveau: int
    texte: str


def _nom_de_section(titre: str) -> str:
    """`La boucle \\`tataitahi\\`` → `la_boucle_tataitahi` : sans casse, accents,
    ponctuation, ni parenthèse finale."""
    titre = re.sub(r"\s*\(.*\)\s*$", "", titre)
    sans_accents = unicodedata.normalize("NFD", titre)
    sans_accents = "".join(c for c in sans_accents if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "_", sans_accents.lower()).strip("_")


def _sans_article(nom: str) -> str:
    return re.sub(r"^(le|la|les|l|un|une|d)_", "", nom)


@cache
def sections() -> tuple[Section, ...]:
    """Les sections de la spécification, dans l'ordre : les titres `##`, et après
    chacun ses sous-sections `###`. Le texte d'un `##` contient ses sous-sections."""
    texte = _lire(SPECIFICATION)
    titres = list(re.finditer(r"^(#{2,3}) (.+)$", texte, re.MULTILINE))
    trouvees: list[Section] = []
    for i, titre in enumerate(titres):
        niveau = len(titre[1])
        fin = len(texte)
        for suivant in titres[i + 1 :]:
            if len(suivant[1]) <= niveau:
                fin = suivant.start()
                break
        trouvees.append(
            Section(
                _sans_article(_nom_de_section(titre[2])),
                titre[2],
                niveau,
                texte[titre.start() : fin].rstrip() + "\n",
            )
        )
    return tuple(trouvees)


def sommaire_specification() -> str:
    """La liste des sections qu'on peut demander, avec leur taille."""
    lignes = "\n".join(
        f"{'  ' * (s.niveau - 2)}- `{s.nom}` : {s.titre} "
        f"({len(s.texte.encode('utf-8')) / 1024:.1f} Kio)"
        for s in sections()
    )
    total = len(_lire(SPECIFICATION).encode("utf-8")) / 1024
    return (
        "# La spécification d'Upea : les sections\n\n"
        'aide("specification", section="<nom>") rend une section (un titre `##` rend '
        'aussi ses sous-sections) ; section="tout" rend la spécification entière '
        f"({total:.1f} Kio).\n\n{lignes}\n"
    )


def texte_specification(section: str | None = None) -> str:
    """Le sujet `specification` : le sommaire, une section, ou « tout ». Un nom
    inconnu rend le sommaire, précédé de ce qui n'a pas été trouvé."""
    if section is None or not section.strip():
        return sommaire_specification()
    cle = _nom_de_section(section)
    if cle == "tout":
        return _lire(SPECIFICATION)
    for s in sections():
        if _sans_article(cle) == s.nom:
            return s.texte
    return f"Pas de section « {section} ».\n\n{sommaire_specification()}"


# --- L'aide-mémoire -------------------------------------------------------------------

#: Le sujet `apercu` : une page, à lire en premier. Son programme est exécuté par les
#: tests, qui vérifient aussi sa sortie ; sa taille est bornée à 8 Kio.
_APERCU = """\
# Upea @VERSION@ : l'aide-mémoire (à lire en premier)

Upea est un langage impératif à accolades, aux mots-clés tahitiens, transpilé en \
Python 3.12. Les arbres (`tumu`) et les graphes (`upea`) y sont des valeurs de \
première classe. **Ne devine pas la syntaxe** : `si`, `if`, `while`, `def`, `print`, \
`true`, `None`, `+=` n'existent pas (voir `aide("mots_cles")`).

## Démarche

1. Écris le programme complet, en t'appuyant sur cet aide-mémoire et sur `exemples()`.
2. Passe-le à `verifier`, et corrige jusqu'à `valide: true` : les messages donnent la \
ligne et la colonne, et un conseil quand tu as écrit un mot d'un autre langage.
3. Exécute-le avec `executer` et compare sa sortie à celle que tu attends. Une erreur \
du programme est un résultat à lire, pas une panne de l'outil.

## Les bases

- Une instruction finit par `;`, un bloc est entre `{ }`, l'indentation ne compte \
pas. Commentaires : `// ligne` et `/* bloc */`.
- `tuu x = 1;` déclare une variable, `mau PI = 3.14;` une constante. On déclare avant \
d'utiliser, avec une valeur, une seule fois (pas de masquage). On change une valeur \
avec `x = x + 1;` (pas de `+=`). Type facultatif : `tuu x: numera = 1;`.
- Valeurs : `42`, `3.14`, `"texte"` (guillemets droits seulement), `tia` (vrai), \
`hape` (faux), `aore` (rien), `[1, 2]`. Types : `numera` entier, `tuhaa` décimal, \
`parau` texte, `tiahape` booléen, `tapura[T]` liste.
- Opérateurs : `+ - * / %` (`/` rend toujours un décimal), `== != < <= > >=`, `ma` \
(et), `anei` (ou), `eiaha` (non), `x roto l` (appartenance). Les comparaisons ne \
s'enchaînent pas : `a < b ma b < c`. Texte et nombre : `"n = " + parau(n)`.

## Les constructions

- Condition : `ahani c { … } taae ahani d { … } taae { … }` (si, sinon si, sinon).
- Boucle : `tamau c { … }` (tant que) ; `tataitahi i roto 0..n { … }` (`0..=n` inclut \
`n`) ; `tataitahi x roto liste { … }` ; `faaea;` sort de la boucle, `haere;` passe au \
tour suivant.
- Fonction, au niveau global et avant son premier appel : \
`ohipa nom(a, b: numera) -> numera { hoi a + b; }`. Pas de fonction imbriquée, ni \
comme valeur.
- Affichage : `faaite a, b;` (séparés par une espace, puis un saut de ligne). \
`faaite arbre;` ou `faaite graphe;` dessine la structure.
- Listes : `l[0]`, `l[-1]`, `roa(l)` (longueur), `amui(l, x)` (ajouter), \
`tatara(l, x)` (retirer). Un texte aussi : `t[0]`, `roa(t)`.
- Arbres : `tumu(1, tumu(2), tumu(3))`, champs `a.hotu` (valeur) et `a.amaa` (liste \
des enfants), `prefixe(a)`, `teitei(a)` ; ajouter un enfant : \
`amui(a.amaa, tumu(4))` ; arbres de recherche et tas : `aifaito [5, 3, 8]`, \
`ahu [3, 1]`.
- Graphes : `upea { "A" <-> "B" : 17, "B" -> "C" }` (`->` un sens, `<->` deux, `: p` \
le poids) ; `tataitahi n roto g mai "A" aano { … }` parcourt en largeur depuis A \
(`hohonu` : profondeur) ; `ea(g, a, b)` plus court chemin, `motu(g)`, `pihai(g, a)`, \
`taati(g, a, b, p)`. Tout le catalogue : `aide("predefinies")`.

## Un exemple complet

```upea
ohipa somme_carres(l: tapura[numera]) -> numera {
    tuu total = 0;
    tataitahi x roto l {
        total = total + x * x;
    }
    hoi total;
}

tuu notes = [3, 1, 2];
amui(notes, 4);
faaite "somme des carrés :", somme_carres(notes);

tuu i = 0;
tamau i < 3 {
    ahani i == 1 {
        faaite "un";
    } taae {
        faaite "pas un";
    }
    i = i + 1;
}

tuu arbre = tumu(1, tumu(2), tumu(3));
faaite arbre.hotu, roa(arbre.amaa), prefixe(arbre);

tuu iles = upea { "Tahiti" <-> "Moorea" : 17, "Moorea" -> "Huahine" : 160 };
tataitahi ile roto iles mai "Tahiti" aano {
    faaite ile;
}
faaite ea(iles, "Tahiti", "Huahine"), distance(iles, "Tahiti", "Huahine");
```

```sortie
somme des carrés : 30
pas un
un
pas un
1 2 [1, 2, 3]
Tahiti
Moorea
Huahine
["Tahiti", "Moorea", "Huahine"] 177
```

## Ce qu'Upea n'a pas

- Ni dictionnaires, ni ensembles littéraux, ni tuples : une liste de paires, un \
graphe, ou un arbre ordonné (`aifaito`, un ensemble) les remplacent.
- Ni clavier (`input`), ni fichiers, ni réseau, ni aléatoire : écris les entrées dans \
le programme, et un petit générateur pseudo-aléatoire si besoin.
- Ni classes, ni méthodes : un état global et des fonctions, ou une liste par objet \
(`aide("depuis_python")` en donne la recette).
- Pas de `//` : c'est un commentaire. La division entière s'écrit `numera(a / b)`, qui \
tronque vers zéro ; le `//` de Python arrondit vers le bas, ce qui diffère pour les \
négatifs (la formule exacte est dans `depuis_python`).
- Ni fonctions imbriquées, ni fonctions comme valeurs, ni récursion croisée, ni `+=`, \
ni comparaisons chaînées, ni `for … in` ni `range` ni `len` (voir `tataitahi` et \
`roa`).

Pour le détail : `aide("depuis_python")` (la traduction pas à pas), \
`aide("specification")`, `exemples()`.
"""

APERCU = _APERCU.replace("@VERSION@", __version__)


# --- Les faux amis --------------------------------------------------------------------


@dataclass(frozen=True)
class FauxAmi:
    """Un mot que l'on écrit par habitude, et qui n'est pas d'Upea.

    `equivalents` sont les mots d'Upea que le conseil cite (des mots-clés ou des
    fonctions prédéfinies : un test le vérifie). `absent` : rien ne le remplace.
    `intention` : le mot est aussi un nom de variable naturel en français ; le conseil
    reste alors au conditionnel (« si vous vouliez … »).
    """

    mots: tuple[str, ...]
    langage: str
    conseil: str
    equivalents: tuple[str, ...] = ()
    absent: bool = False
    intention: str | None = None


def _faux(
    mots: str,
    langage: str,
    conseil: str,
    equivalents: str = "",
    *,
    absent: bool = False,
    intention: str | None = None,
) -> FauxAmi:
    return FauxAmi(
        tuple(mots.split()),
        langage,
        conseil,
        tuple(equivalents.split()),
        absent,
        intention,
    )


_PYTHON = "Python"
_FRANCAIS = "français"
_AUTRE = "autres langages"

#: La table, courte et assumée. Les mots d'Upea cités viennent de la table de la
#: spécification ; aucun mot de la table n'est un mot-clé d'Upea ni une prédéfinie
#: (sinon il ne serait pas un faux ami : une variable peut donc porter ces noms).
FAUX_AMIS: tuple[FauxAmi, ...] = (
    _faux("if", _PYTHON, "écrivez 'ahani'", "ahani"),
    _faux("elif", _PYTHON, "écrivez 'taae ahani'", "taae ahani"),
    _faux("else", _PYTHON, "écrivez 'taae'", "taae"),
    _faux("while", _PYTHON, "écrivez 'tamau'", "tamau"),
    _faux(
        "for",
        _PYTHON,
        "écrivez 'tataitahi x roto liste', ou 'tataitahi i roto a..b'",
        "tataitahi roto",
    ),
    _faux("in", _PYTHON, "écrivez 'roto'", "roto"),
    _faux("def", _PYTHON, "écrivez 'ohipa'", "ohipa"),
    _faux("return", _PYTHON, "écrivez 'hoi'", "hoi"),
    _faux("break", _PYTHON, "écrivez 'faaea'", "faaea"),
    _faux("continue", _PYTHON, "écrivez 'haere'", "haere"),
    _faux("print", _PYTHON, "écrivez 'faaite'", "faaite"),
    _faux("True", _PYTHON, "écrivez 'tia'", "tia"),
    _faux("False", _PYTHON, "écrivez 'hape'", "hape"),
    _faux("None", _PYTHON, "écrivez 'aore'", "aore"),
    _faux("and", _PYTHON, "écrivez 'ma'", "ma"),
    _faux("or", _PYTHON, "écrivez 'anei'", "anei"),
    _faux("not", _PYTHON, "écrivez 'eiaha'", "eiaha"),
    _faux("pass", _PYTHON, "écrivez un bloc vide : '{ }'"),
    _faux("len", _PYTHON, "écrivez 'roa(x)'", "roa"),
    _faux(
        "range", _PYTHON, "écrivez 'a..b' (ou 'a..=b') dans un 'tataitahi'", "tataitahi"
    ),
    _faux("append", _PYTHON, "écrivez 'amui(liste, x)'", "amui"),
    _faux("int", _PYTHON, "écrivez 'numera(x)'", "numera"),
    _faux("float", _PYTHON, "écrivez 'tuhaa(x)'", "tuhaa"),
    _faux("str", _PYTHON, "écrivez 'parau(x)'", "parau"),
    _faux(
        "input",
        _PYTHON,
        "un programme Upea ne lit pas le clavier ; écrivez les valeurs dans le "
        "programme",
        absent=True,
    ),
    _faux(
        "random randint",
        _PYTHON,
        'pas d\'aléatoire ; voyez aide("depuis_python")',
        absent=True,
    ),
    _faux(
        "import",
        _PYTHON,
        "pas de modules ; les fonctions prédéfinies sont déjà là",
        absent=True,
    ),
    _faux(
        "class",
        _PYTHON,
        "pas de classes ; voyez 'tumu' et 'upea' pour les structures",
        "tumu upea",
        absent=True,
    ),
    _faux(
        "lambda",
        _PYTHON,
        "pas de fonctions comme valeurs ; déclarez une 'ohipa' au niveau global",
        "ohipa",
        absent=True,
    ),
    _faux("si", _FRANCAIS, "écrivez 'ahani'", "ahani"),
    _faux(
        "sinon",
        _FRANCAIS,
        "écrivez 'taae' ('taae ahani' pour « sinon si »)",
        "taae ahani",
    ),
    _faux("tantque", _FRANCAIS, "écrivez 'tamau'", "tamau"),
    _faux(
        "pour",
        _FRANCAIS,
        "écrivez 'tataitahi x roto liste', ou 'tataitahi i roto a..b'",
        "tataitahi roto",
        intention="écrire une boucle",
    ),
    _faux(
        "dans",
        _FRANCAIS,
        "écrivez 'roto'",
        "roto",
        intention="écrire « dans » (une appartenance, un parcours)",
    ),
    _faux(
        "fonction",
        _FRANCAIS,
        "écrivez 'ohipa'",
        "ohipa",
        intention="déclarer une fonction",
    ),
    _faux("retourner", _FRANCAIS, "écrivez 'hoi'", "hoi"),
    _faux(
        "retour",
        _FRANCAIS,
        "écrivez 'hoi'",
        "hoi",
        intention="renvoyer une valeur",
    ),
    _faux("afficher", _FRANCAIS, "écrivez 'faaite'", "faaite"),
    _faux(
        "vrai", _FRANCAIS, "écrivez 'tia'", "tia", intention="écrire la valeur « vrai »"
    ),
    _faux(
        "faux",
        _FRANCAIS,
        "écrivez 'hape'",
        "hape",
        intention="écrire la valeur « faux »",
    ),
    _faux(
        "rien",
        _FRANCAIS,
        "écrivez 'aore'",
        "aore",
        intention="écrire « rien » (l'absence de valeur)",
    ),
    _faux("et", _FRANCAIS, "écrivez 'ma'", "ma"),
    _faux("ou", _FRANCAIS, "écrivez 'anei'", "anei"),
    _faux(
        "non",
        _FRANCAIS,
        "écrivez 'eiaha'",
        "eiaha",
        intention="écrire une négation",
    ),
    _faux("function", _AUTRE, "écrivez 'ohipa'", "ohipa"),
    _faux("let var", _AUTRE, "écrivez 'tuu'", "tuu"),
    _faux("const", _AUTRE, "écrivez 'mau'", "mau"),
    _faux("true", _AUTRE, "écrivez 'tia'", "tia"),
    _faux("false", _AUTRE, "écrivez 'hape'", "hape"),
    _faux("null", _AUTRE, "écrivez 'aore'", "aore"),
)

_PAR_MOT: dict[str, FauxAmi] = {mot: f for f in FAUX_AMIS for mot in f.mots}


def conseil_de(faux: FauxAmi, mot: str) -> str:
    """Le conseil pour `mot`, sans son préfixe « — » : ce qu'on ajoute à un message."""
    if faux.absent:
        return f"'{mot}' n'existe pas en Upea : {faux.conseil}"
    if faux.intention:
        return (
            f"'{mot}' n'est pas un mot-clé d'Upea ; "
            f"si vous vouliez {faux.intention}, {faux.conseil}"
        )
    return f"'{mot}' n'est pas un mot-clé d'Upea : {faux.conseil}"


def texte_faux_amis() -> str:
    """La table des faux amis, pour le sujet `mots_cles` : ce qu'on écrit par
    habitude, et ce que dit le conseil."""
    lignes: list[str] = []
    for faux in FAUX_AMIS:
        mots = ", ".join(f"`{mot}`" for mot in faux.mots)
        conseil = faux.conseil
        if faux.intention:
            conseil = f"si vous vouliez {faux.intention}, {conseil}"
        lignes.append(f"| {mots} | {faux.langage} | {conseil} |")
    return (
        "## Les mots d'un autre langage\n\n"
        "Ces mots ne sont pas d'Upea : `verifier` ajoute un conseil à l'erreur "
        "qu'ils causent. Une variable peut pourtant porter l'un de ces noms, une "
        "fois déclarée.\n\n"
        "| Mot | D'où | Conseil |\n|---|---|---|\n" + "\n".join(lignes) + "\n"
    )


# --- Ajouter les conseils aux erreurs -------------------------------------------------

#: La suggestion que `semantique` ajoute à « 'x' n'est pas déclaré », que le conseil
#: d'un faux ami, ou de déclaration, remplace (elle proposerait une prédéfinie sans
#: rapport : `vrai` → `rahi`, `compteur` → `composantes`).
SUGGESTION = re.compile(r" \(vouliez-vous dire '[^']*' \?\)$")
_NON_DECLARE = re.compile(r"^'([^']+)' n'est pas déclaré")
_OPERATEURS_COMPOSES = {
    T.PLUS: "+",
    T.MOINS: "-",
    T.ETOILE: "*",
    T.BARRE: "/",
    T.POURCENT: "%",
}


class _Contexte:
    """Les tokens du source, et les noms que le programme déclare quelque part."""

    def __init__(self, source: str) -> None:
        self.jetons: list[Token] = []
        with suppress(ErreurLexicale):  # les tokens lus avant l'erreur suffisent
            self.jetons.extend(tokenize(source))
        self.declares = self._declares()

    def _declares(self) -> frozenset[str]:
        """Les noms qui suivent `tuu`, `mau`, `ohipa` ou `tataitahi`, et les paramètres
        des fonctions : un nom que le programmeur déclare n'est jamais un faux ami."""
        jetons = self.jetons
        noms: set[str] = set()
        for i, jeton in enumerate(jetons[:-1]):
            declare = jeton.kind in (T.TUU, T.MAU, T.OHIPA, T.TATAITAHI)
            if declare and jetons[i + 1].kind is T.IDENT:
                noms.add(jetons[i + 1].lexeme)
            if jeton.kind is T.OHIPA and i + 2 < len(jetons):
                j = i + 2
                if jetons[j].kind is T.PAR_G:
                    j += 1
                    while j < len(jetons) and jetons[j].kind not in (T.PAR_D, T.FIN):
                        debut = jetons[j - 1].kind in (T.PAR_G, T.VIRGULE)
                        if jetons[j].kind is T.IDENT and debut:
                            noms.add(jetons[j].lexeme)
                        j += 1
        return frozenset(noms)

    def premier_depuis(self, ligne: int, colonne: int) -> int:
        """L'indice du premier token qui commence à cette position ou après."""
        for i, jeton in enumerate(self.jetons):
            p = jeton.position
            if (p.ligne, p.colonne) >= (ligne, colonne):
                return i
        return len(self.jetons)

    def mot_en(self, i: int) -> tuple[str, int] | None:
        """Le mot de l'identifiant d'indice `i` (« tant que » compte pour un seul) et
        l'indice de son premier token ; `None` si ce n'est pas un identifiant."""
        jetons = self.jetons
        if not 0 <= i < len(jetons) or jetons[i].kind is not T.IDENT:
            return None
        mot = jetons[i].lexeme
        suivant = jetons[i + 1].lexeme if i + 1 < len(jetons) else ""
        if mot == "tant" and suivant == "que":
            return "tant que", i
        if mot == "que" and i > 0 and jetons[i - 1].lexeme == "tant":
            return "tant que", i - 1
        return mot, i

    def faux_ami(self, i: int) -> tuple[FauxAmi, str] | None:
        """Le faux ami que désigne le token d'indice `i`, avec le mot tel qu'écrit ;
        `None` s'il n'y en a pas, si le programme déclare ce nom, ou si le mot qui le
        précède est déjà l'équivalent d'Upea (`hoi retour` : on écrit déjà `hoi`)."""
        trouve = self.mot_en(i)
        if trouve is None:
            return None
        mot, debut = trouve
        faux = _PAR_MOT.get(mot.replace(" ", ""))
        if faux is None or mot in self.declares:
            return None
        if debut > 0 and self.jetons[debut - 1].lexeme in faux.equivalents:
            return None
        return faux, mot


def _conseil_de_syntaxe(contexte: _Contexte, ligne: int, colonne: int) -> str | None:
    """Le conseil pour une erreur de syntaxe à cette position : le token fautif, ou
    celui qui le précède (« ';' attendu après l'expression, trouvé 'x' » signale la
    fin de `si` dans `si x > 1`)."""
    jetons = contexte.jetons
    k = contexte.premier_depuis(ligne, colonne)
    if 1 <= k < len(jetons) and jetons[k].kind is T.EGAL:
        operateur = jetons[k - 1]
        if (
            operateur.kind in _OPERATEURS_COMPOSES
            and operateur.fin == jetons[k].position
        ):
            avant = jetons[k - 2] if k >= 2 else None
            nom = avant.lexeme if avant is not None and avant.kind is T.IDENT else "x"
            signe = _OPERATEURS_COMPOSES[operateur.kind]
            return (
                "Upea n'a pas d'affectation composée : "
                f"écrivez '{nom} = {nom} {signe} …;'"
            )
    for i in (k - 1, k):
        trouve = contexte.faux_ami(i)
        if trouve is not None:
            return conseil_de(*trouve)
    return None


def _conseil_de_nom(
    contexte: _Contexte, message: str, ligne: int, colonne: int
) -> str | None:
    """Le message complété d'un conseil, pour « 'x' n'est pas déclaré » : la
    déclaration d'abord quand `x` est la cible d'une affectation, puis la table."""
    reconnu = _NON_DECLARE.match(message)
    if reconnu is None:
        return None
    nom = reconnu[1]
    jetons = contexte.jetons
    k = contexte.premier_depuis(ligne, colonne)
    if k >= len(jetons) or jetons[k].lexeme != nom or jetons[k].kind is not T.IDENT:
        return None
    base = SUGGESTION.sub("", message)
    cible = k + 1 < len(jetons) and jetons[k + 1].kind is T.EGAL
    if cible and not (k > 0 and jetons[k - 1].kind in (T.TUU, T.MAU)):
        return f"{base} — déclarez-la d'abord : tuu {nom} = …;"
    trouve = contexte.faux_ami(k)
    if trouve is not None:
        return f"{base} — {conseil_de(*trouve)}"
    return None


def ajouter_conseils(erreurs: ErreursMultiples, source: str) -> ErreursMultiples:
    """Les mêmes erreurs, où chaque erreur de syntaxe ou de noms causée par un mot
    d'un autre langage porte, à la fin de son message, un conseil. Les messages
    d'origine sont gardés tels quels devant ; les erreurs de type, lexicales et les
    avertissements ne changent pas."""
    contexte: _Contexte | None = None
    nouvelles: list[ErreurUpea] = []
    change = False
    for erreur in erreurs.erreurs:
        position = erreur.position
        if position is None or type(erreur) not in (ErreurSyntaxe, ErreurSemantique):
            nouvelles.append(erreur)
            continue
        if contexte is None:
            contexte = _Contexte(source)
        if type(erreur) is ErreurSyntaxe:
            conseil = _conseil_de_syntaxe(contexte, position.ligne, position.colonne)
            message = None if conseil is None else f"{erreur.message} — {conseil}"
        else:
            message = _conseil_de_nom(
                contexte, erreur.message, position.ligne, position.colonne
            )
        if message is None:
            nouvelles.append(erreur)
        else:
            nouvelles.append(type(erreur)(message, position))
            change = True
    return ErreursMultiples(nouvelles) if change else erreurs


# --- Depuis Python --------------------------------------------------------------------

#: Ce qu'on écrit en Python, et ce qu'on écrit en Upea à la place. Une cellule Upea qui
#: n'a pas de `…` est un programme : un test l'analyse.
EQUIVALENCES: tuple[tuple[str, str], ...] = (
    ("x = 1", "tuu x = 1;"),
    ("MAX = 10", "mau MAX = 10;"),
    ("x += 1", "x = x + 1;"),
    ("# commentaire", "// commentaire"),
    ("def f(a, b):", "ohipa f(a, b) { … }"),
    ("return v", "hoi v;"),
    ("if c: … elif d: … else: …", "ahani c { … } taae ahani d { … } taae { … }"),
    ("while c:", "tamau c { … }"),
    ("while True:", "tamau tia { … }"),
    ("for i in range(a, b):", "tataitahi i roto a..b { … }"),
    ("for i in range(a, b + 1):", "tataitahi i roto a..=b { … }"),
    ("for x in l:", "tataitahi x roto l { … }"),
    ("break", "faaea;"),
    ("continue", "haere;"),
    ("print(a, b)", "faaite a, b;"),
    ("True", "tia"),
    ("False", "hape"),
    ("None", "aore"),
    ("a and b", "a ma b"),
    ("a or b", "a anei b"),
    ("not a", "eiaha a"),
    ("x in l", "x roto l"),
    ("a < b < c", "a < b ma b < c"),
    ("a // b", "div_ent(a, b)"),
    ("len(l)", "roa(l)"),
    ("l.append(x)", "amui(l, x);"),
    ("l.remove(x)", "tatara(l, x);"),
    ("min(l)", "iti(l)"),
    ("max(l)", "rahi(l)"),
    ("int(x)", "numera(x)"),
    ("float(x)", "tuhaa(x)"),
    ("str(x)", "parau(x)"),
    ('"n = " + str(n)', '"n = " + parau(n)'),
    ("l[-1]", "l[-1]"),
    ("heapq.heappush(h, x)", "amui(h, x);"),
    ("heapq.heappop(h)", "iriti(h)"),
)


#: Ce qui change le plus quand on passe de Python à Upea.
DIFFERENCES = """\
## Ce qui change le plus

- **Toute variable se déclare** avant son premier usage, une seule fois, avec `tuu` \
(ou `mau` pour une constante) : `compteur = 0;` sans déclaration est une erreur, \
`tuu compteur = 0;` la déclare. On ne redéclare pas un nom encore visible.
- Les instructions finissent par `;` et les blocs sont entre accolades : \
l'indentation ne compte pas.
- **Pas de dictionnaires, de tuples, ni de méthodes** (`l.append(x)` devient \
`amui(l, x)`, `len(l)` devient `roa(l)`). Les recettes plus bas les remplacent.
- Une fonction (`ohipa`) se déclare **au niveau global**, avant son premier appel ; \
pas de fonction imbriquée, ni de fonction comme valeur, ni de récursion croisée. Elle \
peut lire et modifier les variables globales déclarées avant elle.
- Les comparaisons ne s'enchaînent pas : `a < b ma b < c` au lieu de `a < b < c`.
- `ma`, `anei`, `eiaha` pour `and`, `or`, `not` ; `tia`, `hape`, `aore` pour `True`, \
`False`, `None`.
- `/` rend toujours un décimal ; il n'y a ni `//` ni `**`. Pour coller un nombre à \
un texte : `"n = " + parau(n)`.
- **Un programme est arrêté au bout de 5 s** (démarrage de Python compris) : une \
exploration exponentielle (l'espace des états d'un taquin, par exemple) le dépasse \
vite ; réduisez la profondeur ou la taille du problème.
- **Pas de clavier, de fichiers, de réseau ni d'aléatoire** : un programme ne fait \
que calculer et afficher.
- Pour un arbre ou un graphe, préférez les structures et les algorithmes d'Upea \
(`upea { "A" -> "B" : 3 }`, `tumu`, `aifaito`, `dijkstra`, `bfs`…) à une \
réimplémentation avec des listes.
"""

#: Ce qu'on écrit à la place de ce qu'Upea n'a pas. Chaque programme est suivi de sa
#: sortie, copiée d'une exécution réelle : les tests les rejouent.
RECETTES = """\
## Remplacer ce qu'Upea n'a pas

### Un dictionnaire : une liste de paires

Une liste de paires `[clé, valeur]`, et deux fonctions pour lire et écrire. Python :

```python
stock = {"pommes": 3, "poires": 5}
stock["bananes"] = 7
stock["pommes"] = 4
print(stock.get("pommes"), stock.get("bananes"), stock.get("kiwis"))
```

Upea :

```upea
ohipa chercher(paires, cle) {
    tataitahi p roto paires {
        ahani p[0] == cle {
            hoi p[1];
        }
    }
    hoi aore;
}

ohipa mettre(paires, cle, valeur) {
    tataitahi p roto paires {
        ahani p[0] == cle {
            p[1] = valeur;
            hoi;
        }
    }
    amui(paires, [cle, valeur]);
}

tuu stock = [["pommes", 3], ["poires", 5]];
mettre(stock, "bananes", 7);
mettre(stock, "pommes", 4);
faaite chercher(stock, "pommes"), chercher(stock, "bananes"), chercher(stock, "kiwis");
faaite stock;
```

```sortie
4 7 aore
[["pommes", 4], ["poires", 5], ["bananes", 7]]
```

La recherche parcourt la liste : c'est linéaire, comme `in` sur une liste Python.

### Un dictionnaire de nombres : un graphe

Quand les valeurs sont des nombres, un graphe fait l'affaire : la valeur d'une clé est \
le poids de l'arc qui va d'un nœud « racine » à cette clé. `taati` écrit (et \
remplace), `teiaha` lit, `roto` teste la présence, `pihai` donne les clés.

```upea
tuu stock = upea { "racine" };
taati(stock, "racine", "pommes", 3);
taati(stock, "racine", "poires", 5);
taati(stock, "racine", "pommes", 4);
faaite teiaha(stock, "racine", "pommes"), "pommes" roto stock, "kiwis" roto stock;
faaite pihai(stock, "racine");
```

```sortie
4 tia hape
["pommes", "poires"]
```

### Un ensemble : un arbre ordonné

Un arbre ordonné (`imi`, `aifaito`, `uteere`, `pupu`) est un ensemble : ajouter une \
clé déjà présente ne fait rien, `roto` teste l'appartenance, `tatara` retire, et \
`tataitahi` parcourt les clés dans l'ordre croissant. Python :

```python
vus = set()
for x in [5, 3, 5, 1, 3]:
    vus.add(x)
print(len(vus), 3 in vus, 4 in vus)
```

Upea :

```upea
tuu vus = aifaito [];
tataitahi x roto [5, 3, 5, 1, 3] {
    amui(vus, x);
}
faaite roa(vus), 3 roto vus, 4 roto vus;
tatara(vus, 3);
tataitahi x roto vus {
    faaite x;
}
```

```sortie
3 tia hape
1
5
```

### Trier une liste

Il n'y a pas de `sorted`. Un tas min (`ahu`) rend ses clés dans l'ordre, doublons \
compris : on y verse la liste, puis on la relit. Python :

```python
print(sorted([5, 3, 8, 3, 1]))
```

Upea :

```upea
tuu tas = ahu [];
tataitahi x roto [5, 3, 8, 3, 1] {
    amui(tas, x);
}
tuu trie = [];
tataitahi x roto tas {
    amui(trie, x);
}
faaite trie;
```

```sortie
[1, 3, 3, 5, 8]
```

### Plusieurs valeurs de retour : une liste

```upea
ohipa min_max(l) {
    hoi [iti(l), rahi(l)];
}
tuu r = min_max([4, 9, 2]);
faaite "min", r[0], "max", r[1];
```

```sortie
min 2 max 9
```

### Une classe : un état et des fonctions

Il n'y a ni classes ni méthodes. Pour un seul objet, l'état devient des variables \
globales et les méthodes des fonctions, qui lisent et modifient les globales déclarées \
avant elles. Python :

```python
class Compteur:
    def __init__(self):
        self.n = 0

    def incremente(self):
        self.n += 1
        return self.n

c = Compteur()
c.incremente()
print(c.incremente())
```

Upea :

```upea
tuu n = 0;

ohipa incremente() -> numera {
    n = n + 1;
    hoi n;
}

incremente();
faaite incremente();
```

```sortie
2
```

Pour plusieurs objets, une liste par objet (ses champs sont ses cases), que l'on passe \
aux fonctions :

```upea
ohipa nouveau_compteur() {
    hoi [0];
}

ohipa incremente(c) {
    c[0] = c[0] + 1;
    hoi c[0];
}

tuu a = nouveau_compteur();
tuu b = nouveau_compteur();
incremente(a);
incremente(a);
incremente(b);
faaite a[0], b[0];
```

```sortie
2 1
```

### La division entière : `//`

`//` n'existe pas : c'est le début d'un commentaire. `/` rend toujours un décimal, et \
`numera(a / b)` tronque vers zéro, alors que le `//` de Python arrondit vers le bas : \
les deux diffèrent dès que le résultat est négatif (`-7 // 2` vaut -4, \
`numera(-7 / 2)` vaut -3). Le reste `%` est le même qu'en Python. La formule exacte \
pour les deux signes retranche 1 quand la division ne tombe pas juste et que les \
signes diffèrent. Python :

```python
print(7 // 2, -7 // 2, 7 // -2, -7 // -2)
```

Upea :

```upea
ohipa div_ent(a: numera, b: numera) -> numera {
    tuu q = numera(a / b);
    ahani a % b != 0 ma (a < 0) != (b < 0) {
        q = q - 1;
    }
    hoi q;
}

faaite div_ent(7, 2), div_ent(-7, 2), div_ent(7, -2), div_ent(-7, -2);
faaite numera(-7 / 2), div_ent(6, -3);
```

```sortie
3 -4 -4 3
-3 -2
```

### Le hasard : un générateur pseudo-aléatoire

Il n'y a pas de `random`. Un générateur congruentiel linéaire, écrit en Upea, donne \
une suite qui a l'air aléatoire et qui est toujours la même pour une même graine : \
c'est pratique pour tester. Python :

```python
import random
print([random.randint(1, 6) for _ in range(8)])
```

Upea :

```upea
tuu graine = 42;

ohipa alea(n: numera) -> numera {
    graine = (graine * 1103515245 + 12345) % 2147483648;
    hoi graine % n;
}

tuu des = [];
tataitahi i roto 0..8 {
    amui(des, alea(6) + 1);
}
faaite des;
```

```sortie
[4, 3, 6, 5, 2, 1, 6, 1]
```

Pour une autre suite, changez la graine.

### Le clavier : des constantes

Un programme Upea ne lit rien : les réponses attendues de l'utilisateur deviennent des \
constantes, écrites en tête du programme. Dites-le à qui lira le programme. \
Python :

```python
nom = input()
age = int(input())
print("Ia ora na", nom + ", dans un an vous aurez", age + 1, "ans.")
```

Upea :

```upea
mau nom = "Teva";
mau age = 27;
faaite "Ia ora na", nom + ", dans un an vous aurez", age + 1, "ans.";
```

```sortie
Ia ora na Teva, dans un an vous aurez 28 ans.
```
"""


def texte_depuis_python() -> str:
    """Le sujet `depuis_python` : comment traduire un programme Python en Upea."""
    lignes = "\n".join(f"| `{python}` | `{upea}` |" for python, upea in EQUIVALENCES)
    return (
        "# De Python à Upea\n\n"
        "Pour qui connaît Python : ce qui change, le tableau des équivalences, et "
        "comment remplacer ce qu'Upea n'a pas (dictionnaires, ensembles, tri, "
        "hasard, clavier).\n\n"
        f"{DIFFERENCES}\n"
        "## Les équivalences\n\n"
        "| Python | Upea |\n|---|---|\n"
        f"{lignes}\n\n"
        "Il n'y a pas d'opérateur de puissance (`x ** 2` : écrivez `x * x`), pas "
        "d'expression conditionnelle (`a if c else b` : un `ahani`) ; `//` est un "
        "commentaire (voir la division entière plus bas).\n\n"
        f"{RECETTES}"
    )


# --- Les sujets de l'outil `aide` -----------------------------------------------------


def texte_sujet(sujet: str, section: str | None = None) -> str:
    """Le texte du sujet demandé à l'outil `aide`. `section` ne sert qu'à la
    spécification. Lève `AideInconnue` pour un sujet inconnu."""
    match sujet:
        case "apercu":
            return APERCU
        case "mots_cles":
            return f"{texte_mots_cles()}\n{texte_faux_amis()}"
        case "predefinies":
            return texte_predefinies()
        case "depuis_python":
            return texte_depuis_python()
        case "specification":
            return texte_specification(section)
        case _:
            raise AideInconnue(
                f"pas de sujet « {sujet} » ; les sujets : {', '.join(SUJETS)}"
            )


# --- Les pages de docs/, générées -----------------------------------------------------

DOCS = DOSSIER.parent / "docs"
COMMANDE_PAGES = "uv run python -m upea.aide --ecrire"
_ENTETE_GENEREE = (
    "<!-- Fichier généré par `upea/aide.py` (`uv run python -m upea.aide --ecrire`) :"
    " ne pas le modifier à la main. -->\n\n"
)


def pages() -> dict[str, str]:
    """Les pages de `docs/` que ce module produit : leur nom de fichier et leur texte.
    Ce sont les mêmes textes que ceux des sujets `apercu` et `depuis_python`."""
    return {
        "aide-memoire.md": _ENTETE_GENEREE + APERCU,
        "depuis-python.md": _ENTETE_GENEREE + texte_depuis_python(),
    }


def ecrire_pages(dossier: Path = DOCS) -> list[Path]:
    """Écrit les pages dans `dossier` (UTF-8, fins de ligne `\\n`) et rend leurs
    chemins."""
    dossier.mkdir(parents=True, exist_ok=True)
    chemins: list[Path] = []
    for nom, texte in pages().items():
        chemin = dossier / nom
        with chemin.open("w", encoding="utf-8", newline="\n") as fichier:
            fichier.write(texte)
        chemins.append(chemin)
    return chemins


def pages_perimees(dossier: Path = DOCS) -> list[str]:
    """Les pages de `dossier` qui n'existent pas, ou qui ne sont plus celles que le
    module produit."""
    perimees: list[str] = []
    for nom, texte in pages().items():
        chemin = dossier / nom
        if not chemin.is_file() or _lire(chemin) != texte:
            perimees.append(nom)
    return perimees


def main(arguments: list[str] | None = None) -> int:
    """`python -m upea.aide --ecrire` réécrit les pages ; `--verifier` échoue (code 1)
    si l'une d'elles ne correspond plus au module."""
    analyseur = argparse.ArgumentParser(
        prog="python -m upea.aide",
        description="Écrit ou vérifie les pages d'aide de docs/ (aide-memoire.md, "
        "depuis-python.md), produites à partir de upea/aide.py.",
    )
    action = analyseur.add_mutually_exclusive_group(required=True)
    action.add_argument("--ecrire", action="store_true", help="réécrire les pages")
    action.add_argument(
        "--verifier", action="store_true", help="échouer si une page est périmée"
    )
    analyseur.add_argument(
        "--dossier", type=Path, default=DOCS, help="le dossier des pages (docs/)"
    )
    options = analyseur.parse_args(arguments)
    for flux in (sys.stdout, sys.stderr):
        if isinstance(flux, io.TextIOWrapper):  # accents lisibles, même redirigés
            flux.reconfigure(encoding="utf-8")
    if options.ecrire:
        for chemin in ecrire_pages(options.dossier):
            print(f"écrit : {chemin}")
        return 0
    perimees = pages_perimees(options.dossier)
    for nom in perimees:
        print(f"page périmée : {nom}", file=sys.stderr)
    if perimees:
        print(f"lancez `{COMMANDE_PAGES}`", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
