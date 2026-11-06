"""Conseil, lot L6 : le bac à sable et la CLI face à leur environnement.

- l'enfant du bac à sable se limite en temps CPU : il ne tourne pas sans fin si le
  serveur meurt (TEST-04), et un délai dépassé ne laisse aucun processus derrière lui ;
- une mémoire remplie de petits objets donne « mémoire dépassée » (TEST-05) ;
- une demi-paire de substitution ne casse pas le résultat (TEST-06) ;
- les écritures impossibles, un tube fermé, un dossier passé à `run` (TEST-10).
"""

import json
import os
import stat
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from upea import bac_a_sable
from upea.cli import ERREUR_COMPILATION, OK, main
from upea.compilateur import MEMOIRE_EPUISEE, executer_code
from upea.erreurs import ErreurExecution
from upea.sourcemap import SourceMap

SANS_FIN = "tamau tia { }"

# --- TEST-04 : le temps CPU, et la descendance -------------------------------------


def test_l_enfant_seul_s_arrete_de_lui_meme() -> None:
    """L'enfant lancé sans parent pour le tuer (le serveur est mort) : sa limite de
    temps CPU, deux fois le délai, l'arrête."""
    requete = {
        "source": SANS_FIN,
        "types": True,
        "backend": "python",
        "plafond": bac_a_sable.PLAFOND,
        "memoire": bac_a_sable.PLAFOND_MEMOIRE,
        "delai": 0.5,
        "marqueur": "0" * 32,
    }
    debut = time.monotonic()
    resultat = subprocess.run(
        bac_a_sable.COMMANDE,
        input=json.dumps(requete).encode("utf-8"),
        capture_output=True,
        cwd=bac_a_sable.RACINE,
        env=bac_a_sable._environnement(),
        timeout=60,
    )
    assert time.monotonic() - debut < 30
    assert resultat.returncode != 0
    assert b"0" * 32 not in resultat.stdout


def _processus_windows() -> list[dict[str, object]]:
    sortie = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "Get-CimInstance Win32_Process | "
            "Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json",
        ],
        capture_output=True,
        text=True,
        timeout=60,
    ).stdout
    tous: list[dict[str, object]] = json.loads(sortie)
    return tous


@pytest.mark.skipif(sys.platform != "win32", reason="lanceur du venv : Windows")
def test_apres_un_delai_depasse_aucun_descendant_ne_survit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sous Windows, le `python.exe` d'un venv est un lanceur qui crée l'interpréteur.
    Tuer le lanceur doit arrêter l'interpréteur : Windows garde l'identifiant du
    parent d'un processus orphelin, ce qui permet de le retrouver."""
    lances: list[int] = []

    class Espion(subprocess.Popen[bytes]):
        """Note le PID de chaque processus lancé (ici, le seul enfant)."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            lances.append(self.pid)

    with monkeypatch.context() as m:
        m.setattr(subprocess, "Popen", Espion)
        with pytest.raises(bac_a_sable.DelaiDepasse):
            bac_a_sable.executer(SANS_FIN, delai=0.5)
    time.sleep(0.5)
    tous = _processus_windows()
    (racine,) = lances
    famille, a_voir = [], [racine]
    while a_voir:
        parent = a_voir.pop()
        for p in tous:
            if p["ParentProcessId"] == parent:
                famille.append(p)
                a_voir.append(int(str(p["ProcessId"])))
    vivants = [p for p in tous if p["ProcessId"] == racine] + famille
    for p in vivants:  # le ménage, avant d'échouer
        subprocess.run(["taskkill", "/F", "/PID", str(p["ProcessId"])], check=False)
    assert vivants == []


# --- TEST-05 : la mémoire ----------------------------------------------------------


def test_un_memory_error_libere_l_espace_avant_l_erreur() -> None:
    """Les valeurs du programme ne survivent pas à l'erreur : sans quoi rédiger
    l'erreur, puis le résultat, n'aurait plus de mémoire."""
    code = (
        "import sys, weakref\n"
        "class Lourd: pass\n"
        "lourd = Lourd()\n"
        "sys._upea_temoin = weakref.ref(lourd)\n"
        "raise MemoryError\n"
    )
    with pytest.raises(ErreurExecution) as info:
        executer_code(code, SourceMap(lignes={5: 7}))
    temoin = sys.__dict__.pop("_upea_temoin")
    assert temoin() is None
    assert info.value.message == MEMOIRE_EPUISEE
    assert info.value.position is not None and info.value.position.ligne == 7
    assert info.value.__cause__ is None


@pytest.mark.skipif(
    sys.platform not in ("win32", "linux"), reason="pas de plafond de mémoire ici"
)
def test_une_memoire_remplie_de_petits_objets() -> None:
    """La panne était intermittente (deux fois sur trois à 512 Mo) : trois essais."""
    source = (
        "tuu g = upea {};\ntuu i = 0;\n"
        "tamau tia { taati(g, i, i + 1); i = i + 1; }\n"
    )
    for _ in range(3):
        resultat = bac_a_sable.executer(source, delai=30)
        assert resultat.statut == "erreur_execution", resultat.rapport
        assert resultat.diagnostics[-1].message == (
            "mémoire dépassée : un programme a au plus 512 Mo"
        )


def test_le_parent_traduit_un_enfant_mort_de_memoire(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Dernier recours : l'enfant meurt sans résultat, sur `MemoryError`."""
    monkeypatch.setattr(
        bac_a_sable,
        "COMMANDE",
        [sys.executable, "-c", "import sys; print('a'); raise MemoryError"],
    )
    resultat = bac_a_sable.executer("faaite 1;")
    assert resultat.statut == "erreur_execution"
    assert resultat.code_retour == 3
    assert resultat.diagnostics[-1].message == (
        "mémoire dépassée : un programme a au plus 512 Mo"
    )


