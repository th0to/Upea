"""Conseil, lot M5 : dans le REPL, une erreur levée dans une fonction déclarée lors
d'une saisie antérieure est signalée à sa vraie ligne. Chaque saisie a son nom de
fichier (`<upea-1>`, `<upea-2>`…) et sa source map."""

import pytest

from outils import lancer
from upea.erreurs import ErreurExecution
from upea.repl import repl

#: Le programme de COMP-01 : la fonction, puis un bloc de plusieurs lignes qui
#: l'appelle.
INDICE = """\
ohipa f(l) {
    faaite "dans f";
    hoi l[3];
}
ahani tia {
    faaite "x";
    faaite "y";
    faaite f([1]);
}"""

#: La variante du casseur, avec une division.
DIVISION = """\
ohipa div(a, b) {
    faaite "calcul";
    hoi a / b;
}
ahani tia {
    faaite "x";
    faaite "y";
    faaite "z";
    faaite div(1, 0);
}"""


def session(lignes: str) -> str:
    """Envoie les lignes une à une au REPL ; rend tout ce qu'il a répondu."""
    generateur = repl()
    next(generateur)
    return "".join(generateur.send(ligne).sortie for ligne in lignes.splitlines())


def test_une_erreur_dans_une_fonction_d_une_saisie_anterieure() -> None:
    assert session(INDICE) == (
        "x\ny\ndans f\n"
        "<repl>:3 : erreur d'exécution : indice hors limites\n"
        "        hoi l[3];\n"
    )


def test_la_variante_avec_une_division() -> None:
    assert session(DIVISION).endswith(
        "<repl>:3 : erreur d'exécution : division par zéro\n        hoi a / b;\n"
    )


def test_une_erreur_dans_la_saisie_courante() -> None:
    sortie = session('tuu l = [1];\nfaaite "a";\nfaaite l[5];')
    assert sortie == (
        "a\n<repl>:3 : erreur d'exécution : indice hors limites\n    faaite l[5];\n"
    )


def test_apres_une_erreur_les_lignes_restent_justes() -> None:
    """Une saisie en erreur n'est pas retenue : les numéros de la suivante ne la
    comptent pas."""
    sortie = session(INDICE + "\nfaaite 1 / 0;\ntuu m = [];\nfaaite f(m);")
    assert sortie.endswith(
        "<repl>:5 : erreur d'exécution : division par zéro\n"
        "    faaite 1 / 0;\n"
        "dans f\n"
        "<repl>:3 : erreur d'exécution : indice hors limites\n"
        "        hoi l[3];\n"
    )


def test_run_est_inchange() -> None:
    with pytest.raises(ErreurExecution) as info:
        lancer(INDICE + "\n")
    assert info.value.position is not None and info.value.position.ligne == 3
