from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Sequence, Annotated
import operator
from langchain.schema import BaseMessage
from copilotkit import CopilotKitState


# File information model
class FileInfo(BaseModel):
    """Information about a file in the project."""

    path: str
    module: Optional[str] = None
    description: str
    content: Optional[str] = ""
    complete: Optional[bool] = False


# File model
class File(BaseModel):
    """File in the project."""

    key_functions: str
    path: str


class FileList(BaseModel):
    """List of files in the project."""

    module_specifications: str
    dependencies: str
    interfaces_and_integration_points: str
    implementation_notes: str
    files: List[File]


# Base module model
class BaseModule(BaseModel):
    """Base module structure in the project."""

    name: str
    description: str
    sections: List[str]
    files: List[FileInfo] = []


# Module plan model
class ModulePlan(BaseModel):
    """Detailed plan for a module."""

    name: str
    description: str
    technologies: List[str]
    dependencies: List[str]


# Section plan model
class SectionPlan(BaseModel):
    """Plan for a section within a module."""

    name: str
    description: str
    files: List[FileInfo]


# Current module being processed
class CurrentModule(BaseModel):
    """Currently active module being processed."""

    name: str
    description: str
    specification: str
    files: List[FileInfo]
    sections: List[str]
    completed_files: List[FileInfo]
    pending_files: List[FileInfo]


# Log entry model
class Log(BaseModel):
    """Log entry for tracking workflow progress."""

    message: str
    level: str
    section: str
    time: str
    done: bool
    updates: List[str]


class ArtifactContent(BaseModel):
    content: str
    module: str
    path: str
    description: str


class Artifact(BaseModel):
    current_index: int
    contents: List[ArtifactContent]


# FileState model - application state
class FileState(CopilotKitState):
    """State for the project generation workflow."""

    # artifacts
    artifacts: Artifact

    # Project information
    implementation: Dict[str, Any] = {}
    project_name: str
    project_summary: str
    project_structure_json: Annotated[Dict[str, Any], operator.or_] = Field(
        default_factory=dict, description="Project structure in JSON format"
    )

    # Flow control
    should_continue: str = "yes"
    user_input: str = ""
    last_action: str = ""
    next_node: Optional[str] = None

    # Tracking
    logs: List[dict] = Field(default_factory=list)
    files: List[File] = Field(default_factory=list)
    selected_file: Dict = {}
    processed_files: int = 0
    all_files_processed: bool = False
    previous_code: str = ""

    # Project planning
    specifications: str = ""
    pending_sections: List[dict] = Field(default_factory=list)
    completed_sections: List[dict] = Field(default_factory=list)

    formatted_plan: str = ""

    analysis: str = ""
    stream: dict
    user_stories: str = ""

    # Current processing
    current_module: Optional[dict] = None
    current_section: Optional[BaseModule] = None
    generated_files: List[Any] = Field(default_factory=list)

    module_plans: Annotated[Dict[str, ModulePlan], operator.or_] = Field(
        default_factory=dict
    )
    section_plans: Annotated[Dict[str, SectionPlan], operator.or_] = Field(
        default_factory=dict
    )

    # Workflow responses
    hitl: Optional[dict]
    response: Optional[str] = None
    follow_up: Optional[str] = None
    reflection: Optional[str] = None
