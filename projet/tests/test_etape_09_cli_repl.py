"""Étape 9 : la ligne de commande et le REPL."""

import inspect
import os
import subprocess
import sys
import warnings
from collections.abc import Generator, Iterator
from pathlib import Path

import pytest

from outils import EXEMPLES, PROJET, lire
from upea.cli import ERREUR_COMPILATION, ERREUR_EXECUTION, ERREUR_USAGE, OK, main
from upea.compilateur import executer
from upea.erreurs import ErreurExecution
from upea.repl import INVITE, SUITE, Reponse, repl

FAUX = (
    "tuu total = 0;\ntataitahi i roto 1..4 {\n"
    "    total = totale + i\n}\nfaaite total;\n"
)
EXECUTION = """\
ohipa moyenne(l) -> tuhaa {
    hoi tuhaa(l[0] + l[1]) / roa(l);
}
tuu vide = [];
faaite moyenne([2, 4]);
faaite moyenne(vide);
"""


@pytest.fixture
def programme(tmp_path: Path) -> Iterator[Path]:
    """Un fichier `.upea` à remplir dans le test."""
    yield tmp_path / "programme.upea"


def ecrire(chemin: Path, source: str) -> str:
    chemin.write_text(source, encoding="utf-8")
    return str(chemin)


# --- run, transpile, check ------------------------------------------------------------


def test_run_execute_le_programme(capsys: pytest.CaptureFixture[str]) -> None:
    exemple = EXEMPLES / "02_fibonacci.upea"
    assert main(["run", str(exemple)]) == OK
    assert capsys.readouterr().out == lire(exemple.with_suffix(".attendu"))


def test_run_avec_le_backend_ast(capsys: pytest.CaptureFixture[str]) -> None:
    exemple = EXEMPLES / "05_motu.upea"
    assert main(["run", str(exemple), "--backend", "ast"]) == OK
    assert capsys.readouterr().out == lire(exemple.with_suffix(".attendu"))


def test_transpile_affiche_le_python(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["transpile", str(EXEMPLES / "02_fibonacci.upea")]) == OK
    sortie = capsys.readouterr().out
    assert "def fibo(n: int) -> int:" in sortie
    assert "class _Tumu" in sortie  # le prélude


def test_transpile_ecrit_dans_un_fichier(tmp_path: Path) -> None:
    sortie = tmp_path / "fibo.py"
    assert (
        main(["transpile", str(EXEMPLES / "02_fibonacci.upea"), "-o", str(sortie)])
        == OK
    )
    compile(sortie.read_text(encoding="utf-8"), str(sortie), "exec")
    assert not (tmp_path / "fibo.py.map.json").exists()


def test_check_un_programme_correct(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["check", str(EXEMPLES / "06_tahua.upea")]) == OK
    assert "aucune erreur" in capsys.readouterr().out


