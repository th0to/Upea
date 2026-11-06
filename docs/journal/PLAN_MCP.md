> Document de travail, état au commit `c9a5961` (4 novembre 2026). Il n'est plus tenu à jour.

# Plan : le serveur MCP d'Upea

> Plan validé le 4 novembre 2026, avec ces réponses et ces ajouts.
>
> - Décisions : D1 (a) ; D2 oui, **en lot séparé** ; D3 Markdown ; D4 oui ; D5 code 2 ;
>   D6 oui (une ligne dans *Utilisation*) ; D7 npx ; D8 oui ; D9 oui ;
>   D10 `mcp>=2.3,<3` ; D11 oui.
> - **Lot 3b (mémoire)**, juste après le lot 3 : mesurer ce qu'occupe un programme qui
>   double une liste ou un texte à chaque tour (mesure arrêtée vers 1 Go), puis un
>   plafond de 512 Mo sans dépendance (job object Windows par ctypes,
>   `resource.setrlimit` sous Linux). Un dépassement donne « mémoire dépassée ». Au-delà
>   de ~80 lignes, ou si c'est fragile : s'arrêter et montrer la mesure et les options.
> - **Concurrence** (lot 5) : au plus 2 exécutions simultanées (un sémaphore) ; l'attente
>   ne compte pas dans le délai de 5 s ; un test.
> - **Lot 6a (D2)**, juste avant les ressources : aucun comportement de typage ne change,
>   la suite existante reste verte sans modification, un commit à part. Au-delà de ~150
>   lignes changées dans `predefinies.py` : s'arrêter et proposer la version réduite.
>
> Ordre des lots : 1, 2, 3, 3b, 4, 5, 6a, 6, 7, 8, 9.
>
> **État** : tous les lots sont faits, un commit chacun. Écart au plan : le
> bac à sable lit la sortie de l'enfant avec `communicate`, sans fil de lecture
> plafonné côté parent (seul le code de l'enfant écrit sur ses sorties, et il borne
> lui-même la sortie du programme).

## 0. État des lieux (phase 0)

- `git status` : arbre propre, branche `master`, dernier commit `9f2ce74`.
- `uv run pytest projet` : **1 016 réussis, 4 ignorés** (Graphviz absent).
  `uv run mypy projet` : aucune erreur (56 fichiers). `uv run ruff check projet` : rien.
- Démarrer un sous-processus `python -m upea run` coûte **0,3 à 0,7 s** sur cette machine
  (`01_ia_ora_na` : 0,3 s, `08_algorithmes_graphes` : 0,7 s). Le délai de 5 s laisse
  donc de la marge.

## 1. Ce que j'ai appris du SDK `mcp` v2

Sources :

- **[doc]** : la documentation v2, <https://py.sdk.modelcontextprotocol.io/v2/>, avec
  le chemin de chaque page ;
- **[source]** : le code de `mcp==2.3.0`, installé dans un environnement jetable
  (hors du dépôt) ;
- **[essai]** : un prototype jetable, lancé avec ce même paquet. C'est la source qui
  fait foi quand elle contredit la doc.

### 1.1 Version et typage

- Dernière version : **2.3.0**, publiée le 2 octobre 2026 (PyPI). Versions précédentes :
  2.0.0 le 28 juillet 2026, puis 2.1.0, 2.2.0. Elle dépend du paquet `mcp-types==2.3.0`.
  Elle demande Python ≥ 3.10 (PyPI), ou 3.11+ selon `get-started/installation/` : les
  deux conviennent à 3.12.
- **Typage** : `mcp/py.typed` et `mcp_types/py.typed` sont présents **[source]**. Le
  prototype passe `mypy --strict` **[essai]** : les décorateurs sont typés
  `Callable[[_CallableT], _CallableT]` et gardent donc la signature des fonctions, et
  `CallToolResult.content` est une union précise (il faut la réduire avec `isinstance`).
  La doc ne parle ni de `py.typed` ni de mypy.
- **Dépendances tirées** : pydantic, starlette, uvicorn, sse-starlette, httpx2, anyio,
  jsonschema, pyjwt[crypto], opentelemetry-api, python-multipart, et pywin32 sous
  Windows. C'est lourd : raison de plus pour un groupe facultatif.
