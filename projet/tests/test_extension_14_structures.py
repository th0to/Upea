"""Extension 14 : les arbres ordonnés natifs — ABR (imi), AVL (aifaito),
rouge-noir (uteere), arbre B (pupu) et tas (ahu, ahunui)."""

import random
from collections.abc import Callable
from itertools import pairwise
from typing import Any

import pytest

from outils import lancer, position, une_erreur
from upea.compilateur import compiler, mettre_en_forme, transpiler
from upea.erreurs import ErreurExecution, ErreurSemantique, ErreurType
from upea.execution.arbre_b import _NoeudB, _Pupu
from upea.execution.recherche import (
    _Aifaito,
    _ArbreBinaire,
    _Imi,
    _NoeudBinaire,
    _Uteere,
)
from upea.execution.tas import _Ahu
from upea.lexer import tokenize
from upea.noeuds import Collection, Entier, Texte
from upea.parser import parse_expression
from upea.tokens import TokenKind as T

# --- Les invariants de chaque structure -----------------------------------------------


def croissant(cles: list[Any]) -> bool:
    return all(a < b for a, b in pairwise(cles))


def hauteur_avl(noeud: _NoeudBinaire | None) -> int:
    """La hauteur, après avoir vérifié l'équilibre AVL et la hauteur notée."""
    if noeud is None:
        return 0
    gauche, droite = hauteur_avl(noeud.gauche), hauteur_avl(noeud.droite)
    assert abs(gauche - droite) <= 1, f"déséquilibre en {noeud.cle}"
    assert noeud.hauteur == 1 + max(gauche, droite)
    return noeud.hauteur


def hauteur_noire(noeud: _NoeudBinaire | None) -> int:
    """La hauteur noire, après avoir vérifié les invariants rouge-noir (penché à
    gauche : un lien rouge n'est jamais à droite, jamais deux rouges de suite)."""
    if noeud is None:
        return 1
    assert not (noeud.droite is not None and noeud.droite.rouge), "rouge à droite"
    if noeud.rouge and noeud.gauche is not None:
        assert not noeud.gauche.rouge, f"deux rouges de suite en {noeud.cle}"
    gauche, droite = hauteur_noire(noeud.gauche), hauteur_noire(noeud.droite)
    assert gauche == droite, f"hauteurs noires différentes en {noeud.cle}"
    return gauche + (0 if noeud.rouge else 1)


def verifier_arbre_b(arbre: _Pupu) -> None:
    profondeurs: set[int] = set()

    def visiter(noeud: _NoeudB, profondeur: int, racine: bool) -> None:
        assert len(noeud.cles) <= arbre.ordre - 1
        if not racine:
            assert len(noeud.cles) >= arbre.minimum
        assert croissant(noeud.cles)
        if noeud.feuille:
            profondeurs.add(profondeur)
            return
        assert len(noeud.fils) == len(noeud.cles) + 1
        for fils in noeud.fils:
            visiter(fils, profondeur + 1, False)

    visiter(arbre.racine, 0, True)
    assert len(profondeurs) <= 1, "les feuilles ne sont pas au même niveau"


def verifier(structure: Any) -> None:
    """Vérifie l'invariant propre à `structure`."""
    if isinstance(structure, _ArbreBinaire):
        assert croissant(list(structure))
        assert structure.taille == len(list(structure))
    if isinstance(structure, _Aifaito):
        hauteur_avl(structure.racine)
    if isinstance(structure, _Uteere):
        assert structure.racine is None or not structure.racine.rouge
        hauteur_noire(structure.racine)
    if isinstance(structure, _Pupu):
        verifier_arbre_b(structure)
        assert croissant(list(structure))


FABRIQUES: dict[str, Callable[[], Any]] = {
    "imi": _Imi,
    "aifaito": _Aifaito,
    "uteere": _Uteere,
    "pupu 3": lambda: _Pupu(ordre=3),
    "pupu 4": lambda: _Pupu(ordre=4),
    "pupu 5": lambda: _Pupu(ordre=5),
}


@pytest.mark.parametrize("sorte", FABRIQUES)
@pytest.mark.parametrize("graine", range(6))
def test_les_invariants_tiennent_apres_des_ajouts_et_retraits_aleatoires(
    sorte: str, graine: int
) -> None:
    hasard = random.Random(graine)
    structure = FABRIQUES[sorte]()
    modele: set[int] = set()
    for _ in range(400):
        cle = hasard.randrange(120)
        if hasard.random() < 0.6:
            assert structure.ajouter(cle) == (cle not in modele)
            modele.add(cle)
        else:
            assert structure.retirer(cle) == (cle in modele)
            modele.discard(cle)
        verifier(structure)
    assert list(structure) == sorted(modele)
    for cle in range(120):
        assert (cle in structure) == (cle in modele)


