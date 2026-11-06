"""Conseil, lot L5 : `fmt --ecrire` réécrit le fichier comme avant (code 0), mais dit
sur la sortie d'erreur combien de commentaires il a perdus."""

from pathlib import Path

import pytest

from upea.cli import OK, main
from upea.compilateur import commentaires

COMMENTE = (
    "// Calcul du total des ventes\n"
    "tuu total = 0; /* en francs */\n"
    'faaite total, "// pas un commentaire", "/* non plus */";\n'
)


def test_les_commentaires_sont_comptes() -> None:
    assert commentaires(COMMENTE) == 2
    assert commentaires("/* sur\n deux lignes */ faaite 1; // fin") == 2
    assert commentaires('faaite "//";') == 0


def test_fmt_ecrire_signale_les_commentaires_perdus(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "commente.upea"
    fichier.write_text(COMMENTE, encoding="utf-8")
    assert main(["fmt", str(fichier), "--ecrire"]) == OK
    sortie = capsys.readouterr()
    assert sortie.err == "upea : 2 commentaires perdus\n"
    assert sortie.out == ""
    assert fichier.read_text(encoding="utf-8") == (
        'tuu total = 0;\nfaaite total, "// pas un commentaire", "/* non plus */";\n'
    )


def test_un_seul_commentaire(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "un.upea"
    fichier.write_text("faaite 1; // un\n", encoding="utf-8")
    assert main(["fmt", str(fichier), "--ecrire"]) == OK
    assert capsys.readouterr().err == "upea : 1 commentaire perdu\n"


def test_sans_commentaire_rien_sur_la_sortie_d_erreur(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "net.upea"
    fichier.write_text("faaite  ( 1+2 ) ;", encoding="utf-8")
    assert main(["fmt", str(fichier), "--ecrire"]) == OK
    assert capsys.readouterr().err == ""
    assert fichier.read_text(encoding="utf-8") == "faaite 1 + 2;\n"


def test_sans_ecrire_rien_ne_change(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """Sans `--ecrire`, `fmt` n'écrit que sur la sortie standard, sans avertissement."""
    fichier = tmp_path / "commente.upea"
    fichier.write_text(COMMENTE, encoding="utf-8")
    assert main(["fmt", str(fichier)]) == OK
    assert capsys.readouterr().err == ""
    assert fichier.read_text(encoding="utf-8") == COMMENTE
