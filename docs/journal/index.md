# Journal du projet

Ce dossier garde la trace de la démarche : les plans de travail successifs, et l'audit
du « conseil ». Ce sont des documents de travail, rédigés pendant le développement et
adressés à Thomas (d'où la deuxième personne). Chacun dit en tête à quel commit il
s'arrête ; aucun n'est plus tenu à jour. L'état actuel du projet est dans le
[README](../../README.md) et dans [`NOTES.md`](../../NOTES.md).

## Chronologie

D'après `git log`, en 2026 :

| Date | Ce qui s'est passé | Commits |
|---|---|---|
| 3 novembre | les premières versions du compilateur (v0 à v1.1), puis le plan d'un premier audit | `bbca8d1` à `c694f95`, puis `9dc63d7` ([`PLAN.md`](PLAN.md)) |
| 4 novembre | les corrections de cet audit, notamment les fins de ligne, `roto`, les `tumu` profonds, la sortie UTF-8, les propriétés `hypothesis`, le prélude externe et le test différentiel des backends ; puis le README | `e94a9ff` à `9f2ce74` |
| 4 novembre | le serveur MCP, lot par lot : squelette, atelier, bac à sable et son plafond de mémoire, outils, signatures des prédéfinies, ressources, prompts, tests de bout en bout, documentation | `ceb03b4` à `c9a5961` ([`PLAN_MCP.md`](PLAN_MCP.md)) |
| 5 novembre | la CI (GitHub Actions) et mypy sur toutes les plateformes ; puis l'audit du conseil, sur ce commit | `ce53700` ([rapport](conseil/RAPPORT-FINAL.md)) |
| 5 et 6 novembre | les corrections retenues par le conseil : L1, M1 à M6, L2, L4, L5, L6 | `dd46173` à `498adfe`, puis `5e64cfa` ([`PLAN_ETAPE3.md`](PLAN_ETAPE3.md), écrit en `6d64da9`) |
| 6 novembre | la livraison : nettoyage, code mort, outils MCP manquants, docstrings, mise en forme, test de la documentation, documentation | à partir de `82a815c` ([`PLAN_LIVRAISON.md`](PLAN_LIVRAISON.md)) |

## Les documents

| Document | Ce qu'il contient | Arrêté au commit |
|---|---|---|
| [`PLAN.md`](PLAN.md) | le premier audit d'Upea, et le plan de ses corrections | `9dc63d7` |
| [`PLAN_MCP.md`](PLAN_MCP.md) | ce que le SDK `mcp` v2 demande, l'architecture du serveur, ses lots et ses décisions (D1 à D11) | `c9a5961` |
| [`PLAN_ETAPE3.md`](PLAN_ETAPE3.md) | le plan des corrections du conseil, lot par lot, avec leurs mesures | `6d64da9` |
| [`PLAN_LIVRAISON.md`](PLAN_LIVRAISON.md) | le plan de la livraison, l'inventaire du dépôt, et la liste de contrôle de livraison | le dernier commit |

## Le conseil

Le 5 novembre, six agents de Claude Code (un architecte du langage, un ingénieur
compilateur, un spécialiste des arbres et des graphes, un testeur, un linguiste et un
sceptique) ont audité le commit `ce53700`, en deux phases, avec un débat
contradictoire. Leur [rapport final](conseil/RAPPORT-FINAL.md) classe les problèmes par
gravité (M1 à M9 majeurs, L1 à L10 mineurs) ; sa première ligne dit ce qui a été
corrigé depuis. La [fiche de départ](conseil/00-brief.md) est l'état des lieux remis
aux agents. Les rapports intermédiaires et le débat intégral ne sont pas livrés.

## L'exercice final du projet MCP

Une première session, où une IA qui ne connaissait pas Upea a échoué à traduire un
programme Python, a mené à une série de corrections (les outils `aide` et `exemples`,
des conseils dans les messages d'erreur). Le [journal de l'exercice](exercice-final/index.md)
la raconte, garde le [rapport de la session 1](exercice-final/session-1-rapport.md),
prépare la session 2, et réserve la place des observations de l'auteur (voir aussi
[`NOTES.md`](../../NOTES.md)).
