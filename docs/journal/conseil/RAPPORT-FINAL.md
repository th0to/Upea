> État au commit `ce53700`. Corrigé depuis : M1 à M6, L1, L2, L4, L5, L6 (étape 3, commits `dd46173` à `5e64cfa`). Non traité : M7 (l'exercice final du projet MCP, à faire par Thomas), M9 (la date de validation de la spécification, à remplir), L3, L7, L8 et L10 ; M8 et L9 en partie, pendant la livraison (voir [`NOTES.md`](../../../NOTES.md)). Seuls ce rapport et la fiche [`00-brief.md`](00-brief.md) sont livrés : les pièces qu'il cite (`round-1/`, `round-2/`) sont restées hors du dépôt.

# Conseil Upea — rapport final

Audit contradictoire du commit `ce53700` (2026-11-05) par six membres : architecte (ARCH), compilateur (COMP), graphes (GRAPH), casseur (TEST), linguiste (LING), sceptique (SCEP). Mode B (sous-agents, échanges relayés par le modérateur). 54 constats en phase 1, 7 de plus en phase 2, 25 contestations, 26 réponses, 6 répliques. **Aucun désaccord persistant formel** : toutes les répliques finales sont des acceptations. Le modérateur n'a rien tranché sur le fond. Les gravités ci-dessous sont celles que les auteurs ont retenues après le débat.

Pièces : `00-brief.md` ; `round-1/` (rapports) ; `round-2/debat.md` (échange intégral classé par constat) ; `round-2/<membre>.md` (fiches de position) ; `round-2/brut/` (textes des trois tours, mot pour mot).

---

## 1. Résumé

Upea est solide : les 1 110 tests passent, mypy strict et ruff sont propres, les diagnostics sont d'un niveau rare, et aucune collision d'identifiants n'a été trouvée. Ses défauts sont des bords non gardés, presque tous corrigeables en moins d'une heure chacun. Trois priorités :
1. **Faire valider la spécification et le vocabulaire** par l'enseignant et par un locuteur, avant tout renommage (SCEP-03, LING-05).
2. **Livrer ce que le cours attend du projet MCP** : la session réelle avec une IA, et une table de correspondance des écarts (SCEP-01, SCEP-02).
3. **Corriger les bugs avérés les moins chers**, comme la récursion utilisateur limitée à environ 1 000 niveaux, les entiers de plus de 4 300 chiffres et les tracebacks qui fuient encore (§2 et §4).

---

## 2. Problèmes consensuels

Le classement suit la gravité, puis le rapport entre l'impact et le coût. La colonne « Soutiens » liste l'auteur, puis les membres qui ont **renforcé** le constat avec une preuve nouvelle ou qui l'ont trouvé **indépendamment** (doublon). Les autres membres ont lu le constat sans le contester.

### 2.1 Majeurs

| # | Problème | Preuve | Solution retenue | Coût | Soutiens |
|---|---|---|---|---|---|
| M1 | **La récursion d'une fonction utilisateur casse vers 990 niveaux**, avec le message de la « récursion sans fin ». Elle échoue sur l'ABR en peigne que la spécification met en avant. | `profond_991` réussit et `profond_993` échoue (bac à sable) ; `abr_peigne.upea` (0..1200) ; aucun `setrecursionlimit` dans `projet/upea` ; `specification.md:411`, `:525` | `sys.setrecursionlimit(20_000)` pour le code utilisateur et en tête du fichier autonome ; limite écrite dans *Limites assumées* ; message « récursion trop profonde (plus de N appels imbriqués) ». Mesuré sûr sous Windows (le pire cas) jusqu'à 90 000 niveaux ; une récursion infinie s'arrête proprement en 0,15 s. | S | graphes (GRAPH-01), casseur (TEST-07, relevé à majeur), compilateur |
| M2 | **Les entiers « à précision illimitée » ne s'affichent plus au-delà de 4 300 chiffres**, et le message cite une API Python. Un littéral de 5 000 chiffres produit un traceback du compilateur. | `factorielle(2000)` donne `erreur inattendue (ValueError : Exceeds the limit (4300 digits)…)` ; `specification.md:189` ; `parser.py:463` | `sys.set_int_max_str_digits(0)` dans le prélude (`execution/base.py`) **et** côté compilateur (le littéral est converti par `parser.py:463`, hors prélude). Sans risque : un million de chiffres en 0,81 s sous 3.12, et le source MCP est plafonné à 100 Kio. | S | casseur (TEST-01, majeur), architecte (ARCH-04, mineur), compilateur (COMP-06, mineur), sceptique |
| M3 | **`kruskal` et `prim` perdent les nœuds isolés.** La « forêt couvrante » ne couvre pas le graphe. | `couvrant.upea` : 3 nœuds sur 5 ; `algorithmes_graphes.py:311-316` ; le test `test_extension_15_algorithmes.py:155-157` compare `k` à lui-même ; contredit `specification.md:388` | Passer les nœuds à `_couvrant`, puis ajouter au test une comparaison avec le graphe d'entrée. | S | graphes (GRAPH-03), sceptique (« bug avéré », exception (a) de SCEP-04) |
| M4 | **Un nœud isolé ne peut pas être ajouté à un graphe**, alors que le littéral sait le faire. Le cas standard « liste de nœuds + liste d'arêtes » donne un résultat faux en silence, et une copie de graphe faite à la main est infidèle. | `t3/liste_noeuds.upea` : `composantes : 1` au lieu de 3 ; `copie.upea` : `g == copie(g)` vaut `hape` ; `amui(g, "X")` donne une erreur de type ; `parser.py:520-524` | `amui(g, v)` : ajoute le nœud, sans effet s'il existe déjà. Mettre à jour dans le même lot la signature (`predefinies.py:247`), la ressource `upea://predefinies` et `test_extension_18_signatures.py`. | S | graphes (GRAPH-06), architecte (ARCH-02, mineur), sceptique (rallié au tour 3), linguiste (préfère la surcharge à un nouveau mot) |
| M5 | **Dans le REPL, une erreur levée dans une fonction d'une saisie antérieure pointe une ligne innocente.** | Programme de COMP-01 : `<repl>:7 … faaite "y";` alors que `run` donne `:3 … hoi l[3];` ; reproduction indépendante avec `div(1, 0)` (casseur), intermittente ; `compilateur.py:30`, `:147`, `:156-163` | Un nom de fichier par saisie (`<upea-1>`, …) et une table `nom → SourceMap` dans `_Session`. | S | compilateur (COMP-01), casseur |
| M6 | **Ctrl-C pendant une évaluation tue la session du REPL** (traceback, déclarations perdues), et `run` affiche un traceback. | `KeyboardInterrupt` via `_thread.interrupt_main` ; `compilateur.py:150`, `cli.py:59-81`, `:160-167` ; validation de l'étape 9 du cours (« le REPL survit aux erreurs ») | `except KeyboardInterrupt` dans `_Session.evaluer` (affiche « interrompu », garde l'état) et dans `commande_run` (code 130). | S | compilateur (COMP-02), sceptique |
| M7 | **L'exercice final du projet MCP manque** : une vraie IA qui écrit et exécute un programme via le serveur, avec sa trace et un scénario testé. | `mcp/etapes/06_integration.md` (*Validation*, consignes 5-6) ; `NOTES.md` sans observation ; aucun test de scénario dans `test_extension_18_*` | Une session réelle (Claude Code, prompt `ecrire_programme`), sa trace conservée, dix lignes d'observations dans `NOTES.md`, puis un test scénarisé avec le `Client` en mémoire. | S + S | sceptique (SCEP-01) |
| M8 | **Le serveur MCP s'écarte du cahier des charges du cours sans le dire** : pas d'outils `tokenize` et `parse`, pas de prompt `corriger_programme`, pas de `mcp.exemple.json`, environnement de l'enfant non réduit, et les sélecteurs `-k mcp_0x` ne trouvent rien. | `serveur_mcp.py:168-240`, `:479-486` ; `bac_a_sable.py:154` ; `pytest --collect-only -k mcp_02` donne `no tests collected` | En minimum, une table « étape MCP → fait / remplacé / écarté, et pourquoi » dans `NOTES.md`, qui renvoie à `-k extension_18`. Ajouts S possibles : `tokenize`/`parse`, `corriger_programme`, `mcp.exemple.json`, environnement réduit (le casseur a vérifié que `{PYTHONPATH, PYTHONUTF8}` suffit sous Windows). | S | sceptique (SCEP-02), casseur |
| M9 | **La spécification n'est pas validée par l'enseignant**, alors que 18 étapes sont faites, et une partie du vocabulaire est marquée « à corriger ». | `NOTES.md:52`, `:97` ; `langage/etapes/01_specification.md` (consigne 6) ; `specification.md:77` | La présenter maintenant et noter la date et les retours. Chaque renommage touche aussi `execution/base.py:29`, `:159`, `:170` et les `.attendu` (22, 14 et 6 occurrences de `tia`, `hape`, `aore`). | S | sceptique (SCEP-03), linguiste |

