from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import MemorySaver
import os
from pathlib import Path


@dataclass(kw_only=True)
class DocumentationSection(BaseModel):
    """Model for individual documentation sections."""

    id: str
    title: str
    content: str
    path: str
    format: str  # md, mdx, rst
    status: str = "draft"
    review_comments: List[str] = field(default_factory=list)


@dataclass(kw_only=True)
class APIEndpoint(BaseModel):
    """Model for API endpoint documentation."""

    path: str
    method: str
    description: str
    parameters: List[Dict]
    responses: Dict[str, Any]
    examples: List[Dict]


@dataclass(kw_only=True)
class DocumentationState(BaseModel):
    """State management for documentation phase."""

    code_base: Dict = field(default_factory=dict)
    api_docs: Dict[str, APIEndpoint] = field(default_factory=dict)
    user_guides: Dict[str, DocumentationSection] = field(default_factory=dict)
    developer_docs: Dict[str, DocumentationSection] = field(default_factory=dict)
    architecture_docs: Dict[str, DocumentationSection] = field(default_factory=dict)
    deployment_guides: Dict[str, DocumentationSection] = field(default_factory=dict)
    release_notes: List[Dict] = field(default_factory=list)
    current_section: Optional[str] = None
    messages: List[str] = field(default_factory=list)
    current_phase: str = "documentation"
    human_feedback: str = "continue"
    next_node: str = ""
    errors: List[str] = field(default_factory=list)
