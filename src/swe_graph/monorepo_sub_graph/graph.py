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
from swe_graph.monorepo_sub_graph.nodes import (
    setup_cicd,
    setup_dependencies,
    setup_directory_structure,
    setup_tooling,
)
from swe_graph.monorepo_sub_graph.state import MonorepoState
from swe_graph.researcher_graph.state import QueryState, ResearcherState
from shared import retrieval
from shared.utils import load_chat_model
from swe_graph.state import AgentState


def human_review(state: MonorepoState) -> Dict[str, Any]:
    """Handle human review checkpoint."""
    if state.human_feedback == "continue":
        return {"current_phase": state.current_phase, "next_node": state.next_node}
    elif state.human_feedback == "end":
        return {"current_phase": "ended", "next_node": "end"}
    else:
        return {"current_phase": state.current_phase, "next_node": state.human_feedback}


def router(state: MonorepoState) -> str:
    """Route to next node based on human feedback and errors."""
    if state.errors:
        return "human_review"
    elif state.human_feedback == "end":
        return END
    elif state.human_feedback == "continue":
        return state.next_node
    else:
        return state.human_feedback


# Create monorepo subgraph
builder = StateGraph(MonorepoState)

# Add nodes
builder.add_node("setup_directory_structure", setup_directory_structure)
builder.add_node("setup_tooling", setup_tooling)
builder.add_node("setup_dependencies", setup_dependencies)
builder.add_node("setup_cicd", setup_cicd)
builder.add_node("human_review", human_review)

# Add edges
builder.add_edge(START, "setup_directory_structure")
builder.add_conditional_edges("setup_directory_structure", router)
builder.add_conditional_edges("setup_tooling", router)
builder.add_conditional_edges("setup_dependencies", router)
builder.add_conditional_edges("setup_cicd", router)
builder.add_conditional_edges("human_review", router)


from langgraph.checkpoint.memory import MemorySaver

# Set up memory and compile
memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["human_review"])
graph.name = "MonorepoGraph"
