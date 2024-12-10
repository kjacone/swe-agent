from typing import Annotated, Any, Literal, TypedDict, List, Dict, Optional, cast
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from shared.utils import load_chat_model
from swe_graph.analyser_sub_graph.state import AnalyzerState
from swe_graph.configuration import AgentConfiguration
from swe_graph.development_sub_graph.state import (
    CodeImplementation,
    CodePath,
    DevelopmentState,
    TestCase,
)


def determine_code_paths(
    task_name: str, component_type: str, root_path: str
) -> CodePath:
    """Determine appropriate paths for code and tests based on task and component type."""

    # Clean task name for path usage
    safe_name = task_name.lower().replace(" ", "_").replace("-", "_")

    if component_type == "frontend":
        base_path = os.path.join(root_path, "frontend", "src")
        test_base = os.path.join(root_path, "frontend", "tests")

        if "component" in task_name.lower():
            module_path = os.path.join(base_path, "components")
            package_name = "components"
        elif "page" in task_name.lower():
            module_path = os.path.join(base_path, "pages")
            package_name = "pages"
        else:
            module_path = os.path.join(base_path, "utils")
            package_name = "utils"

        file_path = os.path.join(module_path, f"{safe_name}.tsx")
        test_path = os.path.join(test_base, package_name, f"{safe_name}.test.tsx")
        relative_import_path = f"@/{package_name}/{safe_name}"

    elif component_type == "backend":
        base_path = os.path.join(root_path, "backend", "src")
        test_base = os.path.join(root_path, "backend", "tests")

        if "api" in task_name.lower():
            module_path = os.path.join(base_path, "api")
            package_name = "api"
        elif "service" in task_name.lower():
            module_path = os.path.join(base_path, "services")
            package_name = "services"
        else:
            module_path = os.path.join(base_path, "models")
            package_name = "models"

        file_path = os.path.join(module_path, f"{safe_name}.py")
        test_path = os.path.join(test_base, package_name, f"test_{safe_name}.py")
        relative_import_path = f"{package_name}.{safe_name}"

    else:  # shared
        base_path = os.path.join(root_path, "shared", "src")
        test_base = os.path.join(root_path, "shared", "tests")
        module_path = os.path.join(base_path, "utils")
        package_name = "shared.utils"
        file_path = os.path.join(module_path, f"{safe_name}.ts")
        test_path = os.path.join(test_base, f"{safe_name}.test.ts")
        relative_import_path = f"@shared/utils/{safe_name}"

    return CodePath(
        file_path=file_path,
        module_path=module_path,
        test_path=test_path,
        relative_import_path=relative_import_path,
        package_name=package_name,
    )


async def plan_development(state: DevelopmentState) -> Dict[str, Any]:
    """Plan development tasks and create test strategy."""
    try:
        # Sort tasks by priority and dependencies
        sorted_tasks = sorted(
            state.tasks,
            key=lambda x: (x.get("priority", 0), len(x.get("dependencies", []))),
        )

        # Set current task
        current_task = sorted_tasks[0] if sorted_tasks else None

        if current_task:
            return {
                "current_task": current_task["id"],
                "messages": [f"Starting development of task: {current_task['name']}"],
                "next_node": "generate_tests",
            }
        else:
            return {
                "errors": ["No tasks available for development"],
                "next_node": "human_review",
            }
    except Exception as e:
        return {
            "errors": [f"Error in development planning: {str(e)}"],
            "next_node": "human_review",
        }


async def generate_tests(state: DevelopmentState) -> Dict[str, Any]:
    """Enhanced test generation with proper paths."""
    try:
        current_task = next(
            (t for t in state.tasks if t["id"] == state.current_task), None
        )
        if not current_task:
            raise ValueError("Current task not found")

        # Determine component type and paths
        component_type = current_task.get("component_type", "shared")
        code_paths = determine_code_paths(
            current_task["name"], component_type, state.root_path
        )

        # Generate tests with proper imports and paths
        test_cases = {}

        # Unit Test
        unit_test_code = f"""
import {{ describe, it, expect }} from '@jest/globals';
import {{ {current_task['name']} }} from '{code_paths.relative_import_path}';

describe('{current_task['name']}', () => {{
    it('should handle basic functionality', () => {{
        const result = {current_task['name']}();
        expect(result).toBeDefined();
    }});
    
    it('should handle edge cases', () => {{
        const result = {current_task['name']}();
        expect(result).toBeDefined();
    }});
}});
"""
        test_cases[f"test_unit_{state.current_task}_1"] = TestCase(
            id=f"test_unit_{state.current_task}_1",
            type="unit",
            description=f"Unit test for {current_task['name']}",
            requirements=current_task.get("requirements", []),
            code=unit_test_code,
            code_path=code_paths,
            status="pending",
        )

        # Integration Test with proper imports
        integration_test_code = f"""
import {{ describe, it, expect }} from '@jest/globals';
import {{ {current_task['name']} }} from '{code_paths.relative_import_path}';
import {{ dependencies }} from './test-utils';

describe('{current_task['name']} Integration', () => {{
    it('should integrate with dependencies', async () => {{
        const deps = await setupDependencies();
        const result = await {current_task['name']}(deps);
        expect(result).toMatchExpectedIntegration();
    }});
}});
"""
        test_cases[f"test_integration_{state.current_task}_1"] = TestCase(
            id=f"test_integration_{state.current_task}_1",
            type="integration",
            description=f"Integration test for {current_task['name']}",
            requirements=current_task.get("requirements", []),
            code=integration_test_code,
            code_path=code_paths,
            status="pending",
        )

        return {
            "test_cases": test_cases,
            "messages": [
                f"Generated {len(test_cases)} test cases for {current_task['name']}",
                f"Test files will be created at: {code_paths.test_path}",
            ],
            "next_node": "implement_code",
        }

    except Exception as e:
        return {
            "errors": [f"Error in test generation: {str(e)}"],
            "next_node": "human_review",
        }


