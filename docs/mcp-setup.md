# CockroachDB Cloud Managed MCP setup

MCP is a developer integration, not a browser feature in Engram. CockroachDB Cloud's managed endpoint is `https://cockroachlabs.cloud/mcp`. Prefer the console-generated OAuth connection and choose **read-only** consent; this keeps access auditable and avoids storing a credential in a local MCP file. The MCP client must still be scoped to the intended cluster.

```bash
claude mcp add cockroachdb-cloud https://cockroachlabs.cloud/mcp \
  --transport http \
  --header "mcp-cluster-id: <COCKROACH_CLOUD_CLUSTER_ID>"
```

Run `/mcp` in Claude Code and complete the browser authentication. Select read-only access for the demo. Never add a SQL password, API key, or connection string to this command or to Git.

Suggested prompts:

- Describe the Engram schema and foreign-key relationships.
- Show score components for the latest retrieval run without returning raw event content.
- List active memories that supersede older decisions.
- Check vector index and cluster health.

Mock mode exposes the same explanation and sample prompts in the MCP Inspector without claiming an active connection. For programmatic service-account access, use a separately documented, least-privilege credential rather than the public demo configuration.

References: [Managed MCP announcement](https://www.cockroachlabs.com/blog/cockroachdb-ai-agents-managed-mcp-server/), [CockroachDB vector indexes](https://www.cockroachlabs.com/docs/stable/vector-indexes).
