/* ── Shared types across the AgentForge frontend ────────────────── */

/** Agent definitions that populate the sidebar */
export interface AgentDef {
  id: string;
  label: string;
  tools: string[];
  color: string;      // accent color (hsl string)
  icon: string;       // emoji
}

/** Status of an agent node on the canvas */
export type AgentStatus = "idle" | "running" | "complete" | "error";

/** Data stored inside each React Flow node */
export interface AgentNodeData {
  agentId: string;
  label: string;
  tools: string[];
  color: string;
  icon: string;
  status: AgentStatus;
  output: string;
}

/** WebSocket event from the backend */
export interface StreamEvent {
  type: "agent_start" | "agent_output" | "agent_complete" | "run_complete" | "run_error";
  agent?: string;
  content?: string;
  metadata?: {
    quality_status?: string;
    revision_count?: number;
    agent_trace?: string[];
    total_duration_ms?: number;
  };
}

/** Run history item from GET /api/run/history */
export interface RunHistoryItem {
  run_id: string;
  task: string;
  status: string;
  revision_count: number;
  total_duration_ms: number | null;
  created_at: string;
  completed_at: string | null;
}

/** Metrics summary from GET /api/metrics/summary */
export interface MetricsSummary {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  success_rate: number;
  avg_total_duration_ms: number | null;
  avg_agent_durations: { agent: string; avg_ms: number; total_runs: number }[];
}

/** Pipeline template for quick-load */
export interface PipelineTemplate {
  id: string;
  name: string;
  description: string;
  icon: string;
  agents: string[];    // agent IDs in order
  disabled?: boolean;  // true if not yet supported by the backend
}

/** Available agents to drag onto the canvas */
export const AGENT_CATALOG: AgentDef[] = [
  {
    id: "researcher",
    label: "Researcher",
    tools: ["Tavily Search"],
    color: "hsl(200, 90%, 60%)",
    icon: "🔍",
  },
  {
    id: "writer",
    label: "Writer",
    tools: ["Text Generation"],
    color: "hsl(270, 80%, 65%)",
    icon: "✍️",
  },
  {
    id: "critic",
    label: "Critic",
    tools: ["Quality Review"],
    color: "hsl(45, 90%, 55%)",
    icon: "🧐",
  },
];

/** Preset pipeline templates */
export const PIPELINE_TEMPLATES: PipelineTemplate[] = [
  {
    id: "research-write-critique",
    name: "Research → Write → Critique",
    description: "Full pipeline: research a topic, write content, and quality-check it",
    icon: "🚀",
    agents: ["researcher", "writer", "critic"],
  },
  {
    id: "research-summarize",
    name: "Research → Summarize",
    description: "Coming soon — requires dynamic pipeline support",
    icon: "⚡",
    agents: ["researcher", "writer"],
    disabled: true,
  },
  {
    id: "deep-research",
    name: "Deep Research Report",
    description: "Same agents, optimized for long-form research output",
    icon: "📚",
    agents: ["researcher", "writer", "critic"],
  },
];
