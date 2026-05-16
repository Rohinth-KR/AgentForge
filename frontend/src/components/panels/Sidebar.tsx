/* ── Sidebar — agent catalog + draggable cards ─────────────────── */
import { AGENT_CATALOG } from "../../types";
import { useCanvasStore } from "../../store/useCanvasStore";

export function Sidebar() {
  const addAgentNode = useCanvasStore((s) => s.addAgentNode);
  const runStatus = useCanvasStore((s) => s.runStatus);
  const isRunning = runStatus === "running";

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <span className="sidebar__logo-icon">⚡</span>
          <span className="sidebar__logo-text">AgentForge</span>
        </div>
        <span className="sidebar__version">v0.4</span>
      </div>

      <div className="sidebar__section-title">Agents</div>
      <p className="sidebar__hint">Click to add to canvas</p>

      <div className="sidebar__agents">
        {AGENT_CATALOG.map((agent) => (
          <button
            key={agent.id}
            className="sidebar__agent-card"
            onClick={() => addAgentNode(agent)}
            disabled={isRunning}
            style={{ "--agent-color": agent.color } as React.CSSProperties}
          >
            <span className="sidebar__agent-icon">{agent.icon}</span>
            <div className="sidebar__agent-info">
              <span className="sidebar__agent-name">{agent.label}</span>
              <span className="sidebar__agent-tools">
                {agent.tools.join(", ")}
              </span>
            </div>
            <span className="sidebar__agent-add">+</span>
          </button>
        ))}
      </div>

      <div className="sidebar__divider" />

      <div className="sidebar__section-title">Quick Templates</div>
      <button
        className="sidebar__template-btn"
        disabled={isRunning}
        onClick={() => {
          AGENT_CATALOG.forEach((agent) => addAgentNode(agent));
        }}
      >
        🚀 Full Pipeline
        <span className="sidebar__template-desc">Researcher → Writer → Critic</span>
      </button>
    </aside>
  );
}
