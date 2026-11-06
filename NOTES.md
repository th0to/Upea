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
uv run python -m upea mcp            # serveur MCP en stdio (SDK : groupe `mcp`, inclus dans `dev`)
```

## Avancement

| Étape | État | Module(s) | Tests |
|---|---|---|---|
| 1 spécification | écrite, **validée par l'enseignant le [DATE À REMPLIR]** (modifications depuis : voir plus bas) | `specification.md`, `exemples/` | `test_etape_01_*` |
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
| 18 serveur MCP | fait ([`PLAN_MCP.md`](PLAN_MCP.md), branchement dans le [README](README.md)) : `python -m upea mcp` en stdio (SDK `mcp` 2.x, facultatif ; sans lui, un message et le code 2). Outils `verifier`, `formater`, `transpiler` (diagnostics structurés : sorte, ligne, colonne, message) et `executer` (sous-processus : 5 s, 64 Kio de sortie, 512 Mo de mémoire, deux exécutions à la fois) ; ressources `upea://specification`, `upea://exemples` (chacun avec sa sortie), `upea://predefinies` (signatures calculées à partir des patrons de typage : `pihai(upea[T], T) -> tapura[T]`) ; prompts `ecrire_programme`, `traduire_depuis_python`. Testé en mémoire et de bout en bout en stdio | `serveur_mcp.py`, `atelier.py`, `bac_a_sable.py`, `predefinies.py`, `cli.py` | `test_extension_18_*` |

## Modifications depuis la validation de la spécification (le [DATE À REMPLIR])

Après la validation, un audit (le « conseil », rapport du commit `ce53700`) a relevé
des bugs. Leur correction a demandé les changements de
[`specification.md`](projet/specification.md) ci-dessous, et seulement ceux-là. Le
lot est l'identifiant du rapport, cité dans le message du commit.

| Lot | Endroit | Changement | Raison |
|---|---|---|---|
| L1 | *Limites assumées* | une puce ajoutée : 90 blocs imbriqués, 20 boucles imbriquées, 150 niveaux dans une expression ; au-delà, erreur de syntaxe | `check` acceptait des programmes que Python refusait ensuite de compiler : `run` affichait un traceback, et le REPL s'arrêtait. Ce sont les limites de CPython, désormais vérifiées par le parser |
| M1 | tableau des erreurs d'exécution | la ligne « récursion sans fin » devient « une fonction qui s'appelle plus de 20 000 fois en chaîne », avec le message « récursion trop profonde (plus de 20 000 appels imbriqués) » | la récursion d'une fonction s'arrêtait vers 990 appels, même finie et juste (un ABR en peigne de 1 000 clés) ; la limite est relevée à 20 000 dans le prélude |
| M1 | *Limites assumées* | une puce ajoutée : 20 000 appels imbriqués au plus | écrire la nouvelle limite |
| M1 | *Limites assumées* | les listes imbriquées : « sur plus d'un millier de niveaux » devient « leur affichage s'arrête vers un millier de niveaux, et leur comparaison vers trois mille » | l'affirmation était fausse (l'affichage s'arrêtait à 247 niveaux) ; seuils mesurés après M1 : 995 à 997 pour l'affichage, 2 992 pour la comparaison |
| M4 | *Graphes* | « Un nœud existe dès qu'un arc le touche, dès qu'il est écrit seul dans le littéral, ou dès que `amui(g, v)` l'ajoute » | aucune opération ne savait ajouter un nœud isolé : un graphe construit à partir d'une liste de nœuds perdait ses nœuds isolés (`composantes` rendait 1 au lieu de 3), et une copie faite à la main était infidèle |
| M4 | *Fonctions prédéfinies*, `amui` | « ajoute `x` … dans l'arbre ordonné `c`, ou comme nœud du graphe `c` (sans effet s'il y est déjà) » | même raison : `amui` est surchargé, sans nouveau mot réservé |
| L2 | *Lexique*, décimaux | deux phrases ajoutées : un exposant peut suivre un entier ou un décimal (`1e-05`, `1.5e+16`, `2E3`) | l'affichage écrit les très grands et très petits décimaux avec un exposant (`1e-05`), que le lexer refusait : la forme compacte d'une liste ou d'un graphe n'était pas relisible, contre ce que promet la spécification. Aucun programme valide ne change de sens : `1e…` était toujours une erreur |
| L2 | *Limites assumées* | une puce ajoutée : littéral trop grand refusé, trop petit lu `0.0`, `inf` et `nan` non relisibles et refusés comme nœuds, poids et clés | l'exposant rend l'infini facile à écrire (`1e999`), qui donnait `NameError` avec un backend et `inf` avec l'autre ; un NaN dédoublait les nœuds, disparaissait comme clé d'arbre ordonné et faisait planter `bellman_ford` |
| L4 | *Types*, règles | une puce ajoutée : un tas max s'annote `ahu`, l'annotation ne fixe pas l'ordre, `ahunui` n'est pas un nom de type | `tuu h: ahunui = …` donnait « type attendu, trouvé 'ahunui' » sans dire quoi écrire ; le message le dit désormais, et la règle est écrite |
| M6 | *Utilisation*, codes de retour | « `130` exécution interrompue (Ctrl-C) » ajouté | Ctrl-C affichait un traceback dans `run` et tuait la session du REPL (déclarations perdues) ; `run` s'arrête désormais avec le code 130, la convention des shells, et le REPL répond « interrompu » |
| L6 | *Utilisation*, codes de retour | « `1` erreur de compilation (ou fichier illisible, ou impossible à écrire) » | `transpile -o` vers un dossier absent et `fmt --ecrire` sur un fichier en lecture seule affichaient un traceback ; ils donnent désormais un message et le code 1, comme un fichier illisible |

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
- **Serveur MCP** : une erreur de compilation ou d'exécution du programme est un
  *résultat* d'outil, que le modèle lit pour corriger ; seules les pannes de l'outil
  (délai dépassé, source de plus de 100 Kio, backend inconnu) sont des erreurs
  d'outil. Limites :
  - les avertissements ne sont connus que d'un programme sans erreur (comme avec
    `check`) ;
  - le délai de 5 s compte le démarrage de Python (0,3 à 0,7 s ici) ;
  - l'enfant se limite lui-même à deux fois le délai en temps CPU (*job object* sous Windows, `RLIMIT_CPU` ailleurs) : si le serveur meurt pendant une boucle sans fin, l'enfant ne tourne pas indéfiniment ;
  - **limite connue** : le tout premier lancement d'une session, à froid (dossier OneDrive, antivirus), peut dépasser le délai de 5 s à lui seul. Le test `test_extension_18_bac_a_sable.py::test_un_exemple_donne_sa_sortie_attendue` échoue alors une fois, puis passe : c'est arrivé une fois sur trois suites complètes pendant l'étape 3. Le délai n'a pas été allongé ;
  - aucun plafond de mémoire sous macOS, qui n'applique pas `RLIMIT_AS` ;
  - les résultats des outils sont des dataclasses sans `slots` : avec `slots`,
    pydantic (dans le SDK) perd leur schéma.