# --- TEST-06 : les demi-paires de substitution ------------------------------------


@pytest.mark.parametrize(
    ("source", "statut"),
    [
        ('faaite "a\ud800b";', "erreur_execution"),
        ("faaite 1; \ud800", "erreur_compilation"),
    ],
)
def test_une_demi_paire_rend_un_resultat(source: str, statut: str) -> None:
    resultat = bac_a_sable.executer(source)
    assert resultat.statut == statut


def test_un_resultat_illisible_est_une_panne(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        bac_a_sable,
        "COMMANDE",
        [sys.executable, "-c", "import sys; print(sys.stdin.read()[-34:-2] + '{')"],
    )
    with pytest.raises(bac_a_sable.EnfantEnPanne):
        bac_a_sable.executer("faaite 1;")


# --- TEST-10 : la CLI --------------------------------------------------------------


@pytest.fixture
def programme(tmp_path: Path) -> Path:
    fichier = tmp_path / "programme.upea"
    fichier.write_text("// un commentaire\nfaaite  1 ;\n", encoding="utf-8")
    return fichier


def test_transpile_vers_un_dossier_absent(
    programme: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cible = tmp_path / "absent" / "x.py"
    assert main(["transpile", str(programme), "-o", str(cible)]) == ERREUR_COMPILATION
    erreurs = capsys.readouterr().err
    assert erreurs.startswith(f"upea : impossible d'écrire {cible} (")
    assert "Traceback" not in erreurs


def test_transpile_vers_un_dossier(
    programme: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["transpile", str(programme), "-o", str(tmp_path)]) == (
        ERREUR_COMPILATION
    )
    assert capsys.readouterr().err.startswith("upea : impossible d'écrire ")


def test_le_prelude_externe_impossible_a_ecrire(
    programme: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "upea_prelude.py").mkdir()  # un dossier à la place du prélude
    sortie = tmp_path / "x.py"
    code = main(
        ["transpile", str(programme), "-o", str(sortie), "--prelude", "externe"]
    )
    assert code == ERREUR_COMPILATION
    assert "upea_prelude.py" in capsys.readouterr().err


def test_fmt_ecrire_sur_un_fichier_en_lecture_seule(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    programme.chmod(stat.S_IREAD)
    try:
        if os.access(programme, os.W_OK):
            pytest.skip("le fichier reste inscriptible (administrateur)")
        assert main(["fmt", str(programme), "--ecrire"]) == ERREUR_COMPILATION
    finally:
        programme.chmod(stat.S_IREAD | stat.S_IWRITE)
    erreurs = capsys.readouterr().err
    assert erreurs.startswith(f"upea : impossible d'écrire {programme} (")
    assert "commentaire" not in erreurs  # rien n'a été écrit, rien n'est perdu


def test_run_sur_un_dossier(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["run", str(tmp_path)]) == ERREUR_COMPILATION
    assert capsys.readouterr().err == (
        f"upea : {tmp_path} est un dossier, pas un fichier\n"
    )


@pytest.mark.parametrize(
    "commande",
    [["run"], ["transpile"]],
    ids=["run", "transpile"],
)
def test_un_tube_ferme_est_une_fin_silencieuse(
    commande: list[str], tmp_path: Path
) -> None:
    fichier = tmp_path / "bavard.upea"
    fichier.write_text("tataitahi i roto 0..200000 { faaite i; }\n", encoding="utf-8")
    processus = subprocess.Popen(
        [sys.executable, "-m", "upea", *commande, str(fichier)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=bac_a_sable.RACINE,
        env=bac_a_sable._environnement(),
    )
    assert processus.stdout is not None and processus.stderr is not None
    processus.stdout.readline()
    processus.stdout.close()  # le lecteur s'en va, comme `| head -1`
    erreurs = processus.stderr.read()
    assert processus.wait(timeout=60) == OK
    assert erreurs == b""
