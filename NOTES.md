# Upea — notes de rendu

Upea est un langage aux mots-clés tahitiens, centré sur les arbres (`tumu`) et les
graphes (`upea`), transpilé en Python. La spécification est dans
[`projet/specification.md`](projet/specification.md), les programmes d'exemple dans
[`projet/exemples/`](projet/exemples/), et l'installation, les commandes et l'état de
la qualité dans le [README](README.md).

```upea
tuu iles = upea { "Tahiti" <-> "Moorea" : 17, "Moorea" -> "Huahine" : 160 };
tataitahi ile roto iles mai "Tahiti" aano {
    faaite "on atteint", ile;
}
faaite ea(iles, "Tahiti", "Huahine");
```

## Avancement

Chaque étape a son fichier de tests, que `-k` sélectionne : `uv run pytest projet -k
etape_05`, `-k extension_12`… Les modules sont dans `projet/upea/`.

| Étape | État | Module(s) | Tests |
|---|---|---|---|
| 1 spécification | écrite, **validée par l'enseignant le [DATE À REMPLIR]** <!-- À RELIRE PAR THOMAS --> (modifications depuis : voir plus bas) | `specification.md`, `exemples/` | `test_etape_01_*` |
| 2 tokens | fait | `tokens.py`, `erreurs.py` | `test_etape_02_*` |
| 3 lexer, flux | fait | `lexer.py`, `flux.py` | `test_etape_03_*` |
| 4 AST | fait | `noeuds.py` | `test_etape_04_*` |
| 5 Pratt | fait | `parser.py` | `test_etape_05_*` |
| 6 instructions | fait (récupération d'erreurs, limite de 20) | `parser.py` | `test_etape_06_*` |
| 7 sémantique | fait (avertissements en bonus) | `symboles.py`, `semantique.py` | `test_etape_07_*` |
| 8 génération | fait | `emetteur.py`, `generateur.py`, `prelude.py` et le paquet `execution/` (le prélude) | `test_etape_08_*` |
| 9 CLI, REPL | fait (`--trace`, `:tokens`, `:arbre`, `:python`) | `compilateur.py`, `cli.py`, `repl.py` | `test_etape_09_*` |
| 10 qualité | fait (mypy strict, `Protocol`, formateur) | `backend.py`, `formateur.py` | `test_etape_10_*` |
| 11 module `ast` | fait ; un test différentiel vérifie que les deux backends produisent le même arbre Python (exemples, et programmes tirés au hasard) | `generateur_ast.py` | `test_extension_11_*` |
| 12 types | fait (graduel, types paramétrés `tapura[T]`, `tumu[T]`, `upea[T]`) | `typage.py`, `predefinies.py` | `test_extension_12_*` |
| 13 source maps | fait | `sourcemap.py` | `test_extension_13_*` |
| 14 arbres ordonnés | fait : ABR `imi`, AVL `aifaito`, rouge-noir `uteere`, arbre B `pupu`, tas `ahu` / `ahunui` | `execution/recherche.py`, `arbre_b.py`, `tas.py` | `test_extension_14_*` |
| 15 algorithmes | fait : parcours, hauteur, diamètre, ancêtre commun… sur toutes les sortes d'arbres ; Dijkstra, Bellman-Ford, Floyd-Warshall, Kahn, Tarjan, biparti, Prim, Kruskal, Edmonds-Karp | `execution/vues.py`, `algorithmes_arbres.py`, `algorithmes_graphes.py` | `test_extension_15_*` |
| 16 affichage | fait : `faaite` d'une structure seule la dessine (arbres binaires de haut en bas, `tumu` et arbres B en retrait, graphes en liste d'adjacence), `matrice`, couleurs au terminal, export `dot` (Graphviz) et `mermaid`, nœud seul dans un littéral `upea` | `execution/dessins.py`, `exports.py` | `test_extension_16_*` |
| 17 propriétés | fait (`hypothesis`) : formater est idempotent et garde le sens, relire `parau` redonne une valeur égale, les deux backends font la même chose, sur des programmes et des valeurs tirés au hasard | `tests/generateurs.py` | `test_extension_17_*` |
| 18 serveur MCP | fait (le [plan](docs/journal/PLAN_MCP.md), et le branchement dans le [README](README.md)) : `python -m upea mcp` en stdio (SDK `mcp` 2.x, facultatif ; sans lui, un message et le code 2). Outils `tokenize`, `parse`, `verifier`, `formater`, `transpiler` (diagnostics structurés : sorte, ligne, colonne, message) et `executer` (sous-processus : 5 s par défaut et au plus, 64 Kio de sortie, 512 Mo de mémoire, deux exécutions à la fois, environnement réduit) ; ressources `upea://specification`, `upea://exemples` (chacun avec sa sortie), `upea://predefinies` (signatures calculées à partir des patrons de typage : `pihai(upea[T], T) -> tapura[T]`) ; prompts `ecrire_programme`, `corriger_programme`, `traduire_depuis_python`. Testé en mémoire et de bout en bout en stdio | `serveur_mcp.py`, `atelier.py`, `bac_a_sable.py`, `predefinies.py`, `cli.py` | `test_extension_18_*` |

