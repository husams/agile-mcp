"""Response models for the Agile Management MCP Server."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StoryResponse(BaseModel):
    """Response model for story data."""

    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    structured_acceptance_criteria: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    comments: List[Dict[str, Any]]
    dev_notes: Optional[str]
    status: str
    priority: int
    created_at: Optional[str]
    epic_id: str


class ProjectResponse(BaseModel):
    """Response model for project data."""

    id: str
    name: str
    description: str


class EpicResponse(BaseModel):
    """Response model for epic data."""

    id: str
    title: str
    description: str
    status: str
    project_id: str


class ArtifactResponse(BaseModel):
    """Response model for artifact data."""

    id: str
    story_id: str
    uri: str
    relation: str


class DependencyResponse(BaseModel):
    """Response model for dependency data."""

    story_id: str
    depends_on_story_id: str


class StorySectionResponse(BaseModel):
    """Response model for story section data."""

    story_id: str
    section_name: str
    content: str


class DependencyAddResponse(BaseModel):
    """Response model for dependency addition operations."""

    status: str
    story_id: str
    depends_on_story_id: str
    message: str


class DoDChecklistResponse(BaseModel):
    """Response model for Definition of Done checklist evaluation."""

    story_id: str
    story_title: str
    story_status: str
    overall_status: str
    checklist_items: List[Dict[str, Any]]
    summary: Dict[str, int]
    recommendations: List[str]
    evaluated_at: str


class DocumentSectionResponse(BaseModel):
    """Response model for document section data."""

    id: str
    document_id: str
    title: str
    content: str
    order: int


class DocumentResponse(BaseModel):
    """Response model for document data."""

    id: str
    project_id: str
    title: str
    file_path: str
    created_at: Optional[str]
    sections: List[DocumentSectionResponse]
