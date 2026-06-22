import { useEffect, useRef } from 'react';
import { useWorkflowStore } from '../stores/workflowStore';
import type { TaskStatus } from '../types/workflow';

/** Polls task status and dispatches updates to the store. */
export default function ExecutionOverlay() {
  const { currentTask, loadTaskDetail, nodes } = useWorkflowStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!currentTask) return;
    const isTerminal = ['completed', 'failed'].includes(currentTask.status);
    if (isTerminal) return;

    intervalRef.current = setInterval(() => {
      loadTaskDetail(currentTask.id);
    }, 2000);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [currentTask?.id, currentTask?.status]);

  if (!currentTask) return null;

  const statusColor: Record<TaskStatus, string> = {
    pending: '#999',
    running: '#2196f3',
    waiting_human: '#ff9800',
    completed: '#4caf50',
    failed: '#e53935',
  };

  const statusLabel: Record<TaskStatus, string> = {
    pending: 'Pending',
    running: 'Running...',
    waiting_human: 'Waiting for Review',
    completed: 'Completed',
    failed: 'Failed',
  };

  const status = currentTask.status as TaskStatus;
  const color = statusColor[status] || '#999';

  return (
    <>
      {/* Top-right status badge */}
      <div style={{
        position: 'fixed',
        top: 56,
        right: 260,
        padding: '6px 14px',
        borderRadius: 20,
        background: color,
        color: '#fff',
        fontSize: 12,
        fontWeight: 700,
        zIndex: 10,
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
      }}>
        {statusLabel[status]}
      </div>

      {/* Bottom status bar when running */}
      {['running', 'waiting_human'].includes(status) && (
        <div style={{
          position: 'fixed',
          bottom: 0,
          left: 200,
          right: 240,
          height: 32,
          background: '#263238',
          color: '#fff',
          display: 'flex',
          alignItems: 'center',
          padding: '0 16px',
          fontSize: 12,
          zIndex: 10,
          gap: 12,
        }}>
          <span style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: color,
            display: 'inline-block',
            animation: status === 'running' ? 'pulse 1.5s infinite' : 'none',
          }} />
          <span>Task {currentTask.id.slice(0, 8)}...</span>
          <span style={{ color: '#90a4ae' }}>{nodes.length} nodes</span>
        </div>
      )}

      {/* Pulse animation */}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
      `}</style>
    </>
  );
}
