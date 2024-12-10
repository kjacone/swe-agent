"""Researcher graph used in the conversational retrieval system as a subgraph.

This module defines the core structure and functionality of the researcher graph,
which is responsible for generating search queries and retrieving relevant documents.
"""

from typing import Any, Dict, TypedDict, cast

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from swe_graph.configuration import AgentConfiguration
from swe_graph.researcher_graph.state import QueryState, ResearcherState
from shared import retrieval
from shared.utils import load_chat_model
from swe_graph.review_and_documentation_sub_graph.nodes import (
    generate_api_docs,
    generate_user_guides,
    generate_developer_docs,
    generate_deployment_guides,
    compile_release_notes,
    review_documentation,
)
from swe_graph.review_and_documentation_sub_graph.state import DocumentationState
from swe_graph.state import AgentState


def human_review(state: DocumentationState) -> Dict[str, Any]:
    """Handle human review checkpoint."""
    if state.human_feedback == "continue":
        return {"current_phase": state.current_phase, "next_node": state.next_node}
    elif state.human_feedback == "end":
        return {"current_phase": "ended", "next_node": "end"}
    else:
        return {"current_phase": state.current_phase, "next_node": state.human_feedback}


def router(state: DocumentationState) -> str:
    """Route to next node based on human feedback and errors."""
    if state.errors:
        return "human_review"
    elif state.human_feedback == "end":
        return END
    elif state.human_feedback == "continue":
        return state.next_node
    else:
        return state.human_feedback


# Create documentation subgraph
builder = StateGraph(DocumentationState)

# Add nodes
builder.add_node("generate_api_docs", generate_api_docs)
builder.add_node("generate_user_guides", generate_user_guides)
builder.add_node("generate_developer_docs", generate_developer_docs)
builder.add_node("generate_deployment_guides", generate_deployment_guides)
builder.add_node("compile_release_notes", compile_release_notes)
builder.add_node("review_documentation", review_documentation)
builder.add_node("human_review", human_review)

# Add edges
builder.add_edge(START, "generate_api_docs")
builder.add_conditional_edges("generate_api_docs", router)
builder.add_conditional_edges("generate_user_guides", router)
builder.add_conditional_edges("generate_developer_docs", router)
builder.add_conditional_edges("generate_deployment_guides", router)
builder.add_conditional_edges("compile_release_notes", router)
builder.add_conditional_edges("review_documentation", router)
builder.add_conditional_edges("human_review", router)

# Set up memory and compile
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["human_review"])
graph.name = "DocumentationGraph"
