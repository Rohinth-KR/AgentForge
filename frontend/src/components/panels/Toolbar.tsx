/* ── Toolbar — task input + run controls ────────────────────────── */
import { useState } from "react";
import { useCanvasStore } from "../../store/useCanvasStore";

export function Toolbar() {
  const task = useCanvasStore((s) => s.task);
  const setTask = useCanvasStore((s) => s.setTask);
  const startRun = useCanvasStore((s) => s.startRun);
  const resetRun = useCanvasStore((s) => s.resetRun);
  const autoLayout = useCanvasStore((s) => s.autoLayout);
  const runStatus = useCanvasStore((s) => s.runStatus);
  const nodes = useCanvasStore((s) => s.nodes);
  const finalOutput = useCanvasStore((s) => s.finalOutput);
  const [copied, setCopied] = useState(false);

  const isRunning = runStatus === "running";
  const canRun = task.trim().length > 0 && nodes.length > 0 && !isRunning;

  const copyOutput = async () => {
    if (!finalOutput) return;
    try {
      await navigator.clipboard.writeText(finalOutput);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch { /* clipboard not available */ }
  };

  return (
    <div className="toolbar">
      <div className="toolbar__input-group">
        <label className="toolbar__label" htmlFor="task-input">Task</label>
        <input
          id="task-input"
          className="toolbar__input"
          type="text"
          placeholder="e.g., Research the top 5 AI trends in 2026 and write a blog post…"
          value={task}
          onChange={(e) => setTask(e.target.value)}
          disabled={isRunning}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && canRun) startRun();
          }}
        />
      </div>

      <div className="toolbar__actions">
        <button
          id="btn-auto-layout"
          className="toolbar__btn toolbar__btn--secondary"
          onClick={autoLayout}
          disabled={isRunning || nodes.length === 0}
          title="Auto-arrange nodes"
        >
          ⊞ Layout
        </button>

        {finalOutput && (
          <button
            id="btn-copy"
            className="toolbar__btn toolbar__btn--secondary"
            onClick={copyOutput}
            title="Copy output to clipboard"
          >
            {copied ? "✓ Copied" : "📋 Copy"}
          </button>
        )}

        {(runStatus === "success" || runStatus === "error") && (
          <button
            id="btn-reset"
            className="toolbar__btn toolbar__btn--secondary"
            onClick={resetRun}
          >
            ↺ Reset
          </button>
        )}

        <button
          id="btn-run"
          className={`toolbar__btn toolbar__btn--primary ${isRunning ? "toolbar__btn--running" : ""}`}
          onClick={startRun}
          disabled={!canRun}
          title="Ctrl+Enter"
        >
          {isRunning ? (
            <>
              <span className="toolbar__spinner" />
              Running…
            </>
          ) : (
            "▶ Run Pipeline"
          )}
        </button>
      </div>

      {/* Status indicator */}
      {runStatus !== "idle" && (
        <div className={`toolbar__status toolbar__status--${runStatus}`}>
          {runStatus === "running" && "Pipeline executing…"}
          {runStatus === "success" && "✓ Pipeline complete"}
          {runStatus === "error" && "✗ Pipeline failed"}
        </div>
      )}
    </div>
  );
}
