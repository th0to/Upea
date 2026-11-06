"""Des stratégies `hypothesis` : des programmes Upea, et des littéraux à relire.

Les programmes sont petits et se terminent toujours (pas de `tamau`, des boucles
sur des valeurs connues) ; toute opération composée est parenthésée, pour que le
formateur ait des parenthèses inutiles à retirer sans jamais changer le sens.
"""

from hypothesis import strategies as st

from upea.formateur import texte_upea

type Strategie = st.SearchStrategy[str]

#: Des textes qui demandent des échappements.
TEXTES: Strategie = st.text(alphabet='ab "\\\n\té', max_size=4).map(texte_upea)

# --- Les programmes -------------------------------------------------------------------

#: Les variables que déclare le début de chaque programme.
ENTETE = (
    'tuu a = 3;\ntuu b = 2.5;\ntuu c = "ia";\ntuu l = [1, 2];\n'
    "tuu t = tumu(1, tumu(2));\ntuu g = upea { 1 -> 2 };\n"
)
NOMS = ["a", "b", "c", "l", "t", "g", "t.hotu"]

#: Des entiers petits : `"ab" * 9 * 9 * 9` reste raisonnable.
ATOMES: Strategie = st.one_of(
    st.integers(0, 9).map(str),
    st.sampled_from(["0.5", "2.0", "tia", "hape", "aore", "[]", *NOMS]),
    TEXTES,
)

BINAIRES = ["+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">="]
BINAIRES += ["roto", "ma", "anei"]


def _composees(sous: Strategie) -> Strategie:
    return st.one_of(
        st.tuples(sous, st.sampled_from(BINAIRES), sous).map(
            lambda e: f"({e[0]} {e[1]} {e[2]})"
        ),
        st.tuples(st.sampled_from(["-", "eiaha "]), sous).map(
            lambda e: f"({e[0]}{e[1]})"
        ),
        st.lists(sous, max_size=3).map(lambda es: f"[{', '.join(es)}]"),
        st.tuples(sous, st.integers(-2, 2)).map(lambda e: f"({e[0]})[{e[1]}]"),
        sous.map(lambda e: f"({e})"),
    )


EXPRESSIONS: Strategie = st.recursive(ATOMES, _composees, max_leaves=6)


def instructions(profondeur: int) -> Strategie:
    """Une instruction ; les blocs s'imbriquent sur `profondeur` niveaux. Chaque
    niveau a sa variable de boucle (pas de masquage)."""
    faaite = st.lists(EXPRESSIONS, min_size=1, max_size=2).map(
        lambda es: f"faaite {', '.join(es)};"
    )
    if profondeur == 0:
        return faaite
    bloc = st.lists(instructions(profondeur - 1), max_size=2).map(
        lambda corps: "{ " + " ".join(corps) + " }"
    )
    i = f"i{profondeur}"
    return st.one_of(
        faaite,
        st.tuples(EXPRESSIONS, bloc, bloc).map(
            lambda e: f"ahani {e[0]} {e[1]} taae {e[2]}"
        ),
        st.tuples(st.integers(0, 3), bloc).map(
            lambda e: f"tataitahi {i} roto 0..{e[0]} {e[1]}"
        ),
        st.tuples(st.sampled_from([*NOMS, "3", "[]"]), bloc).map(
            lambda e: f"tataitahi {i} roto {e[0]} {e[1]}"
        ),
    )


PROGRAMMES: Strategie = st.lists(instructions(2), min_size=1, max_size=4).map(
    lambda suite: ENTETE + "\n".join(suite) + "\n"
)

# --- Les littéraux de structures ------------------------------------------------------

#: Des décimaux finis quelconques, écrits comme Python les affiche (`1e-05`, `1e+16`) :
#: leur forme compacte doit se relire (conseil, L2).
DECIMAUX: Strategie = st.floats(allow_nan=False, allow_infinity=False).map(repr)

NOEUDS: Strategie = st.one_of(st.integers(-3, 9).map(str), TEXTES, DECIMAUX)
POIDS: Strategie = st.one_of(
    st.integers(-5, 5).map(str), st.sampled_from(["0.5", "-2.5", "1.0"]), DECIMAUX
)


def _arete(e: tuple[str, str | None, str, str | None]) -> str:
    depart, fleche, arrivee, poids = e
    if fleche is None:
        return depart  # un nœud seul
    return f"{depart} {fleche} {arrivee}" + ("" if poids is None else f" : {poids}")


GRAPHES: Strategie = st.lists(
    st.tuples(
        NOEUDS, st.sampled_from(["->", "<->", None]), NOEUDS, st.none() | POIDS
    ).map(_arete),
    max_size=6,
).map(lambda aretes: "upea { " + ", ".join(aretes) + " }")

VALEURS_DE_NOEUD: Strategie = st.one_of(
    st.integers(-3, 9).map(str),
    TEXTES,
    st.sampled_from(["aore", "tia", "[1, 2]", "[]"]),
)

TUMU: Strategie = st.recursive(
    VALEURS_DE_NOEUD.map(lambda v: f"tumu({v})"),
    lambda enfants: st.tuples(
        VALEURS_DE_NOEUD, st.lists(enfants, min_size=1, max_size=3)
    ).map(lambda e: f"tumu({', '.join([e[0], *e[1]])})"),
    max_leaves=8,
)

SORTES = ["imi", "aifaito", "uteere", "ahu", "ahunui", "pupu", "pupu 4", "pupu 5"]

#: Des clés toutes numériques ou toutes textuelles : un arbre ordonné ne les mêle pas.
CLES: st.SearchStrategy[list[str]] = st.one_of(
    st.lists(st.integers(-20, 20).map(str), max_size=12),
    st.lists(TEXTES, max_size=8),
)

ORDONNES: Strategie = st.tuples(st.sampled_from(SORTES), CLES).map(
    lambda e: f"{e[0]} [{', '.join(e[1])}]"
)
