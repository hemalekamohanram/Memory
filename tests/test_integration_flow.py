from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from scripts.seed_demo import ADR, INCIDENT, seed_project
from services.api.app.consolidation import ConsolidationService
from services.api.app.database import Base
from services.api.app.memory_service import (
    AgentResponseService,
    MemoryIngestionService,
    MemoryRetrievalService,
)
from services.api.app.models import (
    AgentSession,
    Memory,
    Organization,
    Project,
    RetrievalCandidate,
    User,
)


def database() -> Session:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    session.add(Organization(id="org", name="Test"))
    session.add(User(id="user", organization_id="org", display_name="Tester", email="test@example.com"))
    session.add(Project(id="project", organization_id="org", name="Acme Commerce API", description=""))
    session.commit()
    return session


def test_event_to_cross_session_answer_and_trace():
    db = database()
    first = AgentSession(id="session-1", project_id="project", user_id="user", title="Incident")
    fresh = AgentSession(id="session-2", project_id="project", user_id="user", title="Fresh")
    db.add_all([first, fresh])
    db.commit()
    service = MemoryIngestionService()
    service.ingest(db, organization_id="org", project_id="project", user_id="user",
                   title="Authentication ADR", content=ADR, event_type="adr",
                   source_type="test", session_id=first.id, request_id="request-1")
    service.ingest(db, organization_id="org", project_id="project", user_id="user",
                   title="INC-104", content=INCIDENT, event_type="incident",
                   source_type="test", session_id=first.id, request_id="request-2")
    response, retrieval = AgentResponseService().answer(
        db, "project", fresh.id, "How do we stop parallel refresh logouts?"
    )
    assert "serializable transaction" in response.response_content.lower()
    assert any(candidate.selected_for_context for candidate in retrieval.candidates)
    assert db.scalar(select(RetrievalCandidate).where(
        RetrievalCandidate.retrieval_run_id == retrieval.run_id
    ))
    db.close()


def test_superseded_memory_is_penalized():
    db = database()
    seed_project(db, "project", "org", "user")
    result = MemoryRetrievalService().retrieve(db, "project", "refresh token storage", None, 6)
    old = next(item for item in result.candidates if item.memory.title == "Legacy session storage")
    active = next(item for item in result.candidates if item.memory.status == "active")
    assert old.status_component < active.status_component
    assert old.final_score < active.final_score
    db.close()


def test_consolidation_is_idempotent():
    db = database()
    seed_project(db, "project", "org", "user")
    service = ConsolidationService()
    first = service.run(db, "project", 0.82, "same-idempotency-key", False)
    second = service.run(db, "project", 0.82, "same-idempotency-key", False)
    assert first == second
    assert db.scalar(select(Memory).where(Memory.project_id == "project"))
    db.close()
