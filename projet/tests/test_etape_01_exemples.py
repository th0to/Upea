"""Étape 1 : la spécification et les programmes d'exemple."""

from pathlib import Path

from outils import EXEMPLES, LISTE_EXEMPLES, PROJET, lancer
from upea.lexer import tokenize
from upea.tokens import MOTS_CLES, TokenKind


def test_il_y_a_au_moins_cinq_exemples() -> None:
    assert len(LISTE_EXEMPLES) >= 5


def test_chaque_exemple_a_sa_sortie_attendue(exemple: Path) -> None:
    attendu = exemple.with_suffix(".attendu")
    assert attendu.is_file(), f"{attendu.name} manque"


def test_aucune_sortie_attendue_orpheline() -> None:
    for attendu in EXEMPLES.glob("*.attendu"):
        assert attendu.with_suffix(".upea").is_file(), f"{attendu.name} sans programme"


def test_la_specification_cite_chaque_mot_cle() -> None:
    specification = (PROJET / "specification.md").read_text(encoding="utf-8")
    for mot in MOTS_CLES:
        assert f"`{mot}`" in specification, mot


def test_le_programme_d_ouverture_de_la_specification_s_execute() -> None:
    specification = (PROJET / "specification.md").read_text(encoding="utf-8")
    programme = specification.split("## Un programme pour donner le ton")[1]
    programme = programme.split("```")[1]
    assert lancer(programme).splitlines()[-1] == (
        '["Tahiti", "Huahine", "Raiatea", "Bora Bora"] 280 km'
    )


def test_les_exemples_emploient_ensemble_tous_les_tokens() -> None:
    employes = {
        token.kind
        for chemin in LISTE_EXEMPLES
        for token in tokenize(chemin.read_text(encoding="utf-8"))
    }
    assert set(TokenKind) - employes == set()
