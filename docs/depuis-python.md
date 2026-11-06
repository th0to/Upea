<!-- Fichier généré par `upea/aide.py` (`uv run python -m upea.aide --ecrire`) : ne pas le modifier à la main. -->

# De Python à Upea

Pour qui connaît Python : ce qui change, le tableau des équivalences, et comment remplacer ce qu'Upea n'a pas (dictionnaires, ensembles, tri, hasard, clavier).

## Ce qui change le plus

- **Toute variable se déclare** avant son premier usage, une seule fois, avec `tuu` (ou `mau` pour une constante) : `compteur = 0;` sans déclaration est une erreur, `tuu compteur = 0;` la déclare. On ne redéclare pas un nom encore visible.
- Les instructions finissent par `;` et les blocs sont entre accolades : l'indentation ne compte pas.
- **Pas de dictionnaires, de tuples, ni de méthodes** (`l.append(x)` devient `amui(l, x)`, `len(l)` devient `roa(l)`). Les recettes plus bas les remplacent.
- Une fonction (`ohipa`) se déclare **au niveau global**, avant son premier appel ; pas de fonction imbriquée, ni de fonction comme valeur, ni de récursion croisée. Elle peut lire et modifier les variables globales déclarées avant elle.
- Les comparaisons ne s'enchaînent pas : `a < b ma b < c` au lieu de `a < b < c`.
- `ma`, `anei`, `eiaha` pour `and`, `or`, `not` ; `tia`, `hape`, `aore` pour `True`, `False`, `None`.
- `/` rend toujours un décimal ; il n'y a ni `//` ni `**`. Pour coller un nombre à un texte : `"n = " + parau(n)`.
- **Un programme est arrêté au bout de 5 s** (démarrage de Python compris) : une exploration exponentielle (l'espace des états d'un taquin, par exemple) le dépasse vite ; réduisez la profondeur ou la taille du problème.
- **Pas de clavier, de fichiers, de réseau ni d'aléatoire** : un programme ne fait que calculer et afficher.
- Pour un arbre ou un graphe, préférez les structures et les algorithmes d'Upea (`upea { "A" -> "B" : 3 }`, `tumu`, `aifaito`, `dijkstra`, `bfs`…) à une réimplémentation avec des listes.

## Les équivalences

| Python | Upea |
|---|---|
| `x = 1` | `tuu x = 1;` |
| `MAX = 10` | `mau MAX = 10;` |
| `x += 1` | `x = x + 1;` |
| `# commentaire` | `// commentaire` |
| `def f(a, b):` | `ohipa f(a, b) { … }` |
| `return v` | `hoi v;` |
| `if c: … elif d: … else: …` | `ahani c { … } taae ahani d { … } taae { … }` |
| `while c:` | `tamau c { … }` |
| `while True:` | `tamau tia { … }` |
| `for i in range(a, b):` | `tataitahi i roto a..b { … }` |
| `for i in range(a, b + 1):` | `tataitahi i roto a..=b { … }` |
| `for x in l:` | `tataitahi x roto l { … }` |
| `break` | `faaea;` |
| `continue` | `haere;` |
| `print(a, b)` | `faaite a, b;` |
| `True` | `tia` |
| `False` | `hape` |
| `None` | `aore` |
| `a and b` | `a ma b` |
| `a or b` | `a anei b` |
| `not a` | `eiaha a` |
| `x in l` | `x roto l` |
| `a < b < c` | `a < b ma b < c` |
| `a // b` | `div_ent(a, b)` |
| `len(l)` | `roa(l)` |
| `l.append(x)` | `amui(l, x);` |
| `l.remove(x)` | `tatara(l, x);` |
| `min(l)` | `iti(l)` |
| `max(l)` | `rahi(l)` |
| `int(x)` | `numera(x)` |
| `float(x)` | `tuhaa(x)` |
| `str(x)` | `parau(x)` |
| `"n = " + str(n)` | `"n = " + parau(n)` |
| `l[-1]` | `l[-1]` |
| `heapq.heappush(h, x)` | `amui(h, x);` |
| `heapq.heappop(h)` | `iriti(h)` |

Il n'y a pas d'opérateur de puissance (`x ** 2` : écrivez `x * x`), pas d'expression conditionnelle (`a if c else b` : un `ahani`) ; `//` est un commentaire (voir la division entière plus bas).

## Remplacer ce qu'Upea n'a pas

### Un dictionnaire : une liste de paires

Une liste de paires `[clé, valeur]`, et deux fonctions pour lire et écrire. Python :

```python
stock = {"pommes": 3, "poires": 5}
stock["bananes"] = 7
stock["pommes"] = 4
print(stock.get("pommes"), stock.get("bananes"), stock.get("kiwis"))
```

Upea :

```upea
ohipa chercher(paires, cle) {
    tataitahi p roto paires {
        ahani p[0] == cle {
            hoi p[1];
        }
    }
    hoi aore;
}

ohipa mettre(paires, cle, valeur) {
    tataitahi p roto paires {
        ahani p[0] == cle {
            p[1] = valeur;
            hoi;
        }
    }
    amui(paires, [cle, valeur]);
}

tuu stock = [["pommes", 3], ["poires", 5]];
mettre(stock, "bananes", 7);
mettre(stock, "pommes", 4);
faaite chercher(stock, "pommes"), chercher(stock, "bananes"), chercher(stock, "kiwis");
faaite stock;
```

```sortie
4 7 aore
[["pommes", 4], ["poires", 5], ["bananes", 7]]
```

La recherche parcourt la liste : c'est linéaire, comme `in` sur une liste Python.

### Un dictionnaire de nombres : un graphe