- **Protocole** : le `Client` v2 négocie par défaut la révision **2026-07-28** (sonde
  `server/discover`, puis repli sur l'ancienne poignée de main `initialize` si le serveur
  ne la connaît pas) **[doc `whats-new/`, source `Client.mode`]**. Le serveur accepte
  toujours `initialize` : une requête `initialize` avec `protocolVersion: "2025-06-18"`
  reçoit une réponse normale (capacités, `serverInfo`, `instructions`) **[essai]**. C'est
  ce qui compte pour Claude Code et Claude Desktop.

### 1.2 Déclarer un serveur, un outil, une ressource et un prompt

- `from mcp.server import MCPServer` (il n'y a pas de `from mcp import MCPServer`)
  **[doc `get-started/first-steps/`, source `mcp/server/__init__.py`]**.
- Constructeur : `MCPServer(name, title=, description=, instructions=, version=, …,
  lifespan=, log_level="INFO")` **[source]**. `instructions` est transmis au client
  à l'initialisation **[essai]** : c'est là qu'on dira au modèle de lire la spécification
  d'abord.
- **Outil** : `@serveur.tool(name=, title=, description=, annotations=ToolAnnotations(…),
  structured_output=None)` **[source, doc `servers/tools/`]**. Le nom par défaut est celui
  de la fonction, et la description sa docstring. Les arguments sont décrits par
  `Annotated[str, Field(description="…")]` (pydantic), `Literal[...]` donne une
  énumération dans le schéma **[doc `servers/tools/`]**. **Les sections `Args:` de la
  docstring ne sont pas lues** : il faut passer par `Field` **[source
  `func_metadata.py`]**. Une fonction synchrone est appelée dans un fil de travail
  (`anyio.to_thread.run_sync`) **[source `func_metadata.py:164`]** : un `executer` qui
  attend son sous-processus ne bloque pas le serveur.
- **Ressource fixe** : `@serveur.resource("upea://specification", mime_type=…,
  description=…)` sur une fonction sans paramètre qui rend un `str` **[doc
  `servers/resources/`]**.
- **Ressource à gabarit** : un `{nom}` dans l'URI, et un paramètre `nom` dans la
  fonction. Elle est listée par `resources/templates/list`, pas `resources/list`. Si les
  paramètres et le gabarit ne correspondent pas, `ValueError` dès l'import **[doc
  `servers/uri-templates/`, essai]**. Les valeurs extraites passent par
  `ResourceSecurity` (refus de `..`, des chemins absolus, des octets nuls) **[source
  `resources/templates.py`]**.
- **Prompt** : `@serveur.prompt(title=, description=)` sur une fonction qui rend un
  `str`, transformé en un message `user` ; les arguments sont décrits par `Field`
  **[doc `servers/prompts/`, essai]**.

### 1.3 Lancer le serveur en stdio

- `serveur.run()` est **synchrone** et bloquant ; sans argument, le transport est stdio
  (`anyio.run(self.run_stdio_async)`) **[doc `run/`, source]**.
- Pendant le service, le SDK déplace le fil du protocole sur un descripteur privé, fait
  pointer le fd 1 sur stderr et le fd 0 sur le périphérique nul. Un `print` vidé
  arrive donc sur stderr **[doc `run/`, source `server/stdio.py`]**. La doc précise que
  c'est « au mieux » : **[essai]** un `print` resté dans le tampon de `sys.stdout` est
  écrit sur stdout à la sortie du processus, **après** le JSON-RPC. Il faut donc
  protéger stdout nous-mêmes (lot 1).
- Journalisation : `MCPServer(...)` appelle `logging.basicConfig` **dès sa
  construction**, avec un `StreamHandler` vers stderr (ou `RichHandler(stderr=True)` si
  `rich` est installé) **[source `utilities/logging.py`]**. On construira donc le
  serveur dans une fonction, pas à l'import du module.

### 1.4 Résultats structurés et erreurs d'outil

- **Résultat structuré** : le type de retour annoté donne le schéma de sortie. Une
  `dataclass`, un `TypedDict` ou un modèle pydantic sont rendus tels quels dans
  `structured_content`, et un scalaire ou une liste sont enveloppés dans
  `{"result": …}`. Le texte JSON est aussi mis dans `content` pour les clients qui
  n'utilisent pas `structured_content` **[doc `servers/structured-output/`, essai]**.
