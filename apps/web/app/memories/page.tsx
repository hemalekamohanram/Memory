"use client";

import { useEffect, useMemo, useState } from "react";

import { demoProject, Memory, request } from "../../lib/api";

export default function Memories() {
  const [rows, setRows] = useState<Memory[]>([]);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [error, setError] = useState("");

  useEffect(() => {
    demoProject()
      .then((project) => request<Memory[]>(`/api/projects/${project.id}/memories`))
      .then(setRows)
      .catch((reason) => setError(reason.message));
  }, []);

  const visible = useMemo(
    () =>
      rows.filter(
        (memory) =>
          (status === "all" || memory.status === status) &&
          `${memory.title} ${memory.content}`.toLowerCase().includes(query.toLowerCase()),
      ),
    [rows, query, status],
  );

  async function dispute(memory: Memory) {
    const updated = await request<Memory>(`/api/memories/${memory.id}/dispute`, { method: "POST" });
    setRows((current) => current.map((item) => (item.id === updated.id ? updated : item)));
  }

  return (
    <div className="page">
      <div className="topline">
        <div>
          <h1>Memory Explorer</h1>
          <p className="subtle">Inspect durable knowledge, provenance, status, and usage.</p>
          {error && <p style={{ color: "#f07878" }}>{error}</p>}
        </div>
        <span className="badge active">{visible.length} visible</span>
      </div>
      <div className="filters">
        <input className="input" aria-label="Search memories" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search memories…" />
        <select className="input" aria-label="Memory status" value={status} onChange={(event) => setStatus(event.target.value)}>
          <option value="all">All statuses</option>
          <option value="active">Active</option>
          <option value="superseded">Superseded</option>
          <option value="disputed">Disputed</option>
          <option value="merged">Merged</option>
        </select>
      </div>
      <div className="card" style={{ padding: 0, overflow: "auto" }}>
        <table className="table">
          <thead><tr><th>Memory</th><th>Type</th><th>Status</th><th>Confidence</th><th>Importance</th><th>Uses</th><th>Action</th></tr></thead>
          <tbody>
            {visible.map((memory) => (
              <tr key={memory.id}>
                <td><strong>{memory.title}</strong><div className="subtle">{memory.concise_summary}</div></td>
                <td><span className="type">{memory.memory_type}</span></td>
                <td><span className={`badge ${memory.status === "active" ? "active" : memory.status === "disputed" ? "warn" : ""}`}>{memory.status}</span></td>
                <td>{Math.round(memory.confidence_score * 100)}%</td>
                <td>{memory.importance_score.toFixed(2)}</td>
                <td>{memory.access_count}</td>
                <td>{memory.status === "active" && <button className="button secondary" onClick={() => dispute(memory)}>Dispute</button>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
