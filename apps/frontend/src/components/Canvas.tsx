import { useCallback, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import {
  ReactFlow, Controls, Background, MiniMap,
  useNodesState, useEdgesState,
  type Node, type Edge, type Connection,
  useReactFlow, ReactFlowProvider, BackgroundVariant,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import { nodeTypes } from './nodes';
import type { NodeType, ConditionOp } from '../types/workflow';
import { useWorkflowStore } from '../stores/workflowStore';

// ── Helpers ──

let _idCounter = 0;
const genId = (prefix: string) => `${prefix}_${Date.now()}_${++_idCounter}`;

function addToBoth(type: NodeType, pos: { x: number; y: number }) {
  const id = genId(type);
  const wfNode = { id, type };
  const rfNode: Node = { id, type, position: pos, data: {} };

  // Trigger React Flow update via custom event (avoids prop drilling)
  window.dispatchEvent(new CustomEvent('flowcraft:add-node', { detail: { rfNode, wfNode } }));
}

function CanvasInner() {
  const rf = useReactFlow();
  const [rfNodes, setRfNodes, onNodesChange] = useNodesState<Node>([]);
  const [rfEdges, setRfEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const store = useWorkflowStore();
  const { nodes: wfNodes, edges: wfEdges, selectNode } = store;

  // Track if we loaded a workflow to trigger full sync once
  const loadedId = useRef<string | null>(null);

  // Full reset when workflow loaded from API / import
  useEffect(() => {
    const wid = store.workflowId;
    if (wid && wid !== loadedId.current && wfNodes.length > 0) {
      loadedId.current = wid;
      const spacing = 220;
      const startX = 250;
      const startY = 150;
      const newNodes: Node[] = wfNodes.map((n, i) => ({
        id: n.id, type: n.type,
        position: { x: startX + i * spacing, y: startY + (i % 2) * 100 },
        data: { tools: n.tools, human_confirm: n.human_confirm, tool_name: n.tool_name },
      }));
      const newEdges: Edge[] = wfEdges.map((e, i) => {
        const c = e.condition;
        return {
          id: `e${i}`, source: e.source, target: e.target,
          label: c ? `${c.field} ${c.op} ${String(c.value)}` : undefined,
          animated: !!c,
          style: c ? { stroke: '#ff9800', strokeDasharray: '5,5' } : { stroke: '#b1b1b7' },
          markerEnd: { type: 'arrowclosed' as const, color: c ? '#ff9800' : '#b1b1b7' },
        };
      });
      setTimeout(() => { setRfNodes(newNodes); setRfEdges(newEdges); }, 0);
    }
  }, [store.workflowId, wfNodes, wfEdges, setRfNodes, setRfEdges]);

  // Listen for add-node events from Sidebar click
  useEffect(() => {
    const handler = (e: Event) => {
      const { rfNode, wfNode } = (e as CustomEvent).detail;
      setRfNodes((nds) => [...nds, rfNode]);
      useWorkflowStore.setState((s) => ({
        nodes: [...s.nodes, wfNode],
        isDirty: true,
      }));
    };
    window.addEventListener('flowcraft:add-node', handler);
    return () => window.removeEventListener('flowcraft:add-node', handler);
  }, [setRfNodes]);

  // ── Drag from sidebar ──
  const onDragOver = useCallback((e: React.DragEvent) => { e.preventDefault(); e.dataTransfer.dropEffect = 'move'; }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const type = e.dataTransfer.getData('application/reactflow-type') as NodeType;
    if (!type) return;
    const pos = rf.screenToFlowPosition({ x: e.clientX, y: e.clientY });
    addToBoth(type, pos);
  }, [rf]);

  // ── Connect ──
  const onConnect = useCallback((c: Connection) => {
    if (!c.source || !c.target) return;
    useWorkflowStore.setState((s) => ({
      edges: [...s.edges, { source: c.source, target: c.target, condition: null }],
      isDirty: true,
    }));
  }, []);

  // ── Clicks ──
  const onNodeClick = useCallback((_: any, n: Node) => selectNode(n.id), [selectNode]);
  const onPaneClick = useCallback(() => selectNode(null), [selectNode]);

  const onEdgeClick = useCallback((_: any, edge: Edge) => {
    const field = prompt('Condition field (e.g. review_decision):', '');
    if (!field) return;
    const op = prompt('Operator (==, !=, >, <, >=, <=):', '==');
    if (!op) return;
    const valRaw = prompt('Value:', 'approved');
    if (valRaw === null) return;
    const val: any = valRaw === 'true' ? true : valRaw === 'false' ? false : isNaN(+valRaw) ? valRaw : +valRaw;

    useWorkflowStore.setState((s) => ({
      edges: s.edges.map((e) =>
        e.source === edge.source && e.target === edge.target
          ? { ...e, condition: { field, op: op as ConditionOp, value: val } }
          : e
      ),
      isDirty: true,
    }));
  }, []);

  return (
    <ReactFlow
      nodes={rfNodes} edges={rfEdges}
      onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
      onConnect={onConnect} onDragOver={onDragOver} onDrop={onDrop}
      onNodeClick={onNodeClick} onEdgeClick={onEdgeClick} onPaneClick={onPaneClick}
      nodeTypes={nodeTypes} fitView
      deleteKeyCode={['Backspace', 'Delete']}
      style={{ background: '#fcfcfc' }}
    >
      <Controls />
      <Background variant={BackgroundVariant.Dots} gap={12} size={1} color="#e0e0e0" />
      <MiniMap
        nodeColor={(n) => ({ planner: '#81c784', executor: '#7986cb', reviewer: '#ffb74d', tool: '#ce93d8' }[n.type || ''] || '#ddd')}
        style={{ background: '#f5f5f5' }}
      />
    </ReactFlow>
  );
}

export default function Canvas() {
  return <ReactFlowProvider><CanvasInner /></ReactFlowProvider>;
}

// Export for Sidebar
export { addToBoth };
