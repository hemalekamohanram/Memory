# Three-minute video production guide

## Recording setup

- Record the deployed app at 1440x960 or 1920x1080. Keep browser zoom at 100%.
- Use Loom, OBS, Clipchamp, or ScreenPal. Turn off notifications and hide bookmarks.
- Record your own voice if possible. Speak slightly slower than normal, with short pauses after key ideas. This will sound more credible than synthetic narration.
- If you cannot record live narration, use a natural neural voice at 0.95x speed, but do not claim that it is a human presenter.

## Timed narration and screen actions

### 0:00–0:18 — Problem

**Show:** Engram Overview.

**Say:** “AI coding agents are great at producing code, but they forget the decisions and incidents that taught a team how to operate safely. Engram gives those agents governed long-term memory—so they can use what the team learned, not just what fits in one chat.”

### 0:18–0:42 — Why this is more than RAG

**Show:** Memory Explorer with active, superseded, and disputed records.

**Say:** “This is not just document RAG. Engram stores typed engineering memory alongside its evidence: decisions, incidents, successful fixes, rejected approaches, and constraints. Each record has ownership, confidence, lifecycle state, and provenance.”

### 0:42–1:05 — CockroachDB memory layer

**Show:** Architecture page, then CockroachDB console/vector index.

**Say:** “CockroachDB is the persistent memory layer. It keeps embeddings in the same database as structured state and audit history. Its distributed vector index finds semantically relevant memories, while SQL transactions keep the current decision, evidence, and retrieval record consistent.”

### 1:05–1:35 — New-session proof

**Show:** Workspace. Create/select a new session and ask: “How should parallel refresh requests avoid intermittent logouts?”

**Say:** “Here I’m in a brand-new session. I have not re-explained the incident. Engram retrieves the previous INC-104 repair and recommends serializable token rotation with retries—the confirmed fix—while retaining the security requirement for auditable revocation.”

### 1:35–1:58 — Explainability

**Show:** Memory Trace beside the response.

**Say:** “Every answer is inspectable. The trace shows every candidate, semantic similarity, importance, recency, confidence, lifecycle penalty, final score, and why a memory was selected. Retrieved memory is evidence, never instructions.”

### 1:58–2:18 — Decision Graveyard

**Show:** Decision Graveyard.

**Say:** “Engineering knowledge changes. The Decision Graveyard preserves the old record and the replacement relationship. The old approach is still available for audit, but it cannot quietly return as the agent’s current recommendation.”

### 2:18–2:36 — Agent handoff

**Show:** Agent Handoff.

**Say:** “When another agent or engineer starts work, Engram creates a governed briefing: verified knowledge to carry forward, approaches not to repeat, and unresolved questions. That turns handoffs from a fragile chat summary into durable operational context.”

### 2:36–2:52 — Managed MCP and AWS

**Show:** MCP Inspector, then AWS/Cockroach console briefly.

**Say:** “We use CockroachDB Cloud Managed MCP with a separate read-only service account for safe schema and trace inspection. Amazon Bedrock powers live extraction and reasoning, Lambda runs consolidation, and encrypted S3 stores archived evidence.”

### 2:52–3:00 — Close

**Show:** Overview or Architecture.

**Say:** “Engram makes agents more useful because they can remember what mattered, prove why it mattered, and safely adapt when the truth changes.”

## Editing checklist

- Keep the final export below 3:00, preferably 2:50–2:55.
- Cut pauses, loading screens, login screens, terminal output, and credentials.
- Add simple opening and closing title cards only; do not use distracting transitions.
- Upload as **public** to YouTube or Vimeo and verify playback while signed out.
