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
from utils.logger import BRDLogger, LogLevel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from copilotkit.langchain import copilotkit_emit_state
from config import Config
from langgraph.types import Command
from datetime import datetime
from sub_graphs.swe.config import llm_mini, call_ai
# from langchain_deepseek import ChatDeepSeek


logger = BRDLogger()


module_creation_prompt = ChatPromptTemplate.from_messages(
    [
        "system",
        """
You are an expert software architect creating detailed module specifications. For each module, provide the following:
1. A clear and concise description of the module's purpose and functionality.
2. A list all the files needed for the module, specifying the full path and  detailed Key Functions of the file. 
3. A clear description module setting up , configuration  and environment variables needed for module
  
Be comprehensive and provide specific technical details that can be used directly for implementation with an LLM. 
Include all necessary files, dependencies, and interfaces for the module.

   Provide a concise module specification with a description, list of files and their key functions, and any setup/configuration/environment variables required.
   <Output_Format> 
   # Module Specification: __content_here__
## 1. Module Description
**Purpose and Functionality:**  
__content_here__
## 2. Files and Key Functions
### File Structure
__content_here__
### Detailed Key Functions of Each File
1. **__file_full_path_here__**
   - **Key Functions:**
    __content_here__
## 3. Module Setup, Configuration, and Environment Variables
### Module Setup
   __content_here__
### Configuration
1. **__file_full_path_here__:**
      __content_here__
### Environment Variables
   __content_here__
### Additional Notes
   __content_here__
This module specification ...
   </Example_Response>
    """,
        "human",
        """Project Name: {project_name}\n
     
        Module to Create: {module_name}\n
        Module Plan: {module_description}\n\n
        Create a comprehensive module specification for this module""",
    ]
)
module_creation_chain = module_creation_prompt | llm_mini


async def create_module(
    state: FileState, config: RunnableConfig
) -> Command[Literal["generate_path"]]:
    """
    Create detailed specifications for the current module to be implemented.
    This prepares all details needed for code generation.
    """

    # Get next module to create from pending sections
    pending = state.get("pending_sections", [])
    if not pending:
        logger.log("No more modules to create", section="module")
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        hitl = {
            "name": "success",
            "title": "Coding Agent",
            "description": "Code generation completed succesfully",
            "approved": False,
        }
        return Command(
            goto="generate_path",
            update={
                "all_files_processed": True,
                "last_action": "All modules created",
                "next_node": "clear_state",
            },
        )

    # Pop the first pending module
    current_module = pending[0]
    remaining_modules = pending[1:]
    print("prev_modules: ", len(pending))
    print("remaining_modules: ", len(remaining_modules))

    hitl = {
        "name": "create_module",
        "title": current_module["name"],
        "description": "",
        "module": current_module,
        "remarks": "",
        "approved": False,
        "timestamp": str(datetime.now()),
    }

    return Command(
        goto="generate_path",
        update={
            "hitl": hitl,
            "current_module": current_module,
            "pending_sections": remaining_modules,
            "next_node": "process_feedback_node",
            "last_action": f"Created module specification for {current_module['name']}",
        },
    )


# Helper function to extract files from module specification
# Helper function to extract files and their details from module specification
def extract_file_data(markdown_text):
    # Find the "Detailed Key Functions of Each File" section
    pattern = r"### Detailed Key Functions of Each File\s+(.*?)(?:##|\Z)"
    section_match = re.search(pattern, markdown_text, re.DOTALL)

    if not section_match:
        return []

    section_content = section_match.group(1)

    # Extract each file entry
    file_entries = re.findall(
        r"\d+\.\s+\*\*(.*?)\*\*\s+- \*\*Key Functions:\*\*\s+(.*?)(?=\d+\.\s+\*\*|\Z)",
        section_content,
        re.DOTALL,
    )

    result = []
    for file_path, functions_text in file_entries:
        # Clean up the file path
        file_path = file_path.strip()

        # Extract and clean up key functions
        functions = re.findall(r"`([^`]+)`:(.*?)(?=`|$)", functions_text, re.DOTALL)
        if functions:
            key_functions = " ".join(
                [
                    f"{func_name}: {func_desc.strip()}"
                    for func_name, func_desc in functions
                ]
            )
        else:
            key_functions = functions_text.strip()

        result.append({"path": file_path, "description": key_functions})

    return result
