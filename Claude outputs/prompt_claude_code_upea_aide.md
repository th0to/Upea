Tu travailles sur **Upea**, un langage aux mots-clés tahitiens, centré sur les arbres et les graphes, transpilé en Python 3.12. Le dépôt est le dossier courant (`myLanguage/`). Lis d'abord `README.md`, `NOTES.md`, `docs/mcp.md` et `docs/architecture.md`.

## Le contexte

J'ai branché le serveur MCP et demandé à une IA qui ne connaissait pas Upea de traduire un programme Python (un taquin). Elle a échoué. Son rapport est dans `docs/journal/exercice-final/session-1-rapport.md` : lis-le en entier.

L'analyse du rapport, déjà faite :

1. **L'IA n'a vu que les outils.** Ni les ressources (`upea://specification`, `upea://exemples/{nom}`, `upea://predefinies`), ni les prompts, ni les instructions du serveur ne lui sont parvenus. Le client passait par un pont qui ne transmet que les outils. Mais même branché directement, le problème demeure : en MCP, une ressource est choisie par l'application ou l'utilisateur, un prompt par l'utilisateur, et **seuls les outils sont appelés par le modèle de lui-même**. Tout ce qu'une IA doit pouvoir consulter seule doit donc être un outil.
2. **Les descriptions d'outils**, seuls textes garantis d'arriver jusqu'à l'IA, ne donnent aucune base du langage.
3. **Les messages d'erreur n'aident pas à deviner la syntaxe.** `si x > 1 { print(x); }` donne « ';' attendu après l'expression, trouvé 'x' », sans dire que `si` n'est pas un mot-clé d'Upea (il faut `ahani`).
4. **Le rapport surestime certains points, à ne pas traiter** :
   - l'absence de suggestion pour `blabla` est normale : aucun nom proche n'existe ;
   - le nom des outils vu par l'IA (`mcp__remote-devices__upea__*`) vient du pont, pas du serveur ;
   - garder les commentaires dans `formater` est une limite documentée, trop coûteuse à lever.
5. Il manque une page qui explique comment **passer de Python à Upea**, et comment remplacer ce qu'Upea n'a pas (dictionnaires, aléatoire, entrée clavier).

**Le gel du code est levé pour cette mission seulement**, dans le périmètre ci-dessous. La spécification (`projet/specification.md`, validée par mon enseignant) **ne change pas**.

Le travail se fait en **trois phases**. Ne passe pas à la phase suivante sans que je te le dise.

`uv` n'est pas dans le PATH : utilise `C:\Users\thoma\AppData\Roaming\Python\Python311\Scripts\uv.exe`.

---

## Phase 0 — État des lieux

1. `git status --short` doit être vide. Sinon, arrête-toi et dis-le-moi.
2. Vérification de référence : `uv run pytest projet`, `uv run mypy projet --platform win32` (puis `linux` et `darwin`), `uv run ruff check projet`, `uv run ruff format --check projet`. Attendu : 1 361 réussis et 4 ignorés, et aucune erreur.

## Phase 1 — Vérifier, puis écrire un plan

### 1a. Vérifier l'analyse

Reproduis les points 1 à 3 avant de les croire :
- avec le `Client` en mémoire du SDK, liste ce que le serveur expose (outils, ressources, gabarits, prompts, instructions) ;
- relis les six descriptions d'outils telles qu'un client les reçoit, et note ce qu'un modèle qui ne connaît pas Upea peut en déduire ;
- lance `verifier` sur une dizaine de programmes « devinés » par quelqu'un qui connaît Python ou le français (`si`, `sinon`, `pour`, `tant que`, `if`, `while`, `def`, `print`, `return`, `true`, `None`, `x += 1`…), et note chaque message obtenu.

### 1b. Le périmètre (décidé)

**Lot A0 — Une source unique pour l'aide.** Un nouveau module sans dépendance au SDK (par exemple `upea/aide.py`) contient les données et le texte de l'aide :
- les mots-clés, construits à partir de `tokens.py` (jamais recopiés à la main), avec le sens donné par la **table de la spécification** (ne pas inventer de sens ni d'étymologie) et leur équivalent Python ;
- les « faux amis » (lot C) ;
- le texte des sujets de l'outil `aide` (lot A).

Les outils MCP et les pages de `docs/` (lot D) sont produits à partir de ce module. Un test vérifie que chaque mot-clé de `tokens.py` y figure.

**Lot C — Les faux amis dans les messages d'erreur.** Quand l'erreur porte sur un mot d'un autre langage, le message ajoute un conseil, par exemple « `si` n'est pas un mot-clé d'Upea : écrivez `ahani` ».
- Une table courte et assumée : des mots de Python (`if`, `elif`, `else`, `while`, `for`, `def`, `return`, `break`, `continue`, `print`, `True`, `False`, `None`, `and`, `or`, `not`…) et du français (`si`, `sinon`, `tantque`, `pour`, `fonction`, `retourner`, `afficher`, `vrai`, `faux`, `et`, `ou`, `non`…). Chaque entrée renvoie au mot d'Upea, ou dit qu'il n'a pas d'équivalent.
- Le conseil n'apparaît **que dans une erreur** : une erreur de syntaxe dont le token fautif ou précédent est l'un de ces mots, ou « 'x' n'est pas déclaré » quand x en fait partie. Une variable déclarée qui s'appelle `si` ou `et` reste permise et ne reçoit aucun conseil (test obligatoire).
- Les messages actuels sont conservés : le conseil s'ajoute à la fin.
- **La spécification ne change pas** : ce sont des messages, pas le langage.

**Lot A — L'aide sous forme d'outils.**
- `aide(sujet)`, avec au moins les sujets suivants :
  - `apercu` : un aide-mémoire d'une page, à lire en premier (structure d'un programme, déclarations, conditions, boucles, fonctions, listes, arbres, graphes, affichage, un exemple complet, ce qu'Upea n'a pas, et la démarche verifier → executer) ;
  - `mots_cles` ;
  - `predefinies`, le catalogue des fonctions qui existe déjà pour la ressource ;
  - `depuis_python` ;
  - `specification`, avec un paramètre facultatif `section` qui rend une seule section (un nom inconnu donne la liste des sections).
