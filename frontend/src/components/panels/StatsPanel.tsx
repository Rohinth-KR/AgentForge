/* ── Stats Dashboard Panel ──────────────────────────────────────── */
import { useEffect, useState } from "react";
import type { MetricsSummary } from "../../types";

export function StatsPanel() {
  const [metrics, setMetrics] = useState<MetricsSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      setLoading(true);
      const res = await fetch("/api/metrics/summary");
      const data: MetricsSummary = await res.json();
      setMetrics(data);
    } catch (err) {
      console.error("Failed to fetch metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const formatMs = (ms: number | null | undefined) => {
    if (!ms) return "—";
    if (ms < 1000) return `${Math.round(ms)}ms`;
    return `${(ms / 1000).toFixed(1)}s`;
  };

  const agentColor = (agent: string) => {
    switch (agent) {
      case "researcher": return "hsl(200, 90%, 60%)";
      case "writer": return "hsl(270, 80%, 65%)";
      case "critic": return "hsl(45, 90%, 55%)";
      case "finalize": return "hsl(145, 70%, 50%)";
      default: return "hsl(0, 0%, 60%)";
    }
  };

  if (loading) {
    return <div className="stats-panel"><div className="stats-panel__loading">Loading metrics…</div></div>;
  }

  if (!metrics) {
    return <div className="stats-panel"><div className="stats-panel__empty">Failed to load metrics.</div></div>;
  }

  // Find max avg_ms for the bar chart scaling
  const maxMs = Math.max(...metrics.avg_agent_durations.map((a) => a.avg_ms), 1);

  return (
    <div className="stats-panel">
      <div className="stats-panel__header">
        <h3 className="stats-panel__title">Pipeline Stats</h3>
        <button className="stats-panel__refresh" onClick={fetchMetrics} title="Refresh">
          ↻
        </button>
      </div>

      {/* KPI Cards */}
      <div className="stats-panel__kpis">
        <div className="stats-panel__kpi">
          <div className="stats-panel__kpi-value">{metrics.total_runs}</div>
          <div className="stats-panel__kpi-label">Total Runs</div>
        </div>
        <div className="stats-panel__kpi stats-panel__kpi--success">
          <div className="stats-panel__kpi-value">{metrics.success_rate}%</div>
          <div className="stats-panel__kpi-label">Success Rate</div>
        </div>
        <div className="stats-panel__kpi">
          <div className="stats-panel__kpi-value">{formatMs(metrics.avg_total_duration_ms)}</div>
          <div className="stats-panel__kpi-label">Avg Duration</div>
        </div>
        <div className="stats-panel__kpi stats-panel__kpi--info">
          <div className="stats-panel__kpi-value">{metrics.completed_runs}</div>
          <div className="stats-panel__kpi-label">Completed</div>
        </div>
      </div>

      {/* Per-Agent Breakdown */}
      {metrics.avg_agent_durations.length > 0 && (
        <div className="stats-panel__breakdown">
          <div className="stats-panel__breakdown-title">Avg Time Per Agent</div>
          {metrics.avg_agent_durations.map((a) => (
            <div key={a.agent} className="stats-panel__agent-row">
              <div className="stats-panel__agent-name" style={{ color: agentColor(a.agent) }}>
                {a.agent}
              </div>
              <div className="stats-panel__agent-bar-container">
                <div
                  className="stats-panel__agent-bar"
                  style={{
                    width: `${Math.max((a.avg_ms / maxMs) * 100, 4)}%`,
                    backgroundColor: agentColor(a.agent),
                  }}
                />
              </div>
              <div className="stats-panel__agent-value">{formatMs(a.avg_ms)}</div>
            </div>
          ))}
        </div>
      )}

      {metrics.failed_runs > 0 && (
        <div className="stats-panel__failed-note">
          ⚠ {metrics.failed_runs} failed run{metrics.failed_runs > 1 ? "s" : ""}
        </div>
      )}
    </div>
  );
}
