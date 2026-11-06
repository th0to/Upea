# Plan : l'aide à l'IA (suite de l'extension 18)

Ce plan répond au rapport de la session 1 (`docs/journal/exerciceFinal/session-1-rapport.md`).
Il ne change ni la spécification ni le langage. **Rien n'est encore écrit dans le code** :
la phase 2 attend ta validation.

## 0. État des lieux (phase 0)

- `git status --short` : vide. (Le commit `51bc06d « v2.5 »` a absorbé `NOTES.md`, le rapport
  de la session 1 et `Claude outputs/` avant que je commence.)
- `uv run pytest projet` : **1 362 réussis, 4 ignorés** (180 s). Tu attendais 1 361 : il y a un
  test de plus, sans conséquence ; je prends 1 362 comme référence. Les 4 ignorés sont ceux de
  Graphviz, absent de la machine.
- `mypy projet --platform win32 | linux | darwin` : « no issues found in 75 source files » (×3).
- `ruff check projet` : « All checks passed ! » ; `ruff format --check projet` : « 76 files
  already formatted ».

**Écart de nom** : le dossier existant est `docs/journal/exerciceFinal/` ; ta consigne, `NOTES.md`
(ligne 161) et `docs/journal/index.md` (ligne 44) écrivent `exercice-final/`. Voir D7.

## 1. Vérification de l'analyse (phase 1a)

Script : `scratchpad/verif.py`, avec `Client(construire_serveur())` en mémoire (le SDK `mcp` 2.x).

### Point 1 : ce que le serveur expose

| Quoi | Résultat |
|---|---|
| Outils (6) | `tokenize`, `parse`, `verifier`, `formater`, `transpiler`, `executer`, tous `read_only=True`, `idempotent=True`, `open_world=False` |
| Ressources (13) | `upea://specification`, `upea://exemples`, les dix `upea://exemples/NN_nom`, `upea://predefinies` |
| Gabarit (1) | `upea://exemples/{nom}` |
| Prompts (3) | `ecrire_programme`, `traduire_depuis_python`, `corriger_programme` |
| Instructions | **présentes** (`Client.instructions`, 637 caractères) : elles disent de lire `upea://specification` |

**Confirmé, avec une nuance.** Le serveur envoie bien ses instructions, ses ressources et ses
prompts. Mais tout ce qu'elles disent de faire passe par des *ressources*, qu'un client « outils
seuls » ne voit pas, et que le modèle ne lit de lui-même nulle part. Les instructions disent
donc à l'IA d'aller chercher quelque chose qu'elle n'a pas le moyen de demander : même branchée
directement, un modèle n'ouvre pas `upea://specification` sans qu'on le lui fasse faire.

### Point 2 : ce que les six descriptions permettent de déduire

Je les ai relues telles qu'un client les reçoit (748 à 1 373 caractères chacune). Un modèle qui
ne connaît pas Upea y apprend :

