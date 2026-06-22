import { useState } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';

export default function HumanDecisionDialog() {
  const { currentTask, taskDetail, loadTaskDetail, submitDecision } = useWorkflowStore();
  const [feedback, setFeedback] = useState('');
  const [submitted, setSubmitted] = useState(false);

  if (!currentTask || currentTask.status !== 'waiting_human') return null;
  if (submitted) {
    return (
      <Overlay>
        <div style={{ textAlign: 'center', padding: 24 }}>
          <p style={{ fontSize: 16, color: '#4caf50', fontWeight: 600 }}>Decision submitted</p>
          <button onClick={() => { setSubmitted(false); }} style={btnSecondary}>
            Close
          </button>
        </div>
      </Overlay>
    );
  }

  const handleDecision = async (decision: 'approved' | 'rejected') => {
    if (!currentTask) return;
    await submitDecision(currentTask.id, decision, feedback);
    setSubmitted(true);
    // Refresh after 1s to get updated status
    setTimeout(() => loadTaskDetail(currentTask.id), 1000);
  };

  const execOutput = taskDetail?.node_executions?.find(
    (e) => e.status === 'success' && e.output_snapshot
  );

  return (
    <Overlay>
      <div style={{
        background: '#fff',
        borderRadius: 12,
        padding: 24,
        maxWidth: 500,
        width: '90%',
        boxShadow: '0 8px 32px rgba(0,0,0,0.2)',
      }}>
        <h2 style={{ margin: '0 0 4px 0', fontSize: 18 }}>Human Review Required</h2>
        <p style={{ color: '#999', fontSize: 12, marginBottom: 16 }}>
          Task: {currentTask.id.slice(0, 8)}...
        </p>

        {/* Execution Output */}
        <div style={{
          background: '#f5f5f5',
          borderRadius: 6,
          padding: 12,
          marginBottom: 16,
          maxHeight: 200,
          overflowY: 'auto',
        }}>
          <p style={{ fontSize: 11, color: '#999', marginBottom: 8, fontWeight: 600 }}>
            Execution Output
          </p>
          <pre style={{
            fontSize: 12,
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-all',
            margin: 0,
            fontFamily: 'monospace',
            color: '#333',
          }}>
            {execOutput?.output_snapshot
              ? JSON.stringify(execOutput.output_snapshot, null, 2)
              : 'No output available yet.'}
          </pre>
        </div>

        {/* Feedback */}
        <textarea
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Optional feedback..."
          style={{
            width: '100%',
            minHeight: 60,
            padding: 8,
            borderRadius: 6,
            border: '1px solid #ddd',
            fontSize: 13,
            marginBottom: 16,
            resize: 'vertical',
            fontFamily: 'system-ui, sans-serif',
          }}
        />

        {/* Actions */}
        <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
          <button onClick={() => handleDecision('rejected')} style={btnReject}>
            ✕ Reject
          </button>
          <button onClick={() => handleDecision('approved')} style={btnApprove}>
            ✓ Approve
          </button>
        </div>
      </div>
    </Overlay>
  );
}

function Overlay({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(0,0,0,0.4)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 100,
    }}>
      {children}
    </div>
  );
}

const btnApprove: React.CSSProperties = {
  padding: '8px 24px',
  borderRadius: 6,
  border: 'none',
  background: '#4caf50',
  color: '#fff',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 700,
};

const btnReject: React.CSSProperties = {
  padding: '8px 24px',
  borderRadius: 6,
  border: '1px solid #e53935',
  background: '#fff',
  color: '#e53935',
  cursor: 'pointer',
  fontSize: 14,
  fontWeight: 700,
};

const btnSecondary: React.CSSProperties = {
  padding: '8px 20px',
  borderRadius: 6,
  border: '1px solid #ddd',
  background: '#f5f5f5',
  cursor: 'pointer',
  fontSize: 13,
  fontWeight: 600,
  marginTop: 12,
};
