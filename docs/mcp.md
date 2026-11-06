# Le serveur MCP d'Upea

`python -m upea mcp` est un serveur [MCP](https://modelcontextprotocol.io) (Model
Context Protocol), en stdio. Il permet à une IA qui ne connaît pas Upea de l'apprendre
(l'outil `aide`, les exemples, les fonctions prédéfinies, la spécification), puis de se
servir du compilateur pour vérifier, corriger et exécuter ce qu'elle écrit. Ce guide décrit ce
qu'il offre, ses limites, et comment le brancher. Son code est décrit dans
l'[architecture](architecture.md#9-le-serveur-mcp).

## 1. Installer

Le serveur dépend du SDK Python `mcp` (version 2), dans un groupe de dépendances à
part : le compilateur, lui, n'en a aucune. `uv sync` l'installe avec les outils de
développement ; pour le serveur seul : `uv sync --no-dev --group mcp`. Sans le SDK,
`python -m upea mcp` le dit, et rend le code 2.

Pour vérifier qu'il démarre, depuis `projet/` : `uv run python -m upea mcp` doit
rester silencieux, en attente d'un client sur son entrée standard (Ctrl-C l'arrête).

## 2. Ce que l'IA lit en se connectant

À la connexion, le serveur envoie ses **instructions** : ce qu'est Upea, et la
démarche. L'IA appelle `aide("apercu")` (une page, environ 4 Kio), écrit son
programme, le vérifie avec `verifier` jusqu'à ce qu'il n'ait plus d'erreur, puis
l'exécute avec `executer` ; `tokenize` et `parse` aident à comprendre une erreur de
lexique ou de syntaxe. Le serveur expose aussi des ressources et des prompts. Mais ce
qu'une IA en voit dépend de **qui choisit** :

| Ce que le serveur expose | Qui le choisit |
|---|---|
| un outil | **le modèle**, de lui-même |
| une ressource | l'application, ou l'utilisateur |
| un prompt | l'utilisateur |

**Seuls les outils sont appelés par le modèle de lui-même.** Tout ce qu'une IA doit
pouvoir consulter seule doit donc être un outil : c'est le rôle de `aide` et de
`exemples` (section 3). Les ressources et les prompts restent, pour les clients qui les
affichent (dans Claude Code, `@upea:upea://specification` cite une ressource).

### Un client qui n'affiche que les outils

Un client peut ne transmettre que les outils : ni ressources, ni prompts, ni
instructions. C'est ce qui s'est passé lors de la première session de l'exercice final
(voir le [journal](journal/index.md)) : un pont entre l'IA et le serveur ne lui laissait
voir que les six outils d'alors, et leurs descriptions ne disaient rien du langage. Pour
que ce cas marche, le serveur ne compte que sur ses outils :

- chaque description d'outil commence par la même phrase, « Upea est un langage aux
  mots-clés tahitiens, transpilé en Python. Si tu ne le connais pas, appelle d'abord
  aide("apercu"). » ;
- `aide("apercu")` est un aide-mémoire d'une page, avec un exemple complet ;
- `verifier` dit, dans le message d'erreur, quand un mot est d'un autre langage
  (`si`, `while`, `print`…) et quoi écrire à la place.

Les mêmes textes sont dans le dépôt, pour un lecteur humain :
l'[aide-mémoire](aide-memoire.md), et [de Python à Upea](depuis-python.md).

## 3. Les outils

