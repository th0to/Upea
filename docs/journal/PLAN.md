> Document de travail, état au commit `9dc63d7` (3 novembre 2026). Il n'est plus tenu à jour.

# Plan de correction — audit d'Upea

État de départ : commit `c694f95 v1.1`, arbre de travail propre.

## 0. Référence

| Vérification | Résultat |
|---|---|
| `pytest projet` (CPython 3.12.16) | **921 réussis, 4 ignorés** (`test_extension_16_affichage.py:265`, Graphviz absent) : 925 tests |
| `mypy projet/upea` (strict) | aucune erreur, 35 fichiers |
| `ruff check projet` | aucune erreur |

`uv` n'est pas dans le PATH du shell que j'utilise. J'ai donc lancé les exécutables du `.venv` (créé par uv, CPython 3.12) : `.venv\Scripts\pytest.exe`, `mypy.exe`, `ruff.exe`. C'est le même environnement. Je ferai de même en phase 2, sauf si tu me donnes le chemin de `uv`.

Les reproductions sont lancées depuis `projet/` avec
`timeout 10 python -m upea run [--sans-types] fichier.upea`.

---

## 1. Vérification de l'audit

| Point | Verdict | En bref |
|---|---|---|
| A | **confirmé, plus large que décrit** | toute traversée d'un `tumu` cyclique boucle |
| B | **nuancé** (mécanisme confirmé, échec non reproduit ici) | pas de Python 3.15 sur la machine |
| C | **confirmé** | même racine que A |
| D | **confirmé** | 2 468 lignes pour `faaite 1;` |
| E | **nuancé** : l'unification n'est pas raisonnable, un test différentiel l'est | les deux backends produisent déjà le même arbre Python |
| F | **confirmé** | |
| G | **confirmé, mais cohérent avec le reste du langage** | `1 == 1.0` vaut `tia` partout |
| H | **nuancé** | les règles `@regle` ne font qu'environ 100 lignes |
| I | **nuancé** | l'index Git est déjà tout en LF ; seule la copie de travail est mélangée |
| J | **nuancé** | les invariants des arbres ordonnés sont déjà testés au hasard |
| K | **confirmé** | |

### A — `tumu` qui se contient : confirmé, plus large que décrit

Avec `tuu t = tumu(1); amui(t.amaa, t);` puis :

