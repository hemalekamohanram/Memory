import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base
from .uuid_type import UUIDString
from .vector_type import VectorJSON


def utcnow() -> datetime:
    return datetime.now(UTC)


class MemoryStatus(str, enum.Enum):
    active = "active"
    superseded = "superseded"
    merged = "merged"
    expired = "expired"
    disputed = "disputed"
    archived = "archived"


class MemoryType(str, enum.Enum):
    architecture_decision = "architecture_decision"
    incident = "incident"
    successful_fix = "successful_fix"
    rejected_approach = "rejected_approach"
    security_constraint = "security_constraint"
    coding_standard = "coding_standard"
    team_preference = "team_preference"
    deployment_observation = "deployment_observation"
    task_state = "task_state"
    general_fact = "general_fact"


class IdMixin:
    id: Mapped[str] = mapped_column(UUIDString(), primary_key=True, default=lambda: str(uuid.uuid4()))


class Organization(IdMixin, Base):
    __tablename__ = "organizations"
    name: Mapped[str] = mapped_column(String(200), unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class User(IdMixin, Base):
    __tablename__ = "users"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    display_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Project(IdMixin, Base):
    __tablename__ = "projects"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    repository_url: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    __table_args__ = (UniqueConstraint("organization_id", "name"),)


class AgentSession(IdMixin, Base):
    __tablename__ = "agent_sessions"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(30), default="active")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Event(IdMixin, Base):
    __tablename__ = "events"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("agent_sessions.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(80))
    source_type: Mapped[str] = mapped_column(String(80), default="user")
    title: Mapped[str] = mapped_column(String(300))
    raw_content: Mapped[str] = mapped_column(Text)
    structured_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    content_hash: Mapped[str] = mapped_column(String(64))
    archive_status: Mapped[str] = mapped_column(String(30), default="local")
    s3_object_key: Mapped[str | None] = mapped_column(String(1000))
    created_by: Mapped[str] = mapped_column(UUIDString())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    __table_args__ = (UniqueConstraint("project_id", "content_hash"),)


class Memory(IdMixin, Base):
    __tablename__ = "memories"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    memory_type: Mapped[str] = mapped_column(String(50), index=True)
    title: Mapped[str] = mapped_column(String(300))
    content: Mapped[str] = mapped_column(Text)
    concise_summary: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float]] = mapped_column(VectorJSON())
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    status: Mapped[str] = mapped_column(String(30), default=MemoryStatus.active.value, index=True)
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    access_count: Mapped[int] = mapped_column(Integer, default=0)
    last_accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    canonical_memory_id: Mapped[str | None] = mapped_column(ForeignKey("memories.id"))
    superseded_by_memory_id: Mapped[str | None] = mapped_column(ForeignKey("memories.id"))
    created_from_event_id: Mapped[str | None] = mapped_column(ForeignKey("events.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)
    evidence: Mapped[list["MemoryEvidence"]] = relationship(cascade="all, delete-orphan")
    __table_args__ = (Index("ix_memories_project_status_type", "project_id", "status", "memory_type"),)


class MemoryEvidence(Base):
    __tablename__ = "memory_evidence"
    memory_id: Mapped[str] = mapped_column(ForeignKey("memories.id"), primary_key=True)
    event_id: Mapped[str] = mapped_column(ForeignKey("events.id"), primary_key=True)
    evidence_excerpt: Mapped[str] = mapped_column(Text)
    source_weight: Mapped[float] = mapped_column(Float, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class MemoryRelation(IdMixin, Base):
    __tablename__ = "memory_relations"
    from_memory_id: Mapped[str] = mapped_column(ForeignKey("memories.id"), index=True)
    to_memory_id: Mapped[str] = mapped_column(ForeignKey("memories.id"), index=True)
    relation_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class RetrievalRun(IdMixin, Base):
    __tablename__ = "retrieval_runs"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    session_id: Mapped[str | None] = mapped_column(ForeignKey("agent_sessions.id"))
    query_text: Mapped[str] = mapped_column(Text)
    query_embedding: Mapped[list[float]] = mapped_column(VectorJSON())
    retrieval_configuration: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    total_latency_ms: Mapped[int] = mapped_column(Integer)
    candidates: Mapped[list["RetrievalCandidate"]] = relationship(cascade="all, delete-orphan")


class RetrievalCandidate(Base):
    __tablename__ = "retrieval_candidates"
    retrieval_run_id: Mapped[str] = mapped_column(ForeignKey("retrieval_runs.id"), primary_key=True)
    memory_id: Mapped[str] = mapped_column(ForeignKey("memories.id"), primary_key=True)
    vector_similarity: Mapped[float] = mapped_column(Float)
    importance_component: Mapped[float] = mapped_column(Float)
    recency_component: Mapped[float] = mapped_column(Float)
    confidence_component: Mapped[float] = mapped_column(Float)
    status_component: Mapped[float] = mapped_column(Float)
    final_score: Mapped[float] = mapped_column(Float)
    rank: Mapped[int] = mapped_column(Integer)
    selected_for_context: Mapped[bool] = mapped_column(default=False)
    selection_reason: Mapped[str] = mapped_column(Text)


class AgentResponse(IdMixin, Base):
    __tablename__ = "agent_responses"
    session_id: Mapped[str] = mapped_column(ForeignKey("agent_sessions.id"), index=True)
    retrieval_run_id: Mapped[str | None] = mapped_column(ForeignKey("retrieval_runs.id"))
    user_prompt: Mapped[str] = mapped_column(Text)
    response_content: Mapped[str] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float)
    model_id: Mapped[str] = mapped_column(String(200))
    prompt_version: Mapped[str] = mapped_column(String(30), default="v1")
    usage_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConsolidationJob(IdMixin, Base):
    __tablename__ = "consolidation_jobs"
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), index=True)
    status: Mapped[str] = mapped_column(String(30))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    input_memory_count: Mapped[int] = mapped_column(Integer, default=0)
    output_memory_count: Mapped[int] = mapped_column(Integer, default=0)
    merged_count: Mapped[int] = mapped_column(Integer, default=0)
    superseded_count: Mapped[int] = mapped_column(Integer, default=0)
    archived_event_count: Mapped[int] = mapped_column(Integer, default=0)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    idempotency_key: Mapped[str] = mapped_column(String(100), unique=True)
    error_message: Mapped[str | None] = mapped_column(Text)


class AuditLog(IdMixin, Base):
    __tablename__ = "audit_logs"
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"), index=True)
    actor_type: Mapped[str] = mapped_column(String(30))
    actor_id: Mapped[str | None] = mapped_column(UUIDString())
    action: Mapped[str] = mapped_column(String(100))
    resource_type: Mapped[str] = mapped_column(String(80))
    resource_id: Mapped[str | None] = mapped_column(UUIDString())
    request_id: Mapped[str] = mapped_column(String(100), index=True)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
