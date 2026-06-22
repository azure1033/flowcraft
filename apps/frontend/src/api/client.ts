/** API client for FlowCraft backend. */

const API_BASE = '/api';
const API_KEY = 'flowcraft-dev-key-change-in-production';

const headers = {
  'Content-Type': 'application/json',
  'X-API-Key': API_KEY,
};

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: { ...headers, ...options?.headers },
  });
  if (res.status === 204) return undefined as T;
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

import type { WorkflowRecord, WorkflowDefinition, TaskRecord, TaskDetail } from '../types/workflow';

export const api = {
  // Workflows
  createWorkflow: (name: string, definition: WorkflowDefinition, description = '') =>
    request<WorkflowRecord>('/workflows', {
      method: 'POST',
      body: JSON.stringify({ name, description, definition }),
    }),

  listWorkflows: () =>
    request<{ workflows: WorkflowRecord[]; total: number }>('/workflows'),

  getWorkflow: (id: string) =>
    request<WorkflowRecord>(`/workflows/${id}`),

  updateWorkflow: (id: string, data: Partial<{ name: string; description: string; definition: WorkflowDefinition }>) =>
    request<WorkflowRecord>(`/workflows/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteWorkflow: (id: string) =>
    request<void>(`/workflows/${id}`, { method: 'DELETE' }),

  // Tasks
  createTask: (workflowId: string, taskInput: string) =>
    request<TaskRecord>('/tasks', {
      method: 'POST',
      body: JSON.stringify({ workflow_id: workflowId, task_input: taskInput }),
    }),

  listTasks: () =>
    request<{ tasks: TaskRecord[]; total: number }>('/tasks'),

  getTask: (id: string) =>
    request<TaskDetail>(`/tasks/${id}`),

  submitDecision: (taskId: string, decision: 'approved' | 'rejected', feedback = '') =>
    request<unknown>(`/tasks/${taskId}/human-decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, feedback }),
    }),
};
