from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class StoryResponse(BaseModel):
    id: str
    title: str
    description: str
    acceptance_criteria: List[str]
    status: str
    priority: int
    created_at: Optional[str]
    epic_id: str


class EpicResponse(BaseModel):
    id: str
    title: str
    description: str
    status: str


class ArtifactResponse(BaseModel):
    id: str
    story_id: str
    uri: str
    relation: str


class DependencyResponse(BaseModel):
    story_id: str
    depends_on_story_id: str


class StorySectionResponse(BaseModel):
    story_id: str
    section_name: str
    content: str


class DependencyAddResponse(BaseModel):
    status: str
    story_id: str
    depends_on_story_id: str
    message: str


class DoDChecklistResponse(BaseModel):
    story_id: str
    story_title: str
    story_status: str
    overall_status: str
    checklist_items: List[Dict[str, Any]]
    summary: Dict[str, int]
    recommendations: List[str]
    evaluated_at: str
