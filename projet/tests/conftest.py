"""Rend importables le paquet `upea` (le dossier parent de `tests/`) et le module
`outils` des tests, et fournit la fixture des programmes d'exemple."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from outils import LISTE_EXEMPLES  # noqa: E402


@pytest.fixture(autouse=True)
def sans_couleurs(monkeypatch: pytest.MonkeyPatch) -> None:
    """Les couleurs de l'environnement (`FORCE_COLOR`) ne changent pas les sorties."""
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    monkeypatch.delenv("NO_COLOR", raising=False)


@pytest.fixture(params=LISTE_EXEMPLES, ids=lambda p: p.stem)
def exemple(request: pytest.FixtureRequest) -> Path:
    """Chacun des programmes d'exemple, tour à tour."""
    chemin = request.param
    assert isinstance(chemin, Path)
    return chemin
