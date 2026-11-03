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

Depuis `projet/` :

```bash
uv run python -m upea run exemples/05_motu.upea
uv run python -m upea transpile exemples/02_fibonacci.upea --backend ast
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py --sourcemap
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
| 11 module `ast` | fait | `generateur_ast.py` | `test_extension_11_*` |
| 12 types | fait (graduel, types paramétrés `tapura[T]`, `tumu[T]`, `upea[T]`) | `typage.py`, `predefinies.py` | `test_extension_12_*` |
| 13 source maps | fait | `sourcemap.py` | `test_extension_13_*` |

Le serveur MCP n'est pas commencé.

## Choix à signaler

- **Vocabulaire tahitien** en ASCII, sans ʻeta ni macron (`tuu`, `ohipa`, `faaite`…) ; le
  sens de chaque mot est donné dans la spécification. Il reste à le faire relire par
  quelqu'un qui parle tahitien.
- **Arbres et graphes natifs** : littéral `upea { a -> b : poids, c <-> d }`, champs
  `t.hotu` / `t.amaa`, boucle `tataitahi … mai depart aano|hohonu`. Les algorithmes
  (parcours, Dijkstra) sont dans le prélude (`execution.py`), un vrai module Python
  vérifié par mypy et testé, recopié en tête de chaque fichier généré.
- **Comparaisons non associatives** : `a < b < c` est une erreur de syntaxe.
- **Typage graduel intégré à l'analyse sémantique** : `--sans-types` le désactive, ce
  qui permet de tester les erreurs d'exécution que le vérificateur attraperait sinon.
