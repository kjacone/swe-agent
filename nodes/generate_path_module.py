# Generate path node to direct workflow based on input
from sub_graphs.swe.project_data_state import (
    FileState,
)

from typing import Literal
from utils.logger import BRDLogger
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
# from langchain_deepseek import ChatDeepSeek


logger = BRDLogger()


# Map keywords to nodes
path_mapping = {
    "analyze": "analyze_request",
    "process_feedback_node": "process_feedback_node",
    "planner": "planner",
    "code_module": "code_module",
    "generate_respond_to_query": "generate_respond_to_query",
    "reflect": "reflect",
    "create_module": "create_module",
    "clear_state": "clear_state",
}


async def generate_path(
    state: FileState, config: RunnableConfig
) -> Command[
    Literal[
        "analyze_request",
        "planner",
        "generate_respond_to_query",
        "create_module",
        "code_module",
        "reflect",
        "clear_state",
        "process_feedback_node",
    ]
]:
    # Logic to determine which node to go to based on state information
    user_input = state.get("next_node", "")
    # print("state generate_respond_to_query:/n", state)
    # Default to analyze_request if no specific path is determined
    next_node = "generate_respond_to_query"

    for keyword, node in path_mapping.items():
        if keyword.lower() in user_input.lower():
            next_node = node
            break
    print(f"Navigating to {next_node}")

    return Command(
        # state update
        update=state,
        # control flow
        goto=next_node,
    )