- ⚠ **Écart avec la doc [essai]** : une `@dataclass(frozen=True, slots=True)`, le style
  du projet, **ne donne pas de schéma**. pydantic prend les descripteurs de slots pour
  des valeurs par défaut (« non-serializable-default »), le SDK l'écrit sur stderr, et
  l'outil retombe en texte seul (`structured_content=None`, pas d'`output_schema`). Une
  `@dataclass(frozen=True)` sans `slots`, ou un `TypedDict`, fonctionne. Voir la
  décision D1.
- **Erreur d'outil** : `from mcp.server.mcpserver.exceptions import ToolError`. La lever
  donne `is_error=True`, avec le message dans `content`, préfixé :
  `Error executing tool verifier: <message>` **[doc `servers/handling-errors/`,
  essai]**. Toute autre exception donne aussi `is_error=True`, mais **sans** son message
  (`Error executing tool verifier`) ; la trace part dans le journal. Des arguments qui ne
  respectent pas le schéma donnent `is_error=True` avant l'appel, avec le message de
  pydantic **[essai]**.
- **Ressource absente** : `ResourceNotFoundError` (même module) donne une erreur de
  protocole −32602 avec notre message ; côté `Client`, `read_resource` lève
  `mcp.shared.exceptions.MCPError` **[source, essai]**.

### 1.5 Tester en mémoire avec le `Client` v2

- `from mcp import Client` ; `async with Client(serveur) as client:` se connecte **dans
  le processus**, et le mode `auto` envoie les requêtes directement, **sans passer par
  JSON-RPC** **[source, docstring de `Client.mode`]**. La sérialisation n'est donc
  vérifiée que par les tests en stdio (lot 8).
- Méthodes **[source `client/client.py`, essai]** : `list_tools()`, `call_tool(nom,
  arguments)`, `list_resources()`, `list_resource_templates()`, `read_resource(uri)`,
  `list_prompts()`, `get_prompt(nom, arguments)`. Les attributs sont en snake_case :
  `.is_error`, `.content`, `.structured_content`, `.tools[i].input_schema`,
  `.output_schema`, `.resource_templates`, `.contents[i].text`, `.messages`.