- la **démarche** (`verifier` avant `executer`, jusqu'à `valide`), la forme des résultats, les
  limites chiffrées (5 s, 512 Mo, 64 Kio, pas de clavier ni de fichier ni de réseau) ;
- cinq mots-clés, cités sans définition : `hoi`, `faaea`, `haere` (dans la description de
  `verifier`), `faaite` (« il ne peut qu'afficher (faaite) ») et, par `tokenize`, `TUU`.

Il n'y apprend **aucune** construction : ni comment on déclare, ni les conditions, ni les
boucles, ni les fonctions. Aucune description ne dit qu'une aide existe, puisqu'il n'y a que les
ressources, non visibles. `tokenize` ne dit pas que `si` n'est pas un mot-clé : tout mot inconnu
y est un `IDENT`, donc `valide: true` (c'est ce que l'IA a observé).

### Point 3 : les messages sur des programmes « devinés »

`verifier` sur 30 programmes (sortie complète dans `scratchpad/sortie_1a.txt`) :

| Programme deviné | Message obtenu (ligne:colonne, sorte) |
|---|---|
| `si x > 1 { faaite x; }` | 1:3 syntaxe : `';' attendu après l'expression, trouvé 'x'` |
| `ahani … { } sinon { … }` | 2:32 syntaxe : `';' attendu après l'expression, trouvé '{'` |
| `ahani … { } else { … }` | 2:31 syntaxe : idem |
| `… elif x < 0 { … }` | 2:31 syntaxe : `';' attendu après l'expression, trouvé 'x'` |
| `pour i in range(3) { … }` | 1:5 syntaxe : `';' attendu après l'expression, trouvé 'i'` |
| `for x in [1, 2] { … }` | 1:4 syntaxe : idem, trouvé 'x' |
| `tant que i < 3 { … }` | 2:5 syntaxe : `';' attendu après l'expression, trouvé 'que'` |
| `if x > 1 { … }` | 2:3 syntaxe : `';' attendu après l'expression, trouvé 'x'` |
| `while i < 3 { … }` | 2:6 syntaxe : idem, trouvé 'i' |
| `def f(x) { return x; }` | 1:4 syntaxe : idem, trouvé 'f' |
| `fonction f(x) { hoi x; }` | 1:9 syntaxe : idem, trouvé 'f' |
| `ohipa f(x) { return x; }` | 1:20 syntaxe : idem, trouvé 'x' |
| `ahani a and a { … }` | 2:9 syntaxe : `'{' attendu après la condition, trouvé 'and'` |
| `ahani not a { … }` | 2:11 syntaxe : `'{' attendu après la condition, trouvé 'a'` |
| `print("a");` | 1:1 sémantique : `'print' n'est pas déclaré (vouliez-vous dire 'prim' ?)` |
| `tuu x = true;` | 1:9 sémantique : `'true' n'est pas déclaré` |
| `tuu x = None;` | 1:9 sémantique : `'None' n'est pas déclaré` |
| `tuu x = vrai;` | 1:9 sémantique : `'vrai' n'est pas déclaré (vouliez-vous dire 'rahi' ?)` |
| `afficher("a");` | 1:1 sémantique : `'afficher' n'est pas déclaré` |
| `faaite len([1]);` | 1:8 sémantique : `'len' n'est pas déclaré` |
| `tuu s = input();` | 1:9 sémantique : `'input' n'est pas déclaré` |
| `x += 1;` | 2:4 syntaxe : `expression attendue, trouvé '='` |
| `l.append(1);` | 2:9 syntaxe : `seule une fonction nommée peut être appelée` |
| `tuu d = {"a": 1};` | 1:9 syntaxe : `expression attendue, trouvé '{'`, puis deux autres erreurs en cascade |
| `ahani tia faaite 1;` | 1:11 syntaxe : `'{' attendu après la condition, trouvé 'faaite'` |
| `blabla;` | 1:1 sémantique : `'blabla' n'est pas déclaré` (normal : voir le point 4 de ton analyse) |
| `tuu si = 1; faaite si;` | valide (variable nommée `si` : permise) |
| `tuu et = 1; faaite et;` | valide |

**Confirmé** : pas un message ne dit qu'un mot n'est pas d'Upea ; le même `';' attendu` sort
pour `si`, `if`, `while`, `def`, `pour`, `for`, `elif`, `else` ; c'est le mot *d'avant* l'erreur
qui est fautif, pas celui que le message cite.

**Deux constats que le rapport ne faisait pas :**

1. **Des suggestions trompeuses.** `vrai` donne « vouliez-vous dire `rahi` ? » (la plus grande
   valeur d'une liste), et `print` « vouliez-vous dire `prim` ? » (l'algorithme de Prim). Le
   conseil d'un faux ami doit donc *remplacer* ce `vouliez-vous dire`, sinon la bonne phrase
   et la mauvaise voisinent. Voir D3.
2. **`x += 1`** donne « expression attendue, trouvé '=' » : le faux ami est un symbole, que la
   table de mots ne couvre pas. Voir D2.

## 2. Les lots, dans l'ordre A0 → C → A → B → D → E

Le test d'abord (je vérifie qu'il échoue), puis le code, puis toute la vérification, puis un
commit par lot en français. Les nouveaux tests s'appellent `test_extension_18_aide_*.py`.

### Lot A0 : une source unique, `projet/upea/aide.py`

- **Touche** : `projet/upea/aide.py` (nouveau) ; `serveur_mcp.py` n'importe plus que lui pour les
  textes (les fonctions `_exemples`, `_description`, `_exemple`, `_predefinies` et les constantes
  `SPECIFICATION` et `EXEMPLES` y passent ; `serveur_mcp` garde des alias, car des tests s'en
  servent peut-être).
- **Contenu** :
  - `MOTS_CLES` : une entrée par mot de `tokens.MOTS_CLES` (jamais recopié à la main), avec son
    **rôle**, **lu à l'exécution dans la table « Vocabulaire » de `specification.md`** (colonne
    « Rôle dans Upea ») : aucun sens inventé, et il ne peut pas diverger de la spécification
    (voir D9). Seul l'équivalent Python est écrit à la main, mot par mot ;
  - `FAUX_AMIS` : la table du lot C (voir §4) ;
  - les sujets de l'aide, chacun une fonction qui rend du Markdown : `apercu()`, `mots_cles()`,
    `predefinies()`, `depuis_python()`, `specification(section)`, `exemples(nom)` ;
  - `PRESENTATION`, la phrase d'en-tête du lot B.
