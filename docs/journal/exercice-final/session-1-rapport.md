# Rapport d'utilisation du serveur MCP Upea

Point de vue : un utilisateur "lambda" (un assistant IA) qui découvre le serveur sans documentation préalable.
Date : 6 novembre 2026. Tâche d'origine : traduire un programme Python (taquin) en Upea.

## 1. Ce que j'ai réellement fait (base du rapport)

| # | Appel | Résultat |
|---|-------|----------|
| 1 | `executer` avec `faaite("Ia ora na");` | Succès, sortie `Ia ora na\n` |
| 2 | `tokenize` sur un faux programme (si / sinon / tant que / arbre) | `valide: true`, `tuu` et `faaite` reconnus comme mots-clés, tout le reste en `IDENT` |
| 3 | `verifier` sur `tuu x = 1; faaite(x);` | Valide |
| 4 | `verifier` sur `blabla;` | Erreur sémantique propre : `'blabla' n'est pas déclaré` (ligne 1, colonne 1) |
| 5 | `ListMcpResourcesTool` sur le serveur `upea` | Échec : serveur introuvable, seul `visualize` est listé |

**Non testés, donc non évalués :** `parse`, `formater`, `transpiler`, les erreurs de syntaxe, les erreurs d'exécution, les timeouts, la vérification de types, le prélude (arbres, graphes, algorithmes). Tout ce qui suit sur ces points est une hypothèse.

## 2. Points forts (constatés)

- Les descriptions d'outils sont claires : elles disent quand s'en servir, dans quel ordre (`verifier` puis `executer`), avec les limites chiffrées (5 s, 512 Mo, 64 Kio de sortie).
- Le message "une erreur de programme n'est pas une panne de l'outil" évite de confondre un échec du code et un échec du serveur.
- Les diagnostics ont une ligne, une colonne et une `sorte` (lexicale, syntaxe, semantique, type, avertissement), plus un `rapport` formaté avec `^`.
- Les messages d'erreur sont en français et en termes d'Upea.
- `executer` a fonctionné du premier coup, sans installation ni configuration.

## 3. Points bloquants et difficultés

### 3.1 Aucune référence du langage accessible (bloquant principal)

- Les descriptions citent `tuu`, `faaite`, `hoi`, `faaea`, `haere` sans jamais les définir. J'ai déduit seulement que `faaite` affiche et que `tuu` déclare.
- Je n'ai trouvé ni ressource MCP, ni outil `aide` ou `reference`, ni grammaire, ni liste des mots-clés, ni exemples.
- Le prélude est décrit comme "arbres, graphes, algorithmes et fonctions prédéfinies" (environ 2 500 lignes), mais aucun outil n'en donne le catalogue (noms, signatures). Je ne peux donc pas savoir ce qu'Upea offre déjà.
- Conséquence : impossible de traduire un programme réel sans que l'utilisateur me donne la spec.

### 3.2 Découvrir le langage par essais est inefficace

- Au niveau lexical, tout mot inconnu devient `IDENT`. `tokenize` ne signale donc pas qu'un mot est probablement un mot-clé mal orthographié ou d'un autre langage.
- `tokenize` rend `valide: true` pour un programme absurde. C'est normal, mais ça ne m'aide pas à deviner la syntaxe.
- Le message `'blabla' n'est pas déclaré` ne propose rien ("vouliez-vous dire…", liste des mots-clés proches).
- Piste de contournement que je n'ai pas encore exploitée : envoyer une longue liste de mots à `tokenize` et repérer ceux qui deviennent un token autre que `IDENT`. Il faudrait quand même deviner les mots à tester.

### 3.3 Découvrabilité du serveur

- Les outils étaient "différés" : il a fallu un `ToolSearch` pour charger leurs schémas avant tout appel.
- Le bloc d'instructions MCP de la session ne contenait que celles de `claude-in-chrome`. Je n'ai reçu aucune instruction propre à Upea (workflow conseillé, résumé du langage).
- Le nom d'outil (`mcp__remote-devices__upea__*`) ne correspond pas au nom de serveur attendu par `ListMcpResourcesTool` (`upea`). Je ne sais donc pas si le serveur n'expose réellement aucune ressource ou s'il est simplement injoignable par ce biais.

### 3.4 Limites du langage non signalées au bon endroit

- La contrainte "ni clavier, ni fichier, ni réseau" n'apparaît que dans la description d'`executer`. Elle est décisive pour traduire n'importe quel programme interactif (`input()`).
- Je ne sais pas s'il existe un équivalent de l'aléatoire (`randint`). Information absente.

## 4. Recommandations, par ordre de priorité

1. **Exposer la référence du langage** : ressources MCP (spec, grammaire, table des mots-clés avec leur équivalent Python, catalogue du prélude avec signatures) ou un outil `aide(sujet)` / `reference()`.
2. **Ajouter des instructions de serveur** : 10 à 15 lignes avec le workflow (`verifier` puis `executer`), un mini-programme exemple, et les limites (pas d'entrée, pas de fichier, pas de réseau).
3. **Fournir des exemples** : un outil ou une ressource `exemples` avec 5 à 10 programmes courts (boucle, fonction, arbre, graphe, parcours).
4. **Améliorer les erreurs** : suggestions de mots proches ; sur une erreur de syntaxe, indiquer ce qui était attendu ("attendu : `;` ou `}`").
5. **Mots-clés reconnus par `tokenize`** : ajouter un champ ou un outil `mots_cles()` listant tous les mots réservés.
6. **`formater`** : conserver les commentaires, car les perdre rend l'outil risqué sur du code documenté.
7. **Cohérence des noms** : aligner le nom de serveur et le préfixe d'outils, pour que les ressources soient interrogeables.

## 5. Ce qui m'aurait permis de réussir la tâche (traduction du taquin)

- La spec ou des exemples : syntaxe des fonctions, des conditions et des boucles, structures de données (listes, ensembles, dictionnaires, chaînes).
- La liste des fonctions de graphes et d'arbres du prélude, pour écrire une recherche BFS ou A* sans tout recoder.
- La confirmation qu'il n'y a ni entrée utilisateur ni aléatoire, ou comment les remplacer.

## 6. Verdict

Les outils eux-mêmes (`verifier`, `executer`) sont fiables et bien décrits sur ce que j'ai testé. Le frein est l'absence de documentation interrogeable : sans elle, un assistant ne peut ni écrire du Upea correct du premier coup, ni apprendre le langage seul de manière économique.