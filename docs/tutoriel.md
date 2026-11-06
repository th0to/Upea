# Apprendre Upea

Ce tutoriel va pas à pas, du premier programme aux graphes et aux arbres ordonnés.
Chaque leçon tient en une explication courte, un exemple et sa sortie, puis un
exercice et sa solution. Pour le détail d'une construction, chaque leçon renvoie à la
[spécification](../projet/specification.md), qui fait foi.

Tous les programmes de cette page sont exécutés par les tests du projet : la sortie
montrée est celle qu'ils affichent vraiment.

## 0. Installer, et lancer un premier programme

Installez le projet comme le dit le [README](../README.md#installation). Puis créez,
dans le dossier `projet/`, un fichier `bonjour.upea` :

```upea
faaite "Ia ora na !";
```

Lancez-le depuis `projet/` :

```bash
uv run python -m upea run bonjour.upea
```

```sortie
Ia ora na !
```

`faaite` affiche ses valeurs, et chaque instruction se termine par `;`. Pour vérifier
un programme sans l'exécuter, remplacez `run` par `check`.

## 1. Afficher et nommer

`tuu` déclare une variable, `mau` une constante. Un nom se déclare une seule fois, et
avant de servir. `faaite` sépare ses valeurs par une espace.

```upea
// Un commentaire va jusqu'au bout de la ligne.
tuu ile = "Moorea";
mau km = 17;   // une constante : on ne peut plus l'affecter
faaite "De Tahiti à", ile, ":", km, "km";
ile = "Huahine";
faaite "puis", ile;
```

```sortie
De Tahiti à Moorea : 17 km
puis Huahine
```

Les noms des fonctions prédéfinies sont réservés : une variable ne peut pas s'appeler
`distance` ou `roa`. Voir la spécification, [*Variables, constantes et
portées*](../projet/specification.md#variables-constantes-et-portées).

**Exercice.** Déclarez un prénom et un âge, affichez une phrase avec les deux, puis
augmentez l'âge d'un an et affichez-le de nouveau.

<details>
<summary>Solution</summary>

```upea
tuu prenom = "Teva";
tuu age = 19;
faaite prenom, "a", age, "ans.";
age = age + 1;
faaite "L'an prochain,", prenom, "aura", age, "ans.";
```

```sortie
Teva a 19 ans.
L'an prochain, Teva aura 20 ans.
```

</details>

## 2. Valeurs et opérateurs

Upea a des entiers, des décimaux, des textes, des booléens (`tia`, `hape`) et `aore`,
l'absence de valeur. `/` donne toujours un décimal. `ma`, `anei` et `eiaha` sont le
« et », le « ou » et le « non ». `roto` teste l'appartenance. Un indice compte à partir
de 0, et un indice négatif depuis la fin.

```upea
faaite 7 / 2, 7 % 2, 2 + 3 * 4, (2 + 3) * 4;
faaite "Ia ora" + " na", "n°" + parau(1);
faaite tia ma hape, tia anei hape, eiaha tia;
faaite 3 < 5, "abc" < "abd", 2 roto [1, 2, 3];
tuu l = [10, 20, 30];
faaite l[0], l[-1], roa(l);
```

```sortie
3.5 1 14 20
Ia ora na n°1
hape tia hape
tia tia tia
10 30 3
```

Un texte ne s'ajoute pas à un nombre : on écrit `"n°" + parau(1)`. Les comparaisons ne
s'enchaînent pas : `a < b < c` est une erreur, on écrit `a < b ma b < c`. Voir
[*Opérateurs*](../projet/specification.md#opérateurs) et [*Priorité et associativité
des opérateurs*](../projet/specification.md#priorité-et-associativité-des-opérateurs).

**Exercice.** Combien de secondes font 3 heures et 25 minutes ? Utilisez deux
constantes.

<details>
<summary>Solution</summary>

```upea
mau heures = 3;
mau minutes = 25;
faaite heures * 3600 + minutes * 60, "secondes";
```

```sortie
12300 secondes
```

</details>

## 3. Décider et répéter

`ahani` est le « si », `taae ahani` le « sinon si », `taae` le « sinon ». `tamau`
répète tant que la condition est vraie. `tataitahi … roto` parcourt un intervalle (`a..b`
exclut `b`, `a..=b` l'inclut), une liste ou un texte. Dans une boucle, `haere` passe au
tour suivant et `faaea` en sort.

```upea
tuu n = 7;
ahani n % 2 == 0 {
    faaite n, "est pair";
} taae ahani n > 5 {
    faaite n, "est impair et plus grand que 5";
} taae {
    faaite n, "est impair";
}

tuu i = 0;
tamau i < 3 {
    faaite "tour", i;
    i = i + 1;
}

tataitahi k roto 1..=10 {
    ahani k % 3 != 0 { haere; }   // au tour suivant
    ahani k > 7 { faaea; }        // on sort de la boucle
    faaite k;
}
```

```sortie
7 est impair et plus grand que 5
tour 0
tour 1
tour 2
3
6
```

Voir [*Structures de contrôle*](../projet/specification.md#structures-de-contrôle) et
[*La boucle `tataitahi`*](../projet/specification.md#la-boucle-tataitahi).

**Exercice.** Affichez la somme des entiers de 1 à 100.

<details>
<summary>Solution</summary>

```upea
tuu somme = 0;
tataitahi k roto 1..=100 {
    somme = somme + k;
}
faaite somme;
```

```sortie
5050
```

</details>

## 4. Fonctions

`ohipa` déclare une fonction, au niveau global et avant son premier appel ; `hoi`
renvoie une valeur. Les annotations de types sont facultatives (le typage est
graduel), mais le vérificateur s'en sert dès la compilation. Une fonction peut
s'appeler elle-même.

```upea
ohipa carre(n: numera) -> numera {
    hoi n * n;
}

ohipa factorielle(n: numera) -> numera {
    ahani n <= 1 {
        hoi 1;
    }
    hoi n * factorielle(n - 1);
}

faaite carre(12), factorielle(20);
```

```sortie
144 2432902008176640000
```

Les entiers n'ont pas de limite de taille. Un argument du mauvais type est refusé
avant l'exécution :

```upea
ohipa carre(n: numera) -> numera {
    hoi n * n;
}
faaite carre("douze");
```

```erreur
exemple.upea:4:14 : erreur de type : argument 1 de 'carre' : numera attendu, parau reçu
    faaite carre("douze");
                 ^
```

Voir [*Fonctions*](../projet/specification.md#fonctions) et
[*Types*](../projet/specification.md#types-extension-12).

**Exercice.** Écrivez `est_premier(n)`, qui rend `tia` si `n` est premier, puis
affichez la liste des nombres premiers plus petits que 30.

<details>
<summary>Solution</summary>

```upea
ohipa est_premier(n: numera) -> tiahape {
    ahani n < 2 {
        hoi hape;
    }
    tataitahi d roto 2..n {
        ahani n % d == 0 {
            hoi hape;
        }
    }
    hoi tia;
}

tuu premiers = [];
tataitahi n roto 1..30 {
    ahani est_premier(n) {
        amui(premiers, n);
    }
}
faaite premiers;
```

```sortie
[2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
```

</details>

## 5. Listes

Une liste (`tapura`) s'écrit `[…]` et se modifie : `amui` ajoute à la fin, `tatara`
retire, `l[i] = x` remplace. `roa` donne la longueur, `iti` et `rahi` le plus petit
et le plus grand élément, `+` met deux listes bout à bout. Dans une liste, les textes
s'affichent entre guillemets.

```upea
tuu courses = ["taro", "mangues"];
amui(courses, "ananas");
faaite courses, roa(courses);
tatara(courses, "taro");
courses[0] = "papayes";
faaite courses;
tataitahi x roto courses {
    faaite "-", x;
}
faaite iti([5, 3, 8]), rahi([5, 3, 8]), [1, 2] + [3];
```

```sortie
["taro", "mangues", "ananas"] 3
["papayes", "ananas"]
- papayes
- ananas
3 8 [1, 2, 3]
```

Voir [*Fonctions prédéfinies*](../projet/specification.md#fonctions-prédéfinies).

**Exercice.** Écrivez `renverser(l)`, qui rend une nouvelle liste avec les éléments
de `l` dans l'ordre inverse.

<details>
<summary>Solution</summary>

```upea
ohipa renverser(l) {
    tuu resultat = [];
    tataitahi i roto 0..roa(l) {
        amui(resultat, l[roa(l) - 1 - i]);
    }
    hoi resultat;
}

faaite renverser([1, 2, 3, 4]);
faaite renverser([]);
```

```sortie
[4, 3, 2, 1]
[]
```

</details>

## 6. Arbres

`tumu(v, e1, e2…)` construit un nœud de valeur `v`, dont les enfants sont des arbres.
`t.hotu` est sa valeur, `t.amaa` la liste de ses enfants. `faaite` d'un arbre seul le
dessine ; `parau` l'écrit sur une ligne. `tataitahi` parcourt les nœuds, en profondeur
(par défaut) ou en largeur (`aano`).

```upea
tuu arbre = tumu("A", tumu("B", tumu("D")), tumu("C"));
faaite arbre;
faaite arbre.hotu, roa(arbre), teitei(arbre), rau(arbre);
tataitahi n roto arbre aano {
    faaite n.hotu;
}
amui(arbre.amaa[1].amaa, tumu("E"));
faaite parau(arbre);
```

```sortie
A
├── B
│   └── D
└── C
A 4 2 ["D", "C"]
A
B
C
D
tumu("A", tumu("B", tumu("D")), tumu("C", tumu("E")))
```

`teitei` donne la hauteur, `rau` les feuilles. Voir [*Arbres
(`tumu`)*](../projet/specification.md#arbres-tumu) et [*Algorithmes
d'arbres*](../projet/specification.md#algorithmes-darbres).

**Exercice.** Écrivez une fonction récursive `somme(t)`, qui additionne les valeurs de
tous les nœuds d'un arbre de nombres.

<details>
<summary>Solution</summary>

```upea
ohipa somme(t) -> numera {
    tuu total = t.hotu;
    tataitahi enfant roto t.amaa {
        total = total + somme(enfant);
    }
    hoi total;
}

faaite somme(tumu(1, tumu(2, tumu(4)), tumu(3)));
```

```sortie
10
```

</details>

## 7. Graphes

Un graphe (`upea`) est orienté et pondéré : `a -> b : p` ajoute un arc de poids `p`
(1 par défaut), `a <-> b` les deux sens. `pihai` donne les successeurs d'un nœud,
`teiaha` le poids d'un arc, `taati` ajoute un arc. `tataitahi … mai d` parcourt ce
qui est atteignable depuis `d`, en profondeur ou en largeur (`aano`). Le prélude
fournit les algorithmes classiques.

```upea
tuu reseau = upea {
    "A" -> "B" : 4,
    "A" -> "C" : 1,
    "C" -> "B" : 2,
    "B" -> "D" : 5,
};
faaite reseau;
faaite pihai(reseau, "A"), teiaha(reseau, "A", "C");
faaite dijkstra(reseau, "A", "D"), distance(reseau, "A", "D");
tataitahi n roto reseau mai "A" {
    faaite n;
}
taati(reseau, "D", "E");
faaite tae(reseau, "A", "E"), cycle(reseau);
```

```sortie
upea : 4 nœuds, 4 arcs
A → B (4), C
B → D (5)
C → B (2)
D ·
["B", "C"] 1
["A", "C", "B", "D"] 8
A
B
D
C
tia hape
```

Le plus court chemin de `A` à `D` passe par `C` (1 + 2 + 5 = 8), et non par l'arc
direct vers `B` (4 + 5 = 9). Voir [*Graphes (`upea`)*](../projet/specification.md#graphes-upea)
et [*Algorithmes de graphes*](../projet/specification.md#algorithmes-de-graphes).

**Exercice.** Pour chaque nœud de `upea { "A" -> "B", "A" -> "C", "B" -> "C", "D" }`,
affichez le nombre d'arcs qui en partent. (`"D"`, écrit seul, est un nœud isolé.)

<details>
<summary>Solution</summary>

```upea
tuu g = upea { "A" -> "B", "A" -> "C", "B" -> "C", "D" };
tataitahi n roto g {
    faaite n, roa(pihai(g, n));
}
```

```sortie
A 2
B 1
C 0
D 0
```

</details>

## 8. Arbres ordonnés

Les arbres ordonnés rangent des clés : l'ABR (`imi`), l'AVL (`aifaito`), le
rouge-noir (`uteere`), l'arbre B (`pupu`), et les tas (`ahu`, tas min ; `ahunui`, tas
max). `amui` ajoute une clé, `tatara` en retire une, `iriti` extrait la plus petite
(ou le sommet d'un tas). Rempli dans l'ordre, un ABR devient un peigne ; un AVL se
rééquilibre.

```upea
tuu peigne = imi [];
tuu avl = aifaito [];
tataitahi i roto 1..=7 {
    amui(peigne, i);
    amui(avl, i);
}
faaite teitei(peigne), teitei(avl);
faaite avl;

tuu file = ahu [5, 1, 4];
amui(file, 2);
faaite iriti(file), iriti(file), file;
```

```sortie
6 2
      4
  ┌───┴───┐
  2       6
┌─┴─┐   ┌─┴─┐
1   3   5   7
1 2 ahu [4, 5]
```

Voir [*Arbres ordonnés*](../projet/specification.md#arbres-ordonnés-imi-aifaito-uteere-pupu-ahu-ahunui).

**Exercice.** Triez la liste `[9, 4, 7, 1, 8]` avec un tas : ajoutez-y chaque élément,
puis extrayez-les tant qu'il en reste.

<details>
<summary>Solution</summary>

```upea
tuu tas = ahu [];
tataitahi x roto [9, 4, 7, 1, 8] {
    amui(tas, x);
}
tuu trie = [];
tamau roa(tas) > 0 {
    amui(trie, iriti(tas));
}
faaite trie;
```

```sortie
[1, 4, 7, 8, 9]
```

</details>

## 9. Dessins et exports

`faaite` d'une structure seule la dessine (`hohoa` rend le même dessin sous forme de
texte). `matrice` donne la matrice d'adjacence d'un graphe, `dot` et `mermaid` le
texte que Graphviz et Mermaid transforment en image.

```upea
tuu g = upea { "A" <-> "B" : 3, "B" -> "C" };
faaite g;
faaite matrice(g);
faaite mermaid(g);
```

```sortie
upea : 3 nœuds, 3 arcs
A → B (3)
B → A (3), C
C ·
  A B C
A · 3 ·
B 3 · 1
C · · ·
flowchart LR
  n0["A"]
  n1["B"]
  n2["C"]
  n0 <-->|3| n1
  n1 --> n2
```

Voir [*Dessins*](../projet/specification.md#dessins). L'exemple
`projet/exemples/10_hohoa.upea` les montre tous.

## 10. Lire un message d'erreur

Un message donne le fichier, la ligne et la colonne, la sorte d'erreur et ce qui ne
va pas, puis la ligne fautive avec un `^` sous l'endroit en cause. Un `;` oublié est
signalé là où il manque, à la fin de la ligne :

```upea
tuu x = 1
faaite x;
```

```erreur
exemple.upea:1:10 : erreur de syntaxe : ';' attendu après la déclaration, trouvé 'faaite'
    tuu x = 1
             ^
```

Toutes les erreurs d'une même phase sont signalées en une fois, la syntaxe d'abord,
puis les noms et les types :

```upea
faaite total;
faaite moyenne;
```

```erreur
exemple.upea:1:8 : erreur sémantique : 'total' n'est pas déclaré
    faaite total;
           ^
exemple.upea:2:8 : erreur sémantique : 'moyenne' n'est pas déclaré
    faaite moyenne;
           ^
```

Une erreur d'exécution donne la ligne Upea, jamais un traceback Python. Voir
[*Erreurs*](../projet/specification.md#erreurs-exemples-de-messages) et [*Erreurs
d'exécution*](../projet/specification.md#erreurs-dexécution).

**Exercice.** Ce programme doit afficher la moyenne des notes. Corrigez-le, en lisant
les messages de `check` un à un.

```upea
tuu notes = [12, 15, 9];
tuu somme = 0;
tataitahi n roto notes {
    somme = somme + n
}
faaite "moyenne :", somme / roa(note);
```

```erreur
exemple.upea:4:22 : erreur de syntaxe : ';' attendu après l'affectation, trouvé '}'
        somme = somme + n
                         ^
```

<details>
<summary>Solution</summary>

Une fois le `;` ajouté, `check` signale l'erreur suivante : `'note' n'est pas déclaré
(vouliez-vous dire 'notes' ?)`, ligne 6, colonne 33. Le programme corrigé :

```upea
tuu notes = [12, 15, 9];
tuu somme = 0;
tataitahi n roto notes {
    somme = somme + n;
}
faaite "moyenne :", somme / roa(notes);
```

```sortie
moyenne : 12.0
```

</details>

## 11. Le REPL

`uv run python -m upea repl` ouvre une session : on tape une instruction, ou une
expression seule, que le REPL affiche. Les déclarations restent d'une saisie à
l'autre, un bloc ouvert attend la suite (`....>`), et une erreur n'efface rien.
`:aide` liste les commandes, comme `:tokens`, `:arbre` et `:python`. Une session :

```text
upea> tuu x = 6;
upea> x * 7
42
upea> ohipa double(n) {
....>     hoi 2 * n;
....> }
upea> double(x)
12
upea> faaite y;
<repl>:7:8 : erreur sémantique : 'y' n'est pas déclaré
    faaite y;
           ^
upea> :tokens x + 1
Token(IDENT, 'x', 1:1)
Token(PLUS, '+', 1:3)
Token(ENTIER, '1', 1:5)
Token(FIN, '', 1:6)
upea>
```

Ctrl-D (Ctrl-Z puis Entrée sous Windows) quitte la session.

## 12. Pour aller plus loin

- Les programmes de [`projet/exemples/`](../projet/exemples/), chacun avec sa sortie
  exacte dans un fichier `.attendu` : `06_tahua.upea` résout un vrai petit problème,
  `08_algorithmes_graphes.upea` et `09_algorithmes_arbres.upea` montrent tous les
  algorithmes.
- La [spécification](../projet/specification.md) entière, en particulier ses
  [*Limites assumées*](../projet/specification.md#limites-assumées).
- `transpile`, pour voir le Python qu'Upea produit
  (`uv run python -m upea transpile bonjour.upea`), et l'[architecture](architecture.md)
  du compilateur.
