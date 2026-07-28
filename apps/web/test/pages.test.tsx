import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import Overview from "../app/page";
import Memories from "../app/memories/page";

const project = {
  id: "project-1",
  name: "Acme Commerce API",
  description: "demo",
  created_at: new Date().toISOString(),
};
const memory = {
  id: "memory-1",
  project_id: project.id,
  memory_type: "successful_fix",
  title: "Serializable token rotation",
  content: "Use a serializable transaction.",
  concise_summary: "Use a serializable transaction.",
  importance_score: 0.98,
  confidence_score: 0.98,
  status: "active",
  access_count: 4,
  superseded_by_memory_id: null,
  created_at: new Date().toISOString(),
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function mockFetch(responses: unknown[]) {
  const queue = [...responses];
  vi.stubGlobal("fetch", vi.fn(async () => ({
    ok: true,
    json: async () => queue.shift(),
  })));
}

describe("API-driven pages", () => {
  it("renders dashboard values returned by the API", async () => {
    mockFetch([[project], {
      active_memories: 8,
      superseded_memories: 2,
      events: 24,
      sessions: 3,
      memory_types: { successful_fix: 2 },
    }]);
    render(<Overview />);
    expect(await screen.findByText("8")).toBeInTheDocument();
    expect(screen.getByText("successful fix")).toBeInTheDocument();
  });

  it("filters memories by text", async () => {
    mockFetch([[project], [memory, {
      ...memory,
      id: "memory-2",
      title: "Unrelated catalog fact",
      content: "Catalog entries expire.",
      concise_summary: "Catalog entries expire.",
    }]]);
    render(<Memories />);
    expect(await screen.findByText("Serializable token rotation")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Search memories"), { target: { value: "serializable" } });
    await waitFor(() => expect(screen.queryByText("Unrelated catalog fact")).not.toBeInTheDocument());
  });

  it("exposes a status filter", async () => {
    mockFetch([[project], [memory]]);
    render(<Memories />);
    expect(await screen.findByLabelText("Memory status")).toBeInTheDocument();
  });
});
