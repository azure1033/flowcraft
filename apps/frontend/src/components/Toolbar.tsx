import { useWorkflowStore } from '../stores/workflowStore';

export default function Toolbar() {
  const store = useWorkflowStore();
  const { workflowId, workflowName, isDirty, saveWorkflow, setCanvas } = store;

  const handleSave = async () => {
    try {
      const record = await saveWorkflow();
      alert(`Saved: "${record.name}" v${record.version}`);
    } catch (e: unknown) {
      alert(`Save failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  const handleNew = () => {
    if (isDirty && !confirm('Discard unsaved changes?')) return;
    setCanvas({ nodes: [], edges: [] });
    useWorkflowStore.setState({
      workflowId: null,
      workflowName: 'Untitled Workflow',
      workflowVersion: 0,
      isDirty: false,
    });
  };

  const handleExport = () => {
    const def = store.getDefinition();
    const json = JSON.stringify(def, null, 2);
    navigator.clipboard.writeText(json).then(
      () => alert('Workflow JSON copied to clipboard.'),
      () => alert('Failed to copy.')
    );
  };

  const handleImport = () => {
    const json = prompt('Paste workflow JSON:');
    if (!json) return;
    try {
      const def = JSON.parse(json);
      if (!def.nodes || !def.edges) throw new Error('Invalid format');
      setCanvas(def);
    } catch {
      alert('Invalid workflow JSON. Must contain "nodes" and "edges" arrays.');
    }
  };

  const handleRun = async () => {
    if (!workflowId) {
      alert('Save the workflow first.');
      return;
    }
    const taskInput = prompt('Task description:');
    if (!taskInput) return;
    try {
      const task = await store.executeWorkflow(taskInput);
      alert(`Task created: ${task.id.slice(0, 8)}... Status: ${task.status}`);
    } catch (e: unknown) {
      alert(`Execution failed: ${e instanceof Error ? e.message : String(e)}`);
    }
  };

  return (
    <div
      style={{
        height: 48,
        background: '#fff',
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        alignItems: 'center',
        padding: '0 16px',
        gap: 8,
        fontFamily: 'system-ui, sans-serif',
      }}
    >
      <span style={{ fontWeight: 700, fontSize: 14, marginRight: 12, color: '#333' }}>
        {workflowName}
        {isDirty && <span style={{ color: '#ff9800', marginLeft: 4 }}>*</span>}
        {workflowId && (
          <span style={{ color: '#999', fontSize: 11, marginLeft: 8 }}>
            v{store.workflowVersion}
          </span>
        )}
      </span>

      <div style={{ flex: 1 }} />

      <button onClick={handleNew} style={btnStyle}>New</button>
      <button onClick={handleSave} style={{ ...btnStyle, background: isDirty ? '#4caf50' : '#e0e0e0', color: isDirty ? 'white' : '#666' }}>Save</button>
      <button onClick={handleExport} style={btnStyle}>Export</button>
      <button onClick={handleImport} style={btnStyle}>Import</button>
      <button onClick={handleRun} style={{ ...btnStyle, background: '#2196f3', color: 'white', fontWeight: 700 }}>▶ Run</button>
    </div>
  );
}

const btnStyle: React.CSSProperties = {
  padding: '6px 14px',
  borderRadius: 4,
  border: '1px solid #ddd',
  background: '#f5f5f5',
  cursor: 'pointer',
  fontSize: 12,
  fontWeight: 600,
  color: '#333',
};
