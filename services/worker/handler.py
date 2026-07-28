from services.api.app.consolidation import ConsolidationService
from services.api.app.database import SessionLocal


def lambda_handler(event: dict, _context) -> dict:
    """Idempotent Lambda entrypoint; API and Lambda share the same consolidation service."""
    with SessionLocal() as db:
        details = ConsolidationService().run(
            db=db,
            project_id=event["project_id"],
            threshold=float(event.get("similarity_threshold", 0.82)),
            idempotency_key=event["idempotency_key"],
            dry_run=bool(event.get("dry_run", False)),
        )
    return {"statusCode": 200, "body": details}
