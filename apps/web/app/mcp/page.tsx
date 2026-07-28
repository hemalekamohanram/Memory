const config=`{
  "mcpServers": {
    "cockroachdb-cloud": {
      "type": "http",
      "url": "https://cockroachlabs.cloud/mcp",
      "headers": { "Authorization": "Bearer <SERVICE_ACCOUNT_API_KEY>" }
    }
  }
}`;
export default function Mcp(){return <div className="page"><div className="topline"><div><h1>MCP Inspector</h1><p className="subtle">Developer-side inspection through CockroachDB Cloud Managed MCP Server.</p></div><span className="badge warn">Configuration required</span></div><div className="twoCol"><div className="card"><h2>Safe read-only setup</h2><p className="subtle">This browser is not an MCP client. Configure Codex, Claude Code, or Cursor separately with a database role that can only inspect approved schemas and views.</p><pre className="code">{config}</pre></div><div className="card"><h2>Suggested inspection prompts</h2><div className="event"><div><strong>Schema</strong><p>Describe the memories, evidence, relation, and retrieval trace tables.</p></div></div><div className="event"><div><strong>Retrieval</strong><p>Show score components for the latest Acme Commerce retrieval run.</p></div></div><div className="event"><div><strong>Memory health</strong><p>List superseded or disputed memories that were selected in the last 24 hours.</p></div></div><div className="event"><div><strong>Cluster</strong><p>Check index and range health without exposing application secrets.</p></div></div></div></div><div className="section card"><h2>What MCP contributes</h2><p className="subtle">It gives engineering tools governed, direct database inspection for schema review, trace validation, and cluster diagnostics. Application writes still flow through Engram’s authorized API and audit controls.</p></div></div>}
