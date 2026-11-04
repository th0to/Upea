# Upea

Upea est un petit langage impératif aux mots-clés tahitiens, où les **arbres** et les
**graphes** sont des valeurs de première classe. Il est transpilé en Python 3.12. Un
graphe s'écrit comme une carte des îles, et un même mot-clé, `tataitahi`, parcourt une
liste, un arbre ou un graphe, en profondeur ou en largeur.

C'est un projet d'école (2e année d'informatique). Le langage est décrit dans
[`projet/specification.md`](projet/specification.md) ; [`NOTES.md`](NOTES.md) suit
l'avancement, étape par étape.

## Un exemple

```
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

```
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
3.12, et les outils de développement : Upea lui-même n'a aucune dépendance). Depuis
`projet/` :

```bash
uv run python -m upea run exemples/05_motu.upea        # exécuter
uv run python -m upea check exemples/06_tahua.upea     # vérifier sans exécuter
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py   # vers Python
uv run python -m upea fmt exemples/04_tumu.upea        # présentation canonique
uv run python -m upea repl                             # session interactive
```

Le fichier produit par `transpile` se lance seul (`python fibo.py`) ;
`--prelude externe` le réduit à quelques dizaines de lignes, à côté d'un
`upea_prelude.py`.

## Qualité

Depuis la racine du dépôt :

```bash
uv run pytest projet          # 1 016 tests (4 de plus avec Graphviz installé)
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
