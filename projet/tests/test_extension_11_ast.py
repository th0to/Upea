"""Extension 11 : la génération via le module `ast` et `ast.unparse`."""

import ast
import time
import warnings
from pathlib import Path
from types import CodeType

import pytest

from outils import EXEMPLES, lancer, lire
from upea.compilateur import NOM_FICHIER, compiler, executer_arbre, transpiler
from upea.erreurs import ErreurExecution
from upea.generateur_ast import GenerateurAst, compiler_module
from upea.prelude import PRELUDE


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


def test_compiler_l_arbre_ne_laisse_passer_aucun_syntaxwarning() -> None:
    # `(3)[0]`, accepté sans types : CPython avertirait « perhaps you missed a comma? ».
    with warnings.catch_warnings(record=True) as avertissements:
        warnings.simplefilter("always")
        with pytest.raises(ErreurExecution):
            executer_arbre("faaite (3)[0];", types=False)
    assert [a for a in avertissements if a.category is SyntaxWarning] == []


def test_le_texte_produit_se_relit_avec_la_meme_structure(exemple: Path) -> None:
    module = module_de(lire(exemple))
    relu = ast.parse(ast.unparse(module))
    assert ast.dump(relu) == ast.dump(module)


# --- Le prélude en cache --------------------------------------------------------------


def generer_sans_cache(source: str) -> tuple[str, dict[int, int]]:
    """Le code et la correspondance des lignes, tout recalculé : prélude analysé,
    réécrit et relu avec le programme. C'est la référence du cache."""
    compilation = compiler(source, types=False)
    prelude = ast.parse(PRELUDE)
    utilisateur = GenerateurAst().module(compilation.programme, compilation.analyse)
    complet = ast.Module(body=[*prelude.body, *utilisateur.body], type_ignores=[])
    code = ast.unparse(complet) + "\n"
    relu = ast.parse(code).body[len(prelude.body) :]
    lignes: dict[int, int] = {}
    for original, nouveau in zip(utilisateur.body, relu, strict=True):
        for a, b in zip(ast.walk(original), ast.walk(nouveau), strict=True):
            if isinstance(a, ast.stmt) and isinstance(b, ast.stmt):
                lignes.setdefault(b.lineno, a.lineno)
    return code, lignes


def genere(source: str) -> tuple[str, dict[int, int]]:
    sortie = transpiler(source, "ast", types=False)
    return sortie.code, sortie.sourcemap.lignes


#: Des débuts de programme où le texte du programme seul se distinguerait de sa
#: place après le prélude : une fonction (précédée d'une ligne vide), un texte seul
#: (qu'`ast.unparse` écrirait comme une docstring en tête de module).
DEBUTS = [
    "ohipa f(n) {\n    hoi n + 1;\n}\nfaaite f(1);",
    '"abc";\nfaaite 1;',
    "tuu x = 1;\nohipa g() { }\ng();",
]


@pytest.mark.parametrize("source", DEBUTS)
def test_le_cache_du_prelude_donne_le_meme_code(source: str) -> None:
    assert genere(source) == generer_sans_cache(source)


def test_le_cache_du_prelude_donne_le_meme_code_pour_les_exemples(
    exemple: Path,
) -> None:
    assert genere(lire(exemple)) == generer_sans_cache(lire(exemple))


def test_generer_deux_fois_puis_un_autre_programme() -> None:
    a, b = lire(EXEMPLES / "02_fibonacci.upea"), lire(EXEMPLES / "04_tumu.upea")
    premiere, seconde, autre = genere(a), genere(a), genere(b)
    assert premiere == seconde == generer_sans_cache(a)
    assert autre == generer_sans_cache(b)
    assert lancer(a, "ast") == lire(EXEMPLES / "02_fibonacci.attendu")


def test_generer_avec_le_backend_ast_ne_refait_pas_le_prelude() -> None:
    genere("faaite 1;")  # la première fois remplit le cache
    debut = time.perf_counter()
    genere("faaite 2;")
    assert time.perf_counter() - debut < 0.02  # 85 ms sans cache


def test_le_texte_complet_contient_le_prelude() -> None:
    code = transpiler("faaite 1;", "ast").code
    assert "class _Tumu" in code
    compile(code, "<test>", "exec")
