"use client";

import { useEffect, useState } from "react";

import { demoProject, Memory, request } from "../../lib/api";

export default function Timeline() {
  const [memories, setMemories] = useState<Memory[]>([]);
  useEffect(() => {
    demoProject()
      .then((project) => request<Memory[]>(`/api/projects/${project.id}/memories`))
      .then((rows) => setMemories(rows.sort((left, right) => left.created_at.localeCompare(right.created_at))))
      .catch(() => setMemories([]));
  }, []);
  return (
    <div className="page">
      <div className="topline">
        <div><h1>Memory Timeline</h1><p className="subtle">How project knowledge evolved without losing history.</p></div>
        <span className="badge">{memories.length} memories</span>
      </div>
      <div className="card timeline">
        {memories.map((memory) => (
          <div className={`timelineItem ${memory.status === "superseded" ? "old" : ""}`} key={memory.id}>
            <span className={`badge ${memory.status === "active" ? "active" : ""}`}>{memory.status}</span>
            <h2>{memory.title}</h2>
            <p className="subtle">{memory.concise_summary}</p>
            <small>{new Date(memory.created_at).toLocaleDateString()} · {memory.memory_type.replaceAll("_", " ")}</small>
          </div>
        ))}
      </div>
    </div>
  );
}
