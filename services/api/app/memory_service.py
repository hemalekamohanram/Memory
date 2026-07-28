import hashlib
import math
import re
import time
from datetime import UTC, datetime
from typing import Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import cast, select
from sqlalchemy.orm import Session

from .config import get_settings
from .embeddings import cosine_similarity, get_embedding_provider
from .models import (
    AgentResponse,
    AuditLog,
    Event,
    Memory,
    MemoryEvidence,
    MemoryRelation,
    RetrievalCandidate,
    RetrievalRun,
)
from .schemas import CandidateMemory, CandidateTrace, MemoryOut, RetrievalResult


def _candidate(memory_type: str, title: str, content: str, importance: float,
               confidence: float, evidence: str) -> CandidateMemory:
    return CandidateMemory(memory_type=memory_type, title=title, content=content,
                           importance=importance, confidence=confidence,
                           evidence_excerpt=evidence[:2000])


class MemoryExtractionService:
    """Deterministic mock extractor for the demo; live Bedrock implements the same contract."""

    def extract(self, title: str, content: str) -> list[CandidateMemory]:
        lower = content.lower()
        items: list[CandidateMemory] = []
        if "incident" in lower or re.search(r"inc-\d+", lower):
            incident_id = (re.search(r"inc-\d+", content, re.I) or ["Incident"])[0]
            items.append(_candidate("incident", f"{incident_id}: concurrent refresh logout",
                content, 0.94, 0.96, content))
        if "successful fix" in lower or "resolved the issue" in lower:
            items.append(_candidate("successful_fix", "Serializable refresh-token rotation",
                "Use a serializable transaction to atomically validate the active refresh token, rotate it, "
                "and revoke the family only when a previously consumed token is reused. Retry serialization failures.",
                0.98, 0.98, content))
        if "security rejected" in lower or "security" in lower and "refresh" in lower:
            items.append(_candidate("security_constraint", "Refresh revocation must be auditable",
                "Refresh-token revocation requires auditable transactional records in CockroachDB.",
                0.97, 0.97, content))
        if "redis" in lower and ("rejected" in lower or "considered" in lower):
            items.append(_candidate("rejected_approach", "Do not store refresh-token state in Redis",
                "Redis refresh-token storage was rejected because revocation must be auditable and transactional.",
                0.9, 0.96, content))
        if "approved decision" in lower or "adr-" in lower or "supersedes" in lower:
            if "s3" in lower:
                decision = ("Keep operational refresh-token state and compact security summaries in CockroachDB; "
                            "archive token-family evidence to S3 after 90 days and retain its reference.")
                decision_title = "ADR-029: archive token-family evidence after 90 days"
            else:
                decision = ("Store hashed refresh-token records in CockroachDB. Access tokens expire after 15 minutes; "
                            "refresh tokens rotate on every use; reuse revokes the token family.")
                decision_title = "CockroachDB refresh-token architecture"
            items.append(_candidate("architecture_decision", decision_title, decision, 0.98, 0.98, content))
        if not items:
            kind = "coding_standard" if any(word in lower for word in ("standard", "must", "convention")) else "general_fact"
            items.append(_candidate(kind, title, content, 0.55, 0.72, content))
        return items


