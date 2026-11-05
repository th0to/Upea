"""Conseil, lot L1 : un programme trop imbriqué pour Python est une erreur de syntaxe,
signalée de la même façon par check, run, fmt, le REPL, l'atelier et le bac à sable
(jamais un traceback).

Les limites viennent de CPython : 200 parenthèses ouvertes, 100 niveaux
d'indentation, une vingtaine de boucles imbriquées dans un même bloc de code.
"""

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pytest

from outils import PROJET, lancer
from upea import atelier, bac_a_sable
from upea.cli import ERREUR_COMPILATION, main
from upea.compilateur import compiler, executer_code, mettre_en_forme, transpiler
from upea.erreurs import ErreursMultiples, ErreurSyntaxe
from upea.parser import MAX_BLOCS, MAX_BOUCLES, MAX_EXPRESSION, parse
from upea.repl import repl
from upea.sourcemap import SourceMap

# --- Les programmes -------------------------------------------------------------------


def somme(termes: int) -> str:
    """`x + x + … + x` : une somme à plat, profonde de `termes - 1` opérations."""
    return "tuu x = 1;\nfaaite " + " + ".join(["x"] * termes) + ";\n"


def blocs(n: int) -> str:
    return "ahani tia {\n" * n + "faaite 1;\n" + "}\n" * n


def boucles(n: int) -> str:
    entetes = "".join(f"tataitahi i{k} roto 0..1 {{\n" for k in range(n))
    return entetes + "faaite 1;\n" + "}\n" * n


def parentheses(n: int) -> str:
    return "faaite " + "(" * n + "1" + ")" * n + ";\n"


