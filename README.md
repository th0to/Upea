# Upea

Upea est un petit langage impératif aux mots-clés tahitiens, où les **arbres** et les
**graphes** sont des valeurs de première classe. Son compilateur, écrit à la main en
Python (lexer, parser, analyse sémantique et typage, deux générateurs), le transpile
en Python 3.12. Un serveur MCP permet à une IA d'apprendre le langage, puis de
vérifier, de corriger et d'exécuter ce qu'elle écrit.

C'est un projet d'école (2e année d'informatique). Le langage est décrit dans
[`projet/specification.md`](projet/specification.md) ; [`NOTES.md`](NOTES.md) suit
l'avancement, étape par étape.

## Un exemple

```upea
// Les îles atteignables depuis Tahiti, et le plus court trajet vers Bora Bora.
tuu iles = upea {
    "Tahiti" <-> "Moorea" : 17,
    "Tahiti" -> "Huahine" : 170,
    "Huahine" <-> "Raiatea" : 40,
    "Raiatea" <-> "Bora Bora" : 70,
};

tataitahi ile roto iles mai "Tahiti" aano {
    faaite "on atteint", ile;
}
faaite ea(iles, "Tahiti", "Bora Bora"), distance(iles, "Tahiti", "Bora Bora"), "km";
faaite iles;

tuu arbre = aifaito [];
tataitahi i roto 1..=7 { amui(arbre, i); }   // dans l'ordre : l'AVL se rééquilibre
faaite arbre;
```

```sortie
on atteint Tahiti
on atteint Moorea
on atteint Huahine
on atteint Raiatea
on atteint Bora Bora
["Tahiti", "Huahine", "Raiatea", "Bora Bora"] 280 km
upea : 5 nœuds, 7 arcs
Tahiti    → Moorea (17), Huahine (170)
Moorea    → Tahiti (17)
Huahine   → Raiatea (40)
Raiatea   → Huahine (40), Bora Bora (70)
Bora Bora → Raiatea (70)
      4
  ┌───┴───┐
  2       6
┌─┴─┐   ┌─┴─┐
1   3   5   7
```

`tuu` déclare une variable, `tataitahi … roto` parcourt, `mai … aano` part d'un nœud
en largeur, et `faaite` affiche : une structure seule est dessinée. Le prélude fournit
les arbres de recherche (ABR, AVL, rouge-noir, arbre B, tas) et les algorithmes
classiques (Dijkstra, Bellman-Ford, Floyd-Warshall, Tarjan, Kruskal, Prim, flot
maximal…). Les dessins s'exportent aussi en Graphviz (`dot`) et en Mermaid.

## Installation

Il faut [uv](https://docs.astral.sh/uv/), qui gère Python et l'environnement : si
Python 3.12 manque, uv le télécharge. Depuis le dossier du projet, celui qui contient
`pyproject.toml` :

```bash
uv sync                # Python 3.12, les outils de développement, le SDK du serveur MCP
uv run pytest projet   # vérifier l'installation : tous les tests passent
```

Upea lui-même n'a aucune dépendance : le SDK `mcp` ne sert qu'au serveur MCP. Si `uv`
n'est pas dans le `PATH`, utilisez son chemin complet (sous Windows, par exemple,
`C:\Users\<vous>\AppData\Roaming\Python\Python311\Scripts\uv.exe`).

## Premiers pas

Depuis `projet/` :

```bash
uv run python -m upea run exemples/05_motu.upea        # exécuter
uv run python -m upea check exemples/06_tahua.upea     # vérifier sans exécuter
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py   # vers Python
uv run python -m upea fmt exemples/04_tumu.upea        # présentation canonique
uv run python -m upea repl                             # session interactive
uv run python -m upea mcp                              # serveur MCP (voir plus bas)
uv run python -m upea --help                           # toutes les options
```

Le fichier produit par `transpile` se lance seul (`python fibo.py`) ;
`--prelude externe` le réduit à quelques dizaines de lignes, à côté d'un
`upea_prelude.py`.

## Le serveur MCP : apprendre Upea à une IA

`uv run python -m upea mcp` est un serveur [MCP](https://modelcontextprotocol.io)
(en stdio) qui permet à une IA comme Claude d'apprendre Upea, puis de se servir du
compilateur pour vérifier, corriger et exécuter ce qu'elle écrit : des ressources (la
spécification, les exemples, les fonctions prédéfinies), six outils (`tokenize`,
`parse`, `verifier`, `formater`, `transpiler`, `executer`) et trois prompts. Ses
outils, ses limites et son branchement dans Claude Code, Claude Desktop ou MCP
Inspector sont décrits dans [`docs/mcp.md`](docs/mcp.md).

## La documentation

| Document | Pour qui | Ce qu'on y trouve |
|---|---|---|
| [`projet/specification.md`](projet/specification.md) | qui écrit en Upea | la référence du langage : vocabulaire, grammaire, sémantique, types, fonctions prédéfinies, limites |
| [`NOTES.md`](NOTES.md) | l'enseignant | l'avancement étape par étape, les choix et les limites, les modifications depuis la validation de la spécification |
| [`docs/tutoriel.md`](docs/tutoriel.md) | qui veut apprendre Upea | une progression pas à pas, du premier programme aux graphes et aux arbres ordonnés, avec des exercices corrigés |
| [`docs/architecture.md`](docs/architecture.md) | un développeur, le jury | la chaîne de compilation, le prélude, le REPL, le serveur MCP, le rôle de chaque module, les choix de conception |
| [`docs/mcp.md`](docs/mcp.md) | qui branche le serveur MCP | ses outils, ressources et prompts, les limites du bac à sable, le branchement dans Claude Code, Claude Desktop et MCP Inspector |
| [`docs/developpement.md`](docs/developpement.md) | un contributeur | l'environnement, les vérifications, l'organisation des tests, la CI, et des recettes : ajouter une prédéfinie, un backend, un mot-clé |
| [`docs/journal/`](docs/journal/index.md) | qui veut retracer la démarche | la chronologie du projet, les plans de travail successifs, et le rapport de l'audit du conseil |

## Qualité

Depuis la racine du dépôt :

```bash
uv run pytest projet                 # les tests
uv run mypy projet                   # typage strict, tests compris
uv run ruff check projet             # style
uv run ruff format --check projet    # mise en forme
```

Mesuré le 6 novembre 2026, sous Windows : 1 327 tests réussis et 4 ignorés (ils
demandent Graphviz) ; aucune erreur de mypy (75 fichiers, et de même avec
`--platform linux` et `--platform darwin`), de `ruff check` ni de `ruff format`.

- Chaque étape du compilateur a ses tests : lexer, parser de Pratt, analyse
  sémantique, typage graduel, deux générateurs de Python (texte, et module `ast`),
  source maps, CLI et REPL.
- Chaque programme d'`exemples/` a sa sortie attendue exacte.
- Des propriétés sont vérifiées par `hypothesis` sur des programmes tirés au hasard :
  le formateur est idempotent, relire `parau(x)` redonne `x`, et les deux générateurs
  produisent le même arbre Python et la même sortie.
- Les invariants des arbres équilibrés (AVL, rouge-noir, arbre B, tas) sont vérifiés
  après chaque opération de suites aléatoires d'ajouts et de retraits.
- Avec `run` et dans le REPL, aucune erreur n'affiche de traceback Python : elle est
  signalée en termes d'Upea, à sa ligne.
- Le serveur MCP est testé avec un client en mémoire, et de bout en bout en stdio :
  rien d'autre que le JSON-RPC n'y passe sur la sortie standard.
- Les programmes de la documentation sont exécutés par les tests, qui comparent leur
  sortie à celle qui est écrite, et chaque lien interne est vérifié.
- CI configurée (GitHub Actions, Windows et Linux) :
  [`tests.yml`](.github/workflows/tests.yml) prévoit pytest, mypy, `ruff check` et
  `ruff format --check` à chaque push et pull request.

## In English

Upea is a small imperative language with Tahitian keywords, in which trees and graphs
are first-class values. Its hand-written compiler (lexer, Pratt parser, semantic
analysis with gradual typing, two code generators) transpiles it to Python 3.12, and
an MCP server lets an AI learn the language, then check, fix and run the programs it
writes. It is a school project: the code, the tests and the documentation are in
French. To try it, install [uv](https://docs.astral.sh/uv/), run `uv sync` and
`uv run pytest projet` from the project folder, then
`uv run python -m upea run exemples/05_motu.upea` from `projet/`. The language
reference is [`projet/specification.md`](projet/specification.md).