### 2.2 Mineurs, regroupés en lots

| # | Lot | IDs | Solution retenue après débat | Coût | Soutiens |
|---|---|---|---|---|---|
| L1 | **Imbrication extrême.** `check` et `verifier` disent « aucune erreur », puis `run` affiche un traceback (201 termes, 100 blocs, 492 parenthèses) ; le REPL meurt ; le MCP renvoie des erreurs opaques. Le README promet « aucun traceback ». | COMP-03, COMP-04, TEST-03, COMP-10, SCEP-09 | (1) Une limite de profondeur dans l'analyse sémantique (environ 90 blocs, environ 150 niveaux d'expression), testée **à l'entrée** de chaque nœud, qui lève une erreur de **compilation** positionnée (code 1). (2) Dans `parse`, `RecursionError` devient `ErreurSyntaxe`. (3) Un filet de seconde barrière autour de `compile()`. (4) `except (RecursionError, ValueError)` dans `atelier`. (5) Une ligne dans *Limites assumées*. Mesure : 98 blocs dans une `ohipa` passent, 99 échouent. | S | compilateur, casseur, sceptique, architecte, linguiste |
| L2 | **Décimaux.** La forme compacte n'est pas relisible (`1e-05`). Un littéral infini donne `NameError: inf` avec le backend texte et `inf` avec `ast`. Les NaN se dédoublent comme nœuds, se perdent comme clés d'arbre ordonné, et `bellman_ford` laisse fuir un `KeyError`. | ARCH-03, COMP-05, GRAPH-08, TEST-11 | (1) Le lexer accepte `(e|E)[+-]?chiffres` (essayé sur une copie hors dépôt : `1..5`, `t.hotu` et `0..e5` sont inchangés ; 254 tests passent ; les deux backends sont identiques). (2) **Dans le même lot**, une garde `math.isfinite` au parser (`parser.py:467-468`), car `1e999` suffit désormais à produire un infini. (3) Les non-finis refusés comme nœuds, poids (`graphes.py:15-37`) et clés (`_verifier_cle`). (4) Une ligne pour `inf`/`nan` et `1e-400 → 0.0` dans *Limites*. (5) `st.floats(allow_nan=False, allow_infinity=False)` dans la propriété de relecture. | S | architecte, compilateur (accepte après essai), graphes, casseur |
| L3 | **Graphie tahitienne.** `tuʻu` est lu comme un identifiant, avec un message trompeur (`tiʻa` → « vouliez-vous dire 'teiaha' ? »). Le NFD est refusé avec un diacritique seul dans le message. L'apostrophe reçoit un conseil faux. Les fautes `taae`/`tae`, `ma`/`mai` sont mal diagnostiquées. | LING-01, ARCH-08, TEST-08, LING-08, LING-02, LING-04 | Dans l'ordre : (1) accepter les marques Mn après une lettre dans un identifiant, appliquer NFC **au seul lexème** et renseigner `taille` (`tokens.py:119-121`) ; les textes restent intacts. (2) Lever une erreur lexicale « mot-clé écrit avec ʻeta ou macron : écrivez 'tuu' » quand la forme sans signes est un mot-clé. (3) Donner un conseil pour `'`, `’` et `‘` entre deux lettres. (4) Mettre les mots-clés parmi les candidats de `difflib` (`semantique.py:271-276`). Voir aussi la question Q1. | S | linguiste, architecte, casseur, sceptique (gravité ramenée à mineur) |
| L4 | **`ahunui` n'est pas un type**, et le message ne le dit pas ; le type `ahu` confond tas min et tas max. | LING-07, TEST-09, SCEP-05, ARCH-11 | Un message dédié, « écrivez `ahu` : un ahunui a le type ahu », et une phrase dans *Types* : l'annotation `ahu` ne fixe pas l'ordre. | S | les quatre auteurs |
| L5 | **`fmt --ecrire` efface les commentaires sans signal au moment d'écrire** (l'aide le dit déjà). | TEST-02 | Écrire comme aujourd'hui, avec le code 0, plus `upea : N commentaire(s) perdu(s)` sur stderr (le lexer compte les commentaires). | S | casseur, compilateur, architecte, sceptique |
| L6 | **Bac à sable et CLI** : enfant orphelin quand le serveur est tué ; `MemoryError` sur de petits objets → `EnfantEnPanne` illisible ; une demi-paire de substitution produit `JSONDecodeError` hors contrat ; `-o` vers un dossier absent, tube fermé, dossier passé à `run`. | TEST-04, TEST-05, TEST-06, TEST-10 | Limite de temps CPU dans le *job object* (et `RLIMIT_CPU`) ; tampon libéré sur `MemoryError`, ou traduction côté parent ; `ensure_ascii=True` et `json.loads` gardé ; `OSError` attrapée autour des écritures, tube fermé traité comme une fin silencieuse, `is_dir()`. | S | casseur ; graphes (a rencontré TEST-10) |
| L7 | **Spécification à préciser** (écarts mineurs ou silences) | ARCH-01, ARCH-05, ARCH-06+GRAPH-10, ARCH-07+GRAPH-11, ARCH-09, GRAPH-02, GRAPH-04, GRAPH-05, GRAPH-07, GRAPH-09, LING-03, LING-09, ordre des textes (renforcement de TEST-08) | ARCH-01 : « un opérande de type inconnu suit Python », et traduire les erreurs de `%` sur un texte. ARCH-05 : refuser `eiaha` en opérande (rien ne casse : grep vide) ou corriger l'EBNF, et tester `1 + eiaha hape`. ARCH-06 : le `?` des prédéfinies couvre « T ou aore » et « numera ou tuhaa », et une annotation fausse n'est pas vérifiée. ARCH-07 : la valeur est évaluée avant la cible ; les structures sont partagées ; `a + []` ne copie que les listes. ARCH-09 : nœud sur un `tumu`, clé sur un arbre ordonné. GRAPH-02 : convention typable « `tumu` sans enfants = vide », que le prélude compte. GRAPH-04 : `cycle(upea { 1 <-> 2 })` vaut `tia` (l'exemple vitrine `iles` aussi). GRAPH-05 : idiome des nœuds entiers `0..n-1`. GRAPH-07 : désigner un nœud par son chemin d'indices, et reformuler `:265`. GRAPH-09 : l'erreur de `floyd_warshall`. LING-03 : la règle de langue des noms. LING-09 : les noms réservés, dans `PIEGES_DE_PYTHON`. `:291` : « ordre des caractères Unicode », pas « alphabétique » (`"Zebre" < "abeille"` vaut `tia`). | S chacun | auteurs + renforcements (voir §8) |
| L8 | **Chaîne `ast` et formateur** : `executer_arbre` perd la ligne d'une expression multiligne, alors qu'il est le seul chemin qui remplit le critère de l'étape 11 ; `--backend formateur --sourcemap` donne une carte vide ; `transpile --backend formateur` refuse ce que `fmt` accepte. | COMP-07, COMP-08 | Une carte construite sur tous les nœuds qui ont un `lineno` ; `e.depuis(...)` dans `_Ecrivain`, ou refus de `--sourcemap` ; le formateur sans analyse dans `transpiler`. Voir Q6. | S | compilateur, sceptique |
| L9 | **Rendu** : `PLAN.md` et `PLAN_MCP.md` sont périmés et rédigés à la 2e personne ; `NOTES.md:59` cite `execution.py` ; le README annonce une CI qui n'a jamais tourné (aucun remote). | SCEP-06, SCEP-07 | Une ligne d'en-tête « document de travail, état au commit X » ou un dossier `journal/` ; corriger `NOTES.md:59` ; pousser une fois et citer l'exécution verte, ou écrire « configuré, non encore exécuté ». | S | sceptique |
| L10 | **Couverture du test différentiel** : ni fonctions, ni affectations, ni `tamau`, ni `hoi`. | COMP-09 | Étendre `generateurs.instructions()`, et ajouter `1 + eiaha hape` et `(a < b) == tia`. | S à M | compilateur |

### 2.3 Suggestions conservées

- **SCEP-04, gel du périmètre.** Plus aucune fonctionnalité nouvelle, avec trois exceptions : (a) les bugs avérés (S) ; (b) `amui(g, v)` ; (c) `tatara(g, a, b)`, en dernier. Les solutions M ou L qui ne corrigent pas un bug sont refusées. *Accepté par graphes au tour 3.*
- **GRAPH-06, retrait d'arc** `tatara(g, a, b)` : une suggestion, faute d'exemple qui en ait besoin (Kahn s'écrit par les degrés, `06_tahua.upea:13-45`).
- **LING-05**, sens de `ahani`, `anei`, `eiaha` et `ma`, et **LING-06**, `ahu` et le marae : [HYPOTHÈSE], à vérifier avant tout renommage (voir §7).

---

## 3. Désaccords persistants

Aucune contestation ne s'est conclue par un désaccord persistant. Il reste trois points sur lesquels le conseil n'a **pas** convergé entièrement. Je ne les tranche pas.

**D1. Récursion croisée (ARCH-10 contre SCEP-08).**
- Architecte : la cible le permet. Une première passe déclare les signatures des `ohipa` globales (M), à la manière de `forward` en Pascal.
- Sceptique, avec le compilateur, l'expert graphes et le casseur : ne rien changer ; c'est une limite documentée (`specification.md:516`), conforme à l'étape 7 du cours ; au plus, un message « la récursion croisée n'est pas permise » (S).
- L'architecte a lui-même écrit qu'il « accepte de laisser la limite en l'état au nom du gel ». Le désaccord est faible.
- **Pour trancher** : savoir si l'enseignant attend la récursion croisée (Q12).

**D2. Où relever la limite de récursion (mise en œuvre de M1).** Ce point n'a pas fait l'objet d'une contestation formelle.
- Compilateur : dans le texte du prélude, un seul endroit qui couvre `run`, le REPL et le fichier autonome.
- Graphes, casseur et sceptique : seulement autour de l'`exec` du code utilisateur, puis la remettre, pour que le parser et l'analyse ne descendent pas plus profond avant d'échouer.
- **Pour trancher** : si le lot L1 (limite de profondeur dans l'analyse) est fait, l'argument des seconds tombe. Il suffit d'un test : relever la limite globalement, puis vérifier que les programmes très imbriqués de TEST-03 donnent toujours une erreur de compilation propre.

**D3. Gravité des doublons de M2.** Le casseur classe TEST-01 majeur, l'architecte et le compilateur classent ARCH-04 et COMP-06 mineurs. Aucun ne l'a contesté. La solution, elle, fait consensus.

---

## 4. Quick wins (coût S)

Ordre suggéré : livrables à faible coût et fort effet sur la grille, puis bugs, puis documentation.

1. **SCEP-03** : présenter la spécification à l'enseignant (M9).
2. **SCEP-01** : une session MCP réelle, avec sa trace et son test (M7).
3. **SCEP-02** : la table de correspondance MCP dans `NOTES.md` (M8).
4. **M1, M2** : `setrecursionlimit` et `set_int_max_str_digits(0)`, quelques lignes chacun.
5. **M3, M4** : `_couvrant` avec tous les nœuds, et `amui(g, v)`.
6. **M5, M6** : REPL (une source map par saisie, Ctrl-C).
7. **L1** : limite de profondeur, filet, atelier. Cela rend vraie la phrase du README (SCEP-09).
8. **L2** : notation exponentielle et garde `isfinite`, ensemble.
9. **L3, L4, L5** : graphie tahitienne, `ahunui`, avertissement de `fmt`.
10. **L6** : bac à sable et CLI.
11. **L7, L9** : documentation et rendu.
12. **L8**, puis **GRAPH-06 (c)** `tatara(g, a, b)`.

---

## 5. Chantiers structurels (coût M ou L)

**Le conseil n'en recommande aucun.** Tous les problèmes retenus ont une solution S. Les options M ou L évoquées pendant le débat ont été écartées ou gelées, au nom de SCEP-04 et de la proportionnalité. Si le temps le permet après le §4, voici l'ordre suggéré pour celles qui restent sur la table :

1. **COMP-09** : élargir le test différentiel (S à M). C'est le seul qui renforce la grille, au titre des tests.
2. **ARCH-10** : récursion croisée (M), seulement si l'enseignant l'attend (D1).
3. **ARCH-11** : un vrai type `ahunui` (M), non recommandé.
4. **ARCH-06 / GRAPH-10** : un type « nombre » (M ou plus), non recommandé.

---

## 6. Propositions rejetées pendant le débat (n'y revenez pas)

| Proposition | Origine | Pourquoi elle est rejetée | Qui l'a fait tomber |
|---|---|---|---|
| Parenthèses minimales dans le backend texte | COMP-04 | Le cours **prescrit** le tout-parenthésé (`08_generation.md:55`) et fait du contraste avec `ast.unparse` la démonstration de l'étape 11 (`11_module_ast.md:80`, `test_extension_11_ast.py:47`). Une règle fondée sur la seule précédence change le sens de `(1 < 2) == tia` et casse `1 + eiaha hape`. *Le casseur la cite encore « en option » dans sa fiche : c'est un résidu, son auteur l'a retirée.* | sceptique, graphes |
| `_fois` / `_reste` dans le prélude | ARCH-01 (M) | Ils réintroduisent la limite de 200 imbrications sur les deux backends, coûtent 5,7 à 11 fois plus cher par opération et cassent les textes figés et le test différentiel. | casseur, sceptique, compilateur |
| N'envelopper que les opérandes de type `?` | casseur, variante d'ARCH-01 | `Analyse` ne transmet aucun type d'expression au générateur (`semantique.py:85-93`) ; annoter chaque nœud coûterait M. | architecte (vérifié par le casseur) |
| `decimal_upea` dans le prélude | ARCH-03, v1 | Il donne `Infinity.0` et `NaN.0`, 303 caractères pour `1e300`, et deux affichages pour une même valeur (contre `:299`). | compilateur |
| Refuser `fmt --ecrire` si le fichier a des commentaires, ou exiger `--force` | TEST-02, v1 ; architecte | Les 10 exemples sur 10 sont commentés ; l'étape 10 du cours exige l'écriture en place ; le cours lui-même « avertit ». | compilateur, sceptique, architecte |
| Filet seul autour de `compile()`, en erreur d'exécution | TEST-03, v1 | `check` et `verifier` resteraient en désaccord avec `run`, et le code 3 serait faux pour un programme jamais exécuté. | compilateur |
| Normaliser en NFC **tout** le source | LING-08 et TEST-08, v1 | Cela change le sens des textes : `roa`, `==` et `tataitahi` sur `"tāne"` en NFD passeraient de `5 4 hape` à `4 4 tia`. | casseur |
| `ahunui` synonyme de `ahu` dans les annotations | SCEP-05, TEST-09 | L'annotation mentirait : `h: ahunui` accepterait un tas min (`semantique.py:660`). | architecte |
| `foret(g)` | GRAPH-04 | Le nom reproduit l'ambiguïté (la « forêt » de `kruskal` a `cycle == tia`), réserve un mot et ajoute une fonctionnalité. | linguiste, architecte, sceptique |
| `rang(g, v)` | GRAPH-05 | Le rang se décale après `tatara` (`C` récupère la distance de `B`) ; collision avec l'union-find et les variables d'élèves ; `indice` casserait l'exemple 06. | casseur, linguiste |
| `meme(a, b)` | GRAPH-07 | « même » a déjà deux sens contraires dans la spécification (`:256`, `:265`) ; le chemin d'indices suffit ; gel du périmètre. | linguiste, sceptique |
| `kape(x)`, copie | GRAPH-11 | Gelée ; `amui(g, v)` rend la copie faite à la main fidèle. | sceptique |
| `aore` comme enfant, `tumu[T] \| aore` | GRAPH-02 (M) | Il n'y a pas d'union dans le système de types (`typage.py:48`) ; cela casse l'idiome de l'exemple 04 ; le coût réel est L. | architecte, sceptique |
| Refuser U+02BB dans **tous** les identifiants | option d'ARCH-08 | Cela interdirait des noms tahitiens corrects (`ʻuru`) ; le refus ciblé de LING-01 suffit. *Reste ouvert pour Thomas (Q1).* | linguiste, casseur |
| Renommer les prédéfinies françaises ou anglaises | LING-03 | `largeur` apparaît 42 fois et `profondeur` 47 fois ; écrire la règle suffit. | linguiste (auto-limitation) |

---

## 7. Questions pour Thomas

**Langue (le linguiste n'a consulté aucune source : tout sens est une [HYPOTHÈSE])**
- Q1. Une forme correcte comme `tuʻu` : faut-il la **refuser avec un conseil** (préférence du linguiste, de l'architecte et du casseur) ou l'**accepter comme synonyme** ? Les identifiants avec ʻeta (`tuu ʻupeʻa = …`, acceptés aujourd'hui sans être documentés) doivent-ils rester permis ?
- Q2. D'où viennent les sens de `specification.md:46-75` et `:337-352` ? Un dictionnaire comme le Fare Vānaʻa, un autre lexique, ou des souvenirs ? Les citer lèverait la plupart des [HYPOTHÈSE].
- Q3. `anei` : faut-il écrire « ʻaneʻi » ou « ānei » ? Est-ce un « ou », ou une particule interrogative ?
- Q4. Pour « non », `eiaha` (prohibitif ?) ou `aita` (descriptif ?) ? `ahani` est-il un « si » réel ? `mā` veut-il dire « et » ?
- Q5. `ahu` évoque-t-il fortement la plateforme du marae ? « iriti : le ahu est vide » est-il acceptable ?
- Q6. `taae` : le second mot porte-t-il un macron (« ʻē ») ? `rau` veut-il dire « feuille » (ou « rauere ») ? `ea` sans ʻeta se confond-il avec un mot courant ?
- Q7. La relecture par un tahitophone annoncée dans `NOTES.md` est-elle prévue ? Les tableaux de `round-1/upea-linguiste.md` (environ 45 mots) peuvent lui servir de support.
- Q8. Faut-il normaliser en NFC aussi les **textes** ? Ce serait un changement de sémantique, à décider puis à écrire.

**Cours et rendu**
- Q9. Y a-t-il une soutenance orale ? Avec 8 357 lignes, il faudra pouvoir expliquer le rouge-noir penché, le *job object* ou Edmonds-Karp (SCEP-04).
- Q10. Quelle est la règle du cours sur l'usage d'un assistant IA ? `PLAN.md` et `PLAN_MCP.md` le montrent clairement ; s'il faut le déclarer, mieux vaut l'écrire soi-même dans `NOTES.md`.
- Q11. L'adaptation du projet MCP (outils, nom du paquet, sélecteurs) a-t-elle été convenue avec l'enseignant ? Quelle est la date de présentation de la spécification ? Faut-il attendre son retour avant de corriger le vocabulaire ?
- Q12. La récursion croisée est-elle attendue (D1) ? Le REPL fait-il partie de ce qui est évalué (priorité de M5 et M6) ?

**Choix techniques**
- Q13. Quelle profondeur de récursion visez-vous pour M1 : 20 000 (un ABR dégénéré de 10 000 clés) ou plus ? Où la relever (D2) ?
- Q14. `run --backend ast` doit-il exécuter l'arbre directement (`executer_arbre`, ce que dit l'étape 11), ou le passage par `ast.unparse` est-il voulu (L8) ?
- Q15. La « précision illimitée » doit-elle valoir aussi dans le fichier produit par `transpile` (M2) ?
- Q16. Le serveur MCP est-il lancé par Claude Desktop, et celui-ci tue-t-il le processus brutalement (importance de TEST-04) ?
- Q17. Les prédéfinies réservent des mots courants (`distance`, `largeur`, `cycle`, `dot`) : est-ce voulu pour un public francophone, ou faut-il seulement le documenter (LING-09) ?

---

## 8. Traçabilité

| Point du rapport | Constats d'origine (phase 1 → phase 2) |
|---|---|
| M1 | GRAPH-01, TEST-07 (fusionné, relevé à majeur) ; renforcements du compilateur et du casseur |
| M2 | TEST-01, ARCH-04, COMP-06, partie littéral de COMP-05 ; renforcements du sceptique, du compilateur et du casseur |
| M3 | GRAPH-03 |
| M4 | GRAPH-06 (partie nœud isolé), ARCH-02, GRAPH-11 ; contestation C5 du sceptique et réplique d'acceptation |
| M5 | COMP-01 ; renforcement du casseur |
| M6 | COMP-02 ; renforcement du sceptique |
| M7 | SCEP-01 |
| M8 | SCEP-02 ; renforcement du casseur |
| M9 | SCEP-03 ; renforcement du linguiste |
| L1 | COMP-03, COMP-04 (amendé), TEST-03 (amendé), COMP-10, SCEP-09 ; renforcements de l'architecte et du sceptique |
| L2 | ARCH-03 (amendé, accepté par le compilateur), COMP-05, GRAPH-08, TEST-11 ; renforcements de l'architecte, de l'expert graphes et du casseur |
| L3 | LING-01 (majeur → mineur), ARCH-08, TEST-08 (amendé), LING-08 (amendé), LING-02, LING-04 |
| L4 | LING-07, TEST-09 (amendé), SCEP-05 (amendé), ARCH-11 |
| L5 | TEST-02 (majeur → mineur, amendé) |
| L6 | TEST-04, TEST-05, TEST-06, TEST-10 ; renforcement de l'expert graphes |
| L7 | ARCH-01 (amendé), ARCH-05, ARCH-06 (élargi) + GRAPH-10, ARCH-07 + GRAPH-11, ARCH-09, GRAPH-02 (amendé), GRAPH-04 (amendé), GRAPH-05 (amendé), GRAPH-07 (amendé), GRAPH-09, LING-03, LING-09, renforcement du linguiste sur TEST-08 (ordre des textes) |
| L8 | COMP-07 (renforcé par le sceptique), COMP-08 |
| L9 | SCEP-06, SCEP-07 |
| L10 | COMP-09 |
| Suggestions §2.3 | SCEP-04 (amendé), GRAPH-06 (partie retrait d'arc), LING-05, LING-06 |
| D1 | ARCH-10, SCEP-08 |
| D2 | renforcement du compilateur (prélude) contre TEST-07, GRAPH-01 et conflit 5 du sceptique |
| D3 | TEST-01, ARCH-04, COMP-06 |
| §6 | voir la colonne « Origine » ; le détail est dans `round-2/debat.md` |

Constats sans objection ni changement : ARCH-05, ARCH-07, ARCH-09, GRAPH-09, TEST-04, TEST-05, TEST-06, TEST-10, TEST-11, COMP-01, COMP-02, COMP-05, COMP-07, COMP-08, COMP-09, LING-02 à LING-07, LING-09, SCEP-01 à SCEP-03, SCEP-06 à SCEP-09. Aucun constat n'a été retiré en entier : 15 propositions de solution ont été rejetées (§6), et 8 gravités ont été revues, 7 à la baisse (LING-01, TEST-02, ARCH-01, ARCH-02, GRAPH-02, GRAPH-04, GRAPH-06 pour le retrait d'arc) et 1 à la hausse (TEST-07). GRAPH-06 a été confirmé majeur pour le nœud isolé.