Quand les valeurs sont des nombres, un graphe fait l'affaire : la valeur d'une clé est le poids de l'arc qui va d'un nœud « racine » à cette clé. `taati` écrit (et remplace), `teiaha` lit, `roto` teste la présence, `pihai` donne les clés.

```upea
tuu stock = upea { "racine" };
taati(stock, "racine", "pommes", 3);
taati(stock, "racine", "poires", 5);
taati(stock, "racine", "pommes", 4);
faaite teiaha(stock, "racine", "pommes"), "pommes" roto stock, "kiwis" roto stock;
faaite pihai(stock, "racine");
```

```sortie
4 tia hape
["pommes", "poires"]
```

### Un ensemble : un arbre ordonné

Un arbre ordonné (`imi`, `aifaito`, `uteere`, `pupu`) est un ensemble : ajouter une clé déjà présente ne fait rien, `roto` teste l'appartenance, `tatara` retire, et `tataitahi` parcourt les clés dans l'ordre croissant. Python :

```python
vus = set()
for x in [5, 3, 5, 1, 3]:
    vus.add(x)
print(len(vus), 3 in vus, 4 in vus)
```

Upea :

```upea
tuu vus = aifaito [];
tataitahi x roto [5, 3, 5, 1, 3] {
    amui(vus, x);
}
faaite roa(vus), 3 roto vus, 4 roto vus;
tatara(vus, 3);
tataitahi x roto vus {
    faaite x;
}
```

```sortie
3 tia hape
1
5
```

### Trier une liste

Il n'y a pas de `sorted`. Un tas min (`ahu`) rend ses clés dans l'ordre, doublons compris : on y verse la liste, puis on la relit. Python :

```python
print(sorted([5, 3, 8, 3, 1]))
```

Upea :

```upea
tuu tas = ahu [];
tataitahi x roto [5, 3, 8, 3, 1] {
    amui(tas, x);
}
tuu trie = [];
tataitahi x roto tas {
    amui(trie, x);
}
faaite trie;
```

```sortie
[1, 3, 3, 5, 8]
```

### Plusieurs valeurs de retour : une liste

```upea
ohipa min_max(l) {
    hoi [iti(l), rahi(l)];
}
tuu r = min_max([4, 9, 2]);
faaite "min", r[0], "max", r[1];
```

```sortie
min 2 max 9
```

### Une classe : un état et des fonctions

Il n'y a ni classes ni méthodes. Pour un seul objet, l'état devient des variables globales et les méthodes des fonctions, qui lisent et modifient les globales déclarées avant elles. Python :

```python
class Compteur:
    def __init__(self):
        self.n = 0

    def incremente(self):
        self.n += 1
        return self.n

c = Compteur()
c.incremente()
print(c.incremente())
```

Upea :

```upea
tuu n = 0;

ohipa incremente() -> numera {
    n = n + 1;
    hoi n;
}

incremente();
faaite incremente();
```

```sortie
2
```

Pour plusieurs objets, une liste par objet (ses champs sont ses cases), que l'on passe aux fonctions :

```upea
ohipa nouveau_compteur() {
    hoi [0];
}

ohipa incremente(c) {
    c[0] = c[0] + 1;
    hoi c[0];
}

tuu a = nouveau_compteur();
tuu b = nouveau_compteur();
incremente(a);
incremente(a);
incremente(b);
faaite a[0], b[0];
```

```sortie
2 1
```

### La division entière : `//`

`//` n'existe pas : c'est le début d'un commentaire. `/` rend toujours un décimal, et `numera(a / b)` tronque vers zéro, alors que le `//` de Python arrondit vers le bas : les deux diffèrent dès que le résultat est négatif (`-7 // 2` vaut -4, `numera(-7 / 2)` vaut -3). Le reste `%` est le même qu'en Python. La formule exacte pour les deux signes retranche 1 quand la division ne tombe pas juste et que les signes diffèrent. Python :

```python
print(7 // 2, -7 // 2, 7 // -2, -7 // -2)
```

Upea :

```upea
ohipa div_ent(a: numera, b: numera) -> numera {
    tuu q = numera(a / b);
    ahani a % b != 0 ma (a < 0) != (b < 0) {
        q = q - 1;
    }
    hoi q;
}

faaite div_ent(7, 2), div_ent(-7, 2), div_ent(7, -2), div_ent(-7, -2);
faaite numera(-7 / 2), div_ent(6, -3);
```

```sortie
3 -4 -4 3
-3 -2
```

### Le hasard : un générateur pseudo-aléatoire

Il n'y a pas de `random`. Un générateur congruentiel linéaire, écrit en Upea, donne une suite qui a l'air aléatoire et qui est toujours la même pour une même graine : c'est pratique pour tester. Python :

```python
import random
print([random.randint(1, 6) for _ in range(8)])
```

Upea :

```upea
tuu graine = 42;

ohipa alea(n: numera) -> numera {
    graine = (graine * 1103515245 + 12345) % 2147483648;
    hoi graine % n;
}

tuu des = [];
tataitahi i roto 0..8 {
    amui(des, alea(6) + 1);
}
faaite des;
```

```sortie
[4, 3, 6, 5, 2, 1, 6, 1]
```

Pour une autre suite, changez la graine.

### Le clavier : des constantes

Un programme Upea ne lit rien : les réponses attendues de l'utilisateur deviennent des constantes, écrites en tête du programme. Dites-le à qui lira le programme. Python :

```python
nom = input()
age = int(input())
print("Ia ora na", nom + ", dans un an vous aurez", age + 1, "ans.")
```

Upea :

```upea
mau nom = "Teva";
mau age = 27;
faaite "Ia ora na", nom + ", dans un an vous aurez", age + 1, "ans.";
```

```sortie
Ia ora na Teva, dans un an vous aurez 28 ans.
```