#: Une expression de profondeur exactement `n` (au sens de la limite), par forme.
FORMES: dict[str, Callable[[int], str]] = {
    "somme": lambda n: " + ".join(["1"] * (n + 1)),
    "ma": lambda n: " ma ".join(["tia"] * (n + 1)),
    "moins": lambda n: "- " * n + "1",
    "eiaha": lambda n: "eiaha " * n + "tia",
    "parentheses": lambda n: "(" * n + "1" + ")" * n,
    "moins_parentheses": lambda n: "-(" * (n // 2) + "1" + ")" * (n // 2),
    "listes": lambda n: "[" * n + "1" + "]" * n,
    "appels": lambda n: "roa([" * (n // 2) + "1" + "])" * (n // 2),
    "tumu": lambda n: "roa(" + "tumu(1, " * (n - 2) + "tumu(1)" + ")" * (n - 1),
    "indices": lambda n: "l[" * n + "0" + "]" * n,
    # roa( + [ + upea (3) : 5 niveaux par étage ; aifaito : roa( + aifaito (2) = 3.
    "upea": lambda n: "roa([upea { " * (n // 5) + "1" + " }])" * (n // 5),
    "aifaito": lambda n: "roa(aifaito [" * (n // 3) + "1" + "])" * (n // 3),
}

ENTETE = "tuu l = [0];\ntuu t = tumu(1, tumu(2));\n"


def avec(expression: str) -> str:
    return ENTETE + f"faaite {expression};\n"


#: Les programmes de TEST-03 et de COMP-03, et les 22 boucles trouvées en phase 1.
TROP_IMBRIQUES = {
    "somme201": somme(201),
    "somme1000": "faaite " + " + ".join(["1"] * 1000) + ";\n",
    "blocs100": blocs(100),
    "blocs91": blocs(MAX_BLOCS + 1),
    "parentheses500": parentheses(500),
    "boucles22": boucles(22),
    "boucles21": boucles(MAX_BOUCLES + 1),
    "upea": avec(FORMES["upea"](MAX_EXPRESSION + 5)),
    "champs": ENTETE + "faaite t" + ".amaa[0]" * 100 + ";\n",
}


def _messages(erreur: ErreursMultiples) -> list[str]:
    return [e.message for e in erreur.erreurs]


# --- Les limites, et leur message -----------------------------------------------------


@pytest.mark.parametrize("nom", TROP_IMBRIQUES)
def test_un_programme_trop_imbrique_est_une_erreur_de_syntaxe(nom: str) -> None:
    with pytest.raises(ErreursMultiples) as info:
        compiler(TROP_IMBRIQUES[nom])
    (erreur,) = info.value.erreurs
    assert isinstance(erreur, ErreurSyntaxe)
    assert erreur.position is not None and erreur.position.ligne >= 1
    assert "au plus" in erreur.message


def test_les_messages_nomment_la_limite() -> None:
    def message(source: str) -> str:
        with pytest.raises(ErreursMultiples) as info:
            compiler(source)
        return _messages(info.value)[0]

    assert message(blocs(MAX_BLOCS + 1)) == "trop de blocs imbriqués (90 au plus)"
    assert message(boucles(MAX_BOUCLES + 1)) == (
        "trop de boucles imbriquées (20 au plus)"
    )
    assert message(somme(MAX_EXPRESSION + 2)) == (
        "expression trop imbriquée (150 niveaux au plus)"
    )
    assert message(parentheses(MAX_EXPRESSION + 1)) == (
        "expression trop imbriquée (150 niveaux au plus)"
    )


def test_la_limite_des_blocs_compte_le_corps_d_une_fonction() -> None:
    """Le corps d'une `ohipa` est un niveau d'indentation de plus en Python."""

    def dans_une_fonction(n: int) -> str:
        return "ohipa f() {\n" + blocs(n) + "}\nf();\n"

    with pytest.raises(ErreursMultiples):
        compiler(dans_une_fonction(MAX_BLOCS))
    assert lancer(dans_une_fonction(MAX_BLOCS - 1)) == "1\n"


@pytest.mark.parametrize("forme", FORMES)
def test_a_la_limite_exacte_les_deux_backends_compilent(forme: str) -> None:
    source = avec(FORMES[forme](MAX_EXPRESSION))
    assert lancer(source, types=False) == lancer(source, "ast", types=False)


@pytest.mark.parametrize("forme", ["somme", "moins", "eiaha", "parentheses", "listes"])
def test_juste_au_dessus_de_la_limite_c_est_une_erreur(forme: str) -> None:
    with pytest.raises(ErreursMultiples) as info:
        compiler(avec(FORMES[forme](MAX_EXPRESSION + 1)), types=False)
    assert _messages(info.value) == ["expression trop imbriquée (150 niveaux au plus)"]


def test_blocs_et_boucles_a_la_limite_exacte() -> None:
    assert lancer(blocs(MAX_BLOCS)) == "1\n"
    assert lancer(boucles(MAX_BOUCLES), "ast") == "1\n"


#: Le pire cas : 90 blocs dans une fonction, et une expression au maximum.
PIRE_CAS = """\
import sys
sys.path.insert(0, ".")
from upea import compilateur
from upea.generateur_ast import compiler_module
sys.setrecursionlimit({limite})
source = sys.stdin.read()
compilateur.compiler(source, types=False)
for backend in ("python", "ast"):
    sortie = compilateur.transpiler(source, backend, types=False, prelude_externe=True)
    compiler_module(sortie.code, "<x>")
compilateur.mettre_en_forme(source)
print("ok")
"""


@pytest.mark.parametrize("limite", [1000, 20_000])
@pytest.mark.parametrize("forme", ["somme", "moins", "appels", "upea", "eiaha"])
def test_le_pire_cas_combine_passe_quelle_que_soit_la_limite_de_python(
    forme: str, limite: int
) -> None:
    corps = "ahani tia {\n" * (MAX_BLOCS - 1)
    source = (
        ENTETE
        + "ohipa g() {\n"
        + corps
        + f"faaite {FORMES[forme](MAX_EXPRESSION)};\n"
        + "}\n" * (MAX_BLOCS - 1)
        + "}\ng();\n"
    )
    resultat = subprocess.run(
        [sys.executable, "-c", PIRE_CAS.format(limite=limite)],
        input=source,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=PROJET,
        env=os.environ | {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"},
        timeout=120,
    )
    assert resultat.stdout == "ok\n", resultat.stderr[-2000:]


# --- Chaque chemin le signale de la même façon ---------------------------------------


@pytest.mark.parametrize("nom", ["somme201", "blocs100", "parentheses500", "boucles22"])
def test_check_et_run_donnent_le_code_1_sans_traceback(
    nom: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / f"{nom}.upea"
    fichier.write_text(TROP_IMBRIQUES[nom], encoding="utf-8")
    for commande in ("check", "run"):
        assert main([commande, str(fichier)]) == ERREUR_COMPILATION
        erreurs = capsys.readouterr().err
        assert "erreur de syntaxe" in erreurs
        assert "Traceback" not in erreurs


@pytest.mark.parametrize("nom", ["somme1000", "parentheses500"])
def test_fmt_signale_l_imbrication(
    nom: str, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / f"{nom}.upea"
    fichier.write_text(TROP_IMBRIQUES[nom], encoding="utf-8")
    assert main(["fmt", str(fichier)]) == ERREUR_COMPILATION
    assert "expression trop imbriquée" in capsys.readouterr().err


@pytest.mark.parametrize("nom", TROP_IMBRIQUES)
def test_l_atelier_rend_un_diagnostic(nom: str) -> None:
    source = TROP_IMBRIQUES[nom]
    verification = atelier.verifier(source)
    assert not verification.valide
    assert verification.diagnostics[0].sorte == "syntaxe"
    assert atelier.formater(source).code is None
    assert atelier.transpiler(source).code is None


def test_le_repl_survit() -> None:
    session = repl()
    next(session)
    assert session.send("tuu x = 1;").sortie == ""
    sortie = session.send("faaite " + " + ".join(["x"] * 201) + ";").sortie
    assert "expression trop imbriquée" in sortie
    assert session.send("faaite x;").sortie == "1\n"


@pytest.mark.parametrize("nom", ["somme201", "blocs100", "boucles22"])
def test_le_bac_a_sable_rend_une_erreur_de_compilation(nom: str) -> None:
    resultat = bac_a_sable.executer(TROP_IMBRIQUES[nom])
    assert resultat.statut == "erreur_compilation"
    assert resultat.code_retour == ERREUR_COMPILATION
    assert "erreur de syntaxe" in resultat.rapport


# --- Les secondes barrières -----------------------------------------------------------


def test_le_filet_autour_de_compile() -> None:
    """Un code que CPython refuse de compiler devient une erreur de compilation."""
    code = "x = " + "(" * 300 + "1" + ")" * 300 + "\n"
    with pytest.raises(ErreursMultiples) as info:
        executer_code(code, SourceMap(lignes={1: 4}))
    (erreur,) = info.value.erreurs
    assert isinstance(erreur, ErreurSyntaxe)
    assert erreur.message == "programme trop imbriqué pour être compilé"
    assert erreur.position is not None and erreur.position.ligne == 4


def _profondeur() -> int:
    """Le nombre de frames Python de la pile courante."""
    frame, n = sys._getframe(), 0
    while frame.f_back is not None:
        frame, n = frame.f_back, n + 1
    return n


def test_le_parser_ne_laisse_pas_sortir_recursion_error() -> None:
    """Sous une limite de Python très basse, le parser déborde avant ses propres
    compteurs : l'erreur reste une erreur de syntaxe."""
    limite = sys.getrecursionlimit()
    sys.setrecursionlimit(_profondeur() + 50)
    try:
        with pytest.raises(ErreursMultiples) as info:
            parse(parentheses(60))
    finally:
        sys.setrecursionlimit(limite)
    assert _messages(info.value) == ["programme trop imbriqué pour être compilé"]


def test_la_facade_ne_laisse_pas_sortir_recursion_error() -> None:
    """Une somme à plat ne fait pas descendre le parser, mais l'analyse et les
    générateurs, eux, sont récursifs."""
    limite = sys.getrecursionlimit()
    source = avec(FORMES["somme"](120))
    compiler(source)
    sys.setrecursionlimit(_profondeur() + 60)
    try:
        for appel in (
            lambda: compiler(source),
            lambda: transpiler(source),
            lambda: mettre_en_forme(source),
        ):
            with pytest.raises(ErreursMultiples):
                appel()
    finally:
        sys.setrecursionlimit(limite)
