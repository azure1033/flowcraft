import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

type ToolData = { tool_name?: string };

function ToolNode({ data, selected }: NodeProps) {
  const toolName = (data as ToolData)?.tool_name || 'tool';
  return (
    <div
      style={{
        padding: '10px 16px',
        borderRadius: 8,
        background: selected ? '#f3e5f5' : '#fce4ec',
        border: `2px solid ${selected ? '#9c27b0' : '#ce93d8'}`,
        minWidth: 140,
        fontSize: 13,
        fontFamily: 'system-ui, sans-serif',
        boxShadow: selected ? '0 0 0 2px #9c27b0' : '0 1px 3px rgba(0,0,0,0.12)',
      }}
    >
      <div style={{ fontWeight: 700, color: '#6a1b9a', marginBottom: 2 }}>🔧 Tool</div>
      <div style={{ fontSize: 11, color: '#666' }}>{toolName}</div>
      <Handle type="target" position={Position.Left} style={{ background: '#9c27b0' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#9c27b0' }} />
    </div>
  );
}

export default memo(ToolNode);
