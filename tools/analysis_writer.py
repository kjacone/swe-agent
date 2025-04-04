from datetime import datetime
from typing import Optional, Dict, cast
from langchain_core.messages import AIMessage, ToolMessage
from langchain_community.adapters.openai import convert_openai_messages
from langchain_core.tools import tool, BaseTool
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import random
import string
from copilotkit.langchain import copilotkit_customize_config, copilotkit_emit_state


@tool
def AnalyseSection(path: str, content: str, section_number: int, footer: str = ""):  # pylint: disable=invalid-name,unused-argument
    """Write a file with content and footer containing description"""


def generate_random_id(length=6):
    return "".join(random.choices(string.ascii_letters + string.digits, k=length))


class AnalysisWriterInput(BaseModel):
    title: str
    description: str
    user_query: str = Field(description="The user query or description for the file.")
    path: str = Field(description="The path of the specific file to write.")
    idx: int = Field(
        description="An index representing the order of this file (starting at 0"
    )
    state: Optional[Dict] = Field(description="State of the monorepo")


@tool("analysis_writer", args_schema=AnalysisWriterInput, return_direct=True)
async def analysis_writer(user_query, path, idx, state):
    """Writes a specific file of a monorepo based on the query, path, and provided information."""
    config = RunnableConfig()
    # Log search queries
    state["logs"] = state.get("logs", [])
    state["logs"].append({"message": f"📝 Writing the {path} ...", "done": False})
    await copilotkit_emit_state(config, state)

    section_id = generate_random_id()
    section = {
        "path": path,
        "content": "",
        "footer": "",
        "idx": idx,
        "id": section_id,
    }

    content_state = {
        "state_key": f"section_stream.content.{idx}.{section_id}.{path}",
        "tool": "WriteSection",
        "tool_argument": "content",
    }
    footer_state = {
        "state_key": f"section_stream.footer.{idx}.{section_id}.{path}",
        "tool": "WriteSection",
        "tool_argument": "footer",
    }

    config = copilotkit_customize_config(
        config, emit_intermediate_state=[content_state, footer_state]
    )

    outline = state.get("outline", {})
    sources = state.get("sources").values()
    section_exists = (
        True if section["idx"] in [sec["idx"] for sec in state["sections"]] else False
    )

    if not section_exists:
        # Define the system and user prompts
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that writes a section of a research report in markdown format."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Today's date is {datetime.now().strftime('%d/%m/%Y')}.\n\n"
                    f"Research Query: {user_query}\n\n"
                    f"Section Path: {path}\n\n"
                    f"Section Number: {idx}\n\n"
                    f"Sources:\n{sources}\n\n"
                    "Write a section using the write_section tool. The section should be detailed and well-structured in markdown. "
                    "Use appropriate markdown formatting to create a professional academic document. "
                    "Only use footnotes when citing sources or referencing external material. "
                    "If footnotes are used, they must start from [^1] in this section. "
                    "References must be defined in the footer field, not in the content."
                ),
            },
        ]
    else:
        # get the current content of the section we want to update
        current_section_state = state["sections"][section["idx"]]
        prompt = [
            {
                "role": "system",
                "content": (
                    "You are an AI assistant that makes changes to a given section of a research report in markdown format."
                    "Use the given section and only make changes that were requested by the user."
                    "Do not change the title of a section unless explicitly requested by the user."
                    "The given section:"
                    f"Title : {current_section_state['path']}\n"
                    f"Content : {current_section_state['content']}\n"
                    f"Footer : {current_section_state['footer']}\n\n"
                    "Now use the user's request to alter the given section."
                    f"The user request : {[message_content for message_type, message_content in state['messages'].items() if message_type == 'HumanMessage'][-1]}"
                ),
            },
            {
                "role": "user",
                "content": (
                    "You are an AI assistant that has completed the task of creating a specific section of a research report, now your primary goal is to make changes to the section to fit the users request."
                    "Edit the given section of the report using the write_section tool. Make sure to only make changes to the section that the user requested."
                    "Before making changes to the given section of the report identify the location (heading/subheading/bullet point/etc.) where the user's request needs to be placed in the report, and then only make changes to this location and keep everything else the same. "
                    "Use appropriate markdown formatting to create a professional academic report section."
                    "Do not alter the format of the given section unless explicitly instructed by the user."
                ),
            },
        ]

    try:
        # Convert prompts for OpenAI API
        lc_messages = convert_openai_messages(prompt)

        # Invoke OpenAI's model with tool
        model = ChatOpenAI(model="gpt-4o-mini", max_retries=1)
        response = await model.bind_tools([AnalyseSection]).ainvoke(lc_messages, config)

        state["logs"][-1]["done"] = True
        await copilotkit_emit_state(config, state)

        ai_message = cast(AIMessage, response)
        if ai_message.tool_calls:
            if ai_message.tool_calls[0]["name"] == "AnalyseSection":
                section["path"] = ai_message.tool_calls[0]["args"].get("path", "")
                section["content"] = ai_message.tool_calls[0]["args"].get("content", "")
                section["footer"] = ai_message.tool_calls[0]["args"].get("footer", "")

        if section_exists:
            state["sections"][section["idx"]] = section
        else:
            state["sections"].append(section)

        # Process each stream state
        stream_states = {"content": content_state, "footer": footer_state}

        for stream_type, stream_info in stream_states.items():
            if stream_info["state_key"] in state:
                state[stream_info["state_key"]] = None
        await copilotkit_emit_state(config, state)

        tool_msg = f"Wrote the {path} Section, idx: {idx}"

        return state, tool_msg
    except Exception as e:
        # Clear logs
        state["logs"] = []
        await copilotkit_emit_state(config, state)

        return state, f"Error generating section: {e}"
