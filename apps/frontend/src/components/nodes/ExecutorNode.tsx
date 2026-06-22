import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

type ExecutorData = { tools?: string[] };

function ExecutorNode({ data, selected }: NodeProps) {
  const tools = (data as ExecutorData)?.tools || [];
  return (
    <div
      style={{
        padding: '10px 16px',
        borderRadius: 8,
        background: selected ? '#e3f2fd' : '#e8eaf6',
        border: `2px solid ${selected ? '#2196f3' : '#7986cb'}`,
        minWidth: 140,
        fontSize: 13,
        fontFamily: 'system-ui, sans-serif',
        boxShadow: selected ? '0 0 0 2px #2196f3' : '0 1px 3px rgba(0,0,0,0.12)',
      }}
    >
      <div style={{ fontWeight: 700, color: '#1565c0', marginBottom: 2 }}>⚡ Executor</div>
      <div style={{ fontSize: 11, color: '#666' }}>
        {tools.length > 0 ? `Tools: ${tools.join(', ')}` : 'Step Execution'}
      </div>
      <Handle type="target" position={Position.Left} style={{ background: '#2196f3' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#2196f3' }} />
    </div>
  );
}

export default memo(ExecutorNode);
