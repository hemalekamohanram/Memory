from sqlalchemy import select

from services.api.app.database import SessionLocal
from services.api.app.memory_service import AgentResponseService
from services.api.app.models import AgentSession, Project


def main() -> None:
    with SessionLocal() as db:
        project = db.scalar(select(Project).where(Project.name == "Acme Commerce API"))
        assert project, "Run scripts/seed_demo.py first"
        session = AgentSession(project_id=project.id, user_id="00000000-0000-0000-0000-000000000002",
                               title="Fresh smoke-test session")
        db.add(session)
        db.commit()
        response, trace = AgentResponseService().answer(db, project.id, session.id,
            "We see intermittent logouts during parallel refresh requests. How should we fix it?")
        assert "serializable transaction" in response.response_content.lower()
        assert any(item.selected_for_context for item in trace.candidates)
        print({"status": "ok", "response_id": response.id, "trace_id": trace.run_id})


if __name__ == "__main__":
    main()