@pytest.mark.parametrize("sorte", ["aifaito", "uteere", "pupu 3"])
def test_les_arbres_equilibres_restent_bas(sorte: str) -> None:
    structure = FABRIQUES[sorte]()
    for cle in range(1, 1024):  # l'ordre croissant : le pire cas d'un ABR
        structure.ajouter(cle)
    from upea.execution.algorithmes_arbres import _teitei

    assert _teitei(structure) <= 2 * 10


def test_un_abr_rempli_dans_l_ordre_ne_sature_pas_la_pile() -> None:
    from upea.execution.algorithmes_arbres import _teitei
    from upea.execution.dessins import _hohoa

    arbre = _Imi(range(3000))
    assert _teitei(arbre) == 2999
    assert _hohoa(arbre).count("\n") == 2 * 2999  # chaque nœud : lui et un `·`
    assert arbre.retirer(0) and arbre.min() == 1


@pytest.mark.parametrize("nui", [False, True])
@pytest.mark.parametrize("graine", range(4))
def test_le_tas_rend_les_cles_dans_l_ordre_de_priorite(nui: bool, graine: int) -> None:
    hasard = random.Random(graine)
    tas = _Ahu(nui=nui)
    modele: list[int] = []
    for _ in range(300):
        if modele and hasard.random() < 0.3:
            attendu = max(modele) if nui else min(modele)
            assert tas.iriti() == attendu
            modele.remove(attendu)
        else:
            cle = hasard.randrange(50)  # des doublons, que le tas garde
            tas.ajouter(cle)
            modele.append(cle)
        for i in range(1, len(tas.valeurs)):
            parent = tas.valeurs[(i - 1) // 2]
            assert (parent >= tas.valeurs[i]) if nui else (parent <= tas.valeurs[i])
    assert list(tas) == sorted(modele, reverse=nui)


# --- Dans le langage ------------------------------------------------------------------


@pytest.mark.parametrize("mot", ["imi", "aifaito", "uteere", "pupu", "ahu", "ahunui"])
def test_chaque_sorte_est_un_mot_cle(mot: str) -> None:
    assert next(tokenize(mot)).kind is T[mot.upper()]


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("aifaito [1, 2]", Collection("aifaito", (Entier(1), Entier(2)))),
        ("imi []", Collection("imi", ())),
        ('ahunui ["a"]', Collection("ahunui", (Texte("a"),))),
        ("pupu [1]", Collection("pupu", (Entier(1),))),
        ("pupu 4 [1]", Collection("pupu", (Entier(1),), 4)),
    ],
)
def test_un_litteral_d_arbre_donne_le_bon_noeud(source: str, arbre: Collection) -> None:
    assert parse_expression(source) == arbre


def test_un_litteral_d_arbre_sans_crochet_est_refuse() -> None:
    from upea.erreurs import ErreurSyntaxe

    with pytest.raises(ErreurSyntaxe, match="'\\[' attendu après 'pupu'"):
        parse_expression("pupu 4 1")


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        ("faaite parau(aifaito [3, 1, 2, 1]);", "aifaito [1, 2, 3]"),
        (
            "faaite imi [], uteere [2, 1], pupu 4 [5, 4];",
            "imi [] uteere [1, 2] pupu 4 [4, 5]",
        ),
        ("faaite ahu [3, 1, 3], ahunui [1, 3];", "ahu [1, 3, 3] ahunui [3, 1]"),
        ('faaite [imi ["b", "a"]];', '[imi ["a", "b"]]'),
        (
            "tuu a = aifaito [1];\n"
            "faaite amui(a, 2), a, tatara(a, 1), tatara(a, 9), a;",
            "aore aifaito [2] tia hape aifaito [2]",
        ),  # fmt: skip
        (
            "tuu t = ahu [5, 2];\nfaaite iriti(t), roa(t), iti(t), rahi(ahu [4, 9]);",
            "2 1 5 9",
        ),
        (
            "faaite 2 roto pupu [1, 2], 3 roto imi [1], roa(uteere [1, 1, 2]);",
            "tia hape 2",
        ),
        (
            "tuu l = [3, 1, 2];\nfaaite tatara(l, 1), l, iti(l), rahi(l);",
            "tia [3, 2] 2 3",
        ),
        (
            "tuu g = upea { 1 -> 2, 2 -> 3 };\nfaaite tatara(g, 2), g;",
            "tia upea { 1, 3 }",
        ),
        ("faaite hohoa(uteere [1, 2]);", "  2 (N)\n┌─┘\n1 (R)"),
        ("faaite hohoa(pupu 4 [1, 2, 3, 4]);", "[3]\n├── [1 | 2]\n└── [4]"),
        ("faaite hohoa(imi []), teitei(imi []);", "(vide) -1"),
    ],
)
def test_les_arbres_ordonnes_dans_un_programme(source: str, sortie: str) -> None:
    assert lancer(source) == sortie + "\n"
    assert lancer(source, "ast") == sortie + "\n"


