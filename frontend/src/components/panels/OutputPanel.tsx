/* ── Output Panel — live log + final output ─────────────────────── */
import { useEffect, useRef, useState } from "react";
import { useCanvasStore } from "../../store/useCanvasStore";

export function OutputPanel() {
  const logs = useCanvasStore((s) => s.logs);
  const finalOutput = useCanvasStore((s) => s.finalOutput);
  const runStatus = useCanvasStore((s) => s.runStatus);
  const [activeTab, setActiveTab] = useState<"logs" | "output">("logs");
  const logEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll logs
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Switch to output tab when run completes
  useEffect(() => {
    if (runStatus === "success" && finalOutput) {
      setActiveTab("output");
    }
  }, [runStatus, finalOutput]);

  const eventIcon = (type: string) => {
    switch (type) {
      case "agent_start": return "🟢";
      case "agent_output": return "📝";
      case "agent_complete": return "✅";
      case "run_complete": return "🏁";
      case "run_error": return "❌";
      default: return "❓";
    }
  };

  return (
    <div className="output-panel">
      <div className="output-panel__tabs">
        <button
          className={`output-panel__tab ${activeTab === "logs" ? "output-panel__tab--active" : ""}`}
          onClick={() => setActiveTab("logs")}
        >
          Live Logs
          {logs.length > 0 && (
            <span className="output-panel__tab-badge">{logs.length}</span>
          )}
        </button>
        <button
          className={`output-panel__tab ${activeTab === "output" ? "output-panel__tab--active" : ""}`}
          onClick={() => setActiveTab("output")}
        >
          Final Output
        </button>
      </div>

      <div className="output-panel__content">
        {activeTab === "logs" && (
          <div className="output-panel__logs">
            {logs.length === 0 ? (
              <div className="output-panel__empty">
                Run a pipeline to see live events here…
              </div>
            ) : (
              logs.map((log, i) => (
                <div key={i} className="output-panel__log-entry">
                  <span className="output-panel__log-time">{log.timestamp}</span>
                  <span className="output-panel__log-icon">{eventIcon(log.type)}</span>
                  <span className="output-panel__log-type">{log.type}</span>
                  {log.agent && (
                    <span className="output-panel__log-agent">[{log.agent}]</span>
                  )}
                  {log.content && (
                    <span className="output-panel__log-content">{log.content}</span>
                  )}
                </div>
              ))
            )}
            <div ref={logEndRef} />
          </div>
        )}

        {activeTab === "output" && (
          <div className="output-panel__final">
            {finalOutput ? (
              <div className="output-panel__final-text">{finalOutput}</div>
            ) : (
              <div className="output-panel__empty">
                No output yet. Run a pipeline to generate content.
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
