# L'exercice final du projet MCP

Le dernier exercice du parcours MCP du cours : brancher le serveur sur une IA qui ne
connaît pas le langage, lui faire traduire un vrai programme, et regarder ce qui
l'arrête. Il se fait en plusieurs sessions, séparées par un travail de correction.

| Session | Date | Serveur | Appels | Issue |
|---|---|---|---|---|
| [1](session-1-rapport.md) | 6 novembre 2026 | 6 outils (le pont ne transmettait que les outils) | 5 | échec : aucune référence du langage, programme non traduit |
| [2a](session-2a-rapport.md) | 6 novembre 2026 | 6 outils (serveur lancé avant les lots A0 à E, qui gardait l'ancien code chargé) | 17, dont une quinzaine pour deviner les mots-clés | traduction partielle et approchée ([programme](taquin.upea)) ; le « sinon » n'a jamais été trouvé |
| [2b](session-2b-rapport.md) | 6 novembre 2026 | 8 outils (serveur redémarré) | 6, dont le chargement des schémas (5 au serveur : `aide` trois fois, `verifier`, `executer`) | programme traduit ; `verifier` l'accepte du premier coup ; `executer` : succès, 324 octets de sortie |

Entre la session 1 et la session 2, les lots A0, C, A, B, D et E (voir plus bas). La
session 2b a reçu un texte où le marqueur du programme Python n'était pas encore
remplacé : l'IA l'a dit, et a traduit le fichier `taquin_3.py` joint à la demande. Le
texte ci-dessous contient maintenant ce programme.

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
même pont : c'est ce qui rend la comparaison honnête. Le programme Python est celui de
la session 1 (`taquin_3.py`), collé tel quel. Noter avant de lancer : la date, et le
commit du dépôt (`git rev-parse --short HEAD`). **Après une mise à jour du serveur,
quitter complètement le client et le relancer** : un serveur garde le code chargé à son
démarrage (voir le [dépannage](../../mcp.md#8-dépannage)).

````text
Tu découvres un langage de programmation, Upea, à travers un serveur MCP nommé « upea »
dont tu disposes des outils. Tu n'as aucune documentation du langage, et tu n'en
demandes pas à l'utilisateur : tout ce que tu apprends, tu l'apprends des outils du
serveur.

Ta tâche : traduire en Upea le programme Python ci-dessous (un taquin), l'exécuter avec
le serveur, puis me donner le programme Upea final et la sortie qu'il a réellement
produite.

```python
#taquin
from random import randint
import sys

class taquin:
    def __init__(self) :
        """
        Cette méthode viens initialisé le taquin afin qu'il puisse être utilisé dans le reste du programme.
        -------
        self.t : le taqui originale que le joueur va devoir reconstitué pour gagné
        self.p : la position du 0

        """
        self.t = [[0,1,2],[3,4,5],[6,7,8]]
        self.p = (0,0)
        self.g = Arbre(transform(melange(self.t)))
        self.est_visite = []


    def graph(self, suit, maximum = 24, chemin = 0, visiter = []) :
        """
        Cette méthode va mettre a jour le graph du taquin en lui ajoutant une feuille suplémentère (un enfant: une liste d'objet de classe Arbre) a chque fois que c'est possible.
        Cette méthode est sensé faire de nombreux appel récurssif (selon le maximum qui vous mettez vous pouvez attendre quelques minutes, voirs dixène de minutes).

        Parameters
        ----------
        suit : Objet de classe Arbre
            noeud.
        maximum : INT, optional
            24 est sa valeur par défaut car en théori on npeur résoudre n'importe quel taquin en moins de 24 coups
        chemin : INT, optional
            Hauteur du graph. The default is 0.
        visiter : LIST, optional
            Liste du chemin parcouru de chaque branches du graph (avant c'était une liste commune ce qui faisiat planter). The default is [] (vide).

        Returns
        -------
        chemin : INT
            Hauteur du graph.

        """
        if suit.v == '012345678' or chemin == maximum: #en suppriment le "or chemin == maximum" cette méthodes va essayé faire le graphe jusqu'a la solution (mais ne fonctionne pas car trop de récurtion)
            return (chemin)

        p = trouve_zero(suit, '0')
        if not 0<=p<=2 :
            visiter.append(suit.v)
            suit.add(change(suit.v,'h'))
            for i in suit.enfant :
                if not i.v in visiter :
                    self.graph(i, maximum, chemin+1, visiter)

        if not 6<=p<=8 :
            visiter.append(suit.v)
            suit.add(change(suit.v,'b'))
            for i in suit.enfant :
                if not i.v in visiter :
                    self.graph(i, maximum, chemin+1, visiter)

        if not p in (2,5,8) :
            visiter.append(suit.v)
            suit.add(change(suit.v,'d'))
            for i in suit.enfant :
                if not i.v in visiter :
                    self.graph(i, maximum, chemin+1, visiter)

        if not p in (0,3,6) :
            visiter.append(suit.v)
            suit.add(change(suit.v,'g'))
            for i in suit.enfant :
                if not i.v in visiter :
                    self.graph(i, maximum, chemin+1, visiter)

    def hauteur(self, T, cpt = 0):
        """
        Cette méthodes essaye de calculer la profondeur de la solution

        Parameters
        ----------
        T : Object de classe arbre (noeud)

        cpt : INT, optional
            compte la pronfeur. The default is 0.

        Returns
        -------
        cpt : INT
            Profondeur.

        """
        if T != None:
            for i in T.enfant :
                if i.v == "012345678" :
                    return cpt
                self.hauteur(i, cpt+1)

    def etat(self) :
        """
        cette méthode va simplement faire un sauvegarde du taquin et de la position du 0

        """
        self.tSave = self.t
        self.pSave = self.p


    def haut(self) :
        """
        Cette méthode permet de déplacé le 0 du taquin vers la case du haut

        """
        if not self.p[0] == 0 :
            m = self.t[self.p[0]][self.p[1]]
            self.t[self.p[0]][self.p[1]] = self.t[self.p[0]-1][self.p[1]]
            self.t[self.p[0]-1][self.p[1]] = m
            self.p = (self.p[0]-1, self.p[1])
            return (self.t)

    def bas(self) :
        """
        Cette méthode permet de déplacé le 0 du taquin vers la case du bas

        """
        if not self.p[0] == 2 :
            m = self.t[self.p[0]][self.p[1]]
            self.t[self.p[0]][self.p[1]] = self.t[self.p[0]+1][self.p[1]]
            self.t[self.p[0]+1][self.p[1]] = m
            self.p = (self.p[0]+1, self.p[1])
            return (self.t)

    def droite(self) :
        """
        Cette méthode permet de déplacé le 0 du taquin vers la case de droite

        """
        if not self.p[1] == 2 :
            m = self.t[self.p[0]][self.p[1]]
            self.t[self.p[0]][self.p[1]] = self.t[self.p[0]][self.p[1]+1]
            self.t[self.p[0]][self.p[1]+1] = m
            self.p = (self.p[0], self.p[1]+1)
            return (self.t)

    def gauche(self) :
        """
        Cette méthode permet de déplacé le 0 du taquin vers la case de gauche

        """
        if not self.p[1] == 0 :
            m = self.t[self.p[0]][self.p[1]]
            self.t[self.p[0]][self.p[1]] = self.t[self.p[0]][self.p[1]-1]
            self.t[self.p[0]][self.p[1]-1] = m
            self.p = (self.p[0], self.p[1]-1)
            return (self.t)

    def __str__(self) :
        affiche = ""
        for i in range(0,len(self.t)) :
            affiche += str(self.t[i]) + "\n"
        return(affiche)

def melange(l) :
    """
    Cette fonction va mélangé le taquin afin qu'il y est un intéré a jouer.

    Parameters
    -------
    l : un liste de liste

    Returns
    -------
    La fonction renvoie un taquin en liste de liste mélanger qui et transdormer en chaine de charactères pour tester si le mélange est résolvable


    """
    for i in range(0,len(l)) :
        a = randint(0,2)
        b = randint(0,2)
        c = randint(0,2)
        m = l[a][c]
        l[a][c] = l[c][b]
        l[c][b] = m

    return melangeGrad(transform(l))

def melangeGrad(chain):
    """
    Cette fonction permet de savoir si un melange de taqui est résolvable

    Parameters
    ----------
    chain : STR
        taquin en chaine de charactère

    Returns
    -------
    Si le mélange est résovbles, alors la fonction renvoie le taquin en liste de liste
    Sinon il remélange le taquin

    """
    cpt = 0
    for i in range(9):
        pos_i = trouve_zero(chain, str(i), 1)
        if i != 0:
            for j in range(i,9):
                pos_j = trouve_zero(chain, str(j), 1)
                if pos_j < pos_i: # si i+1 se trouve avant i dans le taquin on ajoute 1 point au
                    cpt += 1
    if cpt%2==0 :
        return transform_tolist(chain)
    else :
        return melange(transform_tolist(chain))

def transform(taq):
    """
    Cette fonction transforme un taquin en liste de liste en un taquin en chaine de charactère

    Parameters
    ----------
    taq : list
        liste de liste (3x3 en 2D)

    Returns
    -------
    chain : STR
        chaine de charactère (de longueur 9)

    """
    chain = ''
    for a in range(0,3):
        for b in range(0,3):
            chain += str(taq[a][b])
    return chain

def transform_tolist(chain) :
    """
    Cette fonction transforme un taquin en chaine de charactère en un taquin en liste de liste

    Parameters
    ----------
    chain : STR
        chaine de charactère (de longueur 9)

    Returns
    -------
    taq : list
        liste de liste (3x3 en 2D)

    """
    l = [[],[],[]]
    for i in range(0,9) :
        if i in (0,1,2) :
            l[0].append(chain[i])
        elif i in (3,4,5) :
            l[1].append(chain[i])
        else :
            l[2].append(chain[i])
    return l

def trouve_zero(taq, val, x=None):
    """
    Cette fonction trouvr le rang du nombre demander

    Parameters
    ----------
    taq : STR
        taquin en chain de charactère

    val : STR

    Returns
    -------
    None.

    """
    s = 0
    if x == None :
        for i in range(0,len(taq.v)):
            if taq.v[i] == val :
                s = int(i)
        return(s)
    else :
        for i in range(0,len(taq)):
            if taq[i] == val :
                s = int(i)
        return(s)

def change(taq,sens,s=None) :
    """
    Cette fonction va modifie la taquin en chain de charactère (en déplacer uniquement le 0) dans le sens voulu
    la fonction fait un primère appel pour trouver le 0 puis modifie le taquin.

    Parameters
    ----------
    taq : STR
        taquin en chain de charactère

    sens : STR
        une simple lettre qui indique de quel coté on veut déplacer le 0 ('d'/'g'/'h'/'b')

    s : INT, optional
        localisation du 0 dans la chain de charactère. The default is None.

    Returns
    -------
    STR
        le taqui modifié.

    """
    if s==None :
        for i in range(0,len(taq)):
            if taq[i]=='0' :
                s = int(i)
                return change(taq,sens,s)
    else :
        l = []
        for i in taq :
            l.append(int(i))
        if sens == 'h' :
            g = l[s-3]
            l[s-3] = l[s]
            l[s] = g
        elif sens == 'b' :
            g = l[s+3]
            l[s+3] = l[s]
            l[s] = g
        elif sens == 'd' :
            g = l[s+1]
            l[s+1] = l[s]
            l[s] = g
        elif sens == 'g' :
            g = l[s-1]
            l[s-1] = l[s]
            l[s] = g

        out = ''
        for i in l:
            out += str(i)
        return out


def search_prof(G,s,but): #je n'ai pas fait la recherche en profondeur étant donnais qu'il n'y a jamais eu la solution dans le graphe donc je n'ai pas peu avoir sa profondeur pour trouver le meilleur chemin
    pass

class Arbre:
    def __init__(self, valeur):
        self.v: str = valeur
        self.enfant = []

    def add(self, add):
        self.enfant.append(Arbre(add))

    def get_valeur(self):
        return self.v

    def get_enfant(self):
        return self.enfant

def affiche(T)  :
    if T != None:
      return (T.get_valeur(),affiche(T.get_enfant()))

def main() :
    melange(j.t)
    print("bienvenue sur votre taquin"+"\n"+"voicie le  taquin que vous devrez résoudre :"+"\n")
    jeu()

def jeu() :
    while j.t != [[0,1,2],[3,4,5],[6,7,8]] :
        print(j)
        print("\n")
        coup = input("que voulez vous jouez ? (h / b / d / g, ab pour abandonné, l'aide est encore en développement ;) : ")
        if coup == "haut" or coup == "h" or coup == "H" or coup == "HAUT" :
            j.haut()
        elif coup in ("bas", "b", "BAS", "B") :
            j.bas()
        elif coup in ("droite", "d", "DROITE", "D") :
            j.droite()
        elif coup in ("gauche", "g", "GAUCHE", "G") :
            j.gauche()
        elif coup in ('abandon', 'ab') :
            return(print("Merci d'avoir joué "))
        else :
            coup = input("désolé mais vous avez rentrez une mauvaise commande veuillez rééssayer :)")
    print(j)
    return print("bravo vous avez gagnez !!!")

sys.setrecursionlimit(2147483647) #fixe le nombre de récurtion très haut si besoin
j = taquin()
print(j.graph(j.g))
#main()
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