- **Ne dépend ni du SDK ni de la façade** : seulement de `tokens`, `lexer` et `predefinies`
  (pour le catalogue ; `compilateur` importera `aide`, et un cycle serait fatal).
- **Tests** : chaque mot de `tokens.MOTS_CLES` figure dans `aide` (et réciproquement) ; chaque
  rôle est celui de la spécification ; `import upea.aide` seul réussit sans le SDK `mcp` ; chaque
  mot d'Upea cité dans un conseil est un mot-clé ou une fonction prédéfinie réels (une faute de
  frappe dans la table échoue).
- **Risques** : l'analyse de la table de la spécification est fragile si son format change (le
  test l'attrape) ; l'import de `predefinies` doit suffire à remplir `PREDEFINIES` (à vérifier au
  premier test).

### Lot C : les faux amis dans les messages d'erreur

- **Touche** : `aide.py` (la table et `ajouter_conseils`), `compilateur.py` (`compiler` et
  `analyser_syntaxe` attrapent `ErreursMultiples`, passent les erreurs à `aide`, relèvent celles
  qui ont un conseil), `semantique.py` (une ligne dans `_non_declare` : pas de `vouliez-vous
  dire` pour un faux ami, voir D3).
- **Approche** : le conseil s'ajoute **à la fin** du message, ` — 'si' n'est pas un mot-clé
  d'Upea : écrivez 'ahani'`. Les messages actuels restent tels quels devant.
  - *Erreur de syntaxe* : on cherche le token fautif (celui à la position de l'erreur) **puis le
    token précédent** ; s'ils sont dans la table, on conseille. `tant que` est traité comme
    `tantque`.
  - *« 'x' n'est pas déclaré »* : le mot de l'erreur lui-même.
  - **Une variable déclarée reste sans conseil** : un mot qui suit `tuu`, `mau`, `ohipa` ou
    `tataitahi` quelque part dans le source, ou qui est dans une liste de paramètres, est
    considéré comme déclaré par le programmeur ; aucun conseil ne le cite, qu'il y ait erreur ou
    non (`tuu si = 1; faaite si x;` : l'erreur de syntaxe n'accuse pas `si`).
  - Les avertissements, les erreurs lexicales et d'exécution : rien.
- **Tests** : (1) pour chaque entrée de la table, `faaite <mot>;` donne le message actuel suivi du
  conseil ; (2) les cas de syntaxe du tableau du §1 (`si`, `pour`, `else`…) ; (3) **obligatoire** :
  `tuu si = 1; faaite si;` et `tuu et = 1; faaite et;` restent valides, et une erreur voisine
  (`faaite si x;`) ne cite pas `si` ; un paramètre nommé `ou` idem ; (4) les messages sans faux
  ami sont **identiques à ceux d'aujourd'hui** (`blabla`, les tests existants, inchangés) ;
  (5) le conseil n'apparaît jamais sur un programme valide ; (6) aucun mot de la table n'est un
  mot-clé ni une prédéfinie (sinon il serait lu comme tel).
- **Risques** : une erreur de syntaxe qui n'a rien à voir avec le mot précédent, mais qui le
  suit : accepté (`faaite non;` donne bien le conseil, c'est la bonne ; `faaite 1 si;` aussi).
  Des tests existants lisent des messages : aucun ne contient un mot de la table (`'y'`, `'x'`,
  `'inconnue'`, `'f'`, `'z'`). Les docs du dépôt (blocs `erreur`) idem ; je le vérifierai.

### Lot A : l'aide sous forme d'outils

- **Touche** : `serveur_mcp.py` (deux outils, 20 lignes), `aide.py`.
- **`aide(sujet, section=None)`** : `sujet` est un `Literal` (le schéma montre la liste au modèle) :
  `apercu`, `mots_cles`, `predefinies`, `depuis_python`, `specification`. Rend du Markdown.
  - `mots_cles` : le tableau des 28 mots (rôle, équivalent Python), puis la table des faux amis ;
  - `predefinies` : le catalogue actuel de la ressource (signatures, abréviations), repris tel
    quel de `aide.py` ;
  - `specification` : sans `section`, **le sommaire** (les sections et leur taille) ; avec
    `section`, le texte de cette section, par le titre sans casse ni accents (`semantique`,
    `boucle_tataitahi`, `grammaire` ; un titre `##` rend ses sous-sections avec lui) ; `section="tout"` rend la spécification entière ; un nom
    inconnu rend la liste (un *résultat*, pas une erreur d'outil). Voir D4 et D5.
- **`exemples(nom=None)`** : sans argument, la liste (`nom` : première ligne du commentaire de
  l'exemple) ; avec un nom, le source et la sortie exacte (même texte que la ressource) ; un nom
  inconnu ou contenant un chemin (`../specification`) rend la liste des noms, sans lire de fichier.
- **Annotations** : `SANS_EFFET` (lecture seule, idempotent, monde fermé), comme les six autres.
- **Les ressources et les prompts restent identiques** (sauf D6 pour une phrase des prompts).
- **Tests** : la liste des outils passe de 6 à 8 ; chaque sujet rend un texte non vide ; `apercu`
  ≤ 8 Kio, **mesuré en octets UTF-8 (le texte ci-dessous : 4 345 octets, marge de 3,6 Kio)** ;
  `section` inconnue → la liste, un chemin dans `exemples` → la liste ; les annotations ; les
  ressources inchangées ; le bloc `upea` d'`apercu` s'exécute et affiche exactement sa sortie.
- **Risques** : un client qui plafonne la taille d'un résultat d'outil (c'est pour cela que
  `specification` sans section rend un sommaire : 43,7 Kio, environ 14 000 jetons).

### Lot B : des descriptions qui suffisent seules

- **Touche** : `serveur_mcp.py` (`_outil` ajoute la phrase avant la docstring, `INSTRUCTIONS` la
  reprend), `aide.py` (`PRESENTATION`).
- **La phrase**, en tête des huit descriptions, et au début des instructions :

  > Upea est un langage aux mots-clés tahitiens, transpilé en Python. Si tu ne le connais pas, appelle d'abord aide("apercu").

- Les instructions du serveur gardent leur contenu, mais n'envoient plus vers les ressources
  (qu'un client outils seuls ne voit pas) : elles envoient vers `aide` et `exemples`.
- **Tests** : chaque description commence par la phrase, et tient à moins de 1 600 caractères ;
  les instructions la contiennent ; plus aucune ne dit de « lire la ressource » seule.
- **Risques** : aucun ; des tests lisent peut-être le début des descriptions (je les adapterai, avec
  explication dans le commit).

### Lot D : la documentation

- **Touche** : `docs/aide-memoire.md` et `docs/depuis-python.md` (**générés**, jamais écrits à la
  main), `docs/mcp.md`, `docs/architecture.md`, `docs/tutoriel.md`, `README.md`, `aide.py`
  (`depuis_python()`), un test.
- **Garder à jour** : `uv run python -m upea.aide --ecrire` réécrit les deux fichiers ;
  `--verifier` (ou le test) échoue s'ils ne correspondent plus au module, et dit la commande à
  lancer. Chaque fichier commence par « Fichier généré par `upea/aide.py` : ne pas modifier à la
  main ». Voir D8.
- **`depuis-python`** : le tableau des équivalences (construit à partir de `aide.py`) ; un
  dictionnaire remplacé par une **liste de paires et une fonction de recherche**, puis par un
  **graphe** ; un ensemble par un **arbre ordonné** (`aifaito` : ajouter deux fois ne fait rien) ;
  l'aléatoire par **un générateur congruentiel linéaire écrit en Upea** ; l'entrée clavier par
  des **constantes** dans le programme. **Chaque exemple est un bloc `upea` suivi de son bloc
  `sortie`**, exécuté par `test_livraison_documentation.py`, comme les autres ; je copie les sorties
  d'une exécution réelle, jamais écrites d'avance.
- **`docs/mcp.md`** : la section 2 est réécrite (ce que le serveur envoie ; ce qu'un client en
  affiche ; **seuls les outils sont appelés par le modèle de lui-même**, d'où `aide` et
  `exemples`) ; les sections 3 et 4 présentent les deux outils ; une courte section sur
  « un client qui n'affiche que les outils » (le pont de la session 1).
- **Tests** : les blocs ci-dessus ; les liens relatifs (test existant) ; la synchronisation des
  deux fichiers générés ; `README.md`, `docs/tutoriel.md` et `docs/architecture.md` contiennent
  un lien vers l'aide-mémoire et `depuis-python` (ou le nouveau module, pour l'architecture).
- **Risques** : un exemple qui ne s'exécute pas comme prévu (le test échoue, je corrige l'exemple,
  pas le langage) ; le générateur pseudo-aléatoire doit rester simple et déterministe.

### Lot E : le scénario de l'exercice final

- **Touche** : `projet/tests/test_extension_18_exercice_final.py`, `docs/journal/exercice-final/`
  (`index.md`, `session-1-rapport.md` inchangé, `session-2-rapport.md` vide avec sa place),
  `docs/journal/index.md`, `NOTES.md`.
- **Le test** (`Client` en mémoire) : liste les outils **et rien d'autre** ; chaque description
  renvoie à `aide` ; appelle `aide("apercu")` ; **extrait l'exemple d'`apercu`, en écrit un
  programme dérivé** (par exemple, le même parcours d'un autre graphe, avec une fonction de plus),
  le vérifie (`verifier`), puis l'exécute (`executer`) et compare sa sortie.
- **`index.md`** : la démarche (la session 1, ses causes, les lots, la session 2) ; **la
  session 2** : le texte exact à donner à une IA neuve (livré aussi dans mon bilan final) ;
  **la section des observations, marquée `<!-- À RÉDIGER PAR THOMAS -->`**, vide.
- **Risques** : aucun sur le code. Le rapport de la session 1 est déplacé tel quel, octet pour octet.

### Fin de mission

Toute la vérification relancée ; `NOTES.md` (avancement de l'extension 18 : les deux outils ;
table des écarts avec le cours : `aide` et `exemples` n'y sont pas, et le scénario scripté passe
de « à faire » à « fait » ; la session 2 reste « à faire », c'est ton exercice) ; le bilan.

## 3. Le texte proposé de `aide("apercu")`

Mesuré : **4 345 octets UTF-8** (budget : 8 192). L'exemple a été **exécuté** (`uv run python -m
upea run`), et la sortie ci-dessous est la sienne, mot pour mot.

````markdown
# Upea : l'aide-mémoire (à lire en premier)

Upea est un langage impératif à accolades, aux mots-clés tahitiens, transpilé en Python 3.12. Les arbres (`tumu`) et les graphes (`upea`) y sont des valeurs de première classe. **Ne devine pas la syntaxe** : `si`, `if`, `while`, `def`, `print`, `true`, `None`, `+=` n'existent pas (voir `aide("mots_cles")`).

## Démarche

1. Écris le programme complet, en t'appuyant sur cet aide-mémoire et sur `exemples()`.
2. Passe-le à `verifier`, et corrige jusqu'à `valide: true` : les messages donnent la ligne et la colonne, et un conseil quand tu as écrit un mot d'un autre langage.
3. Exécute-le avec `executer` et compare sa sortie à celle que tu attends. Une erreur du programme est un résultat à lire, pas une panne de l'outil.

## Les bases

- Une instruction finit par `;`, un bloc est entre `{ }`, l'indentation ne compte pas. Commentaires : `// ligne` et `/* bloc */`.
- `tuu x = 1;` déclare une variable, `mau PI = 3.14;` une constante. On déclare avant d'utiliser, avec une valeur, une seule fois (pas de masquage). On change une valeur avec `x = x + 1;` (pas de `+=`). Type facultatif : `tuu x: numera = 1;`.
- Valeurs : `42`, `3.14`, `"texte"` (guillemets droits seulement), `tia` (vrai), `hape` (faux), `aore` (rien), `[1, 2]`. Types : `numera` entier, `tuhaa` décimal, `parau` texte, `tiahape` booléen, `tapura[T]` liste.
- Opérateurs : `+ - * / %` (`/` rend toujours un décimal), `== != < <= > >=`, `ma` (et), `anei` (ou), `eiaha` (non), `x roto l` (appartenance). Les comparaisons ne s'enchaînent pas : `a < b ma b < c`. Texte et nombre : `"n = " + parau(n)`.

## Les constructions

- Condition : `ahani c { … } taae ahani d { … } taae { … }` (si, sinon si, sinon).
- Boucle : `tamau c { … }` (tant que) ; `tataitahi i roto 0..n { … }` (`0..=n` inclut `n`) ; `tataitahi x roto liste { … }` ; `faaea;` sort de la boucle, `haere;` passe au tour suivant.
- Fonction, au niveau global et avant son premier appel : `ohipa nom(a, b: numera) -> numera { hoi a + b; }`. Pas de fonction imbriquée, ni comme valeur.
- Affichage : `faaite a, b;` (séparés par une espace, puis un saut de ligne). `faaite arbre;` ou `faaite graphe;` dessine la structure.
- Listes : `l[0]`, `l[-1]`, `roa(l)` (longueur), `amui(l, x)` (ajouter), `tatara(l, x)` (retirer). Un texte aussi : `t[0]`, `roa(t)`.
- Arbres : `tumu(1, tumu(2), tumu(3))`, champs `a.hotu` (valeur) et `a.amaa` (liste des enfants), `prefixe(a)`, `teitei(a)` ; arbres de recherche et tas : `aifaito [5, 3, 8]`, `ahu [3, 1]`.
- Graphes : `upea { "A" <-> "B" : 17, "B" -> "C" }` (`->` un sens, `<->` deux, `: p` le poids) ; `tataitahi n roto g mai "A" aano { … }` parcourt en largeur depuis A (`hohonu` : profondeur) ; `ea(g, a, b)` plus court chemin, `motu(g)`, `pihai(g, a)`, `taati(g, a, b, p)`. Tout le catalogue : `aide("predefinies")`.

## Un exemple complet

```upea
ohipa somme_carres(l: tapura[numera]) -> numera {
    tuu total = 0;
    tataitahi x roto l {
        total = total + x * x;
    }
    hoi total;
}

tuu notes = [3, 1, 2];
amui(notes, 4);
faaite "somme des carrés :", somme_carres(notes);

tuu i = 0;
tamau i < 3 {
    ahani i == 1 {
        faaite "un";
    } taae {
        faaite "pas un";
    }
    i = i + 1;
}

tuu arbre = tumu(1, tumu(2), tumu(3));
faaite arbre.hotu, roa(arbre.amaa), prefixe(arbre);

tuu iles = upea { "Tahiti" <-> "Moorea" : 17, "Moorea" -> "Huahine" : 160 };
tataitahi ile roto iles mai "Tahiti" aano {
    faaite ile;
}
faaite ea(iles, "Tahiti", "Huahine"), distance(iles, "Tahiti", "Huahine");
```

Sortie :

```text
somme des carrés : 30
pas un
un
pas un
1 2 [1, 2, 3]
Tahiti
Moorea
Huahine
["Tahiti", "Moorea", "Huahine"] 177
```

## Ce qu'Upea n'a pas

- Ni dictionnaires, ni ensembles littéraux, ni tuples : une liste de paires, un graphe, ou un arbre ordonné (`aifaito`, un ensemble) les remplacent.
- Ni clavier (`input`), ni fichiers, ni réseau, ni aléatoire : écris les entrées dans le programme, et un petit générateur pseudo-aléatoire si besoin.
- Ni fonctions imbriquées, ni fonctions comme valeurs, ni récursion croisée, ni `+=`, ni comparaisons chaînées, ni `for … in` ni `range` ni `len` (voir `tataitahi` et `roa`).

Pour le détail : `aide("depuis_python")` (la traduction pas à pas), `aide("specification")`, `exemples()`.
````

Ce que je n'ai **pas** vérifié encore, et que le test du lot A fera : que chaque phrase du texte
soit vraie (par exemple, qu'un texte se parcourt avec `tataitahi c roto texte`, ce que la
spécification dit). Le programme, lui, tourne.

## 4. La phrase d'en-tête (lot B)

> Upea est un langage aux mots-clés tahitiens, transpilé en Python. Si tu ne le connais pas, appelle d'abord aide("apercu").

Elle est en tête des huit descriptions (les six actuelles, `aide`, `exemples`), puis une ligne vide,
puis le texte actuel, inchangé. Les instructions du serveur la reprennent, puis disent la
démarche en trois lignes, avec `aide` et `exemples` à la place des ressources.

## 5. La table des faux amis proposée (en entier)

Chaque ligne : le mot que quelqu'un écrira, et ce que le conseil dit après « n'est pas un mot-clé
d'Upea : » (ou « n'existe pas en Upea : » quand rien ne le remplace). Tous les mots-clés d'Upea
cités viennent de la table de la spécification, **sans aucun sens ni étymologie ajoutés**.

**Groupe 1 : les mots de ta liste (Python et français).**

| Mot | Conseil |
|---|---|
| `if` | écrivez `ahani` |
| `elif` | écrivez `taae ahani` |
| `else` | écrivez `taae` |
| `while` | écrivez `tamau` |
| `for` | écrivez `tataitahi x roto liste`, ou `tataitahi i roto a..b` |
| `def` | écrivez `ohipa` |
| `return` | écrivez `hoi` |
| `break` | écrivez `faaea` |
| `continue` | écrivez `haere` |
| `print` | écrivez `faaite` |
| `True` / `False` / `None` | écrivez `tia` / `hape` / `aore` |
| `and` / `or` / `not` | écrivez `ma` / `anei` / `eiaha` |
| `in` | écrivez `roto` |
| `si` | écrivez `ahani` |
| `sinon` | écrivez `taae` (`taae ahani` pour « sinon si ») |
| `tantque`, `tant que` | écrivez `tamau` |
| `pour` | écrivez `tataitahi x roto liste`, ou `tataitahi i roto a..b` |
| `dans` | écrivez `roto` |
| `fonction` | écrivez `ohipa` |
| `retourner`, `retour` | écrivez `hoi` |
| `afficher` | écrivez `faaite` |
| `vrai` / `faux` / `rien` | écrivez `tia` / `hape` / `aore` |
| `et` / `ou` / `non` | écrivez `ma` / `anei` / `eiaha` |

**Groupe 2 : ce qu'on devine en venant de Python (les plus fréquents).**

| Mot | Conseil |
|---|---|
| `len` | écrivez `roa(x)` |
| `range` | écrivez `a..b` (ou `a..=b`) dans un `tataitahi` |
| `append` | écrivez `amui(liste, x)` |
| `int` / `float` / `str` | écrivez `numera(x)` / `tuhaa(x)` / `parau(x)` |
| `pass` | écrivez un bloc vide, `{ }` |
| `input` | **n'existe pas** : un programme Upea ne lit pas le clavier ; écrivez les valeurs dans le programme |
| `random`, `randint` | **n'existe pas** : pas d'aléatoire ; voyez `aide("depuis_python")` |
| `import` | **n'existe pas** : pas de modules ; les fonctions prédéfinies sont déjà là |
| `class` | **n'existe pas** : pas de classes ; voyez `tumu` et `upea` pour les structures |
| `lambda` | **n'existe pas** : pas de fonctions comme valeurs ; déclarez une `ohipa` au niveau global |

**Groupe 3 : d'autres langages, pour les mêmes raisons.**

| Mot | Conseil |
|---|---|
| `function` | écrivez `ohipa` |
| `let`, `var` / `const` | écrivez `tuu` / `mau` |
| `true` / `false` / `null` | écrivez `tia` / `hape` / `aore` |

**Symboles** (seulement si D2 est « oui ») : `+=`, `-=`, `*=`, `/=`, `%=` : « Upea n'a pas
d'affectation composée : écrivez `x = x + 1` ».

Exemple de message final : `';' attendu après l'expression, trouvé 'x' — 'si' n'est pas un
mot-clé d'Upea : écrivez 'ahani'`.

Le test `aucun mot de la table n'est un mot-clé ni une prédéfinie` vérifie que ces mots sont
bien des identifiants ordinaires (ce qui est la raison pour laquelle la variable `si` est permise).

## 6. Les décisions qui te reviennent

Chaque question se tranche par oui ou non (ou un nom) ; ma recommandation est en tête.

- **D1. Garder la table du §5 telle quelle (trois groupes, environ 50 mots) ?** *Oui.* Le groupe 1
  est ta liste ; le groupe 2 couvre `len`, `range`, `append`, `input`, vus dans mes essais ; le
  groupe 3 est de la marge, et se coupe sans toucher au reste.
- **D2. Ajouter les affectations composées (`+=`, `-=`, `*=`, `/=`, `%=`) au lot C ?** *Oui.* C'est
  la faute de Python la plus probable, et elle est dans ta propre liste d'essais ; le mécanisme
  est le même (l'erreur tombe sur le `=`, précédé de `+`, collés).
- **D3. Quand le mot est un faux ami, supprimer le « vouliez-vous dire » (`vrai` → `rahi`,
  `print` → `prim`) au profit du conseil ?** *Oui.* Une ligne dans `semantique.py`, `_non_declare` ;
  sans cela, une suggestion fausse suit un conseil juste. Les suggestions des autres mots
  restent.
- **D4. `aide("specification")` sans `section` : rendre le sommaire (les sections et leur taille)
  plutôt que le texte entier ?** *Oui.* 43,7 Kio, c'est environ 14 000 jetons : trop pour un seul
  résultat d'outil, et la spécification entière reste atteignable par `section="tout"`.
- **D5. Les sections nommables sont les titres `##` et `###` de la spécification (27 en tout) ?**
  *Oui.* Mesuré : « Sémantique » en entier (ses 12 sous-sections) fait environ 19 Kio, tandis que
  « La boucle `tataitahi` » en fait 1,9 et « Graphes » 1,2. Demander `semantique` rend toute la
  partie ; demander `boucle_tataitahi` ne rend que la boucle.
- **D6. Ajouter une phrase à `DEMARCHE`, dans les prompts, pour renvoyer vers `aide("apercu")`
  en plus de la spécification ?** *Oui.* Tu as écrit que les prompts « restent tels quels » ; je
  n'y toucherais que pour cette phrase, avec un test, parce que ce prompt dit aujourd'hui
  « lis la ressource ». Dis non, et je n'y touche pas.
- **D7. Renommer `docs/journal/exerciceFinal/` en `docs/journal/exercice-final/` (le nom qu'ont
  déjà `NOTES.md`, `docs/journal/index.md` et ta consigne) ?** *Oui*, avec un déplacement du
  fichier (pas de `git mv`, que tu m'interdis ; git y verra un renommage dans le commit du lot E).
- **D8. Les deux pages sont régénérées par un module exécutable, `uv run python -m upea.aide
  --ecrire`, plutôt que par une sous-commande de la CLI ?** *Oui.* La CLI n'est pas dans le
  périmètre. Un test échoue si les pages diffèrent du module.
- **D9. Lire le sens des mots-clés dans la table de la spécification, à l'exécution, plutôt que
  le recopier dans `aide.py` avec un test de concordance ?** *Oui.* Rien à recopier, donc rien
  d'inventé ni qui diverge. Coût : une analyse de tableau Markdown, testée.
- **D10. Dans l'équivalent Python des mots sans équivalent direct, écrire « aucun » (`upea`, `mai`,
  `imi`, `aifaito`, `uteere`, `pupu`) et citer `heapq` pour `ahu` / `ahunui` ?** *Oui.* `heapq` est un
  tas min ; pour `ahunui`, on y met des clés négatives : c'est un fait de Python, pas du langage.

## 7. Ce que je ne fais pas

`formater` et les commentaires, le nommage des outils par le pont, tout changement de la
spécification ou du langage, toute dépendance ajoutée, tout changement dans `council/` ou
`.claude/`, toute opération Git hors des commits de lot.

**J'attends ton feu vert (et tes réponses à D1–D10) avant de toucher au code.**
