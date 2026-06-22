import { useWorkflowStore } from '../stores/workflowStore';
import type { WorkflowRecord } from '../types/workflow';

interface Props {
  onClose: () => void;
}

export default function WorkflowList({ onClose }: Props) {
  const { savedWorkflows, loadWorkflow, deleteWorkflow, loadWorkflows } = useWorkflowStore();

  const handleLoad = async (wf: WorkflowRecord) => {
    await loadWorkflow(wf.id);
    onClose();
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Delete "${name}"?`)) return;
    await deleteWorkflow(id);
  };

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 56,
        right: 260,
        width: 320,
        maxHeight: 400,
        overflowY: 'auto',
        background: '#fff',
        borderRadius: 8,
        border: '1px solid #e0e0e0',
        boxShadow: '0 4px 16px rgba(0,0,0,0.15)',
        padding: 16,
        zIndex: 10,
      }}
    >
      <h3 style={{ margin: '0 0 12px 0', fontSize: 14 }}>Saved Workflows</h3>
      {savedWorkflows.length === 0 && (
        <p style={{ color: '#999', fontSize: 13 }}>No saved workflows yet.</p>
      )}
      {savedWorkflows.map((wf) => (
        <div
          key={wf.id}
          style={{
            padding: '8px 10px',
            borderRadius: 4,
            marginBottom: 6,
            background: '#f9f9f9',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            fontSize: 12,
          }}
        >
          <div style={{ flex: 1, cursor: 'pointer' }} onClick={() => handleLoad(wf)}>
            <div style={{ fontWeight: 600, color: '#333' }}>{wf.name}</div>
            <div style={{ color: '#999', fontSize: 11 }}>
              v{wf.version} · {wf.definition.nodes.length} nodes
            </div>
          </div>
          <button
            onClick={() => handleDelete(wf.id, wf.name)}
            style={{
              padding: '2px 8px',
              borderRadius: 3,
              border: '1px solid #e53935',
              background: '#fff',
              color: '#e53935',
              cursor: 'pointer',
              fontSize: 11,
            }}
          >
            Del
          </button>
        </div>
      ))}
    </div>
  );
}
