# Memory model

- Working: current session/task observations with explicit expiry.
- Episodic: incidents, deployments, reviews, attempted and successful repairs.
- Semantic: active ADRs, security rules, standards, preferences, and consolidated lessons.
- Archived evidence: immutable source metadata and integrity hash in CockroachDB; large payload in S3 or the local adapter.

Memory rows are never silently deleted by lifecycle operations. `superseded_by_memory_id`, `canonical_memory_id`, relations, and evidence mappings preserve history and provenance.