Les extensions 14 à 18 sont propres au projet : le cours propose les extensions 11 à
13 (`langage/README.md`), puis le serveur MCP (`mcp/README.md`), numéroté ici 18.

## Correspondance avec le projet MCP du cours

Le serveur suit le parcours de `mcp/`, avec ces différences. Les tests du serveur
s'appellent `test_extension_18_*` (décision D9 du [plan MCP](docs/journal/PLAN_MCP.md)) :
`-k mcp_02` … `-k mcp_06` ne sélectionnent rien, `-k extension_18` les sélectionne
tous.

| Étape du cours | Demandé | Dans Upea | Écart |
|---|---|---|---|
| — | un second paquet, `serveur_monlangage/`, lancé par `python -m serveur_monlangage` (`mcp/README.md`) | le module `upea/serveur_mcp.py`, lancé par `python -m upea mcp` | fait autrement : seul ce module importe le SDK, et la CLI ne l'importe qu'à la demande ; le compilateur reste sans dépendance |
| 1 | un serveur d'essai, outils `saluer` et `additionner` | — | non fait |
| 2 | outils `tokenize`, `parse`, `check` ; résultats en `TypedDict` ; `noeud_json` | outils `tokenize`, `parse`, `verifier` (le `check` du cours) ; résultats en dataclasses ; `atelier.noeud_json` | résultats en dataclasses (décision D1 du plan MCP : l'atelier ne dépend pas du SDK) ; ils ont un schéma de sortie |
| 3 | `transpile` avec la source map, `format` avec un champ `modifie` | `transpiler` sans source map, `formater` sans champ `modifie` | non fait |
| 4 | `run(source, delai)`, délai borné par le schéma ; statuts `delai_depasse` et `sortie_tronquee` ; durée de l'exécution | `executer(source, types, backend, delai)`, délai de 0,1 à 5 s ; un délai dépassé est une erreur d'outil (avec la fin de la sortie), une sortie tronquée un champ `tronquee` ; pas de durée | fait autrement, sauf la durée (non faite) |
| 4 | dossier temporaire, environnement réduit, mémoire bornée, context manager qui tue le fils | aucun fichier : la requête passe par l'entrée standard du fils ; environnement réduit ; mémoire et temps CPU bornés (pas de plafond de mémoire sous macOS) ; `communicate` avec délai, puis `kill` | fait autrement |
| 4 | la discussion de sécurité dans la docstring du module de bac à sable | la docstring de `bac_a_sable.py` | aucun |
| 5 | ressources (spécification, exemples), refus de la traversée de chemin ; prompts `ecrire_programme`, `corriger_programme` | les mêmes, plus `upea://predefinies` et le prompt `traduire_depuis_python` | aucun |
| 6 | point d'entrée testé en stdio ; `projet/mcp.exemple.json` testé ; scénario de l'exercice final écrit comme un test ; exercice réel | point d'entrée testé en stdio ; pas de `mcp.exemple.json` ; pas de scénario scripté ; exercice réel : voir plus bas | non fait, sauf le test en stdio |

## Choix à signaler

- **Vocabulaire tahitien** en ASCII, sans ʻeta ni macron (`tuu`, `ohipa`, `faaite`…) ; le
  sens de chaque mot est donné dans la spécification. Il reste à le faire relire par
  quelqu'un qui parle tahitien.
- **Arbres et graphes natifs** : littéral `upea { a -> b : poids, c <-> d }`, champs
  `t.hotu` / `t.amaa`, boucle `tataitahi … mai depart aano|hohonu`, littéraux d'arbres
  ordonnés (`aifaito [5, 3, 8]`, `pupu 4 [1, 2]`). Les structures et les algorithmes sont
  dans le prélude, le paquet `upea/execution/` : de vrais modules Python, vérifiés par
  mypy et testés, concaténés en tête de chaque fichier généré, qui reste autonome ;
  `transpile --prelude externe` les écrit plutôt à côté, dans `upea_prelude.py`, que le
  fichier généré importe.
- **La taille du prélude** : 2 653 lignes, mesurées le 6 novembre 2026 sur
  `exemples/02_fibonacci.upea`. Dans le fichier produit par `uv run python -m upea
  transpile exemples/02_fibonacci.upea`, le séparateur `# --- programme Upea ---` est à
  la ligne 2 656, après le prélude et deux lignes vides. Le fichier fait 2 678 lignes,
  contre 26 avec `--prelude externe`. La spécification et la description de l'outil
  `transpiler` disent « environ 2 500 lignes » ; elles n'ont pas été modifiées.
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
  (délai dépassé, source de plus de 100 Kio, backend inconnu, délai hors des bornes)
  sont des erreurs d'outil.

## Limites connues

Les limites du langage sont dans la spécification (*Limites assumées*). Celles du
serveur MCP :

- les avertissements ne sont connus que d'un programme sans erreur (comme avec
  `check`) ;
