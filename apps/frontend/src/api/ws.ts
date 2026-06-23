import { useEffect, useRef, useCallback } from 'react';

interface TaskEvent {
  event: string;
  task_id: string;
  node_id?: string;
  status?: string;
  [key: string]: unknown;
}

export function useTaskWebSocket(
  taskId: string | null,
  onEvent: (event: TaskEvent) => void
) {
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!taskId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
    const host = window.location.host;
    const url = `${protocol}://${host}/ws/tasks/${taskId}`;

    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as TaskEvent;
        onEvent(data);
      } catch {
        // ignore parse errors
      }
    };

    ws.onerror = () => {
      // WebSocket errors are expected when backend not running
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [taskId, onEvent]);

  return wsRef;
}
