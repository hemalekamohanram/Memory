from sqlalchemy import delete, select

from scripts.seed_demo import main as seed
from scripts.seed_demo import seed_project
from services.api.app.config import get_settings
from services.api.app.database import Base, SessionLocal, engine
from services.api.app.models import (
    AgentResponse,
    AgentSession,
    AuditLog,
    ConsolidationJob,
    Event,
    Memory,
    MemoryEvidence,
    MemoryRelation,
    Project,
    RetrievalCandidate,
    RetrievalRun,
)


def reset_project(db, project: Project, organization_id: str, user_id: str) -> dict:
    run_ids = list(db.scalars(select(RetrievalRun.id).where(RetrievalRun.project_id == project.id)))
    session_ids = list(db.scalars(select(AgentSession.id).where(AgentSession.project_id == project.id)))
    memory_ids = list(db.scalars(select(Memory.id).where(Memory.project_id == project.id)))
    if run_ids:
        db.execute(delete(RetrievalCandidate).where(RetrievalCandidate.retrieval_run_id.in_(run_ids)))
    if session_ids:
        db.execute(delete(AgentResponse).where(AgentResponse.session_id.in_(session_ids)))
    db.execute(delete(RetrievalRun).where(RetrievalRun.project_id == project.id))
    db.execute(delete(ConsolidationJob).where(ConsolidationJob.project_id == project.id))
    if memory_ids:
        db.execute(delete(MemoryRelation).where(
            (MemoryRelation.from_memory_id.in_(memory_ids))
            | (MemoryRelation.to_memory_id.in_(memory_ids))
        ))
        db.execute(delete(MemoryEvidence).where(MemoryEvidence.memory_id.in_(memory_ids)))
    db.execute(delete(Memory).where(Memory.project_id == project.id))
    db.execute(delete(Event).where(Event.project_id == project.id))
    db.execute(delete(AgentSession).where(AgentSession.project_id == project.id))
    db.execute(delete(AuditLog).where(AuditLog.organization_id == organization_id))
    db.commit()
    return seed_project(db, project.id, organization_id, user_id, "reset-demo")


def reset() -> None:
    settings = get_settings()
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(
            Project.organization_id == str(settings.demo_organization_id),
            Project.name == "Acme Commerce API"))
        if project:
            reset_project(
                db,
                project,
                str(settings.demo_organization_id),
                str(settings.demo_user_id),
            )
            return
    seed()


if __name__ == "__main__":
    reset()
