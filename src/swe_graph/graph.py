"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing & routing user queries, generating research plans to answer user questions,
conducting research, and formulating responses.
"""

from typing import Any, Dict, Literal, TypedDict, cast

from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from swe_graph.analyser_sub_graph.state import AnalyzerState
from swe_graph.configuration import AgentConfiguration
from swe_graph.analyser_sub_graph.graph import graph as analyze_requirement_graph
from swe_graph.monorepo_sub_graph.graph import graph as monorepo_creation_graph
from swe_graph.development_sub_graph.graph import graph as development_and_testing_graph
from swe_graph.researcher_graph.graph import graph as researcher_graph
from swe_graph.review_and_documentation_sub_graph.graph import (
    graph as review_documentation_graph,
)


from swe_graph.state import AgentState, InputState, Router
from shared.utils import format_docs, load_chat_model
from langgraph.checkpoint.memory import MemorySaver


async def analyze_requirements(agent_state: InputState) -> Dict[str, Any]:
    """Analyze requirements using the analyzer graph."""

    initial_state = {
        "messages": agent_state.messages,
        "requirements": {},
        "tech_specs": {},
        "architecture": {},
        "monorepo_structure": {},
        "tasks": [],
        "current_phase": "initial",
        "human_feedback": "continue",
        "next_node": "",
        "steps": [],
    }

    result = await analyze_requirement_graph.ainvoke(initial_state)

    return {
        "requirements": result["requirements"],
        "monorepo_config": {
            "structure": result["monorepo_structure"],
            "tech_specs": result["tech_specs"],
            "architecture": result["architecture"],
        },
        "tasks": [{"name": task, "status": "pending"} for task in result["tasks"]],
        # "tasks": result["tasks"],
        "messages": result["messages"],
    }


async def monorepo_creation(state: AgentState) -> dict[str, Any]:
    """Execute monorepo setup subgraph."""
    initial_state = {
        "monorepo_config": state.monorepo_config,
        "requirements": state.requirements,
        "current_phase": "setup",
        "human_feedback": "continue",
        "next_node": "",
        "steps": [],
    }

    result = await monorepo_creation_graph.ainvoke(initial_state)
    return {
        "monorepo_config": result.get("monorepo_config", {}),
        "messages": result.get("messages", []),
    }


async def development_and_testing(state: AgentState) -> dict[str, Any]:
    """Execute development and testing subgraph."""
    initial_state = {
        "tasks": state.tasks,
        "monorepo_config": state.monorepo_config,
        "requirements": state.requirements,
        "current_phase": "development",
        "human_feedback": "continue",
    }

    result = await development_and_testing_graph.ainvoke(initial_state)
    return {
        "code_artifacts": result["code_artifacts"],
        "test_cases": result["test_cases"],
        "messages": result["messages"],
    }


async def review_documentation(state: AgentState) -> dict[str, Any]:
    """Execute documentation subgraph."""
    initial_state = {
        "code_artifacts": state.code_artifacts,
        "requirements": state.requirements,
        "current_phase": "documentation",
        "human_feedback": "continue",
    }

    result = await review_documentation_graph.ainvoke(initial_state)
    return {"documentation": result["documentation"], "messages": result["messages"]}


# Define the graph
builder = StateGraph(AgentState, input=InputState, config_schema=AgentConfiguration)  # type: ignore
builder.add_node(analyze_requirements)
builder.add_node(monorepo_creation)
builder.add_node(development_and_testing)
# builder.add_node(researcher_graph)
builder.add_node(review_documentation)


builder.add_edge(START, "analyze_requirements")
builder.add_edge("analyze_requirements", "monorepo_creation")
builder.add_edge("monorepo_creation", "development_and_testing")
builder.add_edge("development_and_testing", "review_documentation")
builder.add_edge("review_documentation", END)

memory = MemorySaver()
# Compile into a graph object that you can invoke and deploy.
graph = builder.compile(checkpointer=memory)
graph.name = "SWEGraph"
