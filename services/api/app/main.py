import logging
import secrets
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .bedrock import BedrockError
from .config import get_settings
from .consolidation import ConsolidationService
from .database import Base, engine, get_db
from .embeddings import DeterministicEmbeddingProvider
from .memory_service import AgentResponseService, MemoryIngestionService, MemoryRetrievalService
from .models import (
    AgentSession,
    AuditLog,
    ConsolidationJob,
    Event,
    Memory,
    MemoryRelation,
    Organization,
    Project,
    RetrievalCandidate,
    RetrievalRun,
    User,
)
from .schemas import (
    AgentAnswer,
    CandidateTrace,
    ConsolidationRequest,
    EventCreate,
    EventIngestResult,
    MemoryOut,
    MessageCreate,
    ProjectCreate,
    ProjectOut,
    RetrievalResult,
    RetrieveRequest,
    SessionCreate,
    SessionOut,
    SupersedeRequest,
)

logging.basicConfig(level=logging.INFO, format='{"level":"%(levelname)s","message":"%(message)s"}')
logger = logging.getLogger("engram")
settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    with next(get_db()) as db:
        if not db.get(Organization, str(settings.demo_organization_id)):
            db.add(Organization(id=str(settings.demo_organization_id), name="Engram Demo"))
            db.add(User(id=str(settings.demo_user_id), organization_id=str(settings.demo_organization_id),
                        display_name="Demo Engineer", email="demo@engram.local"))
            db.commit()
    yield


app = FastAPI(title="Engram API", version="0.1.0", lifespan=lifespan,
              description="Persistent governed memory for AI engineering agents")
app.add_middleware(CORSMiddleware, allow_origins=[
    settings.web_origin,
    "http://127.0.0.1:3000",
    "http://localhost:3000",
], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def request_context(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    request.state.request_id = request_id
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    logger.info("request method=%s path=%s status=%s latency_ms=%s request_id=%s",
                request.method, request.url.path, response.status_code,
                int((time.perf_counter() - started) * 1000), request_id)
    return response


def principal(x_organization_id: str | None = Header(default=None),
              x_user_id: str | None = Header(default=None),
              x_engram_key: str | None = Header(default=None)) -> tuple[str, str]:
    if settings.engram_mode == "live":
        if not settings.demo_api_key or not x_engram_key or not secrets.compare_digest(
            settings.demo_api_key, x_engram_key
        ):
            raise HTTPException(401, "Valid X-Engram-Key required in live demo mode")
    return (x_organization_id or str(settings.demo_organization_id),
            x_user_id or str(settings.demo_user_id))


@app.exception_handler(BedrockError)
async def bedrock_error_handler(_request: Request, exc: BedrockError):
    from fastapi.responses import JSONResponse

    return JSONResponse(status_code=503, content={"detail": str(exc), "retryable": True})


def scoped_project(db: Session, project_id: str, organization_id: str) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id,
                                              Project.organization_id == organization_id))
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "mode": settings.engram_mode}


@app.get("/ready")
def ready(db: Session = Depends(get_db)) -> dict:
    db.scalar(select(func.count()).select_from(Organization))
    return {"status": "ready", "database": "connected",
            "embedding_dimension": settings.embedding_dimension}


@app.post("/api/projects", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db),
                   actor: tuple[str, str] = Depends(principal)):
    organization_id, _ = actor
    project = Project(organization_id=organization_id, **payload.model_dump())
    db.add(project)
    db.commit()
    return project


