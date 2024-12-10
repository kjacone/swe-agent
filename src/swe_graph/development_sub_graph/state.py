from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import os
from pathlib import Path


@dataclass(kw_only=True)
class CodePath(BaseModel):
    """Model for code file paths and locations."""

    file_path: str
    module_path: str
    test_path: str
    relative_import_path: str
    package_name: str


@dataclass(kw_only=True)
class TestCase(BaseModel):
    """Enhanced model for test cases with paths."""

    id: str
    type: str  # unit, integration, e2e
    description: str
    requirements: List[str]
    code: str
    code_path: CodePath
    status: str = "pending"
    results: Optional[Dict] = None


@dataclass(kw_only=True)
class CodeImplementation(BaseModel):
    """Enhanced model for code implementations with paths."""

    id: str
    task_id: str
    requirements: List[str]
    code: str
    code_path: CodePath
    tests: List[str]
    status: str = "pending"
    review_comments: List[str] = field(default_factory=list)


@dataclass(kw_only=True)
class DevelopmentState(BaseModel):
    """Enhanced state management with path information."""

    tasks: List[Dict] = field(default_factory=list)
    test_cases: Dict[str, TestCase] = field(default_factory=dict)
    implementations: Dict[str, CodeImplementation] = field(default_factory=dict)
    current_task: Optional[str] = None
    code_base: Dict = field(default_factory=dict)
    root_path: str = "packages"
    test_results: Dict = field(default_factory=dict)
    coverage_reports: Dict = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    current_phase: str = "development"
    human_feedback: str = "continue"
    next_node: str = ""
    errors: List[str] = field(default_factory=list)
