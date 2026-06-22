import { useEffect, useState } from 'react';
import Canvas from './components/Canvas';
import Sidebar from './components/Sidebar';
import Toolbar from './components/Toolbar';
import PropertiesPanel from './components/PropertiesPanel';
import WorkflowList from './components/WorkflowList';
import { useWorkflowStore } from './stores/workflowStore';

export default function App() {
  const [showList, setShowList] = useState(false);
  const loadWorkflows = useWorkflowStore((s) => s.loadWorkflows);

  useEffect(() => {
    loadWorkflows().catch(() => {
      // Backend not running — that's OK for canvas editing
    });
  }, [loadWorkflows]);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column', fontFamily: 'system-ui, sans-serif' }}>
      <Toolbar />
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <Sidebar />
        <div style={{ flex: 1, position: 'relative' }}>
          <Canvas />
        </div>
        <PropertiesPanel />
      </div>

      {/* Workflow list toggle */}
      <button
        onClick={() => setShowList(!showList)}
        style={{
          position: 'fixed',
          bottom: 16,
          right: 260,
          padding: '8px 16px',
          borderRadius: 20,
          border: '1px solid #ddd',
          background: '#fff',
          cursor: 'pointer',
          fontSize: 12,
          fontWeight: 600,
          boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
          zIndex: 10,
        }}
      >
        {showList ? '✕ Close' : '☰ Saved Workflows'}
      </button>
      {showList && <WorkflowList onClose={() => setShowList(false)} />}
    </div>
  );
}
