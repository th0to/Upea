"""Étape 10 : le `Protocol` Backend, le formateur, et `mypy --strict`."""

import subprocess
import sys
from pathlib import Path

import pytest

from outils import EXEMPLES, PROJET, lire
from upea.backend import Backend, Sortie
from upea.cli import ERREUR_COMPILATION, ERREUR_USAGE, OK, main
from upea.compilateur import (
    BACKENDS,
    choisir_backend,
    executer,
    mettre_en_forme,
    transpiler,
)
from upea.erreurs import ErreurUpea
from upea.noeuds import Programme, parcourir
from upea.parser import parse
from upea.semantique import Analyse


def test_les_backends_disponibles() -> None:
    assert sorted(BACKENDS) == ["ast", "formateur", "python"]
    assert [b.executable for b in (BACKENDS["python"], BACKENDS["ast"])] == [True, True]


def test_un_backend_inconnu_est_refuse_avec_un_message_clair() -> None:
    with pytest.raises(ErreurUpea) as info:
        choisir_backend("cobol")
    assert info.value.message == (
        "backend inconnu : 'cobol' (disponibles : ast, formateur, python)"
    )


class CompteurInstructions:
    """Un backend écrit dans le test : il n'hérite de rien."""

    nom = "compteur"
    extension = ".txt"
    executable = False

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        noms = [type(n).__name__ for n in parcourir(programme)]
        return Sortie(f"{noms.count('Affiche')} faaite, {noms.count('Pour')} boucles")


