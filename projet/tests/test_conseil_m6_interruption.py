"""Conseil, lot M6 : Ctrl-C interrompt le programme, pas la session. Le REPL répond
« interrompu » et garde ce qui a été déclaré avant ; `run` s'arrête avec le code 130,
sans traceback."""

import _thread
import threading
import time
from pathlib import Path

import pytest

from upea import cli
from upea import repl as module_repl
from upea.cli import INTERROMPU, main
from upea.repl import repl


def _interrompre(*args: object, **kwargs: object) -> None:
    print("avant")
    raise KeyboardInterrupt


def test_le_repl_survit_a_ctrl_c(monkeypatch: pytest.MonkeyPatch) -> None:
    session = repl()
    next(session)
    assert session.send("tuu x = 42;").sortie == ""
    with monkeypatch.context() as m:
        m.setattr(module_repl, "executer_code", _interrompre)
        assert session.send("tuu y = 1;").sortie == "avant\ninterrompu\n"
    assert session.send("faaite x;").sortie == "42\n"
    # La saisie interrompue n'est pas retenue, comme une saisie en erreur.
    assert "'y' n'est pas déclaré" in session.send("faaite y;").sortie


def test_un_ctrl_c_pendant_la_compilation(monkeypatch: pytest.MonkeyPatch) -> None:
    session = repl()
    next(session)
    with monkeypatch.context() as m:
        m.setattr(module_repl, "compiler", _interrompre)
        assert session.send("faaite 1;").sortie == "interrompu\n"
    assert session.send("faaite 2;").sortie == "2\n"


def test_run_rend_le_code_130(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "long.upea"
    fichier.write_text("faaite 1;\n", encoding="utf-8")
    monkeypatch.setattr(cli, "executer", _interrompre)
    assert main(["run", str(fichier)]) == INTERROMPU == 130
    sortie = capsys.readouterr()
    assert sortie.out == "avant\n"
    assert sortie.err == "upea : interrompu\n"


#: Une boucle finie, de l'ordre de deux secondes : sans interruption, elle se termine.
LONGUE = "tuu s = 0;\ntataitahi i roto 0..20000000 { s = s + i; }\nfaaite s;\n"


def _apres(secondes: float) -> threading.Timer:
    minuteur = threading.Timer(secondes, _thread.interrupt_main)
    minuteur.start()
    return minuteur


def test_un_vrai_ctrl_c_dans_le_repl() -> None:
    session = repl()
    next(session)
    session.send("tuu x = 42;")
    debut = time.monotonic()
    minuteur = _apres(0.3)
    try:
        sortie = session.send(LONGUE.replace("\n", " "))
    finally:
        minuteur.cancel()
    assert sortie.sortie == "interrompu\n"
    assert time.monotonic() - debut < 1.5
    assert session.send("faaite x;").sortie == "42\n"


def test_un_vrai_ctrl_c_dans_run(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "long.upea"
    fichier.write_text(LONGUE, encoding="utf-8")
    minuteur = _apres(0.5)
    try:
        code = main(["run", str(fichier)])
    finally:
        minuteur.cancel()
    assert code == INTERROMPU
    erreurs = capsys.readouterr().err
    assert erreurs == "upea : interrompu\n"
