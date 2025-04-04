# Reflect node to analyze progress and suggest improvements
# Planner node to create comprehensive project plans
from sub_graphs.configs.constants import (
    create_file_structure as async_create_file_structure,
)
from sub_graphs.swe.project_data_state import (
    FileInfo,
    FileState,
)

import re
from typing import Literal
from utils.logger import BRDLogger, LogLevel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_emit_state
from langgraph.types import Command
from datetime import datetime
from sub_graphs.swe.config import llm_mini, call_ai
import json

logger = BRDLogger()

reflect_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
            You are a reflective project generation assistant analyzing the current state of the project.
            """,
        ),
        (
            "human",
            """
            Project Name: {project_name}\n
            Project Summary: {project_summary}\n\n
            Current Progress:\n{progress}\n\n
            Files Created: {files_created}\n\n
            Please reflect on the current state of the project, identify any gaps or improvements, 
            and suggest next steps to enhance the project quality.
            """,
        ),
    ]
)
reflect_chain = reflect_prompt | llm_mini


async def reflect(
    state: FileState, config: RunnableConfig
) -> Command[Literal["generate_path"]]:
    """
    Reflect on the current project state, identify gaps, and suggest improvements.
    This node helps ensure the project meets quality standards and requirements.
    """
    logger.log("Reflecting on project state...", section="reflect")
    await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

    files_created = [f.name for f in state.get("files", [])]

    progress = {
        "completed_sections": state.get("completed_sections", []),
        "pending_sections": state.get("pending_sections", []),
        "processed_files": state.get("processed_files", 0),
        "total_files": len(state.get("files", [])),
    }

    try:
        response = await call_ai(
            reflect_chain,
            {
                "project_name": state.get("project_name", ""),
                "project_summary": state.get("project_summary", ""),
                "progress": json.dumps(progress, indent=2),
                "files_created": json.dumps(files_created, indent=2),
            },
            config,
        )

        logger.log("Reflection completed", section="reflect")
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

        return Command(
            goto="generate_path",
            update={"reflection": response.content, "next_node": "clear_state"},
        )
    except Exception as e:
        logger.log(
            f"Error during reflection: {str(e)[:50]}",
            level=LogLevel.ERROR,
            section="reflect",
        )
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        hitl = {
            "name": "error",
            "title": "Reflection Agent",
            "description": f"An Error Occured: \n{str(e)[:500]}",
            "approved": False,
        }
        return Command(
            goto="generate_path",
            update={
                "hitl": hitl,
                "reflection": "I've completed the requested actions for your project.",
                "next_node": "clear_state",
            },
        )
