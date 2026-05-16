/* ── Zustand store — single source of truth for the canvas ──────── */
import { create } from "zustand";
import {
  type Node,
  type Edge,
  type OnNodesChange,
  type OnEdgesChange,
  type Connection,
  applyNodeChanges,
  applyEdgeChanges,
  addEdge,
} from "@xyflow/react";
import type { AgentNodeData, AgentDef, AgentStatus, StreamEvent } from "../types";
import { getLayoutedElements } from "../utils/layout";

/* ── Types ─────────────────────────────────────────────────────── */
export type RunStatus = "idle" | "running" | "success" | "error";

export interface LogEntry {
  timestamp: string;
  type: string;
  agent?: string;
  content?: string;
}

interface CanvasStore {
  /* React Flow state */
  nodes: Node<AgentNodeData>[];
  edges: Edge[];
  onNodesChange: OnNodesChange;
  onEdgesChange: OnEdgesChange;
  onConnect: (connection: Connection) => void;

  /* Pipeline */
  task: string;
  setTask: (task: string) => void;

  /* Run state */
  runId: string | null;
  runStatus: RunStatus;
  logs: LogEntry[];
  finalOutput: string;

  /* Actions */
  addAgentNode: (def: AgentDef) => void;
  removeNode: (id: string) => void;
  autoLayout: () => void;
  startRun: () => Promise<void>;
  handleStreamEvent: (event: StreamEvent) => void;
  setNodeStatus: (agentId: string, status: AgentStatus) => void;
  appendNodeOutput: (agentId: string, output: string) => void;
  resetRun: () => void;
}

/* ── Helpers ────────────────────────────────────────────────────── */
let nodeCounter = 0;

function nowStamp(): string {
  return new Date().toLocaleTimeString("en-GB", { hour12: false });
}

