/* ── WebSocket hook — connects to a run's live stream ──────────── */
import { useEffect, useRef } from "react";
import { useCanvasStore } from "../store/useCanvasStore";
import type { StreamEvent } from "../types";

/**
 * Opens a WebSocket to /api/run/{runId}/stream whenever runId changes.
 * Parses incoming JSON events and feeds them to the Zustand store.
 */
export function useRunStream() {
  const runId = useCanvasStore((s) => s.runId);
  const handleStreamEvent = useCanvasStore((s) => s.handleStreamEvent);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!runId) return;

    // Derive ws:// or wss:// from the current page protocol
    const proto = window.location.protocol === "https:" ? "wss" : "ws";
    const wsUrl = `${proto}://${window.location.host}/api/run/${runId}/stream`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (evt) => {
      try {
        const event: StreamEvent = JSON.parse(evt.data);
        handleStreamEvent(event);
      } catch {
        console.warn("[ws] failed to parse event:", evt.data);
      }
    };

    ws.onerror = (err) => {
      console.error("[ws] error:", err);
    };

    ws.onclose = () => {
      wsRef.current = null;
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [runId, handleStreamEvent]);
}
