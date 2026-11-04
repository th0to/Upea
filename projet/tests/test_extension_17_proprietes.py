"""Extension 17 : des propriétés vérifiées sur des programmes et des valeurs tirés au
hasard par `hypothesis` (les invariants des arbres ordonnés sont dans l'extension 14).

- formater deux fois revient à formater une fois, sans changer le sens ;
- relire `parau(x)` redonne une valeur égale à `x` ;
- les deux backends affichent la même chose, et échouent de la même façon.
"""

import io
from contextlib import redirect_stdout

import pytest
from hypothesis import given, settings

from generateurs import GRAPHES, ORDONNES, PROGRAMMES, TUMU
from outils import lancer
from upea.compilateur import executer, mettre_en_forme
from upea.erreurs import ErreurExecution
from upea.parser import parse

#: Chaque exemple compile et exécute un programme, prélude compris (40 ms, et 120 ms
#: avec le backend ast) : on en tire moins que par défaut, et l'on ne borne pas la
#: durée d'un seul.
REGLAGES = settings(max_examples=30, deadline=None)

# `(3)[0]` (accepté avec --sans-types) fait émettre à CPython un SyntaxWarning en
# compilant le code généré. Ce n'est pas ce que vérifient ces propriétés.
pytestmark = pytest.mark.filterwarnings("ignore::SyntaxWarning")


def resultat(
    source: str, backend: str = "python"
) -> tuple[str, str | None, int | None]:
    """Ce que le programme affiche, puis son erreur d'exécution et sa ligne."""
    tampon = io.StringIO()
    try:
        with redirect_stdout(tampon):
            executer(source, backend, types=False)
    except ErreurExecution as erreur:
        ligne = None if erreur.position is None else erreur.position.ligne
        return tampon.getvalue(), erreur.message, ligne
    return tampon.getvalue(), None, None


# --- Le formateur ---------------------------------------------------------------------


@REGLAGES
@given(PROGRAMMES)
def test_formater_est_idempotent_et_garde_le_sens(source: str) -> None:
    formate = mettre_en_forme(source)
    assert mettre_en_forme(formate) == formate
    assert parse(formate) == parse(source)
    # Le formateur change la mise en page, donc les numéros de ligne.
    assert resultat(formate)[:2] == resultat(source)[:2]


# --- Relire parau ---------------------------------------------------------------------


def relu(litteral: str) -> str:
    """La forme compacte de `litteral`, telle que l'écrit `parau`."""
    sortie = lancer(f"faaite parau({litteral});", types=False)
    assert sortie.endswith("\n") and "\n" not in sortie[:-1]
    return sortie[:-1]


@REGLAGES
@given(GRAPHES)
def test_relire_parau_d_un_graphe_redonne_un_graphe_egal(litteral: str) -> None:
    # L'ordre des successeurs peut changer (spécification) : seule l'égalité compte.
    source = f"tuu x = {litteral};\ntuu y = {relu(litteral)};\nfaaite x == y;"
    assert lancer(source, types=False) == "tia\n"


@REGLAGES
@given(TUMU | ORDONNES)
def test_relire_parau_d_un_arbre_redonne_le_meme_arbre(litteral: str) -> None:
    texte = relu(litteral)
    source = f"tuu x = {litteral};\ntuu y = {texte};\nfaaite x == y;"
    assert lancer(source, types=False) == "tia\n"
    assert relu(texte) == texte


# --- Les deux backends ----------------------------------------------------------------


@REGLAGES
@given(PROGRAMMES)
def test_les_deux_backends_font_la_meme_chose(source: str) -> None:
    assert resultat(source, "ast") == resultat(source, "python")
