# Session 2a : le rapport de l'IA

> Rapport collé tel quel ci-dessous. Session du 2026-11-06, faite avec un serveur MCP lancé
> avant les lots A0 à E : il gardait l'ancien code chargé (6 outils, ni `aide` ni `exemples`).
> Le client et le pont sont les mêmes qu'en session 1.

---

# Rapport d'utilisation du serveur MCP Upea

**Point de vue :** un utilisateur « lambda » (un assistant IA) qui découvre le serveur sans documentation préalable.
**Date :** 2026-11-06
**Tâche d'origine :** traduire en Upea le taquin `taquin_3.py`, l'exécuter avec le serveur, puis rendre le programme Upea final et sa sortie réelle. Le bloc de la consigne contenait encore le marqueur « COLLER ICI… » ; j'ai utilisé le fichier `taquin_3.py` joint.

## 1. Ce que j'ai réellement fait (base du rapport)

Le serveur annonce dans ses instructions des ressources `upea://specification`, `upea://predefinies` et `upea://exemples`. Je n'ai aucun outil pour les lire, donc je ne les ai pas lues. Tout ce qui suit vient des six outils (`verifier`, `executer`, `parse`, `tokenize`, `transpiler`, `formater`) et de leurs messages d'erreur.

| # | Appel | Résultat |
|---|---|---|
| 1 | `verifier` : `tuu x = 1; faaite(x);` | Valide. `tuu` déclare, `faaite` affiche. |
| 2 | `tokenize` du même code | Tokens `TUU`, `FAAITE`, `IDENT`… |
| 3 | `executer` : fonction `ohipa`, `faaite(f(1,2), l, …)`, boucle `ahani (tuu i…)` | Erreurs de syntaxe. `faaite` prend une seule expression, et il n'y a pas de `for` à la C. |
| 4 | `executer` : `faaite f(1,2); … ahani i<3 {…}` | Sortie `3`, `[1, 2, 3]`, `0`. La boucle n'a tourné qu'une fois : `ahani` est un « si ». `ohipa` définit une fonction, `hoi` retourne. |
| 5 | `transpiler` : `ahoi` et `tataitahi i < 3` | Erreur : `tataitahi x roto L` est un « pour chaque ». `ahoi` n'est pas un « sinon ». |
| 6 | `tokenize` d'un lot de mots tahitiens (3 appels, dont un arrêté par une apostrophe, erreur lexicale) | Mots-clés trouvés : `faaea`, `haere`, `hoi`, `mai`, `upea`, `eiaha`, `aore`, `roto`, `ma`, `tamau`, `mau`. |
| 7 | `executer` : `tamau i<3 {…}` puis `ahani … aore {…}` | `tamau` est accepté (tant que). `aore { … }` est refusé comme « sinon ». |
| 8 | `parse` de `faaite … aore …`, `ma`, `eiaha`, `mau` | `ma` et `eiaha i` sont acceptés. `mau` est une déclaration. `aore` n'est pas un opérateur infixe. |
| 9 | `parse` : `aore ahani…`, `aore i==4 {…}`, `aore;` | Les deux premiers sont refusés. `aore;` est accepté comme expression : `aore` est une valeur. |
| 10 | `tokenize` (2 lots) | Autres mots-clés trouvés : `tia`, `hape`. Aucun ne s'est révélé être un « sinon ». |
| 11 | `verifier` avec des noms inventés (`aleatoire`, `randint`, `len`, `str`…) | « non déclaré » avec suggestions : `ancetre`, `largeur`, `teitei`. Cela montre que les prédéfinies ont des noms tahitiens. |
| 12 | `transpiler` avec `avec_prelude=true` | 94 908 caractères, trop gros pour l'affichage. Le résultat a été sauvegardé dans un fichier. J'ai lu ce fichier avec mes propres outils (Grep, Bash), pas avec le serveur. |
| 13 | `executer` : `//`, `ou`, indices, `%`, `/` | `//` commence un commentaire (pas de division entière). `ou` est refusé avec le message « écrivez `anei` ». `tia` s'affiche `tia`, `hape` est le faux, `aore` s'affiche `aore`. `/` donne 3.5 (division réelle). |
| 14 | `parse` : `else`, `sinon`, `while` | Rejetés, sans indice sur le vrai mot pour « sinon ». |
| 15 | `verifier` puis `executer` (fonctions de base du taquin) | Valide. Sortie `312045678`, mais `alea` rendait des flottants. J'ai corrigé avec `numera(x / 65536)`. |
| 16 | `executer` du programme complet | `erreur_compilation` : `'graph' n'est pas déclaré`. La recursion mutuelle (`explore` appelle `graph`, qui appelle `explore`) est impossible. J'ai fusionné les deux fonctions. |
| 17 | `executer` du programme final | **Succès**, voir ci-dessous. |

