"use client";

import { Plus, Send } from "lucide-react";
import { useEffect, useState } from "react";

import {
  Answer,
  demoProject,
  Project,
  request,
  Session,
  Trace,
} from "../../lib/api";

const suggested =
  "We are seeing intermittent logouts during parallel refresh requests. How should we fix it?";

export default function Workspace() {
  const [project, setProject] = useState<Project | null>(null);
  const [sessions, setSessions] = useState<Session[]>([]);
  const [active, setActive] = useState<Session | null>(null);
  const [prompt, setPrompt] = useState(suggested);
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [recording, setRecording] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    demoProject()
      .then(async (found) => {
        setProject(found);
        const rows = await request<Session[]>(`/api/projects/${found.id}/sessions`);
        setSessions(rows);
        setActive(rows[0] ?? null);
      })
      .catch((reason) => setError(reason.message));
  }, []);

  async function newSession() {
    if (!project) return;
    setBusy(true);
    try {
      const created = await request<Session>(`/api/projects/${project.id}/sessions`, {
        method: "POST",
        body: JSON.stringify({ title: "New engineering session" }),
      });
      setSessions((current) => [created, ...current]);
      setActive(created);
      setAnswer(null);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not start session");
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    if (!active || !prompt.trim()) return;
    setBusy(true);
    setError("");
    try {
      setAnswer(
        await request<Answer>(`/api/sessions/${active.id}/messages`, {
          method: "POST",
          body: JSON.stringify({ content: prompt }),
        }),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Agent request failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="workspace">
      <section className="projectRail">
        <div className="brand">{project?.name ?? "Loading project…"}</div>
        <button className="button secondary railButton" onClick={newSession} disabled={busy}>
          <Plus size={14} /> New session
        </button>
        <button className="button secondary railButton" onClick={() => { setRecording(true); setPrompt(""); }}>
          Record event
        </button>
        <p className="eyebrow">SESSIONS</p>
        {sessions.map((session) => (
          <button
            className={`sessionItem ${active?.id === session.id ? "active" : ""}`}
            key={session.id}
            onClick={() => {
              setActive(session);
              setAnswer(null);
            }}
            style={{ border: 0, width: "100%", textAlign: "left", background: active?.id === session.id ? undefined : "transparent" }}
          >
            {session.title}
          </button>
        ))}
      </section>
      <section className="conversation">
        <header className="conversationHeader">
          <h2>{active?.title ?? "Choose a session"}</h2>
          <p className="subtle">
            Session context is isolated · durable project memory remains available
          </p>
        </header>
        <div className="messages">
          {error && <div className="message" role="alert"><p style={{ color: "#f07878" }}>{error}</p></div>}
          {answer ? (
            <>
              <div className="message user">
                <div className="label">YOU · {active?.title.toUpperCase()}</div>
                <p>{prompt}</p>
              </div>
              <div className="message">
                <div className="label">
                  ENGRAM · GROUNDED IN {answer.memory_trace.filter((trace) => trace.selected_for_context).length} MEMORIES
                  {answer.mock_generated ? " · MOCK" : " · BEDROCK"}
                </div>
                <p>{answer.answer}</p>
              </div>
            </>
          ) : (
            <div className="message">
              <div className="label">SESSION READY</div>
              <p>Ask a question and Engram will search durable project memory with a fully persisted trace.</p>
            </div>
          )}
        </div>
        <div className="composer">
          <textarea aria-label={recording ? "Engineering event" : "Message"} placeholder={recording ? "Paste an ADR, incident, review decision, or successful fix…" : "Ask Engram…"} value={prompt} onChange={(event) => setPrompt(event.target.value)} rows={2} />
          <button className="button" onClick={recording ? async () => {
            if (!project || !prompt.trim()) return;
            setBusy(true);
            try {
              const result = await request<{ memories: { title: string }[] }>(`/api/projects/${project.id}/events`, {
                method: "POST",
                body: JSON.stringify({ title: "Engineering event", content: prompt, session_id: active?.id }),
              });
              setError("");
              setAnswer(null);
              setRecording(false);
              setPrompt(suggested);
              alert(`${result.memories.length} durable memories recorded.`);
            } catch (reason) {
              setError(reason instanceof Error ? reason.message : "Event ingestion failed");
            } finally {
              setBusy(false);
            }
          } : send} disabled={busy || (!active && !recording)} aria-label={recording ? "Save event" : "Send"}>
            <Send size={17} />
          </button>
        </div>
      </section>
      <aside className="tracePanel">
        <header className="traceHeader">
          <h2>Memory Trace</h2>
          <p className="subtle">Why this answer knows what it knows</p>
        </header>
        <div className="traceList">
          {answer?.memory_trace.map((trace: Trace) => (
            <article className="traceCard" key={trace.memory.id}>
              <div className="traceTop">
                <div>
                  <span className="type">{trace.memory.memory_type}</span>
                  <h3>{trace.memory.title}</h3>
                </div>
                <span className="score">{Math.round(trace.final_score * 100)}</span>
              </div>
              <div className="scoreGrid">
                <div><small>Similarity</small>{trace.vector_similarity.toFixed(2)}</div>
                <div><small>Importance</small>{trace.importance_component.toFixed(2)}</div>
                <div><small>Recency</small>{trace.recency_component.toFixed(2)}</div>
                <div><small>Confidence</small>{trace.confidence_component.toFixed(2)}</div>
                <div><small>Status weight</small>{trace.status_component.toFixed(2)}</div>
                <div><small>Selected</small>{trace.selected_for_context ? "yes" : "no"}</div>
              </div>
              <p className="subtle" style={{ fontSize: 11, marginTop: 10 }}>{trace.selection_reason}</p>
            </article>
          ))}
        </div>
      </aside>
    </div>
  );
}
