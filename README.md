# Engram

> **AI coding agents generate solutions. Engram remembers what the engineering team learned.**

Engram is a persistent memory operating system for engineering agents. It stores decisions, incidents, rejected approaches, successful fixes, constraints, provenance, and retrieval traces—then retrieves only relevant, current knowledge in a new session.

## Why it matters

Ordinary assistants treat memory as extra chat history. Engram treats it as governed production data: typed, tenant-scoped, evidence-backed, semantically searchable, scored transparently, superseded explicitly, consolidated safely, and archived without erasing history.

## What works

- FastAPI API with projects, sessions, events, memories, retrieval, messages, supersession, dispute, dashboard, and consolidation routes.
- Deterministic structured extraction and embeddings for a credential-free offline demo.
- CockroachDB-compatible normalized model with UUID keys, provenance, relations, audits, traces, and consolidation jobs.
- Transparent hybrid scoring and status-aware eligibility with complete persisted trace.
- New-session grounded answers that cite prior project memory.
- Consolidation preview/apply with idempotency and provenance-preserving merged status.
- Local/S3 archive adapters and a Lambda-compatible worker.
- Next.js product UI: Overview, Workspace, Memory Trace, Explorer, Timeline, Consolidation, Architecture, and MCP Inspector.
- Repeatable Acme Commerce seed/reset and smoke flow.

## Architecture

```text
Browser / Next.js → FastAPI domain services → Bedrock adapter
                                  ↓
                 CockroachDB records + VECTOR index
                                  ↓
                       Lambda → S3 evidence archive
```

Mock mode replaces Bedrock with deterministic providers, CockroachDB with SQLite compatibility, and S3 with `local-archive/`. Business logic remains shared. See [architecture](docs/architecture.md) and [memory model](docs/memory-model.md).

## Quick start: mock mode

Python 3.12 and Node 20+ are required.

```bash
python -m venv .venv
.venv/Scripts/activate          # Windows
python -m pip install -e ".[dev]"
python scripts/seed_demo.py
python -m uvicorn services.api.app.main:app --reload
```

In another terminal:

```bash
corepack enable
pnpm --dir apps/web install
pnpm --dir apps/web dev
```

Open `http://localhost:3000`; API docs are at `http://localhost:8000/docs`.

Reset or verify the exact demo:

```bash
python scripts/reset_demo.py
python scripts/smoke_demo.py
```

## Live CockroachDB and AWS mode

1. Copy `.env.example` to `.env`, set `ENGRAM_MODE=live`, and provide a TLS CockroachDB `DATABASE_URL`.
2. Set the configurable Bedrock chat/embedding model IDs and AWS region; the deployment defaults to the serverless `global.amazon.nova-2-lite-v1:0` inference profile and Titan Text Embeddings V2. Authenticate through the standard AWS credential chain.
3. Set `S3_ARCHIVE_BUCKET`, run application migrations, and create the vector index in `infrastructure/cockroach/bootstrap.sql` with the configured dimension.
4. Deploy `infrastructure/aws/template.yaml` using AWS SAM for the encrypted bucket and consolidation worker.

Never place credentials in committed files. Live provider completion and cloud deployment require external accounts and are intentionally not exercised by default tests.

## CockroachDB features

- `VECTOR` embeddings reside with structured memory and tenant metadata.
- A filtered vector index accelerates active-memory cosine search in live mode.
- Transactional access updates and persisted candidates make retrieval auditable.
- Managed MCP setup gives Codex/Claude/Cursor safe, read-only schema and trace inspection. See [MCP setup](docs/mcp-setup.md).

## Memory lifecycle and retrieval

Events are immutable evidence. Validated candidates become episodic or semantic memories. Queries create embeddings, obtain 15–25 scoped candidates, exclude expired/merged records, penalize disputed/superseded records, and rerank using configurable vector (55%), importance (18%), confidence (12%), recency (10%), and usage (5%) weights. Selected context and every score are stored before the response. Consolidation creates canonical knowledge while marking originals rather than deleting them.

## Security and reliability

Tenant scoping, bounded inputs, parameterized SQL, strict schemas, request IDs, audit writes, evidence hashes, prompt-injection boundaries, idempotency, and recoverable archive states are core design constraints. See [security](docs/security.md).

## Test and build

```bash
python -m pytest
python -m ruff check services scripts tests
python -m mypy services/api/app
pnpm --dir apps/web test
pnpm --dir apps/web build
```

## Demo and submission

- [Three-minute demo](docs/demo-script.md)
- [Devpost draft](docs/devpost-submission.md)
- [Implementation plan](docs/implementation-plan.md)

## Credential-gated integrations and roadmap

Mock mode is fully operational and computes similarity in the service so it can run without cloud resources. Live mode is implemented with native CockroachDB `VECTOR` columns and cosine ANN ordering, Alembic migrations, Bedrock Converse/tool schemas, Titan Text Embeddings V2, S3 encryption, and the Lambda worker. Those cloud paths require the operator's CockroachDB and AWS credentials and are not represented as connected until `/ready` succeeds against those services.

The next production milestones are external identity-provider integration, load testing with a large corpus, managed observability export, and multi-region recovery exercises.

MIT licensed.