- le délai compte le démarrage de Python : de 0,36 à 0,85 s, sur six exécutions de
  `faaite 1;` mesurées le 6 novembre 2026 sur une machine chargée ;
- l'enfant se limite lui-même à deux fois le délai en temps CPU (*job object* sous
  Windows, `RLIMIT_CPU` ailleurs) : si le serveur meurt pendant une boucle sans fin,
  l'enfant ne tourne pas indéfiniment ;
- **limite connue** : le tout premier lancement d'une session, à froid (dossier
  OneDrive, antivirus), peut dépasser le délai de 5 s à lui seul. Le test
  `test_extension_18_bac_a_sable.py::test_un_exemple_donne_sa_sortie_attendue` échoue
  alors une fois, puis passe : c'est arrivé une fois sur trois suites complètes pendant
  l'étape 3. Le délai n'a pas été allongé ;
- aucun plafond de mémoire sous macOS, qui n'applique pas `RLIMIT_AS` ;
- l'environnement réduit de l'enfant n'a été essayé que sous Windows ;
- les résultats des outils sont des dataclasses sans `slots` : avec `slots`,
  pydantic (dans le SDK) perd leur schéma.

## Modifications depuis la validation de la spécification (le [DATE À REMPLIR])

<!-- À RELIRE PAR THOMAS : la date de validation. -->

Après la validation, un audit (le « conseil », dont le rapport porte sur le commit
`ce53700`) a relevé des bugs. Leur correction a demandé les changements de
[`specification.md`](projet/specification.md) ci-dessous, et seulement ceux-là. Le
lot est l'identifiant du rapport, cité dans le message du commit.

