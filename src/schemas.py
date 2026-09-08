from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict

# Extraction schemas (used by LLM structured outputs)
class ActionItemExtract(BaseModel):
    task: str = Field(..., description="Clear description of the action item or deliverable")
    owner: Optional[str] = Field(None, description="Person responsible for executing the task, if mentioned")
    due_date: Optional[str] = Field(None, description="Deadline or timeframe mentioned, if any")
    confidence: float = Field(default=1.0, description="Confidence score of the extraction between 0.0 and 1.0")

class TranscriptExtractionResult(BaseModel):
    action_items: List[ActionItemExtract] = Field(
        default_factory=list,
        description="List of action items extracted from the transcript"
    )

# API Request / Response schemas
class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Title or topic of the meeting")
    transcript: str = Field(..., min_length=10, description="Raw text transcript of the meeting")

class ActionItemResponse(BaseModel):
    id: int
    meeting_id: int
    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None
    status: str
    confidence: float

    model_config = ConfigDict(from_attributes=True)

class MeetingResponse(BaseModel):
    id: int
    title: str
    transcript: str
    created_at: datetime
    action_items: List[ActionItemResponse]

    model_config = ConfigDict(from_attributes=True)

class SearchItemResult(BaseModel):
    id: int
    meeting_id: int
    meeting_title: str
    task: str
    owner: Optional[str] = None
    due_date: Optional[str] = None
    status: str
    relevance_score: float

class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchItemResult]

class HealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    llm_mode: str
    version: str
