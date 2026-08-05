# Devpost submission draft

## Inspiration
AI coding agents are fast but forget why a team rejected an approach, how an incident was fixed, or which decision is current.

## What it does
Engram turns engineering events into governed memories, retrieves valid knowledge across sessions, explains every selected memory, preserves supersession history, and consolidates duplicates without deleting evidence. Decision Graveyard keeps outdated decisions visible without letting them become current advice; Agent Handoff gives the next agent verified context, known failures, and open questions.

## How it was built
Next.js presents the workspace and Memory Trace. FastAPI and SQLAlchemy implement extraction, scoring, lifecycle, provenance, and audit services. CockroachDB stores structured and vector memory. Bedrock powers live extraction/reasoning, Lambda runs idempotent consolidation, and S3 archives large evidence. Deterministic adapters make the full demo available offline.

## CockroachDB tools
Distributed Vector Indexing performs organization/project-scoped semantic candidate search while transactional state, evidence, and audit records stay in the same database. CockroachDB Cloud Managed MCP Server gives developer tools read-only schema, trace, vector-index, and cluster inspection through a separate restricted service account.

## AWS services
Amazon Bedrock handles structured memory operations and responses; Lambda runs consolidation; S3 holds encrypted evidence artifacts.

## Challenges and accomplishments
The central challenge was treating memory as governed data rather than extra prompt text. Engram preserves provenance and contradictions while showing the full scoring trace. The exact INC-104 workflow resumes in a completely new session.

## Learned and next
Memory quality depends on lifecycle governance as much as embeddings. Next steps include richer live-model evaluation, production identity integration, and large-corpus retrieval benchmarks.

Repository: `<REPOSITORY_URL>` · Demo: `<DEMO_URL>`
