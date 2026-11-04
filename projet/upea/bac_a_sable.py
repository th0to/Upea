"""Le bac à sable (extension 18) : exécuter un programme Upea dans un sous-processus,
avec un délai et une sortie plafonnée. Le code à exécuter vient d'une IA.

Le parent (`executer`) lance `python -m upea.bac_a_sable` et lui passe la requête en
JSON sur son entrée standard, qu'il ferme aussitôt : pas de fichier temporaire à
supprimer si l'enfant est tué, et un programme Upea ne sait pas lire son entrée.

L'enfant écrit ce qu'affiche le programme sur sa sortie standard, en vidant chaque
écriture (la sortie déjà écrite survit à l'arrêt de l'enfant), jusqu'au plafond.
Puis il écrit un marqueur, tiré au hasard par le parent pour cette exécution, suivi
du résultat en JSON. Le programme ne connaît pas le marqueur : il ne peut pas imiter
le résultat.
"""

from __future__ import annotations

import io
import json
import os
import secrets
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import BinaryIO, Literal

from . import compilateur
from .atelier import Diagnostic, diagnostics, rapport
from .erreurs import ErreurExecution, ErreursMultiples, ErreurUpea

#: Le délai d'une exécution, démarrage de Python compris (en secondes).
DELAI = 5.0
#: Ce qu'on garde au plus de la sortie d'un programme (en octets UTF-8).
PLAFOND = 64 * 1024
#: Ce que l'on garde au plus de la sortie d'erreur d'un enfant en panne.
FIN_DES_ERREURS = 2000

BACKENDS = ("python", "ast")

#: Le dossier qui contient le paquet `upea`.
RACINE = Path(__file__).resolve().parent.parent
COMMANDE = [sys.executable, "-m", "upea.bac_a_sable"]

type Statut = Literal["succes", "erreur_compilation", "erreur_execution"]


# Pas de `slots`, comme les résultats de l'atelier : ce résultat est celui d'un outil.
@dataclass(frozen=True)
class Execution:
    statut: Statut
    code_retour: int  # comme `python -m upea run` : 0, 1 (compilation), 3 (exécution)
    sortie: str  # ce que le programme a affiché, au plus `PLAFOND` octets
    tronquee: bool
    octets: int  # la taille de toute la sortie, même tronquée
    diagnostics: tuple[Diagnostic, ...]  # avertissements, puis l'erreur éventuelle
    rapport: str


class PanneDuBacASable(Exception):
    """L'exécution n'a pas pu aller à son terme : ce n'est pas une erreur d'Upea."""


class DelaiDepasse(PanneDuBacASable):
    def __init__(self, delai: float, sortie: str, tronquee: bool) -> None:
        super().__init__(
            f"délai de {delai:g} s dépassé : le programme a été arrêté "
            "(une boucle sans fin ?)"
        )
        self.sortie = sortie  # ce qu'il avait affiché avant
        self.tronquee = tronquee


class EnfantEnPanne(PanneDuBacASable):
    pass


# --- Le parent ------------------------------------------------------------------------


