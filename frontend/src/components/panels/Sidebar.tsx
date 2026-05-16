/* ── Sidebar — agent catalog + templates ────────────────────────── */
import { AGENT_CATALOG, PIPELINE_TEMPLATES } from "../../types";
import { useCanvasStore } from "../../store/useCanvasStore";

export function Sidebar() {
  const addAgentNode = useCanvasStore((s) => s.addAgentNode);
  const loadTemplate = useCanvasStore((s) => s.loadTemplate);
  const clearCanvas = useCanvasStore((s) => s.clearCanvas);
  const runStatus = useCanvasStore((s) => s.runStatus);
  const activePanel = useCanvasStore((s) => s.activePanel);
  const setActivePanel = useCanvasStore((s) => s.setActivePanel);
  const nodes = useCanvasStore((s) => s.nodes);
  const isRunning = runStatus === "running";

  return (
    <aside className="sidebar">
      <div className="sidebar__header">
        <div className="sidebar__logo">
          <span className="sidebar__logo-icon">⚡</span>
          <span className="sidebar__logo-text">AgentForge</span>
        </div>
        <span className="sidebar__version">v0.5</span>
      </div>

      {/* Agent Catalog */}
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

      {/* Pipeline Templates */}
      <div className="sidebar__section-title">Templates</div>
      <div className="sidebar__templates">
        {PIPELINE_TEMPLATES.map((tpl) => (
          <button
            key={tpl.id}
            className={`sidebar__template-btn ${tpl.disabled ? "sidebar__template-btn--disabled" : ""}`}
            disabled={isRunning || tpl.disabled}
            onClick={() => loadTemplate(tpl)}
          >
            <span className="sidebar__template-icon">{tpl.icon}</span>
            <div className="sidebar__template-info">
              <span className="sidebar__template-name">{tpl.name}</span>
              <span className="sidebar__template-desc">{tpl.description}</span>
            </div>
          </button>
        ))}
      </div>

      <div className="sidebar__divider" />

      {/* Dashboard Actions */}
      <div className="sidebar__section-title">Dashboard</div>
      <div className="sidebar__dashboard-actions">
        <button
          className={`sidebar__dash-btn ${activePanel === "history" ? "sidebar__dash-btn--active" : ""}`}
          onClick={() => setActivePanel("history")}
        >
          📋 Run History
        </button>
        <button
          className={`sidebar__dash-btn ${activePanel === "stats" ? "sidebar__dash-btn--active" : ""}`}
          onClick={() => setActivePanel("stats")}
        >
          📊 Stats
        </button>
      </div>

      {/* Spacer */}
      <div style={{ flex: 1 }} />

      {/* Clear button */}
      {nodes.length > 0 && !isRunning && (
        <div className="sidebar__footer">
          <button className="sidebar__clear-btn" onClick={clearCanvas}>
            🗑 Clear Canvas
          </button>
        </div>
      )}
    </aside>
  );
}
