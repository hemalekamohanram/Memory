# Engram implementation plan

## Assumptions

- Local development must work without Docker or cloud credentials, using SQLite, deterministic embeddings, mock Bedrock responses, and a filesystem archive.
- Live mode uses the same domain services with CockroachDB, Bedrock, and S3 adapters selected by environment variables.
- The first iteration prioritizes the exact Acme Commerce authentication demo and transparent retrieval traces.

## Phases

1. Foundation: workspace manifests, environment model, SQLAlchemy entities, Alembic/Cockroach bootstrap, health endpoints, seed/reset.
2. Memory engine: validated extraction, deterministic/live embeddings, deduplication, hybrid scoring, eligibility rules, provenance, relations, traces.
3. Agent flow: sessions, grounded responses, citations, confidence, contradiction/supersession warnings, graceful provider failures.
4. Lifecycle: consolidation preview/apply, idempotency, archive state transitions, S3/filesystem adapters, Lambda handler.
5. Product UI: dashboard, workspace and Memory Trace, explorer, timeline, consolidation center, architecture, MCP Inspector.
6. Quality: tests, accessibility, security review, infrastructure examples, README, demo and Devpost materials.

## Delivery checkpoints

- `make dev` (or the documented Windows equivalents) starts API and web.
- `seed_demo.py` creates Acme Commerce with the ADR, constraint, rejected approach, incident, successful fix, noise memories, dispute, supersession, sessions, evidence, and trace.
- A new-session parallel-refresh query returns the serializable transaction fix and exposes score components.
- Consolidation is dry-run by default and idempotent when applied.