- `exemples(nom)` : sans argument, la liste des exemples avec leur première ligne ; avec un nom, le source et la sortie attendue.
- Les ressources et les prompts restent tels quels, pour les clients qui les affichent.
- Annotations : lecture seule, idempotent, monde fermé. `apercu` doit tenir dans un budget raisonnable pour un modèle (environ 8 Kio au plus : mesure-le, et teste-le).

**Lot B — Des descriptions d'outils qui suffisent seules.** Chaque description commence par la même phrase courte, du genre : « Upea est un langage aux mots-clés tahitiens, transpilé en Python. Si tu ne le connais pas, appelle d'abord aide("apercu"). » Les instructions du serveur disent la même chose. Les descriptions restent concises.

**Lot D — La documentation du projet.**
- `docs/aide-memoire.md` et `docs/depuis-python.md`, **produits par le module du lot A0**. Propose comment les garder à jour : par exemple, des fichiers générés par une commande, et un test qui échoue s'ils ne correspondent plus au module.
- `depuis-python` montre au moins :
  - le tableau des équivalences ;
  - comment remplacer un dictionnaire (liste de paires et fonction de recherche, ou un graphe) et un ensemble (un arbre ordonné est un ensemble) ;
  - comment se passer de l'aléatoire (un petit générateur pseudo-aléatoire écrit en Upea) et de l'entrée clavier (des constantes dans le programme).

  Chaque exemple est exécuté par le test de la documentation existant, `test_livraison_documentation.py`.
- `docs/mcp.md` :
  - corrige la section « Ce que l'IA lit en se connectant » (le point 1 de l'analyse) ;
  - présente `aide` et `exemples` ;
  - explique qu'un client peut n'afficher que les outils.
- `README.md` et `docs/tutoriel.md` renvoient à l'aide-mémoire et à `depuis-python`. `docs/architecture.md` présente le nouveau module.

**Lot E — Le scénario de l'exercice final.**
- Un test de bout en bout, avec le `Client` en mémoire, qui joue le client naïf :
  - il ne lit que la liste des outils ;
  - il vérifie que chaque description renvoie à `aide` ;
  - il appelle `aide("apercu")` ;
  - il vérifie un programme écrit **à partir de l'exemple qu'apercu contient**, puis l'exécute.
- Dans `docs/journal/exercice-final/` :
  - un `index.md` qui présente la démarche ;
  - le rapport de la session 1, tel quel ;
  - une place pour la session 2.
- **Prépare le texte exact de la session 2**, que je donnerai à une IA neuve : la même tâche que la session 1, sans fournir la spec, avec une demande de rapport au même format.
- **N'écris pas mes observations** : laisse une section marquée `<!-- À RÉDIGER PAR THOMAS -->`.

**Hors périmètre** : `formater` et les commentaires, le nommage des outils par le pont, tout changement du langage ou de la spécification, toute nouvelle fonctionnalité du langage.

### 1c. Le plan à produire

Écris `PLAN_AIDE.md` à la racine, puis **arrête-toi et attends ma validation**. Il contient :
- la vérification de l'analyse (1a), avec les commandes et les sorties ;
- les lots dans l'ordre (je propose A0 → C → A → B → D → E), avec pour chacun : fichiers touchés, approche, tests, risques ;
- **le texte proposé** de `aide("apercu")` (en entier) et de la phrase d'en-tête des descriptions (lot B) ;
- la table des faux amis proposée, en entier ;
- la liste des décisions qui me reviennent, en questions fermées, avec ta recommandation.

## Phase 2 — Exécution (seulement après mon feu vert)

Pour chaque lot, dans l'ordre :
1. le test d'abord, et vérifier qu'il échoue ;
2. le code ou la documentation ;
3. `uv run pytest projet`, `uv run mypy projet --platform win32` (et `linux`, `darwin`), `uv run ruff check projet`, `uv run ruff format --check projet` : tout vert avant de continuer ;
4. **un commit par lot**, message en français qui dit ce qui change et pourquoi ;
5. un résumé du lot en trois lignes, puis le lot suivant.

À la fin, relance toute la vérification, mets à jour `NOTES.md` (avancement de l'extension 18, table des écarts avec le cours MCP), et donne-moi le bilan ainsi que le texte de la session 2.

## Règles à respecter tout du long

- **La spécification ne change pas.** Le sens des mots tahitiens vient uniquement de sa table.
- **Rien d'inventé dans la documentation** : chaque exemple est exécuté, chaque sortie copiée d'une exécution réelle.
- Le serveur ne touche au compilateur que par la façade `compilateur.py`, comme aujourd'hui.
- Python 3.12, Windows et Linux ; mypy strict sur les trois plateformes ; identifiants et commentaires en français ; style du projet.
- Aucun traceback Python ne doit atteindre l'utilisateur.
- N'ajoute aucune dépendance.
- Ne supprime aucun test existant ; si un test doit changer, explique pourquoi dans le commit.
- Ne modifie rien dans `council/` ni dans `.claude/`.
- **Aucune opération Git en dehors des commits de lot** : pas de `stash`, `rebase`, `amend`, `reset`, ni `push`.
- Si un lot devient plus gros ou plus risqué que prévu, arrête-toi et dis-le-moi.
