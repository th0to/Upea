# Étape 3 — corriger les bugs retenus par le conseil : plan

État de départ : commit `ce53700`, branche `master`. Ce plan attend ta validation :
rien n'est modifié dans le code tant que tu n'as pas répondu aux questions du §4.

## 0. État des lieux (phase 0)

- `git status --short` : vide.
- `uv run mypy projet` : `Success: no issues found in 63 source files`.
- `uv run ruff check projet` : `All checks passed!`.
- `uv run pytest projet` :
  - 1re passe : `1 failed, 1109 passed, 4 skipped in 118.42s`. L'échec est
    `test_extension_18_bac_a_sable.py::test_un_exemple_donne_sa_sortie_attendue`,
    sur `DelaiDepasse : délai de 5 s dépassé`.
  - Ce test, relancé seul trois fois : `18 passed` à chaque fois (16 à 18 s).
  - 2e passe complète : `1110 passed, 4 skipped in 119.82s`.
  - Conclusion : c'est un échec intermittent. C'est le premier sous-processus de
    la session, lancé à froid depuis un dossier OneDrive : le délai de 5 s compte
    le démarrage de Python. Ce n'est pas une régression, et je n'y touche pas
    (hors périmètre). Je le signale parce qu'il peut se reproduire pendant la
    phase 2 : dans ce cas, je relance la suite avant de conclure.

## 1. Reproductions (phase 1)

### Comment j'ai reproduit

- Commandes lancées depuis `projet/`, avec
  `UV=C:\Users\thoma\AppData\Roaming\Python\Python311\Scripts\uv.exe`.
- Les programmes sont dans le dossier temporaire de la session : `r/*.upea`.
- Le pilote `bac.py` appelle `upea.bac_a_sable.executer(source, delai=20)` et
  affiche le statut, la sortie et le rapport. **Tout ce qui s'exécute passe par
  lui**, sauf les cas qui ne lancent aucun programme (`check`, `fmt`,
  `transpile`) et les essais de la CLI elle-même (L6, M6 ; voir la remarque de
  M6).
- Pour mesurer M1 et M2 sans toucher au code, `bac_simule.py` remplace
  l'enfant du bac à sable par un script qui appelle
  `sys.setrecursionlimit(20_000)` et `sys.set_int_max_str_digits(0)`, puis
  `bac_a_sable._enfant()`. Le *job object* et les plafonds restent les mêmes.
- Les accents abîmés dans les sorties brutes (`r�cursion`) viennent de la
  console. Je les ai rétablis ci-dessous.

### L1 — Imbrication extrême : **confirmé, et nuancé deux fois**

| Programme | `check` | exécution (bac à sable) |
|---|---|---|
| `somme201` : `tuu x = 1;` puis `faaite x + x + … ;` (201 termes) | `aucune erreur`, code 0 | `EnfantEnPanne` : `SyntaxError: too many nested parentheses` (`compilateur.py:147`) |
| `bloc100` : 100 `ahani tia {` imbriqués | `aucune erreur`, code 0 | `EnfantEnPanne` : `IndentationError` |
| `p500` : `faaite ((…(1)…));` (500 parenthèses) | traceback, `RecursionError` (parser), code 1 | `EnfantEnPanne` (`parser.py:493`, `_groupe`) |
| `somme1000` : `faaite 1 + … + 1;` (1 000 termes) | traceback, `RecursionError` (`semantique.py:639`), code 1 | `EnfantEnPanne` |

- `run somme201.upea` : `Traceback (most recent call last): File "<frozen runpy>"…`.
- `atelier.verifier` : sur `somme201`, `valide=True, aucune erreur` ; sur `p500`,
  l'exception `RecursionError` sort de l'atelier.
- REPL : `tuu x = 1;`, puis la somme de 201 termes, puis `faaite x;`. Le REPL
  affiche `SyntaxError: too many nested parentheses` et meurt : `faaite x` ne
  s'exécute jamais.
- `--backend ast` passe `somme201` (sortie `201`) : les deux backends divergent.

**Nuance 1 : `fmt` n'est pas protégé non plus.** `fmt somme1000.upea` et
`fmt p500.upea` donnent `RecursionError` en traceback. Le formateur ne passe pas
par l'analyse sémantique, où le conseil plaçait la limite.

**Nuance 2 : la limite « environ 150 niveaux d'expression » ne suffit pas pour
toutes les constructions.** Seuils mesurés (`seuils.py`, `compilateur.executer`,
limite de récursion par défaut), en nombre d'imbrications :

| Construction | dernier succès (python / ast) | premier échec, cause |
|---|---|---|
| `1 + 1 + …` | 200 / 328 | 201 `SyntaxError` / 329 `RecursionError` |
| `roa([roa([…])])` | 99 paires (198 nœuds) | 100 paires, `SyntaxError` |
| `[[[…]]]` | 199 | 200, `SyntaxError` |
| `-(-(…))` | 199 / 245 | 200 / 246 |
| `tumu(1, tumu(1, …))` | 197 | 198 |
| `roa([upea { roa([upea { … }]) }])` | **39 niveaux** | 40, `SyntaxError` |
| `roa(aifaito [roa(aifaito [ … ])])` | **65 niveaux** | 66, `SyntaxError` |
| blocs `ahani` (global / dans une `ohipa`) | 99 / 98 | 100 / 99, `IndentationError` |
| boucles `tataitahi` ou `tamau` imbriquées | **21** | **22**, `SyntaxError: too many statically nested blocks` |

- Un littéral `upea` ouvre trois parenthèses dans le Python généré
  (`_graphe([(a, b, p, False)])`), et un arbre ordonné deux (`_aifaito([…])`).
  Une limite de 150 **nœuds** ne protège donc pas `compile()` : 40 niveaux de
  `roa([upea {…}])` font 120 nœuds et échouent déjà.
- **Trouvaille hors rapport, même bug** : 22 boucles imbriquées suffisent.
  `check boucles22.upea` répond `aucune erreur` (code 0), et l'exécution donne
  `EnfantEnPanne` avec le traceback. CPython limite à environ 20 les boucles
  imbriquées dans un même bloc de code.
