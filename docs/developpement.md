# Guide du développeur

Ce guide s'adresse à qui veut modifier Upea : préparer l'environnement, lancer les
vérifications, comprendre l'organisation des tests, et suivre trois recettes (ajouter
une fonction prédéfinie, un backend, un mot-clé). L'[architecture](architecture.md)
décrit le rôle de chaque module.

## 1. Environnement

- [uv](https://docs.astral.sh/uv/) gère Python et l'environnement. La version est
  fixée par `.python-version` (3.12), et les dépendances par `uv.lock`.
- `uv sync`, depuis la racine du dépôt, installe le groupe `dev` : pytest, mypy, ruff,
  hypothesis, et le groupe `mcp` (le SDK du serveur). Le langage lui-même n'a aucune
  dépendance (`dependencies = []`).
- Le dépôt n'est pas un paquet installable (`package = false` dans `pyproject.toml`).
  Les tests rendent `upea` importable par `projet/tests/conftest.py`, et la CLI se lance
  depuis `projet/` : `uv run python -m upea …`.
- Si `uv` n'est pas dans le `PATH`, appelez-le par son chemin complet.
- Les fins de ligne sont LF partout (`.gitattributes`), quelle que soit la
  configuration de Git sur la machine.

## 2. Les vérifications

Depuis la racine du dépôt :

```bash
uv run pytest projet                       # les tests
uv run mypy projet --platform win32        # le typage, puis --platform linux et darwin
uv run ruff check projet                   # le style
uv run ruff format --check projet          # la mise en forme (ruff format projet la corrige)
```

Les quatre doivent passer avant chaque commit. La configuration est dans
`pyproject.toml` : mypy en mode `strict` avec `warn_unreachable`, sur tout `projet/`
(tests compris) ; ruff avec les règles `E`, `F`, `I`, `UP`, `B` et `SIM`, et des lignes
de 88 caractères. mypy se lance pour les trois plateformes parce que le bac à sable a
du code propre à chacune (`sys.platform`).

## 3. Les tests

Ils sont dans `projet/tests/`, un fichier par étape, et `-k` en choisit un groupe :

| Fichiers | Ce qu'ils vérifient | Sélection |
|---|---|---|
| `test_etape_NN_*.py` | les étapes 1 à 10 du cours | `-k etape_05` |
| `test_extension_NN_*.py` | les extensions 11 à 18 (18 : le serveur MCP) | `-k extension_12` |
| `test_conseil_*.py` | les corrections de l'audit du conseil, une par lot (L1, M1…) | `-k conseil` |
| `test_livraison_documentation.py` | les programmes et les liens de la documentation | `-k livraison` |

Les outils communs :

- `conftest.py` rend `upea` et `outils` importables, choisit le profil `hypothesis`,
  retire les variables de couleur de l'environnement (`sans_couleurs`, pour tous les
  tests), et fournit la fixture `exemple`, qui passe en revue chaque programme
  d'`exemples/`.
- `outils.py` : `lancer(source)` exécute un programme et rend ce qu'il a affiché ;
  `une_erreur(source)` et `erreurs_de_compilation(source)` rendent les erreurs de
  compilation, et `position(erreur)` leur ligne et leur colonne ; `arbres_python`
  rend les arbres Python des deux backends, pour les comparer.
- `generateurs.py` : les stratégies `hypothesis`, des programmes Upea qui se terminent
  toujours, et des littéraux à relire.

Quelques points à connaître :

- **Les exemples** : un programme `exemples/NN_nom.upea` et sa sortie exacte
  `NN_nom.attendu`. Un exemple ajouté est aussitôt vérifié (il est exécuté avec les
  deux backends, formaté, et exposé par le serveur MCP).
- **Les propriétés** (`test_extension_17_proprietes.py`) font 30 tirages par défaut
  (profil `defaut`). Le profil `long` en fait 1 000, pour chercher plus loin : 7 min 50 s
  le 6 novembre 2026.

  ```bash
  HYPOTHESIS_PROFILE=long uv run pytest projet -k extension_17                # bash
  $env:HYPOTHESIS_PROFILE = "long"; uv run pytest projet -k extension_17     # PowerShell
  ```

