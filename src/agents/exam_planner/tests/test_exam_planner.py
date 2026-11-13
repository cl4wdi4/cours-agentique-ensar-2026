"""Tests du squelette exam_planner avec simulation du modèle et du RAG.

Ces tests s'exécutent en < 100 ms via pytest, sans GPU ni connexion réseau.
"""

from unittest.mock import MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from ..agent import ExamPlannerPlugin
from ..tools import format_exam_planning_response, process_exam_planning


@pytest.fixture
def agent():
    return ExamPlannerPlugin()


def test_exam_planner_properties(agent):
    """Vérifie le respect du contrat BaseAgentPlugin."""
    assert agent.name == "exam_planner"
    assert agent.name == agent.name.lower(), "Le nom doit être en minuscules"
    assert " " not in agent.name, "Le nom ne doit pas contenir d'espaces"
    assert len(agent.description) >= 15, "La description doit comporter au moins 15 caractères"
    assert callable(agent.create_node()), "create_node() doit retourner une fonction"


def test_exam_planning_placeholder():
    """Vérifie le comportement de l'outil déterministe."""
    mock_docs = [MagicMock(page_content="Cours IA")]
    res = process_exam_planning("requête test", mock_docs)
    assert isinstance(res, dict)
    assert res["status"] == "success"
    assert res["documents_analyzed"] == 1
    fallback = format_exam_planning_response(res)
    assert "1 document(s)" in fallback


@patch("src.agents.exam_planner.agent.ChatOllama")
@patch("src.agents.exam_planner.agent.get_vector_store")
def test_exam_planner_node_execution(mock_get_vector_store, mock_chat_ollama, agent):
    """Vérifie le flux d'exécution du nœud LangGraph avec mock du SLM et de ChromaDB."""
    # Mocking du Document ChromaDB
    mock_doc = MagicMock()
    mock_doc.metadata = {"code_ue": "SD_212", "section_title": "4. Modalités d’Évaluation"}
    mock_doc.page_content = "Épreuve terminale écrite : 50%."

    mock_retriever = MagicMock()
    mock_retriever.invoke.return_value = [mock_doc]

    mock_vector_store = MagicMock()
    mock_vector_store.as_retriever.return_value = mock_retriever
    mock_get_vector_store.return_value = mock_vector_store

    # Mocking du LLM Ollama
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.return_value = AIMessage(content="Réponse synthétisée par l'agent.")
    mock_chat_ollama.return_value = mock_llm_instance

    node = agent.create_node()
    state = {
        "messages": [HumanMessage(content="Aide-moi à organiser mes révisions pour SD_212.")],
        "next_agent": None,
        "current_agent": None,
        "context_data": {},
    }

    output = node(state)

    assert "messages" in output
    assert len(output["messages"]) == 1
    assert output["current_agent"] == agent.name
    assert f"[{agent.name}]" in output["messages"][0].content