- pytest : `@pytest.mark.anyio` et une fixture `anyio_backend` qui rend `"asyncio"`
  **[doc `get-started/testing/`]**. Le greffon pytest d'anyio est déclaré par anyio lui-même
  (point d'entrée `pytest11`), donc **aucune dépendance de plus** **[source, essai]**.
  `inline-snapshot`, que la doc suggère, n'est pas nécessaire : on compare les champs.
- On peut aussi lancer le vrai serveur : `Client(StdioServerParameters(command=…,
  args=…))` **[source]**.

### 1.6 Inspector

- Toujours documenté : `uv run mcp dev server.py`, qui demande `npx` (l'Inspector est
  une application Node.js) **[doc `run/`]**. La commande `mcp` vient de l'extra
  `mcp[cli]` (typer, python-dotenv), c'est-à-dire de dépendances en plus. Sinon,
  `npx @modelcontextprotocol/inspector <commande>` lance l'Inspector directement ; le
  README du SDK pointe vers son dépôt (`modelcontextprotocol/inspector`). Voir D7.

## 2. Architecture retenue

```
projet/upea/
  atelier.py      vérifier, transpiler, formater : fonctions pures sur la façade,
                  diagnostics structurés (dataclasses), sans dépendance à MCP
  bac_a_sable.py  exécution isolée : côté parent (sous-processus, délai, plafond)
                  et côté enfant (python -m upea.bac_a_sable)
  serveur_mcp.py  la seule couche qui importe `mcp` : descriptions, ressources,
                  prompts, conversion en erreurs d'outil ; construire_serveur(), lancer()
  cli.py          + sous-commande `mcp`, qui importe serveur_mcp en différé
  compilateur.py  + fonctions_predefinies() (la façade expose le registre)
  predefinies.py  + chaque prédéfinie sait écrire sa signature (décision D2)
```

Le serveur ne touche au compilateur que par `compilateur.py`. `atelier.py` et
`bac_a_sable.py` sont testables **sans** le SDK. `serveur_mcp.py` ne fait que décrire,
limiter la taille, et convertir les pannes en `ToolError`.

## 3. Les lots

Par rapport à la liste d'exemple, j'ai fait **deux changements d'ordre** :

- la représentation des diagnostics (sans MCP) passe **avant** l'exécution isolée, qui
  en a besoin pour rendre une erreur de compilation ;
- un premier test en stdio (`initialize`, et rien d'autre sur stdout) entre **dès le
  lot 1**, pour valider tôt le squelette et la protection de stdout. Le lot 8 l'étend.

Ce qui donne 9 lots. Chacun : test d'abord (qui échoue), code, pytest, mypy et ruff au
vert, documentation, un commit.

### Lot 1 : dépendance, squelette, `python -m upea mcp`

- **Fichiers** : `pyproject.toml`, `uv.lock`, `upea/serveur_mcp.py` (nouveau),
  `upea/cli.py`, `tests/test_extension_18_mcp.py` (nouveau).
- **Approche** :
  - Groupe de dépendances `mcp = ["mcp>=2.3,<3"]`, inclus dans `dev` par
    `{include-group = "mcp"}` (PEP 735). C'est la bonne façon de faire avec
    `package = false`, où les extras n'existent pas. Je l'ai vérifié avec uv 0.13.6 sur
    un projet jetable : `uv lock` range bien `mcp` dans les deux groupes. `uv sync`
    installe `dev`, donc `mcp` ; `uv sync --no-dev --group mcp` installe le serveur
    seul.
  - `construire_serveur() -> MCPServer` crée l'instance (pas à l'import, à cause du
    `basicConfig`), avec `instructions` en français. `lancer() -> int` appelle `run()`.
  - **Protection de stdout** : un `lifespan` du serveur, qui s'exécute *après* que le
    transport a pris le fd 1, remplace `sys.stdout` par `sys.stderr` pendant le service,
    puis le rétablit. Tout `print` égaré (le nôtre ou celui d'une bibliothèque) part
    alors sur stderr, même non vidé. `lancer()` l'active, les tests en mémoire non.
  - `cli.py` : sous-commande `mcp`, qui importe `serveur_mcp` **dans** la fonction. Un
    `ModuleNotFoundError` dont le module est `mcp`, `mcp_types` ou `pydantic` donne, sur
    stderr : « le serveur MCP demande le SDK `mcp` : `uv sync --group mcp` », et le code
    2 (D5). Toute autre erreur d'import n'est pas masquée.
- **Alternative écartée** : un `redirect_stdout` autour de chaque outil. Les outils
  synchrones tournent dans des fils, et `sys.stdout` est global : deux appels simultanés
  se marcheraient dessus. Un serveur global à l'import : il configurerait la
  journalisation de quiconque importe le module.
- **Tests** : sans SDK (`sys.modules["mcp"] = None`) : message clair, code 2, aucun
  `Traceback` ; `mcp` figure dans `--help` ; le serveur a un nom et des instructions ;
  **en stdio**, `[sys.executable, "-m", "upea", "mcp"]` reçoit `initialize`, et chaque
  ligne de stdout est un message JSON-RPC.
- **Risques** : `uv sync` a déjà buté, dans mon environnement jetable, sur une erreur de
  lien physique avec le cache (OneDrive) ; le remède est `--link-mode=copy`. Si ça
  arrive dans le dépôt, je m'arrête et te le dis avant de toucher à la configuration de
  uv.

### Lot 2 : diagnostics structurés et atelier (sans MCP)

- **Fichiers** : `upea/atelier.py` (nouveau), `tests/test_extension_18_atelier.py`
  (nouveau).
- **Approche** :
  - `Diagnostic(sorte, ligne, colonne, message)`, où `sorte` vaut `"lexicale"`,
    `"syntaxe"`, `"semantique"`, `"type"`, `"avertissement"` ou `"execution"`. La sorte
    est déduite par `match` sur la classe (`ErreurType` avant `ErreurSemantique`, sa
    classe mère). `ligne` et `colonne` valent `None` quand elles sont inconnues
    (position absente, colonne 0 d'une erreur d'exécution).
  - `verifier(source, types) -> Verification(valide, diagnostics, rapport)`, où
    `rapport` est le texte de `erreurs.formater`, ligne fautive et `^` compris, comme le
    montre la CLI. `transpiler(source, backend, avec_prelude) -> Transpilation(code |
    None, diagnostics)` : sans le prélude, il passe par `prelude_externe=True`, le
    mécanisme de `--prelude externe`, et le résultat le dit. `formater(source) ->
    Formatage(code | None, diagnostics)`.
  - Une erreur de compilation est un **résultat**, jamais une exception. Le code
    accepte `ErreursMultiples` comme une `ErreurUpea` seule.
- **Alternative écartée** : mettre cette logique dans `serveur_mcp.py`. On ne pourrait
  plus la tester sans le SDK, et le serveur ne serait plus mince.
- **Tests** : un programme par sorte d'erreur (les exemples de la section *Erreurs* de
  la spec), avec ligne et colonne exactes ; plusieurs erreurs d'un coup ; avertissement
  seul ⇒ `valide` ; `types=False` ; transpilation sans prélude (commence par
  `from upea_prelude import *`, moins de 100 lignes) et avec (le texte entier) ;
  formatage idempotent ; backend `ast`.
- **Risque** : les avertissements ne sont connus que si la compilation réussit
  (`semantique.py` les perd sinon). C'est le comportement actuel de `check` : je le
  garde, et la description de `verifier` le dit.

### Lot 3 : exécution isolée (sans MCP)

- **Fichiers** : `upea/bac_a_sable.py` (nouveau), `tests/test_extension_18_bac_a_sable.py`
  (nouveau).
- **Approche** :
  - **Parent** : `subprocess.Popen([sys.executable, "-m", "upea.bac_a_sable"], stdin,
    stdout, stderr en PIPE, cwd=le dossier projet/)`. L'environnement est celui du
    serveur, plus `PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8` et `NO_COLOR=1`, et sans
    `FORCE_COLOR`. Sous Windows, `creationflags=CREATE_NO_WINDOW` : lancé par Claude
    Desktop, qui n'a pas de console, l'enfant ouvrirait sinon une fenêtre.
  - **Le source passe par stdin**, dans un objet JSON `{source, types, backend,
    marqueur}`, et stdin est fermé aussitôt. Pas de fichier temporaire : rien à
    supprimer si l'enfant est tué, pas de fichier verrouillé sous Windows, et rien qui
    traîne sur le disque. Un programme Upea ne sait pas lire l'entrée (spec, *Limites*) :
    il ne peut pas toucher à ce canal.
  - **Enfant** : il lit la requête, remplace `sys.stdout` par un écrivain qui compte les
    octets UTF-8, transmet et **vide** chaque écriture jusqu'à 64 Kio, puis jette la
    suite en notant `tronquee` et le total. Il appelle `compilateur.executer`, et
    attrape `ErreursMultiples` et `ErreurExecution`. Enfin il écrit, sur le **vrai**
    stdout, une ligne `marqueur` suivie du résultat en JSON (statut, diagnostics,
    avertissements, code de retour 0/1/3 comme la CLI, troncature).
  - Le **marqueur** est une valeur aléatoire (`secrets.token_hex`) tirée par le parent
    pour chaque exécution : le parent découpe sur sa dernière occurrence, et le
    programme ne peut pas l'imiter, puisqu'il ne la connaît pas.
  - **Délai** : `communicate(timeout=5)`. À l'expiration, `kill()`, puis on récupère ce
    qui a été écrit : puisque l'enfant vide chaque écriture, la sortie partielle est
    conservée. Comme l'enfant ne crée pas d'autre processus, `kill()` suffit sous
    Windows comme sous Linux.
  - **Garde-fou côté parent** : un fil lit stdout par blocs, garde au plus
    64 Kio + 64 Kio (sortie et ligne de résultat) et jette le reste, sans cesser de lire,
    pour ne jamais bloquer l'enfant sur un tube plein.
  - Résultat : `Execution(statut, sortie, tronquee, diagnostics, code_retour)`, ou une
    exception `DelaiDepasse` / `EnfantEnPanne` (avec la fin de son stderr) que le lot 5
    traduit en `ToolError`.
- **Alternatives écartées** : récupérer le résultat sur stderr (Python peut y écrire ses
  propres avertissements) ; un descripteur supplémentaire (`pass_fds` n'existe pas sous
  Windows) ; un fichier de résultat (à nettoyer) ; mettre toute la sortie dans le JSON
  final (perdue si l'enfant est tué) ; analyser le texte de la CLI (fragile, et c'est
  exclu).
- **Tests** : succès, avec la sortie exacte d'un exemple (`05_motu`) ; erreur de
  compilation (diagnostics, code 1) ; erreur d'exécution (`[1, 2][5]` : ligne Upea,
  code 3) ; boucle infinie (`tamau tia {}` : `DelaiDepasse` en moins de 7 s, enfant
  bien mort, sortie partielle gardée) ; sortie énorme (`tamau tia { faaite "x"; }` sans
  fin, et une boucle finie de 200 000 lignes : `tronquee`, au plus 64 Kio, mention
  claire) ; non ASCII (`faaite "île ʻōmuamua", hohoa(...)` : dessins et accents
  intacts) ; un programme qui affiche une fausse ligne de marqueur ; `FORCE_COLOR` dans
  l'environnement sans effet ; backend `ast`. Pour réduire la durée de ces tests, le
  délai est un paramètre (0,5 s pour la boucle infinie).
