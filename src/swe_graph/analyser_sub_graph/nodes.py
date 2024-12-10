from typing import Annotated, Any, Literal, TypedDict, List, Dict, Optional, cast
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from shared.utils import load_chat_model
from swe_graph.analyser_sub_graph.state import AnalyzerState
from swe_graph.configuration import AgentConfiguration


async def extract_requirements(
    state: AnalyzerState, *, config: RunnableConfig
) -> Dict[str, Any]:
    """Extract requirements from the user's input message."""
    current_step = len(state.steps)
    if current_step >= len(state.steps):
        state.steps.append({"description": "extract_requirements", "update": []})

    class Response(TypedDict):
        requirements: Dict[str, List[str]]
        current_phase: Literal["initial"]

    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model).with_structured_output(Response)
    messages = [
        {"role": "system", "content": configuration.extract_requirements_prompt}
    ] + state.messages

    extracted: Response = cast(Response, await model.ainvoke(messages))

    if state.human_feedback == "extract_requirements":
        state.steps[current_step]["update"] = ["Human input extract_requirements"]
        state.human_feedback = ""
        return {
            "steps": state.steps,
            "tech_specs": extracted["requirements"],
            "current_phase": "extract_requirements to human_review",
            "next_node": "human_review",
            "human_feedback": "",
        }

    state.steps[current_step]["update"].append("Requirements extracted")

    return {
        "steps": state.steps,
        "requirements": extracted["requirements"],
        "current_phase": "requirements_extracted",
        "next_node": "generate_tech_specs",
    }


async def generate_tech_specs(state: AnalyzerState) -> Dict[str, Any]:
    """Generate technical specifications based on requirements."""
    print("Generating technical specifications for state:")
    current_step = len(state.steps)
    if current_step >= len(state.steps):
        state.steps.append({"description": "generate_tech_specs", "update": []})

    tech_specs = {
        "authentication": "OAuth 2.0 with JWT",
        "data_processing": "Apache Kafka",
        "backup": "AWS S3 with automated scripts",
    }

    if state.human_feedback == "generate_tech_specs":
        state.human_feedback = ""
        state.steps[current_step]["update"] = ["human input generate_tech_specs"]
        return {
            "steps": state.steps,
            "tech_specs": tech_specs,
            "current_phase": "tech_specs_generated to human_review",
            "next_node": "human_review",
            "human_feedback": "",
        }

    state.steps[current_step]["update"].append("tech spec generated")

    return {
        "steps": state.steps,
        "tech_specs": tech_specs,
        "current_phase": "tech_specs_generated",
        "next_node": "design_architecture",
    }


async def design_architecture(state: AnalyzerState) -> Dict[str, Any]:
    """Design system architecture based on requirements and specifications."""
    print("Designing system architecture for state:")
    current_step = len(state.steps)
    if current_step >= len(state.steps):
        state.steps.append({"description": "design_architecture", "update": []})

    architecture = {
        "frontend": "React with TypeScript",
        "backend": "FastAPI",
        "database": "PostgreSQL",
        "message_queue": "Kafka",
    }

    if state.human_feedback == "design_architecture":
        state.human_feedback = ""
        state.steps[current_step]["update"] = ["human input design_architecture"]
        return {
            "steps": state.steps,
            "tech_specs": architecture,
            "current_phase": "design_architecture to human_review",
            "next_node": "human_review",
            "human_feedback": "",
        }

    state.steps[current_step]["update"].append("architecture designed")

    return {
        "steps": state.steps,
        "architecture": architecture,
        "current_phase": "architecture_designed",
        "next_node": "generate_monorepo",
    }


async def generate_monorepo(state: AnalyzerState) -> Dict[str, Any]:
    """Generate monorepo structure based on architecture design."""
    print("Generating monorepo structure for state:")
    current_step = len(state.steps)
    if current_step >= len(state.steps):
        state.steps.append({"description": "generate_monorepo", "update": []})

    monorepo_structure = {
        "frontend": ["src", "components", "pages", "tests"],
        "backend": ["api", "services", "models", "tests"],
        "common": ["utils", "types", "constants"],
    }

    if state.human_feedback == "generate_monorepo":
        state.human_feedback = ""
        state.steps[current_step]["update"] = ["human input generate_monorepo"]
        return {
            "steps": state.steps,
            "tech_specs": monorepo_structure,
            "current_phase": "generate_monorepo to human_review",
            "next_node": "human_review",
            "human_feedback": "",
        }

    state.steps[current_step]["update"].append("monorepo structure generated")

    return {
        "steps": state.steps,
        "monorepo_structure": monorepo_structure,
        "current_phase": "monorepo_structured",
        "next_node": "generate_tasks",
    }


async def generate_tasks(state: AnalyzerState) -> Dict[str, Any]:
    """Generate development tasks based on all previous analysis."""
    print("Generating tasks for state:")
    current_step = len(state.steps)
    if current_step >= len(state.steps):
        state.steps.append({"description": "generate_tasks", "update": []})

    tasks = [
        "Set up authentication service",
        "Implement real-time data processing pipeline",
        "Configure automated backup system",
    ]

    if state.human_feedback == "generate_tasks":
        state.human_feedback = ""
        state.steps[current_step]["update"] = ["human input generate_tasks"]
        return {
            "steps": state.steps,
            "tech_specs": tasks,
            "current_phase": "generate_tasks to human_review",
            "next_node": "human_review",
            "human_feedback": "",
        }

    state.steps[current_step]["update"].append("tasks generated")

    return {
        "steps": state.steps,
        "tasks": tasks,
        "current_phase": "tasks_generated",
        "next_node": "human_review",
    }
