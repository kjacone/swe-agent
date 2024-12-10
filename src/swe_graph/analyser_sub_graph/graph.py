"""Researcher graph used in the conversational retrieval system as a subgraph.

This module defines the core structure and functionality of the researcher graph,
which is responsible for generating search queries and retrieving relevant documents.
"""

from typing import Annotated, Any, Dict, List, TypedDict, cast

from langchain_core.documents import Document
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from swe_graph.analyser_sub_graph.state import AnalyzerState
from swe_graph.configuration import AgentConfiguration
from swe_graph.researcher_graph.state import QueryState, ResearcherState
from shared import retrieval
from shared.utils import load_chat_model
from swe_graph.state import AgentState
from swe_graph.analyser_sub_graph.nodes import (
    extract_requirements,
    generate_tech_specs,
    design_architecture,
    generate_monorepo,
    generate_tasks,
)

from typing import List


def human_review(state: AnalyzerState) -> Dict[str, Any]:
    """
    Function to handle human review of the current state.
    Returns a dictionary with updated state including the next step to rerun or continue.
    """

    human_feedback = state.human_feedback
    print(f"Human feedback: {human_feedback}")

    if human_feedback == "continue" or human_feedback == "":
        return {"current_phase": "same_state_no_human", "next_node": state.next_node}
    elif human_feedback == "end":
        state.next_node = "end"
        return {"current_phase": "human_ended", "next_node": state.next_node}
    else:
        state.next_node = human_feedback
        return {"current_phase": "human_responded", "next_node": state.next_node}


def router(state: AnalyzerState):
    """
    Routes the flow based on human review feedback.
    """
    if state.human_feedback == "continue" or state.human_feedback == "":
        print(f"Routing to {state.next_node}")
        return state.next_node
    elif state.human_feedback == "end":
        print("Routing to END")
        return END
    else:
        print(f"Routing to node: {state.human_feedback}")
        node: str = state.human_feedback
        return node


# Define the graph
builder = StateGraph(AnalyzerState)

# Add nodes
builder.add_node("extract_requirements", extract_requirements)
builder.add_node("generate_tech_specs", generate_tech_specs)
builder.add_node("design_architecture", design_architecture)
builder.add_node("generate_monorepo", generate_monorepo)
builder.add_node("generate_tasks", generate_tasks)
builder.add_node("human_review", human_review)


# Add edges
builder.add_edge(START, "extract_requirements")
builder.add_conditional_edges("extract_requirements", router)
builder.add_conditional_edges("generate_tech_specs", router)
builder.add_conditional_edges("design_architecture", router)
builder.add_conditional_edges("generate_monorepo", router)
builder.add_conditional_edges("generate_tasks", router)
builder.add_conditional_edges("human_review", router)
# builder.add_edge("human_review", END)


# Set up memory
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()

# Compile graph
graph = builder.compile(checkpointer=memory, interrupt_before=["human_review"])
graph.name = "AnalyzerGraph"