def test_une_erreur_de_compilation_donne_le_code_1(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = ecrire(programme, FAUX)
    assert main(["check", fichier]) == ERREUR_COMPILATION
    erreurs = capsys.readouterr().err
    assert f"{fichier}:3:23 : erreur de syntaxe : ';' attendu" in erreurs
    assert "        total = totale + i\n" in erreurs


def test_run_refuse_un_programme_qui_ne_compile_pas(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["run", ecrire(programme, "faaite y;")]) == ERREUR_COMPILATION
    assert "'y' n'est pas déclaré" in capsys.readouterr().err


def test_une_erreur_d_execution_designe_la_ligne_upea(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = ecrire(programme, EXECUTION)
    assert main(["run", fichier]) == ERREUR_EXECUTION
    sorties = capsys.readouterr()
    assert sorties.out == "3.0\n"
    assert f"{fichier}:2 : erreur d'exécution : indice hors limites" in sorties.err
    assert "hoi tuhaa(l[0] + l[1]) / roa(l);" in sorties.err
    assert "Traceback" not in sorties.err


def test_l_option_trace_montre_le_traceback_python(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["run", ecrire(programme, EXECUTION), "--trace"]) == ERREUR_EXECUTION
    erreurs = capsys.readouterr().err
    assert "Traceback" in erreurs
    assert "IndexError" in erreurs


def test_l_erreur_d_execution_est_chainee_a_l_exception_python() -> None:
    with pytest.raises(ErreurExecution) as info:
        executer(EXECUTION)
    assert isinstance(info.value.__cause__, IndexError)


def test_les_avertissements_vont_sur_stderr(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["run", ecrire(programme, "tuu x = 1;\nfaaite 2;")]) == OK
    sorties = capsys.readouterr()
    assert sorties.out == "2\n"
    assert "avertissement : 'x' est déclarée mais jamais utilisée" in sorties.err


def test_sans_types_desactive_la_verification(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = ecrire(programme, 'tuu x: numera = "a";\nfaaite x;')
    assert main(["run", fichier]) == ERREUR_COMPILATION
    assert main(["run", fichier, "--sans-types"]) == OK
    assert capsys.readouterr().out == "a\n"


def test_un_fichier_avec_marque_d_ordre_des_octets_s_execute(
    programme: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    programme.write_text("faaite 1;", encoding="utf-8-sig")
    assert main(["run", str(programme)]) == OK
    assert capsys.readouterr().out == "1\n"


def test_un_fichier_introuvable_est_signale_proprement(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["run", str(tmp_path / "absent.upea")]) == ERREUR_COMPILATION
    erreurs = capsys.readouterr().err
    assert "fichier introuvable" in erreurs
    assert "Traceback" not in erreurs


def test_une_commande_inconnue_est_refusee(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["vole", "x.upea"]) == ERREUR_USAGE
    assert "vole" in capsys.readouterr().err


def test_un_backend_inconnu_est_refuse_par_argparse() -> None:
    assert main(["run", "x.upea", "--backend", "cobol"]) == ERREUR_USAGE


def test_l_aide_rend_zero(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["--help"]) == OK
    assert "transpile" in capsys.readouterr().out


def test_python_m_upea_fonctionne() -> None:
    resultat = subprocess.run(
        [sys.executable, "-m", "upea", "run", str(EXEMPLES / "01_ia_ora_na.upea")],
        cwd=PROJET,
        env={**os.environ, "PYTHONPATH": str(PROJET), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        encoding="utf-8",
    )
    assert resultat.returncode == OK, resultat.stderr
    attendu = lire(EXEMPLES / "01_ia_ora_na.attendu")
    assert resultat.stdout.replace("\r\n", "\n") == attendu


def test_python_m_upea_rend_le_code_d_erreur(programme: Path) -> None:
    resultat = subprocess.run(
        [sys.executable, "-m", "upea", "run", ecrire(programme, EXECUTION)],
        cwd=PROJET,
        env={**os.environ, "PYTHONPATH": str(PROJET), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        encoding="utf-8",
    )
    assert resultat.returncode == ERREUR_EXECUTION
    assert "indice hors limites" in resultat.stderr


def lancer_en_cp1252(*arguments: str) -> subprocess.CompletedProcess[str]:
    """`python -m upea …` dont la sortie est redirigée vers un fichier sous Windows :
    l'encodage par défaut est alors cp1252, qui n'a ni `┌─┴─┐` ni `ʻ`."""
    return subprocess.run(
        [sys.executable, "-m", "upea", *arguments],
        cwd=PROJET,
        env={**os.environ, "PYTHONPATH": str(PROJET), "PYTHONIOENCODING": "cp1252"},
        capture_output=True,
        encoding="utf-8",
    )


def test_une_sortie_redirigee_recoit_les_dessins_en_utf8() -> None:
    exemple = EXEMPLES / "10_hohoa.upea"
    resultat = lancer_en_cp1252("run", str(exemple))
    assert resultat.returncode == OK, resultat.stderr
    attendu = lire(exemple.with_suffix(".attendu"))
    assert resultat.stdout.replace("\r\n", "\n") == attendu


def test_une_erreur_redirigee_garde_ses_caracteres(programme: Path) -> None:
    source = 'faaite "ʻupeʻa" + 1;'
    resultat = lancer_en_cp1252("run", "--sans-types", ecrire(programme, source))
    assert resultat.returncode == ERREUR_EXECUTION
    assert "opération '+' impossible" in resultat.stderr
    assert '"ʻupeʻa" + 1' in resultat.stderr


#: Accepté sans types, ce programme fait émettre à CPython, quand il compile le
#: Python généré, un SyntaxWarning (« perhaps you missed a comma? »).
INDICE_DE_CONSTANTE = "faaite (3)[0];"


def test_run_n_affiche_aucun_avertissement_de_python(programme: Path) -> None:
    resultat = subprocess.run(
        [
            sys.executable,
            "-m",
            "upea",
            "run",
            "--sans-types",
            ecrire(programme, INDICE_DE_CONSTANTE),
        ],
        cwd=PROJET,
        env={**os.environ, "PYTHONPATH": str(PROJET), "PYTHONIOENCODING": "utf-8"},
        capture_output=True,
        encoding="utf-8",
    )
    assert resultat.returncode == ERREUR_EXECUTION
    assert "on ne peut pas indexer un numera" in resultat.stderr
    assert "Warning" not in resultat.stderr, resultat.stderr


# --- Le REPL --------------------------------------------------------------------------


type Session = Generator[Reponse, str, None]


@pytest.fixture
def session() -> Iterator[Session]:
    generateur = repl()
    assert next(generateur) == Reponse("", INVITE)
    yield generateur


def test_le_repl_est_un_generateur() -> None:
    assert inspect.isgenerator(repl())


def test_le_repl_garde_l_etat_entre_les_saisies(session: Session) -> None:
    assert session.send("tuu x = 2;") == Reponse("", INVITE)
    assert session.send("x * 21") == Reponse("42\n", INVITE)


def test_le_repl_accepte_une_saisie_sur_plusieurs_lignes(session: Session) -> None:
    session.send("tuu x = 3;")
    assert session.send("ahani x > 1 {") == Reponse("", SUITE)
    assert session.send('    faaite "oui";') == Reponse("", SUITE)
    assert session.send("}") == Reponse("oui\n", INVITE)


def test_une_accolade_dans_un_texte_ne_compte_pas(session: Session) -> None:
    assert session.send('faaite "{";') == Reponse("{\n", INVITE)


def test_le_repl_survit_aux_erreurs(session: Session) -> None:
    session.send("tuu x = 2;")
    reponse = session.send("faaite y;")
    assert "<repl>:2:8 : erreur sémantique : 'y' n'est pas déclaré" in reponse.sortie
    assert reponse.invite == INVITE
    assert session.send("x").sortie == "2\n"


def test_une_erreur_d_execution_n_efface_pas_ce_qui_precede(session: Session) -> None:
    session.send("tuu x = 2;")
    assert "division par zéro" in session.send("tuu z = 1 / 0;").sortie
    assert "'z' n'est pas déclaré" in session.send("z").sortie
    assert session.send("x").sortie == "2\n"


def test_le_repl_garde_les_fonctions_et_les_globales(session: Session) -> None:
    session.send("tuu n = 0;")
    session.send("ohipa f() {")
    session.send("    n = n + 1;")
    session.send("}")
    session.send("f();")
    session.send("f();")
    assert session.send("n").sortie == "2\n"


def test_le_repl_n_affiche_aucun_avertissement_de_python() -> None:
    session = repl(types=False)
    next(session)
    with warnings.catch_warnings(record=True) as avertissements:
        warnings.simplefilter("always")
        reponse = session.send(INDICE_DE_CONSTANTE)
    assert "on ne peut pas indexer un numera" in reponse.sortie
    assert [a for a in avertissements if a.category is SyntaxWarning] == []


def test_le_repl_affiche_un_litteral_de_graphe(session: Session) -> None:
    sortie = session.send("upea { 1 -> 2 }").sortie
    assert sortie == "upea : 2 nœuds, 1 arc\n1 → 2\n2 ·\n"


@pytest.mark.parametrize(
    ("commande", "fragment"),
    [
        (":tokens tuu x", "Token(TUU, 'tuu', 1:1)"),
        (":arbre 1 + 2", "Binaire op='+'"),
        (":python 1 + 2", "_affiche((1 + 2))"),
        (":aide", ":tokens"),
        (":vole", "commande inconnue"),
        (":tokens @", "caractère inattendu"),
    ],
)
def test_les_commandes_du_repl(session: Session, commande: str, fragment: str) -> None:
    assert fragment in session.send(commande).sortie


def test_la_sous_commande_repl_lit_l_entree(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    saisies = iter(["tuu x = 20;", "x * 2 + 2"])

    def lire_saisie(invite: str) -> str:
        try:
            return next(saisies)
        except StopIteration:
            raise EOFError from None

    monkeypatch.setattr("builtins.input", lire_saisie)
    assert main(["repl"]) == OK
    assert "42\n" in capsys.readouterr().out
