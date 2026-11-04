# Upea — notes de rendu

Upea est un langage aux mots-clés tahitiens, centré sur les arbres (`tumu`) et les
graphes (`upea`), transpilé en Python. La spécification est dans
[`projet/specification.md`](projet/specification.md), et les programmes d'exemple dans
[`projet/exemples/`](projet/exemples/).

```
tuu iles = upea { "Tahiti" <-> "Moorea" : 17, "Moorea" -> "Huahine" : 160 };
tataitahi ile roto iles mai "Tahiti" aano {
    faaite "on atteint", ile;
}
faaite ea(iles, "Tahiti", "Huahine");
```

## Commandes

Depuis la racine (`myLanguage/`) :

```bash
uv run pytest projet                 # tous les tests (-k etape_05, -k extension_12…)
uv run mypy projet/upea              # typage strict (passe aussi sur projet/, tests compris)
uv run ruff check projet             # style
```

Les propriétés de l'extension 17 (`hypothesis`) font 30 tirages par défaut (profil
`defaut`) ; le profil `long` en fait 1 000, pour chercher plus loin (une dizaine de
minutes) :

```bash
HYPOTHESIS_PROFILE=long uv run pytest projet -k extension_17                # bash
$env:HYPOTHESIS_PROFILE = "long"; uv run pytest projet -k extension_17     # PowerShell
```

Depuis `projet/` :

```bash
uv run python -m upea run exemples/05_motu.upea
uv run python -m upea transpile exemples/02_fibonacci.upea --backend ast
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py --sourcemap
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py --prelude externe  # + upea_prelude.py
uv run python -m upea check exemples/06_tahua.upea
uv run python -m upea fmt exemples/04_tumu.upea
uv run python -m upea repl
```

## Avancement

| Étape | État | Module(s) | Tests |
|---|---|---|---|
| 1 spécification | écrite, **à faire valider par l'enseignant** | `specification.md`, `exemples/` | `test_etape_01_*` |
| 2 tokens | fait | `tokens.py`, `erreurs.py` | `test_etape_02_*` |
| 3 lexer, flux | fait | `lexer.py`, `flux.py` | `test_etape_03_*` |
| 4 AST | fait | `noeuds.py` | `test_etape_04_*` |
| 5 Pratt | fait | `parser.py` | `test_etape_05_*` |
| 6 instructions | fait (récupération d'erreurs, limite de 20) | `parser.py` | `test_etape_06_*` |
| 7 sémantique | fait (avertissements en bonus) | `symboles.py`, `semantique.py` | `test_etape_07_*` |
| 8 génération | fait | `emetteur.py`, `generateur.py`, `execution.py` (prélude) | `test_etape_08_*` |
| 9 CLI, REPL | fait (`--trace`, `:tokens`, `:arbre`, `:python`) | `compilateur.py`, `cli.py`, `repl.py` | `test_etape_09_*` |
| 10 qualité | fait (mypy strict, `Protocol`, formateur) | `backend.py`, `formateur.py` | `test_etape_10_*` |
| 11 module `ast` | fait ; un test différentiel vérifie que les deux backends produisent le même arbre Python (exemples, et programmes tirés au hasard) | `generateur_ast.py` | `test_extension_11_*` |
| 12 types | fait (graduel, types paramétrés `tapura[T]`, `tumu[T]`, `upea[T]`) | `typage.py`, `predefinies.py` | `test_extension_12_*` |
| 13 source maps | fait | `sourcemap.py` | `test_extension_13_*` |
| 14 arbres ordonnés | fait : ABR `imi`, AVL `aifaito`, rouge-noir `uteere`, arbre B `pupu`, tas `ahu` / `ahunui` | `execution/recherche.py`, `arbre_b.py`, `tas.py` | `test_extension_14_*` |
| 15 algorithmes | fait : parcours, hauteur, diamètre, ancêtre commun… sur toutes les sortes d'arbres ; Dijkstra, Bellman-Ford, Floyd-Warshall, Kahn, Tarjan, biparti, Prim, Kruskal, Edmonds-Karp | `execution/vues.py`, `algorithmes_arbres.py`, `algorithmes_graphes.py` | `test_extension_15_*` |
| 16 affichage | fait : `faaite` d'une structure seule la dessine (arbres binaires de haut en bas, `tumu` et arbres B en retrait, graphes en liste d'adjacence), `matrice`, couleurs au terminal, export `dot` (Graphviz) et `mermaid`, nœud seul dans un littéral `upea` | `execution/dessins.py`, `exports.py` | `test_extension_16_*` |
| 17 propriétés | fait (`hypothesis`) : formater est idempotent et garde le sens, relire `parau` redonne une valeur égale, les deux backends font la même chose, sur des programmes et des valeurs tirés au hasard | `tests/generateurs.py` | `test_extension_17_*` |

