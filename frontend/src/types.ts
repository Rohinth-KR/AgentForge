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
  };
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
