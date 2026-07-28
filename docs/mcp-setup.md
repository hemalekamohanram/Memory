# CockroachDB Cloud Managed MCP setup

MCP is a developer integration, not a browser feature in Engram. In CockroachDB Cloud, create a dedicated service account and read-only database role with access only to approved Engram tables or sanitized views. CockroachDB's managed endpoint is `https://cockroachlabs.cloud/mcp`; authentication and consent are enforced through Cloud service-account API keys, RBAC, and the existing SQL proxy. Never commit the API key.

```json
{"mcpServers":{"cockroachdb-cloud":{"type":"http","url":"https://cockroachlabs.cloud/mcp","headers":{"Authorization":"Bearer <SERVICE_ACCOUNT_API_KEY>"}}}}
```

Suggested prompts:

- Describe the Engram schema and foreign-key relationships.
- Show score components for the latest retrieval run without returning raw event content.
- List active memories that supersede older decisions.
- Check vector index and cluster health.

Mock mode exposes the same explanation and sample prompts in the MCP Inspector without claiming an active connection.

References: [Managed MCP announcement](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/), [CockroachDB vector indexes](https://www.cockroachlabs.com/docs/stable/vector-indexes).
