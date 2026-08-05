# Engram hackathon submission checklist

## Current status

- [x] Public GitHub repository with MIT license.
- [x] Persistent structured memory, provenance, relations, audits, retrieval traces, and consolidation.
- [x] CockroachDB-compatible `VECTOR` storage and distributed vector-index SQL.
- [x] Managed MCP configuration and least-privilege read-only instructions.
- [x] AWS adapters for Bedrock, S3, and Lambda worker.
- [x] Local mock demo and automated test/build validation.
- [x] Live CockroachDB Cloud cluster connected and migrated.
- [x] Distributed vector index created and verified on the live `memories` table.
- [x] Managed MCP connected to that cluster with read-only OAuth consent.
- [ ] AWS deployment publicly reachable.
- [ ] Public 3-minute video uploaded.
- [ ] Devpost links replaced with final URLs.

## Required live setup

1. Create a CockroachDB Cloud Standard cluster in AWS `us-west-2`.
2. Create database `engram`, an application SQL user, and a separate read-only MCP SQL role.
3. Store the TLS connection URL in AWS Secrets Manager; never commit it.
4. Run `alembic upgrade head`, then run `infrastructure/cockroach/bootstrap.sql` against the live database.
5. Add CockroachDB Cloud Managed MCP using the console-generated OAuth connection and choose read-only consent.
6. In Amazon Bedrock `us-west-2`, use the serverless Global Amazon Nova 2 Lite inference profile and enable Titan Text Embeddings V2.
7. Create a private S3 evidence bucket with Block Public Access, encryption, versioning, and a lifecycle policy.
8. Deploy the API and consolidation worker to AWS. Configure `ENGRAM_MODE=live`, `DATABASE_URL`, Bedrock model IDs, and `S3_ARCHIVE_BUCKET` through Secrets Manager/IAM roles.
9. Deploy the Next.js app and configure `NEXT_PUBLIC_API_URL` to the HTTPS API endpoint.
10. Verify `/ready`, ingest one internal test event, ask from a new session, open its trace, and inspect the schema/read-only trace via Managed MCP.

## Submission fields

- **Project title:** Engram — Governed Memory for Engineering Agents
- **Repository:** https://github.com/hemalekamohanram/Memory
- **Try it out:** `<DEPLOYED_DEMO_URL>`
- **Video:** `<YOUTUBE_OR_VIMEO_URL>`
- **CockroachDB tools:** Distributed Vector Indexing; Cloud Managed MCP Server
- **AWS services:** Amazon Bedrock; AWS Lambda; Amazon S3
- **Suggested tags:** cockroachdb, aws, amazon-bedrock, aws-lambda, amazon-s3, agents, agentic-ai, memory, vector-search, rag, fastapi, nextjs, typescript, python, security, observability, mcp, hackathon

## Final evidence to capture

1. CockroachDB Cloud console showing the Engram cluster and vector index.
2. MCP client showing a read-only schema or retrieval-trace query.
3. Live app answering an INC-104 question from a new session.
4. Memory Trace showing candidates, component scores, and selected evidence.
5. Decision Graveyard showing a superseded decision and its replacement.
6. Agent Handoff showing carry-forward knowledge and “do not repeat” records.