- **Graphviz** : quatre tests (`test_extension_16_affichage.py`) demandent la commande
  `dot` ; sans elle, ils sont ignorés.
- **Un test sensible au démarrage à froid** : voir les *Limites connues* de
  [`NOTES.md`](../NOTES.md).

## 4. Le test de la documentation

`test_livraison_documentation.py` exécute les programmes de `README.md`, de `NOTES.md`
et de `docs/*.md` (pas ceux du journal). Un bloc de code Upea s'écrit ```` ```upea ````,
et le bloc qui le suit immédiatement dit ce qu'on attend de lui :

````markdown
```upea
faaite 6 * 7;
```

```sortie
42
```
````

| Ce qui suit le bloc `upea` | Ce que vérifie le test |
|---|---|
| un bloc ```` ```sortie ```` | le programme s'exécute et affiche exactement ce texte |
| un bloc ```` ```erreur ```` | le programme échoue, et son message est exactement ce texte (tel que `run` l'écrit, pour un fichier nommé `exemple.upea`) |
| rien de tout cela | le programme passe `check` |

Un fragment qui n'est pas un programme complet s'écrit ```` ```text ````. Un bloc
placé dans une clôture plus longue (```` ```` ````), comme celui de cette section,
n'est pas vérifié. Le test vérifie aussi que chaque lien relatif de la documentation,
journal compris, mène à un fichier qui existe.

## 5. La CI

[`.github/workflows/tests.yml`](../.github/workflows/tests.yml) est configuré pour
GitHub Actions : sous Windows et sous Linux, à chaque push et pull request, il lance
`uv sync`, pytest, mypy, `ruff check` et `ruff format --check`. Les actions sont
épinglées par commit. mypy y tourne pour la plateforme de chaque machine ; macOS se
vérifie en local, avec `--platform darwin`.

## 6. Recettes

Ces recettes ont été suivies sur une copie du projet, et les erreurs qu'elles
annoncent sont celles qu'on obtient.

### Ajouter une fonction prédéfinie

Exemple : `degre(g, v)`, le nombre d'arcs qui partent du nœud `v`.

1. **Vérifier que le nom est libre.** Une prédéfinie réserve son nom : aucune variable
   ne peut plus le porter. `git grep -nw degre -- projet` montre que
   `exemples/06_tahua.upea` emploie justement une variable `degre` : l'ajouter tel
   quel casserait cet exemple (« 'degre' est le nom d'une fonction prédéfinie »).
2. **Son type**, dans `upea/predefinies.py`, avec les patrons (`GRAPHE`, `NOEUD`,
   `ARBRE`, `VALEUR`…), à côté des fonctions de même famille :

   ```python
   signature("degre", GRAPHE, NOEUD, retour=fixe(NUMERA))
   ```

   Un typage qu'aucun patron n'exprime s'écrit à la main, avec le décorateur
   `@predefinie(nom, minimum, maximum, texte=…)`.
3. **Son code**, dans le module du prélude qui convient (`upea/execution/graphes.py`
   ici). Son nom est celui d'Upea, précédé de `_` ; le décorateur vérifie les arguments
   et lève l'erreur en termes d'Upea :

   ```python
   @_sur_graphe(1)
   def _degre(graphe: _Upea, noeud: object) -> int:
       """Le nombre d'arcs qui partent de `noeud`."""
       return len(graphe.successeurs(noeud))
   ```

4. **Ses tests** : ce qu'elle rend, et ses erreurs. Deux tests existants vérifient
   déjà que chaque prédéfinie a son code dans le prélude
   (`test_chaque_predefinie_existe_dans_le_prelude`), et que sa signature lisible suit
   son nombre d'arguments (`test_extension_18_signatures.py`).
5. **La spécification** : une ligne dans le tableau de sa famille. La spécification
   est validée par l'enseignant : la modification se note dans `NOTES.md`.

Le reste suit tout seul : la vérification des types et du nombre d'arguments, la
ressource MCP `upea://predefinies`, et les erreurs (`degre(upea {}, "X")` donne « le
nœud "X" n'est pas dans le graphe »).

### Ajouter un backend

Exemple : un backend qui compte les instructions d'un programme. Il n'hérite de rien :
il a seulement la forme du `Protocol` `Backend` (`upea/backend.py`).

1. **La classe**, dans son propre module, ou à côté des autres :

   ```python
   class Compteur:
       """Un backend d'essai : le nombre d'instructions du programme."""

       nom = "compteur"
       extension = ".txt"
       executable = False

       def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
           return Sortie(f"{len(programme.instructions)} instructions\n")
   ```

2. **Son enregistrement** : une instance de plus dans `BACKENDS`
   (`upea/compilateur.py`). La CLI le propose aussitôt
   (`--backend {ast,compteur,formateur,python}`).
3. **Les tests** : `test_les_backends_disponibles` et
   `test_un_backend_inconnu_est_refuse_avec_un_message_clair`
   (`test_etape_10_qualite.py`) listent les backends, et sont à mettre à jour.

Un backend dont le code n'est pas du Python (`executable = False`) se lance avec
`transpile`, pas avec `run` :

```bash
uv run python -m upea transpile essai.upea --backend compteur    # 2 instructions
uv run python -m upea run essai.upea --backend compteur          # code 2
```

```text
upea : le backend 'compteur' ne produit pas de Python exécutable
```

Deux limites : `transpile --prelude externe` ne vaut que pour les deux générateurs de
Python (`compilateur.importer_le_prelude`), et l'outil MCP `transpiler` n'accepte que
`python` et `ast` (le type `Backend` de `upea/serveur_mcp.py`).

### Ajouter un mot-clé

Un mot-clé touche chaque étage. Voici les endroits où apparaît `faaea` (la
`Rupture`), le modèle à suivre :

1. `upea/tokens.py` : un membre de `TokenKind`, de valeur le mot (`FAAEA = "faaea"`).
   Le lexer le reconnaît alors tout seul (`MOTS_CLES`).
2. `projet/tests/test_etape_02_tokens.py` : la liste `MOTS_CLES_ATTENDUS`.
3. `upea/noeuds.py` : la dataclass du nouveau nœud, ajoutée à l'union `Instr` (ou
   `Expr`).
