# Livraison d'Upea : plan

État de départ : commit `5e64cfa`, branche `master`.

> **Plan validé le 6 novembre 2026.** Décisions : 1a, 2a, 3a, 4a, 5a, 6a, 7a, 9a, 10a,
> 11a, 12a, 13a. **Décision 8 en attente** : la réponse contient les deux options (8a
> et 8b) ; les lots 3 et suivants attendent qu'elle soit tranchée.
>
> Précisions reçues :
> - 2a : en tête du rapport copié, « État au commit ce53700. Corrigé depuis : M1 à M6,
>   L1, L2, L4, L5, L6 (étape 3, commits dd46173 à 5e64cfa). Non traité : … », avec un
>   renvoi à `NOTES.md`.
> - 4a : le README ne dit ni que la CI tourne, ni le format de livraison ; il écrit
>   « CI configurée (GitHub Actions, Windows et Linux) ».
> - 10a : la section de l'exercice final est préparée, vide ; les observations et la
>   trace viendront de Thomas.
> - 11a : `NOTES.md` donne la taille mesurée du prélude, et la façon de la mesurer.

Sommaire : §0 état des lieux · §1 exigences du cours · §2 inventaire · §3 documentation
cible · §4 lots · §5 décisions · §6 liste de contrôle (remplie au dernier lot).

## 0. État des lieux (phase 0)