Le fichier du programme final est [taquin.upea](taquin.upea).

**Sortie réelle du programme final** (statut `succes`, code 0) :
```
melange :
[[0, 2, 3], [4, 8, 1], [5, 7, 6]]
chaine : 023481576
[[[0, 4, 2], [1, 3, 5], [6, 7, 8]], [0, 0]]
resultat graph (maximum 4) :
aore
noeuds du graphe :
45
```
J'ai refait à la main la suite de coups `droite, bas, gauche, haut` : le résultat est cohérent. Je n'ai pas exécuté le Python d'origine, donc je n'ai pas comparé ses résultats à ceux d'Upea.

**Non testés, donc non évalués :** `formater`, `transpiler` avec `backend="ast"`, `executer` avec `types=false`, le délai (`delai`), la troncature de sortie, les structures `tumu` et `upea` (arbres et graphes natifs), `faaea` et `haere`, les fonctions `iti`, `rahi`, `tuhaa`, `tatara`, et le « sinon ».

## 2. Points forts (constatés)

- `verifier` est rapide, et les erreurs sont précises : ligne, colonne, ligne fautive soulignée.
- Plusieurs messages guident vraiment : `ou` → « écrivez `anei` », `tataitahi` → « `roto` attendu », « vouliez-vous dire… ».
- `executer` renvoie un statut, un code et la sortie. Une erreur de programme est un résultat, pas une panne de l'outil.
- `tokenize` et `parse` permettent de deviner des mots-clés par essais.
- Le prélude transpilé (`avec_prelude=true`) contient le vocabulaire complet (`roa`, `amui`, `numera`, `parau`…).

## 3. Points bloquants et difficultés

1. **Aucune documentation lisible avec ces six outils.** Les instructions renvoient à des ressources `upea://…` que je ne peux pas ouvrir. Coût : environ 15 appels de devinette sur les mots-clés.
2. **Le mot-clé « sinon » reste introuvable.** `aore`, `ahoi`, `else` et `sinon` ont échoué, sans suggestion. Je l'ai contourné avec des `ahani` successifs et `eiaha`.
3. **Pas de fonction aléatoire prédéfinie** (`randint` absent), à ma connaissance. J'ai écrit un générateur congruentiel ; la partie « mélange » diffère donc de l'original.
4. **Pas de recursion mutuelle** (déclaration obligatoire avant usage). Coût : une exécution ratée et une refonte de `graph`.
5. **Les noms des prédéfinies ne se découvrent que par le prélude** (95 k caractères, hors limite d'affichage). J'ai dû passer par un fichier sauvegardé et mes propres outils.
6. `/` donne toujours un réel, `//` est un commentaire : l'entier demande `numera(a / b)`. C'est piégeux (premier `alea` faux).
7. **Pas d'entrée clavier** : la boucle `jeu()` du Python n'est pas traduisible telle quelle.

## 4. Recommandations, par ordre de priorité

1. Exposer les ressources de spécification via un outil (par exemple `documentation`), ou en mettre un résumé dans les instructions du serveur.
2. Donner la liste des mots-clés et des prédéfinies par un outil dédié, plutôt que par le prélude entier.
3. Ajouter pour `else` / `sinon` / `while` / `len` le même type d'indice que pour `ou` → `anei`.
4. Documenter ou lever la limite sur la recursion mutuelle (déclaration anticipée).
5. Prévoir une fonction aléatoire (`aleatoire`) ou l'annoncer comme absente.
6. Permettre un prélude paginé ou filtré (`transpiler`).

## 5. Ce qui m'aurait permis de réussir la tâche (traduction du taquin)

Il m'a manqué : le mot-clé du « sinon », une source aléatoire, la règle sur la recursion mutuelle, la liste des prédéfinies, et un moyen d'écrire un jeu interactif. La traduction est donc **partielle et approchée** : classes remplacées par des listes (`[grille, [ligne, colonne]]`, arbre `[valeur, enfants]`), `main()` et la saisie remplacés par des coups scriptés, graphe borné à 4 coups (24 coups seraient hors du délai de 5 s). L'original ne fait que `print(j.graph(j.g))` ; en Upea cela donne `aore` (équivalent de `None`).

## 6. Verdict

Les outils suffisent pour écrire et corriger un programme Upea de taille moyenne par essais et erreurs : les diagnostics sont de bonne qualité. En revanche, ils ne suffisent pas pour *apprendre* le langage sans documentation : sans accès aux ressources, plusieurs notions (sinon, aléatoire, recursion mutuelle) se découvrent par échec, voire restent inconnues. Le programme final est correct sur ce que j'ai vérifié, mais pas démontré équivalent à l'original.

**Programme Upea final :** voir [taquin.upea](taquin.upea). Il contient exactement le code exécuté à l'appel n° 17.
