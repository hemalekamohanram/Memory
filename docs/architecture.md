# Architecture

The Next.js client calls a tenancy-scoped FastAPI service. Domain services extract and validate memories, generate embeddings, retrieve and rerank candidates, create grounded responses, consolidate knowledge, archive evidence, and audit writes. Mock mode uses deterministic providers and SQLite. Live mode swaps in Bedrock, CockroachDB, S3, and the Lambda entrypoint without changing business rules.

Retrieval scores vector similarity (55%), importance (18%), confidence (12%), recency (10%), and usage (5%), then applies a status multiplier. Merged and expired records are ineligible; disputed and superseded records are strongly penalized. Every candidate and component is persisted.
