/* ── App.tsx — main layout ──────────────────────────────────────── */
import {
  ReactFlow,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";

import "./styles.css";

import { useCanvasStore } from "./store/useCanvasStore";
import { useRunStream } from "./hooks/useRunStream";
import { AgentNode } from "./components/nodes/AgentNode";
import { Sidebar } from "./components/panels/Sidebar";
import { Toolbar } from "./components/panels/Toolbar";
import { OutputPanel } from "./components/panels/OutputPanel";

const nodeTypes: NodeTypes = {
  agentNode: AgentNode,
};

export default function App() {
  const nodes = useCanvasStore((s) => s.nodes);
  const edges = useCanvasStore((s) => s.edges);
  const onNodesChange = useCanvasStore((s) => s.onNodesChange);
  const onEdgesChange = useCanvasStore((s) => s.onEdgesChange);
  const onConnect = useCanvasStore((s) => s.onConnect);

  // Activate the WebSocket stream hook
  useRunStream();

  return (
    <div className="app">
      <Sidebar />

      <div className="app__main">
        <Toolbar />

        <div className="app__canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            nodeTypes={nodeTypes}
            fitView
            proOptions={{ hideAttribution: true }}
            defaultEdgeOptions={{
              animated: true,
              style: { stroke: "hsl(270,80%,65%)", strokeWidth: 2 },
            }}
          >
            <Background
              variant={BackgroundVariant.Dots}
              gap={20}
              size={1}
              color="rgba(255,255,255,0.04)"
            />
            <Controls
              className="canvas-controls"
              showInteractive={false}
            />
            <MiniMap
              className="canvas-minimap"
              nodeColor={(node) => {
                const data = node.data as { status?: string; color?: string };
                if (data.status === "running") return "hsl(200,90%,60%)";
                if (data.status === "complete") return "hsl(145,70%,50%)";
                if (data.status === "error") return "hsl(0,80%,55%)";
                return data.color || "rgba(255,255,255,0.15)";
              }}
              maskColor="rgba(0,0,0,0.7)"
            />
          </ReactFlow>

          {/* Empty state */}
          {nodes.length === 0 && (
            <div className="app__empty-state">
              <div className="app__empty-icon">⚡</div>
              <h2>Build Your Agent Pipeline</h2>
              <p>Click an agent from the sidebar to add it to the canvas,<br />then connect them to define the execution flow.</p>
            </div>
          )}
        </div>

        <OutputPanel />
      </div>
    </div>
  );
}
