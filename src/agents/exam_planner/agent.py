"""Squelette de l'agent exam_planner (LangGraph + RAG + SLM).

À compléter : récupération ciblée des syllabus, priorités de révision
et planification déterministe dans tools.py.
"""

import os
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage, SystemMessage
from langchain_ollama import ChatOllama

from src.core.base_agent import BaseAgentPlugin
from src.core.ingestion import get_vector_store
from src.core.state import AgentState

from .tools import format_exam_planning_response, process_exam_planning


class ExamPlannerPlugin(BaseAgentPlugin):
    """Planificateur de révisions respectant le contrat BaseAgentPlugin."""

    @property
    def name(self) -> str:
        """Identifiant utilisé par le superviseur LangGraph."""
        return "exam_planner"

    @property
    def description(self) -> str:
        """Intentions prises en charge par le planificateur de révisions."""
        return (
            "Planificateur d'emploi du temps de révision et de préparation aux examens. "
            "Organise les créneaux d'étude selon les échéances, les disponibilités, "
            "les modalités d'évaluation et le niveau de maîtrise de l'étudiant."
        )

    def create_node(self) -> Callable[[AgentState], dict[str, Any]]:
        """Retourne la fonction exécutable (nœud LangGraph) de l'agent."""
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        model_name = os.getenv("OLLAMA_LLM_MODEL", "qwen2.5:3b")

        llm = ChatOllama(base_url=ollama_url, model=model_name, temperature=0.1, num_predict=400)
        vector_store = None

        def node(state: AgentState) -> dict[str, Any]:
            nonlocal vector_store
            if vector_store is None:
                vector_store = get_vector_store(reindex_if_empty=False)

            # Extraction du dernier message reçu
            last_message = state["messages"][-1]
            user_query = str(last_message.content)

            # Étape 1 : RAG ciblé avec filtres de métadonnées (k <= 2 pour SLM 3B)
            # TODO: Ajuster vos filtres ChromaDB (ex: {"code_ue": "..."}, {"semestre": "S8"})
            relevant_docs = []
            try:
                retriever = vector_store.as_retriever(search_kwargs={"k": 2})
                relevant_docs = retriever.invoke(user_query)
            except Exception:
                relevant_docs = []

            rag_context = (
                "\n---\n".join([doc.page_content for doc in relevant_docs])
                if relevant_docs
                else "Aucun document spécifique trouvé."
            )

            # Étape 2 : Exécution des outils Python déterministes (Règle d'or SLM)
            # TODO: Calculer les priorités et construire un planning vérifié dans tools.py.
            tool_results = process_exam_planning(user_query, relevant_docs)

            # Étape 3 : Synthèse par le SLM avec Prompt Système défensif
            system_prompt = (
                f"Tu es l'agent spécialisé '{self.name}'.\n"
                "Ton rôle est d'apporter une réponse rigoureuse, concise et factuelle à l'étudiant.\n\n"
                "RÈGLES STRICTES :\n"
                "1. Base-toi EXCLUSIVEMENT sur les éléments du Contexte RAG et les Résultats des Outils fournis ci-dessous.\n"
                "2. N'invente aucun cours, code d'UE ou prérequis non présent dans les données.\n"
                "3. Si l'information est absente ou insuffisante, reconnais-le explicitement.\n"
                "4. Reste concis (maximum 3 à 5 phrases claires).\n\n"
                f"CONTEXTE RAG :\n{rag_context}\n\n"
                f"RÉSULTATS DES OUTILS PYTHON :\n{tool_results}"
            )

            messages = [
                SystemMessage(content=system_prompt),
                last_message,
            ]

            try:
                response = llm.invoke(messages)
                response_text = str(response.content)
            except Exception:
                # Fallback défensif en cas d'indisponibilité temporaire du SLM
                response_text = format_exam_planning_response(tool_results)

            # Préfixage obligatoire avec l'identifiant pour la traçabilité
            final_message = AIMessage(content=f"[{self.name}] {response_text}")

            return {
                "messages": [final_message],
                "current_agent": self.name,
            }

        return node
