# Devpost submission copy

## Project title

Engram — Governed Memory for Engineering Agents

## One-line pitch

Engram gives AI engineering agents durable, governed memory that they can retrieve, explain, supersede, and safely hand off across sessions.

## Inspiration

AI coding agents are fast, but they forget the context that makes engineering work safe: why a team rejected an approach, how an incident was fixed, and which decision is current. Chat history and ordinary RAG are too weak for this because they do not preserve lifecycle, provenance, or accountability. We built Engram to turn those lessons into memory an agent can use and prove.

## What it does

Engram ingests engineering events and turns them into typed memories: architecture decisions, incidents, successful fixes, rejected approaches, security constraints, and task state. Each memory carries evidence, confidence, importance, lifecycle status, and a durable audit trail. A new session can retrieve the right prior knowledge without re-explaining the incident. Every grounded answer shows the candidate memories and score components that influenced it.

The Decision Graveyard preserves superseded decisions without letting them silently become current advice. Agent Handoff creates a governed briefing with verified knowledge to carry forward, approaches not to repeat, and unresolved questions.

## How we built it

The user experience is a Next.js and TypeScript application. FastAPI, Pydantic, and SQLAlchemy implement tenant-scoped ingestion, strict extraction validation, hybrid retrieval scoring, lifecycle transitions, audit events, and consolidation. CockroachDB Cloud is the persistent memory system: structured operational records, provenance, relations, retrieval traces, and `VECTOR` embeddings live together. CockroachDB distributed vector indexing performs semantic candidate retrieval while transactions preserve a consistent operational record.

Amazon Bedrock uses the serverless Amazon Nova 2 Lite inference profile for live structured extraction and grounded responses. Titan Text Embeddings V2 supplies 1,024-dimensional embeddings. AWS Lambda hosts the API and a Lambda-compatible consolidation worker; encrypted versioned Amazon S3 stores archived evidence. Deterministic SQLite and model adapters keep the complete local demo repeatable without paid services.

## CockroachDB tools used

**Distributed Vector Indexing:** Engram stores vectors with tenant and lifecycle metadata in CockroachDB and creates a distributed vector index over active project memory. Semantic retrieval, transactional memory state, relations, and audits stay in one database instead of drifting across a separate vector store.

**CockroachDB Cloud Managed MCP Server:** We connect the Cloud Managed MCP endpoint through OAuth with read-only consent. It provides safe, auditable developer inspection of schema, vector-index status, and retrieval traces without embedding database credentials in a client configuration.

## AWS services used

**Amazon Bedrock:** Nova 2 Lite extracts structured durable memories and writes grounded responses; Titan Text Embeddings V2 produces vector embeddings.

**AWS Lambda:** Runs the FastAPI API through Mangum and the idempotent consolidation worker.

**Amazon S3:** Stores encrypted, versioned evidence archives.

**API Gateway and Amplify Hosting:** Expose the HTTPS API and host the public Next.js demo.

## Challenges we ran into

The hard problem was not embedding text. It was preventing stale or disputed knowledge from resurfacing as current agent advice. We designed explicit lifecycle transitions, evidence hashes, supersession relations, status-aware ranking, and persisted retrieval traces. We also had to account for CockroachDB vector-index setup as a separate cluster operation because its feature setting cannot be applied inside a normal multi-statement migration transaction.

## Accomplishments we are proud of

Engram proves cross-session memory with a fresh-session incident question, then exposes exactly why it answered that way. It treats memory as governed production data rather than hidden prompt context. The same CockroachDB system holds the vectors, source evidence, lifecycle state, relations, and audit trail, while Managed MCP gives the team a safe way to inspect it.

## What we learned

Agent memory quality depends on governance as much as retrieval quality. A vector match is not enough: agents need currentness, confidence, provenance, and a safe way to handle contradictions. Keeping operational state and embeddings together in CockroachDB makes those guarantees easier to reason about and operate.

## What is next

Next we will add identity-provider authentication, AWS Secrets Manager-backed configuration, CloudWatch alarms, benchmark retrieval quality on larger memory corpora, and production multi-tenant load and recovery tests.

## Tags

cockroachdb, aws, amazon-bedrock, aws-lambda, amazon-s3, api-gateway, aws-amplify, agents, agentic-ai, memory, vector-search, fastapi, nextjs, typescript, python, security, observability, mcp, rag, hackathon