@app.get("/api/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), actor: tuple[str, str] = Depends(principal)):
    return list(db.scalars(select(Project).where(Project.organization_id == actor[0])
                           .order_by(Project.updated_at.desc())))


@app.post("/api/projects/{project_id}/sessions", response_model=SessionOut, status_code=201)
def create_session(project_id: str, payload: SessionCreate, db: Session = Depends(get_db),
                   actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    session = AgentSession(project_id=project_id, user_id=actor[1], title=payload.title)
    db.add(session)
    db.commit()
    return session


@app.get("/api/projects/{project_id}/sessions", response_model=list[SessionOut])
def list_sessions(project_id: str, db: Session = Depends(get_db),
                  actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    return list(db.scalars(select(AgentSession).where(AgentSession.project_id == project_id)
                           .order_by(AgentSession.started_at.desc())))


@app.post("/api/projects/{project_id}/events", response_model=EventIngestResult, status_code=201)
def ingest_event(project_id: str, payload: EventCreate, request: Request,
                 db: Session = Depends(get_db), actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    event, memories, deduped = MemoryIngestionService().ingest(db, organization_id=actor[0],
        project_id=project_id, user_id=actor[1], request_id=request.state.request_id,
        title=payload.title, content=payload.content, event_type=payload.event_type,
        source_type=payload.source_type, session_id=payload.session_id)
    return EventIngestResult(event_id=event.id, memories=[MemoryOut.model_validate(m) for m in memories],
                             deduplicated_count=deduped)


@app.get("/api/projects/{project_id}/memories", response_model=list[MemoryOut])
def list_memories(project_id: str, status: str | None = None, memory_type: str | None = None,
                  db: Session = Depends(get_db), actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    query = select(Memory).where(Memory.project_id == project_id,
                                 Memory.organization_id == actor[0])
    if status:
        query = query.where(Memory.status == status)
    if memory_type:
        query = query.where(Memory.memory_type == memory_type)
    return list(db.scalars(query.order_by(Memory.updated_at.desc())))


@app.get("/api/memories/{memory_id}", response_model=MemoryOut)
def get_memory(memory_id: str, db: Session = Depends(get_db),
               actor: tuple[str, str] = Depends(principal)):
    memory = db.scalar(select(Memory).where(Memory.id == memory_id,
                                            Memory.organization_id == actor[0]))
    if not memory:
        raise HTTPException(404, "Memory not found")
    return memory


@app.post("/api/projects/{project_id}/retrieve", response_model=RetrievalResult)
def retrieve(project_id: str, payload: RetrieveRequest, db: Session = Depends(get_db),
             actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    return MemoryRetrievalService().retrieve(db, project_id, payload.query,
                                              payload.session_id, payload.limit)


@app.get("/api/retrieval-runs/{run_id}", response_model=RetrievalResult)
def get_retrieval_run(run_id: str, db: Session = Depends(get_db),
                      actor: tuple[str, str] = Depends(principal)):
    run = db.get(RetrievalRun, run_id)
    if not run:
        raise HTTPException(404, "Retrieval run not found")
    scoped_project(db, run.project_id, actor[0])
    rows = list(db.execute(
        select(RetrievalCandidate, Memory)
        .join(Memory, Memory.id == RetrievalCandidate.memory_id)
        .where(RetrievalCandidate.retrieval_run_id == run_id)
        .order_by(RetrievalCandidate.rank)
    ))
    traces = [
        CandidateTrace(
            memory=MemoryOut.model_validate(memory),
            vector_similarity=candidate.vector_similarity,
            importance_component=candidate.importance_component,
            recency_component=candidate.recency_component,
            confidence_component=candidate.confidence_component,
            status_component=candidate.status_component,
            final_score=candidate.final_score,
            rank=candidate.rank,
            selected_for_context=candidate.selected_for_context,
            selection_reason=candidate.selection_reason,
        )
        for candidate, memory in rows
    ]
    return RetrievalResult(run_id=run.id, query=run.query_text, candidates=traces,
                           total_latency_ms=run.total_latency_ms)


@app.post("/api/sessions/{session_id}/messages", response_model=AgentAnswer)
def message(session_id: str, payload: MessageCreate, db: Session = Depends(get_db),
            actor: tuple[str, str] = Depends(principal)):
    session = db.get(AgentSession, session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    scoped_project(db, session.project_id, actor[0])
    response, retrieval = AgentResponseService().answer(db, session.project_id, session_id,
                                                         payload.content)
    return AgentAnswer(response_id=response.id, retrieval_run_id=retrieval.run_id,
        answer=response.response_content, confidence=response.confidence,
        memory_trace=retrieval.candidates, mock_generated=settings.engram_mode == "mock")


@app.post("/api/memories/{memory_id}/dispute", response_model=MemoryOut)
def dispute(memory_id: str, db: Session = Depends(get_db),
            actor: tuple[str, str] = Depends(principal)):
    memory = db.scalar(select(Memory).where(Memory.id == memory_id,
                                            Memory.organization_id == actor[0]))
    if not memory:
        raise HTTPException(404, "Memory not found")
    memory.status = "disputed"
    db.commit()
    return memory


@app.post("/api/memories/{memory_id}/supersede", response_model=MemoryOut)
def supersede(memory_id: str, payload: SupersedeRequest, request: Request,
              db: Session = Depends(get_db), actor: tuple[str, str] = Depends(principal)):
    old = db.scalar(select(Memory).where(Memory.id == memory_id, Memory.organization_id == actor[0]))
    if not old:
        raise HTTPException(404, "Memory not found")
    replacement = Memory(organization_id=old.organization_id, project_id=old.project_id,
        memory_type=old.memory_type, title=payload.replacement_title, content=payload.replacement_content,
        concise_summary=payload.replacement_content[:300],
        embedding=DeterministicEmbeddingProvider().embed(payload.replacement_content),
        importance_score=old.importance_score, confidence_score=0.95)
    db.add(replacement)
    db.flush()
    old.status = "superseded"
    old.superseded_by_memory_id = replacement.id
    db.add(MemoryRelation(from_memory_id=old.id, to_memory_id=replacement.id,
                          relation_type="supersedes", confidence=1.0))
    db.add(AuditLog(organization_id=actor[0], actor_type="user", actor_id=actor[1],
        action="memory.superseded", resource_type="memory", resource_id=old.id,
        request_id=request.state.request_id, metadata_json={"replacement_id": replacement.id}))
    db.commit()
    return replacement


@app.post("/api/projects/{project_id}/consolidation/preview")
def consolidation_preview(project_id: str, payload: ConsolidationRequest,
                          db: Session = Depends(get_db), actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    return ConsolidationService().preview(db, project_id, payload.similarity_threshold)


@app.post("/api/projects/{project_id}/consolidation/run")
def consolidation_run(project_id: str, payload: ConsolidationRequest,
                      db: Session = Depends(get_db), actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    return ConsolidationService().run(db, project_id, payload.similarity_threshold,
                                      payload.idempotency_key, payload.dry_run)


@app.get("/api/consolidation-jobs/{job_id}")
def get_consolidation_job(job_id: str, db: Session = Depends(get_db),
                          actor: tuple[str, str] = Depends(principal)):
    job = db.get(ConsolidationJob, job_id)
    if not job:
        raise HTTPException(404, "Consolidation job not found")
    scoped_project(db, job.project_id, actor[0])
    return {"id": job.id, "status": job.status, "details": job.details,
            "started_at": job.started_at, "completed_at": job.completed_at}


@app.get("/api/projects/{project_id}/dashboard")
def dashboard(project_id: str, db: Session = Depends(get_db),
              actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    rows = list(db.scalars(select(Memory).where(Memory.project_id == project_id)))
    events = db.scalar(select(func.count()).select_from(Event).where(Event.project_id == project_id)) or 0
    sessions = db.scalar(select(func.count()).select_from(AgentSession).where(
        AgentSession.project_id == project_id)) or 0
    by_type: dict[str, int] = {}
    for memory in rows:
        by_type[memory.memory_type] = by_type.get(memory.memory_type, 0) + 1
    return {"active_memories": sum(m.status == "active" for m in rows),
            "superseded_memories": sum(m.status == "superseded" for m in rows),
            "disputed_memories": sum(m.status == "disputed" for m in rows),
            "archived_evidence": sum(m.status == "archived" for m in rows),
            "events": events, "sessions": sessions, "memory_types": by_type}


@app.post("/api/projects/{project_id}/seed-demo")
def seed_demo_route(project_id: str, request: Request, db: Session = Depends(get_db),
                    actor: tuple[str, str] = Depends(principal)):
    scoped_project(db, project_id, actor[0])
    from scripts.seed_demo import seed_project
    return seed_project(db, project_id, actor[0], actor[1], request.state.request_id)


@app.post("/api/projects/{project_id}/reset-demo")
def reset_demo_route(project_id: str, db: Session = Depends(get_db),
                     actor: tuple[str, str] = Depends(principal)):
    project = scoped_project(db, project_id, actor[0])
    from scripts.reset_demo import reset_project

    return reset_project(db, project, actor[0], actor[1])
