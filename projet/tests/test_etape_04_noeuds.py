"""Étape 4 : les nœuds de l'arbre syntaxique."""

import dataclasses

import pytest

from upea.erreurs import Position
from upea.noeuds import (
    Appel,
    Arete,
    Binaire,
    Bloc,
    Branche,
    Entier,
    Graphe,
    Retour,
    Si,
    Texte,
    Variable,
    afficher_arbre,
    parcourir,
)
from upea.parser import parse


def test_un_noeud_est_immuable() -> None:
    noeud = Entier(1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        noeud.valeur = 2  # type: ignore[misc]


def test_la_position_ne_compte_pas_dans_l_egalite() -> None:
    a = Binaire(
        "+", Entier(1, Position(1, 1)), Entier(2, Position(1, 5)), Position(1, 3)
    )
    b = Binaire(
        "+", Entier(1, Position(7, 2)), Entier(2, Position(8, 1)), Position(7, 9)
    )
    assert a == b
    assert hash(a) == hash(b)


def test_la_position_n_apparait_pas_dans_le_repr() -> None:
    texte = repr(Variable("x", Position(4, 2)))
    assert texte == "Variable(nom='x')"


def test_un_noeud_construit_a_la_main_est_accepte() -> None:
    noeud = Appel("roa", (Texte("abc"),))
    assert noeud.pos == Position(0, 0)


def test_les_enfants_sont_des_tuples() -> None:
    graphe = Graphe((Arete(Texte("A"), Texte("B"), True),))
    assert isinstance(graphe.aretes, tuple)
    assert hash(graphe) == hash(Graphe((Arete(Texte("A"), Texte("B"), True),)))


def test_afficher_arbre_sur_deux_niveaux() -> None:
    arbre = Si(
        (
            Branche(
                Binaire("<=", Variable("n"), Entier(1)),
                Bloc((Retour(Binaire("*", Variable("n"), Entier(2))),)),
            ),
        )
    )
    assert afficher_arbre(arbre) == (
        "Si\n"
        "└── branches[0]: Branche\n"
        "    ├── condition: Binaire op='<='\n"
        "    │   ├── gauche: Variable nom='n'\n"
        "    │   └── droite: Entier valeur=1\n"
        "    └── corps: Bloc\n"
        "        └── instructions[0]: Retour\n"
        "            └── valeur: Binaire op='*'\n"
        "                ├── gauche: Variable nom='n'\n"
        "                └── droite: Entier valeur=2"
    )


def test_afficher_arbre_d_un_graphe() -> None:
    graphe = Graphe((Arete(Texte("A"), Texte("B"), False, Entier(3)),))
    assert afficher_arbre(graphe) == (
        "Graphe\n"
        "└── aretes[0]: Arete double=False\n"
        "    ├── depart: Texte valeur='A'\n"
        "    ├── arrivee: Texte valeur='B'\n"
        "    └── poids: Entier valeur=3"
    )


def test_asdict_fonctionne_sur_un_noeud() -> None:
    sans = {"ligne": 0, "colonne": 0}
    assert dataclasses.asdict(Binaire("+", Entier(1), Entier(2))) == {
        "op": "+",
        "gauche": {"valeur": 1, "pos": sans},
        "droite": {"valeur": 2, "pos": sans},
        "pos": sans,
    }


def test_parcourir_produit_tous_les_noeuds() -> None:
    programme = parse("faaite roa([1, 2]), roa(motu(upea { 1 -> 2 }));")
    appels = [n for n in parcourir(programme) if isinstance(n, Appel)]
    assert [a.nom for a in appels] == ["roa", "roa", "motu"]
