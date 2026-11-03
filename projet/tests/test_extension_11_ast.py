"""Extension 11 : la génération via le module `ast` et `ast.unparse`."""

import ast
from pathlib import Path
from types import CodeType

import pytest

from outils import EXEMPLES, lancer, lire
from upea.compilateur import NOM_FICHIER, compiler, executer_arbre, transpiler
from upea.erreurs import ErreurExecution
from upea.generateur_ast import GenerateurAst, compiler_module


def module_de(source: str) -> ast.Module:
    compilation = compiler(source)
    return GenerateurAst().module(compilation.programme, compilation.analyse)


def corps_python(source: str) -> str:
    """Le texte de `ast.unparse` pour le programme seul, sans le prélude."""
    return ast.unparse(module_de(source))


def test_le_backend_produit_un_vrai_module() -> None:
    assert isinstance(module_de("faaite 1;"), ast.Module)


def test_chaque_exemple_genere_par_ce_backend_produit_sa_sortie(exemple: Path) -> None:
    assert lancer(lire(exemple), "ast") == lire(exemple.with_suffix(".attendu"))


def test_les_noeuds_portent_les_lignes_d_upea() -> None:
    module = module_de(lire(EXEMPLES / "02_fibonacci.upea"))
    fibo = module.body[0]
    assert isinstance(fibo, ast.FunctionDef)
    assert fibo.name == "fibo"
    assert fibo.lineno == 2
    assert [instruction.lineno for instruction in fibo.body] == [3, 6]
    boucles = [n for n in module.body if isinstance(n, ast.For)]
    assert [b.lineno for b in boucles] == [22, 28, 31]


def test_unparse_ne_garde_que_les_parentheses_necessaires() -> None:
    source = (
        "tuu a = 1;\ntuu b = 2;\ntuu c = 3;\n"
        "faaite (a + b) * c, a + (b * c), (a < b) == tia, a - (b - c);"
    )
    assert "_affiche((a + b) * c, a + b * c, (a < b) == True, a - (b - c))" in (
        corps_python(source)
    )
    assert lancer(source, "ast") == "9 7 tia 2\n"


def test_une_suite_de_ma_tient_dans_un_seul_boolop() -> None:
    assert (
        corps_python("faaite tia ma hape ma tia;")
        == "_affiche(True and False and True)"
    )


def test_taae_ahani_devient_elif() -> None:
    source = (
        "tuu x = 1;\n"
        "ahani x > 1 { faaite 1; } taae ahani x > 0 { faaite 2; } taae { faaite 3; }"
    )
    texte = corps_python(source)
    assert "elif x > 0:" in texte
    assert "else:" in texte
    assert lancer(source, "ast") == "2\n"


def test_les_declarations_global_et_les_annotations_sont_presentes() -> None:
    texte = corps_python(lire(EXEMPLES / "03_tapura.upea"))
    assert "def classe(n: int) -> str:\n    global appels" in texte
    annote = corps_python("ohipa f(a: tapura, t: tumu, g: upea) -> aore { hoi; }")
    assert "def f(a: list, t: _Tumu, g: _Upea) -> None:" in annote


def test_l_arbre_se_compile_et_s_execute_sans_passer_par_le_texte(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert isinstance(compiler_module(module_de("faaite 1;"), NOM_FICHIER), CodeType)
    executer_arbre(lire(EXEMPLES / "04_tumu.upea"))
    assert capsys.readouterr().out == lire(EXEMPLES / "04_tumu.attendu")


def test_une_erreur_dans_l_arbre_compile_pointe_deja_la_bonne_ligne() -> None:
    source = "ohipa f(l) {\n    hoi l[3];\n}\nfaaite f([1]);"
    with pytest.raises(ErreurExecution) as info:
        executer_arbre(source)
    assert info.value.position is not None
    assert info.value.position.ligne == 2


def test_le_texte_produit_se_relit_avec_la_meme_structure(exemple: Path) -> None:
    module = module_de(lire(exemple))
    relu = ast.parse(ast.unparse(module))
    assert ast.dump(relu) == ast.dump(module)


def test_le_texte_complet_contient_le_prelude() -> None:
    code = transpiler("faaite 1;", "ast").code
    assert "class _Tumu" in code
    compile(code, "<test>", "exec")
