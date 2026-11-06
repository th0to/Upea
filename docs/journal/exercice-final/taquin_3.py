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