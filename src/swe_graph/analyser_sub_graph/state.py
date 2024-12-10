"""State management for the researcher graph.

This module defines the state structures used in the researcher graph.
"""

from dataclasses import dataclass, field
import operator
from typing import Annotated, Dict, List, TypedDict

from langchain_core.documents import Document

from shared.state import reduce_docs
from swe_graph.state import InputState


@dataclass(kw_only=True)
class AnalyzerState(InputState):
    """State definition for the analyzer graph."""

    requirements: Dict[str, List[str]] = field(default_factory=dict)
    tech_specs: Dict[str, str] = field(default_factory=dict)
    architecture: Dict[str, str] = field(default_factory=dict)
    monorepo_structure: Dict[str, List[str]] = field(default_factory=dict)
    tasks: List[str] = field(default_factory=list)
    current_phase: str = "initial"
    next_node: str = "analyze_requirements"
    steps: List[dict] = field(default_factory=list)
