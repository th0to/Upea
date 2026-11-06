<!-- Fichier généré par `upea/aide.py` (`uv run python -m upea.aide --ecrire`) : ne pas le modifier à la main. -->

# Upea 1.0.0 : l'aide-mémoire (à lire en premier)

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
- Arbres : `tumu(1, tumu(2), tumu(3))`, champs `a.hotu` (valeur) et `a.amaa` (liste des enfants), `prefixe(a)`, `teitei(a)` ; ajouter un enfant : `amui(a.amaa, tumu(4))` ; arbres de recherche et tas : `aifaito [5, 3, 8]`, `ahu [3, 1]`.
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

```sortie
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
- Ni classes, ni méthodes : un état global et des fonctions, ou une liste par objet (`aide("depuis_python")` en donne la recette).
- Pas de `//` : c'est un commentaire. La division entière s'écrit `numera(a / b)`, qui tronque vers zéro ; le `//` de Python arrondit vers le bas, ce qui diffère pour les négatifs (la formule exacte est dans `depuis_python`).
- Ni fonctions imbriquées, ni fonctions comme valeurs, ni récursion croisée, ni `+=`, ni comparaisons chaînées, ni `for … in` ni `range` ni `len` (voir `tataitahi` et `roa`).

Pour le détail : `aide("depuis_python")` (la traduction pas à pas), `aide("specification")`, `exemples()`.
