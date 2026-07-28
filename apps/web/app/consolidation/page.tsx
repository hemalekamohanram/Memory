"use client";

import { useEffect, useState } from "react";

import { demoProject, Project, request } from "../../lib/api";

type Preview = {
  before: { active_memories: number; overlapping_groups: number };
  groups: { memory_ids: string[]; proposed_title: string; type: string }[];
  temporary_to_expire: string[];
  after: { active_memories: number; merged_memories: number };
  dry_run?: boolean;
};

export default function Consolidation() {
  const [project, setProject] = useState<Project | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");

  async function load(found: Project) {
    setProject(found);
    setPreview(await request<Preview>(`/api/projects/${found.id}/consolidation/preview`, {
      method: "POST",
      body: JSON.stringify({ dry_run: true, similarity_threshold: 0.82, idempotency_key: `preview-${Date.now()}` }),
    }));
  }
  useEffect(() => { demoProject().then(load).catch((reason) => setMessage(reason.message)); }, []);

  async function apply() {
    if (!project) return;
    setBusy(true);
    try {
      const result = await request<Preview>(`/api/projects/${project.id}/consolidation/run`, {
        method: "POST",
        body: JSON.stringify({ dry_run: false, similarity_threshold: 0.82, idempotency_key: `ui-${crypto.randomUUID()}` }),
      });
      setPreview(result);
      setMessage("Consolidation applied idempotently. Evidence and original memories were preserved.");
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : "Consolidation failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page">
      <div className="topline"><div><h1>Consolidation Center</h1><p className="subtle">Compact memory without deleting its evidence.</p></div><span className="badge active">Preview first</span></div>
      {message && <div className="card" role="status">{message}</div>}
      <div className="grid4 section">
        <div className="card metric"><span>Active before</span><strong>{preview?.before.active_memories ?? "—"}</strong></div>
        <div className="card metric"><span>Overlap groups</span><strong>{preview?.before.overlapping_groups ?? "—"}</strong></div>
        <div className="card metric"><span>Active after</span><strong>{preview?.after.active_memories ?? "—"}</strong></div>
        <div className="card metric"><span>Marked merged</span><strong>{preview?.after.merged_memories ?? "—"}</strong></div>
      </div>
      <div className="section twoCol">
        <div className="card"><h2>Proposed groups</h2>{preview?.groups.length ? preview.groups.map((group) => <div className="event" key={group.memory_ids.join("-")}><div><strong>{group.proposed_title}</strong><p>{group.memory_ids.length} {group.type.replaceAll("_", " ")} memories retain provenance</p></div></div>) : <p className="subtle">No duplicate group currently exceeds the configured threshold.</p>}</div>
        <div className="card"><h2>Lifecycle actions</h2><p className="subtle">{preview?.temporary_to_expire.length ?? 0} temporary memories receive an expiry. Merged records remain queryable for provenance.</p><button className="button section" disabled={busy || !preview} onClick={apply}>{busy ? "Applying…" : "Apply consolidation"}</button></div>
      </div>
    </div>
  );
}