- **Risques** : pas de limite de mémoire. Le module `resource` n'existe pas sous Windows,
  et les *job objects* demanderaient pywin32 ou ctypes. Je la note comme limite. La
  durée totale des tests augmente (une dizaine de sous-processus, ~0,5 s chacun).

### Lot 4 : outils `verifier`, `formater`, `transpiler`

- **Fichiers** : `upea/serveur_mcp.py`, `tests/test_extension_18_mcp.py`.
- **Approche** : des enveloppes minces sur `atelier`, qui :
  - décrivent chaque argument avec `Annotated[…, Field(description=…)]` ;
  - donnent le backend en `Literal["python", "ast"]`, que le SDK refuse lui-même avant
    l'appel (erreur d'outil) ;
  - refusent un source de plus de **100 Kio d'UTF-8** par un `ToolError` (« source trop
    longue : N octets, au plus 102 400 ») ;
  - portent les annotations `readOnlyHint=True`, `idempotentHint=True` et
    `openWorldHint=False`.

  Les descriptions disent quand utiliser l'outil, ce qu'il rend, et ses pièges : les
  commentaires perdus par `formater`, le prélude importé par `transpiler`, les
  avertissements qui n'apparaissent que sans erreur.
- **Tests (client en mémoire)** : les trois outils sont listés, avec leurs schémas
  d'entrée et de sortie ; une erreur de compilation donne `is_error=False` et des
  diagnostics structurés ; un source trop long et un backend inconnu donnent
  `is_error=True` ; `structured_content` correspond au résultat d'`atelier`.

