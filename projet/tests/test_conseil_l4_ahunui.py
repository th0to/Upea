"""Conseil, lot L4 : `ahunui` n'est pas un nom de type (un tas max a le type `ahu`),
et le message le dit."""

import pytest

from outils import lancer, position, une_erreur
from upea.erreurs import ErreurSyntaxe

MESSAGE = "type attendu, trouvé 'ahunui' : écrivez 'ahu' : un ahunui a le type ahu"


@pytest.mark.parametrize(
    ("source", "colonne"),
    [
        ("tuu z: ahunui = ahunui [1];", 8),
        ("ohipa f(h: ahunui) { hoi; }", 12),
        ("ohipa f(h) -> ahunui { hoi h; }", 15),
        ("tuu l: tapura[ahunui] = [];", 15),
    ],
)
def test_ahunui_en_annotation(source: str, colonne: int) -> None:
    erreur = une_erreur(source)
    assert isinstance(erreur, ErreurSyntaxe)
    assert erreur.message == MESSAGE
    assert position(erreur) == (1, colonne)


def test_un_tas_max_s_annote_ahu() -> None:
    assert lancer("tuu h: ahu = ahunui [3, 1, 2];\nfaaite iriti(h);") == "3\n"
