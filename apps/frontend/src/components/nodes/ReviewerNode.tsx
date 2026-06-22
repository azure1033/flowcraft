import { memo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';

type ReviewerData = { human_confirm?: boolean };

function ReviewerNode({ data, selected }: NodeProps) {
  const humanConfirm = (data as ReviewerData)?.human_confirm;
  return (
    <div
      style={{
        padding: '10px 16px',
        borderRadius: 8,
        background: selected ? '#fff3e0' : '#fff8e1',
        border: `2px solid ${selected ? '#ff9800' : '#ffb74d'}`,
        minWidth: 140,
        fontSize: 13,
        fontFamily: 'system-ui, sans-serif',
        boxShadow: selected ? '0 0 0 2px #ff9800' : '0 1px 3px rgba(0,0,0,0.12)',
      }}
    >
      <div style={{ fontWeight: 700, color: '#e65100', marginBottom: 2 }}>
        {humanConfirm ? '👤 Reviewer' : '🔍 Reviewer'}
      </div>
      <div style={{ fontSize: 11, color: '#666' }}>
        {humanConfirm ? 'Human Approval Required' : 'Auto Review'}
      </div>
      <Handle type="target" position={Position.Left} style={{ background: '#ff9800' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#ff9800' }} />
    </div>
  );
}

export default memo(ReviewerNode);