### Lot 5 : outil `executer`

- **Fichiers** : `upea/serveur_mcp.py`, `tests/test_extension_18_mcp.py`.
- **Approche** : une enveloppe sur `bac_a_sable.executer`. Délai dépassé et enfant en
  panne deviennent un `ToolError`. Le message du délai dépassé donne la fin de la sortie
  partielle, au plus 2 Kio (D4). Annotations : `readOnlyHint=True`,
  `openWorldHint=False`, `idempotentHint=True`. La description précise que le programme
  tourne dans un processus séparé, avec 5 s et 64 Kio au plus, et qu'une erreur de
  compilation ou d'exécution est un **résultat** à lire pour corriger.
- **Tests (en mémoire)** : succès d'un exemple ; erreur d'exécution avec sa ligne ;
  boucle infinie ⇒ `is_error=True` et le message le dit (délai réduit par un paramètre
  de `construire_serveur`) ; sortie tronquée.

### Lot 6 : ressources

- **Fichiers** : `upea/serveur_mcp.py`, `upea/compilateur.py`
  (`fonctions_predefinies()`), `upea/predefinies.py` (D2),
  `tests/test_extension_18_mcp.py`, et un test dans `test_extension_12_types.py` si
  `predefinies.py` change.
- **Approche** :
  - `upea://specification` (`text/markdown`) : `projet/specification.md`, relu à chaque
    lecture.
  - `upea://exemples` (`text/markdown`) : les noms (`05_motu`…) et la première ligne de
    commentaire de chaque exemple, lus dans `exemples/`.
  - `upea://exemples/{nom}` (`text/markdown`) : le source et la sortie attendue
    (`.attendu`), dans deux blocs de code. Un nom inconnu lève `ResourceNotFoundError`,
    avec la liste des noms disponibles. Option D8 : chaque exemple aussi en ressource
    fixe.
  - `upea://predefinies` (`text/markdown`, D3) : pour chaque fonction du registre
    `PREDEFINIES`, son arité (`Predefinie.arite()`, qui existe déjà) et sa signature,
    par exemple `pihai(upea[T], T) -> tapura[T]`. Le tout est **calculé** depuis
    `predefinies.py` (D2).
  - D2 en pratique : les patrons (`lie`, `comme_t`, `si`, `TOUT`) deviennent de petits
    objets qui portent leur texte (`upea[T]`, `T`, `nombre`…) en plus de leur
    vérification. Le type de retour est **sondé** : si `retour(NUMERA) == retour(PARAU)`,
    il est fixe ; sinon c'est `str(retour(INCONNU))` où `?` devient `T`. Les trois
    typeurs écrits à la main (`roa`, `tumu`, les conversions) reçoivent leur signature
    en paramètre de `@predefinie`. Aucune règle de typage ne change.