| Suite | Résultat |
|---|---|
| `faaite roa(t);` | ne se termine pas (timeout, code 124) |
| `faaite t;` | ne se termine pas |
| `faaite 2 roto t;` | ne se termine pas (`_Tumu.__contains__`, pile sans fin) |
| `tataitahi n roto t { … }` | ne se termine pas |
| `faaite teitei(t);` | ne se termine pas |
| `faaite t == t;` | `tia` (Python court-circuite l'identité) |
| cycle indirect `a → b → a`, puis `roa(b)` | ne se termine pas |

`tuu l = []; amui(l, l); faaite l;` donne bien « récursion trop profonde ». C'est le même message pour `t.hotu = t; faaite parau(t);` (cycle par la valeur), avec `--sans-types`.

**À ne pas casser** : un sous-arbre partagé sans cycle (`tuu f = tumu(3); tuu t = tumu(1, f, f);`) fonctionne aujourd'hui (`roa(t)` vaut 3).

### B — traduction des erreurs dépendante de CPython : nuancé (mécanisme confirmé, échec non reproduit)

- Confirmé : `compilateur.py:150-200` reconnaît les `TypeError` par des regex sur le texte de CPython. Il n'y a pas de `.python-version`, et `requires-python = ">=3.12"` n'a pas de borne haute.
- Confirmé : CPython a bien changé ce message pour l'opérateur `in` (issue #95144 : « is not a container or iterable »).
- Non reproduit : seul CPython 3.12 est installé ici, et je n'en ai pas téléchargé d'autre. Avec un autre message, le repli de `_type_error` donnerait « opération impossible sur ces valeurs (argument of type 'int' is not a container or iterable) ». Pas de traceback, donc, mais du texte Python, et le test échouerait.
- Le `.venv` actuel est en 3.12. Le risque concerne un clone neuf, ou un `uv sync` qui recréerait l'environnement.

### C — erreur signalée au mauvais endroit : confirmé

Avec `--sans-types` :

- `amui(t.amaa, 5);` (ligne 2) passe ;
- l'erreur ne sort qu'au `roa(t)` de la ligne 4 : « les branches d'un tumu doivent être des tumu, pas un numera » ;
- même chose pour `t.amaa = 5;`.

Sans `--sans-types`, le vérificateur attrape les deux à la bonne ligne. C'est la même correction que A.

### D — prélude recopié : confirmé

- `faaite 1;` donne **2 468 lignes** avec `--backend python`, 1 939 avec `--backend ast` (les commentaires disparaissent).
- La regex `_IMPORT_RELATIF` (`prelude.py:33`) ne retire que les imports **en tête de ligne**. Un import relatif dans une fonction survivrait, et le fichier généré planterait à l'exécution. Aucun module n'en contient aujourd'hui.

### E — deux générateurs : nuancé

J'ai comparé `ast.dump(ast.parse(texte du backend python))` et `ast.dump(module du backend ast)`, sans les positions et après avoir aplati les `and`/`or` imbriqués. Le résultat est **identique sur les 10 exemples**. Voir le lot 11 pour la conclusion.

### F — `toujours_retourne` trop prudent : confirmé

- `ohipa f() -> numera { tamau tia { hoi 1; } }` est refusé (« peut se terminer sans 'hoi' »).
- `tamau tia { faaea; }` est refusé à juste titre : il faut garder ce refus.

### G — nœuds `1` et `1.0` fusionnés : confirmé, mais cohérent avec le reste du langage

`tuu g = upea { 1 -> 2 }; taati(g, 1.0, 3);` (avec `--sans-types`) donne un seul nœud `1`, avec deux arcs. Le vérificateur ne le voit que si `g` a un type connu : avec `upea {}`, il laisse passer. Mais c'est la règle de tout Upea, où `1 == 1.0` vaut `tia` :

- `1.0 roto [1]` vaut `tia` ;
- `aifaito [1, 1.0, 2]` donne `aifaito [1, 2]`.

### H — taille de `semantique.py` : nuancé

La section `@regle` (`semantique.py:729-825`) fait environ 100 lignes. Le gros du fichier est la classe `Analyseur` (lignes 128-728), qui est cohérente : un seul `singledispatchmethod` pour les instructions, un pour les expressions. Sortir les règles ramènerait le fichier à environ 730 lignes : faible gain.

### I — fins de ligne : nuancé

- `git ls-files --eol` donne 44 fichiers `i/lf w/crlf` et 35 `i/lf w/lf`.
- **Dans Git, tout est en LF.** Le mélange ne vient que de la copie de travail : `core.autocrlf=true` sur cette machine, et les nouveaux fichiers écrits en LF par les outils.
- Il n'y a pas de `.gitattributes`. Le résultat dépend donc de la configuration de chaque clone : confirmé.

### J — tests par propriétés : nuancé

| Propriété | Déjà couvert ? | Sondage manuel |
|---|---|---|
| Invariants AVL, rouge-noir, arbre B, ABR | **oui** : `test_extension_14_structures.py:102-121`, 6 graines × 400 ajouts et retraits × 6 structures, comparés à un `set` modèle, invariants vérifiés après chaque opération | — |
| Tas | **oui** : `:145-160` | — |
| `fmt` idempotent | non | vrai sur les 10 exemples, et la sortie est conservée |
| Relecture de `parau` | non | 7 cas délicats relus à l'identique et `==` (échappements, poids négatifs ou décimaux, boucle sur soi, nœud isolé, `tumu` contenant une liste et `aore`) |
| Accord des deux backends | seulement les 10 exemples | — |

### K — README : confirmé

`pyproject.toml` pointe `readme = "NOTES.md"`.

---

## 2. Mes propres trouvailles

### N1 — sous Windows, rediriger la sortie d'un dessin plante (**bug**)

Dans un PowerShell sans `PYTHONIOENCODING` :

- `python -m upea run exemples\10_hohoa.upea > sortie.txt` donne « erreur inattendue (UnicodeEncodeError : 'charmap' codec can't encode…) », code 3.
- Le fichier autonome (`python sortie.py > f.txt`) plante avec un **traceback Python**.

Cause : la sortie redirigée est en cp1252, et les traits `┌─┴─┐` n'y existent pas. Les tests ne le voient pas parce qu'ils forcent `PYTHONIOENCODING=utf-8` (`test_etape_08_generation.py:43`, `test_etape_09_cli_repl.py:177`).

### N2 — `==` et `parau` d'un `tumu` profond

```
tuu t = tumu(0);
tataitahi i roto 1..3000 { t = tumu(i, t); }
```

- `roa`, `teitei`, `roto`, `prefixe`, `diametre`, `hohoa` et `dot` marchent : ils sont itératifs.
- `t == u` et `parau(t)` (donc `faaite t` avec d'autres valeurs) donnent « récursion trop profonde », alors que le programme ne contient aucune récursion. Même chose pour une liste imbriquée 3 000 fois.

### N3 — le fichier autonome affiche des tracebacks

`faaite 1 / 0;` transpilé puis lancé par `python sortie.py` affiche un `ZeroDivisionError` brut. Seule la CLI traduit les erreurs. Est-ce voulu ? C'est la question 10.

---

## 3. Lots, par priorité

Pour chaque lot, en phase 2 :

1. test rouge ;
2. correction ;
3. pytest, mypy et ruff verts ;
4. spec, `.attendu` et `NOTES.md` si besoin ;
5. un commit.

### Lot 1 — B : ne plus dépendre du texte de CPython pour `roto`, et épingler 3.12

- **Fichiers** :
  - nouveau `.python-version` (`3.12`) ;
  - `upea/execution/predefinies.py` (nouvelle fonction `_roto`) ;
  - `generateur.py`, `generateur_ast.py` (`roto` devient `_roto(x, c)`, au lieu de l'opérateur `in`) ;
  - `compilateur.py` (retrait des deux regex de `in`).
- **Approche** :
  - `_roto` vérifie la sorte du conteneur (`tapura`, `parau`, `tumu`, `upea`, arbre ordonné) et lève `_Erreur` avec les messages actuels.
  - Les regex restantes (opérateurs arithmétiques, comparaisons, indexation) ont des messages stables depuis longtemps. Je les garde, et j'ajoute un test « canari » : chaque motif de `TRADUCTIONS` doit être atteint par au moins un programme, et aucun cas connu ne doit tomber dans le repli. Une version de Python qui change un message fait alors échouer ce test précis.
- **Alternative écartée** : assouplir seulement la regex (`is not (?:a container or )?iterable`). On resterait à la merci du prochain changement. Envelopper tous les opérateurs dans des fonctions du prélude rendrait le code généré illisible pour un gain faible.
- **Tests** :
  - `roto` sur `numera`, `aore` et `tiahape` ;
  - `parau` dans `parau` avec un `numera` à gauche ;
  - le canari ;
  - le test différentiel du lot 11 passe toujours.
- **Test existant modifié** : `test_etape_08_generation.py:143-144` attend `('a' in 'abc')`. Il deviendra `_roto('a', 'abc')`, ce que j'expliquerai dans le commit.
- **Spec et `.attendu`** : aucun changement de sortie. Dans la spec, une ligne d'erreur pour `faaite 1 roto 5;`.
- **Risque** : faible. Un appel de fonction par `roto`.

### Lot 2 — A + C : un `tumu` reste un arbre fini, et l'erreur arrive au bon endroit

- **Fichiers** : `upea/execution/tumu.py`, `base.py` (garde de `_texte`), `predefinies.py` si besoin.
- **Approche** :
  - `amaa` devient une `_Branches(list[_Tumu])`, qui connaît son nœud propriétaire et vérifie chaque ajout (`append`, `__setitem__`, et par prudence `insert`, `extend`, `__iadd__`). L'élément doit être un `tumu`, et le propriétaire ne doit pas être atteignable depuis lui (ce qui couvre les cycles indirects).
  - `t.amaa` devient une propriété ; son setter vérifie la liste reçue (question 1).
  - `_Branches` est déclarée `tapura` dans `_SORTES`, donc `isinstance(…, list)`, l'affichage et `_parcours` restent inchangés.
  - Pour les listes, ou un `hotu` qui se contient : une garde (ensemble des `id` en cours d'écriture) dans `_texte` donne une erreur claire au lieu de « récursion trop profonde » (question 3).
- **Alternative écartée** : détecter les cycles à chaque traversée. Il faudrait toucher `__contains__`, `_noeuds_prefixe`, `_taille`, `_texte` et les dessins, et l'erreur resterait au mauvais endroit, donc C ne serait pas corrigé.
- **Tests** (avec et sans `--sans-types`) :
  - les cas A1 à A8 ci-dessus (erreur à la ligne du `amui`) ;
  - C : `amui(t.amaa, 5)`, `t.amaa = 5` et `t.amaa[0] = 5`, signalés à leur ligne ;
  - le sous-arbre partagé reste permis ;
  - `amui(l, l); faaite l;` donne un message clair ;
  - le test existant `test_etape_08_execution.py:163` (`t.amaa = 3` attendu en ligne 3) attendra la ligne 2, ce que j'expliquerai dans le commit.
- **Spec** :
  - section *Arbres* : `t.amaa` n'est plus « une liste ordinaire » mais une liste vérifiée ; l'éventuelle copie lors de l'affectation ; le partage permis ;
  - nouvelles lignes dans la table des erreurs d'exécution.
- **`.attendu`** : aucun. 04 et 06 n'affectent jamais `amaa` ; 04 fait `amui(arbre.amaa[0].amaa, tumu(8))`, qui reste valide.
- **Risque** : moyen-faible. La propriété ajoute un appel à chaque accès à `amaa` (négligeable), et mypy strict sur une sous-classe de `list` demande un peu de soin.

### Lot 3 — N1 : sortie en UTF-8 sous Windows

- **Fichiers** : `upea/execution/base.py`, `upea/cli.py` (stderr, si une ligne source contient un caractère hors cp1252, ce que je vérifierai en début de lot).
- **Approche** : au chargement du prélude, si `sys.stdout` est un `TextIOWrapper` dont l'encodage n'est pas UTF-8, le passer en UTF-8 avec `reconfigure`. Cela couvre la CLI et le fichier autonome. Un terminal Windows n'est pas concerné, car Python y écrit déjà en Unicode.
- **Alternative écartée** : `errors="replace"`. Il n'y aurait plus de plantage, mais le dessin serait détruit.
- **Tests** : sous-processus avec `PYTHONIOENCODING=cp1252` (reproduit le bug sur tous les systèmes), pour `run` et pour `python sortie.py`, sur l'exemple 10.
- **Spec** : une phrase dans *Dessins* (la sortie est en UTF-8). `.attendu` inchangés.
- **Risque** : faible. Sous PowerShell 5.1, `>` réencode la sortie avec la page de code de la console : pas de plantage, mais des traits illisibles. Je le documenterai dans les limites (on peut écrire avec `-o` ou utiliser `cmd`).

### Lot 4 — I : `.gitattributes`

- **Fichiers** : nouveau `.gitattributes` (`* text=auto eol=lf`), puis `git add --renormalize .`. Je m'attends à un index inchangé, puisqu'il est déjà en LF.
- **Alternative écartée** : laisser `core.autocrlf` faire le travail. Cela dépend de chaque clone.
- **Tests** : aucun test automatique, car le résultat dépend de la configuration Git locale. Vérification avec `git ls-files --eol`.
- **Risque** : nul pour l'index. Réécrire aussi la copie de travail en LF est la question 12.

### Lot 5 — J : tests par propriétés

- **Fichiers** :
  - nouveau `tests/test_extension_17_proprietes.py` ;
  - `tests/outils.py` (générateur de programmes et de valeurs) ;
  - `pyproject.toml` et `uv.lock`, seulement si `hypothesis` est accepté (question 6).
- **Propriétés** :
  1. `fmt(fmt(s)) == fmt(s)`, et la sortie d'exécution est inchangée par `fmt` ;
  2. relire `parau(x)` donne `== x` pour les graphes (textes échappés, poids négatifs ou décimaux, boucles, nœuds isolés), les `tumu` et les six sortes ordonnées ;
  3. les deux backends donnent la même sortie, ou la même erreur à la même ligne, sur des programmes générés (et le même arbre Python, lot 11).
- Les invariants sont déjà couverts : je n'y ajoute rien, sauf, avec `hypothesis`, la réduction automatique des contre-exemples sur les mêmes scénarios.
- **Sans `hypothesis`** : mêmes propriétés avec `random.Random(graine)`, comme dans `test_extension_14`. On n'a pas de réduction automatique des contre-exemples, mais aucune dépendance.
- **Spec et `.attendu`** : aucun.
- **Risque** : les propriétés peuvent révéler des bugs. Si c'est le cas, je m'arrête et je te les montre avant de les corriger.

### Lot 6 — F : `tamau tia` sans `faaea` compte comme « renvoie toujours »

- **Fichiers** : `upea/semantique.py` (`toujours_retourne`).
- **Approche** : une boucle `TantQue` dont la condition est le littéral `tia`, et dont le corps ne contient aucun `faaea` qui la vise (on ne descend pas dans les boucles imbriquées), ne se termine jamais normalement. Elle compte donc comme un retour.
- **Alternative** : documenter la limite (question 4).
- **Tests** :
  - `tamau tia { hoi 1; }` est accepté ;
  - `tamau tia { faaea; }` est refusé ;
  - un `faaea` dans une boucle imbriquée laisse la fonction acceptée ;
  - `tamau 1 == 1 { … }` reste refusé (seul le littéral compte).
- **Spec** : `specification.md:429`.
- **Risque** : faible.

### Lot 7 — G : documenter l'égalité des nœuds (recommandé)

- **Fichiers** : `specification.md` (section *Graphes*), un test qui fige le comportement.
- **Approche** : une phrase dans la spec : « deux nœuds égaux au sens de `==` (`1` et `1.0`) sont le même nœud ; le graphe garde l'écriture de la première apparition ». C'est cohérent avec les listes et les arbres ordonnés.
- **Alternatives** :
  - refuser les décimaux comme nœuds (change la spec et le vérificateur) ;
  - distinguer `1` et `1.0` (contredit `==` partout ailleurs).
- **Risque** : nul.

### Lot 8 — N2 : `==` et forme compacte des `tumu` profonds, sans récursion

- **Fichiers** : `upea/execution/tumu.py`.
- **Approche** : rendre itératifs `_Tumu.__eq__` et `_texte` pour les `tumu` (une pile explicite sur la structure ; on ne repasse par `_texte` que pour les `hotu`). Les listes imbriquées très profondément gardent « récursion trop profonde » : c'est un cas artificiel, que je documenterai.
- **Tests** : la chaîne de 3 000 nœuds donne `==` et `parau` corrects.
- **Risque** : faible. Les tests d'affichage existants verrouillent le format.

### Lot 9 — D : prélude robuste, et plus léger si tu le veux

- **9a (toujours)** : retirer les imports relatifs avec `ast` au lieu de la regex. On repère les `ImportFrom` de niveau ≥ 1 et `from __future__` en tête de module, et on supprime leurs lignes (`lineno`…`end_lineno`), ce qui garde les commentaires. Un import relatif ailleurs qu'en tête de module devient une erreur à la construction du prélude, avec un test.
- **9b (question 7)** : élagage fonction par fonction.
  - Les racines sont les noms `_…` utilisés par le code généré.
  - On garde une définition si elle est atteinte.
  - On garde un enregistrement (`@_texte.register(X)`, `@_sorte_upea`) si tous les noms qu'il cite sont gardés, jusqu'à un point fixe.
  - Le fichier reste autonome.
  - Gain attendu : `faaite 1;` passerait à environ 200 lignes. En revanche, tout programme qui parcourt une structure (`_parcours`) tire presque tout. **Je mesure le gain sur les 10 exemples en début de lot ; sous 30 %, je m'arrête et je te le dis.**
- **9c (question 7)** : option `transpile --prelude externe`, qui écrit `upea_prelude.py` à côté de la sortie et l'importe. Le fichier généré n'est plus autonome seul, mais le dossier l'est.
- **Tests** : tous les tests qui exécutent le fichier autonome (`test_etape_08_generation`) passent ; test sur la taille ; test de l'import relatif mal placé.
- **Risque** : 9a faible ; 9b moyen (dispatch dynamique) ; 9c faible.

### Lot 10 — H : sortir les règles des opérateurs

- **Fichiers** : nouveau `upea/regles.py` (`regle`, `RegleBinaire`, les 6 règles, environ 100 lignes) ; `semantique.py` l'importe (`Analyseur` n'est importé que sous `TYPE_CHECKING` dans `regles.py`).
- **Alternative écartée** : découper `Analyseur`, qui est cohérent tel quel.
- **Risque** : faible. Gain modeste, à décider (question 9).

### Lot 11 — E : test différentiel, pas d'unification

- **Pourquoi pas l'unification** :
  - L'étape 8 (texte, `Emetteur`, source map ligne à ligne) et l'extension 11 (`ast`) sont deux livrables distincts du projet. Produire le texte par `ast.unparse` supprimerait le premier.
  - Le style du texte (tout parenthésé) est vérifié par `test_etape_08_generation`.
  - La source map du backend `ast` repose déjà sur une relecture du texte, et celle du backend texte sur l'`Emetteur`. Les fusionner obligerait à réécrire les deux pour un gain nul en sortie.
- **À la place** : un test qui compare, sans les positions et après avoir aplati les `BoolOp`, l'arbre Python des deux backends. Il porte sur les 10 exemples et sur les programmes générés du lot 5, et compare aussi la sortie d'exécution. La sonde montre que c'est déjà vrai sur les 10 exemples. Coût : environ 40 lignes de test.
- **Risque** : nul.

### Lot 12 — K : README

- **Fichiers** : nouveau `README.md` (présentation en trois phrases, l'exemple des îles, un dessin d'AVL et de graphe en bloc texte, tiré de l'exemple 10, les commandes, les chiffres de qualité) ; `pyproject.toml` (`readme`, question 13).
- `NOTES.md` reste le document de rendu.
- **Risque** : nul.

---

## 4. Décisions qui te reviennent

1. **(A)** `t.amaa = l` : le `tumu` reçoit-il une **copie vérifiée** des éléments de `l` (recommandé ; `amui(l, …)` ne change alors plus `t`), ou faut-il **interdire** l'affectation de `amaa` ?
2. **(A)** Un sous-arbre partagé sans cycle (`tumu(1, f, f)`) reste-t-il permis ? (recommandé : **oui**, c'est le comportement actuel)
3. **(A)** Une `tapura` qui se contient : **erreur claire** à l'affichage (recommandé, la forme compacte reste relisible) ou affichage `[...]` comme Python ?
4. **(F)** **Affiner** `toujours_retourne` pour `tamau tia` sans `faaea` (recommandé), ou documenter la limite ?
5. **(G)** **Documenter** la fusion `1` / `1.0` (recommandé), refuser les décimaux comme nœuds, ou les distinguer ?
6. **(J)** J'ajoute **`hypothesis`** au groupe `dev` : oui ou non ? (Sans lui : tirages à graine fixe.)
7. **(D)** Je fais **9b** (élagage du prélude) : oui ou non ? Et **9c** (`--prelude externe`) : oui ou non ? (9a est fait dans tous les cas.)
8. **(E)** Tu confirmes : **pas d'unification**, un test différentiel à la place ?
9. **(H)** Je fais le petit découpage (`regles.py`) : oui ou non ?
10. **(N3)** Le fichier autonome doit-il, lui aussi, traduire ses erreurs (pas de traceback avec `python sortie.py`) ? Si oui, c'est un lot de plus, moyen : il faut une table des lignes et la traduction des exceptions dans le prélude (cela renforcerait aussi B).
11. **(N1)** Je passe la sortie standard en UTF-8 au chargement du prélude : oui ou non ?
12. **(I)** Après le `.gitattributes`, je réécris la copie de travail en LF (44 fichiers sur disque, contenu Git inchangé) : oui ou non ?
13. **(K)** `pyproject.toml` pointe-t-il vers `README.md` au lieu de `NOTES.md` : oui ou non ?

Ordre proposé : 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11 → 12, chaque lot étant indépendant des autres. Seule exception : le lot 11 réutilise le générateur de programmes du lot 5 s'il est fait, et se limite aux exemples sinon.
