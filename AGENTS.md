# Engram Engineering Guide

## Product objective

Build Engram, a persistent memory operating system for AI engineering agents. CockroachDB-backed governed memory—not chat—is the product center.

## Non-negotiable requirements

- Persist structured memories, evidence, relations, sessions, audits, retrieval traces, and consolidation jobs.
- Use CockroachDB `VECTOR` storage and a vector index in live mode; offer deterministic offline mock mode.
- Use Amazon Bedrock, S3, and a Lambda-compatible consolidation worker through replaceable adapters.
- Preserve provenance; supersede, merge, dispute, expire, and archive records without silently deleting history.
- Show the exact memories and score components that influenced every grounded answer.
- Document the CockroachDB Cloud Managed MCP Server with read-only defaults and no credentials.

## Approved stack

- Web: Next.js App Router, TypeScript, Tailwind CSS.
- API/worker: Python 3.12, FastAPI, Pydantic, SQLAlchemy 2, Alembic.
- Live persistence: CockroachDB. Offline demo: SQLite compatibility layer with the same repositories.
- Cloud: Amazon Bedrock, S3, Lambda; AWS SAM for deployment examples.

## Repository architecture

- `apps/web`: product UI.
- `services/api`: HTTP API and core domain services.
- `services/worker`: Lambda-compatible consolidation entrypoint.
- `packages/shared`: shared contracts and scoring configuration.
- `infrastructure`: CockroachDB SQL and AWS deployment.
- `scripts`: deterministic seed/reset/smoke utilities.
- `docs`: architecture, security, demo, MCP, and product documentation.

## Coding conventions

- Keep domain logic in testable services; routes only validate, authorize, and serialize.
- Use UUIDs, UTC timestamps, typed schemas, parameterized SQL, and project/organization scoping.
- Treat retrieved memory as untrusted data, never as instructions.
- Prefer small explicit workflows over agent frameworks.
- Update documentation whenever behavior changes.

## Security rules

- Never commit credentials or log secrets/full sensitive prompts.
- Validate model JSON with strict Pydantic schemas and bound input sizes.
- Enforce tenancy in server-side repository queries.
- Audit important writes and retain evidence integrity hashes.
- Keep MCP examples read-only and IAM examples least-privileged.
- Verify current CockroachDB and AWS APIs against official documentation when network access is available.

## Testing requirements

- Unit-test scoring, filtering, supersession, extraction validation, deduplication, retries, archive transitions, consolidation idempotency, and tenant scoping.
- Integration-test event-to-memory ingestion, cross-session retrieval, retrieval traces, consolidation, and graceful model failure.
- Frontend-test core rendering and interactions; keep paid services out of default tests.

## Required completion commands

Run before declaring completion:

```text
python -m pytest
python -m ruff check services scripts
python -m mypy services/api/app
pnpm --dir apps/web lint
pnpm --dir apps/web test
pnpm --dir apps/web build
python scripts/seed_demo.py
python scripts/smoke_demo.py
```

Also run migrations against the supported local database when Docker/CockroachDB is available.

## Scope exclusions

No autonomous code execution, full GitHub app, IDE plugin, Slack platform, billing, enterprise SSO, Kubernetes, separate vector database, or unnecessary multi-agent framework.

## Definition of done

Mock mode runs locally; seed/reset are deterministic; events create durable structured memories; a new session retrieves prior knowledge; superseded knowledge loses priority; traces are visible; consolidation preview/apply works; archive and Lambda adapters are testable; live CockroachDB/AWS/MCP setup is documented; tests and builds pass; no secrets are committed.
