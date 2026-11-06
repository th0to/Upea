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

Sécurité (`mcp/etapes/04_execution.md` du cours). Un programme Upea ne peut que
calculer et afficher : le langage n'a ni import, ni clavier, ni fichiers, ni réseau
(`specification.md`, *Limites assumées*). Et rien, dans un programme, ne devient du
Python que le compilateur n'a pas prévu :

- un texte entre dans le code généré par `repr` (ou un `ast.Constant`) :
  `"\\"); import os; (\\""` reste un texte, affiché tel quel ;
- un commentaire s'arrête au lexer ;
- un identifiant ne commence jamais par `_` (le lexer le refuse) : le prélude, dont
  tous les noms commencent par `_`, est hors d'atteinte, ses imports compris ;
- un nom non déclaré est refusé avant l'exécution, avec ou sans les types : `open`,
  `eval` ou `globals` n'atteignent jamais Python. Un nom de Python déclaré dans le
  programme (`tuu print = 3;`) devient une variable renommée (`_v_print`) ;
- un champ ne peut être que `hotu` ou `amaa`.

Ce que le bac à sable ajoute, pour ce qu'un programme valide peut faire de mal : un
délai, une sortie plafonnée, une mémoire et un temps CPU bornés (un *job object*
sous Windows, `setrlimit` ailleurs ; macOS n'applique pas la limite de mémoire), un
processus séparé (le serveur survit à un plantage), et un environnement réduit (les
variables du serveur n'atteignent pas l'enfant).

Ce qu'il ne protège pas : l'enfant a les droits de l'utilisateur qui lance le
serveur. Si une faille du compilateur laissait passer du Python arbitraire, il
pourrait lire les fichiers et le réseau : il faudrait alors un vrai bac à sable
(un conteneur, un utilisateur dédié, un filtre des appels système).
"""

from __future__ import annotations

import io
import json
import math
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
#: La mémoire d'un programme, interpréteur compris (en octets) : sans plafond, un
#: texte doublé à chaque tour occupe plusieurs Go avant la fin du délai.
PLAFOND_MEMOIRE = 512 * 1024**2
#: Le temps CPU de l'enfant, en multiple du délai : une seconde barrière, si le parent
#: meurt avant de l'arrêter (le temps CPU ne dépasse jamais le temps réel).
MULTIPLE_CPU = 2
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
    """Le résultat d'une exécution dans le bac à sable (l'outil `executer`)."""

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
    """Le programme a dépassé son délai, et l'enfant a été tué ; `sortie` est ce
    qu'il avait affiché avant."""

    def __init__(self, delai: float, sortie: str, tronquee: bool) -> None:
        super().__init__(
            f"délai de {delai:g} s dépassé : le programme a été arrêté "
            "(une boucle sans fin ?)"
        )
        self.sortie = sortie  # ce qu'il avait affiché avant
        self.tronquee = tronquee


class EnfantEnPanne(PanneDuBacASable):
    """L'enfant s'est arrêté sans rendre de résultat lisible."""

    pass


# --- Le parent ------------------------------------------------------------------------


def executer(
    source: str,
    *,
    types: bool = True,
    backend: str = "python",
    delai: float = DELAI,
    plafond: int = PLAFOND,
    memoire: int = PLAFOND_MEMOIRE,
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
        "memoire": memoire,
        "delai": delai,
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
        if b"MemoryError" in erreurs:
            # L'enfant n'a même pas pu rédiger son résultat : la mémoire était pleine.
            return _memoire_depassee(source, sortie, plafond, memoire)
        fin = _texte(erreurs).strip()[-FIN_DES_ERREURS:]
        raise EnfantEnPanne(
            f"le sous-processus s'est arrêté sans résultat (code {enfant.returncode})"
            + (f" :\n{fin}" if fin else "")
        )
    try:
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
    except (ValueError, KeyError, TypeError) as illisible:
        raise EnfantEnPanne(f"résultat illisible ({illisible})") from None


def _message_memoire(memoire: int) -> str:
    return f"mémoire dépassée : un programme a au plus {memoire // 1024**2} Mo"


def _memoire_depassee(
    source: str, sortie: bytes, plafond: int, memoire: int
) -> Execution:
    """Le résultat d'un enfant mort de `MemoryError` sans avoir rien rendu."""
    erreur = ErreurExecution(_message_memoire(memoire))
    return Execution(
        statut="erreur_execution",
        code_retour=3,
        sortie=_texte(sortie[:plafond]),
        tronquee=len(sortie) > plafond - 4,
        octets=len(sortie),
        diagnostics=diagnostics(erreur),
        rapport=rapport([erreur], source),
    )


def _environnement() -> dict[str, str]:
    """L'environnement de l'enfant, réduit au nécessaire : le paquet `upea`
    importable, de l'UTF-8 partout, et jamais de couleurs.

    Rien n'est hérité du serveur : ses variables (un jeton d'API de l'hôte, par
    exemple) n'atteignent pas le programme. L'enfant est lancé par le chemin absolu
    de l'interpréteur (`sys.executable`) : il n'a pas besoin de `PATH`. Sous Windows,
    `SYSTEMROOT` est gardé, comme le demande la documentation de `subprocess`.
    """
    environnement = {
        "PYTHONPATH": str(RACINE),
        "PYTHONUTF8": "1",
        "PYTHONIOENCODING": "utf-8",
        "NO_COLOR": "1",
    }
    if sys.platform == "win32" and "SYSTEMROOT" in os.environ:
        environnement["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
    return environnement


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


def _plafonner(octets: int, secondes: float) -> bool:
    """Borne la mémoire de ce processus (au-delà, une allocation lève `MemoryError`) et
    son temps CPU (au-delà, le système l'arrête : si le parent meurt, l'enfant ne
    tourne pas sans fin).

    Rend `False` si la mémoire ne peut pas être bornée (le programme tourne alors sans
    plafond de mémoire).
    """
    if sys.platform == "win32":
        return _job_windows(octets, secondes)
    else:
        import resource

        cpu = math.ceil(secondes)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu + 1))
        # Le `else` sert à mypy : sous Linux, un `return` après le `if` serait
        # « unreachable » (warn_unreachable).
        if sys.platform == "linux":
            resource.setrlimit(resource.RLIMIT_AS, (octets, octets))
            return True
        else:  # macOS n'applique pas RLIMIT_AS
            return False