class MemoryIngestionService:
    def __init__(self) -> None:
        settings = get_settings()
        self.extractor: Any
        if settings.engram_mode == "live":
            from .bedrock import BedrockAgentProvider

            self.extractor = BedrockAgentProvider()
        else:
            self.extractor = MemoryExtractionService()
        self.embeddings = get_embedding_provider()

    def ingest(self, db: Session, *, organization_id: str, project_id: str, user_id: str,
               title: str, content: str, event_type: str, source_type: str,
               session_id: str | None, request_id: str) -> tuple[Event, list[Memory], int]:
        content_hash = hashlib.sha256(content.strip().encode()).hexdigest()
        existing_event = db.scalar(select(Event).where(Event.project_id == project_id,
                                                        Event.content_hash == content_hash))
        if existing_event:
            memories = list(db.scalars(select(Memory).where(
                Memory.created_from_event_id == existing_event.id)))
            return existing_event, memories, len(memories)
        event = Event(organization_id=organization_id, project_id=project_id,
                      session_id=session_id, event_type=event_type, source_type=source_type,
                      title=title, raw_content=content, structured_payload={},
                      content_hash=content_hash, created_by=user_id)
        db.add(event)
        db.flush()
        created: list[Memory] = []
        deduped = 0
        for candidate in self.extractor.extract(title, content):
            embedding = self.embeddings.embed(candidate.content)
            possible = list(db.scalars(select(Memory).where(
                Memory.project_id == project_id,
                Memory.memory_type == candidate.memory_type,
                Memory.status.in_(["active", "disputed"]))))
            duplicate = next((m for m in possible if cosine_similarity(embedding, m.embedding) >= 0.97), None)
            if duplicate:
                db.add(MemoryEvidence(memory_id=duplicate.id, event_id=event.id,
                                      evidence_excerpt=candidate.evidence_excerpt, source_weight=1.0))
                duplicate.confidence_score = max(duplicate.confidence_score, candidate.confidence)
                duplicate.importance_score = max(duplicate.importance_score, candidate.importance)
                deduped += 1
                continue
            memory = Memory(organization_id=organization_id, project_id=project_id,
                            memory_type=candidate.memory_type, title=candidate.title,
                            content=candidate.content, concise_summary=candidate.content[:300],
                            embedding=embedding, importance_score=candidate.importance,
                            confidence_score=candidate.confidence, created_from_event_id=event.id)
            db.add(memory)
            db.flush()
            db.add(MemoryEvidence(memory_id=memory.id, event_id=event.id,
                                  evidence_excerpt=candidate.evidence_excerpt, source_weight=1.0))
            created.append(memory)
        event.structured_payload = {"memory_ids": [m.id for m in created], "extractor": "mock-v1"}
        self._link_related(db, project_id, created)
        db.add(AuditLog(organization_id=organization_id, actor_type="user", actor_id=user_id,
                        action="event.ingested", resource_type="event", resource_id=event.id,
                        request_id=request_id, metadata_json={"memory_count": len(created)}))
        db.commit()
        return event, created, deduped

    def _link_related(self, db: Session, project_id: str, created: list[Memory]) -> None:
        all_memories = list(db.scalars(select(Memory).where(Memory.project_id == project_id)))
        for memory in created:
            for other in all_memories:
                if memory.id == other.id:
                    continue
                similarity = cosine_similarity(memory.embedding, other.embedding)
                if similarity >= 0.3:
                    relation = "resolved_by" if other.memory_type == "incident" and memory.memory_type == "successful_fix" else "related_to"
                    db.add(MemoryRelation(from_memory_id=other.id, to_memory_id=memory.id,
                                          relation_type=relation, confidence=max(0.6, similarity)))


class MemoryRetrievalService:
    weights = {"vector": 0.55, "importance": 0.18, "confidence": 0.12,
               "recency": 0.10, "usage": 0.05}
    status_adjustments = {"active": 1.0, "disputed": 0.45, "superseded": 0.08,
                          "merged": 0.0, "expired": 0.0, "archived": 0.15}

    def __init__(self) -> None:
        self.embeddings = get_embedding_provider()

    @staticmethod
    def recency_score(created_at: datetime, now: datetime | None = None) -> float:
        now = now or datetime.now(UTC)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=UTC)
        age_days = max(0.0, (now - created_at).total_seconds() / 86400)
        return math.exp(-age_days / 365)

    def retrieve(self, db: Session, project_id: str, query: str,
                 session_id: str | None, limit: int = 6) -> RetrievalResult:
        started = time.perf_counter()
        query_embedding = self.embeddings.embed(query)
        now = datetime.now(UTC)
        database_native = db.bind is not None and db.bind.dialect.name != "sqlite"
        if database_native:
            dimension = get_settings().effective_embedding_dimension
            distance = cast(Memory.embedding, Vector(dimension)).cosine_distance(query_embedding)
            native_rows: list[tuple[Memory, float]] = [
                (row[0], float(row[1]))
                for row in db.execute(
                select(Memory, (1 - distance).label("similarity"))
                .where(Memory.project_id == project_id)
                .where(Memory.status.in_(["active", "disputed", "superseded", "archived"]))
                .order_by(distance)
                .limit(25)
                )
            ]
        else:
            native_rows = [(memory, cosine_similarity(query_embedding, memory.embedding)) for memory in
                           db.scalars(select(Memory).where(Memory.project_id == project_id))]
        scored: list[tuple[Memory, dict[str, float]]] = []
        for memory, raw_similarity in native_rows:
            expires_at = memory.expires_at
            if expires_at and expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=UTC)
            if expires_at and expires_at <= now:
                continue
            status = self.status_adjustments.get(memory.status, 0.0)
            if status == 0:
                continue
            vector = (raw_similarity + 1) / 2
            recency = self.recency_score(memory.created_at, now)
            usage = min(1.0, math.log1p(memory.access_count) / math.log(11))
            base = (self.weights["vector"] * vector + self.weights["importance"] * memory.importance_score
                    + self.weights["confidence"] * memory.confidence_score
                    + self.weights["recency"] * recency + self.weights["usage"] * usage)
            scored.append((memory, {"similarity": vector, "recency": recency,
                                    "status": status, "final": base * status}))
        scored.sort(key=lambda item: item[1]["final"], reverse=True)
        latency = int((time.perf_counter() - started) * 1000)
        run = RetrievalRun(project_id=project_id, session_id=session_id, query_text=query,
                           query_embedding=query_embedding,
                           retrieval_configuration={"weights": self.weights, "limit": limit},
                           total_latency_ms=latency)
        db.add(run)
        db.flush()
        traces: list[CandidateTrace] = []
        for rank, (memory, scores) in enumerate(scored[:25], 1):
            selected = rank <= limit and memory.status in ("active", "disputed")
            reason = ("Selected: semantically relevant, valid, and high-confidence."
                      if selected else f"Not selected: rank {rank} or status {memory.status}.")
            row = RetrievalCandidate(retrieval_run_id=run.id, memory_id=memory.id,
                vector_similarity=scores["similarity"], importance_component=memory.importance_score,
                recency_component=scores["recency"], confidence_component=memory.confidence_score,
                status_component=scores["status"], final_score=scores["final"], rank=rank,
                selected_for_context=selected, selection_reason=reason)
            db.add(row)
            if selected:
                memory.access_count += 1
                memory.last_accessed_at = now
            traces.append(CandidateTrace(memory=MemoryOut.model_validate(memory),
                vector_similarity=scores["similarity"], importance_component=memory.importance_score,
                recency_component=scores["recency"], confidence_component=memory.confidence_score,
                status_component=scores["status"], final_score=scores["final"], rank=rank,
                selected_for_context=selected, selection_reason=reason))
        db.commit()
        return RetrievalResult(run_id=run.id, query=query, candidates=traces, total_latency_ms=latency)


