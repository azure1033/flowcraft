import { useCallback, useRef } from 'react';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  type Node,
  type Edge,
  type Connection,
  type OnConnect,
  addEdge,
  useReactFlow,
  ReactFlowProvider,
  BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { nodeTypes } from './nodes';
import type { NodeType, WorkflowEdge } from '../types/workflow';
import { useWorkflowStore } from '../stores/workflowStore';

const rfNode = (id: string, type: NodeType, x: number, y: number, data?: Record<string, unknown>): Node => ({
  id,
  type,
  position: { x, y },
  data: data || {},
});

const rfEdge = (id: string, source: string, target: string, label?: string, animated?: boolean): Edge => ({
  id,
  source,
  target,
  label,
  animated,
  style: label ? { stroke: '#ff9800', strokeDasharray: '5,5' } : { stroke: '#b1b1b7' },
  markerEnd: { type: 'arrowclosed' as const, color: label ? '#ff9800' : '#b1b1b7' },
});

function CanvasInner() {
  const reactFlowInstance = useReactFlow();
  const store = useWorkflowStore();
  const {
    nodes: wfNodes,
    edges: wfEdges,
    addNode,
    addEdge: storeAddEdge,
    selectNode,
  } = store;

  // Convert store nodes/edges → React Flow format
  const rfNodes: Node[] = wfNodes.map((n) =>
    rfNode(n.id, n.type, 0, 0, {
      tools: n.tools,
      human_confirm: n.human_confirm,
      tool_name: n.tool_name,
    })
  );
  const rfEdges: Edge[] = wfEdges.map((e, i) => {
    const isCondition = !!e.condition;
    const label = isCondition
      ? `${e.condition!.field} ${e.condition!.op} ${String(e.condition!.value)}`
      : undefined;
    return rfEdge(`e${i}`, e.source, e.target, label, isCondition);
  });

  const onConnect: OnConnect = useCallback(
    (connection: Connection) => {
      if (!connection.source || !connection.target) return;
      const edge: WorkflowEdge = {
        source: connection.source,
        target: connection.target,
        condition: null,
      };
      storeAddEdge(edge);
    },
    [storeAddEdge]
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const type = event.dataTransfer.getData('application/reactflow-type') as NodeType;
      if (!type) return;

      const position = reactFlowInstance.screenToFlowPosition({
        x: event.clientX,
        y: event.clientY,
      });
      addNode(type, position);
    },
    [reactFlowInstance, addNode]
  );

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => selectNode(node.id),
    [selectNode]
  );

  const onPaneClick = useCallback(() => selectNode(null), [selectNode]);

  return (
    <ReactFlow
      nodes={rfNodes}
      edges={rfEdges}
      onConnect={onConnect}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodeTypes={nodeTypes}
      fitView
      style={{ background: '#fcfcfc' }}
    >
      <Controls />
      <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#e0e0e0" />
      <MiniMap
        nodeColor={(n) => {
          const colors: Record<string, string> = {
            planner: '#81c784',
            executor: '#7986cb',
            reviewer: '#ffb74d',
            tool: '#ce93d8',
          };
          return colors[n.type || ''] || '#ddd';
        }}
        style={{ background: '#f5f5f5' }}
      />
    </ReactFlow>
  );
}

export default function Canvas() {
  return (
    <ReactFlowProvider>
      <CanvasInner />
    </ReactFlowProvider>
  );
}
