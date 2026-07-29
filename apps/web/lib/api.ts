export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

export type Project = { id: string; name: string; description: string; created_at: string };
export type Session = { id: string; project_id: string; title: string; status: string; started_at: string };
export type Memory = { id: string; project_id: string; memory_type: string; title: string; content: string; concise_summary: string; importance_score: number; confidence_score: number; status: string; access_count: number; superseded_by_memory_id: string | null; created_at: string };
export type Trace = { memory: Memory; vector_similarity: number; importance_component: number; recency_component: number; confidence_component: number; status_component: number; final_score: number; rank: number; selected_for_context: boolean; selection_reason: string };
export type Answer = { response_id: string; retrieval_run_id: string; answer: string; confidence: number; memory_trace: Trace[]; mock_generated: boolean };
export type DecisionHistory = { former: Memory; current: Memory | null; relation_type: string; confidence: number };
export type Handoff = { project_id: string; generated_at: string; summary: string; carry_forward: Memory[]; do_not_repeat: Memory[]; unresolved: Memory[] };

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(body.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export async function demoProject(): Promise<Project> {
  const projects = await request<Project[]>("/api/projects");
  const existing = projects.find((project) => project.name === "Acme Commerce API");
  if (existing) return existing;
  const created = await request<Project>("/api/projects", {
    method: "POST",
    body: JSON.stringify({ name: "Acme Commerce API", description: "Persistent authentication engineering memory demo" }),
  });
  await request(`/api/projects/${created.id}/seed-demo`, { method: "POST" });
  return created;
}
