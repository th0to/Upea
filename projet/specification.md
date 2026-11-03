# Spécification d'Upea

> Spécification de l'étape 1, rédigée à partir de `langage/gabarits/specification.md`. Elle s'adresse à quelqu'un qui n'a jamais vu le langage : l'enseignant qui la valide, moi-même à chaque étape, et plus tard une IA qui apprendra à écrire de l'Upea.

## Identité

| | |
|---|---|
| Nom | Upea (de *ʻupeʻa*, « le filet » en tahitien : un graphe est un filet de nœuds reliés) |
| Extension | `.upea` |
| Idée | Un petit langage impératif à accolades, aux mots-clés tahitiens, où les **arbres** (`tumu`) et les **graphes** (`upea`) sont des valeurs de première classe. Un graphe s'écrit comme une carte des îles (`"Tahiti" <-> "Moorea" : 17`), et un même mot-clé, `tataitahi`, parcourt un intervalle, une liste, un arbre ou un graphe, en profondeur ou en largeur. Il s'adresse à qui veut manipuler des structures de données sans écrire leur plomberie. |
| Cible | Python 3.12, sous forme de texte (étape 8) ou via le module `ast` (extension 11). |

## Un programme pour donner le ton

```
// Les îles atteignables depuis Tahiti, et le plus court trajet vers Bora Bora.
tuu iles = upea {
    "Tahiti" <-> "Moorea" : 17,
    "Tahiti" -> "Huahine" : 170,
    "Huahine" <-> "Raiatea" : 40,
    "Raiatea" <-> "Bora Bora" : 70,
};

ohipa distance(g, chemin) -> numera {
    tuu total = 0;
    tataitahi i roto 1..roa(chemin) {
        total = total + teiaha(g, chemin[i - 1], chemin[i]);
    }
    hoi total;
}

tataitahi ile roto iles mai "Tahiti" aano {
    faaite "on atteint", ile;
}
tuu trajet = ea(iles, "Tahiti", "Bora Bora");
ahani trajet != aore {
    faaite trajet, distance(iles, trajet), "km";
}
```

## Vocabulaire

Les mots-clés sont des mots tahitiens écrits **en ASCII**, sans ʻeta (coup de glotte) ni macron, pour être faciles à taper. Le sens donné est celui qui a guidé le choix ; il est approximatif.