def test_la_variable_d_une_boucle_suit_l_ordre_trie_ou_l_ordre_choisi() -> None:
    source = (
        "tuu a = aifaito [4, 2, 6, 1, 3, 5, 7];\ntuu t = [];\ntuu p = [];\n"
        "tataitahi x roto a { amui(t, x); }\n"
        "tataitahi x roto a aano { amui(p, x); }\nfaaite t, p;"
    )
    assert lancer(source) == "[1, 2, 3, 4, 5, 6, 7] [4, 2, 6, 1, 3, 5, 7]\n"


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("faaite iriti(ahu []);", "iriti : le ahu est vide"),
        ("faaite iti(aifaito []);", "iti : le aifaito est vide"),
        ('tuu a = aifaito [1];\namui(a, "x");', "clés incomparables dans un aifaito"),
        ("tuu a = imi [];\namui(a, [1]);", "une clé de imi doit être un numera"),
        ("faaite iriti([1]);", "iriti : arbre ordonné attendu, tapura reçu"),
        (
            "faaite amui(tumu(1), 2);",
            "amui : tapura, upea ou arbre ordonné attendu, tumu reçu",
        ),
        (
            "tataitahi x roto aifaito [1] mai 1 { }",
            "'mai' ne s'emploie qu'avec un upea",
        ),
    ],
)
def test_les_erreurs_d_execution_des_arbres_ordonnes(
    source: str, fragment: str
) -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(source, types=False)
    assert fragment in info.value.message


@pytest.mark.parametrize(
    ("source", "fragment", "ligne", "colonne"),
    [
        ("faaite aifaito [[1]];", "une clé de aifaito doit être un numera", 1, 17),
        ('faaite imi [1, "a"];', "clés incomparables dans un imi", 1, 8),
        ('tuu a: aifaito[numera] = aifaito [];\namui(a, "x");', "élément numera", 2, 9),
        ("faaite iriti([1]);", "iriti : arbre ordonné", 1, 14),
        ("tuu a = imi [1];\ntuu b: parau = iriti(a);", "'b' est déclaré parau", 2, 16),
        (
            "tataitahi x roto uteere [1] { tuu y: parau = x; }",
            "'y' est déclaré parau",
            1,
            46,
        ),
    ],
)
def test_les_erreurs_de_type_des_arbres_ordonnes(
    source: str, fragment: str, ligne: int, colonne: int
) -> None:
    erreur = une_erreur(source)
    assert isinstance(erreur, ErreurType)
    assert fragment in erreur.message
    assert position(erreur) == (ligne, colonne)


def test_l_ordre_d_un_arbre_b_est_au_moins_3() -> None:
    erreur = une_erreur("faaite pupu 2 [1];")
    assert isinstance(erreur, ErreurSemantique)
    assert "au moins 3" in erreur.message
    assert position(erreur) == (1, 8)


def test_les_annotations_des_arbres_ordonnes() -> None:
    compiler('tuu a: aifaito[numera] = aifaito [1];\ntuu h: ahu[parau] = ahunui ["a"];')
    code = transpiler("ohipa f(a: uteere, b: pupu[numera]) -> ahu { hoi ahu []; }").code
    assert "def f(a: _Uteere, b: _Pupu) -> _Ahu:" in code


def test_la_traduction_des_litteraux() -> None:
    code = transpiler("faaite aifaito [1, 2], pupu 4 [3], pupu [3];").code
    assert "_affiche(_aifaito([1, 2]), _pupu([3], 4), _pupu([3]))" in code


@pytest.mark.parametrize(
    ("source", "formate"),
    [
        ("faaite  aifaito[ 1,2 ];", "faaite aifaito [1, 2];"),
        ("faaite pupu  5[];", "faaite pupu 5 [];"),
        ('tuu h: ahu[parau]=ahunui["a"];', 'tuu h: ahu[parau] = ahunui ["a"];'),
    ],
)
def test_le_formateur_ecrit_les_litteraux_d_arbres(source: str, formate: str) -> None:
    assert mettre_en_forme(source) == formate + "\n"