4. `upea/parser.py` : une méthode, l'aiguillage de `Parser.instruction`, et, si le mot
   commence une instruction, `DEBUTS_INSTRUCTION` (la récupération d'erreurs s'y
   resynchronise).
5. `upea/semantique.py` : une variante `@instruction.register` (sans elle, l'analyse
   lève « instruction non gérée »).
6. `upea/generateur.py`, `upea/generateur_ast.py` et `upea/formateur.py` : un `case`
   dans le `match` de chacun. Les trois finissent par `assert_never` : mypy signale
   celui qui manque. Le test différentiel vérifie que les deux générateurs produisent
   le même programme.
7. La spécification : *Vocabulaire*, *Lexique* (la liste des mots-clés), *Grammaire* et
   *Sémantique*, et la trace dans `NOTES.md`.

Le mot devient réservé : `git grep -nw mot -- projet` montre les programmes qui
l'emploient comme nom.

## 7. Conventions

- Les noms (modules, fonctions, variables) et les messages sont en français ; les
  messages d'erreur parlent d'Upea, jamais de Python.
- Les noms du prélude commencent par `_` : le lexer interdit ce préfixe aux programmes.
- Les résultats des outils MCP sont des dataclasses sans `slots` : avec `slots`,
  pydantic perd leur schéma de sortie.
- La docstring d'un outil, d'une ressource ou d'un prompt MCP est sa description, lue
  par l'IA : la changer change ce que le serveur annonce.
- Un commit par changement, avec un message en français qui dit ce qui change et
  pourquoi.
