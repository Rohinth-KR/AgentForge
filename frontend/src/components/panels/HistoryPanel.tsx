/* ── Run History Panel ──────────────────────────────────────────── */
import { useEffect, useState } from "react";
import type { RunHistoryItem } from "../../types";

export function HistoryPanel() {
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);

  const fetchHistory = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/run/history?limit=20");
      const data = await res.json();
      setRuns(data.runs);
      setTotal(data.total);
    } catch (err) {
      console.error("Failed to fetch history:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory();
  }, []);

  const statusIcon = (status: string) => {
    switch (status) {
      case "completed": return "✅";
      case "failed": return "❌";
      case "running": return "⚡";
      case "queued": return "⏳";
      default: return "❓";
    }
  };

  const formatDuration = (ms: number | null) => {
    if (!ms) return "—";
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    });
  };

  return (
    <div className="history-panel">
      <div className="history-panel__header">
        <h3 className="history-panel__title">Run History</h3>
        <div className="history-panel__meta">
          <span className="history-panel__total">{total} total runs</span>
          <button className="history-panel__refresh" onClick={fetchHistory} title="Refresh">
            ↻
          </button>
        </div>
      </div>

      {loading ? (
        <div className="history-panel__loading">Loading…</div>
      ) : runs.length === 0 ? (
        <div className="history-panel__empty">No runs yet. Start your first pipeline!</div>
      ) : (
        <div className="history-panel__list">
          {runs.map((run) => (
            <div key={run.run_id} className={`history-panel__item history-panel__item--${run.status}`}>
              <div className="history-panel__item-header">
                <span className="history-panel__item-status">{statusIcon(run.status)}</span>
                <span className="history-panel__item-date">{formatDate(run.created_at)}</span>
                <span className="history-panel__item-duration">{formatDuration(run.total_duration_ms)}</span>
              </div>
              <div className="history-panel__item-task">{run.task}</div>
              {run.revision_count > 0 && (
                <div className="history-panel__item-revisions">
                  🔄 {run.revision_count} revision{run.revision_count > 1 ? "s" : ""}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
