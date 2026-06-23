import type { NodeType } from '../types/workflow';
import { useWorkflowStore } from '../stores/workflowStore';
import { addToBoth } from './Canvas';

const NODE_ITEMS: { type: NodeType; label: string; icon: string; color: string }[] = [
  { type: 'planner', label: 'Planner', icon: '📋', color: '#4caf50' },
  { type: 'executor', label: 'Executor', icon: '⚡', color: '#2196f3' },
  { type: 'reviewer', label: 'Reviewer', icon: '🔍', color: '#ff9800' },
  { type: 'tool', label: 'Tool', icon: '🔧', color: '#9c27b0' },
];

export default function Sidebar() {
  const onDragStart = (event: React.DragEvent, type: NodeType) => {
    event.dataTransfer.setData('application/reactflow-type', type);
    event.dataTransfer.effectAllowed = 'move';
  };

  const handleClick = (type: NodeType) => {
    // Add node at center of viewport
    addToBoth(type, { x: 300, y: 200 });
  };

  return (
    <div style={sidebarStyle}>
      <h3 style={{ margin: '0 0 8px 0', fontSize: 14, color: '#333' }}>Node Types</h3>
      <p style={{ margin: '0 0 4px 0', fontSize: 11, color: '#999' }}>Click or drag onto canvas</p>
      {NODE_ITEMS.map((item) => (
        <div
          key={item.type}
          draggable
          onDragStart={(e) => onDragStart(e, item.type)}
          onClick={() => handleClick(item.type)}
          style={{
            padding: '10px 12px', borderRadius: 6, background: 'white',
            border: `1px solid ${item.color}`, cursor: 'grab',
            display: 'flex', alignItems: 'center', gap: 8,
            fontSize: 13, fontWeight: 600, color: '#333',
            transition: 'box-shadow 0.15s', userSelect: 'none',
          }}
          onMouseEnter={(e) => (e.currentTarget.style.boxShadow = `0 2px 8px ${item.color}40`)}
          onMouseLeave={(e) => (e.currentTarget.style.boxShadow = 'none')}
        >
          <span style={{ fontSize: 18 }}>{item.icon}</span>
          {item.label}
        </div>
      ))}
    </div>
  );
}

const sidebarStyle: React.CSSProperties = {
  width: 200, background: '#fafafa', borderRight: '1px solid #e0e0e0',
  padding: '12px', display: 'flex', flexDirection: 'column', gap: 8,
  fontFamily: 'system-ui, sans-serif',
};
