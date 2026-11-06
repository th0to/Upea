"""Livraison : la documentation dit vrai.

Les blocs de code Upea (```` ```upea ````) de `README.md`, de `NOTES.md` et de
`docs/*.md` sont des programmes, vérifiés d'après le bloc qui les suit (seules des
lignes vides entre les deux) :

- un bloc ```` ```sortie ```` : le programme s'exécute, et affiche exactement ce
  texte ;
- un bloc ```` ```erreur ```` : le programme échoue, avec exactement ce message
  (celui que `run` écrit sur la sortie d'erreur, pour un fichier `exemple.upea`) ;
- rien de tout cela : le programme passe `check`.

Un bloc placé dans une clôture plus longue (```` ```` ````) n'est pas vérifié : il
montre la convention elle-même. Enfin, chaque lien relatif de la documentation,
`docs/journal/` compris, mène à un fichier qui existe.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pytest

from outils import PROJET, lancer
from upea.compilateur import compiler
from upea.erreurs import ErreurExecution, ErreursMultiples, formater

RACINE = PROJET.parent
DOCS = RACINE / "docs"
#: Les documents dont les programmes sont vérifiés (pas le journal, dont les plans
#: citent des états anciens du langage).
DOCUMENTS = sorted([RACINE / "README.md", RACINE / "NOTES.md", *DOCS.glob("*.md")])
#: Les documents dont les liens sont vérifiés.
AVEC_LIENS = sorted({*DOCUMENTS, *DOCS.rglob("*.md")})
#: Le nom du fichier dans les messages d'erreur attendus.
FICHIER = "exemple.upea"

#: Un bloc de code clôturé : sa clôture (trois accents graves ou plus), son langage,
#: son texte. La clôture de fin a la même longueur que celle du début.
BLOC = re.compile(
    r"^(?P<cloture>`{3,})(?P<langage>[\w-]*)[^\n]*\n(?P<texte>.*?)^(?P=cloture)[ \t]*$",
    re.MULTILINE | re.DOTALL,
)
#: Un lien Markdown, `[texte](cible)`.
LIEN = re.compile(r"\[[^\]\n]*\]\(([^)\s]+)\)")
#: Du code dans le texte, `entre accents graves`, où un lien n'en est pas un.
CODE_EN_LIGNE = re.compile(r"`+[^`\n]*`+")


@dataclass(frozen=True)
class Programme:
    """Un programme de la documentation, et ce qu'il doit donner."""

    document: Path
    ligne: int
    source: str
    sorte: str  # "sortie", "erreur" ou "check"
    attendu: str

    def __str__(self) -> str:
        return f"{self.document.relative_to(RACINE).as_posix()}:{self.ligne}"


def programmes(document: Path) -> list[Programme]:
    """Les programmes Upea de `document`, chacun avec la vérification qu'il demande."""
    texte = document.read_text(encoding="utf-8")
    blocs = list(BLOC.finditer(texte))
    trouves: list[Programme] = []
    for bloc, suivant in zip(blocs, [*blocs[1:], None], strict=True):
        if bloc["langage"] != "upea":
            continue
        ligne = texte.count("\n", 0, bloc.start()) + 1
        colle = (
            suivant is not None
            and suivant["langage"] in ("sortie", "erreur")
            and texte[bloc.end() : suivant.start()].strip() == ""
        )
        if suivant is not None and colle:
            sorte, attendu = suivant["langage"], suivant["texte"]
        else:
            sorte, attendu = "check", ""
        trouves.append(Programme(document, ligne, bloc["texte"], sorte, attendu))
    return trouves


PROGRAMMES = [p for document in DOCUMENTS for p in programmes(document)]


def message_d_erreur(source: str) -> str:
    """Ce que `run` écrit sur la sortie d'erreur quand `source` échoue."""
    try:
        lancer(source)
    except (ErreursMultiples, ErreurExecution) as erreur:
        return formater(erreur, source, FICHIER) + "\n"
    pytest.fail("le programme devait échouer, et il a réussi")


@pytest.mark.parametrize("programme", PROGRAMMES, ids=str)
def test_chaque_programme_de_la_documentation(programme: Programme) -> None:
    match programme.sorte:
        case "sortie":
            assert lancer(programme.source) == programme.attendu
        case "erreur":
            assert message_d_erreur(programme.source) == programme.attendu
        case _:
            compiler(programme.source)  # lève ErreursMultiples s'il est faux


def test_le_readme_montre_un_exemple_verifie() -> None:
    """Un marquage perdu (un bloc `upea` devenu un bloc sans langage) ne passe pas
    inaperçu."""
    assert any(p.sorte == "sortie" for p in programmes(RACINE / "README.md"))


def liens_relatifs(document: Path) -> list[str]:
    """Les cibles des liens de `document` vers un fichier du dépôt (ni adresse web,
    ni ancre seule), hors des blocs de code et du code en ligne."""
    texte = BLOC.sub("", document.read_text(encoding="utf-8"))
    texte = CODE_EN_LIGNE.sub("", texte)
    return [
        cible
        for cible in LIEN.findall(texte)
        if not re.match(r"[a-z][a-z0-9+.-]*:", cible) and not cible.startswith("#")
    ]


@pytest.mark.parametrize(
    "document", AVEC_LIENS, ids=lambda d: d.relative_to(RACINE).as_posix()
)
def test_les_liens_internes_menent_a_un_fichier(document: Path) -> None:
    casses = [
        cible
        for cible in liens_relatifs(document)
        if not (document.parent / cible.partition("#")[0]).exists()
    ]
    assert casses == []


# --- La convention elle-même ----------------------------------------------------------

DOCUMENT_D_ESSAI = """\
# Essai

```upea
faaite 6 * 7;
```

```sortie
42
```

```upea
faaite y;
```

```erreur
exemple.upea:1:8 : erreur sémantique : 'y' n'est pas déclaré
    faaite y;
           ^
```

```upea
tuu x = 1;
```

Un texte entre les deux : le bloc suivant n'est pas la sortie attendue.

```sortie
rien
```

````markdown
```upea
ceci n'est pas vérifié
```
````
"""


def test_la_convention_de_marquage(tmp_path: Path) -> None:
    document = tmp_path / "essai.md"
    document.write_text(DOCUMENT_D_ESSAI, encoding="utf-8")
    trouves = programmes(document)
    assert [(p.ligne, p.sorte) for p in trouves] == [
        (3, "sortie"),
        (11, "erreur"),
        (21, "check"),
    ]
    sortie, erreur, seul = trouves
    assert lancer(sortie.source) == sortie.attendu
    assert message_d_erreur(erreur.source) == erreur.attendu
    compiler(seul.source)


def test_une_erreur_d_execution_s_ecrit_comme_avec_run() -> None:
    assert message_d_erreur("tuu l = [1];\nfaaite l[3];\n") == (
        "exemple.upea:2 : erreur d'exécution : indice hors limites\n    faaite l[3];\n"
    )


def test_seuls_les_liens_vers_un_fichier_sont_verifies(tmp_path: Path) -> None:
    document = tmp_path / "liens.md"
    document.write_text(
        "[web](https://example.org) [ancre](#plus-bas) [courriel](mailto:a@b.c)\n"
        "`[code](pas-un-lien.md)` [fichier](autre.md#section)\n"
        "```text\n[dans un bloc](pas-un-lien.md)\n```\n",
        encoding="utf-8",
    )
    assert liens_relatifs(document) == ["autre.md#section"]