- **Pire cas combiné** (`combine.py`, limite de récursion de 1 000, celle de
  l'enfant du bac à sable au moment de la compilation) : une `ohipa` avec 90
  blocs imbriqués et une expression de profondeur 150 (avec les poids : `upea` = 3,
  arbre ordonné = 2). L'analyse, les deux générateurs, `compile()` et le
  formateur passent pour les six formes essayées. À 190, quatre formes sur six
  échouent (`RecursionError`, `MemoryError`). **90 blocs et 150 niveaux pondérés
  sont donc sûrs, et il n'y a pas de marge pour monter.**

### M1 — Récursion limitée à environ 990 niveaux : **confirmé**

```
bac.py r/profond.upea       # somme(n) récursive : faaite somme(991); faaite somme(1200);
== profond.upea : erreur_execution code 3
sortie : 491536
rapport : programme.upea:3 : erreur d'exécution : récursion trop profonde
        hoi n + somme(n - 1);
bac.py r/abr_peigne.upea    # ABR écrit à la main, rempli dans l'ordre 1..1200
rapport : programme.upea:3 : erreur d'exécution : récursion trop profonde
```

Simulation avec la limite à 20 000 (`bac_simule.py`) :

```
profond15000.upea : succes   sortie : 112507500
abr_peigne.upea   : succes   sortie : 1200
tumu_chaine.upea  : succes   sortie : 14999 14999     (hauteur récursive à la main, puis teitei)
infinie.upea      : erreur_execution, « récursion trop profonde », 0,63 s
```

**Nuance : les listes imbriquées ne sont pas des appels de fonction.** Seuils
mesurés par dichotomie dans le bac à sable (`seuil_listes.py`) :

| | aujourd'hui (1 000) | avec 20 000 |
|---|---|---|
| `parau` d'une liste imbriquée n fois | 246 réussit, 247 échoue | 997 réussit, 998 échoue |
| `l == m`, deux listes imbriquées n fois | 2 991 / 2 992 | 2 994 / 2 995 |

- Ces deux erreurs viennent de la pile C de CPython, qui ne dépend pas de
  `setrecursionlimit`.
- Elles s'affichent aujourd'hui « récursion trop profonde ». Le message proposé
  par le conseil, « (plus de N appels imbriqués) », serait **faux** pour elles
  (voir Q5).
- `specification.md:525` annonce que leur affichage s'arrête « sur plus d'un
  millier de niveaux ». C'est faux aujourd'hui (247), et presque juste après M1
  (998). Je propose de ne pas y toucher (Q11).

### M2 — Entiers de plus de 4 300 chiffres : **confirmé**

```
bac.py r/factorielle.upea   (faaite roa(parau(factorielle(2000)));)
rapport : programme.upea:6 : erreur d'exécution : erreur inattendue (ValueError : Exceeds
          the limit (4300 digits) for integer string conversion; use sys.set_int_max_str_digits() …)
bac.py r/numera5000.upea    (numera("111…1"), 5 000 chiffres)   → même ValueError, code 3
bac.py r/litteral5000.upea  (un littéral de 5 000 chiffres)     → EnfantEnPanne, traceback du parser
transpile r/litteral5000.upea                                   → ValueError: Exceeds the limit…
atelier.verifier(littéral de 5 000 chiffres)                     → l'exception ValueError sort
```

Simulation avec `set_int_max_str_digits(0)` : `factorielle.upea : succes`,
sortie `5736` (le nombre de chiffres de 2000!).

### M3 — `kruskal` et `prim` perdent les nœuds isolés : **confirmé**

```
tuu g = upea { "A" <-> "B" : 2, "B" <-> "C" : 1, "D", "E" -> "E" };
faaite roa(g), motu(g);                 → 5 ["A", "B", "C", "D", "E"]
faaite roa(kruskal(g)), kruskal(g);     → 3 upea { "B" <-> "C", "B" <-> "A" : 2 }
faaite roa(prim(g)), prim(g);           → 3 upea { "A" <-> "B" : 2, "B" <-> "C" }
faaite composantes(g);                  → [["A", "B", "C"], ["D"], ["E"]]
faaite composantes(kruskal(g));         → [["B", "C", "A"]]
```

Le test `test_extension_15_algorithmes.py:155-157` compare bien `k` à lui-même
(`aretes == len(k._arcs) - len(_composantes(k))`).

### M4 — Pas d'ajout d'un nœud isolé : **confirmé**

```
liste_noeuds.upea (nœuds ["a","b","c","d"], arêtes [["a","b"]] ajoutées par taati)
sortie : composantes : 1 [["a", "b"]]          (3 attendues)
amui_noeud.upea : amui(g, "C");
rapport : programme.upea:2:6 : erreur de type : amui : tapura ou arbre ordonné attendu, upea[parau] reçu
```

### M5 — REPL : mauvaise ligne pour une erreur dans une fonction antérieure : **confirmé**

```
$UV run python -m upea repl < r/m5.txt       (le programme de COMP-01)
dans f
<repl>:7 : erreur d'exécution : indice hors limites
        faaite "y";
bac.py r/m5.upea (le même source, exécuté d'un bloc)
rapport : programme.upea:3 : erreur d'exécution : indice hors limites
        hoi l[3];
```

La variante du casseur (`div(1, 0)`) donne aussi `<repl>:7 … faaite "y";`.

### M6 — Ctrl-C : **confirmé**

Interruption simulée par `threading.Timer(0.8, _thread.interrupt_main)` dans le
processus de `cli.main`, sur une boucle **finie** de 30 millions de tours, sous
`timeout 60`. Même si l'interruption échouait, rien ne pourrait tourner
indéfiniment. (Ce n'est pas un test de délai : il n'y a pas d'autre moyen
d'envoyer Ctrl-C.)

```
REPL (tuu x = 42; … la boucle … ; faaite x;)
  File "<upea>", line 2, in <module>
KeyboardInterrupt                      (la session est perdue, faaite x n'est jamais exécuté)
run long.upea
  File "<upea>", line 2628, in <module>
KeyboardInterrupt
```

### L2 — Décimaux : **confirmé**

```
expo.upea : faaite [10000000000000000.0], parau(upea { 0.00001 -> 1 }), 0.00001;
            tuu h = upea { 1e-05 -> 1 };
rapport : programme.upea:2:16 : erreur lexicale : nombre mal formé : '1e'
inf_lit.upea (faaite [1 suivi de 400 zéros .0];)
  backend python : erreur inattendue (NameError : name 'inf' is not defined)
  backend ast    : succes, sortie [inf]
  fmt            : faaite [Infinity.0];
nan.upea (x = 1.5 multiplié 400 fois par 10.0, n = x - x)
  sortie : inf nan
           4 upea { 1.5 -> 2.5, nan -> 1 }
           3 hape                  (amui(aifaito [5.0, 3.0, 8.0], n) : roa reste 3, la clé est perdue)
  rapport : programme.upea:13 : erreur d'exécution : erreur inattendue (KeyError : 'B')   (bellman_ford, poids NaN)
nan2.upea (taati(h, x - x, 1) deux fois) → 3 upea { nan -> 1, nan -> 1 }   (deux nœuds NaN)
```

Le lexer actuel, sur les cas du conseil :

```
'1..5' → ENTIER 1, POINT_POINT, ENTIER 5 ;  '1..=5' → ENTIER, POINT_POINT_EGAL, ENTIER
't.hotu' → IDENT, POINT, IDENT ;  '0..e5' → ENTIER 0, POINT_POINT, IDENT e5
'1e5', '1.5e-07', '1e', '1e+', '1E3' → erreur « nombre mal formé »
```

### L4 — `ahunui` en annotation : **confirmé**

```
ahunui.upea : tuu z: ahunui = ahunui [1];
rapport : programme.upea:1:8 : erreur de syntaxe : type attendu, trouvé 'ahunui'
```

### L5 — `fmt --ecrire` efface les commentaires sans signal : **confirmé**

```
commente_copie.upea : « // Calcul du total », « tuu total = 0; /* en francs */ », « faaite total; »
fmt commente_copie.upea --ecrire   → rien sur stderr, code 0 ; le fichier devient :
tuu total = 0;
faaite total;
```

### L6 — Bac à sable et CLI : **confirmé, avec deux nuances**

**TEST-04, enfant orphelin (confirmé).** `orphelin.py` lance un parent qui
appelle `executer("tamau tia { }", delai=60)`, relève tous ses descendants, tue
le parent, attend 3 s, puis tue tout le monde :

```
descendant 30704 : … b.executer('tamau tia { }', delai=60)
descendant 36424 : …\.venv\Scripts\python.exe -m upea.bac_a_sable     (lanceur du venv)
descendant 5524  : …cpython-3.12…\python.exe -m upea.bac_a_sable       (l'interpréteur de l'enfant)
3 s après : 36424 VIVANT, 5524 VIVANT        → tués à la main ensuite
```

Une remarque de méthode : un premier essai ne suivait que les enfants directs et
semblait infirmer le constat. Sous Windows, le `python.exe` d'un venv est un
lanceur qui crée lui-même l'interpréteur. Il faut suivre toute la descendance.

**TEST-05, `MemoryError` sur de petits objets (confirmé).**
`mem_graphe.upea` (`taati(g, i, i + 1)` sans fin) :
`PANNE EnfantEnPanne … object type name: MemoryError … lost sys.stderr`.

**TEST-06, demi-paire de substitution (confirmé).**
`executer('faaite "a\ud800b";')` et `executer('faaite 1; \ud800')` lèvent
`JSONDecodeError Expecting value: line 1 column 1 (char 0)`. `atelier.verifier`
répond normalement.

**TEST-10, CLI (confirmé, nuancé).**

```
transpile … -o r/nexiste/x.py    → traceback, FileNotFoundError, code 1
transpile … -o r                 → traceback, PermissionError, code 1           (un dossier)
fmt r/ro.upea --ecrire           → traceback, PermissionError, code 1           (fichier en lecture seule : cas en plus)
run r/grosse_sortie.upea | head -1
  → 0, puis un traceback complet : OSError: [Errno 22] Invalid argument … code 120
run r                            → upea : impossible de lire … (Permission denied), code 1
```

- **Nuance 1** : sous Windows, un tube fermé lève `OSError` (errno 22), pas
  `BrokenPipeError`. Le traceback sort **même quand stderr est redirigé**, et le
  code est 120, pas 3. La correction doit reconnaître les deux formes.
- **Nuance 2** : `run` sur un dossier ne donne pas de traceback. Le message est
  seulement trompeur (« Permission denied »).

## 2. Ce que je change par rapport aux solutions du conseil

Les points ci-dessous découlent des reproductions. Chacun est soumis à ta
décision au §4.

1. **L1 : les limites vont dans le parser, pas dans l'analyse sémantique** (Q2).
   - `fmt`, `:arbre` et `atelier.formater` ne passent pas par l'analyse : ils
     resteraient sans protection.
   - Surtout, après M1, la limite de récursion de Python ne vaut pas la même
     chose partout :
     - 20 000 dans la CLI, le REPL et le serveur MCP ;
     - 1 000 dans l'enfant du bac à sable au moment de la compilation.

     Si le parser comptait sur `RecursionError`, `p500` serait accepté par
     `check` mais refusé dans le bac à sable : c'est exactement le désaccord que
     L1 doit supprimer.
   - Des compteurs explicites donnent le même verdict quelle que soit la limite
     de Python. Le `RecursionError` du parser devient malgré tout une
     `ErreurSyntaxe`, comme seconde barrière.
2. **L1 : la profondeur d'une expression est pondérée** : un littéral `upea`
   compte 3, un arbre ordonné 2 et toute autre expression 1. Ce sont les
   parenthèses que le Python généré ouvre (Q3).
3. **L1 : 20 boucles imbriquées au plus**, en plus des 90 blocs (Q4).
4. **L1 : l'atelier est protégé par la façade.** `compilateur.compiler`,
   `transpiler` et `mettre_en_forme` ne laissent plus sortir `RecursionError`.
   Je ne mets pas d'`except ValueError` dans l'atelier : après M2, plus rien ne
   lève `ValueError`, et un `except` aussi large masquerait de vrais bugs.
5. **M1 : deux messages** (Q5) :
   - « récursion trop profonde (plus de 20 000 appels imbriqués) » quand la
     pile contient des milliers d'appels du programme ;
   - « récursion trop profonde » inchangé pour les listes imbriquées.
6. **M3 : les nœuds isolés sont ajoutés après les arêtes de l'arbre** (Q7).
   Les sorties des graphes connexes, dont l'exemple 08, ne changent pas.

## 3. Les lots, dans l'ordre

Ordre retenu : **L1 → M1 → M2 → M3 → M4 → L2 → L4 → L5 → M5 → M6 → L6**.

Pour chaque lot :
- le test d'abord, en vérifiant qu'il échoue ;
- puis la correction ;
- puis `pytest`, `mypy` et `ruff` au vert ;
- puis la documentation ;
- enfin un commit, et un résumé en trois lignes.

Les tests qui exécutent un programme lourd, en mémoire ou en durée, passent par
`bac_a_sable.executer`.

### Lot 1 — L1 : imbrication extrême

**Fichiers** : `parser.py`, `compilateur.py`, `repl.py`, `bac_a_sable.py`,
nouveau `tests/test_etape3_imbrication.py`, `specification.md`, `NOTES.md`.

**Approche**

1. Des **compteurs dans le parser** :
   - **blocs** `{ }` imbriqués, au plus **90**. Le corps d'une `ohipa` compte,
     comme dans le Python généré. Erreur sur le `{` fautif.
   - **boucles** `tamau` et `tataitahi` imbriquées dans une même fonction (ou au
     niveau global), au plus **20**. Erreur sur le mot-clé.
   - **appels de `Parser.expression`** imbriqués (parenthèses, opérateurs
     préfixes, opérandes de droite), au plus **150**. Erreur sur le jeton
     courant.

   Au premier dépassement, l'erreur est notée et l'analyse s'arrête (`_Abandon`).
   Sinon, la récupération d'erreurs ferait vingt fois le même signalement.
2. Après l'analyse syntaxique, un **parcours itératif** de l'arbre (pile
   explicite, sans récursion) calcule la profondeur pondérée de chaque
   expression. Une somme à plat est profonde dans l'arbre, mais pas dans le
   parser. La limite est de **150**. Les poids sont dans une table commentée qui
   renvoie aux formes émises par `generateur.py`.
3. Dans `parse`, `RecursionError` devient `ErreurSyntaxe` (seconde barrière).
4. **Filet autour de `compile()`** dans `executer_code` : `SyntaxError` et
   `RecursionError` deviennent une `ErreursMultiples` (compilation, code 1), à la
   ligne Upea si la source map la connaît. Le REPL et `_executer_ici` du bac à
   sable attrapent aussi les erreurs de compilation venues d'`executer_code`.
5. La façade (`compiler`, `transpiler`, `mettre_en_forme`) convertit un
   `RecursionError` résiduel en erreur de compilation. L'atelier en profite sans
   changer.

Messages proposés :

- `trop de blocs imbriqués (90 au plus)`
- `trop de boucles imbriquées (20 au plus)`
- `expression trop imbriquée (150 niveaux au plus)`
- `programme trop imbriqué pour être compilé` (les deux barrières)

**Tests** :
- les programmes de TEST-03 (`somme201`, 91 et 100 blocs, `p500`, `somme1000`)
  et 21 boucles imbriquées : erreur de syntaxe positionnée, sans traceback, dans
  chaque chemin :
  - `check` et `run` (code 1) ;
  - `fmt` ;
  - `atelier.verifier` et `atelier.formater` ;
  - le bac à sable (`erreur_compilation`) ;
  - le REPL, qui survit : la saisie suivante fonctionne.
- **À la limite exacte** : 90 blocs, 20 boucles et une expression de poids 150,
  pour chaque forme (somme, `ma`, appels, listes, `-`, `eiaha`, `tumu`, indices,
  `upea`, arbre ordonné) :
  - les deux backends compilent et donnent la même sortie ;
  - le pire cas combiné passe à la limite de récursion de 1 000 **et** de
    20 000.
- Le filet : `executer_code("(" * 300 + ")" * 300, …)` lève `ErreursMultiples`.
- La seconde barrière du parser : sous une limite de récursion abaissée
  temporairement, `parse` lève `ErreursMultiples` et non `RecursionError`.

**Risques**
- **Régression assumée** : des programmes acceptés aujourd'hui deviennent des
  erreurs de syntaxe. Ce sont les sommes à plat de 151 à 200 termes, les 151 à
  491 parenthèses superflues imbriquées et les `-(-(…))` de plus de 75 niveaux
  (Q3).
- La table des poids dépend des formes du générateur : les tests « à la limite
  exacte » la protègent.
- Le corpus (10 exemples) et les propriétés `hypothesis` doivent passer
  inchangés.

**`specification.md`** : une puce ajoutée à *Limites assumées*, après la ligne
523 :

> - Les imbrications ont les limites de Python : au plus 90 blocs `{ }` imbriqués (le corps d'une fonction compte), 20 boucles `tamau` ou `tataitahi` imbriquées, et 150 niveaux dans une expression (chaque parenthèse, opération, appel, liste ou indice en ajoute un ; un littéral `upea` en ajoute trois, un arbre ordonné deux). Au-delà, c'est une erreur de syntaxe, que `check` signale comme `run`.

**`NOTES.md`** :
- « **à faire valider par l'enseignant** » devient « **validée par l'enseignant
  le [DATE]** » (Q1) ;
- création de la section « Modifications depuis la validation de la
  spécification (le [DATE]) », avec la ligne de L1.

### Lot 2 — M1 : récursion à 20 000 niveaux

**Fichiers** : `execution/base.py` (prélude), `compilateur.py`,
`tests/test_etape_08_execution.py` (1 attente),
`tests/test_extension_18_bac_a_sable.py` (1 attente), le nouveau fichier de
tests de l'étape 3, `specification.md`, `NOTES.md`.

**Approche**
1. Dans le prélude (`execution/base.py`), une seule fois :
   `_PROFONDEUR_MAX = 20_000` et
   `_sys.setrecursionlimit(max(_sys.getrecursionlimit(), _PROFONDEUR_MAX))`.
   Cette ligne couvre `run`, le REPL (`nouvel_espace(avec_prelude=True)`) et le
   fichier autonome, prélude inclus ou externe.
2. `compilateur.py` importe `_PROFONDEUR_MAX` pour rédiger le message (Q6).
   Effet de bord voulu : tout processus qui compile charge le prélude, et a donc
   la même limite. Grâce aux compteurs de L1, le parser n'en dépend pas.
3. Message : si la pile du `RecursionError` contient plus de
   `_PROFONDEUR_MAX // 2` appels du programme (frames qui ont une ligne Upea),
   le message est « récursion trop profonde (plus de 20 000 appels imbriqués) ».
   Sinon, il reste « récursion trop profonde » (Q5).

**Tests**, d'abord en échec :
- par le bac à sable : `somme(15000)`, l'ABR en peigne de 1 200 clés et la
  hauteur récursive d'un `tumu` de 15 000 nœuds réussissent ;
- une récursion sans fin donne le nouveau message ;
- `parau` d'une liste imbriquée 2 000 fois garde « récursion trop profonde » ;
- le fichier produit par `transpile`, lancé par `python sortie.py` dans un
  sous-processus, réussit `somme(15000)`, avec le prélude inclus puis externe ;
- le REPL réussit `somme(15000)` ;
- **le test exigé après M1** : les programmes de TEST-03 donnent toujours une
  erreur de syntaxe propre, en processus (limite 20 000) et dans le bac à sable.

**Tests modifiés**, avec la raison écrite dans le commit :
- `test_etape_08_execution.py:212` et `test_extension_18_bac_a_sable.py:61`
  attendent le message exact de la récursion sans fin, qui gagne
  « (plus de 20 000 appels imbriqués) ».

**Risques**
- La pile C sous Windows : le conseil a mesuré jusqu'à 90 000 niveaux, et mes
  essais à 15 000 passent.
- Une récursion sans fin coûte 0,6 s au lieu de 0,4 s.
- La suite de tests tourne déjà à 20 000 dès qu'un test importe un module du
  prélude.

**`specification.md`**

1. Ligne 411, dans le tableau des erreurs d'exécution :
   - avant : `| récursion sans fin | récursion trop profonde |`
   - après : `| une fonction qui s'appelle plus de 20 000 fois en chaîne (récursion sans fin) | récursion trop profonde (plus de 20 000 appels imbriqués) |`
2. Une puce ajoutée à *Limites assumées*, avant la ligne 525 :

> - Une fonction peut s'appeler elle-même jusqu'à 20 000 fois en chaîne, de quoi parcourir récursivement un ABR dégénéré de 10 000 clés. Au-delà, l'exécution s'arrête sur « récursion trop profonde (plus de 20 000 appels imbriqués) ».

### Lot 3 — M2 : entiers sans limite de chiffres

**Fichiers** : `execution/base.py`, `parser.py`, tests, `NOTES.md`.

**Approche**
- `_sys.set_int_max_str_digits(0)` dans le prélude, à côté de la limite de M1.
  Le fichier autonome en profite.
- Le même appel en tête de `parser.py`, à côté de `_entier`. Le littéral est
  converti avant tout prélude, et le parser peut être importé seul (tests,
  atelier).

**Tests**, d'abord en échec :
- par le bac à sable : `faaite roa(parau(factorielle(2000)));` donne `5736` ;
  `numera` d'un texte de 5 000 chiffres réussit ;
- un littéral de 5 000 chiffres réussit dans le bac à sable, avec `transpile`
  et avec `atelier.verifier` ;
- le fichier autonome affiche `factorielle(2000)`.

**Risques** : aucun déni de service (mesures du conseil : un million de
chiffres en 0,81 s ; le source MCP est plafonné à 100 Kio).

**`specification.md`** : **aucun changement**. La ligne 189 (« précision
illimitée ») devient vraie.

### Lot 4 — M3 : `kruskal` et `prim` gardent les nœuds isolés

**Fichiers** : `execution/algorithmes_graphes.py`,
`tests/test_extension_15_algorithmes.py`, `NOTES.md`.

**Approche** : `_couvrant(graphe, aretes)` relie les arêtes comme aujourd'hui,
puis ajoute chaque nœud du graphe absent de l'arbre, dans l'ordre d'apparition
(Q7).

**Tests**, d'abord en échec :
- sur `couvrant.upea`, avec `kruskal` comme avec `prim` :
  - `roa` vaut 5 ;
  - `composantes(kruskal(g)) == composantes(g)` à l'ordre près ;
  - la forme compacte est
    `upea { "B" <-> "C", "B" <-> "A" : 2, "D", "E" }` pour `kruskal` (à
    confirmer à l'essai).
- Le test de `test_extension_15_algorithmes.py:155-157` est **complété, pas
  supprimé** : on garde l'assertion existante, et on ajoute
  `set(k._arcs) == set(g._arcs)` et
  `len(_composantes(k)) == len(_composantes(g))`, pour `k` comme pour `p`.

**Risques** : les sorties des graphes connexes ne changent pas. L'exemple 08 est
vérifié par son `.attendu`.

**`specification.md`** : **aucun changement**. La ligne 388 (« un arbre (ou une
forêt) couvrant ») devient vraie.

### Lot 5 — M4 : `amui(g, v)` ajoute un nœud isolé

**Fichiers** : `execution/predefinies.py` (`_amui` accepte un `_Upea` et appelle
`ajouter`), `predefinies.py` (signature),
`tests/test_extension_18_signatures.py` (1 attente),
`tests/test_extension_18_mcp.py`, tests de l'étape 3, `specification.md`,
`NOTES.md`.

**Approche**
- À l'exécution, `_amui` accepte « tapura, upea ou arbre ordonné ». Sur un
  graphe, c'est `ajouter(v)`, déjà sans effet si le nœud existe, et qui vérifie
  le nœud.
- Au typage, un nouveau patron `AJOUTABLE` sur les mêmes sortes que
  `RETIRABLE`. La signature devient `amui(ajoutable[T], T) -> aore` (Q8). Sur un
  `upea[T]`, la valeur doit être compatible avec `T`.

**Tests**, d'abord en échec :
- l'exemple `liste_noeuds` complété (une boucle `amui(g, n)` sur la liste des
  nœuds) donne 3 composantes ;
- `amui(g, "A")` sur un nœud existant ne change rien ;
- `amui(g, [1])` donne une erreur de type, et la même erreur à l'exécution avec
  `--sans-types` ;
- la copie d'un graphe faite à la main avec `motu`, `amui` et `taati` est égale
  à l'original (le cas de GRAPH-11) ;
- la ressource `upea://predefinies` contient `amui(ajoutable[T], T) -> aore`.
  Elle est calculée à partir de `PREDEFINIES`, donc il n'y a aucun texte à
  modifier à la main : le test le vérifie.

**Test modifié** : `test_extension_18_signatures.py:18`, de
`amui(collection[T], T) -> aore` à `amui(ajoutable[T], T) -> aore`. C'est la
nouvelle signature.

**`specification.md`**

1. Ligne 264, section *Graphes* :
   - avant : « Un nœud existe dès qu'un arc le touche, ou dès qu'il est écrit seul dans le littéral (`upea { "Rangiroa" }`) ; »
   - après : « Un nœud existe dès qu'un arc le touche, dès qu'il est écrit seul dans le littéral (`upea { "Rangiroa" }`), ou dès que `amui(g, v)` l'ajoute ; »
2. Ligne 339, tableau des fonctions prédéfinies :
   - avant : « ajoute `x` à la fin de la liste `c`, ou dans l'arbre ordonné `c` ; renvoie `aore` »
   - après : « ajoute `x` à la fin de la liste `c`, dans l'arbre ordonné `c`, ou comme nœud du graphe `c` (sans effet s'il y est déjà) ; renvoie `aore` »

### Lot 6 — L2 : notation exponentielle, et refus des non-finis

**Fichiers** : `lexer.py`, `parser.py` (`_decimal`), `execution/graphes.py`
(nœuds et poids), `execution/base.py` (`_verifier_cle`), `tests/generateurs.py`,
`tests/test_extension_17_proprietes.py`, tests du lexer, `specification.md`,
`NOTES.md`.

**Approche**
1. Le lexer accepte `(e|E)[+-]?chiffres` après la partie entière ou décimale.
   Le résultat est un `DECIMAL`. `1e`, `1e+`, `1ex` et `1e5x` restent
   « nombre mal formé ».
2. **Dans le même lot**, `_decimal` refuse un résultat non fini
   (`math.isfinite`) : `décimal trop grand : 1e999`, erreur de syntaxe.
3. À l'exécution, sont refusés :
   - un nœud non fini : « un nœud de upea doit être un nombre fini, pas inf » ;
   - un poids non fini : « le poids d'un arc doit être un nombre fini » ;
   - une clé non finie : « une clé de aifaito doit être un nombre fini ».
4. Dans `generateurs.py`, des décimaux tirés par
   `st.floats(allow_nan=False, allow_infinity=False)` (écrits avec `repr`)
   s'ajoutent aux nœuds et aux poids de la propriété de relecture.

**Tests**, d'abord en échec :
- lexer : `1..5`, `1..=5`, `t.hotu` et `0..e5` sont inchangés ; `1e5`,
  `1.5e-07`, `1e+16` et `1E3` sont des `DECIMAL` ; les formes mal formées
  restent refusées ;
- relire `upea { 1e-05 -> 1 }` redonne le même graphe ;
- `faaite 1e999;` est une erreur de syntaxe sur les deux backends, et `fmt` la
  refuse aussi ;
- `faaite 1e-400;` affiche `0.0` ;
- NaN et infini refusés comme nœuds (`taati`, littéral, `amui`), comme poids et
  comme clés (`aifaito`, `pupu`, `ahu`) ;
- `bellman_ford` ne peut plus recevoir de poids NaN ;
- la propriété de relecture, avec les nouveaux décimaux.

**Risques**
- Le test différentiel des deux backends doit rester vert.
- `tuhaa("inf")` fabrique encore un infini à partir d'un texte. Ce n'est pas
  dans le rapport et je n'y touche pas : la garde des nœuds, poids et clés suffit
  à protéger les structures.

**`specification.md`**

1. Ligne 85, *Lexique* : après « **Décimaux** : au moins un chiffre de chaque côté du point, `3.14`. », ajouter :
   « Un exposant peut suivre un entier ou un décimal : `1e-05`, `1.5e+16` et `2E3` sont des décimaux. C'est ainsi que s'affichent les très grands et les très petits décimaux. »
2. Une puce ajoutée à *Limites assumées* :

> - Les décimaux sont ceux de Python. Un littéral trop grand (`1e999`) est une erreur de syntaxe, et un littéral trop petit (`1e-400`) vaut `0.0`. Un calcul peut donner un infini ou un « pas un nombre », affichés `inf` et `nan`, que le parser ne relit pas. Ils ne peuvent être ni des nœuds de graphe, ni des poids, ni des clés d'arbre ordonné.

### Lot 7 — L4 : message pour `ahunui` en annotation

**Fichiers** : `parser.py` (`Parser.type`), tests du parser,
`specification.md`, `NOTES.md`.

**Approche** : quand le jeton est `AHUNUI`, le message devient
« type attendu, trouvé 'ahunui' : écrivez 'ahu' : un ahunui a le type ahu ».

**Tests**, d'abord en échec :
- `tuu z: ahunui = ahunui [1];` donne le message ;
- `ohipa f(h: ahunui)` et `-> ahunui` aussi.

**`specification.md`** : section *Types*, une puce ajoutée aux *Règles*, après la
ligne 437 :

> - Un tas max s'annote `ahu`, comme un tas min : l'annotation `ahu` ne fixe pas l'ordre du tas, et `ahunui` n'est pas un nom de type.

### Lot 8 — L5 : `fmt --ecrire` signale les commentaires perdus

**Fichiers** : `lexer.py` (compter les commentaires), `compilateur.py`
(`commentaires(source) -> int`), `cli.py`, tests de la CLI, `NOTES.md`.

**Approche**
- `tokenize(source, commentaires=None)` ajoute la position de chaque
  commentaire sauté à la liste qu'on lui passe.
- `fmt --ecrire` écrit comme aujourd'hui (code 0), puis affiche sur stderr
  `upea : 2 commentaires perdus`, ou `upea : 1 commentaire perdu`, rien s'il n'y
  en a aucun.

**Tests**, d'abord en échec :
- un fichier avec deux commentaires donne le message, le code 0 et le fichier
  réécrit ;
- sans commentaire, stderr est vide ;
- le test existant `test_etape_10_qualite.py:183-191` passe inchangé ;
- un `//` dans un texte n'est pas compté.

**`specification.md`** : **aucun changement** (Q10). La perte des commentaires
est déjà écrite (ligne 523), et la ligne 512 dit déjà que les avertissements
vont sur la sortie d'erreur.

### Lot 9 — M5 : une source map par saisie du REPL

**Fichiers** : `compilateur.py` (`executer_code`, `ligne_fautive`), `repl.py`,
tests du REPL, `NOTES.md`.

**Approche**
- `executer_code(code, sourcemap, espace, *, nom=NOM_FICHIER, cartes=None)`
  compile sous le nom `nom`. `ligne_fautive(exc, cartes)` cherche, pour chaque
  frame, la carte de **son** fichier.
- `_Session` numérote les saisies (`<upea-1>`, `<upea-2>`…) et garde
  `cartes: dict[str, SourceMap]`.
- Les lignes restent justes, car le source accepté est toujours un préfixe du
  source suivant.
- `run` et `executer_arbre` gardent `<upea>` et une seule carte.

**Tests**, d'abord en échec :
- le programme de COMP-01 et la variante `div(1, 0)` donnent
  `<repl>:3 … hoi l[3];` et `<repl>:3 … hoi a / b;` ;
- une erreur dans la saisie courante est toujours bien placée ;
- `run` est inchangé.

**`specification.md`** : **aucun changement**.

### Lot 10 — M6 : Ctrl-C

**Fichiers** : `repl.py`, `cli.py`, tests du REPL et de la CLI,
`specification.md`, `NOTES.md`.

**Approche**
- Dans `_Session.evaluer`, `except KeyboardInterrupt` autour de l'exécution :
  - la réponse est la sortie déjà produite, plus `interrompu` ;
  - la saisie est traitée comme une saisie en erreur : non retenue, l'état
    antérieur est gardé, comme pour une erreur d'exécution ;
  - le générateur `repl()` attrape aussi un Ctrl-C pendant la compilation.
- Dans `commande_run`, `except KeyboardInterrupt` : vider stdout, afficher
  `upea : interrompu` sur stderr, puis renvoyer **130**.

**Tests**, d'abord en échec :
- déterministes, par `monkeypatch` : l'exécution lève `KeyboardInterrupt` ;
  - le REPL répond `interrompu`, puis `faaite x;` affiche la valeur déclarée
    avant ;
  - `run` renvoie 130 sans traceback ;
- un test de bout en bout avec `_thread.interrupt_main` sur une boucle finie
  d'au plus 2 s.

**`specification.md`** : ligne 512, codes de retour.
- avant : « `3` erreur d'exécution. »
- après : « `3` erreur d'exécution, `130` exécution interrompue (Ctrl-C). »

### Lot 11 — L6 : bac à sable et CLI

**Fichiers** : `bac_a_sable.py`, `compilateur.py` (`MemoryError`), `cli.py`,
tests du bac à sable et de la CLI, `specification.md`, `NOTES.md`, `README.md`.

**Approche**

1. **TEST-04** : la requête transmet le délai à l'enfant. L'enfant se limite à
   2 × délai de temps CPU :
   - sous Windows, `JOB_OBJECT_LIMIT_PROCESS_TIME` (0x2) et
     `PerProcessUserTimeLimit`, dans le *job object* existant ;
   - sous Linux, `RLIMIT_CPU`.

   Le délai mesuré par le parent reste la règle : le temps CPU ne dépasse pas le
   temps réel, et la limite CPU n'agit donc que si le parent a disparu.
2. **TEST-05**, en deux temps :
   - dans `executer_code`, un `MemoryError` est d'abord noté (sa ligne relevée
     sans allocation), puis on **sort** du bloc `except` pour libérer les frames
     et l'espace du programme, `gc.collect()`, et enfin on lève
     `ErreurExecution("mémoire dépassée", ligne)` ;
   - côté parent, en dernier recours, un `EnfantEnPanne` dont la sortie d'erreur
     contient `MemoryError` devient un résultat `erreur_execution`
     « mémoire dépassée ».
3. **TEST-06** :
   - côté enfant, `json.dumps(…, ensure_ascii=True)` ;
   - côté parent, `json.loads` et la lecture des champs sont gardés : en cas
     d'échec, `EnfantEnPanne`.
4. **TEST-10** :
   - un `_ecrire(chemin, texte)` attrape `OSError` pour chaque écriture de
     `transpile` (programme, prélude, source map) et de `fmt --ecrire`. Il
     affiche `upea : impossible d'écrire <fichier> (<raison>)`, code 1 (Q9) ;
   - `_lire` teste `is_dir()` d'abord ;
   - un tube fermé est une fin silencieuse :
     - dans `run`, une `ErreurExecution` causée par une `OSError` (le seul
       accès au système d'un programme Upea est sa sortie) ;
     - dans `main`, une `BrokenPipeError` ou une `OSError` en écrivant sur
       stdout.

     Dans les deux cas, stdout est redirigé vers `os.devnull` pour que
     l'interpréteur ne lève rien en se fermant, et le code est **0** (Q9).

**Tests**, d'abord en échec :
- l'enfant lancé directement, avec un délai de 0,5 s et sans parent qui le tue,
  se termine seul en quelques secondes, sans résultat ;
- remplir 128 Mo de petits objets (paramètre `memoire`) donne `erreur_execution`
  « mémoire dépassée » ;
- les deux sources de TEST-06 rendent une `Execution` ;
- `-o` vers un dossier absent, `-o` vers un dossier, et `fmt --ecrire` sur un
  fichier en lecture seule donnent un message, le code 1 et aucun traceback ;
- `run <dossier>` donne « … est un dossier, pas un fichier » ;
- `run` d'une grosse sortie dont on ferme le tube après une ligne donne le
  code 0 et une sortie d'erreur vide.

**Risques**
- Le *job object* est le code le plus délicat : un test s'exécute sous Windows,
  et la CI le lance sous Linux.
- `gc.collect()` après un `MemoryError` n'est appelé que dans ce cas.

**`specification.md`** : ligne 512.
- avant : « `1` erreur de compilation (ou fichier illisible) »
- après : « `1` erreur de compilation (ou fichier illisible, ou impossible à écrire) »

**`README.md`** : le nombre de tests (à la fin), et le bac à sable de la section
MCP (« 5 s, 512 Mo » ; j'ajoute « et deux fois le délai en temps CPU »).

### Récapitulatif des changements de `specification.md`

| Lot | Endroit | Nature |
|---|---|---|
| L1 | *Limites assumées* | 1 puce ajoutée (imbrications) |
| M1 | tableau des erreurs, l. 411 | 1 ligne réécrite |
| M1 | *Limites assumées* | 1 puce ajoutée (20 000 appels) |
| M4 | *Graphes*, l. 264 | 1 phrase complétée |
| M4 | *Fonctions prédéfinies*, l. 339 | 1 cellule complétée |
| L2 | *Lexique*, l. 85 | 2 phrases ajoutées |
| L2 | *Limites assumées* | 1 puce ajoutée (décimaux) |
| L4 | *Types*, règles | 1 puce ajoutée |
| M6 | *Utilisation*, l. 512 | `130` ajouté |
| L6 | *Utilisation*, l. 512 | « ou impossible à écrire » |

M2, M3, L5 et M5 ne la changent pas. Chaque ligne entre, dans le même commit,
dans la section « Modifications depuis la validation de la spécification » de
`NOTES.md`, avec son lot et sa raison.

## 4. Décisions qui te reviennent

**Q1. La date de validation.** Ton message dit « [DATE] ». Quelle date écrire
dans `NOTES.md` ? Je la reporte à l'identique, et je fais le remplacement « à
faire valider » → « validée le … » dans le commit du lot 1.

**Q2. Où placer les limites d'imbrication (L1) ?**
- (a) **Dans le parser**, avec des compteurs et un parcours itératif après
  l'analyse syntaxique. Cela couvre aussi `fmt`, `:arbre` et
  `atelier.formater`, et le verdict ne dépend pas de la limite de récursion de
  Python. **Recommandé.**
- (b) Dans l'analyse sémantique, comme le conseil. Dans ce cas, `fmt` garde son
  traceback, et le bac à sable et `check` peuvent diverger sur `p500`.

**Q3. Les limites d'expression (L1) : 150 niveaux, avec un poids de 3 pour
`upea` et de 2 pour un arbre ordonné ?**
- (a) **Oui** : c'est mesuré sûr dans le pire cas combiné. Les sommes à plat de
  151 à 200 termes, qui passent aujourd'hui, deviennent des erreurs.
  **Recommandé.**
- (b) 190 niveaux : on garde les sommes jusqu'à 191 termes, mais le pire cas
  combiné échoue à la limite de récursion de 1 000. Ce choix demande donc Q6 (a)
  pour tenir.

**Q4. Ajouter la limite de 20 boucles imbriquées à L1 (trouvaille hors
rapport) ?**
- (a) **Oui** : c'est le même bug (`check` accepte, l'exécution plante) avec un
  seuil plus bas. **Recommandé.**
- (b) Non : le filet autour de `compile()` en fait une erreur de compilation à
  l'exécution seulement, et `check` reste en désaccord.

**Q5. Le message de M1.**
- (a) **Deux messages** : « récursion trop profonde (plus de 20 000 appels
  imbriqués) » pour une récursion du programme, et « récursion trop profonde »
  inchangé pour une liste imbriquée. **Recommandé.**
- (b) Un seul message, celui du conseil, faux pour les listes imbriquées.

**Q6. La limite de récursion vaut-elle aussi à la compilation ?**
`compilateur.py` importe `_PROFONDEUR_MAX` du prélude, ce qui applique la limite
(et celle des chiffres) dans tout processus qui compile.
- (a) **Oui** : il n'y a toujours qu'un seul appel, dans le prélude.
  **Recommandé.**
- (b) Non : la constante est dupliquée dans `compilateur.py`, avec un test qui
  vérifie l'égalité des deux.

**Q7. L'ordre des nœuds dans `kruskal` et `prim` (M3).**
- (a) **Les nœuds isolés après les arêtes** : les sorties actuelles ne changent
  pas. **Recommandé.**
- (b) Tous les nœuds dans l'ordre du graphe : la sortie de l'exemple 08 et son
  `.attendu` changent.

**Q8. Le nom du patron dans la signature d'`amui` (M4).**
- (a) **`amui(ajoutable[T], T) -> aore`**, une nouvelle abréviation pour
  « tapura, upea ou arbre ordonné ». **Recommandé.**
- (b) `amui(retirable[T], T) -> aore` : on réutilise l'abréviation de `tatara`,
  dont le nom est trompeur pour un ajout.

**Q9. Les codes de retour de L6.**
- Écriture impossible : (a) **1, avec « ou impossible à écrire » dans la
  spécification** (**recommandé**) ; (b) 2.
- Tube fermé : (a) **0, sans message** : le lecteur est parti, le programme n'a
  pas échoué, et la spécification ne change pas (**recommandé**) ; (b) 141, la
  convention Unix (128 + SIGPIPE), qu'il faudrait ajouter à la spécification ;
  (c) 1.

**Q10. L5 : mentionner l'avertissement de `fmt --ecrire` dans la
spécification ?**
- (a) **Non** : c'est une sortie d'erreur de la CLI, et la perte des commentaires
  y est déjà écrite. **Recommandé.**
- (b) Oui, une demi-phrase à la ligne 523.

**Q11. `specification.md:525` (« listes imbriquées sur plus d'un millier de
niveaux »).** C'est faux aujourd'hui (247 niveaux), et presque juste après M1
(998). Aucun point du rapport ne la vise.
- (a) **Ne pas y toucher.** **Recommandé.**
- (b) Écrire « environ un millier », dans le lot M1.
