"""Rend importables le paquet `upea` (le dossier parent de `tests/`) et le module
`outils` des tests, et fournit la fixture des programmes d'exemple."""

import os
import sys
from pathlib import Path

import pytest
from hypothesis import settings

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from outils import LISTE_EXEMPLES  # noqa: E402

# Les profils d'`hypothesis` (extension 17), choisis par HYPOTHESIS_PROFILE :
# « defaut » à chaque lancement, « long » pour chercher plus loin. Chaque tirage
# compile et exécute un programme : on ne borne pas la durée d'un seul.
settings.register_profile("defaut", max_examples=30, deadline=None)
settings.register_profile("long", max_examples=1000, deadline=None)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "defaut"))


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
