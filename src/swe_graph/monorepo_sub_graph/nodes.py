from typing import Annotated, Any, Literal, TypedDict, List, Dict, Optional, cast
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from shared.utils import load_chat_model
from swe_graph.analyser_sub_graph.state import AnalyzerState
from swe_graph.configuration import AgentConfiguration
from swe_graph.monorepo_sub_graph.state import MonorepoState


async def setup_directory_structure(state: MonorepoState) -> Dict[str, Any]:
    """Set up the basic directory structure for the monorepo."""
    try:
        # Extract architecture and specs from state
        architecture = state.specifications.get("architecture", {})
        tech_specs = state.specifications.get("tech_specs", {})

        # Define basic directory structure
        directory_structure = {
            "packages": {
                "frontend": {
                    "src": {"components": {}, "pages": {}, "utils": {}},
                    "tests": {},
                    "public": {},
                },
                "backend": {
                    "src": {"api": {}, "services": {}, "models": {}},
                    "tests": {},
                    "config": {},
                },
                "shared": {
                    "src": {"types": {}, "utils": {}, "constants": {}},
                    "tests": {},
                },
            },
            "tools": {"scripts": {}, "config": {}},
            "docs": {"api": {}, "guides": {}, "architecture": {}},
        }

        # Customize based on architecture
        if architecture.get("microservices"):
            directory_structure["packages"]["services"] = {
                service: {
                    "src": {"api": {}, "core": {}, "utils": {}},
                    "tests": {},
                    "config": {},
                }
                for service in architecture.get("services", [])
            }

        return {
            "monorepo_config": {
                "directory_structure": directory_structure,
                "root_config": {
                    "package_manager": tech_specs.get("package_manager", "yarn"),
                    "node_version": tech_specs.get("node_version", "18.x"),
                },
            },
            "next_node": "setup_tooling",
            "messages": ["Successfully created directory structure"],
        }
    except Exception as e:
        return {
            "errors": [f"Error in directory setup: {str(e)}"],
            "next_node": "human_review",
        }


async def setup_tooling(state: MonorepoState) -> Dict[str, Any]:
    """Configure development tooling and build setup."""
    try:
        tech_specs = state.specifications.get("tech_specs", {})

        # Define tooling configuration
        tooling_config = {
            "build_tools": {
                "typescript": {"version": "4.9.x", "strict": True},
                "babel": {"presets": ["@babel/preset-env", "@babel/preset-react"]},
                "webpack": {"version": "5.x"},
            },
            "linting": {
                "eslint": {
                    "extends": [
                        "eslint:recommended",
                        "plugin:@typescript-eslint/recommended",
                    ],
                },
                "prettier": {"semi": True, "singleQuote": True, "tabWidth": 2},
            },
            "testing": {
                "jest": {"version": "29.x", "coverage": {"threshold": 80}},
                "cypress": {"version": "12.x"},
            },
        }

        # Customize based on tech specs
        if tech_specs.get("framework") == "next.js":
            tooling_config["build_tools"]["next"] = {"version": "13.x"}

        return {
            "tooling_config": tooling_config,
            "next_node": "setup_dependencies",
            "messages": ["Successfully configured development tooling"],
        }
    except Exception as e:
        return {
            "errors": [f"Error in tooling setup: {str(e)}"],
            "next_node": "human_review",
        }


async def setup_dependencies(state: MonorepoState) -> Dict[str, Any]:
    """Set up dependency management and shared libraries."""
    try:
        tech_specs = state.specifications.get("tech_specs", {})

        # Define dependency management
        dependencies_config = {
            "shared_dependencies": {
                "production": {
                    "react": "^18.0.0",
                    "typescript": "^4.9.0",
                    "axios": "^1.3.0",
                },
                "development": {
                    "jest": "^29.0.0",
                    "eslint": "^8.0.0",
                    "prettier": "^2.8.0",
                },
            },
            "workspace_config": {
                "nohoist": ["**/react", "**/react-dom"],
                "package_manager_config": {
                    "yarn": {"workspaces": True, "version": "3.x"}
                },
            },
            "dependency_policies": {
                "allowed_licenses": ["MIT", "Apache-2.0", "BSD-3-Clause"],
                "dependency_review": {
                    "required": True,
                    "criteria": ["security", "performance", "maintenance"],
                },
            },
        }

        return {
            "dependencies": dependencies_config,
            "next_node": "setup_cicd",
            "messages": ["Successfully configured dependency management"],
        }
    except Exception as e:
        return {
            "errors": [f"Error in dependency setup: {str(e)}"],
            "next_node": "human_review",
        }


async def setup_cicd(state: MonorepoState) -> Dict[str, Any]:
    """Configure CI/CD pipelines and deployment strategies."""
    try:
        # Define CI/CD configuration
        cicd_config = {
            "ci_pipeline": {
                "triggers": ["push", "pull_request"],
                "stages": [
                    {
                        "name": "lint",
                        "commands": ["yarn lint", "yarn prettier --check"],
                    },
                    {
                        "name": "test",
                        "commands": ["yarn test", "yarn test:e2e"],
                        "coverage": True,
                    },
                    {
                        "name": "build",
                        "commands": ["yarn build"],
                        "artifacts": ["dist", "build"],
                    },
                ],
            },
            "cd_pipeline": {
                "environments": {
                    "staging": {
                        "auto_deploy": True,
                        "branch": "develop",
                        "approval": False,
                    },
                    "production": {
                        "auto_deploy": False,
                        "branch": "main",
                        "approval": True,
                    },
                },
                "deployment_strategy": {
                    "type": "rolling",
                    "canary": {"enabled": True, "percentage": 10},
                },
            },
            "quality_gates": {
                "test_coverage": 80,
                "performance_budget": {"js": "200kb", "css": "50kb"},
            },
        }

        return {
            "cicd_config": cicd_config,
            "next_node": "human_review",
            "messages": ["Successfully configured CI/CD pipelines"],
        }
    except Exception as e:
        return {
            "errors": [f"Error in CI/CD setup: {str(e)}"],
            "next_node": "human_review",
        }