- **Alternative écartée** : un tableau des prédéfinies écrit dans `serveur_mcp.py` (il
  se désynchroniserait). Analyser les tableaux Markdown de la spec (fragile).
- **Tests** : la liste des ressources et du gabarit ; la spec lue est égale au fichier ;
  chaque exemple de `exemples/` est accessible et rend son `.attendu` ; un nom inconnu
  donne `MCPError` ; `../specification` est refusé ; **chaque** nom de `PREDEFINIES`
  apparaît dans `upea://predefinies` avec la bonne arité ; quelques signatures exactes
  (`pihai`, `tarjan`, `iriti`, `taati` avec son poids facultatif).
- **Risque** : D2 touche le cœur du typage. Les 1 016 tests existants et
  `test_extension_12_types.py` le couvrent, et je n'y change aucun comportement.

### Lot 7 : prompts

- **Fichiers** : `upea/serveur_mcp.py`, `tests/test_extension_18_mcp.py`.
- **Approche** :
  - `ecrire_programme(tache)` : lire `upea://specification` (et `upea://predefinies`,
    un exemple proche), écrire le programme, le passer à `verifier`, corriger jusqu'à ce
    qu'il n'y ait plus d'erreur, l'exécuter avec `executer`, comparer la sortie à ce qui
    est attendu, puis rendre le programme final et sa sortie.
  - `traduire_depuis_python(code)` : la même démarche. Le prompt rappelle aussi les
    différences qui piègent : pas de dictionnaires, pas de fonctions comme valeurs, des
    comparaisons non enchaînées, `tuu` obligatoire et sans masquage, `faaite` et
    `parau(x)` pour l'affichage, et les graphes et arbres natifs à préférer aux
    réimplémentations.
  - Chaque prompt rend un seul message `user`, en français.
- **Tests** : les deux prompts sont listés avec leurs arguments décrits et obligatoires ;
  le texte rendu contient la tâche (ou le code), et nomme `verifier`, `executer` et
  `upea://specification`.

### Lot 8 : tests de bout en bout

- **Fichiers** : `tests/test_extension_18_mcp.py`.
- **Approche** :
  - Test **brut** : lancer `python -m upea mcp`, envoyer `initialize` (ancienne poignée
    de main), `notifications/initialized`, `tools/call executer` sur un programme qui
    fait `faaite` (accents et dessin compris), puis `tools/call verifier` sur un source
    faux. Ensuite, fermer stdin et attendre la fin. Vérifier que **chaque** ligne de
    stdout est un message JSON-RPC 2.0, que les deux réponses sont là, et que rien
    d'autre n'a été écrit : ni la sortie du programme, ni un journal.
  - Test avec le `Client` du SDK sur `StdioServerParameters` (mode `auto`, donc le
    protocole 2026-07-28) : listes et un appel d'outil.