| Lot | Endroit | Changement | Raison |
|---|---|---|---|
| L1 | *Limites assumées* | une puce ajoutée : 90 blocs imbriqués, 20 boucles imbriquées, 150 niveaux dans une expression ; au-delà, erreur de syntaxe | `check` acceptait des programmes que Python refusait ensuite de compiler : `run` affichait un traceback, et le REPL s'arrêtait. Ce sont les limites de CPython, désormais vérifiées par le parser |
| M1 | tableau des erreurs d'exécution | la ligne « récursion sans fin » devient « une fonction qui s'appelle plus de 20 000 fois en chaîne », avec le message « récursion trop profonde (plus de 20 000 appels imbriqués) » | la récursion d'une fonction s'arrêtait vers 990 appels, même finie et juste (un ABR en peigne de 1 000 clés) ; la limite est relevée à 20 000 dans le prélude |
| M1 | *Limites assumées* | une puce ajoutée : 20 000 appels imbriqués au plus | écrire la nouvelle limite |
| M1 | *Limites assumées* | les listes imbriquées : « sur plus d'un millier de niveaux » devient « leur affichage et leur comparaison s'arrêtent […] à une profondeur qui dépend de la pile du système (sous Windows, vers un millier de niveaux pour l'affichage et trois mille pour la comparaison ; davantage sous Linux) » | l'affirmation était fausse (l'affichage s'arrêtait à 247 niveaux). Seuils mesurés après M1 : sous Windows, 995 à 997 pour l'affichage et 2 992 pour la comparaison ; sous Linux, l'affichage passe 2 000 niveaux et échoue à 5 000. Ces seuils viennent de la pile C de CPython, propre à chaque système |
| M4 | *Graphes* | « Un nœud existe dès qu'un arc le touche, dès qu'il est écrit seul dans le littéral, ou dès que `amui(g, v)` l'ajoute » | aucune opération ne savait ajouter un nœud isolé : un graphe construit à partir d'une liste de nœuds perdait ses nœuds isolés (`composantes` rendait 1 au lieu de 3), et une copie faite à la main était infidèle |
| M4 | *Fonctions prédéfinies*, `amui` | « ajoute `x` … dans l'arbre ordonné `c`, ou comme nœud du graphe `c` (sans effet s'il y est déjà) » | même raison : `amui` est surchargé, sans nouveau mot réservé |
| L2 | *Lexique*, décimaux | deux phrases ajoutées : un exposant peut suivre un entier ou un décimal (`1e-05`, `1.5e+16`, `2E3`) | l'affichage écrit les très grands et très petits décimaux avec un exposant (`1e-05`), que le lexer refusait : la forme compacte d'une liste ou d'un graphe n'était pas relisible, contre ce que promet la spécification. Aucun programme valide ne change de sens : `1e…` était toujours une erreur |
| L2 | *Limites assumées* | une puce ajoutée : littéral trop grand refusé, trop petit lu `0.0`, `inf` et `nan` non relisibles et refusés comme nœuds, poids et clés | l'exposant rend l'infini facile à écrire (`1e999`), qui donnait `NameError` avec un backend et `inf` avec l'autre ; un NaN dédoublait les nœuds, disparaissait comme clé d'arbre ordonné et faisait planter `bellman_ford` |
| L4 | *Types*, règles | une puce ajoutée : un tas max s'annote `ahu`, l'annotation ne fixe pas l'ordre, `ahunui` n'est pas un nom de type | `tuu h: ahunui = …` donnait « type attendu, trouvé 'ahunui' » sans dire quoi écrire ; le message le dit désormais, et la règle est écrite |
| M6 | *Utilisation*, codes de retour | « `130` exécution interrompue (Ctrl-C) » ajouté | Ctrl-C affichait un traceback dans `run` et tuait la session du REPL (déclarations perdues) ; `run` s'arrête désormais avec le code 130, la convention des shells, et le REPL répond « interrompu » |
| L6 | *Utilisation*, codes de retour | « `1` erreur de compilation (ou fichier illisible, ou impossible à écrire) » | `transpile -o` vers un dossier absent et `fmt --ecrire` sur un fichier en lecture seule affichaient un traceback ; ils donnent désormais un message et le code 1, comme un fichier illisible |

