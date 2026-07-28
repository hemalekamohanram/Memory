# Security

Engram enforces organization/project scope in server-side queries, parameterizes SQL through SQLAlchemy, bounds input sizes, validates structured model output, audits important writes, and emits request IDs without raw sensitive prompts. Retrieved memory is untrusted data and cannot authorize tool calls or database writes.

Production deployments should use an external identity provider, TLS CockroachDB connections, secret-manager references, least-privilege Bedrock/S3 IAM, S3 KMS encryption where required, short-lived presigned URLs, private networking, database roles split between application and read-only MCP access, and log redaction. Serialization failures should be retried with bounded jitter. Archive failures remain recoverable in a pending/failed state.