Aucun outil n'a d'effet de bord, et tous sont annoncés comme tels. Une erreur du
**programme** (de syntaxe, de type, d'exécution) n'est pas un échec de l'outil : c'est
un résultat, que l'IA lit pour corriger. L'outil n'échoue (`isError`) que s'il ne peut
pas faire son travail.

| Outil | Paramètres | Résultat | Échec de l'outil |
|---|---|---|---|
| `aide` | `sujet` (`apercu`, `mots_cles`, `predefinies`, `depuis_python` ou `specification`), `section` (facultatif, pour `specification`) | du texte Markdown. Un nom de section inconnu rend la liste des sections | sujet inconnu |
| `exemples` | `nom` (facultatif) | du texte Markdown : sans nom, la liste des exemples ; avec un nom, son source et sa sortie exacte. Un nom inconnu rend la liste des noms | aucun |
| `tokenize` | `source` | `valide`, `jetons` (chacun `sorte`, `texte`, `ligne`, `colonne` ; sur une erreur lexicale, ceux lus avant elle), `diagnostics`, `rapport` | source trop longue |
| `parse` | `source` | `valide`, `arbre` (chaque nœud a un `type`, ses champs, sa `ligne` et sa `colonne` ; `null` s'il y a des erreurs), `diagnostics`, `rapport` | source trop longue |
| `verifier` | `source`, `types` (vrai par défaut) | `valide`, `diagnostics`, `rapport` | source trop longue |
| `formater` | `source` | `code` (le programme réécrit, ou `null`), `diagnostics`, `rapport` | source trop longue |
| `transpiler` | `source`, `backend` (`python` ou `ast`), `avec_prelude` (faux par défaut) | `code` (ou `null`), `diagnostics`, `rapport` | source trop longue, backend inconnu |
| `executer` | `source`, `types`, `backend`, `delai` (de 0,1 à 5 s, 5 par défaut) | `statut` (`succes`, `erreur_compilation` ou `erreur_execution`), `code_retour` (0, 1 ou 3, comme `run`), `sortie`, `tronquee`, `octets`, `diagnostics`, `rapport` | source trop longue, délai hors des bornes, délai dépassé, panne du processus |

`aide` et `exemples` ne lisent que des textes que le serveur a déjà : les sujets sont
l'aide-mémoire, les mots-clés (avec leur équivalent Python, et les mots d'autres
langages qu'Upea ne connaît pas), le catalogue des fonctions prédéfinies, la
traduction depuis Python, et la spécification, qu'on lit par sections
(`section="grammaire"`, `section="boucle_tataitahi"`) : sans section, le sommaire,
et `section="tout"` rend les 44 Kio. Ils ne font rien d'autre, et le serveur
les annonce en lecture seule, idempotents, sans accès au monde extérieur.

Un diagnostic a une `sorte` (`lexicale`, `syntaxe`, `semantique`, `type`,
`avertissement` ou `execution`), une `ligne` et une `colonne` (à partir de 1, ou
`null`), et un `message`. Le `rapport` donne les mêmes erreurs mises en forme comme par
la CLI. `parse` ne fait que l'analyse syntaxique : un nom non déclaré y passe, et
`verifier` le refuse. Les avertissements ne sont signalés que pour un programme sans
erreur.

Par exemple, `verifier` sur `tuu x = 1;` puis `faaite y;` rend :

```json
{
  "valide": false,
  "diagnostics": [
    {
      "sorte": "semantique",
      "ligne": 2,
      "colonne": 8,
      "message": "'y' n'est pas déclaré"
    }
  ],
  "rapport": "programme.upea:2:8 : erreur sémantique : 'y' n'est pas déclaré\n    faaite y;\n           ^"
}
```

Quand l'erreur porte sur un mot d'un autre langage, le message garde son texte, puis
ajoute un conseil. `verifier` sur un `si` écrit à la place de `ahani` rend :

```json
{
  "valide": false,
  "diagnostics": [
    {
      "sorte": "syntaxe",
      "ligne": 2,
      "colonne": 3,
      "message": "';' attendu après l'expression, trouvé 'x' — 'si' n'est pas un mot-clé d'Upea : écrivez 'ahani'"
    }
  ],
  "rapport": "programme.upea:2:3 : erreur de syntaxe : ';' attendu après l'expression, trouvé 'x' — 'si' n'est pas un mot-clé d'Upea : écrivez 'ahani'\n    si x > 1 {\n      ^"
}
```

Le conseil ne vient que d'une erreur : une variable que le programme déclare peut
s'appeler `si` ou `et`, sans qu'on l'accuse. Affecter un nom jamais déclaré
(`compteur = 0;`, l'habitude de Python) propose de le déclarer d'abord.

Et `executer` sur `faaite 6 * 7;` :

```json
{
  "statut": "succes",
  "code_retour": 0,
  "sortie": "42\n",
  "tronquee": false,
  "octets": 3,
  "diagnostics": [],
  "rapport": "aucune erreur"
}
```

Un programme qui ne s'arrête pas est un échec de l'outil, avec la fin de ce qu'il
avait affiché (au plus 2 000 caractères) : `executer` sur `tamau tia { }`, avec un
délai de 1 s, rend « délai de 1 s dépassé : le programme a été arrêté (une boucle sans
fin ?) ; il n'avait rien affiché ».

## 4. Les ressources

Toutes en Markdown. Elles donnent les mêmes textes que les outils `aide` et `exemples`,
pour les clients qui affichent les ressources (voir la section 2) :

| Ressource | Contenu |
|---|---|
| `upea://specification` | la spécification complète |
| `upea://exemples` | la liste des exemples, chacun avec ce qu'il montre |
| `upea://exemples/{nom}` (par exemple `upea://exemples/05_motu`) | un exemple et sa sortie exacte ; chaque exemple est aussi une ressource fixe, pour apparaître dans la liste des ressources |
| `upea://predefinies` | la signature de chaque fonction prédéfinie, tirée du compilateur (`pihai(upea[T], T) -> tapura[T]`) |

Un nom d'exemple inconnu est refusé, avec la liste des noms ; un nom qui contient un
chemin (`..%2Fspecification`) aussi.

## 5. Les prompts

| Prompt | Paramètres | Ce qu'il demande |
|---|---|---|
| `ecrire_programme` | `tache` | écrire un programme Upea qui accomplit la tâche |
| `corriger_programme` | `source`, `erreurs` | corriger un programme d'après les erreurs reçues |
| `traduire_depuis_python` | `code` | traduire un programme Python en Upea, qui affiche la même chose |

Chacun rappelle la même démarche : lire la spécification, écrire, vérifier jusqu'à ce
qu'il n'y ait plus d'erreur, exécuter, et donner la sortie réellement produite.
`traduire_depuis_python` ajoute les pièges d'une traduction depuis Python.

## 6. Le bac à sable

`executer` lance le programme dans un sous-processus, `python -m upea.bac_a_sable`,
avec ces limites :

| Limite | Valeur | Constante |
|---|---|---|
| délai par défaut, et le plus long | 5 s, démarrage de Python compris | `bac_a_sable.DELAI` |
| délai le plus court | 0,1 s | `serveur_mcp.DELAI_MINIMAL` |
| sortie gardée | 64 Kio | `bac_a_sable.PLAFOND` |
| mémoire (Windows, Linux ; aucune sous macOS) | 512 Mo | `bac_a_sable.PLAFOND_MEMOIRE` |
| temps CPU, posé par l'enfant lui-même | deux fois le délai | `bac_a_sable.MULTIPLE_CPU` |
| exécutions simultanées (les suivantes attendent leur tour) | 2 | `serveur_mcp.EXECUTIONS_SIMULTANEES` |
| taille d'un source, pour tous les outils | 100 Kio | `serveur_mcp.TAILLE_MAX_SOURCE` |

L'enfant ne reçoit pas l'environnement du serveur : seulement `PYTHONPATH`,
`PYTHONUTF8`, `PYTHONIOENCODING`, `NO_COLOR`, et `SYSTEMROOT` sous Windows. Ce que le
bac à sable protège, et ce qu'il ne protège pas, est écrit dans la docstring de
`projet/upea/bac_a_sable.py` : en bref, un programme Upea ne peut que calculer et
afficher, et rien dans un programme ne devient du Python que le compilateur n'a pas
prévu ; le bac à sable borne ce qu'un programme valide peut faire de mal, mais l'enfant
garde les droits de l'utilisateur qui lance le serveur.

## 7. Brancher le serveur

Claude Code et Claude Desktop ne fixent pas le dossier courant du serveur :
`uv run --directory` s'en charge. Dans les commandes ci-dessous, remplacer `<uv>` par
le chemin de `uv` (absolu s'il n'est pas dans le `PATH`, par exemple
`C:\Users\<vous>\AppData\Roaming\Python\Python311\Scripts\uv.exe`) et `<dépôt>` par le
chemin absolu du dépôt. [`projet/mcp.exemple.json`](../projet/mcp.exemple.json) donne
la configuration type, que les tests vérifient.

**Claude Code** ([documentation](https://code.claude.com/docs/en/mcp)) :

```bash
claude mcp add --transport stdio --scope user upea -- <uv> run --directory <dépôt>/projet python -m upea mcp
claude mcp list        # upea doit être « Connected »
```

`--scope user` rend le serveur disponible dans tous les projets (sans cette option,
dans le seul dossier courant). Dans une session, `/mcp` montre son état,
`@upea:upea://specification` cite une ressource, et `/mcp__upea__ecrire_programme`
lance un prompt. Sous Windows PowerShell 5.1, si `claude` est un script PowerShell
(installation par npm), PowerShell peut retirer le `--` : lancer alors la commande
depuis `cmd` ou Git Bash.

**Claude Desktop** ([documentation](https://modelcontextprotocol.io/docs/develop/connect-local-servers)) :
dans `claude_desktop_config.json` (`%APPDATA%\Claude\` sous Windows,
`~/Library/Application Support/Claude/` sous macOS), puis quitter complètement
Claude Desktop et le relancer :

```json
{
  "mcpServers": {
    "upea": {
      "command": "C:\\Users\\<vous>\\AppData\\Roaming\\Python\\Python311\\Scripts\\uv.exe",
      "args": ["run", "--directory", "C:\\<dépôt>\\projet", "python", "-m", "upea", "mcp"]
    }
  }
}
```

**MCP Inspector** (une application Node.js, ≥ 22.19 ; rien à installer côté
Python) :

```bash
npx @modelcontextprotocol/inspector <uv> run --directory <dépôt>/projet python -m upea mcp
npx @modelcontextprotocol/inspector --cli <uv> run --directory <dépôt>/projet python -m upea mcp --method tools/list
```

## 8. Dépannage

- **Le serveur ne démarre pas dans l'hôte** : lancer exactement la commande de la
  configuration dans un terminal. Elle doit rester silencieuse, en attente ; une erreur
  affichée est celle que voit l'hôte. Dans Claude Code, `/mcp` montre l'état des
  serveurs.
- **Le journal de Claude Desktop** : la sortie d'erreur du serveur est dans
  `%APPDATA%\Claude\logs\mcp-server-upea.log` (`~/Library/Logs/Claude/` sous macOS).
- **« le serveur MCP demande le SDK Python `mcp` »** : l'environnement a été installé
  sans le groupe `mcp` ; `uv sync` le rétablit.
- **Un délai dépassé dès le premier appel** : le tout premier lancement, à froid, peut
  être lent (voir les *Limites connues* de [`NOTES.md`](../NOTES.md)).

## 9. Écarts avec le projet MCP du cours

Le serveur suit le parcours du cours (`mcp/`), avec quelques différences : un module
de la CLI plutôt qu'un paquet à part, des résultats en dataclasses, des tests nommés
`test_extension_18_*`. La table complète est dans [`NOTES.md`](../NOTES.md).
