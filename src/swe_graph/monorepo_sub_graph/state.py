"""State management for the researcher graph.

This module defines the state structures used in the researcher graph.
"""

from dataclasses import dataclass, field
from typing import Annotated, Dict, List
from pydantic import BaseModel
from langchain_core.documents import Document

from shared.state import reduce_docs


@dataclass(kw_only=True)
class MonorepoState(BaseModel):
    """State management for monorepo setup phase."""

    monorepo_config: Dict = field(default_factory=dict)
    requirements: Dict = field(default_factory=dict)
    tooling_config: Dict = field(default_factory=dict)
    dependencies: Dict = field(default_factory=dict)
    cicd_config: Dict = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)
    current_phase: str = "setup"
    human_feedback: str = "continue"
    next_node: str = ""
    errors: List[str] = field(default_factory=list)
    steps: List[dict] = field(default_factory=list)