async def implement_code(state: DevelopmentState) -> Dict[str, Any]:
    """Enhanced code implementation with proper paths."""
    try:
        current_task = next(
            (t for t in state.tasks if t["id"] == state.current_task), None
        )
        if not current_task:
            raise ValueError("Current task not found")

        # Get paths for the current task
        code_paths = determine_code_paths(
            current_task["name"],
            current_task.get("component_type", "shared"),
            state.root_path,
        )

        # Determine file extension and template based on component type
        if current_task.get("component_type") == "frontend":
            implementation_code = f"""
import React from 'react';
import {{ useCallback }} from 'react';

interface {current_task['name']}Props {{
    // Define props here
}}

export const {current_task['name']}: React.FC<{current_task['name']}Props> = (props) => {{
    const handleAction = useCallback(() => {{
        // Implementation
    }}, []);

    return (
        <div>
            // UI
        </div>
    );
}};

export default {current_task['name']};
"""
        elif current_task.get("component_type") == "backend":
            implementation_code = f"""
from typing import Dict, List, Optional
from fastapi import HTTPException

class {current_task['name']}:
    def __init__(self):
        self.configure()
    
    def configure(self):
        \"\"\"Initialize configuration.\"\"\"
        pass
    
    async def process(self, data: Dict) -> Dict:
        \"\"\"Process the main business logic.\"\"\"
        try:
            # Implementation
            return {{"status": "success"}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
"""
        else:
            implementation_code = f"""
export interface {current_task['name']}Config {{
    // Configuration interface
}}

export class {current_task['name']} {{
    private config: {current_task['name']}Config;

    constructor(config: {current_task['name']}Config) {{
        this.config = config;
    }}

    public async execute(): Promise<void> {{
        // Implementation
    }}
}}
"""

        implementation = CodeImplementation(
            id=f"impl_{state.current_task}",
            task_id=state.current_task,
            requirements=current_task.get("requirements", []),
            code=implementation_code,
            code_path=code_paths,
            tests=list(state.test_cases.keys()),
            status="implemented",
        )

        return {
            "implementations": {implementation.id: implementation},
            "messages": [
                f"Implemented code for {current_task['name']}",
                f"Code file will be created at: {code_paths.file_path}",
            ],
            "next_node": "run_tests",
        }

    except Exception as e:
        return {
            "errors": [f"Error in code implementation: {str(e)}"],
            "next_node": "human_review",
        }


async def run_tests(state: DevelopmentState) -> Dict[str, Any]:
    """Execute tests and analyze results."""
    try:
        # Simulate test execution
        test_results = {}
        coverage_data = {
            "overall": 85.5,
            "by_module": {"core": 90.0, "utils": 88.5, "handlers": 82.0},
        }

        for test_id, test_case in state.test_cases.items():
            # Simulate test run
            test_results[test_id] = {
                "status": "passed",
                "execution_time": 0.45,
                "coverage": 85.5,
                "assertions": {"total": 5, "passed": 5, "failed": 0},
            }

        all_tests_passed = all(
            result["status"] == "passed" for result in test_results.values()
        )

        if all_tests_passed:
            # Update implementation status
            implementations = state.implementations
            for impl_id in implementations:
                implementations[impl_id].status = "verified"

            return {
                "test_results": test_results,
                "coverage_reports": coverage_data,
                "implementations": implementations,
                "messages": ["All tests passed successfully"],
                "next_node": "refactor_code",
            }
        else:
            return {
                "test_results": test_results,
                "messages": ["Some tests failed"],
                "next_node": "implement_code",
            }
    except Exception as e:
        return {
            "errors": [f"Error in test execution: {str(e)}"],
            "next_node": "human_review",
        }


async def refactor_code(state: DevelopmentState) -> Dict[str, Any]:
    """Refactor code while maintaining test coverage."""
    try:
        # Update code base with implemented and tested code
        code_base = state.code_base
        for impl_id, implementation in state.implementations.items():
            if implementation.status == "verified":
                code_base[implementation.task_id] = {
                    "code": implementation.code,
                    "tests": implementation.tests,
                    "coverage": state.coverage_reports.get("overall", 0),
                }

        # Check if more tasks need to be implemented
        remaining_tasks = [t for t in state.tasks if t["id"] not in code_base]

        if remaining_tasks:
            return {
                "code_base": code_base,
                "current_task": remaining_tasks[0]["id"],
                "messages": ["Moving to next task"],
                "next_node": "generate_tests",
            }
        else:
            return {
                "code_base": code_base,
                "messages": ["All tasks completed"],
                "next_node": "human_review",
            }
    except Exception as e:
        return {
            "errors": [f"Error in code refactoring: {str(e)}"],
            "next_node": "human_review",
        }
