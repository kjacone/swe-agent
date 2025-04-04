import os
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
from langgraph.types import Command
from sub_graphs.swe.config import llm_mini, call_ai

# from langchain_deepseek import ChatDeepSeek


logger = BRDLogger()
# Code module node to generate actual implementation
code_generation_prompt = ChatPromptTemplate.from_messages(
    [
        "system",
        """
        You are an expert software developer creating high-quality implementation code. 
        Create complete, production-ready code for the specified module. 
        
1. For File Path always include the full path of the file eg. /package.json       
2. For File Content Your code should be:
- Comprehensive and complete; do not leave any placeholders, TODOs, or unfinished sections. 
- Well-structured and following best practices for the specified technology stack.
- Includes comprehensive error handling mechanisms.
- Contains clear and concise comments explaining the code's functionality.
- Include a detailed comment at the top of file on what the file does
- Include all necessary imports, dependencies, and functionality to ensure the file works seamlessly within the context of the project.

3. Dont Get Lazy generate complete code

Here is Just An example of a Frontend Module
 <Example_Response> 
 Sure! Below is a complete and production-ready implementation code for each specified file of the frontend module...
 
### 1.**/main.js**
```javascript

// /main.js
import Vue from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';

Vue.config.productionTip = false;

new Vue({{
  router,
  store,
  render: h => h(App)
}}).$mount('#app');

``` 

### 2.**/package.json**
```json 

// /package.json
{{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {{
    "serve": "vue-cli-service serve",
    "build": "vue-cli-service build",
    "lint": "vue-cli-service lint"
  }},
  "dependencies": {{
    "core-js": "^3.6.5",
    "vue": "^2.6.11",
    "vue-router": "^3.2.0",
    "vuex": "^3.4.0"
  }},
  "devDependencies": {{
    "@vue/cli-plugin-babel": "~4.5.0",
    "@vue/cli-plugin-eslint": "~4.5.0",
    "@vue/cli-service": "~4.5.0",
    "babel-eslint": "^10.1.0"
  }}
}}

```

</Example_Response> 
    """,
        "system",
        """
        Module Specification: {module_spec}
        Technologies: {technologies}
        If there are any missing files, please identify and include them.
        Generate complete, production-ready code for each file specified as part of the module, 
        ensuring best practices and proper documentation are followed.""",
    ]
)
code_generation_chain = code_generation_prompt | llm_mini


async def code_module(
    state: FileState, config: RunnableConfig
) -> Command[Literal["generate_path"]]:
    """
    Generate implementation code for the current module's files.
    This creates actual code files based on the module specification.
    """

    current_module = state.get("current_module", {})
    if not current_module:
        print("************ No current module to code")
        logger.log("No current module to code", section="code", level=LogLevel.ERROR)
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        Command(
            goto="generate_path",
            update={
                "last_action": "Generated code for current module",
            },
        )

    try:
        logger.log(f"Generating code for {current_module['name']}...", section="code")
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})

        response = await call_ai(
            code_generation_chain,
            {
                # "project_summary": state.get("project_summary", ""),
                "technologies": current_module["technologies"],
                "module_spec": current_module["specification"],
            },
            config,
        )
        print(current_module["name"], response.content)
        # Extract code from the response
        files = extract_code_from_markdown(response.content, current_module["name"])
        print("FILES", files)
        # Save the file to the project structure
        name = state["project_name"].replace(" ", "_").lower()
        project_structure = state.get("project_structure_json", {})
        mod = current_module["name"].replace(" ", "_").lower()

        for file in files:
            file_path = f"./{name}/{mod}/{file.path}"
            await async_create_file_structure(
                file_path, file.content, project_structure
            )

        # Create updated current module
        updated_module = CurrentModule(
            name=current_module["name"],
            description=current_module["description"],
            specification=current_module["specification"],
            files=files,
            sections=[s["name"].replace(" ", "_") for s in current_module["sections"]],
            completed_files=files,
            pending_files=[],
        )

        generated_files = state.get("generated_files", []) + [updated_module.dict()]

        next_node = "create_module"
        logger.mark_all_done("code")
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        return Command(
            goto="generate_path",
            update={
                "generated_files": generated_files,
                "processed_files": state.get("processed_files", 0) + 1,
                "last_action": f"Generated code for {current_module['name']}",
                "next_node": next_node,
                "current_module": {},
            },
        )
    except Exception as e:
        print("code_module Error:\n", e)
        logger.log(
            f"Error generating code: {str(e)[:50]}",
            level=LogLevel.ERROR,
            section="code",
        )
        await copilotkit_emit_state(config, {"logs": logger._format_logs_for_state()})
        hitl = {
            "name": "error",
            "title": "Coding Agent",
            "description": f"An Error Occured in {current_module['name']}: \n{str(e)[:500]}",
            "approved": False,
        }
        return Command(
            goto="process_feedback_node",
            update={
                "hitl": hitl,
                "pending_sections": state.get("pending_sections", []).append(
                    current_module
                ),
                "completed_sections": [],
                "error": str(e),
                "last_action": f"Generated code for {current_module['name']}",
                "next_node": "code_module",
            },
        )


# Helper function to extract code content from AI response
def extract_code_from_markdown(content, current_module):
    """
    Extract code blocks from a markdown file and format as a list of FileInfo objects.
    Specifically handles file paths in the format: ### 2. **/frontend/README.md**

    Args:
        markdown_file_path: Path to the markdown file
        current_module: Current module name to prefix paths

    Returns:
        List of FileInfo objects
    """
    try:
        # Pattern to match numbered file paths and code blocks
        # Specifically targets: ### 2. **/frontend/README.md** format
        pattern = r"###\s*\d+\.\s*\*\*(.*?)\*\*\n```.*?\n(.*?)```"
        matches = re.findall(pattern, content, re.DOTALL)

        results = []
        for match in matches:
            file_path = match[0].strip()
            code_content = match[1]

            # Make sure we get the actual path by removing any extra characters
            # Path will be like /frontend/README.md
            if file_path.startswith("/"):
                clean_path = file_path
            else:
                # In case there are extra characters before the path
                path_match = re.search(r"(/[\w/.-]+)", file_path)
                if path_match:
                    clean_path = path_match.group(1)
                else:
                    # Fallback if no path format is found
                    clean_path = file_path

            # Ensure the path isn't too long
            if len(clean_path) > 100:
                # Extract just the filename
                filename = os.path.basename(clean_path)
                directory = os.path.dirname(clean_path)

                # If the directory path is too long, shorten it
                if len(directory) > 50:
                    shortened_dir = directory[:20] + "..." + directory[-20:]
                    clean_path = os.path.join(shortened_dir, filename)

            # Create the module-prefixed path but ensure it's not too long
            module_path = f"{clean_path}"
            if len(module_path) > 200:
                # Keep the important parts - beginning of path and filename
                module_path = f"/{os.path.basename(clean_path)}"

            results.append(
                FileInfo(
                    path=module_path,
                    module=current_module,
                    description=f"{current_module} - {os.path.basename(clean_path)}",
                    content=code_content,
                    complete=True,
                )
            )

        return results

    except Exception as e:
        print(f"Error processing markdown file: {e}")
        return []