Le serveur MCP n'est pas commencé.

## Outils Python mobilisés (refactorisation)

- **Décorateurs paramétrés** : `@prefixe` / `@infixe` (parser), `@regle("+")` (règles de typage des
  opérateurs), `@predefinie`, `@_attend(...)` et `@_sur_graphe(1, 2)` (vérification des arguments à
  l'exécution, avec `functools.wraps`), `@_sorte_upea("aifaito")` (décorateur de classe).
- **Fonctions d'ordre supérieur et lambdas** : la DSL de patrons de `predefinies.py`
  (`signature("tarjan", GRAPHE, retour=lambda t: tapura(tapura(t)))`), la table de traduction des
  `TypeError` (`(motif, lambda m: …)`), le tas paramétré par `operator.lt` / `operator.gt`, les clés de
  tri (`key=lambda arete: arete[2]`).
- **functools** : `singledispatch` (une vue commune à toutes les sortes d'arbres, l'affichage `_texte`,
  le dessin `_dessin` de chaque structure),
  `singledispatchmethod` (l'analyseur), `reduce` (type commun, choix dans le tas), `cache`, `wraps`.
- **itertools** : `chain.from_iterable`, `pairwise`, `count`, `product`.

## Choix à signaler

- **Vocabulaire tahitien** en ASCII, sans ʻeta ni macron (`tuu`, `ohipa`, `faaite`…) ; le
  sens de chaque mot est donné dans la spécification. Il reste à le faire relire par
  quelqu'un qui parle tahitien.
- **Arbres et graphes natifs** : littéral `upea { a -> b : poids, c <-> d }`, champs
  `t.hotu` / `t.amaa`, boucle `tataitahi … mai depart aano|hohonu`, littéraux d'arbres
  ordonnés (`aifaito [5, 3, 8]`, `pupu 4 [1, 2]`). Les structures et les algorithmes sont
  dans le prélude, le paquet `upea/execution/` : de vrais modules Python, vérifiés par
  mypy et testés, concaténés en tête de chaque fichier généré (qui reste autonome, mais
  fait environ 2 500 lignes) ; `transpile --prelude externe` les écrit plutôt à côté,
  dans `upea_prelude.py`, que le fichier généré importe.
- Les mots-clés des arbres ordonnés (`imi`, `aifaito`, `uteere`, `pupu`, `ahu`, `ahunui`)
  et des opérations (`tatara`, `iriti`, `iti`, `rahi`, `hohoa`) sont des propositions, à
  corriger. `matrice`, `dot` et `mermaid` gardent leur nom connu, comme les algorithmes.
- **`faaite` d'un arbre ou d'un graphe seul** écrit son dessin sur plusieurs lignes ; avec
  d'autres valeurs, dans une liste ou par `parau`, il garde la forme compacte, relisible
  par le parser. Les sorties attendues des exemples 04, 07, 08 et 09 ont changé en
  conséquence (la logique des programmes, non).
- **Comparaisons non associatives** : `a < b < c` est une erreur de syntaxe.
- **Typage graduel intégré à l'analyse sémantique** : `--sans-types` le désactive, ce
  qui permet de tester les erreurs d'exécution que le vérificateur attraperait sinon.
