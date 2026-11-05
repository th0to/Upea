"""Conseil, lot M2 : les entiers ont une précision illimitée, à l'affichage aussi.

Python refuse par défaut de convertir en texte (et depuis un texte) un entier de plus
de 4 300 chiffres. La limite est levée dans le prélude (exécution, fichier autonome)
et dans le parser (les littéraux sont convertis avant tout prélude).
"""

import subprocess
import sys
from pathlib import Path

from upea import atelier, bac_a_sable
from upea.cli import OK, main
from upea.compilateur import transpiler

FACTORIELLE = """\
ohipa factorielle(n: numera) -> numera {
    tuu r = 1;
    tataitahi i roto 2..=n { r = r * i; }
    hoi r;
}
faaite roa(parau(factorielle(2000)));
"""

LITTERAL = "faaite roa(parau(" + "1" * 5000 + "));\n"
CONVERSION = 'faaite roa(parau(numera("' + "7" * 5000 + '")));\n'


def test_l_affichage_d_un_grand_entier() -> None:
    resultat = bac_a_sable.executer(FACTORIELLE)
    assert resultat.statut == "succes", resultat.rapport
    assert resultat.sortie == "5736\n"  # 2000! a 5 736 chiffres


def test_la_conversion_d_un_long_texte() -> None:
    resultat = bac_a_sable.executer(CONVERSION)
    assert resultat.statut == "succes", resultat.rapport
    assert resultat.sortie == "5000\n"


def test_un_long_litteral() -> None:
    resultat = bac_a_sable.executer(LITTERAL)
    assert resultat.statut == "succes", resultat.rapport
    assert resultat.sortie == "5000\n"
    assert atelier.verifier(LITTERAL).valide
    assert "1" * 5000 in transpiler(LITTERAL).code


def test_le_fichier_autonome(tmp_path: Path) -> None:
    source = tmp_path / "factorielle.upea"
    source.write_text(FACTORIELLE, encoding="utf-8")
    sortie = tmp_path / "factorielle.py"
    assert main(["transpile", str(source), "-o", str(sortie)]) == OK
    resultat = subprocess.run(
        [sys.executable, str(sortie)],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        timeout=60,
    )
    assert resultat.stdout == "5736\n", resultat.stderr[-2000:]
