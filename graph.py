from sub_graphs.swe.nodes.analyse_module import analyze_request
from sub_graphs.swe.nodes.code_module import code_module
from sub_graphs.swe.nodes.create_module import create_module
from sub_graphs.swe.nodes.general_response_module import generate_respond_to_query
from sub_graphs.swe.nodes.generate_path_module import generate_path
from sub_graphs.swe.nodes.planning_module import planner
from sub_graphs.swe.nodes.reflect_module import reflect
from langgraph.checkpoint.memory import MemorySaver
from sub_graphs.swe.project_data_state import (
    FileState,
)
from typing import Literal
from utils.logger import BRDLogger
from langgraph.graph import StateGraph, END, START
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_emit_state
from langchain_core.messages import SystemMessage
from config import Config
from dotenv import load_dotenv
import json
from langgraph.types import Command, interrupt

# Import nodes


memory = MemorySaver()
logger = BRDLogger()


async def process_feedback_node(state: FileState) -> Command[Literal["generate_path"]]:
    print("HITL:", state.get("hitl", {}))

    response = interrupt(state.get("hitl", {}))
    print("INTERRUPTED HITL:\n", response)

    try:
        if isinstance(response, str):
            hitl = json.loads(response)
        else:
            hitl = response

        print("USER_HITL:\n", hitl)
        match hitl["name"]:
            case "documentation":
                state["next_node"] = "planner"
                # state["follow_up"] = hitl["remarks"]
                state["hitl"] = {}
            case "planner":
                print("selected_sections_pfn:\n", hitl["selected_sections"])
                state["pending_sections"].clear()
                state["pending_sections"] = hitl["selected_sections"]
                state["next_node"] = "create_module"
                # state["follow_up"] = hitl["remarks"]
                state["hitl"] = {}
            case "create_module":
                state["next_node"] = "code_module"
                # state["follow_up"] = hitl["remarks"]
            case "success":
                print("Generation completed")
                state["next_node"] = "reflect"
                # state["follow_up"] = hitl["remarks"]
            case "error":
                state["follow_up"] = ""
    except Exception as e:
        print("Error processing feedback:\n", e)
        # state["follow_up"] = str(e)

    state["messages"] = [
        SystemMessage(
            content="User has reviewed the documents, please process their feedback and act accordingly."
        )
    ]
    # print("STATE:\n", state)
    return Command(goto="generate_path", update={**state})


# Clear state node to reset temporary workflow state
async def clear_state(state: FileState, config: RunnableConfig):
    """
    Clear temporary workflow state variables to prepare for the next iteration.
    This prevents state accumulation and potential conflicts.
    """
    logger.log("Clearing temporary workflow state...", section="clear_state")
    await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

    # List of temporary state variables to clear
    temp_vars = ["follow_up", "response"]

    # Create an update dictionary to clear temporary variables
    update = {var: None for var in temp_vars if var in state}

    # Preserve essential project state variables
    logger.log("Temporary state cleared", section="clear_state")
    await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

    # Return the update to apply to the state
    return update


# Create workflow
workflow = StateGraph(FileState)
workflow.add_node("generate_path", generate_path)
workflow.add_node("analyze_request", analyze_request)

workflow.add_node("planner", planner)
workflow.add_node("create_module", create_module)
workflow.add_node("code_module", code_module)
workflow.add_node("generate_respond_to_query", generate_respond_to_query)
# workflow.add_node("follow_up_node", follow_up_node)

workflow.add_node("reflect", reflect)
workflow.add_node("clear_state", clear_state)
workflow.add_node("process_feedback_node", process_feedback_node)

# Set entry point to generate_path
workflow.add_edge(START, "generate_path")
workflow.add_edge("clear_state", END)


# Compile the graph
graph = workflow.compile(checkpointer=memory)
# graph = workflow.compile()
