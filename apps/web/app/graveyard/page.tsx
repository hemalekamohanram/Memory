"use client";

import { useEffect, useState } from "react";
import { ArrowRight, ShieldCheck } from "lucide-react";

import { DecisionHistory, demoProject, request } from "../../lib/api";

export default function DecisionGraveyard() {
  const [history, setHistory] = useState<DecisionHistory[]>([]);
  useEffect(() => {
    demoProject().then((project) => request<DecisionHistory[]>(`/api/projects/${project.id}/decision-graveyard`))
      .then(setHistory).catch(() => setHistory([]));
  }, []);
  return <div className="page">
    <div className="topline"><div><h1>Decision Graveyard</h1><p className="subtle">Old decisions remain visible as evidence, but cannot quietly become today&apos;s advice.</p></div><span className="badge">{history.length} governed transitions</span></div>
    <div className="callout"><ShieldCheck size={18} /><span>Engram preserves history and gives current, verified knowledge priority during retrieval.</span></div>
    <div className="stack">
      {history.map((item) => <article className="card decision" key={item.former.id}>
        <div><span className="badge">Former · {item.former.status}</span><h2>{item.former.title}</h2><p>{item.former.concise_summary}</p></div>
        <ArrowRight className="decisionArrow" aria-label="replaced by" />
        <div><span className="badge active">Current · {item.relation_type.replaceAll("_", " ")}</span><h2>{item.current?.title ?? "No current record"}</h2><p>{item.current?.concise_summary ?? "Historical relationship retained."}</p></div>
        <small>Relationship confidence: {Math.round(item.confidence * 100)}%</small>
      </article>)}
      {!history.length && <div className="card"><p>No governed decision transitions yet. Supersede a memory to create its historical trail.</p></div>}
    </div>
  </div>;
}
