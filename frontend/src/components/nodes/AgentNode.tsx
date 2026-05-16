/* ── Custom React Flow node — Agent card ────────────────────────── */
import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { AgentNodeData } from "../../types";

const STATUS_CONFIG = {
  idle: { border: "rgba(255,255,255,0.08)", glow: "none", badge: "⏸", badgeColor: "#666" },
  running: { border: "hsl(200,90%,60%)", glow: "0 0 20px hsla(200,90%,60%,0.4)", badge: "⚡", badgeColor: "hsl(200,90%,60%)" },
  complete: { border: "hsl(145,70%,50%)", glow: "0 0 16px hsla(145,70%,50%,0.3)", badge: "✓", badgeColor: "hsl(145,70%,50%)" },
  error: { border: "hsl(0,80%,55%)", glow: "0 0 16px hsla(0,80%,55%,0.4)", badge: "✗", badgeColor: "hsl(0,80%,55%)" },
} as const;

function AgentNodeComponent({ data }: NodeProps) {
  const nodeData = data as unknown as AgentNodeData;
  const cfg = STATUS_CONFIG[nodeData.status];

  return (
    <div
      className={`agent-node ${nodeData.status === "running" ? "agent-node--running" : ""}`}
      style={{
        borderColor: cfg.border,
        boxShadow: cfg.glow,
      }}
    >
      {/* Top handle (target) */}
      <Handle type="target" position={Position.Top} className="agent-handle" />

      {/* Header */}
      <div className="agent-node__header">
        <div className="agent-node__icon">{nodeData.icon}</div>
        <div className="agent-node__title">{nodeData.label}</div>
        <div className="agent-node__badge" style={{ color: cfg.badgeColor }}>
          {cfg.badge}
        </div>
      </div>

      {/* Tools */}
      <div className="agent-node__tools">
        {nodeData.tools.map((t) => (
          <span key={t} className="agent-node__tool-tag" style={{ borderColor: nodeData.color + "44" }}>
            {t}
          </span>
        ))}
      </div>

      {/* Output preview */}
      {nodeData.output && (
        <div className="agent-node__output">
          <div className="agent-node__output-text">
            {nodeData.output.length > 150
              ? nodeData.output.slice(0, 150) + "…"
              : nodeData.output}
          </div>
        </div>
      )}

      {/* Status bar at bottom */}
      <div className="agent-node__status-bar" style={{ backgroundColor: cfg.border }} />

      {/* Bottom handle (source) */}
      <Handle type="source" position={Position.Bottom} className="agent-handle" />
    </div>
  );
}

export const AgentNode = memo(AgentNodeComponent);
