# Generate response to general queries node
from sub_graphs.swe.project_data_state import (
    FileState,
)

from typing import Literal
from utils.logger import BRDLogger, LogLevel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_emit_state
from config import Config
import json
from langgraph.types import Command
from sub_graphs.swe.config import llm_mini, call_ai
# from langchain_deepseek import ChatDeepSeek


logger = BRDLogger()


generate_response_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a helpful assistant helping with project generation
            """,
        ),
        (
            "human",
            """
    Project Context: {query}       
    Previous Messages: {messages}""",
        ),
    ]
)
generate_response_chain = generate_response_prompt | llm_mini


async def generate_respond_to_query(
    state: FileState, config: RunnableConfig
) -> Command[Literal["generate_path"]]:
    """
    Generate general responses to queries that don't require specific project actions.
    """
    logger.log("Generating response to query...", section="response")
    await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

    messages = state.get("messages", "")
    project_context = {
        "project_name": state.get("project_name", ""),
        "project_summary": state.get("project_summary", ""),
        "analysis": state.get("analysis", ""),
        "files_created": len(state.get("files", [])),
        "project_progress": f"{state.get('processed_files', 0)}/{len(state.get('files', []))}",
    }

    try:
        formatted_query = f"Messages: {messages}\n\nProject Context: {json.dumps(project_context, indent=2)}"
        response = await call_ai(
            generate_response_chain,
            {"messages": messages, "query": formatted_query},
            config,
        )

        logger.log("Response generated successfully", section="response")
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

        return Command(
            goto="generate_path",
            update={
                "last_action": f"general query",
                "next_node": "clear_state",
                "messages": state.get("messages", []) + [response],
                "response": response.content,
            },
        )
    except Exception as e:
        print("generate_respond_to_query:\n", e)
        logger.log(
            f"Error generating response: {str(e)[:50]}",
            level=LogLevel.ERROR,
            section="response",
        )
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        hitl = {
            "name": "error",
            "title": "General Queries Agent",
            "description": f"An Error Occured: \n{str(e)[:500]}",
            "approved": False,
        }
        return Command(
            goto="generate_path",
            update={
                "hitl": hitl,
                "last_action": "general query",
                "next_node": "process_feedback_node",
                "response": f"I encountered an error while processing your request. {str(e)}",
            },
        )