/* ── Store ──────────────────────────────────────────────────────── */
export const useCanvasStore = create<CanvasStore>((set, get) => ({
  nodes: [],
  edges: [],
  task: "",
  runId: null,
  runStatus: "idle",
  logs: [],
  finalOutput: "",

  /* ── React Flow callbacks ────────────────────────────────────── */
  onNodesChange: (changes) =>
    set((s) => ({ nodes: applyNodeChanges(changes, s.nodes) as Node<AgentNodeData>[] })),

  onEdgesChange: (changes) =>
    set((s) => ({ edges: applyEdgeChanges(changes, s.edges) })),

  onConnect: (connection) =>
    set((s) => ({
      edges: addEdge(
        { ...connection, animated: true, style: { stroke: "hsl(270,80%,65%)", strokeWidth: 2 } },
        s.edges
      ),
    })),

  /* ── Task ─────────────────────────────────────────────────────── */
  setTask: (task) => set({ task }),

  /* ── Add an agent node to the canvas ─────────────────────────── */
  addAgentNode: (def) => {
    const id = `${def.id}-${++nodeCounter}`;
    const newNode: Node<AgentNodeData> = {
      id,
      type: "agentNode",
      position: { x: 0, y: 0 }, // dagre will fix this
      data: {
        agentId: def.id,
        label: def.label,
        tools: def.tools,
        color: def.color,
        icon: def.icon,
        status: "idle",
        output: "",
      },
    };

    set((s) => {
      const nodes = [...s.nodes, newNode];
      const laid = getLayoutedElements(nodes, s.edges);
      return { nodes: laid.nodes as Node<AgentNodeData>[], edges: laid.edges };
    });
  },

  /* ── Remove a node ───────────────────────────────────────────── */
  removeNode: (id) =>
    set((s) => ({
      nodes: s.nodes.filter((n) => n.id !== id),
      edges: s.edges.filter((e) => e.source !== id && e.target !== id),
    })),

  /* ── Auto-layout ─────────────────────────────────────────────── */
  autoLayout: () =>
    set((s) => {
      const laid = getLayoutedElements(s.nodes, s.edges);
      return { nodes: laid.nodes as Node<AgentNodeData>[], edges: laid.edges };
    }),

  /* ── Start a pipeline run ────────────────────────────────────── */
  startRun: async () => {
    const { nodes, edges, task } = get();
    if (!task.trim()) return;
    if (nodes.length === 0) return;

    // Derive pipeline order from edges (topological sort via source→target)
    const pipeline = derivePipeline(nodes, edges);

    // Reset all nodes to idle
    set((s) => ({
      nodes: s.nodes.map((n) => ({
        ...n,
        data: { ...n.data, status: "idle" as AgentStatus, output: "" },
      })) as Node<AgentNodeData>[],
      logs: [],
      finalOutput: "",
      runStatus: "running",
    }));

    try {
      const res = await fetch("/api/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task, pipeline }),
      });
      const data = await res.json();
      set({ runId: data.run_id });
    } catch (err) {
      set({
        runStatus: "error",
        logs: [{ timestamp: nowStamp(), type: "error", content: String(err) }],
      });
    }
  },

  /* ── Handle a single WebSocket event ─────────────────────────── */
  handleStreamEvent: (event) => {
    const store = get();
    const log: LogEntry = {
      timestamp: nowStamp(),
      type: event.type,
      agent: event.agent,
      content: event.content?.slice(0, 200),
    };

    set((s) => ({ logs: [...s.logs, log] }));

    switch (event.type) {
      case "agent_start":
        if (event.agent) store.setNodeStatus(event.agent, "running");
        break;
      case "agent_output":
        if (event.agent && event.content) store.appendNodeOutput(event.agent, event.content);
        break;
      case "agent_complete":
        if (event.agent) store.setNodeStatus(event.agent, "complete");
        break;
      case "run_complete":
        set({ runStatus: "success", finalOutput: event.content || "" });
        break;
      case "run_error":
        set({ runStatus: "error" });
        break;
    }
  },

  /* ── Update a node's status ──────────────────────────────────── */
  setNodeStatus: (agentId, status) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.data.agentId === agentId ? { ...n, data: { ...n.data, status } } : n
      ) as Node<AgentNodeData>[],
    })),

  /* ── Append output to a node ─────────────────────────────────── */
  appendNodeOutput: (agentId, output) =>
    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.data.agentId === agentId ? { ...n, data: { ...n.data, output } } : n
      ) as Node<AgentNodeData>[],
    })),

  /* ── Reset the run state ─────────────────────────────────────── */
  resetRun: () =>
    set((s) => ({
      runId: null,
      runStatus: "idle",
      logs: [],
      finalOutput: "",
      nodes: s.nodes.map((n) => ({
        ...n,
        data: { ...n.data, status: "idle" as AgentStatus, output: "" },
      })) as Node<AgentNodeData>[],
    })),
}));

/* ── Derive pipeline order from edges ──────────────────────────── */
function derivePipeline(nodes: Node<AgentNodeData>[], edges: Edge[]): string[] {
  if (edges.length === 0) {
    return nodes.map((n) => n.data.agentId);
  }

  // Find nodes with no incoming edges (roots)
  const hasIncoming = new Set(edges.map((e) => e.target));
  const roots = nodes.filter((n) => !hasIncoming.has(n.id));

  const ordered: string[] = [];
  const visited = new Set<string>();
  const adjacency = new Map<string, string[]>();

  edges.forEach((e) => {
    const list = adjacency.get(e.source) || [];
    list.push(e.target);
    adjacency.set(e.source, list);
  });

  function walk(nodeId: string) {
    if (visited.has(nodeId)) return;
    visited.add(nodeId);
    const node = nodes.find((n) => n.id === nodeId);
    if (node) ordered.push(node.data.agentId);
    const children = adjacency.get(nodeId) || [];
    children.forEach(walk);
  }

  roots.forEach((r) => walk(r.id));

  // Add any unvisited nodes at the end
  nodes.forEach((n) => {
    if (!visited.has(n.id)) ordered.push(n.data.agentId);
  });

  return ordered;
}
