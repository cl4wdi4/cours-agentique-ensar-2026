"""Répartition du temps de révision entre les UE.

Ce module reçoit des scores calculés par le module de priorités.
Les durées sont exprimées en minutes entières.
"""

from math import isfinite


def allocate_revision_time(
    priority_scores: dict[str, float],
    total_minutes: int,
) -> dict[str, int]:
    """Répartit un budget de révision proportionnellement aux scores de priorité associé aux UE souhaités

    Args:
        priority_scores: Association entre chaque code UE et son score numérique de priorité,
            fini, positif ou nul. Au moins un score doit être strictement positif.
        total_minutes: Budget total en minutes entières, strictement positif.

    Notes:
        Après le calcul des durées théoriques, int(minutes) conserve uniquement
        la partie entière de chaque durée. Les minutes restantes sont calculées
        en soustrayant la somme de ces durées entières au budget total.
        Elles sont ensuite attribuées une par une aux UE ayant les plus grands
        restes décimaux, jusqu'à épuisement du budget.
        L'instruction return allocated_minutes retourne la répartition finale.

    Returns:
        Minutes de révision attribuées à chaque UE, avec les mêmes clés qu'en entrée.
        La somme doit être égale au budget et les UE à scores nuls reçoivent zéro minute.
        En cas d'égalité des restes décimaux, l'ordre des UE fourni est conservé.

    Raises:
        ValueError: Budget non entier, nul ou négatif, score invalide, dictionnaire vide
            ou scores tous nuls. Les booléens ne sont pas acceptés comme nombres.

    Exemple attendu :
    scores {"SD_212": 3.0, "SSI_212": 1.0}
    + budget de 600 minutes
    donnent {"SD_212": 450, "SSI_212": 150}.

    Un budget nul est rejeté : aucune répartition ne peut être utile dans ce cas.
    """
    # Étape 1 : Vérification de la validité des entrées
    if type(total_minutes) is not int or total_minutes <= 0:
        raise ValueError(
            "Le temps disponible pour réviser doit être un entier strictement positif, en minutes."
        )

    if not priority_scores:
        raise ValueError("Il faut fournir au moins une UE visée et son score.")

    for code_ue, score in priority_scores.items():
        if (
            isinstance(score, bool)
            or not isinstance(score, (int, float))
            or not isfinite(score)
            or score < 0
        ):
            raise ValueError(f"Le score de {code_ue} doit être un nombre fini positif ou nul.")

    if not any(score > 0 for score in priority_scores.values()):
        raise ValueError("Au moins une UE doit avoir un score strictement positif.")

    # Étape 2 : Calculer les minutes théoriques de chaque UE, sans arrondir.
    total_score = sum(priority_scores.values())
    theoretical_minutes: dict[str, float] = {}

    for code_ue, score in priority_scores.items():
        theoretical_minutes[code_ue] = total_minutes * score / total_score

    # Étape 3 : Garder la partie entière de chaque durée.
    allocated_minutes: dict[str, int] = {}
    for code_ue, minutes in theoretical_minutes.items():
        allocated_minutes[code_ue] = int(minutes)

    remaining_minutes = total_minutes - sum(allocated_minutes.values())

    # Les UE aux plus grands restes décimaux reçoivent une minute supplémentaire.
    ordered_ues = sorted(
        theoretical_minutes,
        key=lambda code_ue: theoretical_minutes[code_ue] - allocated_minutes[code_ue],
        reverse=True,
    )
    for code_ue in ordered_ues[:remaining_minutes]:
        allocated_minutes[code_ue] += 1

    # Étape 4 : Retourner la répartition en minutes entières.
    return allocated_minutes
