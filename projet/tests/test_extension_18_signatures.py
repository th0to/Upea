"""Extension 18 : la signature de chaque fonction prédéfinie, calculée à partir de son
typage (pour la ressource `upea://predefinies` du serveur MCP)."""

import re

import pytest

from upea.predefinies import ABREVIATIONS, PREDEFINIES


@pytest.mark.parametrize(
    ("nom", "attendu"),
    [
        ("pihai", "pihai(upea[T], T) -> tapura[T]"),
        ("tarjan", "tarjan(upea[T]) -> tapura[tapura[T]]"),
        ("floyd_warshall", "floyd_warshall(upea[T]) -> upea[T]"),
        ("iriti", "iriti(ordonne[T]) -> T"),
        ("amui", "amui(ajoutable[T], T) -> aore"),
        ("taati", "taati(upea[T], T, T[, numera | tuhaa]) -> aore"),
        ("ea", "ea(upea[T], T, T) -> ?"),
        ("teitei", "teitei(arbre[T]) -> numera"),
        ("hohoa", "hohoa(structure[T]) -> parau"),
        ("numera", "numera(numera | tuhaa | parau | tiahape) -> numera"),
        ("parau", "parau(?) -> parau"),
        ("roa", "roa(tapura[T] | parau | upea[T] | arbre[T]) -> numera"),
        ("tumu", "tumu(T[, tumu[T]...]) -> tumu[T]"),
    ],
)
def test_une_signature(nom: str, attendu: str) -> None:
    assert PREDEFINIES[nom].texte == attendu


def test_chaque_predefinie_a_une_signature_conforme_a_son_arite() -> None:
    for nom, predefinie in PREDEFINIES.items():
        texte = predefinie.texte
        assert texte.startswith(f"{nom}("), nom
        arguments = texte[len(nom) + 1 : texte.index(")")]
        # Les virgules des arguments, hors de ce qui suit un `[` facultatif.
        obligatoires = arguments.split("[,")[0]
        nombre = len(re.findall(r",", obligatoires)) + 1
        assert nombre == predefinie.minimum, nom
        if predefinie.maximum is not None:
            assert arguments.count(",") + 1 == predefinie.maximum, nom


def test_les_abreviations_sont_definies() -> None:
    assert ABREVIATIONS["arbre[T]"] == (
        "tumu[T] | imi[T] | aifaito[T] | uteere[T] | pupu[T] | ahu[T]"
    )
    utilisees = {
        mot
        for predefinie in PREDEFINIES.values()
        for mot in re.findall(r"\b[a-z]+\[T\]", predefinie.texte)
    }
    simples = {"upea[T]", "tapura[T]", "tumu[T]"}
    assert utilisees - simples <= set(ABREVIATIONS)
