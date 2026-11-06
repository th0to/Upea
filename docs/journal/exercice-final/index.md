# L'exercice final du projet MCP

Le dernier exercice du parcours MCP du cours : brancher le serveur sur une IA qui ne
connaît pas le langage, lui faire traduire un vrai programme, et regarder ce qui
l'arrête. Il se fait en deux sessions, séparées par un travail de correction.

| | Quand | Quoi |
|---|---|---|
| Session 1 | 6 novembre 2026 | une IA découvre le serveur, et échoue : [son rapport](session-1-rapport.md) |
| Correction | 6 novembre 2026 | les lots A0, C, A, B, D et E (voir plus bas) |
| Session 2 | à faire | la même tâche, avec le serveur corrigé : [son rapport](session-2-rapport.md) |

## La session 1 : ce qui s'est passé

Une IA, qui ne connaissait pas Upea, a reçu une tâche : traduire en Upea un programme
Python, un taquin. Elle a réussi à exécuter `faaite("Ia ora na");`, à vérifier un
programme de deux lignes, et à provoquer une erreur de noms. Elle n'a pas pu traduire
son programme : aucune référence du langage ne lui était accessible. Son
[rapport](session-1-rapport.md) est conservé tel quel.

## L'analyse

L'analyse du rapport, puis sa vérification sur le serveur (`PLAN_AIDE.md`, à la racine
du dépôt), ont donné ces causes :

1. **L'IA n'a vu que les outils.** Ni les ressources (`upea://specification`,
   `upea://exemples/{nom}`, `upea://predefinies`), ni les prompts n'ont été transmis par
   le client, qui passait par un pont. Et même branché directement, le problème reste :
   en MCP, une ressource est choisie par l'application ou l'utilisateur, un prompt par
   l'utilisateur, et **seuls les outils sont appelés par le modèle de lui-même**. Les
   instructions du serveur, elles, disaient de lire la spécification : une ressource.
2. **Les descriptions des outils**, seuls textes garantis d'arriver jusqu'à l'IA, ne
   donnaient aucune base du langage.
3. **Les messages d'erreur n'aidaient pas à deviner la syntaxe.** `si x > 1 { … }` donnait
   « ';' attendu après l'expression, trouvé 'x' », sans dire que `si` n'est pas un
   mot-clé d'Upea. Deux suggestions de nom proche étaient fausses (`vrai` → `rahi`,
   `print` → `prim`).
4. Il manquait une page qui explique comment passer de Python à Upea, et comment
   remplacer ce qu'Upea n'a pas.

Trois points du rapport n'ont pas été traités : l'absence de suggestion pour `blabla`
est normale (aucun nom proche n'existe) ; le nom des outils vu par l'IA
(`mcp__remote-devices__upea__*`) vient du pont, pas du serveur ; garder les commentaires
dans `formater` est une limite documentée, trop coûteuse à lever.

## Ce qui a été fait

Le code était gelé ; il ne l'a été levé que pour cette mission. La spécification
(`projet/specification.md`) n'a pas changé.

| Lot | Commit | Ce qui change |
|---|---|---|
| A0 | `9c863b5` | `upea/aide.py` : une source unique des textes d'aide, sans le SDK |
| C | `cdc0d73` | les messages d'erreur disent qu'un mot est d'un autre langage (`si` → `ahani`) |
| A | `efaeda7` | les outils `aide` et `exemples` : ce que l'IA doit consulter seule est un outil |
| B | `540b883` | chaque description d'outil, et les instructions, commencent par la même phrase |
| D | `0de8a91` | l'[aide-mémoire](../../aide-memoire.md), [de Python à Upea](../../depuis-python.md), le guide MCP corrigé |
| E | ce dossier | le scénario de l'exercice, joué par un test ; ce journal |

Le test `test_extension_18_exercice_final.py` joue le client naïf : il ne lit que la
liste des outils, constate que chaque description le renvoie à `aide("apercu")`, appelle
`aide("apercu")`, écrit un programme avec ce que cette page lui montre, se fait dire par
`verifier` que `si` n'est pas d'Upea, corrige, et exécute. Il ne remplace pas la
session 2 : un test ne dit pas ce qu'un modèle comprend de ces textes.

## La session 2 : le texte à donner

À donner à une IA **neuve** (aucune mémoire de la session 1, aucune documentation d'Upea),
branchée sur le serveur **de la même façon qu'en session 1**, par le même client et le
même pont : c'est ce qui rend la comparaison honnête. Remplacer la ligne marquée par le
programme Python du taquin de la session 1. Noter avant de lancer : la date, et le
commit du dépôt (`git rev-parse --short HEAD`).

````text
Tu découvres un langage de programmation, Upea, à travers un serveur MCP nommé « upea »
dont tu disposes des outils. Tu n'as aucune documentation du langage, et tu n'en
demandes pas à l'utilisateur : tout ce que tu apprends, tu l'apprends des outils du
serveur.

Ta tâche : traduire en Upea le programme Python ci-dessous (un taquin), l'exécuter avec
le serveur, puis me donner le programme Upea final et la sortie qu'il a réellement
produite.

```python
<COLLER ICI LE PROGRAMME PYTHON DU TAQUIN UTILISÉ EN SESSION 1>
```

Règles :
- N'invente pas ce que tu ne vois pas. Si un outil échoue, ou si une information manque,
  dis-le.
- Note chaque appel d'outil que tu fais, dans l'ordre, et ce qu'il t'a appris.
- Si tu ne parviens pas à finir, dis précisément ce qui t'a bloqué.

Quand tu as fini, ou que tu es bloqué, rends un rapport en Markdown, au même format que
celui-ci. Titre : « Rapport d'utilisation du serveur MCP Upea ». Point de vue : un
utilisateur « lambda » (un assistant IA) qui découvre le serveur sans documentation
préalable. Puis la date, et la tâche d'origine. Puis ces sections, dans cet ordre :

## 1. Ce que j'ai réellement fait (base du rapport)
Un tableau « # | Appel | Résultat » de tes appels réels, puis ce que tu n'as pas testé
(« Non testés, donc non évalués »), sans l'évaluer.

## 2. Points forts (constatés)
Seulement ce que tu as constaté.

## 3. Points bloquants et difficultés
Avec, pour chacun, ce qui s'est passé et ce qu'il t'a coûté.

## 4. Recommandations, par ordre de priorité
Numérotées, de la plus utile à la moins utile.

## 5. Ce qui m'aurait permis de réussir la tâche (traduction du taquin)
Ce qui t'a manqué, précisément.

## 6. Verdict
Deux ou trois phrases : les outils suffisent-ils pour apprendre ce langage et écrire un
programme correct ?

Dans le rapport, distingue toujours ce que tu as constaté de ce que tu supposes.
````

Ce que le texte ne dit pas, exprès : aucun mot d'Upea, aucun nom d'outil, aucun conseil
de démarche. Il ne dit même pas d'appeler `aide` : c'est la phrase qui ouvre chaque
description d'outil qui doit l'apprendre à l'IA. Un test (`test_extension_18_exercice_final.py`)
vérifie qu'il ne cite aucune construction du langage, et qu'il reprend les six titres
du rapport de la session 1.

## Les observations de Thomas

Ce qu'on regarde, d'après la consigne du cours : l'IA lit-elle l'aide avant d'écrire ?
quelles erreurs fait-elle, et les messages de `verifier` lui suffisent-ils pour corriger ?
combien d'allers-retours avant un programme correct ? ce qui a été amélioré ensuite.

<!-- À RÉDIGER PAR THOMAS -->