class AgentResponseService:
    def __init__(self) -> None:
        self.retrieval = MemoryRetrievalService()

    def answer(self, db: Session, project_id: str, session_id: str, prompt: str) -> tuple[AgentResponse, RetrievalResult]:
        result = self.retrieval.retrieve(db, project_id, prompt, session_id)
        selected = [t for t in result.candidates if t.selected_for_context]
        fixes = [t for t in selected if t.memory.memory_type == "successful_fix"]
        incidents = [t for t in selected if t.memory.memory_type == "incident"]
        constraints = [t for t in selected if t.memory.memory_type == "security_constraint"]
        if get_settings().engram_mode == "live" and selected:
            from .bedrock import BedrockAgentProvider

            answer = BedrockAgentProvider().answer(prompt, [
                {"memory_id": trace.memory.id, "type": trace.memory.memory_type,
                 "status": trace.memory.status, "content": trace.memory.content}
                for trace in selected
            ])
        elif fixes:
            primary = fixes[0].memory
            answer = (f"Recommended action: {primary.content} [{primary.id[:8]}]\n\n"
                      "This is confirmed historical evidence from a successful repair, not a new inference. ")
            if incidents:
                answer += f"It addresses the concurrent-refresh failure recorded in {incidents[0].memory.title} [{incidents[0].memory.id[:8]}]. "
            if constraints:
                answer += f"It also preserves the auditable revocation requirement [{constraints[0].memory.id[:8]}]. "
            answer += "Validate with a parallel-refresh concurrency test and monitor serialization retry exhaustion."
        elif selected:
            citations = ", ".join(f"[{trace.memory.id[:8]}]" for trace in selected[:3])
            answer = (f"The available project memory suggests: {selected[0].memory.content} {citations}\n\n"
                      "Memory coverage is partial; confirm the recommendation before production use.")
        else:
            answer = "Engram has insufficient relevant project memory to recommend a confirmed fix. Record an ADR, incident, or verified repair first."
        confidence = round(sum(t.memory.confidence_score for t in selected) / max(1, len(selected)), 2)
        response = AgentResponse(session_id=session_id, retrieval_run_id=result.run_id,
            user_prompt=prompt, response_content=answer, confidence=confidence,
            model_id=(get_settings().bedrock_chat_model_id if get_settings().engram_mode == "live"
                      else "deterministic-mock-v1"),
            usage_metadata={"selected_memories": len(selected)})
        db.add(response)
        db.commit()
        return response, result
