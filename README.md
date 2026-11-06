# Upea

Upea est un petit langage impératif aux mots-clés tahitiens, où les **arbres** et les
**graphes** sont des valeurs de première classe. Il est transpilé en Python 3.12. Un
graphe s'écrit comme une carte des îles, et un même mot-clé, `tataitahi`, parcourt une
liste, un arbre ou un graphe, en profondeur ou en largeur.

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

## Commandes

Il faut [uv](https://docs.astral.sh/uv/) ; `uv sync` installe l'environnement (Python
3.12, les outils de développement et le SDK du serveur MCP : Upea lui-même n'a
aucune dépendance). Depuis
`projet/` :

```bash
uv run python -m upea run exemples/05_motu.upea        # exécuter
uv run python -m upea check exemples/06_tahua.upea     # vérifier sans exécuter
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py   # vers Python
uv run python -m upea fmt exemples/04_tumu.upea        # présentation canonique
uv run python -m upea repl                             # session interactive
uv run python -m upea mcp                              # serveur MCP (voir plus bas)
```

Le fichier produit par `transpile` se lance seul (`python fibo.py`) ;
`--prelude externe` le réduit à quelques dizaines de lignes, à côté d'un
`upea_prelude.py`.

## Le serveur MCP : apprendre Upea à une IA

`python -m upea mcp` est un serveur [MCP](https://modelcontextprotocol.io) (en
stdio) qui permet à une IA comme Claude d'apprendre Upea et de se servir du
compilateur pour vérifier, exécuter et corriger ce qu'elle écrit :

- **ressources** : la spécification (`upea://specification`), les exemples avec
  leur sortie exacte (`upea://exemples`, `upea://exemples/05_motu`…), et les
  signatures des fonctions prédéfinies, tirées du compilateur
  (`upea://predefinies`) ;
- **outils** : `verifier` (erreurs et avertissements, avec ligne et colonne),
  `executer` (dans un sous-processus : 5 s, 512 Mo, 64 Kio de sortie au plus,
  et deux fois le délai en temps CPU),
  `transpiler` et `formater` ;
- **prompts** : `ecrire_programme` et `traduire_depuis_python`.

Le serveur dépend du SDK Python `mcp` (version 2), dans un groupe de dépendances à
part : le compilateur, lui, n'en a aucune. `uv sync` l'installe avec les outils de
développement ; pour le serveur seul : `uv sync --no-dev --group mcp`.

Claude Code et Claude Desktop ne fixent pas le dossier courant du serveur :
`uv run --directory` s'en charge. Dans les commandes ci-dessous, remplacer
`<uv>` par le chemin de `uv` (absolu s'il n'est pas dans le `PATH`, par exemple
`C:\Users\<vous>\AppData\Roaming\Python\Python311\Scripts\uv.exe`) et `<dépôt>`
par le chemin absolu de ce dépôt.

**Claude Code** ([documentation](https://code.claude.com/docs/en/mcp)) :

```bash
claude mcp add --transport stdio --scope user upea -- <uv> run --directory <dépôt>/projet python -m upea mcp
claude mcp list        # upea doit être « Connected »
```

`--scope user` rend le serveur disponible dans tous les projets (sans cette option,
dans le seul dossier courant). Dans une session, `/mcp` montre son état,
`@upea:upea://specification` cite une ressource, et `/mcp__upea__ecrire_programme`
lance un prompt. Sous Windows PowerShell 5.1, si `claude` est un script PowerShell
(installation par npm), PowerShell peut retirer le `--` : lancer alors la commande
depuis `cmd` ou Git Bash.

**Claude Desktop** ([documentation](https://modelcontextprotocol.io/docs/develop/connect-local-servers)) :
dans `claude_desktop_config.json` (`%APPDATA%\Claude\` sous Windows,
`~/Library/Application Support/Claude/` sous macOS), puis quitter complètement
Claude Desktop et le relancer :

```json
{
  "mcpServers": {
    "upea": {
      "command": "C:\\Users\\<vous>\\AppData\\Roaming\\Python\\Python311\\Scripts\\uv.exe",
      "args": ["run", "--directory", "C:\\<dépôt>\\projet", "python", "-m", "upea", "mcp"]
    }
  }
}
```

La sortie d'erreur du serveur est dans `%APPDATA%\Claude\logs\mcp-server-upea.log`
(`~/Library/Logs/Claude/` sous macOS).

**MCP Inspector** (une application Node.js, ≥ 22.19 ; rien à installer côté
Python) :

```bash
npx @modelcontextprotocol/inspector <uv> run --directory <dépôt>/projet python -m upea mcp
npx @modelcontextprotocol/inspector --cli <uv> run --directory <dépôt>/projet python -m upea mcp --method tools/list
```

## Qualité

Depuis la racine du dépôt :

```bash
uv run pytest projet          # 1 278 tests (4 de plus avec Graphviz installé)
uv run mypy projet/upea       # typage strict (mypy --strict passe aussi sur les tests)
uv run ruff check projet      # style
```

- Chaque étape du compilateur a ses tests : lexer, parser de Pratt, analyse
  sémantique, typage graduel, deux générateurs de Python (texte, et module `ast`),
  source maps, CLI et REPL.
- Les 10 programmes d'`exemples/` ont leur sortie attendue exacte.
- Des propriétés sont vérifiées par `hypothesis` sur des programmes tirés au hasard :
  le formateur est idempotent, relire `parau(x)` redonne `x`, et les deux générateurs
  produisent le même arbre Python et la même sortie.
- Les invariants des arbres équilibrés (AVL, rouge-noir, arbre B, tas) sont vérifiés
  après chaque opération de suites aléatoires d'ajouts et de retraits.
- Avec `run` et dans le REPL, aucune erreur n'affiche de traceback Python : elle est
  signalée en termes d'Upea, à sa ligne.
- Le serveur MCP est testé avec un client en mémoire, et de bout en bout en stdio :
  rien d'autre que le JSON-RPC n'y passe sur la sortie standard.
- GitHub Actions ([`tests.yml`](.github/workflows/tests.yml)) lance pytest, mypy
  et ruff sous Windows et sous Linux, à chaque push et pull request ; mypy passe
  aussi avec `--platform darwin` (macOS).
