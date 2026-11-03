"""Extension 13 : les source maps, ligne Python ↔ ligne Upea."""

import json
from pathlib import Path

import pytest

from outils import EXEMPLES, lire
from upea.cli import OK, main
from upea.compilateur import executer, transpiler
from upea.erreurs import ErreurExecution
from upea.prelude import PRELUDE
from upea.sourcemap import SourceMap, SourceMapJSON

PROFOND = """\
ohipa interieure(l) {
    hoi l[5];
}
ohipa exterieure() {
    hoi interieure([1]);
}
faaite exterieure();
"""


@pytest.mark.parametrize("backend", ["python", "ast"])
def test_chaque_ligne_issue_du_programme_a_une_ligne_source(
    exemple: Path, backend: str
) -> None:
    source = lire(exemple)
    sortie = transpiler(source, backend)
    nombre = len(source.splitlines())
    assert sortie.sourcemap.lignes
    for ligne_python, ligne_source in sortie.sourcemap.lignes.items():
        assert 1 <= ligne_source <= nombre
        assert sortie.code.splitlines()[ligne_python - 1].strip()


def test_toutes_les_lignes_apres_le_prelude_sont_couvertes(exemple: Path) -> None:
    sortie = transpiler(lire(exemple))
    lignes = sortie.code.splitlines()
    debut = (
        len(PRELUDE.splitlines()) + 3
    )  # le prélude, deux lignes vides, le séparateur
    for numero in range(debut + 1, len(lignes) + 1):
        assert sortie.sourcemap.ligne_source(numero) is not None, lignes[numero - 1]


def test_les_lignes_du_prelude_n_ont_pas_de_ligne_source() -> None:
    sortie = transpiler(lire(EXEMPLES / "02_fibonacci.upea"))
    for numero in range(1, len(PRELUDE.splitlines()) + 1):
        assert sortie.sourcemap.ligne_source(numero) is None


def test_la_ligne_d_une_fonction_correspond_a_sa_declaration() -> None:
    for backend in ("python", "ast"):
        sortie = transpiler(lire(EXEMPLES / "02_fibonacci.upea"), backend)
        lignes = sortie.code.splitlines()
        numero = next(
            i for i, texte in enumerate(lignes, 1) if texte.startswith("def fibo")
        )
        assert sortie.sourcemap.ligne_source(numero) == 2


@pytest.mark.parametrize("backend", ["python", "ast"])
def test_une_erreur_au_fond_des_appels_pointe_la_ligne_la_plus_profonde(
    backend: str,
) -> None:
    with pytest.raises(ErreurExecution) as info:
        executer(PROFOND, backend)
    assert info.value.position is not None
    assert info.value.position.ligne == 2


def test_l_aller_retour_json_redonne_la_meme_source_map() -> None:
    carte = SourceMap("p.upea", {10: 1, 12: 3})
    donnees = carte.vers_json()
    assert donnees == {"version": 1, "source": "p.upea", "lignes": {"10": 1, "12": 3}}
    relue = SourceMap.depuis_json(json.loads(json.dumps(donnees)))
    assert relue == carte


def test_une_version_inconnue_est_refusee() -> None:
    donnees: SourceMapJSON = {"version": 2, "source": "p", "lignes": {}}  # type: ignore[typeddict-item]
    with pytest.raises(ValueError, match="version de source map inconnue"):
        SourceMap.depuis_json(donnees)


def test_decaler_ne_touche_qu_aux_lignes_python() -> None:
    carte = SourceMap("p", {1: 5, 4: 7})
    assert carte.decaler(10) == SourceMap("p", {11: 5, 14: 7})
    assert carte == SourceMap("p", {1: 5, 4: 7})  # l'original est intact


def test_ecrire_puis_lire_un_fichier(tmp_path: Path) -> None:
    carte = SourceMap("p.upea", {3: 1})
    chemin = tmp_path / "p.py.map.json"
    carte.ecrire(chemin)
    assert SourceMap.lire(chemin) == carte


def test_transpile_sourcemap_ecrit_un_json_a_cote_du_fichier(tmp_path: Path) -> None:
    exemple = EXEMPLES / "02_fibonacci.upea"
    sortie = tmp_path / "fibo.py"
    commande = ["transpile", str(exemple), "-o", str(sortie), "--sourcemap"]
    assert main(commande) == OK
    donnees = json.loads((tmp_path / "fibo.py.map.json").read_text(encoding="utf-8"))
    assert donnees["version"] == 1
    assert donnees["source"] == str(exemple)
    carte = SourceMap.depuis_json(donnees)
    lignes = sortie.read_text(encoding="utf-8").splitlines()
    numero = next(
        i for i, texte in enumerate(lignes, 1) if texte.startswith("def factorielle")
    )
    assert carte.ligne_source(numero) == 9


def test_sourcemap_sans_fichier_de_sortie_est_refuse(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert main(["transpile", str(EXEMPLES / "01_ia_ora_na.upea"), "--sourcemap"]) == 2
    assert "-o" in capsys.readouterr().err