def test_un_nouveau_backend_n_a_besoin_que_du_protocol(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    backend: Backend = CompteurInstructions()  # vérifié par mypy
    monkeypatch.setitem(BACKENDS, backend.nom, backend)
    sortie = transpiler(lire(EXEMPLES / "02_fibonacci.upea"), "compteur")
    assert sortie.code == "6 faaite, 4 boucles"


def test_le_formateur_preserve_l_arbre(exemple: Path) -> None:
    source = lire(exemple)
    assert parse(mettre_en_forme(source)) == parse(source)


def test_le_formateur_est_idempotent(exemple: Path) -> None:
    une_fois = mettre_en_forme(lire(exemple))
    assert mettre_en_forme(une_fois) == une_fois


def test_un_programme_mal_presente_est_remis_en_forme() -> None:
    laid = 'tuu   x=(1+2)*3 ;ahani x>2{faaite x ,"grand";}taae{faaite((x));}'
    assert mettre_en_forme(laid) == (
        "tuu x = (1 + 2) * 3;\n"
        "ahani x > 2 {\n"
        '    faaite x, "grand";\n'
        "} taae {\n"
        "    faaite x;\n"
        "}\n"
    )


@pytest.mark.parametrize(
    ("source", "formate"),
    [
        ("faaite (1 + 2) * 3, 1 + (2 * 3);", "faaite (1 + 2) * 3, 1 + 2 * 3;"),
        ("faaite ((x));", "faaite x;"),
        ("faaite a - (b - c), (a - b) - c;", "faaite a - (b - c), a - b - c;"),
        ("faaite (a < b) == c, a == (b < c);", "faaite (a < b) == c, a == (b < c);"),
        (
            "faaite eiaha (a == b), eiaha (a ma b);",
            "faaite eiaha a == b, eiaha (a ma b);",
        ),
        ("faaite -(a + b), -(a.hotu), (-a) * b;", "faaite -(a + b), -a.hotu, -a * b;"),
        (
            "faaite (a + b)[0], (f(x)).hotu, (1).hotu;",
            "faaite (a + b)[0], f(x).hotu, (1).hotu;",
        ),
        (
            "faaite (a ma b) anei c, a ma (b anei c);",
            "faaite a ma b anei c, a ma (b anei c);",
        ),
        ("faaite (x roto l) ma (eiaha y);", "faaite x roto l ma eiaha y;"),
        ("faaite - (-a), a - (-b);", "faaite --a, a - -b;"),
    ],
)
def test_le_formateur_ne_garde_que_les_parentheses_utiles(
    source: str, formate: str
) -> None:
    assert mettre_en_forme(source) == formate + "\n"
    assert parse(formate) == parse(source)


@pytest.mark.parametrize(
    ("source", "formate"),
    [
        (r'faaite "il a dit \"oui\"\n";', r'faaite "il a dit \"oui\"\n";'),
        (r'faaite "a\tb\\c";', r'faaite "a\tb\\c";'),
        ("faaite 1.5, 2.0, 0.000001;", "faaite 1.5, 2.0, 0.000001;"),
        ("faaite 100000000000000000000.0;", "faaite 100000000000000000000.0;"),
        ("faaite tia, hape, aore, [];", "faaite tia, hape, aore, [];"),
    ],
)
def test_les_litteraux_sont_reecrits_correctement(source: str, formate: str) -> None:
    assert mettre_en_forme(source) == formate + "\n"
    assert parse(mettre_en_forme(source)) == parse(source)


def test_un_petit_graphe_tient_sur_une_ligne() -> None:
    source = 'tuu g = upea {1->2:3,"a"<->"b"};'
    assert mettre_en_forme(source) == 'tuu g = upea { 1 -> 2 : 3, "a" <-> "b" };\n'


def test_un_grand_graphe_s_ecrit_une_arete_par_ligne() -> None:
    source = "ahani tia { tuu g = upea { 1 -> 2, 2 -> 3, 3 -> 1 }; }"
    assert mettre_en_forme(source) == (
        "ahani tia {\n"
        "    tuu g = upea {\n"
        "        1 -> 2,\n"
        "        2 -> 3,\n"
        "        3 -> 1,\n"
        "    };\n"
        "}\n"
    )


def test_les_fonctions_sont_separees_par_une_ligne_vide() -> None:
    source = 'tuu x = 1; ohipa f(a: numera, b) -> parau { hoi ""; } faaite f(x, 2);'
    assert mettre_en_forme(source) == (
        "tuu x = 1;\n\n"
        "ohipa f(a: numera, b) -> parau {\n"
        '    hoi "";\n'
        "}\n\n"
        "faaite f(x, 2);\n"
    )


def test_les_boucles_et_les_chaines_de_conditions() -> None:
    source = (
        'tataitahi i roto 0..=n{faaea;}tataitahi m roto g mai "A" aano{haere;}'
        "ahani a{}taae ahani b{faaite;}taae{hoi;}"
    )
    assert mettre_en_forme(source) == (
        "tataitahi i roto 0..=n {\n    faaea;\n}\n"
        'tataitahi m roto g mai "A" aano {\n    haere;\n}\n'
        "ahani a {\n} taae ahani b {\n    faaite;\n} taae {\n    hoi;\n}\n"
    )


def test_le_formateur_est_un_backend_non_executable() -> None:
    assert transpiler("faaite  1;", "formateur").code == "faaite 1;\n"
    with pytest.raises(ErreurUpea, match="ne produit pas de Python exécutable"):
        executer("faaite 1;", "formateur")


def test_run_refuse_le_formateur(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "p.upea"
    fichier.write_text("faaite 1;", encoding="utf-8")
    assert main(["run", str(fichier), "--backend", "formateur"]) == ERREUR_USAGE
    assert "ne produit pas de Python exécutable" in capsys.readouterr().err


def test_fmt_affiche_et_fmt_ecrire_reecrit_le_fichier(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fichier = tmp_path / "laid.upea"
    fichier.write_text("faaite  ( 1+2 ) ;", encoding="utf-8")
    assert main(["fmt", str(fichier)]) == OK
    assert capsys.readouterr().out == "faaite 1 + 2;\n"
    assert fichier.read_text(encoding="utf-8") == "faaite  ( 1+2 ) ;"
    assert main(["fmt", str(fichier), "--ecrire"]) == OK
    assert fichier.read_text(encoding="utf-8") == "faaite 1 + 2;\n"


def test_fmt_refuse_un_programme_faux(tmp_path: Path) -> None:
    fichier = tmp_path / "faux.upea"
    fichier.write_text("faaite (1;", encoding="utf-8")
    assert main(["fmt", str(fichier)]) == ERREUR_COMPILATION


def test_mypy_strict_passe_sur_le_paquet() -> None:
    resultat = subprocess.run(
        [sys.executable, "-m", "mypy", "--strict", str(PROJET / "upea")],
        cwd=PROJET.parent,
        capture_output=True,
        text=True,
    )
    assert resultat.returncode == 0, resultat.stdout
