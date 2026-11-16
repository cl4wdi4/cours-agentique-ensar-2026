"""Outils Python déterministes pour l'agent exam_planner.

RÈGLE D'OR DE L'INGÉNIERIE SLM :
Tout calcul arithmétique, manipulation d'ensembles, algorithme de graphe,
validation de format JSON ou parsing par regex DOIT être exécuté en pur Python ici.
Ne laissez jamais le SLM faire des additions ou des détections de cycles.
"""

from typing import Any


def process_exam_planning(query: str, retrieved_docs: list[Any]) -> dict[str, Any]:
    """TODO: Implémenter la logique de planification des révisions.

    À développer : validation de la demande, extraction des informations d'examen,
    calcul des priorités, répartition du temps, génération et validation du planning.
    Le retour actuel est celui du squelette : aucun planning n'est encore calculé.

    Args:
        query: Texte de la question de l'étudiant
        retrieved_docs: Chunks documentaires extraits par ChromaDB

    Returns:
        Dictionnaire contenant les données chiffrées ou vérifiées.
    """
    return {
        "status": "success",
        "documents_analyzed": len(retrieved_docs),
        "summary": "Données traitées avec succès par les outils Python déterministes.",
    }


def format_exam_planning_response(tool_results: dict[str, Any]) -> str:
    """Génère une réponse formatée de secours si le SLM n'est pas disponible."""
    summary = tool_results.get("summary", "")
    analyzed = tool_results.get("documents_analyzed", 0)
    return f"Traitement effectué : {summary} ({analyzed} document(s) analysé(s))."