def executer(
    source: str,
    *,
    types: bool = True,
    backend: str = "python",
    delai: float = DELAI,
    plafond: int = PLAFOND,
) -> Execution:
    """Exécute `source` dans un sous-processus.

    Une erreur de compilation ou d'exécution est un résultat. Lève `DelaiDepasse`
    si le programme ne finit pas à temps, `EnfantEnPanne` si le sous-processus
    meurt sans rendre de résultat.
    """
    if backend not in BACKENDS:
        raise ValueError(f"le backend '{backend}' ne produit pas de Python exécutable")
    marqueur = secrets.token_hex(16).encode("ascii")
    requete = {
        "source": source,
        "types": types,
        "backend": backend,
        "plafond": plafond,
        "marqueur": marqueur.decode("ascii"),
    }
    enfant = subprocess.Popen(
        COMMANDE,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=RACINE,
        env=_environnement(),
        # Sous Windows, un serveur lancé sans console (Claude Desktop) en ouvrirait
        # une pour chaque enfant.
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    # La sortie de l'enfant est bornée par son plafond ; `communicate` peut tout lire.
    try:
        sortie, erreurs = enfant.communicate(
            json.dumps(requete).encode("utf-8"), timeout=delai
        )
    except subprocess.TimeoutExpired:
        enfant.kill()
        sortie, _ = enfant.communicate()
        # Arrêté avant d'avoir écrit son résultat : tout est sortie du programme.
        # L'enfant s'arrête au plafond, ou juste avant pour ne pas couper un caractère.
        tronquee = len(sortie) > plafond - 4
        raise DelaiDepasse(delai, _texte(sortie), tronquee) from None
    position = sortie.rfind(marqueur)
    if position < 0:
        fin = _texte(erreurs).strip()[-FIN_DES_ERREURS:]
        raise EnfantEnPanne(
            f"le sous-processus s'est arrêté sans résultat (code {enfant.returncode})"
            + (f" :\n{fin}" if fin else "")
        )
    resultat = json.loads(sortie[position + len(marqueur) :])
    return Execution(
        statut=resultat["statut"],
        code_retour=resultat["code_retour"],
        sortie=_texte(sortie[:position]),
        tronquee=resultat["tronquee"],
        octets=resultat["octets"],
        diagnostics=tuple(Diagnostic(**d) for d in resultat["diagnostics"]),
        rapport=resultat["rapport"],
    )


def _environnement() -> dict[str, str]:
    """L'environnement de l'enfant : le paquet `upea` importable, de l'UTF-8 partout,
    et jamais de couleurs."""
    environnement = dict(os.environ)
    environnement.pop("FORCE_COLOR", None)
    chemins = [str(RACINE), environnement.get("PYTHONPATH", "")]
    return environnement | {
        "PYTHONPATH": os.pathsep.join(filter(None, chemins)),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "NO_COLOR": "1",
    }


def _texte(octets: bytes) -> str:
    return octets.decode("utf-8", errors="replace")


# --- L'enfant -------------------------------------------------------------------------


class _SortiePlafonnee(io.TextIOBase):
    """Le `sys.stdout` du programme : transmet et vide chaque écriture jusqu'au
    plafond, sans couper de caractère, puis ne fait plus que compter."""

    def __init__(self, canal: BinaryIO, plafond: int) -> None:
        self.canal = canal
        self.plafond = plafond
        self.ecrits = 0
        self.octets = 0
        self.tronquee = False

    def writable(self) -> bool:
        return True

    def write(self, texte: str) -> int:
        donnees = texte.encode("utf-8")
        self.octets += len(donnees)
        if self.tronquee:  # rien ne passe après une coupure, même plus court
            return len(texte)
        if self.ecrits + len(donnees) > self.plafond:
            self.tronquee = True
            reste = donnees[: self.plafond - self.ecrits]
            donnees = reste.decode("utf-8", errors="ignore").encode("utf-8")
        if donnees:
            self.canal.write(donnees)
            self.canal.flush()
            self.ecrits += len(donnees)
        return len(texte)


def _executer_ici(
    source: str, types: bool, backend: str
) -> tuple[Statut, int, list[ErreurUpea]]:
    """Exécute le programme dans ce processus : son statut, le code de retour de la
    CLI, et ses avertissements et erreurs."""
    try:
        signales: list[ErreurUpea] = list(
            compilateur.compiler(source, types=types).analyse.avertissements
        )
    except ErreursMultiples as echec:
        return "erreur_compilation", 1, [echec]
    try:
        compilateur.executer(source, backend, types=types)
    except ErreurExecution as erreur:
        return "erreur_execution", 3, [*signales, erreur]
    return "succes", 0, signales


def _enfant() -> int:
    requete = json.loads(sys.stdin.buffer.read())
    sys.stdin.close()
    canal = sys.stdout.buffer
    sortie = _SortiePlafonnee(canal, requete["plafond"])
    sys.stdout = sortie
    source = requete["source"]
    statut, code, signales = _executer_ici(source, requete["types"], requete["backend"])
    texte = rapport(signales, source)
    if sortie.tronquee:
        texte += (
            f"\nsortie tronquée : {sortie.ecrits} octets montrés sur {sortie.octets}"
        )
    resultat = {
        "statut": statut,
        "code_retour": code,
        "tronquee": sortie.tronquee,
        "octets": sortie.octets,
        "diagnostics": [asdict(d) for e in signales for d in diagnostics(e)],
        "rapport": texte,
    }
    canal.write(requete["marqueur"].encode("ascii"))
    canal.write(json.dumps(resultat, ensure_ascii=False).encode("utf-8"))
    canal.flush()
    return 0


if __name__ == "__main__":
    sys.exit(_enfant())
