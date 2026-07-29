from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=5000)
    repository_url: str | None = Field(default=None, max_length=500)


class ProjectOut(ORMModel):
    id: str
    name: str
    description: str
    repository_url: str | None
    created_at: datetime


class SessionCreate(BaseModel):
    title: str = Field(default="New engineering session", min_length=1, max_length=200)


class SessionOut(ORMModel):
    id: str
    project_id: str
    title: str
    status: str
    started_at: datetime


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=5, max_length=50_000)
    event_type: str = Field(default="engineering_event", max_length=80)
    source_type: str = Field(default="user", max_length=80)
    session_id: str | None = None


class CandidateMemory(BaseModel):
    memory_type: Literal[
        "architecture_decision", "incident", "successful_fix", "rejected_approach",
        "security_constraint", "coding_standard", "team_preference",
        "deployment_observation", "task_state", "general_fact"
    ]
    title: str = Field(min_length=1, max_length=300)
    content: str = Field(min_length=3, max_length=10_000)
    importance: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    evidence_excerpt: str = Field(min_length=1, max_length=2000)


class MemoryOut(ORMModel):
    id: str
    project_id: str
    memory_type: str
    title: str
    content: str
    concise_summary: str
    importance_score: float
    confidence_score: float
    status: str
    access_count: int
    superseded_by_memory_id: str | None
    created_at: datetime


class EventIngestResult(BaseModel):
    event_id: str
    memories: list[MemoryOut]
    deduplicated_count: int = 0


class RetrieveRequest(BaseModel):
    query: str = Field(min_length=3, max_length=10_000)
    session_id: str | None = None
    limit: int = Field(default=6, ge=1, le=12)


class CandidateTrace(BaseModel):
    memory: MemoryOut
    vector_similarity: float
    importance_component: float
    recency_component: float
    confidence_component: float
    status_component: float
    final_score: float
    rank: int
    selected_for_context: bool
    selection_reason: str


class RetrievalResult(BaseModel):
    run_id: str
    query: str
    candidates: list[CandidateTrace]
    total_latency_ms: int


class MessageCreate(BaseModel):
    content: str = Field(min_length=3, max_length=10_000)


class AgentAnswer(BaseModel):
    response_id: str
    retrieval_run_id: str
    answer: str
    confidence: float
    memory_trace: list[CandidateTrace]
    mock_generated: bool


class SupersedeRequest(BaseModel):
    replacement_title: str = Field(min_length=1, max_length=300)
    replacement_content: str = Field(min_length=3, max_length=10_000)


class ConsolidationRequest(BaseModel):
    dry_run: bool = True
    similarity_threshold: float = Field(default=0.82, ge=0.5, le=1)
    idempotency_key: str = Field(min_length=8, max_length=100)


class DecisionHistoryItem(BaseModel):
    former: MemoryOut
    current: MemoryOut | None = None
    relation_type: str
    confidence: float


class HandoffBrief(BaseModel):
    project_id: str
    generated_at: datetime
    summary: str
    carry_forward: list[MemoryOut]
    do_not_repeat: list[MemoryOut]
    unresolved: list[MemoryOut]


class Envelope(BaseModel):
    data: object
    request_id: str