## Outils Python mobilisés

- **Décorateurs paramétrés** : `@prefixe` / `@infixe` (parser), `@regle("+")` (règles de typage des
  opérateurs), `@predefinie`, `@_attend(...)` et `@_sur_graphe(1, 2)` (vérification des arguments à
  l'exécution, avec `functools.wraps`), `@_sorte_upea("aifaito")` (décorateur de classe).
- **Fonctions d'ordre supérieur et lambdas** : la DSL de patrons de `predefinies.py`
  (`signature(_nom, GRAPHE, retour=lambda t: tapura(tapura(t)))`, pour `composantes` et
  `tarjan`), la table de traduction des `TypeError` (`(motif, lambda m: …)`), le tas
  paramétré par `operator.lt` / `operator.gt`, les clés de tri (`key=lambda arete:
  arete[2]`).
- **functools** : `singledispatch` (une vue commune à toutes les sortes d'arbres, l'affichage `_texte`,
  le dessin `_dessin` de chaque structure),
  `singledispatchmethod` (l'analyseur), `reduce` (type commun, choix dans le tas), `cache`, `wraps`.
- **itertools** : `chain.from_iterable`, `pairwise`, `count`, `product`.

## Exercice final du projet MCP

<!-- À REMPLIR PAR THOMAS : la session réelle (`mcp/etapes/06_integration.md`,
consigne 6), dans une session de Claude Code ouverte hors du projet et branchée sur le
serveur. La trace de la conversation va dans `docs/journal/exercice-final/`. Les
observations demandées : l'IA lit-elle la spécification avant d'écrire ? quelles
erreurs fait-elle, et les messages de `verifier` lui suffisent-ils pour corriger ?
combien d'allers-retours avant un programme correct ? ce qui a été amélioré ensuite. -->

*En attente de la session réelle.*

## Usage d'un assistant IA

<!-- À RELIRE PAR THOMAS : brouillon à réécrire avec vos mots. Les crochets marquent
ce que vous seul pouvez dire. -->

J'ai travaillé avec Claude Code (Anthropic) comme assistant de programmation.
[Ce que j'ai décidé et fait moi-même : l'idée du langage, son vocabulaire, …]
[Ce que l'assistant a fait : …] [Comment j'ai relu et vérifié son travail : …]
Les commits écrits avec lui portent la ligne `Co-Authored-By: Claude`. Les plans de
[`docs/journal/`](docs/journal/) sont des documents de travail rédigés par l'assistant,
puis validés par moi ; l'audit du « conseil » a été mené par six agents de Claude
Code.

## Pour vérifier

Les commandes d'installation et de vérification sont dans le [README](README.md)
(*Installation* et *Qualité*). Pour voir les extensions 11 et 13, et le prélude
externe, depuis `projet/` :

```bash
uv run python -m upea transpile exemples/02_fibonacci.upea --backend ast                 # extension 11
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py --sourcemap        # extension 13
uv run python -m upea transpile exemples/02_fibonacci.upea -o fibo.py --prelude externe  # + upea_prelude.py
```

L'organisation des tests, et le profil `long` des propriétés de l'extension 17 (1 000
tirages au lieu de 30), sont décrits dans le [guide du
développeur](docs/developpement.md#3-les-tests).

La liste de contrôle de livraison, qui dit où chaque exigence du cours est remplie, est
dans [`PLAN_LIVRAISON.md`](PLAN_LIVRAISON.md).
