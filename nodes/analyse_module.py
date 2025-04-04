# Analyse reuirements node

from sub_graphs.swe.tools.core_tools import SummarizeTool
from sub_graphs.swe.config import llm_mini, logger
from sub_graphs.swe.prompts.swe_prompts import build_system_prompt
from sub_graphs.configs.constants import (
    create_file_structure as async_create_file_structure,
)
from sub_graphs.swe.project_data_state import (
    CurrentModule,
    FileInfo,
    FileState,
)

import re
from typing import Literal
from utils.logger import LogLevel
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_emit_state
from langchain_core.messages import SystemMessage
from langgraph.types import Command
from datetime import datetime
from langgraph.types import Command
from langchain_core.runnables import RunnableConfig
from copilotkit.langgraph import copilotkit_customize_config


model = llm_mini
tools = [SummarizeTool]


async def analyze_request(
    state: FileState, config: RunnableConfig
) -> Command[Literal["generate_path"]]:
    """
    Analyze the user's request to understand project requirements and scope.

    Extracts key information such as project type, features, technologies, and constraints.
    Results are stored in state for use by downstream nodes.
    """

    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[
            {
                "state_key": "stream",
                "tool": "SummarizeTool",
            }
        ],
    )

    project_name = state.get("project_name", "")
    generated_files = state.get("generated_files", [])
    analysis = {}
    logger.log("Analyzing user request...", section="analysis")
    await copilotkit_emit_state(
        config,
        {
            "stream": analysis,
            "generated_files": generated_files,
            "logs": logger._format_logs_for_state(),
        },
    )

    try:
        response = await model.bind_tools(tools, tool_choice="SummarizeTool").ainvoke(
            [
                SystemMessage(content=build_system_prompt(state, "analyze")),
                *state["messages"],
            ],
            config,
        )
        analysis = response.tool_calls[0]["args"]
        print(analysis["markdown"])

        if project_name == "":
            # Extract project name from analysis or query
            project_name_match = re.search(
                r"(?:Project|App|Tool|Library)\s+Name:?\s+([A-Za-z0-9_\-\s]+)",
                analysis["markdown"],
            )
            project_name = (
                project_name_match.group(1).strip()
                if project_name_match
                else "UntitledProject"
            )
        project_name = project_name.replace(" ", "_").lower()
        logger.log(f"Project identified as: {project_name}", section="analysis")

        analysis_file = FileInfo(
            path="/docs/analysis.md",
            module="documentation",
            description="analysis report",
            content=analysis["markdown"],
            complete=True,
        )

        docs_module = CurrentModule(
            name="documentation",
            description="I've prepared some documentation for your project. Feel free to ask if I can modify any document to better match your needs - we can adjust until it's exactly what you're looking for.",
            specification="this contains documentations",
            files=[analysis_file],
            sections=["analysis"],
            completed_files=[analysis_file],
            pending_files=[],
        )
        state["generated_files"] = [docs_module.dict()]
        project_structure = state.get("project_structure", {})
        await async_create_file_structure(
            f"./{project_name}/docs/analysis.md",
            analysis["markdown"],
            project_structure,
        )
        logger.log("Analysis completed successfully", section="analysis")
        logger.mark_all_done("analysis")
        await copilotkit_emit_state(
            config, {**state, "logs": logger._format_logs_for_state()}
        )

        hitl = {
            "name": "documentation",
            "title": "Analysis Agent",
            "description": "Check the analysis resport and choose to reflect or proceed to planning if its OK",
            "remarks": "",
            "approved": False,
            "timestamp": str(datetime.now()),
        }

        next_node = "process_feedback_node"
        # if state.get("follow_up", "") == "":
        #     next_node = "planner"

        return Command(
            goto="generate_path",
            update={
                **state,
                "processed_files": state.get("processed_files", 0) + 1,
                "hitl": hitl,
                "follow_up": "",
                "stream": response.tool_calls[0]["args"],
                "analysis": analysis["markdown"],
                "project_name": project_name,
                "project_analyzed": True,
                "last_action": "Generated Analysis",
                "project_structure_json": project_structure,
                "messages": state["messages"],
                "next_node": next_node,
            },
        )

    except Exception as e:
        print("analysis_node:\n", e)
        logger.log(
            f"Error during request analysis: {str(e)[:100]}",
            level=LogLevel.ERROR,
            section="analysis",
        )
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        hitl = {
            "name": "error",
            "title": "Analysis Agent",
            "description": f"An Error Occured: \n{str(e)[:500]}",
            "approved": False,
        }
        return Command(
            goto="generate_path",
            update={
                "hitl": hitl,
                "stream": f"Error analyzing request  \n{str(e)[:500]} ",
                "project_analyzed": False,
                "error": str(e),
                "last_action": "Created Analysis",
                "next_node": "analyze",
            },
        )