| Vérification | Commande | Résultat |
|---|---|---|
| arbre de travail | `git status --short` | vide, une fois `Claude outputs/` retiré par vous (le dossier n'était pas suivi et ne contenait que la consigne) |
| tests | `uv run pytest projet` | **1 278 réussis, 4 ignorés** en 142 s (`test_extension_16_affichage.py:265` : Graphviz n'est pas installé) |
| typage | `uv run mypy projet --platform win32`, puis `linux`, puis `darwin` | `Success: no issues found in 74 source files`, trois fois |
| style | `uv run ruff check projet` | `All checks passed!` |
| mise en forme | `uv run ruff format --check projet` | **4 fichiers** à reformater, et non 2 (voir §2.5) |

Les résultats sont conformes à ce qui était attendu. Seul écart : `ruff format` signale
quatre fichiers.

## 1. Ce que le cours attend du rendu

Sources : le dossier voisin `Python_advanced-main/`, lu sans rien y écrire. Les
chemins ci-dessous partent de ce dossier. « Écart » : ce que le projet ne fait pas, ou
fait autrement.

### 1.1 Le rendu lui-même

| # | Exigence | Source | Projet | Écart |
|---|---|---|---|---|
| R1 | Un `.zip` par jour, de ce qui a été fait | `docs/rendu.md:5`, `README.md:57` | à produire | aucun |
| R2 | Aucun format imposé : nom, contenu, arborescence | `docs/rendu.md:7-12` | — | aucun |
| R3 | Suggéré : nom et date dans le nom du fichier (`dupont_2026-11-03.zip`) | `docs/rendu.md:26` | à produire | aucun |
| R4 | Suggéré : un court `NOTES.md` (fait, reste, questions) | `docs/rendu.md:27` | `NOTES.md` existe | aucun |
| R5 | Suggéré : pas de `.venv/`, `__pycache__/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` | `docs/rendu.md:28` | `git archive` les exclut (essai : 106 fichiers, aucun cache, 335 Ko) | aucun |
| R6 | On regarde le code **et les tests écrits par l'étudiant** | `docs/rendu.md:19`, `langage/README.md:12`, `:76` | 33 fichiers de tests, 1 282 tests | aucun |
| R7 | Tout ce qui aide à comprendre la démarche est bienvenu | `docs/rendu.md:20` | `NOTES.md`, les `PLAN*.md` | à organiser (§3) |

### 1.2 Le langage

| # | Exigence | Source | Projet | Écart |
|---|---|---|---|---|
| L1 | Chaîne lexer → parser → analyse sémantique → génération, écrite à la main | `langage/README.md:9-10` | `lexer.py`, `parser.py`, `semantique.py`, `generateur.py` ; `dependencies = []` dans `pyproject.toml` | aucun |
| L2 | Spécification **validée par l'enseignant** avant le code | `langage/etapes/01_specification.md:5`, `:53` | `NOTES.md:52` et `:71` : « validée par l'enseignant le [DATE À REMPLIR] » | la date manque (à vous de la remplir) |
| L3 | Spécification d'après le gabarit : lexique, grammaire EBNF, priorités, sémantique, limites | `langage/etapes/01_specification.md:50` | `projet/specification.md`, sections *Lexique*, *Grammaire (EBNF)*, *Priorité et associativité*, *Sémantique*, *Limites assumées* | aucun |
| L4 | Au moins cinq exemples, chacun avec son `.attendu` | `langage/etapes/01_specification.md:51`, `:110` | 10 exemples, tous avec leur `.attendu` | aucun |
| L5 | Commandes : `uv run pytest projet`, `uv run mypy projet/monlangage`, `uv run ruff check projet` | `langage/README.md:68-72` | les trois passent (§0, et `mypy projet/upea` : 38 fichiers sans erreur) | aucun |
| L6 | Tests nommés `etape_NN` (langage) et `mcp_NN` (serveur), pour `-k` | `langage/gabarits/arborescence.md:68-70` | `test_etape_NN_*`, `test_extension_NN_*`, `test_conseil_*` | serveur : `-k mcp_04` → `no tests collected (1282 deselected)` ; ses tests s'appellent `test_extension_18_*` |
| L7 | CLI : `run`, `transpile [-o]`, `check` ; codes 0, 1, 3 ; `python -m` | `langage/etapes/09_cli_repl.md:77-82`, `:132-138` | les trois, plus `fmt`, `repl`, `mcp` ; codes 0, 1, 2, 3, 130 | aucun (des ajouts) |
| L8 | REPL : un générateur qui reçoit par `send` | `langage/etapes/09_cli_repl.md:83` | `repl.py` | aucun |
| L9 | `mypy --strict` sur le paquet ; en bonus, sur `projet` tests compris | `langage/etapes/10_qualite.md:62`, `:119`, `:125` | les deux | aucun |
| L10 | Au moins une extension parmi 11, 12, 13 | `langage/README.md:52-58` | les trois, plus cinq extensions propres au projet (14 à 18) | aucun |
| L11 | `transpile --sourcemap` écrit un `.map.json` | `langage/etapes/13_source_maps.md:40` | vérifié (fichier écrit) | aucun |
| L12 | Critères : spécification, chaîne de bout en bout, tests, notions Python, `mypy --strict`, extensions | `langage/README.md:87-94` | — | à rendre visibles dans `NOTES.md` (§3) |

### 1.3 Le serveur MCP

Le conseil avait déjà relevé ces écarts (rapport `council/RAPPORT-FINAL.md:32-33`, points
M7 et M8) ; l'étape 3 ne les a pas traités. Sous le gel du code, ils ne peuvent être que
**documentés** (décisions 8 à 10).

| # | Exigence | Source | Projet | Écart |
|---|---|---|---|---|
| M1 | Un second paquet `serveur_monlangage/`, lancé par `python -m serveur_monlangage` | `mcp/README.md:47-72` | le module `upea/serveur_mcp.py`, lancé par `python -m upea mcp` | fait autrement |
| M2 | Étape 1 : un serveur « bonjour » (`saluer`, `additionner`) | `mcp/etapes/01_concepts_bonjour.md:5`, `:125-137` | absent | non fait |
| M3 | Étape 2 : outils `tokenize`, `parse`, `check`, résultats en `TypedDict`, `noeud_json` | `mcp/etapes/02_analyse.md:5`, `:121-134` | `verifier` seul (l'équivalent de `check`), résultats en dataclasses | `tokenize` et `parse` absents |
| M4 | Instructions du serveur et docstrings écrites pour une IA | `mcp/etapes/02_analyse.md:81` | `INSTRUCTIONS`, docstrings des outils (`serveur_mcp.py:87`, `:168-230`) | aucun |
| M5 | Étape 3 : `transpile` (avec la source map) et `format` (avec `modifie`) | `mcp/etapes/03_transformation.md:69-82` | `transpiler` sans source map, `formater` sans champ `modifie` | fait autrement |
| M6 | Étape 4 : `run(source, delai=2.0)`, délai borné par le schéma, durée dans la réponse, statuts `delai_depasse` et `sortie_tronquee` | `mcp/etapes/04_execution.md:66`, `:80`, `:132` | `executer(source, types, backend)` : délai fixe de 5 s, pas de durée ; délai dépassé = erreur d'outil ; troncature = champ `tronquee` | fait autrement |
| M7 | Étape 4 : environnement réduit du fils, et un test qui le prouve | `mcp/etapes/04_execution.md:75`, `:135` | `bac_a_sable.py:185` copie **tout** `os.environ` (sauf `FORCE_COLOR`) | non fait (voir §2.9) |
| M8 | Étape 4 : un context manager qui tue le fils et ferme ses tubes | `mcp/etapes/04_execution.md:79` | `Popen` + `communicate(timeout)`, `kill` sur délai dépassé, plafond de temps CPU dans le fils | fait autrement |
| M9 | Étape 4 : la discussion de sécurité dans la docstring du module de bac à sable | `mcp/etapes/04_execution.md:30`, `:83` | la docstring de `bac_a_sable.py` décrit le mécanisme, pas les risques | partiel : comblé au lot 3 (docstring seulement) |
| M10 | Étape 5 : ressources spécification et exemples, traversée de chemin refusée ; prompts `ecrire_programme` et `corriger_programme` | `mcp/etapes/05_ressources_prompts.md:113-127` | ressources et refus faits (`test_pas_de_chemin_dans_un_nom_d_exemple`) ; prompts `ecrire_programme` et `traduire_depuis_python` | `corriger_programme` absent |
| M11 | Étape 6 : le vrai point d'entrée testé en stdio | `mcp/etapes/06_integration.md:48-49`, `:113` | `test_de_bout_en_bout_avec_le_client_du_sdk`, `test_de_bout_en_bout_en_json_rpc` | aucun |
| M12 | `projet/mcp.exemple.json`, et un test qui le valide | `mcp/etapes/06_integration.md:77`, `:114` | absent (la configuration est dans le README) | non fait (décision 9) |
| M13 | Le scénario de l'exercice final, écrit comme un test | `mcp/etapes/06_integration.md:78`, `:115` | absent | non fait |
| M14 | L'exercice final réel : observations dans `NOTES.md`, trace de la session dans le rendu | `mcp/etapes/06_integration.md:79-84`, `:121` | absent | **à faire par vous** (décision 10) |

### 1.4 L'usage d'un assistant IA

Les consignes n'en disent rien. Recherche dans `langage/`, `mcp/`, `docs/` et
`README.md` du cours (`IA`, `assistant`, `Claude`, `ChatGPT`, `Copilot`, `déclar…`) :
l'IA n'y apparaît que comme sujet du projet MCP. Le conseil posait déjà la question
(`council/RAPPORT-FINAL.md`, Q10). Côté dépôt, 39 des 44 commits portent la ligne
`Co-Authored-By: Claude`. Voir la décision 6.

## 2. Inventaire du dépôt

### 2.1 Fichiers de la racine

`git ls-files` : 106 fichiers suivis.

| Fichier ou dossier | Suivi | Rôle | Proposition |
|---|---|---|---|
| `README.md` | oui | présentation, commandes, serveur MCP, qualité | réécrit (lot 6) |
| `NOTES.md` | oui | document de rendu pour l'enseignant | réécrit (lot 7) |
| `PLAN.md` | oui | plan de l'audit, état au commit `9dc63d7` (3 nov.), à la 2e personne | `docs/journal/` (lot 1) |
| `PLAN_MCP.md` | oui | plan du serveur MCP, état au commit `c9a5961` (4 nov.) | `docs/journal/` (lot 1) |
| `PLAN_ETAPE3.md` | oui | plan des corrections du conseil, état au commit `6d64da9` (6 nov.) | `docs/journal/` (lot 1) |
| `pyproject.toml`, `uv.lock`, `.python-version` | oui | environnement (Python 3.12, aucune dépendance du langage) | inchangés |
| `.gitignore`, `.gitattributes` | oui | caches ignorés ; fins de ligne LF | inchangés |
| `.github/workflows/tests.yml` | oui | CI : pytest, mypy, ruff, sous Windows et Linux | inchangé, sauf décision 1 (a) |
| `projet/` | oui | spécification, exemples, paquet `upea`, tests | voir lots 2 à 5 |
| `council/` | non (`.git/info/exclude:7`) | rapport du conseil : 41 fichiers, 596 Ko, dont `round-2/debat.md` (136 Ko) | décision 2 ; jamais modifié |
| `.claude/agents/upea-council/` | non (`.git/info/exclude:8`) | les six agents du conseil | hors du rendu ; jamais modifié |
| `.venv/`, `.hypothesis/`, `.mypy_cache/`, `.pytest_cache/`, `.ruff_cache/` | non (`.gitignore`) | générés | rien à faire |

Le dépôt n'a **aucun dépôt distant** (`git remote -v` est vide) : la CI n'a donc jamais
tourné. Le README dit pourtant qu'elle « lance pytest, mypy et ruff … à chaque push »
(décision 4).

### 2.2 Code mort

Méthode, sans outil nouveau : un script jetable (bibliothèque standard, hors du dépôt)
énumère les fonctions, classes, méthodes, constantes et alias de `projet/upea`. Pour
chacun, il compte ses jetons `NAME` dans **tous** les `.py` suivis, tests compris, et
ses occurrences dans les textes (jetons `STRING`). Chaque candidat est ensuite vérifié
par `git grep -w` sur tout le dépôt, Markdown compris. `ruff check --select
F401,F811,F841` (imports, redéfinitions, variables inutilisés) : aucune erreur.

**Les faux positifs, et pourquoi ils sont vivants.** Ces noms n'apparaissent qu'une fois
dans le code, à leur définition, mais ils sont appelés autrement :

| Mécanisme | Noms | Preuve |
|---|---|---|
| appel par nom depuis le code généré (`f"_{nom}"`) | `_amui`, `_tatara`, `_roto`, `_iriti`, `_iti`, `_rahi`, `_numera`, `_tuhaa`, `_parau`, `_parcours`, `_taati`, `_pihai`, `_motu`, `_teiaha`, `_tae`, `_bfs`, `_dfs`, `_cycle`, `_biparti`, `_equilibre`, `_affiche` | `prelude.py:136` (`f"_{nom}" if nom in PREDEFINIES`) |
| constructeurs des littéraux d'arbres ordonnés | `_imi`, `_aifaito`, `_uteere`, `_ahu`, `_ahunui` | `generateur.py:163`, `generateur_ast.py:266` (`f"_{sorte}"`) |
| enregistrés par `@prefixe` / `@infixe` | `_decimal`, `_booleen`, `_rien`, `_variable`, `_groupe`, `_liste`, `_moins`, `_eiaha`, `_collection`, `_comparaison`, `_champ` | `parser.py:139` et suivantes |
| enregistrés par `@regle` | `_logique`, `_egalite`, `_ordre`, `_appartenance`, `_plus` | `semantique.py:764`, `:781-838` |
| protocole d'`io.TextIOBase` | `_SortiePlafonnee.writable` | `bac_a_sable.py:203` (la classe hérite de `io.TextIOBase`, dont `writable()` rend `False`) |
| fixture `autouse`, visiteur `ast.NodeTransformer` | `sans_couleurs`, `_Aplatir.visit_BoolOp` | `conftest.py:24`, `outils.py:32` |

Les modules sont tous importés : chacun l'est au moins deux fois, et les modules du
prélude sont listés dans `prelude.MODULES`. Aucun `getattr` sur un nom calculé ne
touche les candidats (`git grep -nE "getattr\([^,]+, *f?[\"']"` : trois appels, sans
rapport). Il n'y a pas d'`import *` du paquet, ni de `__all__` hors du prélude externe.

**Le code mort prouvé.**

| Nom | Endroit | Preuve de non-usage | Depuis quand |
|---|---|---|---|
| `ligne_fautive(exc, cartes)` | `compilateur.py:265-268` | `git grep -n ligne_fautive` : sa définition, et deux mentions dans `PLAN_ETAPE3.md:649`, `:654` | `git log -S` : son dernier appel a disparu au commit `d2e437b` (M1), remplacé par `lignes_du_programme` |
| `Emetteur.nombre_de_lignes` (propriété) | `emetteur.py:52-54` | `git grep -n nombre_de_lignes` : sa seule définition | depuis `bbca8d1` (v0) |
| `type Noeud = Expr \| Instr \| …` | `noeuds.py:287` | `git grep -nw Noeud` : sa seule définition ; `parcourir`, `sous_noeuds` et `afficher_arbre` sont annotés `object` | depuis `bbca8d1` |

**Le code commenté** : `ruff check projet --select ERA001` : aucun.

### 2.3 Marqueurs et commentaires périmés

- `TODO`, `FIXME`, `XXX`, `HACK` : aucun dans les fichiers suivis (`git ls-files | xargs
  grep -nE "\b(TODO|FIXME|XXX|HACK)\b"`).
- `breakpoint()`, `pdb` : aucun.
- `print` (`ruff check --select T20`) : 9 dans `projet/upea`, tous voulus. Ce sont la
  sortie de `faaite` (`execution/base.py:243`, `:245`), les messages et la boucle de la
  CLI (`cli.py:36`, `:191`, `:219-230`) et l'avertissement de l'enfant sur stderr
  (`bac_a_sable.py:354`). Un dans les tests, voulu lui aussi : il est dans le programme
  d'un sous-processus (`test_conseil_m6_interruption.py:19`).
- Commentaires périmés dans le code : aucun trouvé. Toutes les docstrings de module ont
  été relues et décrivent le code actuel. Un fichier cité (`execution.py`) n'existe plus,
  mais seulement dans `NOTES.md:59`. La mention de `compilateur.py:292` est
  `test_etape_08_execution.py`, qui existe.
- Approximations qui ont vieilli : « environ 2 500 lignes » pour le prélude, dans
  `specification.md:511`, dans `NOTES.md:116`, et dans deux descriptions lues par l'IA
  (`serveur_mcp.py:76`, `:220`). Mesure : un fichier produit par `transpile` sans
  option fait 2 680 lignes, dont 26 pour le programme ; `upea_prelude.py` en fait 2 851
  (son `__all__` compris). Voir la décision 11.

### 2.4 Docstrings

Mesure : `ruff check projet/upea --select D100,D101,D102,D103,D104` (règles lues
ponctuellement, la configuration n'est pas modifiée).

| Règle | Manquantes | Où |
|---|---|---|
| D100, D104 (modules, paquets) | 0 | — |
| D101 (classes publiques) | 56 | `noeuds.py` 26 (les nœuds de l'AST), `erreurs.py` 5, `atelier.py` 3, `bac_a_sable.py` 3, `symboles.py` 3, `backend.py` 2, `parser.py` 2, `sourcemap.py` 2, et 1 dans chacun de `compilateur`, `emetteur`, `flux`, `formateur`, `generateur_ast`, `predefinies`, `repl`, `semantique`, `tokens`, `typage` |
| D102 (méthodes publiques) | 51 | `parser.py` 17, `semantique.py` 14, `sourcemap.py` 6, `symboles.py` 5, `emetteur.py` 2, et 1 dans chacun de `backend`, `flux`, `formateur`, `generateur`, `generateur_ast`, `predefinies`, `tokens` |
| D103 (fonctions publiques) | 19 | `cli.py` 8, `typage.py` 6, `formateur.py` 2, `atelier.py` 1, `compilateur.py` 1, `predefinies.py` 1 |

Les modules du prélude (`execution/`) ne nomment que des noms en `_` : ruff ne les
compte pas.

**Trois pièges, vérifiés, qui fixent ce qu'il ne faut pas toucher :**

1. **La docstring d'une dataclass rendue par un outil MCP part dans le `outputSchema`.**
   Un script jetable qui appelle `client.list_tools()` montre, pour les quatre outils, `$defs →
   Diagnostic → description : "Une erreur ou un avertissement ; …"`. Ajouter une
   docstring à `Verification`, `Transpilation`, `Formatage` (`atelier.py:51-69`) ou
   `Execution` (`bac_a_sable.py:56`) changerait ce que le serveur annonce. Aucun test ne
   le verrait : `test_extension_18_mcp.py:222` vérifie seulement que le schéma existe.
   Ces quatre classes restent sans docstring, et sont décrites dans `docs/mcp.md`.
2. **La docstring d'un outil, d'une ressource ou d'un prompt est sa description**
   (`serveur_mcp.py:157`, `:286`, `:473`). Aucune n'est modifiée.
3. **Les modules du prélude sont recopiés dans chaque fichier généré.** Une docstring
   ajoutée dans `execution/` changerait la sortie de `transpile`. On n'y touche pas.

Docstrings qui ne correspondent plus au code : aucune trouvée dans les docstrings de
module. Les approximations sur la taille du prélude sont traitées en §2.3. Les
docstrings de fonctions seront relues une à une pendant le lot 3.

### 2.5 Mise en forme

`uv run ruff format --check projet` (ruff 0.17.3, la version de `uv.lock`) signale quatre
fichiers. `ruff format --diff` : **10 lignes retirées, 6 ajoutées**.

| Fichier | Changement | Dernière modification |
|---|---|---|
| `projet/upea/prelude.py:99` | un `case A \| B(...)` mis entre parenthèses | `ff3f41e` (4 nov., avant l'étape 3) |
| `projet/upea/repl.py:105` | un appel ramené sur une ligne | `85e6434` (étape 3) |
| `projet/upea/execution/base.py:114` | un `raise _Erreur(...)` ramené sur une ligne | `039fc23` (étape 3) |
| `projet/tests/test_conseil_l6_bac_cli.py:139` | deux textes collés en un seul | `498adfe` (étape 3) |

`execution/base.py` fait partie du prélude. Le reformater raccourcit de deux lignes le
fichier produit par `transpile`, sans en changer le code. Voir la décision 1.

### 2.6 La documentation existante, affirmation par affirmation

Chaque commande a été exécutée telle quelle, depuis le dossier indiqué. Les fichiers
produits sont allés dans un dossier temporaire, hors du dépôt.

**README.md**

| Ligne | Affirmation | Vérification | Verdict |
|---|---|---|---|
| 14-52 | l'exemple et sa sortie | programme extrait et lancé avec `python -m upea run` : sortie identique ligne à ligne | exact |
| 62-65 | `uv sync` installe Python 3.12, les outils et le SDK ; Upea sans dépendance | `pyproject.toml` : `dependencies = []`, groupe `dev` qui inclut `mcp` | exact (une coupure de ligne bizarre, « Depuis\n`projet/` ») |
| 68 | `run exemples/05_motu.upea` | code 0, sortie identique à `05_motu.attendu` | exact |
| 69 | `check exemples/06_tahua.upea` | `exemples/06_tahua.upea : aucune erreur`, code 0 | exact |
| 70, 76 | `transpile … -o fibo.py`, puis `python fibo.py` | code 0 ; le fichier (2 680 lignes) se lance seul | exact |
| 71 | `fmt exemples/04_tumu.upea` | code 0 | exact |
| 72 | `repl` | bannière, `upea> 42`, sortie propre en fin d'entrée, code 0 | exact |
| 73 | `mcp` | `uv run --directory <dépôt>/projet python -m upea mcp`, lancé depuis un autre dossier : silencieux, code 0 à la fermeture de l'entrée | exact |
| 77 | `--prelude externe` : « quelques dizaines de lignes » | 26 lignes, à côté d'un `upea_prelude.py` ; se lance | exact |
| 86-94 | ressources, outils, prompts | `list_tools` donne `verifier`, `formater`, `transpiler`, `executer` ; les tests listent les ressources et les prompts | exact |
| 91-92 | 5 s, 512 Mo, 64 Kio, deux fois le délai en CPU | `DELAI = 5.0`, `PLAFOND_MEMOIRE = 512 * 1024**2`, `PLAFOND = 64 * 1024`, `MULTIPLE_CPU = 2` (`bac_a_sable.py:33-41`) | exact |
| 98 | `uv sync --no-dev --group mcp` | non rejoué, pour ne pas modifier le `.venv` | à vérifier sur le clone neuf (lot 13) |
| 109-118 | `claude mcp add …`, `/mcp`, `@upea:…` | `claude` n'est pas dans le `PATH` de cette machine | non vérifiable ici |
| 125-137 | configuration de Claude Desktop, journaux | Claude Desktop n'est pas lancé ici | non vérifiable ici |
| 139-145 | MCP Inspector, Node ≥ 22.19 | `npx` est installé ; non lancé, car il télécharge un paquet npm | vérifiable au lot 13 si vous l'acceptez |
| 152 | « 1 278 tests (4 de plus avec Graphviz installé) » | 1 278 réussis, 4 ignorés pour Graphviz | exact |
| 153 | `mypy projet/upea`, strict, « passe aussi sur les tests » | 38 fichiers, puis 74 avec `projet` | exact |
| 160 | « Les 10 programmes d'`exemples/` » | 10 `.upea`, 10 `.attendu` | exact |
| 170-172 | GitHub Actions à chaque push et pull request ; mypy `--platform darwin` | le fichier le prévoit, mais **aucun dépôt distant** : jamais exécuté ; `darwin` vérifié en §0 | à reformuler (décision 4) |
| liens | `projet/specification.md`, `NOTES.md`, `.github/workflows/tests.yml` | les trois existent | exact |

**NOTES.md**

| Ligne | Affirmation | Vérification | Verdict |
|---|---|---|---|
| 8-14 | l'exemple | se lance : `on atteint` ×3, puis la liste | exact (sans sortie écrite) |
| 21-23 | commandes de qualité | voir README | exact |
| 26-28 | profils `defaut` (30 tirages) et `long` (1 000), « une dizaine de minutes » | `conftest.py:19-21` ; `HYPOTHESIS_PROFILE=long uv run pytest projet -k extension_17` : `5 passed, 1277 deselected in 469.62s (0:07:49)` | exact (ordre de grandeur) |
| 38-45 | commandes depuis `projet/` (dont `--backend ast`, `--sourcemap`) | toutes de code 0 ; `fibo.py.map.json` écrit | exact |
| 52, 71 | « [DATE À REMPLIR] », deux fois | — | **à remplir par vous** ; laissé tel quel |
| 57 | récupération d'erreurs, « limite de 20 » | `MAX_ERREURS = 20` (`parser.py:62`) | exact |
| 59 | « `execution.py` (prélude) » | c'est le paquet `execution/` depuis la refonte | **périmé** |
| 69 | lien vers `PLAN_MCP.md` ; « 5 s, 64 Kio, 512 Mo, deux exécutions à la fois » | lien valide aujourd'hui ; `EXECUTIONS_SIMULTANEES = 2` | exact, mais le lien casse au lot 1 (corrigé dans le même lot) |
| 73 | « rapport du commit `ce53700` » | le commit existe ; le rapport est dans `council/`, **hors du dépôt** | invérifiable pour un lecteur (décision 2) |
| 81-82 | 20 000 appels imbriqués | `_PROFONDEUR_MAX = 20_000` (`execution/base.py:23`) | exact |
| 94-104 | notions Python mobilisées | chaque décorateur et outil cité existe (`_sorte_upea`, `_attend`, `_sur_graphe`, `regle`, `predefinie`, `prefixe`, `infixe`, `singledispatchmethod`, `reduce`, `cache`, `pairwise`, `count`, `product`, `chain.from_iterable`, `operator.lt`, `key=lambda arete: arete[2]`) | exact, sauf la citation `signature("tarjan", GRAPHE, retour=lambda t: tapura(tapura(t)))` : le code l'écrit dans une boucle `for _nom in ("composantes", "tarjan")` (`predefinies.py:287-288`) |
| 116 | « environ 2 500 lignes » | 2 680 (voir §2.3) | approximation datée |
| 134 | démarrage de Python : « 0,3 à 0,7 s ici » | six exécutions de `faaite 1;` par le bac à sable : 0,36 à 0,85 s, avec la mesure `hypothesis` qui tournait en même temps | plausible ; à remesurer machine au repos |
| 136 | nom du test qui échoue parfois à froid | `test_extension_18_bac_a_sable.py:20` existe | exact |

**Liens internes** de `README.md`, `NOTES.md`, `specification.md` et des `PLAN*.md` : tous
valides aujourd'hui. Les `PLAN*.md` n'ont aucun lien relatif : les déplacer n'en casse
aucun.

### 2.7 Les chiffres écrits à plusieurs endroits

| Chiffre | Valeur mesurée | Écrit dans | Proposition |
|---|---|---|---|
| nombre de tests | 1 278 réussis + 4 ignorés = 1 282 | `README.md:152` | un seul endroit (README, section Qualité), avec la commande qui le mesure ; les autres documents y renvoient |
| nombre d'exemples | 10 | `README.md:160`, `specification.md:487-498` (la table) | la spécification fait foi ; le README dit « les programmes d'`exemples/` » sans les compter |
| taille du prélude | 2 654 lignes recopiées (2 680 − 26) ; 2 851 pour `upea_prelude.py` | `specification.md:511`, `NOTES.md:116`, `serveur_mcp.py:76`, `:220` | décision 11 |
| limites du bac à sable | 5 s, 512 Mo, 64 Kio, CPU ×2, deux à la fois | `README.md:91`, `NOTES.md:69`, `:134-135`, `serveur_mcp.py:247-257` | une seule table, dans `docs/mcp.md`, avec le nom de chaque constante ; README et NOTES y renvoient |
| récursion | 20 000 | `specification.md:411`, `:528`, `NOTES.md:81-82`, `compilateur.py:254` | la spécification fait foi |
| lignes de code | `wc -l` : 8 799 (`projet/upea`), 6 802 (`projet/tests`) | nulle part dans la documentation (8 357 dans le rapport du conseil, au commit `ce53700`) | ne pas l'écrire, ou une seule fois, dans `docs/architecture.md`, avec la commande |

### 2.8 `[DATE À REMPLIR]`

Deux occurrences dans `NOTES.md` : ligne 52 (tableau d'avancement, étape 1) et ligne 71
(titre de la section des modifications). Elles restent telles quelles. La réécriture
de `NOTES.md` les garde à leur place, avec un `<!-- À RELIRE PAR THOMAS -->` à côté.

### 2.9 Anomalies relevées (aucune corrigée)

Rien qui contredise la spécification. Trois points à vous signaler :

1. **L'enfant du bac à sable hérite de tout l'environnement du serveur**
   (`bac_a_sable.py:182-193`, `dict(os.environ)`), contre la consigne
   `mcp/etapes/04_execution.md:75`. Aujourd'hui, un programme Upea ne peut pas lire une
   variable d'environnement : le langage n'a ni import, ni accès au système, et les noms
   en `_` lui sont interdits. Je le vérifierai par l'essai au lot 3, avant de l'écrire
   dans la docstring du module. Si un jour une faille de génération laissait passer du
   Python arbitraire, le fils verrait les secrets du serveur (jetons d'API d'un hôte
   MCP, par exemple). Le conseil a vérifié que `{PYTHONPATH, PYTHONUTF8}` suffit sous
   Windows (`council/RAPPORT-FINAL.md:33`).
2. **Les sélecteurs du cours pour le serveur ne trouvent rien** (`-k mcp_02` … `-k
   mcp_06` : `no tests collected`) ; `-k mcp` en trouve 45, `-k extension_18` les trouve
   tous. À documenter.
3. **La CI n'a jamais tourné** (pas de dépôt distant). Les versions épinglées des actions
   (`actions/checkout` v7.0.1, `astral-sh/setup-uv` v10.3.3) n'ont donc jamais été
   essayées.

## 3. La documentation cible

### 3.1 Organisation

Votre proposition, avec quatre retouches : la table de correspondance avec le cours dans
`NOTES.md` ; un emplacement réservé, mais vide, pour l'exercice final MCP ; les limites du
bac à sable dans `docs/mcp.md` seul ; un test qui vérifie aussi les liens internes.

| Document | Public | Contenu |
|---|---|---|
| `README.md` | tout le monde, première lecture | ce qu'est Upea en trois phrases, un exemple et sa sortie (testés), installation, commandes, plan de la documentation, qualité (le seul endroit où le nombre de tests est écrit) |
| `NOTES.md` | l'enseignant | document de rendu : avancement, correspondance avec le cours (langage et MCP), choix à signaler, limites, modifications depuis la validation, notions Python mobilisées, exercice final (à remplir par vous), usage d'un assistant IA (brouillon à réécrire) |
| `projet/specification.md` | référence du langage | **inchangée** (décision 11) |
| `docs/tutoriel.md` | quelqu'un qui veut apprendre Upea | une progression pas à pas, avec des exercices et leurs solutions (testées) ; renvoie à la spécification |
| `docs/architecture.md` | un développeur, le jury | la chaîne, un schéma Mermaid, le rôle de chaque module, les choix de conception et leur raison |
| `docs/developpement.md` | un contributeur | environnement, vérifications, organisation des tests, CI, test de la documentation, recettes |
| `docs/mcp.md` | un utilisateur du serveur MCP | outils, ressources, prompts, bac à sable, branchement (déplacé du README), dépannage |
| `docs/journal/` | traçabilité | `index.md` (l'historique), les trois `PLAN*.md` avec leur en-tête, et le rapport du conseil si vous l'acceptez |

### 3.2 Plan de chaque document

**`README.md`**
1. Upea (trois phrases : ce que c'est, son idée, à quoi il sert)
2. Un exemple (le programme des îles et sa sortie, marqués pour le test)
3. Installation (prérequis : uv ; récupérer le projet ; `uv sync` ; vérifier)
4. Premiers pas (`run`, `check`, `transpile`, `fmt`, `repl`, `mcp`, une ligne chacun)
5. La documentation (une table : document, pour qui, ce qu'on y trouve)
6. Qualité (les commandes, et ce qu'elles donnent aujourd'hui, avec la date de la mesure)
7. In English (selon la décision 5)

**`NOTES.md`**
1. En bref (une phrase et les liens)
2. Avancement, étape par étape (le tableau actuel, corrigé : `execution/` au lieu de
   `execution.py`)
3. Correspondance avec le cours : langage (étapes 1 à 13), puis serveur MCP (étapes 1
   à 6 : fait, remplacé ou absent, et pourquoi ; les sélecteurs `-k` qui marchent)
4. Choix à signaler (repris de l'actuel)
5. Limites connues (repris ; renvoi à *Limites assumées* de la spécification)
6. Modifications depuis la validation de la spécification (le tableau actuel, tel quel,
   et `[DATE À REMPLIR]`)
7. Notions Python mobilisées (repris, la citation de `signature` corrigée)
8. Exercice final MCP (`<!-- À REMPLIR PAR THOMAS -->` : la session, ses observations,
   le lien vers sa trace)
9. Usage d'un assistant IA (`<!-- À RELIRE PAR THOMAS -->`, selon la décision 6)
10. Pour vérifier (renvoi au README, et à la liste de contrôle de livraison)

**`docs/tutoriel.md`** (chaque leçon : une explication courte, un exemple qui tourne, un
exercice, sa solution dans un bloc `<details>`, et le lien vers la section de la
spécification)
0. Installer, et lancer un premier fichier
1. Afficher et nommer (`faaite`, `tuu`, `tamau`, commentaires)
2. Valeurs et opérateurs (nombres, textes, booléens, priorités)
3. Décider et répéter (`ahani`, `tamau tia`, `tataitahi … roto`, intervalles)
4. Fonctions (`ohipa`, `hoi`, annotations de types)
5. Listes (`tapura`)
6. Arbres (`tumu`, `hotu`, `amaa`, parcours en profondeur et en largeur)
7. Graphes (le littéral `upea`, `mai … aano`, plus courts chemins)
8. Arbres ordonnés (ABR, AVL, rouge-noir, arbre B, tas)
9. Dessins et exports (`faaite` d'une structure, `hohoa`, `dot`, `mermaid`)
10. Lire un message d'erreur (lexicale, syntaxe, sémantique, type, exécution)
11. Le REPL
12. Pour aller plus loin (les exemples, la spécification, le serveur MCP)

**`docs/architecture.md`**
1. Vue d'ensemble (schéma Mermaid : source → `lexer` → `parser` → `semantique` →
   backends → Python → exécution ; à côté, le prélude, la CLI, le REPL, l'atelier, le bac
   à sable, le serveur MCP)
2. Du texte aux tokens (`tokens`, `flux`, `lexer`)
3. Des tokens à l'arbre (`noeuds`, `parser` : Pratt, descente récursive, récupération
   d'erreurs, limites d'imbrication)
4. Noms et types (`symboles`, `semantique`, `typage`, `predefinies`)
5. Les backends (`backend` et son `Protocol`, `generateur` et `emetteur`,
   `generateur_ast`, `formateur`)
6. Le prélude (`execution/`, `prelude` : concaténation, préfixe `_`, `--prelude
   externe`)
7. Exécuter et rapporter les erreurs (`compilateur`, `sourcemap`, traduction des
   exceptions)
8. CLI et REPL (`cli`, `repl`)
9. Le serveur MCP (`serveur_mcp`, `atelier`, `bac_a_sable`)
10. Rôle de chaque module (une table : module, rôle, étape du cours, fichier de tests)
11. Choix de conception, et leur raison (une table)

**`docs/developpement.md`**
1. Environnement (uv, Python 3.12, `uv sync`, le cas d'un `uv` hors du `PATH`)
2. Les vérifications (pytest, mypy sur trois plateformes, ruff, et `ruff format`
   selon la décision 1)
3. Les tests (organisation des fichiers et de leurs noms, `outils.py`, `generateurs.py`,
   les fixtures, les profils `hypothesis`, les tests qui demandent Graphviz)
4. Le test de la documentation (la convention du §3.3)
5. La CI (`tests.yml`)
6. Recettes : ajouter une fonction prédéfinie ; ajouter un mot-clé ; ajouter un backend
   (chacune : les fichiers à toucher, dans l'ordre, et les tests à écrire)
7. Conventions (noms en français, préfixe `_` du prélude, messages d'erreur)

**`docs/mcp.md`**
1. Ce que fait le serveur
2. Installer (le groupe `mcp`)
3. Les outils (une table : nom, paramètres, résultat, quand c'est une erreur d'outil ;
   les champs de `Verification`, `Transpilation`, `Formatage`, `Execution`)
4. Les ressources
5. Les prompts
6. Le bac à sable (la table des limites, avec leurs constantes ; ce qu'il protège, et ce
   qu'il ne protège pas)
7. Brancher le serveur (Claude Code, Claude Desktop, MCP Inspector)
8. Dépannage
9. Écarts avec le projet MCP du cours (renvoi à `NOTES.md`)

**`docs/journal/index.md`**
1. À quoi sert ce dossier
2. Chronologie, d'après `git log` : v0 à v1.1 (3 nov.) ; audit et `PLAN.md` (3-4 nov.) ;
   serveur MCP et `PLAN_MCP.md` (4 nov.) ; CI (5 nov.) ; conseil (5 nov.) ; corrections
   L1 à M6 et `PLAN_ETAPE3.md` (5-6 nov.) ; livraison (6 nov.)
3. Les documents, et le commit où chacun s'arrête
4. Le conseil (selon la décision 2)

### 3.3 Le test de la documentation

**Convention.** Les blocs de code Upea s'écrivent ```` ```upea ````. Le bloc qui suit
immédiatement (seules des lignes vides entre les deux) dit ce qu'on attend :

````markdown
```upea
faaite 6 * 7;
```

```sortie
42
```
````

| Forme | Ce que vérifie le test |
|---|---|
| ```` ```upea ```` suivi de ```` ```sortie ```` | le programme s'exécute (comme `run`) et affiche exactement ce texte |
| ```` ```upea ```` suivi de ```` ```erreur ```` | le programme échoue, et le message (tel que `run` l'écrit sur stderr, pour un fichier nommé `exemple.upea`) est exactement ce texte |
| ```` ```upea ```` seul | le programme passe `check` : aucun extrait de la documentation n'est faux |
| ```` ```text ````, ```` ```bash ````, etc. | rien : fragments, sessions du REPL, commandes (vérifiées à la main au lot 13) |

**Le test**, `projet/tests/test_livraison_documentation.py` :
- il lit `README.md`, `NOTES.md` et `docs/*.md` (pas `docs/journal/`, dont les plans
  citent d'anciens états du langage) ;
- un cas par bloc, nommé `fichier:ligne`, pour qu'un échec désigne la ligne de la
  documentation ;
- il vérifie que le README contient au moins un bloc testé, pour qu'un marquage perdu ne
  passe pas inaperçu ;
- il vérifie aussi que chaque lien relatif de ces fichiers, et de `docs/journal/`, mène à
  un fichier qui existe ;
- il passe par la façade (`compiler`, `executer`) et par `formater`, comme les autres
  tests, sans sous-processus.

Il ne remplace pas les tests des exemples : `exemples/*.attendu` reste la référence du
langage.

## 4. Les lots

Après chaque lot : `uv run pytest projet`, `uv run mypy projet --platform win32`
(puis `linux` et `darwin`), `uv run ruff check projet`, tout vert, puis un commit en
français. Le test de la documentation arrive **avant** les documents (lot 5), au lieu
d'arriver à la fin : chaque document est ainsi vérifié dès qu'il est écrit.

| Lot | Travail | Fichiers touchés | Supprimé ou déplacé, et preuve que c'est sans risque | Risques |
|---|---|---|---|---|
| 1. Nettoyage de la racine | `git mv` des trois `PLAN*.md` vers `docs/journal/`, chacun précédé d'une ligne « Document de travail, état au commit X, plus tenu à jour » ; le lien de `NOTES.md:69` corrigé | `PLAN.md`, `PLAN_MCP.md`, `PLAN_ETAPE3.md`, `NOTES.md` | aucun fichier de `projet/`, `.github/` ni `pyproject.toml` ne cite les plans (`git grep -n PLAN -- projet .github pyproject.toml` : rien) ; les plans n'ont pas de lien relatif ; seul `NOTES.md:69` pointe vers l'un d'eux | aucun (`git log --follow` garde l'historique) |
| 2. Code mort | supprimer `ligne_fautive`, `Emetteur.nombre_de_lignes` et l'alias `Noeud` (selon la décision 7) | `compilateur.py`, `emetteur.py`, `noeuds.py` | §2.2 | un usage invisible au `grep` : écarté par l'inventaire des usages dynamiques ; tests et mypy le confirment |
| 3. Docstrings | ajouter les docstrings publiques manquantes (§2.4), dans le style du projet (une phrase, un nom, des `` ` `` ; un nœud de l'AST = la construction Upea qu'il représente ; une méthode du parser = sa règle EBNF) ; la discussion de sécurité dans la docstring de `bac_a_sable.py`, chaque affirmation vérifiée par un essai | 20 modules de `projet/upea` hors `execution/` | rien | **les trois pièges du §2.4** : 4 classes, les fonctions des outils et `execution/` sont exclus ; environ 120 docstrings, soit 300 à 400 lignes : si cela déborde, je m'arrête |
| 4. Mise en forme | `ruff format projet`, et selon la décision 1, `ruff format --check projet` dans la CI et dans `docs/developpement.md` | les 4 fichiers du §2.5 (`tests.yml`) | rien | le fichier produit par `transpile` perd deux lignes (`execution/base.py`), sans changer de code ; les tests le confirment |
| 5. Test de la documentation | le test du §3.3 ; marquer l'exemple du README (`upea`, `sortie`) | `projet/tests/test_livraison_documentation.py`, `README.md` | rien | fins de ligne et encodage sous Windows : le test compare des `str`, sans console |
| 6. README | réécriture (§3.2) | `README.md` | rien : la section sur le branchement MCP reste dans le README jusqu'au lot 11, qui la déplace dans `docs/mcp.md` | inventer une sortie : chaque bloc `upea` est testé |
| 7. NOTES | réécriture (§3.2) | `NOTES.md` | rien n'est retiré sans être repris ou déplacé | écrire à votre place : tout ce qui vous engage est marqué `<!-- À RELIRE PAR THOMAS -->` |
| 8. Architecture | `docs/architecture.md` | nouveau fichier | — | un schéma faux : chaque flèche correspond à un import réel (vérifié par `git grep`) |
| 9. Tutoriel | `docs/tutoriel.md` | nouveau fichier | — | le plus gros lot de rédaction ; si cela dépasse environ 600 lignes, je m'arrête pour vous montrer la moitié faite |
| 10. Développement | `docs/developpement.md` | nouveau fichier | — | une recette fausse : chacune est suivie sur une copie jetable du dépôt (hors du dépôt), puis la copie est supprimée |
| 11. MCP | `docs/mcp.md` ; le README ne garde qu'un paragraphe et un lien ; `projet/mcp.exemple.json` et son test selon la décision 9 | `docs/mcp.md`, `README.md`, peut-être `projet/mcp.exemple.json` et un test | la section MCP du README, recopiée dans `docs/mcp.md` avant d'être réduite | rien |
| 12. Journal | `docs/journal/index.md` ; le rapport du conseil copié selon la décision 2 | `docs/journal/` | `council/` reste intact : on copie, on ne déplace pas | le rapport cite `round-1/`, `round-2/` : une ligne en tête précise ce qui est livré |
| 13. Vérification de livraison | un clone neuf dans `%TEMP%`, hors du dépôt, puis les commandes d'installation du README telles qu'écrites, les tests et un exemple ; puis la même chose depuis l'archive `.zip` si la décision 4 la retient ; tous les liens ; la liste de contrôle du §6 ; ce qui reste de votre côté ; ce plan déplacé selon la décision 12 | `PLAN_LIVRAISON.md` | les dossiers temporaires, supprimés à la fin | `uv sync` sur le clone télécharge des paquets (réseau) ; `uv` hors du `PATH` ici : j'utiliserai son chemin complet, et je le noterai |

## 5. Les décisions qui vous reviennent

Chaque question est fermée ; la recommandation est en premier.

1. **`ruff format`** (4 fichiers, 10 lignes retirées et 6 ajoutées, §2.5)
   - (a) **l'appliquer**, et ajouter `ruff format --check projet` à la CI et aux
     vérifications documentées. *Recommandé* : un correcteur qui lance `ruff format
     --check` (le cours cite `ruff format` dans `langage/gabarits/arborescence.md:57`)
     ne verra pas quatre échecs.
   - (b) l'appliquer, sans toucher à la CI.
   - (c) ne pas l'appliquer, et écrire dans `docs/developpement.md` que la mise en forme
     n'est pas vérifiée.
2. **`council/`**
   - (a) **copier `RAPPORT-FINAL.md` et `00-brief.md`** dans `docs/journal/conseil/`,
     sans toucher à `council/`. *Recommandé* : `NOTES.md` et les messages de commit
     citent les lots L1 à M6 du rapport, qu'un lecteur ne peut pas retrouver
     aujourd'hui ; le débat brut (136 Ko) n'apporte rien au correcteur.
   - (b) copier tout `council/` (41 fichiers, 596 Ko).
   - (c) le laisser hors du rendu, et dire dans `NOTES.md` que le rapport n'est pas livré.
3. **Les `PLAN*.md`**
   - (a) **les déplacer dans `docs/journal/`**, avec leur ligne d'en-tête. *Recommandé* :
     ils montrent la démarche (`docs/rendu.md:20`).
   - (b) les supprimer (l'historique Git les garde).
4. **Le format de livraison** (aucun n'est imposé : `docs/rendu.md:7-12`)
   - (a) **une archive `git archive --format=zip --prefix=upea/`**, nommée
     `marinier_AAAA-MM-JJ.zip`. *Recommandé* : elle contient exactement ce qui est
     commité, sans cache (`docs/rendu.md:26`, `:28`) ; essai : 106 fichiers, 335 Ko. Le
     README dit alors que la CI est « configurée, jamais exécutée faute de dépôt
     distant ».
   - (b) la même archive, plus un `git bundle` pour garder l'historique que `NOTES.md`
     cite par ses commits.
   - (c) un dépôt GitHub que vous créez et poussez vous-même (je ne pousse rien) : la CI
     tournerait enfin, et le README pourrait le dire.
5. **La langue du README**
   - (a) **français, plus une courte section « In English »** (huit lignes environ : ce
     qu'est Upea, comment l'installer et le lancer). *Recommandé* : le reste de la
     documentation reste en français.
   - (b) français seul.
   - (c) un README entièrement bilingue.
6. **La déclaration d'usage d'un assistant IA** (les consignes n'en parlent pas, §1.4)
   - (a) **un brouillon court dans `NOTES.md`**, marqué `<!-- À RELIRE PAR THOMAS -->`,
     que vous réécrivez. *Recommandé* : 39 commits sur 44 portent `Co-Authored-By:
     Claude`, et le journal montre les plans ; mieux vaut que ce soit vous qui le disiez.
   - (b) une section vide, avec seulement le marqueur.
   - (c) rien.
7. **Le code mort** (§2.2)
   - (a) **supprimer les trois** (`ligne_fautive`, `nombre_de_lignes`, `Noeud`).
     *Recommandé.*
   - (b) supprimer les deux fonctions, garder l'alias `Noeud` comme documentation de
     l'AST.
   - (c) ne rien supprimer.
8. **Les écarts avec le projet MCP du cours** (§1.3, non corrigeables sous le gel)
   - (a) **une table dans `NOTES.md`** : étape MCP, fait, remplacé ou absent, et pourquoi.
     *Recommandé* : c'est le minimum qu'avait demandé le conseil (M8).
   - (b) la même table, et une liste « à faire après la livraison » (`tokenize`, `parse`,
     `corriger_programme`, environnement réduit, `delai`) : ce serait une nouvelle phase
     de développement, hors de cette mission.
9. **`projet/mcp.exemple.json`** (`mcp/etapes/06_integration.md:77`, `:114`)
   - (a) **l'ajouter, avec un test** qui vérifie qu'il est un JSON valide et qu'il lance
     `python -m upea mcp`. *Recommandé* : c'est un fichier de configuration et un test,
     sans changement de comportement, et le cours le demande explicitement.
   - (b) ne pas l'ajouter, et le signaler dans la table de la décision 8.
10. **L'exercice final MCP** (une vraie IA, sa trace, vos observations :
    `mcp/etapes/06_integration.md:79-84`, `:121`)
    - (a) **vous le faites avant la livraison** ; je prépare dans `NOTES.md` une section
      vide, `<!-- À REMPLIR PAR THOMAS -->`, et l'endroit où ranger la trace
      (`docs/journal/exercice-final/`). *Recommandé* : c'est une validation humaine, je ne
      peux pas l'écrire à votre place.
    - (b) on le déclare non fait dans `NOTES.md`.
11. **« Environ 2 500 lignes »** (mesuré : 2 654 recopiées, 2 851 dans `upea_prelude.py`)
    - (a) **ne pas toucher à la spécification ni aux descriptions des outils**
      (c'est une approximation, et ces descriptions font partie du comportement), et ne
      pas répéter ce chiffre ailleurs. *Recommandé.*
    - (b) corriger `specification.md:511` en « environ 2 700 lignes », et le tracer dans
      `NOTES.md` ; les descriptions des outils restent inchangées.
12. **Ce plan, à la fin**
    - (a) **le déplacer dans `docs/journal/` au dernier lot**, avec sa liste de contrôle,
      et un lien depuis `NOTES.md`. *Recommandé* : la racine ne garde que `README.md` et
      `NOTES.md`.
    - (b) le laisser à la racine.
13. **Une licence** (un futur employeur la cherchera ; c'est un engagement juridique)
    - (a) **aucune pour l'instant**, à voir avec l'école. *Recommandé.*
    - (b) une licence libre que vous choisissez (MIT, par exemple).

## 6. Liste de contrôle de livraison

Remplie au lot 13 : chaque exigence du §1, et l'endroit où elle est remplie (fichier,
section, test ou commande), ou la raison de l'écart.
