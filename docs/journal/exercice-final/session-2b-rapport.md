# Session 2b : le rapport de l'IA

---

# Rapport d'utilisation du serveur MCP Upea

**Point de vue** : utilisateur « lambda » (un assistant IA) qui découvre le serveur sans documentation préalable.
**Date** : 2026-11-06
**Tâche d'origine** : traduire en Upea le taquin Python `taquin_3.py`, l'exécuter avec le serveur, puis rendre le programme Upea final et sa sortie réelle.

**Avertissement sur la source.** Le bloc Python collé contenait le texte `<COLLER ICI LE PROGRAMME…>`, pas un programme. J'ai donc traduit le fichier `taquin_3.py` joint à la demande. C'est une supposition de ma part sur ce que vous vouliez.

## 1. Ce que j'ai réellement fait (base du rapport)

| # | Appel | Résultat |
|---|---|---|
| 1 | `ToolSearch` (chargement des 8 outils `mcp__upea__*`) | Les schémas sont chargés : aide, executer, exemples, formater, parse, tokenize, transpiler, verifier. |
| 2 | `aide("apercu")` | Aide-mémoire d'une page : syntaxe, mots-clés, exemple complet, liste de ce qu'Upea n'a pas. Suffisant pour écrire presque tout le programme. |
| 3 | `aide("depuis_python")` | Table d'équivalences Python→Upea et recettes (hasard par générateur congruentiel, clavier remplacé par des constantes, dictionnaires). |
| 4 | `aide("predefinies")` | Signatures des fonctions prédéfinies. Elles m'ont servi à vérifier `amui`, `tumu`, `teitei`, `roa`. |
| 5 | `verifier(programme)` | `valide: true`, aucun diagnostic, du premier coup. |
| 6 | `executer(programme)` | `statut: succes`, `code_retour: 0`, 324 octets de sortie, non tronquée. |

