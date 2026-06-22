import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

type PlannerData = Record<string, unknown>;

function PlannerNode({ data, selected }: NodeProps) {
  return (
    <div
      style={{
        padding: '10px 16px',
        borderRadius: 8,
        background: selected ? '#e8f5e9' : '#f1f8e9',
        border: `2px solid ${selected ? '#4caf50' : '#81c784'}`,
        minWidth: 140,
        fontSize: 13,
        fontFamily: 'system-ui, sans-serif',
        boxShadow: selected ? '0 0 0 2px #4caf50' : '0 1px 3px rgba(0,0,0,0.12)',
      }}
    >
      <div style={{ fontWeight: 700, color: '#2e7d32', marginBottom: 2 }}>📋 Planner</div>
      <div style={{ fontSize: 11, color: '#666' }}>Task Decomposition</div>
      <Handle type="target" position={Position.Left} style={{ background: '#4caf50' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#4caf50' }} />
    </div>
  );
}

export default memo(PlannerNode);
