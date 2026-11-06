> Fiche de départ du conseil, état au commit `ce53700`. Le [rapport final](RAPPORT-FINAL.md) dit ce qui a été corrigé depuis.

# Conseil Upea — fiche commune (phase 0)

Fiche factuelle, sans opinion, établie par le modérateur le 2026-11-05 sur le commit `ce53700` (branche `master`, arbre de travail propre). À lire avant toute chose.

## 1. Le projet en bref

- **Upea** : langage impératif à accolades et points-virgules, mots-clés tahitiens écrits en ASCII (sans ʻeta ni macron, choix assumé : `projet/specification.md:44`). Arbres (`tumu`) et graphes (`upea`) sont des valeurs de première classe ; six sortes d'arbres ordonnés (`imi`, `aifaito`, `uteere`, `pupu`, `ahu`, `ahunui`).
- **Cible** : Python 3.12 (`.python-version`), par deux générateurs (texte, et module `ast`).
- **Contexte** : projet d'école, cours « Python avancé ». Les consignes du cours sont **hors du repo**, en lecture seule : `C:/Users/thoma/OneDrive/Bureau/3eme/python/Python_advanced-main/langage/README.md` (critères d'évaluation en fin de fichier) et `.../langage/etapes/01_specification.md` à `13_source_maps.md`. Imposé par le cours : chaîne lexer → parser → sémantique → génération écrite à la main, tests écrits par l'étudiant, `mypy --strict` dès l'étape 10.
- **Statut de la spécification** : « écrite, à faire valider par l'enseignant » (`NOTES.md`, tableau d'avancement). Le vocabulaire « reste à faire relire par quelqu'un qui parle tahitien » (`NOTES.md`, *Choix à signaler*).

## 2. Documentation

| Fichier | Contenu |
|---|---|
| `README.md` | présentation pour un lecteur extérieur, commandes, serveur MCP |
| `NOTES.md` | avancement étape par étape, outils Python mobilisés, choix à signaler |
| `projet/specification.md` (526 l.) | vocabulaire (l. 42-79), lexique (l. 81-102), grammaire EBNF (l. 104-159), priorités (l. 161-181), sémantique (l. 183-416), types (l. 418-462), erreurs (l. 464-480), utilisation (l. 499-512), limites assumées (l. 514-526) |
| `PLAN.md` | **un audit antérieur** (points A à K, N1 à N3) et son plan de correction en 12 lots |
| `PLAN_MCP.md` | plan du serveur MCP (extension 18) |

**Audit antérieur.** `PLAN.md` a déjà traité : `tumu` cyclique (A, C), traduction des erreurs dépendant du texte de CPython (B), prélude recopié (D), deux générateurs (E), `toujours_retourne` (F), nœuds `1`/`1.0` (G), taille de `semantique.py` (H), fins de ligne (I), tests par propriétés (J), README (K), sortie UTF-8 sous Windows (N1), `tumu` profonds (N2), traceback du fichier autonome (N3). L'historique git (`git log --oneline`, 31 commits) montre les commits correspondants (`010fccc`, `ada7f9b`, `d5cb1c6`, `c5c2184`, `5ff9835`, `ff3f41e`, `6c53f33`…). **Un point de ce plan ne se re-signale que s'il a régressé ou s'il a été mal corrigé, preuve à l'appui.** La section 4 de `PLAN.md` liste les décisions qui avaient été soumises à Thomas.

## 3. Structure

```
myLanguage/
├── README.md, NOTES.md, PLAN.md, PLAN_MCP.md, pyproject.toml, uv.lock
├── .github/workflows/tests.yml        pytest, mypy, ruff sous Windows et Linux
└── projet/
    ├── specification.md
    ├── exemples/  01_ia_ora_na … 10_hohoa   (.upea + .attendu, sortie exacte)
    ├── upea/      (paquet, 8 357 lignes ; tests : 5 424 lignes)
    │   ├── tokens.py, erreurs.py, lexer.py, flux.py     jetons, erreurs positionnées, lexer
    │   ├── noeuds.py, parser.py                         AST, parser (Pratt + descente récursive)
    │   ├── symboles.py, semantique.py, typage.py,
    │   │   predefinies.py                               portées, analyse sémantique, typage graduel
    │   ├── generateur.py, emetteur.py                   backend texte (`--backend python`, défaut)
    │   ├── generateur_ast.py                            backend `ast` (`--backend ast`)
    │   ├── formateur.py                                 backend `formateur` (`fmt`)
    │   ├── backend.py                                   `Protocol` Backend
    │   ├── sourcemap.py                                 ligne Python ↔ ligne Upea
    │   ├── prelude.py                                   assemble le prélude à partir de execution/
    │   ├── execution/                                   le prélude : structures, algorithmes, dessins
    │   ├── compilateur.py                               façade (seul point d'entrée de la chaîne)
    │   ├── cli.py, __main__.py, repl.py                 ligne de commande, REPL
    │   └── atelier.py, bac_a_sable.py, serveur_mcp.py   serveur MCP (extension 18)
    └── tests/     22 fichiers test_etape_01 … test_extension_18, + conftest, outils, generateurs
```

