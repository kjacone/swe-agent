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
from swe_graph.development_sub_graph.nodes import (
    generate_tests,
    implement_code,
    plan_development,
    run_tests,
    refactor_code,
)
from swe_graph.development_sub_graph.state import DevelopmentState
from swe_graph.researcher_graph.state import QueryState, ResearcherState
from shared import retrieval
from shared.utils import load_chat_model
from swe_graph.state import AgentState


def human_review(state: DevelopmentState) -> Dict[str, Any]:
    """Handle human review checkpoint."""
    if state.human_feedback == "continue":
        return {"current_phase": state.current_phase, "next_node": state.next_node}
    elif state.human_feedback == "end":
        return {"current_phase": "ended", "next_node": "end"}
    else:
        return {"current_phase": state.current_phase, "next_node": state.human_feedback}


def router(state: DevelopmentState) -> str:
    """Route to next node based on human feedback and errors."""
    if state.errors:
        return "human_review"
    elif state.human_feedback == "end":
        return END
    elif state.human_feedback == "continue":
        return state.next_node
    else:
        return state.human_feedback


# Create development subgraph
builder = StateGraph(DevelopmentState)

# Add nodes
builder.add_node("plan_development", plan_development)
builder.add_node("generate_tests", generate_tests)
builder.add_node("implement_code", implement_code)
builder.add_node("run_tests", run_tests)
builder.add_node("refactor_code", refactor_code)
builder.add_node("human_review", human_review)

# Add edges
builder.add_edge(START, "plan_development")
builder.add_conditional_edges("plan_development", router)
builder.add_conditional_edges("generate_tests", router)
builder.add_conditional_edges("implement_code", router)
builder.add_conditional_edges("run_tests", router)
builder.add_conditional_edges("refactor_code", router)
builder.add_conditional_edges("human_review", router)


from langgraph.checkpoint.memory import MemorySaver

# Set up memory and compile
memory = MemorySaver()
graph = builder.compile(checkpointer=memory, interrupt_before=["human_review"])
graph.name = "DevelopmentGraph"