def _job_windows(octets: int, secondes: float) -> bool:
    """Place ce processus dans un *job object* qui limite sa mémoire et son temps
    CPU (en mode utilisateur)."""
    # Jamais appelée ailleurs que sous Windows : ce test sert à mypy, qui, sous
    # Linux ou macOS, ne connaît pas ctypes.WinDLL et saute alors le `else`. Le
    # `else` est nécessaire : du code après le `return` serait « unreachable »
    # (warn_unreachable).
    if sys.platform != "win32":
        return False
    else:
        import ctypes
        from ctypes import wintypes

        class Limites(ctypes.Structure):  # JOBOBJECT_BASIC_LIMIT_INFORMATION
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64),
                ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD),
                ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t),
                ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t),
                ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD),
            ]

        class LimitesEtendues(ctypes.Structure):  # JOBOBJECT_EXTENDED_LIMIT_INFORMATION
            _fields_ = [
                ("Basic", Limites),
                ("IoInfo", ctypes.c_uint64 * 6),  # IO_COUNTERS
                ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t),
            ]

        job_object_limit_process_time = 0x2
        job_object_limit_process_memory = 0x100
        job_object_extended_limit_information = 9
        poignee = wintypes.HANDLE
        noyau = ctypes.WinDLL("kernel32", use_last_error=True)
        noyau.CreateJobObjectW.restype = poignee
        noyau.GetCurrentProcess.restype = poignee  # une pseudo-poignée : -1
        noyau.SetInformationJobObject.argtypes = [
            poignee,
            ctypes.c_int,
            ctypes.c_void_p,
            wintypes.DWORD,
        ]
        noyau.AssignProcessToJobObject.argtypes = [poignee, poignee]
        limites = LimitesEtendues()
        limites.Basic.LimitFlags = (
            job_object_limit_process_memory | job_object_limit_process_time
        )
        limites.ProcessMemoryLimit = octets
        # En unités de 100 ns.
        limites.Basic.PerProcessUserTimeLimit = int(secondes * 10_000_000)
        # La poignée du job reste ouverte jusqu'à la fin du processus.
        job = noyau.CreateJobObjectW(None, None)
        return bool(
            job
            and noyau.SetInformationJobObject(
                job,
                job_object_extended_limit_information,
                ctypes.byref(limites),
                ctypes.sizeof(limites),
            )
            and noyau.AssignProcessToJobObject(job, noyau.GetCurrentProcess())
        )


def _executer_ici(
    source: str, types: bool, backend: str, memoire: int
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
    except ErreursMultiples as echec:  # CPython refuse le code généré : le filet
        return "erreur_compilation", 1, [*signales, echec]
    except ErreurExecution as erreur:
        if erreur.message == compilateur.MEMOIRE_EPUISEE:
            erreur = ErreurExecution(_message_memoire(memoire), erreur.position)
        return "erreur_execution", 3, [*signales, erreur]
    return "succes", 0, signales


def _enfant() -> int:
    requete = json.loads(sys.stdin.buffer.read())
    sys.stdin.close()
    if not _plafonner(requete["memoire"], MULTIPLE_CPU * requete["delai"]):
        print("upea : pas de plafond de mémoire sur ce système", file=sys.stderr)
    canal = sys.stdout.buffer
    sortie = _SortiePlafonnee(canal, requete["plafond"])
    sys.stdout = sortie
    source = requete["source"]
    statut, code, signales = _executer_ici(
        source, requete["types"], requete["backend"], requete["memoire"]
    )
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
    # En ASCII : une demi-paire de substitution venue du source (U+D800) s'écrit
    # avec un échappement JSON, et ne casse pas le résultat.
    canal.write(json.dumps(resultat, ensure_ascii=True).encode("ascii"))
    canal.flush()
    return 0


if __name__ == "__main__":
    sys.exit(_enfant())
