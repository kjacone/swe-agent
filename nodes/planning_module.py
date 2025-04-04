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
from utils.logger import LogLevel
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_emit_state, copilotkit_customize_config
from langgraph.types import Command
from datetime import datetime
from sub_graphs.swe.config import llm_mini, logger
from sub_graphs.swe.tools.core_tools import SummarizeTool
from sub_graphs.swe.prompts.swe_prompts import build_system_prompt
from langchain_core.messages import SystemMessage, HumanMessage


human_message = HumanMessage(
    content="Create a comprehensive project plan that covers all necessary components and provides clearimplementation instructions for each module"
)
model = llm_mini
tools = [SummarizeTool]


async def planner(
    state: FileState, config: RunnableConfig
) -> Command[Literal["generate_path"]]:
    """
    Create a comprehensive project plan covering all aspects of the project.
    Determines what modules and components need to be built and in what order.
    """
    logger.log("Creating project plan...", section="planner")
    await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
    project_structure = state.get("project_structure_json", {})

    config = copilotkit_customize_config(
        config,
        emit_intermediate_state=[
            {
                "state_key": "stream",
                "tool": "SummarizeTool",
            }
        ],
    )

    try:
        response = await model.bind_tools(tools, tool_choice="SummarizeTool").ainvoke(
            [
                SystemMessage(content=build_system_prompt(state, "planner")),
                human_message,
                *state["messages"],
            ],
            config,
        )
        raw = response.tool_calls[0]["args"]
        raw_plan = raw["markdown"]
        # print("Plan:\n", raw["markdown"])

        name = state.get("project_name", "untitled_project")
        await async_create_file_structure(
            f"./{name}/docs/project_plan.md", raw_plan, project_structure
        )

        specs_file = FileInfo(
            path="/docs/project_plan.md",
            module="documentation",
            description="project plan",
            content=raw_plan,
            complete=True,
        )

        doc_module = next(
            (m for m in state["generated_files"] if m["name"] == "documentation"),
            {},
        )
        doc_module["completed_files"] = doc_module.get("completed_files", []) + [
            specs_file.dict()
        ]
        doc_module["files"] = doc_module.get("files", []) + [specs_file.dict()]
        doc_module["sections"] = doc_module.get("sections", []) + ["planner"]

        state["generated_files"] = [doc_module]

        logger.log("System Design completed successfully", section="planner")
        logger.mark_all_done("planner")
        await copilotkit_emit_state(
            config, {**state, "logs": logger._format_logs_for_state()}
        )

        # Process the raw plan into structured modules and sections
        # print("raw_plan:\n", raw_plan)
        modules = extract_data_from_md(raw_plan)
        print("\n\n\nmodules:\n", modules)
        if not modules:
            hitl = {
                "name": "error",
                "title": "Planning Agent",
                "description": "No modules extracted try again",
                "approved": False,
                "timestamp": str(datetime.now()),
            }
            return Command(
                goto="process_feedback_node",
                update={
                    "hitl": hitl,
                    "last_action": "Created project plan",
                    "next_node": "planner",
                },
            )

        hitl = {
            "name": "planner",
            "title": "Planning Agent",
            "description": "Select the Modules you need generated",
            "remarks": "",
            "pending_sections": modules,
            "selected_sections": [],
            "approved": False,
            "timestamp": str(datetime.now()),
        }
        next_node = "process_feedback_node"

        return Command(
            goto="generate_path",
            update={
                "hitl": hitl,
                "formatted_plan": raw_plan,
                "base_plan": modules,
                "stream": response.tool_calls[0]["args"],
                "pending_sections": modules,
                "completed_sections": [],
                "last_action": "Created project plan",
                "next_node": next_node,
            },
        )
    except Exception as e:
        print("planner_node:\n", e)
        logger.log(
            f"Error creating project plan: {str(e)[:50]}",
            level=LogLevel.ERROR,
            section="planner",
        )
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

        hitl = {
            "name": "error",
            "title": "Planning Agent",
            "description": f"An Error Occured: \n{str(e)[:500]}",
            "approved": False,
        }

        return Command(
            goto="__end__",
            update={
                "hitl": hitl,
                "pending_sections": [],
                "error": str(e),
                "last_action": "Created a planner",
                "next_node": "planner",
            },
        )


import re


def extract_data_from_md(file_content):
    """
    Extract structured module data from markdown content.
    Returns a list of modules with their details.
    """
    # Split content into module sections
    sections = _split_into_sections(file_content)

    # Process each section to extract module data
    result = []
    for section in sections:
        module_data = _process_module_section(section)
        if module_data:
            result.append(module_data)

    return result


def _split_into_sections(file_content):
    """Split the markdown content into module sections by '---' delimiter."""
    sections = file_content.split("---")
    # Remove first and last items if they're not module sections
    if len(sections) > 3:
        return sections[1:-2]
    return sections


def _process_module_section(section):
    """Process a single module section to extract all relevant data."""
    # Extract module header
    module_match = re.search(r"## (\d+\.\s+.+)", section)
    if not module_match:
        return None

    module_name = module_match.group(1).strip()

    # Extract module description
    description = _extract_description(section)

    # Extract module Technologies
    technologies = _extract_technologies(section)

    # Extract all sections within the module
    sections_data = _extract_sections(section)

    return {
        "name": module_name,
        "description": description,
        "technologies": technologies,
        "sections": sections_data,
        "specification": section,
        "approved": False,
    }


def _extract_description(section):
    """Extract the module description from the section."""
    desc_match = re.search(
        r"- \*\*Description\*\*:\s*(.*?)(?=###|\Z)", section, re.DOTALL
    )

    if not desc_match:
        return ""

    # Extract and clean the description
    raw_desc = desc_match.group(1).strip()
    desc_lines = [line.strip() for line in raw_desc.split("\n") if line.strip()]
    return " ".join(desc_lines)


def _extract_technologies(section):
    """Extract the module Technologies from the section."""
    desc_match = re.search(
        r"- \*\*Technologies\*\*:\s*(.*?)(?=###|\Z)", section, re.DOTALL
    )

    if not desc_match:
        return ""

    # Extract and clean the description
    raw_desc = desc_match.group(1).strip()
    desc_lines = [line.strip() for line in raw_desc.split("\n") if line.strip()]
    return " ".join(desc_lines)


def _extract_sections(section):
    """Extract all subsections within a module section."""
    section_matches = re.finditer(
        r"(### \d+\.\d+.+)(?:\n)([\s\S]*?)(?=###|\Z)", section
    )

    sections_data = []
    for match in section_matches:
        section_header = match.group(1).replace("###", "").strip()
        section_content = _clean_section_content(match.group(2).strip())

        sections_data.append(
            {"name": section_header, "specifications": section_content}
        )

    return sections_data


def _clean_section_content(content):
    """Clean markdown formatting from section content."""
    # Remove Markdown formatting like "- **Tasks**:"
    content = re.sub(r"- \*\*([^:]+)\*\*:", r"\1:", content)

    # Remove other markdown formatting like bullet points
    content = re.sub(r"^\s*-\s+", "", content, flags=re.MULTILINE)

    return content