| Mot-clé | Mot tahitien | Rôle dans Upea |
|---|---|---|
| `tuu` | tuʻu, poser | déclarer une variable |
| `mau` | mau, ferme, fixe | déclarer une constante |
| `ohipa` | ʻohipa, travail, tâche | déclarer une fonction |
| `hoi` | hoʻi, revenir | renvoyer une valeur |
| `ahani` | ahani, si | si |
| `taae` | taʻa ʻe, autrement | sinon (`taae ahani` : sinon si) |
| `tamau` | tāmau, persévérer | tant que |
| `tataitahi` | tātaʻitahi, un par un | pour chaque |
| `roto` | i roto, dedans | dans (boucle, et opérateur d'appartenance) |
| `mai` | mai, depuis | point de départ d'un parcours de graphe |
| `aano` | ʻāano, large | parcours en largeur |
| `hohonu` | hohonu, profond | parcours en profondeur |
| `faaea` | faʻaea, s'arrêter | sortir de la boucle (*break*) |
| `haere` | haere, aller | passer au tour suivant (*continue*) |
| `faaite` | faʻaite, montrer | afficher |
| `upea` | ʻupeʻa, filet | littéral de graphe, et type graphe |
| `tia` | tiʻa, juste, droit | vrai |
| `hape` | hape, faux, erroné | faux |
| `aore` | ʻaore, il n'y a pas, rien | absence de valeur |
| `ma` | mā, avec | et logique |
| `anei` | ʻaneʻi, ou bien | ou logique |
| `eiaha` | ʻeiaha, ne pas | non logique |

Les noms des types et des fonctions prédéfinies (`numera`, `parau`, `tumu`, `roa`…) ne sont **pas** des mots-clés : ce sont des identifiants que le compilateur connaît d'avance (voir *Fonctions prédéfinies* et *Types*).

## Lexique

- **Blancs et sauts de ligne** : espaces, tabulations, `\r` et `\n` sont ignorés. La mise en forme est libre ; les instructions se terminent par `;`, les blocs sont entre `{ }`. L'indentation ne compte pas.
- **Commentaires** : `//` jusqu'à la fin de la ligne, ou `/* … */` sur plusieurs lignes. Les commentaires `/* */` ne s'imbriquent pas ; un `/*` jamais refermé est une erreur lexicale.
- **Entiers** : une suite de chiffres ASCII, `0`, `42`. **Décimaux** : au moins un chiffre de chaque côté du point, `3.14`. `1.` et `.5` sont refusés (écrire `1.0` et `0.5`), car `1..5` et `1..=5` sont des intervalles, et `t.hotu` un accès de champ. Un nombre collé à une lettre (`12abc`) est une erreur lexicale.
- **Textes** : entre guillemets droits, `"..."`, sur une seule ligne. Échappements acceptés : `\n` (saut de ligne), `\t` (tabulation), `\"` (guillemet) et `\\` (barre oblique). Tout autre échappement est une erreur. Le texte vide `""` est permis.
- **Identifiants** : une lettre (les lettres accentuées sont permises : `déjà`, `île`), puis des lettres, des chiffres ou `_`. Un identifiant **ne commence jamais par `_`** : ce préfixe est réservé au code Python généré. Un mot-clé n'est jamais le préfixe d'un identifiant : `iaora` et `tuu_x` sont des identifiants. Un identifiant mal formé (`x²`) est une erreur lexicale. La casse compte : `Tuu` est un identifiant.
- **Mots-clés** : `tuu mau ohipa hoi ahani taae tamau tataitahi roto mai aano hohonu faaea haere faaite upea tia hape aore ma anei eiaha`.
- **Symboles** : `( ) { } [ ] , ; : . .. ..= -> <-> + - * / % = == != < <= > >=`.

Les jetons qui se ressemblent sont lus du plus long au plus court :

| Source | Jetons |
|---|---|
| `1.5` | le décimal `1.5` |
| `1..5` | `1`, `..`, `5` |
| `1..=5` | `1`, `..=`, `5` |
| `t.hotu` | `t`, `.`, `hotu` |
| `a<->b` | `a`, `<->`, `b` |
| `a<-1` | `a`, `<`, `-`, `1` (et non une flèche) |
| `x->y` | `x`, `->`, `y` |
| `a==b` / `a=b` | `==` / `=` |

## Grammaire (EBNF)

Notation : `{ x }` répète zéro fois ou plus, `[ x ]` est facultatif, `|` sépare les choix, les terminaux sont entre guillemets. `IDENT`, `ENTIER`, `DECIMAL` et `TEXTE` sont les jetons décrits plus haut, `FIN` la fin du source.

```ebnf
programme     = { instruction } FIN ;
instruction   = declaration | fonction | si | tantque | pour | rupture | retour
              | affiche | affectation | expression ";" ;

declaration   = ( "tuu" | "mau" ) IDENT [ annotation ] "=" expression ";" ;
annotation    = ":" type ;
type          = ( IDENT | "upea" | "aore" ) [ "[" type "]" ] ;
fonction      = "ohipa" IDENT "(" [ parametre { "," parametre } ] ")"
                [ "->" type ] bloc ;
parametre     = IDENT [ annotation ] ;
si            = "ahani" expression bloc { "taae" "ahani" expression bloc } [ "taae" bloc ] ;
tantque       = "tamau" expression bloc ;
pour          = "tataitahi" IDENT "roto" expression [ suite_pour ] bloc ;
suite_pour    = ( ".." | "..=" ) expression
              | "mai" expression [ mode ]
              | mode ;
mode          = "aano" | "hohonu" ;
rupture       = ( "faaea" | "haere" ) ";" ;
retour        = "hoi" [ expression ] ";" ;
affiche       = "faaite" [ expression { "," expression } ] ";" ;
affectation   = cible "=" expression ";" ;
cible         = IDENT | postfixe "[" expression "]" | postfixe "." IDENT ;
bloc          = "{" { instruction } "}" ;

expression    = ou ;
ou            = et { "anei" et } ;
et            = negation { "ma" negation } ;
negation      = "eiaha" negation | comparaison ;
comparaison   = somme [ ( "==" | "!=" | "<" | "<=" | ">" | ">=" | "roto" ) somme ] ;
somme         = produit { ( "+" | "-" ) produit } ;
produit       = unaire { ( "*" | "/" | "%" ) unaire } ;
unaire        = "-" unaire | postfixe ;
postfixe      = primaire { "(" [ arguments ] ")" | "[" expression "]" | "." IDENT } ;
arguments     = expression { "," expression } ;
primaire      = ENTIER | DECIMAL | TEXTE | "tia" | "hape" | "aore" | IDENT
              | "(" expression ")" | "[" [ arguments ] "]" | graphe ;
graphe        = "upea" "{" [ arete { "," arete } [ "," ] ] "}" ;
arete         = expression ( "->" | "<->" ) expression [ ":" expression ] ;
```

Remarques :

- Une affectation commence comme une expression : le parser lit d'abord une expression, puis, si un `=` suit, vérifie que c'est une cible valide (une variable, un élément `t[i]` ou un champ `t.hotu`).
- `comparaison` n'a **qu'un seul** opérateur facultatif : les comparaisons ne s'enchaînent pas (voir ci-dessous).
- Dans une `arete`, `->`, `<->` et `:` ne sont pas des opérateurs d'expression : chaque extrémité s'arrête d'elle-même devant eux.
- `upea` est toujours suivi de `{` : `ahani g == upea {} { … }` n'est donc pas ambigu.
- `tumu(…)` (un arbre) n'a pas de syntaxe à lui : c'est un appel de fonction prédéfinie.

## Priorité et associativité des opérateurs

Du moins prioritaire au plus prioritaire :

| Niveau | Opérateurs | Associativité |
|---|---|---|
| 1 | `anei` | gauche |
| 2 | `ma` | gauche |
| 3 | `eiaha` (préfixe) | — |
| 4 | `==` `!=` `<` `<=` `>` `>=` `roto` | **aucune** |
| 5 | `+` `-` | gauche |
| 6 | `*` `/` `%` | gauche |
| 7 | `-` (préfixe) | — |
| 8 | appel `f(x)`, indice `t[i]`, champ `t.hotu` | gauche |

Points particuliers :

- **Pas de comparaison chaînée** : `a < b < c` et `a == b == c` sont des erreurs de syntaxe (« les comparaisons ne s'enchaînent pas »). On écrit `a < b ma b < c`, ou `(a < b) == c` si c'est vraiment ce que l'on veut.
- `-a * b` se lit `(-a) * b`, mais `eiaha a == b` se lit `eiaha (a == b)`.
- `x roto l ma y roto l` se lit `(x roto l) ma (y roto l)`.
- `t.amaa[0].hotu` se lit de gauche à droite : `((t.amaa)[0]).hotu`.

## Sémantique

### Valeurs

| Sorte | Exemples | Remarques |
|---|---|---|
| entier | `0`, `42`, `-7` | précision illimitée |
| décimal | `3.14`, `0.5` | flottant de Python |
| texte | `"Ia ora na"` | immuable ; `t[0]` est un texte d'un caractère |
| booléen | `tia`, `hape` | |
| rien | `aore` | absence de valeur ; c'est ce que renvoie une fonction sans `hoi` |
| liste | `[1, 2, 3]`, `[]` | modifiable, éléments de sortes quelconques |
| arbre | `tumu(1, tumu(2), tumu(3))` | nœud n-aire modifiable |
| graphe | `upea { "A" -> "B" : 3 }` | graphe orienté pondéré, modifiable |

### Variables, constantes et portées

- On **déclare** une variable avec `tuu`, une constante avec `mau`, avant de s'en servir, **une seule fois par portée**. Une déclaration sans valeur n'existe pas.
- Chaque bloc `{ }` ouvre une portée. Une variable n'existe que de sa déclaration à la fin de son bloc. Deux blocs **frères** peuvent déclarer le même nom.
- La valeur d'une déclaration est évaluée **avant** que le nom n'existe : `tuu x = x;` est une erreur si aucun `x` n'est visible.
- **Pas de masquage** : on ne peut pas redéclarer un nom encore visible dans le même *espace de noms Python*, c'est-à-dire dans la même fonction, ou au niveau global hors de toute fonction. Python n'a pas de portée de bloc : sans cette règle, le code généré changerait de sens.
- Une fonction peut déclarer une locale qui porte le nom d'une variable globale, **sauf** si elle lit ou modifie aussi cette globale (avant ou après la déclaration) : en Python, le nom serait local dans toute la fonction.
- On ne peut pas affecter une **constante** (`mau`), ni la **variable d'une boucle** `tataitahi`, ni une fonction.
- Modifier le contenu d'une liste, d'un arbre ou d'un graphe (`t[0] = 1;`, `a.hotu = 2;`, `taati(g, …)`) est permis même s'il est désigné par une constante : `mau` fixe le nom, pas la valeur.

### Fonctions

- Une fonction se déclare avec `ohipa`, **au niveau global uniquement**, avant son premier appel. Ses paramètres sont des variables locales.
- Une fonction peut s'appeler elle-même (récursion directe) ; la récursion croisée n'est pas possible, puisqu'une fonction n'est connue qu'après sa déclaration.
- Le **nombre d'arguments** est vérifié à la compilation.
- Une fonction peut lire et modifier les variables globales déclarées **avant** elle.
- `hoi expression;` renvoie une valeur, `hoi;` renvoie `aore`. Une fonction qui se termine sans `hoi` renvoie `aore`. `hoi` hors d'une fonction est une erreur.
- Seule une fonction nommée peut être appelée : `f(1)` est valide, `f(1)(2)` ne l'est pas. Une fonction n'est pas une valeur (`tuu g = f;` est refusé).
- Un nom de fonction (définie ou prédéfinie) ne peut pas être réutilisé pour une variable ou une autre fonction.

### Structures de contrôle

- `ahani` / `taae ahani` / `taae` : la première branche dont la condition est vraie s'exécute.
- `tamau c { … }` répète le bloc tant que `c` est vraie (zéro tour si `c` est fausse dès le départ).
- **Conditions** : `hape`, `aore`, `0`, `0.0`, `""` et `[]` sont considérés comme faux, toute autre valeur comme vraie (règle de Python). Le vérificateur de types (extension 12) exige une condition de type `tiahape` quand il connaît son type.
- `faaea;` quitte la boucle la plus proche, `haere;` passe à son tour suivant. Hors d'une boucle, ce sont des erreurs.

### La boucle `tataitahi`

La variable de boucle n'existe que dans le bloc, et ne peut pas y être affectée.

| Forme | Ce qui est parcouru |
|---|---|
| `tataitahi i roto a..b` | `a, a+1, …, b-1` (zéro tour si `a >= b`) ; `a` et `b` doivent être des entiers |
| `tataitahi i roto a..=b` | `a, a+1, …, b` (borne haute incluse) |
| `tataitahi x roto liste` | les éléments de la liste, dans l'ordre |
| `tataitahi c roto texte` | les caractères du texte |
| `tataitahi n roto arbre` | **les nœuds** (sous-arbres) en profondeur, ordre préfixe : la racine, puis chaque enfant de gauche à droite |
| `tataitahi n roto arbre hohonu` | idem, explicitement |
| `tataitahi n roto arbre aano` | les nœuds en largeur : niveau par niveau, de gauche à droite |
| `tataitahi m roto graphe` | les nœuds du graphe, dans l'ordre où ils y sont apparus |
| `tataitahi m roto graphe mai d` | les nœuds atteignables depuis `d`, en profondeur (ordre préfixe, `d` d'abord) |
| `tataitahi m roto graphe mai d aano` | les nœuds atteignables depuis `d`, en largeur (`d` d'abord) |

Dans un parcours, les successeurs d'un nœud sont visités dans l'ordre où leurs arcs ont été ajoutés : la sortie est toujours la même. Ce qui est parcouru est **fixé au début de la boucle** : ajouter un élément à une liste pendant qu'on la parcourt ne rallonge pas la boucle.

Erreurs d'exécution : `mai` sur autre chose qu'un graphe ; nœud de départ absent du graphe ; `aano` ou `hohonu` sur une liste ou un texte, ou sur un graphe sans `mai` ; parcours d'un nombre, d'un booléen ou de `aore`.

### Arbres (`tumu`)

- `tumu(v)` est une feuille de valeur `v` ; `tumu(v, e1, e2, …)` un nœud dont les enfants sont `e1, e2…`, qui doivent être des arbres.
- `t.hotu` (*hotu*, le fruit) est la valeur du nœud, `t.amaa` (*ʻamaʻa*, les branches) la liste de ses enfants. Ce sont les deux seuls champs : `t.taille` est une erreur sémantique. Les deux sont affectables (`t.hotu = 4;`), et `t.amaa` est une liste ordinaire (`amui(t.amaa, tumu(5));`).
- `==` compare deux arbres par leur structure et leurs valeurs.
- `v roto t` vaut `tia` si l'un des nœuds de `t` a la valeur `v`.

### Graphes (`upea`)

- Un graphe est **orienté** et **pondéré**. Ses nœuds sont des textes ou des entiers (ou des décimaux), jamais des listes, des arbres ou des booléens.
- `a -> b` ajoute un arc de `a` vers `b`, `a <-> b` ajoute les deux arcs. `: p` donne un poids à l'arc ; sans poids, il vaut `1`. Un poids est un nombre positif ou nul.
- Un nœud existe dès qu'un arc le touche ; les nœuds sont rangés dans l'ordre où ils apparaissent. Ajouter un arc qui existe déjà remplace son poids.
- `v roto g` vaut `tia` si `v` est un nœud de `g`.
- `==` compare deux graphes par leurs nœuds et leurs arcs (poids compris), quel que soit l'ordre d'ajout.

### Opérateurs

- `+ - * %` sur deux entiers donnent un entier ; si l'un des opérandes est décimal, un décimal. `/` donne **toujours** un décimal. `%` suit la convention de Python (le reste a le signe du diviseur).
- `+` concatène aussi deux textes, ou deux listes (le résultat est une nouvelle liste). `"a" + 1` est une erreur : on écrit `"a" + parau(1)`.
- `< <= > >=` comparent deux nombres, ou deux textes (ordre alphabétique). `==` et `!=` comparent n'importe quelles valeurs.
- `ma` et `anei` sont paresseux : `hape ma f()` n'appelle pas `f`.
- `roto` teste l'appartenance : à une liste (un élément égal), à un texte (un sous-texte), à un arbre (une valeur de nœud), à un graphe (un nœud).
- `t[i]` lit l'élément `i` d'une liste ou d'un texte, en comptant à partir de 0 ; un indice négatif compte depuis la fin (`t[-1]` est le dernier).

### Affichage

- `faaite a, b, c;` affiche ses valeurs séparées par une espace, puis un saut de ligne. `faaite;` affiche une ligne vide.
- Les textes s'affichent sans guillemets ; les entiers et les décimaux comme en Python (`3`, `3.5`, `3.0`) ; les booléens `tia` / `hape` ; l'absence de valeur `aore`.
- Les listes s'affichent `[1, 2, 3]`. **À l'intérieur** d'une liste, d'un arbre ou d'un graphe, les textes sont entre guillemets, avec leurs échappements : `["a", "b\"c"]`.
- Un arbre s'affiche avec la syntaxe qui le construit : `tumu(1, tumu(2), tumu(3, tumu(4)))`.
- Un graphe s'affiche avec la syntaxe du littéral, un arc par arc orienté, dans l'ordre d'ajout ; le poids n'est affiché que s'il est différent de 1 : `upea { "A" -> "B" : 3, "B" -> "A" : 3, "B" -> "C" }`. Le graphe vide s'affiche `upea {}`.

### Fonctions prédéfinies

| Fonction | Ce qu'elle fait |
|---|---|
| `roa(x)` | *roa*, long : longueur d'une liste ou d'un texte, nombre de nœuds d'un arbre, nombre de nœuds d'un graphe |
| `amui(l, x)` | *ʻāmui*, réunir : ajoute `x` à la fin de la liste `l` ; renvoie `aore` |
| `numera(x)` | convertit en entier un texte (`"41"`), un décimal (tronqué vers zéro) ou un booléen |
| `tuhaa(x)` | *tuhaʻa*, part, fraction : convertit en décimal un texte ou un entier |
| `parau(x)` | *parau*, parole : le texte qu'afficherait `faaite x` |
| `tumu(v, e…)` | *tumu*, tronc, racine : construit un nœud d'arbre (voir *Arbres*) |
| `teitei(t)` | *teitei*, haut : hauteur d'un arbre, en arcs ; une feuille a la hauteur 0 |
| `rau(t)` | *rau*, feuille : la liste des valeurs des feuilles, de gauche à droite |
| `taati(g, a, b)` | *taʻati*, relier : ajoute l'arc `a -> b` de poids 1 ; `taati(g, a, b, p)` de poids `p` ; renvoie `aore` |
| `pihai(g, a)` | *pīhaʻi*, à côté : la liste des successeurs de `a`, dans l'ordre d'ajout |
| `motu(g)` | *motu*, île : la liste des nœuds du graphe |
| `teiaha(g, a, b)` | *teiaha*, poids : le poids de l'arc `a -> b` |
| `tae(g, a, b)` | *tae*, arriver : `tia` si `b` est atteignable depuis `a` (un nœud s'atteint lui-même) |
| `ea(g, a, b)` | *ʻeʻa*, chemin : le plus court chemin pondéré de `a` à `b` (algorithme de Dijkstra), sous forme de liste de nœuds, ou `aore` s'il n'y en a pas |

### Erreurs d'exécution

Le programme s'arrête, et l'utilisateur voit la **ligne Upea** en cause, jamais un traceback Python :

| Cause | Message |
|---|---|
| `1 / 0`, `1 % 0` | division par zéro |
| `[1, 2][5]` | indice hors limites |
| `numera("abc")` | conversion impossible : "abc" n'est pas un numera |
| `"a" + 1` | opération '+' impossible entre parau et numera |
| `pihai(g, "X")` (absent) | le nœud "X" n'est pas dans le graphe |
| `teiaha(g, "A", "C")` | pas d'arc de "A" vers "C" |
| `tataitahi x roto 5 { … }` | on ne peut pas parcourir un numera |
| `x.hotu` (x n'est pas un arbre) | seul un tumu a les champs hotu et amaa |
| récursion sans fin | récursion trop profonde |

## Types (extension 12)

Le typage est **graduel**. On peut annoter les déclarations, les paramètres et le type de retour des fonctions ; une valeur sans annotation et dont le type ne peut pas être déduit a le type **inconnu** (`?`), compatible avec tout. Le vérificateur ne signale une erreur que lorsqu'il **sait** que les types ne collent pas.

| Type | Valeurs |
|---|---|
| `numera` | entiers (*numera*, nombre) |
| `tuhaa` | décimaux (*tuhaʻa*, fraction) |
| `parau` | textes |
| `tiahape` | booléens (mot composé de `tia` et `hape`, assumé) |
| `aore` | l'absence de valeur |
| `tapura[T]` | listes d'éléments de type `T` (*tāpura*, liste) ; `tapura` seul vaut `tapura[?]` |
| `tumu[T]` | arbres dont les nœuds ont des valeurs de type `T` |
| `upea[T]` | graphes dont les nœuds sont de type `T` |

Règles :

- Un `numera` est accepté là où un `tuhaa` est attendu, pas l'inverse. Les types paramétrés suivent leur paramètre (`tapura[numera]` est accepté là où `tapura[tuhaa]` est attendu : choix assumé, plus souple que sûr).
- **Inférence** : `tuu x = 1;` donne à `x` le type `numera` ; `x = "deux";` est alors refusé. `tuu x = aore;` donne le type inconnu, et `tuu l = [];` le type `tapura[?]`.
- Une fonction sans `->` renvoie le type inconnu. Une fonction annotée `-> T` (autre que `aore`) doit renvoyer une valeur sur tous les chemins.
- Les conditions (`ahani`, `tamau`) et les opérandes de `ma`, `anei`, `eiaha` doivent être des `tiahape` ; les bornes d'un intervalle et les indices des `numera`.

| Expression | Type |
|---|---|
| `numera + numera` (et `-`, `*`, `%`) | `numera` |
| un opérande `tuhaa`, ou l'opérateur `/` | `tuhaa` |
| `parau + parau` | `parau` |
| `tapura[A] + tapura[B]` | `tapura` du type commun |
| comparaisons, `roto`, `ma`, `anei`, `eiaha` | `tiahape` |
| `[a, b]` | `tapura` du type commun de `a` et `b` (`?` s'ils diffèrent) |
| `l[i]` avec `l : tapura[T]` | `T` |
| `t[i]` avec `t : parau` | `parau` |
| `t.hotu`, `t.amaa` avec `t : tumu[T]` | `T`, `tapura[tumu[T]]` |
| `tumu(v, e…)` | `tumu` du type commun de `v` et des valeurs des enfants |
| `upea { a -> b, … }` | `upea` du type commun des nœuds |
| variable d'une boucle sur `tapura[T]`, `tumu[T]`, `upea[T]` | `T`, `tumu[T]`, `T` |
| `pihai(g, a)`, `motu(g)` avec `g : upea[T]` | `tapura[T]` |
| `ea(…)`, `teiaha(…)` | `?` |

## Erreurs (exemples de messages)

| Sorte | Programme | Message |
|---|---|---|
| lexicale | `tuu x = 3 @ 2;` | `1:11 : erreur lexicale : caractère inattendu : '@'` |
| lexicale | `faaite "Ia ora na;` | `1:8 : erreur lexicale : texte non terminé` |
| syntaxe | `tuu x = 1` puis `faaite x;` | `1:10 : erreur de syntaxe : ';' attendu après la déclaration, trouvé 'faaite'` |
| syntaxe | `ahani a < b < c { }` | `1:13 : erreur de syntaxe : les comparaisons ne s'enchaînent pas` |
| syntaxe | `1 = 2;` | `1:1 : erreur de syntaxe : on ne peut affecter qu'à une variable, un élément t[i] ou un champ t.hotu` |
| sémantique | `faaite y;` | `1:8 : erreur sémantique : 'y' n'est pas déclaré` |
| sémantique | `mau pi = 3.14; pi = 3;` | `1:16 : erreur sémantique : on ne peut pas affecter la constante 'pi'` |
| sémantique | `faaea;` | `1:1 : erreur sémantique : faaea hors d'une boucle` |
| sémantique | `tuu t = tumu(1); faaite t.taille;` | `1:27 : erreur sémantique : champ inconnu 'taille' : un tumu n'a que hotu et amaa` |
| de type | `tuu x: numera = "a";` | `1:17 : erreur de type : 'x' est déclaré numera, mais reçoit parau` |
| exécution | `faaite [1, 2][5];` | `1 : erreur d'exécution : indice hors limites` (la ligne seulement) |

Les erreurs lexicales, de syntaxe et sémantiques ne s'arrêtent pas à la première : toutes celles d'une même phase sont signalées en une fois. Les avertissements (variable déclarée mais jamais utilisée, code placé après un `hoi`, `faaea` ou `haere`) n'empêchent pas l'exécution.

## Programmes d'exemple

Les programmes de `exemples/` ont chacun leur sortie attendue exacte (`.attendu`) :

| Fichier | Ce qu'il montre |
|---|---|
| `01_ia_ora_na.upea` | variables, constantes, textes, arithmétique, logique, conversions, affichage |
| `02_fibonacci.upea` | fonctions typées, récursion, intervalles `..` et `..=`, boucle de zéro tour, fonction sans `hoi` |
| `03_tapura.upea` | listes, `ahani` / `taae ahani` / `taae`, `roto`, `faaea` / `haere`, globale modifiée dans une fonction |
| `04_tumu.upea` | arbres : construction, champs, récursion, `teitei`, `rau`, parcours en profondeur et en largeur, modification |
| `05_motu.upea` | graphe des îles : littéral `upea`, parcours depuis Tahiti, `ea` (Dijkstra), `tae`, `taati`, `teiaha` |
| `06_tahua.upea` | non-régression (~60 lignes) : tri topologique d'un graphe de tâches, détection de cycle, évaluation d'un arbre d'expression |

## Utilisation

```
python -m upea run       programme.upea [--backend python|ast] [--trace] [--sans-types]
python -m upea transpile programme.upea [--backend python|ast|formateur] [-o sortie.py] [--sourcemap]
python -m upea check     programme.upea [--sans-types]
python -m upea fmt       programme.upea [--ecrire]
python -m upea repl
```

Codes de retour : `0` succès, `1` erreur de compilation (ou fichier illisible), `2` erreur d'utilisation (réservé par `argparse`), `3` erreur d'exécution. Les erreurs et les avertissements vont sur la sortie d'erreur.

## Limites assumées

- Pas de dictionnaires, de fonctions imbriquées ni de fonctions comme valeurs ; pas de récursion croisée.
- Pas de lecture au clavier, ni de fichiers, ni de réseau : un programme Upea ne touche pas au système.
- Les arbres ont des enfants ordonnés et en nombre quelconque ; un arbre binaire « avec un trou » se représente avec une convention du programmeur.
- Un nœud de graphe isolé (sans aucun arc) ne peut pas exister.
- `ma` et `anei` sur des valeurs non booléennes suivent Python (`hape anei 3` vaut `3`), de même que `tia == 1` (vaut `tia`) : le vérificateur de types refuse ces mélanges quand il connaît les types.
- Le formateur perd les commentaires, qui ne sont pas dans l'arbre syntaxique.
- Les colonnes d'une erreur d'exécution ne sont pas connues : seule la ligne est indiquée.
