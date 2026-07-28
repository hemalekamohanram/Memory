from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from services.api.app.config import get_settings
from services.api.app.database import Base, SessionLocal, engine
from services.api.app.memory_service import MemoryIngestionService, MemoryRetrievalService
from services.api.app.models import (
    AgentSession,
    Event,
    Memory,
    MemoryRelation,
    Organization,
    Project,
    User,
)

ADR = ("We are implementing authentication. We previously considered storing refresh tokens in Redis, "
       "but security rejected that approach because we need auditable transactional revocation. The approved "
       "decision is to store hashed refresh-token records in CockroachDB. Access tokens expire after 15 minutes, "
       "refresh tokens rotate on every use, and reused tokens revoke the entire token family.")
INCIDENT = ("Incident INC-104: users were unexpectedly logged out after deployment. Root cause: concurrent refresh "
            "requests caused token-family reuse detection to trigger incorrectly. The successful fix was a serializable "
            "transaction that atomically validates the active token, rotates it, and revokes the family only when a "
            "previously consumed token is reused. Adding retries for serialization failures resolved the issue.")


def stable(name: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"engram-demo:{name}"))


def seed_project(db: Session, project_id: str, organization_id: str, user_id: str,
                 request_id: str = "seed-demo") -> dict:
    existing = db.scalar(select(Memory).where(Memory.project_id == project_id))
    if existing:
        return {"project_id": project_id, "status": "already_seeded"}
    sessions = [AgentSession(id=stable("session-architecture"), project_id=project_id, user_id=user_id,
                             title="Authentication architecture"),
                AgentSession(id=stable("session-incident"), project_id=project_id, user_id=user_id,
                             title="INC-104 response")]
    db.add_all(sessions)
    db.commit()
    ingestion = MemoryIngestionService()
    ingestion.ingest(db, organization_id=organization_id, project_id=project_id, user_id=user_id,
        title="Authentication decision", content=ADR, event_type="adr", source_type="demo",
        session_id=sessions[0].id, request_id=request_id)
    ingestion.ingest(db, organization_id=organization_id, project_id=project_id, user_id=user_id,
        title="INC-104", content=INCIDENT, event_type="incident", source_type="demo",
        session_id=sessions[1].id, request_id=request_id)
    noise = [
        ("coding_standard", "Python formatting", "Backend Python uses Ruff formatting and 100 character lines."),
        ("deployment_observation", "Image build", "Web images are built in CI before deployment."),
        ("team_preference", "API errors", "The team prefers problem-detail style API errors."),
        ("general_fact", "Catalog cache", "Product catalog cache entries expire after five minutes."),
    ]
    embed = ingestion.embeddings
    for index, (kind, title, content) in enumerate(noise):
        db.add(Memory(id=stable(f"noise-{index}"), organization_id=organization_id,
            project_id=project_id, memory_type=kind, title=title, content=content,
            concise_summary=content, embedding=embed.embed(content), importance_score=0.4,
            confidence_score=0.8, status="disputed" if index == 3 else "active"))
    old = Memory(id=stable("superseded-session-storage"), organization_id=organization_id,
        project_id=project_id, memory_type="architecture_decision", title="Legacy session storage",
        content="Store refresh token state in an application-local session store.",
        concise_summary="Legacy application-local token storage.", embedding=embed.embed("refresh token session store"),
        importance_score=0.7, confidence_score=0.5, status="superseded")
    current = Memory(
        id=stable("adr-029"),
        organization_id=organization_id,
        project_id=project_id,
        memory_type="architecture_decision",
        title="ADR-029: archive token-family evidence after 90 days",
        content=(
            "Refresh-token state remains in CockroachDB. Archive token-family events to S3 "
            "after 90 days while retaining a compact security summary and evidence reference."
        ),
        concise_summary="CockroachDB operational state with 90-day S3 evidence archive.",
        embedding=embed.embed("CockroachDB refresh token S3 archive after 90 days"),
        importance_score=0.92,
        confidence_score=0.97,
        status="active",
    )
    db.add(current)
    db.flush()
    old.superseded_by_memory_id = current.id
    db.add(old)
    db.flush()
    db.add(MemoryRelation(
        id=stable("adr-029-relation"),
        from_memory_id=old.id,
        to_memory_id=current.id,
        relation_type="supersedes",
        confidence=1.0,
    ))
    db.commit()
    archived_event = db.scalar(select(Event).where(Event.project_id == project_id).limit(1))
    if archived_event:
        archived_event.archive_status = "archived"
        archived_event.s3_object_key = f"projects/{project_id}/events/{archived_event.id}.txt"
        archived_event.structured_payload = {
            **archived_event.structured_payload,
            "archive_sha256": archived_event.content_hash,
            "seeded_archive_reference": True,
        }
        db.commit()
    run = MemoryRetrievalService().retrieve(db, project_id,
        "How should parallel refresh requests avoid intermittent logouts?", sessions[1].id)
    return {"project_id": project_id, "status": "seeded", "retrieval_run_id": run.run_id}


def main() -> None:
    settings = get_settings()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        organization_id = str(settings.demo_organization_id)
        user_id = str(settings.demo_user_id)
        if not db.get(Organization, organization_id):
            db.add(Organization(id=organization_id, name="Engram Demo"))
            db.add(User(id=user_id, organization_id=organization_id,
                        display_name="Demo Engineer", email="demo@engram.local"))
        project = db.scalar(select(Project).where(Project.organization_id == organization_id,
                                                   Project.name == "Acme Commerce API"))
        if not project:
            project = Project(id=stable("acme-project"), organization_id=organization_id,
                name="Acme Commerce API", description="Persistent authentication engineering memory demo")
            db.add(project)
        db.commit()
        print(seed_project(db, project.id, organization_id, user_id))


if __name__ == "__main__":
    main()