- **Risque** : la durée (deux serveurs lancés, ~2 s). Sous Windows, l'arrêt du serveur
  à la fermeture de stdin est à vérifier ; le test aura un délai pour ne jamais rester
  bloqué.

### Lot 9 : documentation

- **Fichiers** : `NOTES.md`, `README.md`, et `projet/specification.md` si D6 = oui.
- `NOTES.md` : une ligne « 18 serveur MCP » dans le tableau d'avancement (modules,
  tests), « Le serveur MCP n'est pas commencé » retiré, la commande dans *Commandes*, les
  limites (pas de limite mémoire, avertissements seulement sans erreur, dataclasses sans
  `slots` si D1).
- `README.md` : installation (`uv sync`, ou `uv sync --no-dev --group mcp`),
  branchement dans Claude Code (commande `claude mcp add`, **vérifiée dans la
  documentation de Claude Code** à ce moment-là) et dans Claude Desktop
  (`claude_desktop_config.json`, avec `uv run --directory <…>/projet python -m upea
  mcp` : Claude Desktop ne fixe pas le dossier courant, et uv n'est pas dans le PATH,
  d'où un chemin absolu), et l'Inspector.
- Les lots 1 à 8 mettent déjà à jour leur part de `NOTES.md` ; ce lot fait la
  relecture d'ensemble et le README.

## 4. Décisions qui te reviennent

Pour chaque question, ma recommandation est en gras.

- **D1. Types des résultats d'outil.** Le style du projet, `dataclass(frozen=True,
  slots=True)`, empêche le SDK de produire un schéma de sortie (vérifié). Que faire ?
  **(a) `@dataclass(frozen=True)` sans `slots`, pour ces seuls types, avec un
  commentaire qui explique pourquoi** ; (b) `TypedDict` ; (c) modèles pydantic (qui
  rendraient `atelier.py` dépendant de pydantic, donc du SDK).
- **D2. Signatures des prédéfinies.** Faut-il enrichir `predefinies.py` (des patrons qui
  portent leur texte, et un type de retour sondé) pour que `upea://predefinies` donne
  les types des arguments ? **Oui** ; sinon, la ressource ne donne que le nom, l'arité
  et un type de retour sondé.
- **D3. Format de `upea://predefinies` et des exemples.** **Markdown** (lisible par un
  modèle, et cohérent avec la spec), ou JSON ?
- **D4. Délai dépassé.** Le `ToolError` doit-il contenir la fin de la sortie partielle
  (au plus 2 Kio), pour aider à trouver la boucle ? **Oui.**
- **D5. Code de retour de `python -m upea mcp` sans le SDK.** **2 (erreur
  d'utilisation, déjà défini)**, ou un nouveau code 4 ?
- **D6. Spécification.** Ajouter une ligne `python -m upea mcp` à la section
  *Utilisation* de `specification.md` ? Elle décrit la CLI, pas le langage, mais tu as
  demandé de ne pas toucher à la spec. **Oui, une ligne**, si tu l'acceptes ; sinon,
  seulement le README et `NOTES.md`.
- **D7. Inspector.** **`npx @modelcontextprotocol/inspector <commande>`, sans dépendance
  Python de plus**, ou ajouter l'extra `mcp[cli]` au groupe pour avoir `mcp dev` ?
- **D8. Exemples en ressources fixes.** En plus du gabarit, enregistrer chaque exemple
  comme une ressource fixe, générée par une boucle sur `exemples/`, pour qu'il apparaisse
  dans `resources/list` (le menu `@` de Claude Code) ? **Oui.**
- **D9. Nommage.** Tests `test_extension_18_*.py` et ligne « 18 serveur MCP » dans
  l'avancement ? **Oui.**
- **D10. Épinglage.** **`mcp>=2.3,<3` dans `pyproject.toml`, la version exacte (2.3.0)
  étant fixée par `uv.lock`**, ou `mcp==2.3.0` ?
- **D11. Noms des modules.** **`atelier.py`, `bac_a_sable.py` et `serveur_mcp.py`** :
  te conviennent-ils ?
