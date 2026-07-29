"use client";

import { useEffect, useState } from "react";
import { Copy, RefreshCcw } from "lucide-react";

import { demoProject, Handoff, request } from "../../lib/api";

function MemoryList({ title, rows, tone }: { title: string; rows: Handoff["carry_forward"]; tone: string }) {
  return <section className="card handoffSection"><h2>{title}</h2>{rows.length ? rows.map((memory) => <div className="handoffMemory" key={memory.id}><span className={`badge ${tone}`}>{memory.memory_type.replaceAll("_", " ")}</span><strong>{memory.title}</strong><p className="subtle">{memory.concise_summary}</p></div>) : <p className="subtle">None recorded.</p>}</section>;
}

export default function AgentHandoff() {
  const [brief, setBrief] = useState<Handoff | null>(null);
  const load = () => demoProject().then((project) => request<Handoff>(`/api/projects/${project.id}/handoff`)).then(setBrief).catch(() => setBrief(null));
  useEffect(() => { void load(); }, []);
  const copy = async () => { if (brief) await navigator.clipboard.writeText(brief.summary); };
  return <div className="page">
    <div className="topline"><div><h1>Agent Handoff</h1><p className="subtle">A governed briefing for a new engineering agent or session.</p></div><div className="actions"><button className="secondary" onClick={load}><RefreshCcw size={15} /> Refresh</button><button onClick={copy}><Copy size={15} /> Copy briefing</button></div></div>
    {brief ? <><div className="callout"><strong>Handoff rule:</strong><span>{brief.summary}</span></div><div className="handoffGrid"><MemoryList title="Carry forward" rows={brief.carry_forward} tone="active" /><MemoryList title="Do not repeat" rows={brief.do_not_repeat} tone="warning" /><MemoryList title="Open questions" rows={brief.unresolved} tone="" /></div></> : <div className="card"><p>Loading project briefing…</p></div>}
  </div>;
}