Chaîne (façade `projet/upea/compilateur.py`) : `tokenize` (lexer) → `parse` → `analyser` (sémantique + types) → backend → `compile`/`exec` dans un espace contenant le prélude. Les exceptions à l'exécution sont traduites en messages Upea par `compilateur.py:156-265` (`ligne_fautive`, `traduire`).

## 4. Commandes exactes

On passe par `uv run`, comme les tests, la CI et le README. `uv` (0.13.6) **n'est pas dans le PATH** : on l'appelle par son chemin absolu. En Git Bash :

```bash
UV=/c/Users/thoma/AppData/Roaming/Python/Python311/Scripts/uv.exe     # Windows : C:\Users\thoma\AppData\Roaming\Python\Python311\Scripts\uv.exe
```

`uv run` utilise l'environnement `.venv` (CPython 3.12.16) du dépôt. Chemins relatifs à la racine `myLanguage/`.

Exécuter un programme (depuis `projet/`, pour que le paquet `upea` soit importable) :

```bash
cd projet
$UV run python -m upea run exemples/05_motu.upea
$UV run python -m upea run <fichier>.upea [--backend python|ast] [--trace] [--sans-types]
$UV run python -m upea check <fichier>.upea [--sans-types]
$UV run python -m upea transpile <fichier>.upea [--backend python|ast|formateur] [-o sortie.py] [--sourcemap] [--prelude inclus|externe]
$UV run python -m upea fmt <fichier>.upea          # sans --ecrire : n'écrit rien
$UV run python -m upea repl
```

Codes de retour : 0 succès, 1 erreur de compilation, 2 usage, 3 erreur d'exécution (`specification.md:512`).

Exécution **isolée** (délai de 5 s, sortie de 64 Kio, mémoire de 512 Mo par un *job object* sous Windows), depuis `projet/` — **obligatoire** pour tout programme qui teste la mémoire, le délai ou une boucle potentiellement infinie :

```bash
$UV run python -c "from upea import bac_a_sable as b; r = b.executer(open(r'<fichier>.upea', encoding='utf-8').read()); print(r.statut, r.code_retour); print(r.sortie); print(r.rapport)"
```

`bac_a_sable.executer(source, *, types=True, backend="python", delai=5.0, plafond=65536, memoire=512*1024**2)` (`projet/upea/bac_a_sable.py:83`) lève `DelaiDepasse` ou `EnfantEnPanne` en cas de panne.

Tests et qualité (depuis la racine, sans écrire de cache dans le repo) :

```bash
$UV run pytest projet -q -p no:cacheprovider          # ~1 min 50
$UV run pytest projet -q -p no:cacheprovider -k etape_05
$UV run mypy projet --cache-dir "$TEMP/upea-council/<nom>/mypy"
$UV run ruff check projet --no-cache
```

Programmes de test des membres : dans `C:/Users/thoma/AppData/Local/Temp/upea-council/<nom>/` uniquement (hors du repo).

## 5. État constaté par le modérateur

| Vérification | Résultat |
|---|---|
| `pytest projet` | **1 110 réussis, 4 ignorés** (`test_extension_16_affichage.py:265`, Graphviz absent), 107 s |
| `mypy projet` (strict) | `Success: no issues found in 63 source files` |
| `ruff check projet` | `All checks passed!` |
| `run exemples/05_motu.upea` | code 0 ; sortie identique à `05_motu.attendu` **aux `\r` près** |
| `uv run ruff check projet --no-cache` | `All checks passed!` |
| `bac_a_sable.executer("faaite 1 + 1;")` | `succes 0 '2\n'` |
| `run` de `faaite [1, 2][5];` | `…\t.upea:1 : erreur d'exécution : indice hors limites` puis la ligne source ; code 3 |
| `transpile exemples/02_fibonacci.upea` | 2 647 lignes, dont le prélude recopié en tête (comportement documenté, `specification.md:510`) |

**Fins de ligne.** Sous Windows, une sortie redirigée vers un fichier est en CRLF ; les `.attendu` sont en LF (`.gitattributes` : `eol=lf`). Pour comparer une sortie à un `.attendu`, utiliser `diff --strip-trailing-cr`. Les tests de `test_etape_01_exemples.py` comparent en mémoire.

**Environnement.** Windows 11, Git Bash et PowerShell 5.1 disponibles. Graphviz absent. Le SDK `mcp` est installé dans le `.venv`.

## 6. Points de vigilance factuels

- Le projet dépasse les 10 étapes du cours : extensions 11 à 13 du cours, et 14 à 18 ajoutées par l'étudiant (arbres ordonnés, algorithmes, affichage, propriétés `hypothesis`, serveur MCP).
- La spécification déclare ses propres limites (`specification.md:514-526`) : une limite **documentée** n'est pas un écart entre documentation et comportement ; elle peut en revanche être discutée sur le fond.
- Les mots-clés des arbres ordonnés et de leurs opérations sont signalés comme « propositions, à corriger » (`NOTES.md`, *Choix à signaler*).