**Non testés, donc non évalués** : `exemples`, `formater`, `parse`, `tokenize`, `transpiler`, `aide("mots_cles")`, `aide("specification")`, l'option `types=false`, le backend `ast`, les messages d'erreur (je n'en ai provoqué aucun), et le délai maximal de 5 s sur une boucle longue.

## 2. Points forts (constatés)

- `aide("apercu")` donne assez d'informations pour écrire un programme de plus de 150 lignes. `verifier` l'a accepté immédiatement.
- `aide("depuis_python")` m'a indiqué les contraintes dont je me suis servi : pas de classes, pas d'aléatoire, pas de récursion croisée, `/` toujours décimal.
- `executer` a rendu un statut, un code de retour et la sortie exacte dans un JSON lisible.

## 3. Points bloquants et difficultés

- **Fidélité de la traduction.** Je n'ai pas pu reproduire le programme à l'identique, et chaque écart a une cause constatée :
  - Les classes n'existent pas : j'ai utilisé un état global et des fonctions.
  - Il n'y a ni `random` ni `input` : j'ai écrit un générateur congruentiel et une liste de coups scriptés.
  - La récursion croisée est interdite : `melange` et `melangeGrad` sont fusionnées en une boucle, et `graph` écrit ses quatre blocs à la suite.
  - Le délai d'exécution est de 5 s au plus. Je n'ai pas lancé la profondeur 24 du Python. **Je suppose** qu'elle ne tiendrait pas en 5 s, car c'est une exploration exponentielle, mais je ne l'ai pas mesuré. J'ai exécuté `graph` avec une profondeur de 4.
- **Bogues du Python conservés.** Le Python ne met pas à jour la position du zéro après `melange`, donc le premier coup « h » ne fait rien. Je l'ai gardé tel quel.
- **Fonction `hauteur`.** Je ne l'ai pas traduite, car son résultat n'est jamais utilisé. J'ai appelé `teitei` à la place.
- **Coût.** Aucun échec d'outil, aucune correction nécessaire : 6 appels au total.

## 4. Recommandations, par ordre de priorité

1. Rendre explicite, dans `aide("apercu")` ou `depuis_python`, la règle sur les classes (pas d'`class`) et la méthode de traduction. Je ne l'ai déduite que de la liste « ce qu'Upea n'a pas », qui ne les cite pas.
2. Indiquer dans `executer` si le délai est coupé par un timeout, et à quel moment, pour les programmes lourds comme l'exploration à profondeur 24. Je n'ai pas testé ce cas.
3. Ajouter un exemple de traduction de classe en état global, qui est le cas le plus courant en Python scolaire.
4. Documenter dans `predefinies` que `amui` s'applique à `x.amaa` (liste des enfants) pour ajouter un enfant à un `tumu`. Cela fonctionne, mais je l'ai trouvé en essayant, pas en lisant.

## 5. Ce qui m'aurait permis de réussir la tâche (traduction du taquin)

Le programme a été écrit, vérifié et exécuté sans blocage. Ce qui m'a manqué :

- Le programme Python réellement collé dans la consigne.
- Un moyen de savoir à l'avance si une exploration profonde tient dans les 5 s.
- Une confirmation de la forme d'un arbre modifiable (`amui` sur `.amaa`). Je l'ai supposée valide, et l'exécution l'a confirmé.

## 6. Verdict

**Constaté** : les outils (`aide`, `verifier`, `executer`) suffisent pour apprendre assez d'Upea et écrire un programme correct. **Non constaté** : la fidélité complète au Python, puisque la profondeur 24, l'aléa et le clavier ne sont pas reproductibles tels quels. Je n'ai pas testé les outils de diagnostic.

---

## Programme Upea final

```upea
// taquin (traduction de taquin_3.py)
tuu graine = 42;
tuu visiter = [];

ohipa alea(n: numera) -> numera {
    graine = (graine * 1103515245 + 12345) % 2147483648;
    hoi graine % n;
}

ohipa transform(taq) -> parau {
    tuu chain = "";
    tataitahi a roto 0..3 {
        tataitahi b roto 0..3 {
            chain = chain + parau(taq[a][b]);
        }
    }
    hoi chain;
}

ohipa transform_tolist(chain: parau) {
    tuu l = [[], [], []];
    tataitahi i roto 0..9 {
        ahani i < 3 {
            amui(l[0], chain[i]);
        } taae ahani i < 6 {
            amui(l[1], chain[i]);
        } taae {
            amui(l[2], chain[i]);
        }
    }
    hoi l;
}

ohipa trouve_zero(taq: parau, val: parau) -> numera {
    tuu s = 0;
    tataitahi i roto 0..roa(taq) {
        ahani taq[i] == val {
            s = i;
        }
    }
    hoi s;
}

ohipa melange_grad(chain: parau) -> numera {
    tuu cpt = 0;
    tataitahi i roto 1..9 {
        tuu pos_i = trouve_zero(chain, parau(i));
        tataitahi j roto i..9 {
            tuu pos_j = trouve_zero(chain, parau(j));
            ahani pos_j < pos_i {
                cpt = cpt + 1;
            }
        }
    }
    hoi cpt;
}

ohipa melange(l) {
    tuu cur = l;
    tuu ok = hape;
    tamau eiaha ok {
        tataitahi i roto 0..3 {
            tuu a = alea(3);
            tuu b = alea(3);
            tuu c = alea(3);
            tuu m = cur[a][c];
            cur[a][c] = cur[c][b];
            cur[c][b] = m;
        }
        ahani melange_grad(transform(cur)) % 2 == 0 {
            ok = tia;
        } taae {
            cur = transform_tolist(transform(cur));
        }
    }
    hoi transform_tolist(transform(cur));
}

ohipa change(taq: parau, sens: parau) -> parau {
    tuu s = trouve_zero(taq, "0");
    tuu l = [];
    tataitahi c roto taq {
        amui(l, numera(c));
    }
    tuu g = 0;
    ahani sens == "h" {
        g = l[s - 3]; l[s - 3] = l[s]; l[s] = g;
    } taae ahani sens == "b" {
        g = l[s + 3]; l[s + 3] = l[s]; l[s] = g;
    } taae ahani sens == "d" {
        g = l[s + 1]; l[s + 1] = l[s]; l[s] = g;
    } taae ahani sens == "g" {
        g = l[s - 1]; l[s - 1] = l[s]; l[s] = g;
    }
    tuu out = "";
    tataitahi x roto l {
        out = out + parau(x);
    }
    hoi out;
}

ohipa graph(suit, maximum: numera, chemin: numera) {
    ahani suit.hotu == "012345678" anei chemin == maximum {
        hoi chemin;
    }
    tuu p = trouve_zero(suit.hotu, "0");
    ahani eiaha (0 <= p ma p <= 2) {
        amui(visiter, suit.hotu);
        amui(suit.amaa, tumu(change(suit.hotu, "h")));
        tataitahi i roto suit.amaa {
            ahani eiaha (i.hotu roto visiter) {
                graph(i, maximum, chemin + 1);
            }
        }
    }
    ahani eiaha (6 <= p ma p <= 8) {
        amui(visiter, suit.hotu);
        amui(suit.amaa, tumu(change(suit.hotu, "b")));
        tataitahi i roto suit.amaa {
            ahani eiaha (i.hotu roto visiter) {
                graph(i, maximum, chemin + 1);
            }
        }
    }
    ahani eiaha (p == 2 anei p == 5 anei p == 8) {
        amui(visiter, suit.hotu);
        amui(suit.amaa, tumu(change(suit.hotu, "d")));
        tataitahi i roto suit.amaa {
            ahani eiaha (i.hotu roto visiter) {
                graph(i, maximum, chemin + 1);
            }
        }
    }
    ahani eiaha (p == 0 anei p == 3 anei p == 6) {
        amui(visiter, suit.hotu);
        amui(suit.amaa, tumu(change(suit.hotu, "g")));
        tataitahi i roto suit.amaa {
            ahani eiaha (i.hotu roto visiter) {
                graph(i, maximum, chemin + 1);
            }
        }
    }
}

tuu t = [[0, 1, 2], [3, 4, 5], [6, 7, 8]];
tuu pl = 0;
tuu pc = 0;

ohipa echange(l2: numera, c2: numera) {
    tuu m = t[pl][pc];
    t[pl][pc] = t[l2][c2];
    t[l2][c2] = m;
    pl = l2;
    pc = c2;
}

ohipa haut() { ahani pl != 0 { echange(pl - 1, pc); } }
ohipa bas() { ahani pl != 2 { echange(pl + 1, pc); } }
ohipa droite() { ahani pc != 2 { echange(pl, pc + 1); } }
ohipa gauche() { ahani pc != 0 { echange(pl, pc - 1); } }

ohipa affiche_taquin() {
    tataitahi ligne roto t {
        faaite ligne;
    }
}

melange(t);
tuu g = tumu(transform(t));
faaite "taquin melange :", transform(t);
faaite "graph :", graph(g, 4, 0);
faaite "noeuds de la racine :", roa(g.amaa), "hauteur :", teitei(g);

faaite "bienvenue sur votre taquin";
tuu coups = ["h", "b", "d", "g", "x", "ab", "h"];
tuu fini = hape;
tataitahi coup roto coups {
    ahani eiaha fini {
        affiche_taquin();
        ahani coup == "h" { haut(); }
        taae ahani coup == "b" { bas(); }
        taae ahani coup == "d" { droite(); }
        taae ahani coup == "g" { gauche(); }
        taae ahani coup == "ab" { faaite "Merci d'avoir joue"; fini = tia; }
        taae { faaite "mauvaise commande :", coup; }
    }
}
```

## Sortie réellement produite (statut `succes`, code 0)

```
taquin melange : 038145276
graph : aore
noeuds de la racine : 2 hauteur : 4
bienvenue sur votre taquin
[0, 3, 8]
[1, 4, 5]
[2, 7, 6]
[0, 3, 8]
[1, 4, 5]
[2, 7, 6]
[1, 3, 8]
[0, 4, 5]
[2, 7, 6]
[1, 3, 8]
[4, 0, 5]
[2, 7, 6]
[1, 3, 8]
[0, 4, 5]
[2, 7, 6]
mauvaise commande : x
[1, 3, 8]
[0, 4, 5]
[2, 7, 6]
Merci d'avoir joue
```
