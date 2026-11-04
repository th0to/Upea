"""Étape 8 : la génération de Python, et l'exécution des exemples."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from outils import lancer, lire
from upea.compilateur import compiler, transpiler
from upea.emetteur import Emetteur
from upea.generateur import GenerateurPython


def python_de(source: str, *, types: bool = True) -> str:
    """Le Python généré pour `source`, sans le prélude."""
    compilation = compiler(source, types=types)
    return GenerateurPython().traduire(
        compilation.programme.instructions, compilation.analyse
    )[0]


# --- Le test central -----------------------------------------------------------------


def test_chaque_exemple_produit_sa_sortie_attendue(exemple: Path) -> None:
    attendu = lire(exemple.with_suffix(".attendu"))
    assert lancer(lire(exemple)) == attendu


def test_le_code_genere_pour_chaque_exemple_est_du_python_valide(exemple: Path) -> None:
    compile(transpiler(lire(exemple)).code, exemple.name, "exec")


def test_le_fichier_genere_est_autonome(exemple: Path, tmp_path: Path) -> None:
    fichier = tmp_path / "programme.py"
    fichier.write_text(transpiler(lire(exemple)).code, encoding="utf-8")
    resultat = subprocess.run(
        [sys.executable, str(fichier)],
        capture_output=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        check=True,
    )
    assert resultat.stdout.replace("\r\n", "\n") == lire(
        exemple.with_suffix(".attendu")
    )


# --- L'émetteur -----------------------------------------------------------------------


def test_l_emetteur_indente_dans_un_with_et_retrouve_son_niveau() -> None:
    e = Emetteur()
    e.ligne("if x:")
    with e.bloc():
        e.ligne("y = 1")
        assert e.niveau == 1
    e.ligne("z = 2")
    assert e.niveau == 0
    assert e.texte() == "if x:\n    y = 1\nz = 2\n"


def test_l_emetteur_ajoute_pass_a_un_bloc_vide() -> None:
    e = Emetteur()
    e.ligne("def f():")
    with e.bloc():
        pass
    assert e.texte() == "def f():\n    pass\n"


def test_l_emetteur_retrouve_son_niveau_si_une_exception_traverse_le_with() -> None:
    e = Emetteur()
    with pytest.raises(ValueError), e.bloc():
        raise ValueError
    assert e.niveau == 0


def test_l_emetteur_note_la_ligne_source_de_chaque_ligne() -> None:
    e = Emetteur()
    with e.depuis(4):
        e.ligne("a")
        with e.depuis(7):
            e.ligne("b")
        e.ligne("c")
    e.ligne("d")
    assert e.correspondances == {1: 4, 2: 7, 3: 4}


def test_l_emetteur_indente_un_texte_de_plusieurs_lignes() -> None:
    e = Emetteur()
    with e.bloc(vide=None):
        e.ligne("x = [\n    1,\n]")
    assert e.texte() == "    x = [\n        1,\n    ]\n"


# --- La traduction des instructions ---------------------------------------------------


@pytest.mark.parametrize(
    ("source", "python"),
    [
        ("tuu x = 1 + 2 * 3;\nfaaite x;", "x = (1 + (2 * 3))\n_affiche(x)\n"),
        (
            "tuu a = 1;\nahani a > 1 { faaite 1; } taae ahani a < 0 { faaite 2; } "
            "taae { faaite 3; }",
            "a = 1\nif (a > 1):\n    _affiche(1)\nelif (a < 0):\n    _affiche(2)\n"
            "else:\n    _affiche(3)\n",
        ),
        (
            "tuu n = 3;\ntataitahi i roto 0..=n { faaite i; }",
            "n = 3\nfor i in range(0, n + 1):\n    _affiche(i)\n",
        ),
        (
            "tataitahi i roto 1..4 { haere; }",
            "for i in range(1, 4):\n    continue\n",
        ),
        (
            'tuu g = upea { "A" -> "B" : 2, 1 <-> 2 };\n'
            'tataitahi m roto g mai "A" aano { faaite m; }',
            "g = _graphe([('A', 'B', 2, False), (1, 2, 1, True)])\n"
            "for m in _parcours(g, 'A', mode='aano'):\n    _affiche(m)\n",
        ),
        (
            "tuu t = tumu(1);\ntataitahi n roto t { faaite n.hotu; }",
            "t = _tumu(1)\nfor n in _parcours(t):\n    _affiche(n.hotu)\n",
        ),
        (
            "tuu n = 0;\n"
            "ohipa f(x: numera) -> numera { n = n + x; hoi n; }\nfaaite f(2);",
            "n = 0\ndef f(x: int) -> int:\n    global n\n"
            "    n = (n + x)\n    return n\n"
            "_affiche(f(2))\n",
        ),
        ("ohipa f(a, b) { }", "def f(a, b):\n    pass\n"),
        ("tamau hape { faaea; }", "while False:\n    break\n"),
        (
            "tuu t = tumu(1);\nt.hotu = -t.hotu;\nfaaite eiaha tia ma hape;",
            "t = _tumu(1)\nt.hotu = (-t.hotu)\n_affiche(((not True) and False))\n",
        ),
        (
            'tuu l = [hape];\nl[0] = "a" roto "abc";',
            "l = [False]\nl[0] = _roto('a', 'abc')\n",
        ),
    ],
)
def test_chaque_instruction_est_traduite_comme_prevu(source: str, python: str) -> None:
    assert python_de(source) == python


def test_un_texte_ne_devient_jamais_du_code() -> None:
    assert python_de('faaite "\\"); import os; (\\"";') == (
        "_affiche('\"); import os; (\"')\n"
    )


def test_un_champ_sur_un_entier_reste_du_python_valide() -> None:
    code = python_de("faaite (1).hotu;", types=False)
    assert code == "_affiche((1).hotu)\n"
    compile(code, "<test>", "exec")


def test_les_parentheses_preservent_le_sens() -> None:
    # En Python, `1 < 2 == True` serait une comparaison chaînée, fausse.
    source = (
        "tuu a = 1;\ntuu b = 2;\nfaaite (a < b) == tia, 10 - (4 - 3), (10 - 4) - 3;"
    )
    assert lancer(source) == "tia 9 3\n"


def test_les_noms_reserves_en_python_sont_renommes() -> None:
    source = (
        "tuu print = 1;\ntuu class = 2;\ntuu len = [print, class];\n"
        "ohipa list(match) { hoi match + 1; }\n"
        "faaite print + class, len, list(3), roa(len);"
    )
    assert "_v_print = 1" in python_de(source)
    assert "def _v_list(_v_match):" in python_de(source)
    assert lancer(source) == "3 [1, 2] 4 2\n"


@pytest.mark.parametrize(
    ("source", "sortie"),
    [
        (
            'faaite tia, hape, aore, 3, 3.5, 2.0, -0.5, "a";',
            "tia hape aore 3 3.5 2.0 -0.5 a",
        ),
        ('faaite [1, "a\\"b", [tia, aore], 1.5];', '[1, "a\\"b", [tia, aore], 1.5]'),
        ('faaite ["l1\\nl2\\t"];', '["l1\\nl2\\t"]'),
        (
            'faaite parau(tumu("r", tumu(1), tumu([2])));',
            'tumu("r", tumu(1), tumu([2]))',
        ),
        (
            'faaite upea { "A" -> "B", "B" -> "A" : 2.5 }, upea {};',
            'upea { "A" -> "B", "B" -> "A" : 2.5 } upea {}',
        ),
        ("faaite parau(upea { 1 <-> 2 : 4 });", "upea { 1 <-> 2 : 4 }"),
        (
            "faaite 0, upea { 1 -> 2, 2 -> 1 : 3, 4 };",
            "0 upea { 1 -> 2, 2 -> 1 : 3, 4 }",
        ),
        ("faaite parau(tia) + parau([1]);", "tia[1]"),
        ('faaite "a\\nb";', "a\nb"),
        ("faaite 1 / 3, 6 / 3;", "0.3333333333333333 2.0"),
        ("faaite 7 % -3, -7 % 3;", "-2 2"),
        ("faaite 2 * 1.5, 2 + 3;", "3.0 5"),
        ("faaite;", ""),
        ("faaite [];", "[]"),
    ],
)
def test_l_affichage_suit_la_specification(source: str, sortie: str) -> None:
    assert lancer(source) == sortie + "\n"
