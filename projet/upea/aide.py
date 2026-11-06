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

import re
import unicodedata
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from .predefinies import ABREVIATIONS, PREDEFINIES
from .tokens import MOTS_CLES

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
APERCU = """\
# Upea : l'aide-mémoire (à lire en premier)

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
des enfants), `prefixe(a)`, `teitei(a)` ; arbres de recherche et tas : \
`aifaito [5, 3, 8]`, `ahu [3, 1]`.
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
- Ni fonctions imbriquées, ni fonctions comme valeurs, ni récursion croisée, ni `+=`, \
ni comparaisons chaînées, ni `for … in` ni `range` ni `len` (voir `tataitahi` et \
`roa`).

Pour le détail : `aide("depuis_python")` (la traduction pas à pas), \
`aide("specification")`, `exemples()`.
"""
