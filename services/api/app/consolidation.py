from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from .archive import get_archive_service
from .embeddings import cosine_similarity
from .models import ConsolidationJob, Event, Memory, MemoryRelation


class ConsolidationService:
    def preview(self, db: Session, project_id: str, threshold: float) -> dict:
        memories = list(db.scalars(select(Memory).where(
            Memory.project_id == project_id, Memory.status == "active")))
        groups: list[list[Memory]] = []
        used: set[str] = set()
        for memory in memories:
            if memory.id in used:
                continue
            group = [memory]
            for other in memories:
                if other.id == memory.id or other.id in used or other.memory_type != memory.memory_type:
                    continue
                if cosine_similarity(memory.embedding, other.embedding) >= threshold:
                    group.append(other)
            if len(group) > 1:
                groups.append(group)
                used.update(item.id for item in group)
        temporary = [m for m in memories if m.memory_type == "task_state" and not m.expires_at]
        return {"before": {"active_memories": len(memories), "overlapping_groups": len(groups)},
                "groups": [{"memory_ids": [m.id for m in g],
                            "proposed_title": max(g, key=lambda m: m.confidence_score).title,
                            "type": g[0].memory_type} for g in groups],
                "temporary_to_expire": [m.id for m in temporary],
                "after": {"active_memories": len(memories) - sum(len(g) - 1 for g in groups),
                          "merged_memories": sum(len(g) - 1 for g in groups)}}

    def run(self, db: Session, project_id: str, threshold: float, idempotency_key: str,
            dry_run: bool) -> dict:
        existing = db.scalar(select(ConsolidationJob).where(
            ConsolidationJob.idempotency_key == idempotency_key))
        if existing:
            return existing.details
        preview = self.preview(db, project_id, threshold)
        if dry_run:
            return {**preview, "dry_run": True}
        job = ConsolidationJob(project_id=project_id, status="running",
            input_memory_count=preview["before"]["active_memories"], idempotency_key=idempotency_key)
        db.add(job)
        db.flush()
        merged = 0
        for group_data in preview["groups"]:
            group = list(db.scalars(select(Memory).where(Memory.id.in_(group_data["memory_ids"]))))
            canonical = max(group, key=lambda m: (m.confidence_score, m.importance_score))
            canonical.canonical_memory_id = canonical.id
            for memory in group:
                if memory.id == canonical.id:
                    continue
                memory.status = "merged"
                memory.canonical_memory_id = canonical.id
                db.add(MemoryRelation(from_memory_id=memory.id, to_memory_id=canonical.id,
                                      relation_type="derived_from", confidence=1.0))
                merged += 1
        for memory_id in preview["temporary_to_expire"]:
            temporary_memory = db.get(Memory, memory_id)
            if temporary_memory:
                temporary_memory.expires_at = datetime.now(UTC) + timedelta(days=7)
        archived = 0
        archive = get_archive_service()
        events = list(db.scalars(select(Event).where(
            Event.project_id == project_id,
            Event.archive_status.in_(["local", "pending", "failed"]),
        )))
        for event in events:
            if len(event.raw_content) < 400:
                continue
            event.archive_status = "pending"
            try:
                result = archive.store(project_id, event.id, event.raw_content.encode())
                event.s3_object_key = result["object_key"]
                event.archive_status = "archived"
                event.structured_payload = {
                    **event.structured_payload,
                    "archive_sha256": result["sha256"],
                }
                archived += 1
            except Exception as exc:
                event.archive_status = "failed"
                event.structured_payload = {
                    **event.structured_payload,
                    "archive_error": type(exc).__name__,
                }
        job.status = "completed"
        job.completed_at = datetime.now(UTC)
        job.merged_count = merged
        job.output_memory_count = job.input_memory_count - merged
        job.archived_event_count = archived
        job.details = {
            **preview,
            "dry_run": False,
            "job_id": job.id,
            "archived_event_count": archived,
        }
        db.commit()
        return job.details
