"""Le prélude d'exécution d'Upea, un module par famille de structures.

Ces modules sont recopiés, dans l'ordre de `prelude.MODULES`, en tête de chaque
fichier Python généré, qui reste ainsi autonome. Tous leurs noms commencent par
`_` : le lexer d'Upea interdit ce préfixe, aucun programme ne peut donc les
écraser. Les imports relatifs entre eux disparaissent à la concaténation.
"""
