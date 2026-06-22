/** Zustand store for FlowCraft frontend state management. */

import { create } from 'zustand';
import type {
  WorkflowNode,
  WorkflowEdge,
  WorkflowDefinition,
  WorkflowRecord,
  TaskRecord,
  TaskDetail,
  NodeType,
} from '../types/workflow';
import { api } from '../api/client';

let nodeCounter = 0;
const nextId = (prefix: string) => `${prefix}_${++nodeCounter}`;

interface WorkflowState {
  // Canvas
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
  selectedNodeId: string | null;
  selectedEdgeId: string | null;

  // Workflow metadata
  workflowId: string | null;
  workflowName: string;
  workflowVersion: number;
  isDirty: boolean;

  // API state
  savedWorkflows: WorkflowRecord[];
  currentTask: TaskRecord | null;
  taskDetail: TaskDetail | null;
  taskHistory: TaskRecord[];

  // Node actions
  addNode: (type: NodeType, position?: { x: number; y: number }) => void;
  updateNode: (id: string, data: Partial<WorkflowNode>) => void;
  removeNode: (id: string) => void;
  selectNode: (id: string | null) => void;

  // Edge actions
  addEdge: (edge: WorkflowEdge) => void;
  updateEdge: (source: string, target: string, data: Partial<WorkflowEdge>) => void;
  removeEdge: (source: string, target: string) => void;
  selectEdge: (source: string | null, target: string | null) => void;

  // Canvas actions
  setCanvas: (def: WorkflowDefinition) => void;
  getDefinition: () => WorkflowDefinition;

  // API actions
  loadWorkflows: () => Promise<void>;
  saveWorkflow: () => Promise<WorkflowRecord>;
  loadWorkflow: (id: string) => Promise<void>;
  deleteWorkflow: (id: string) => Promise<void>;
  executeWorkflow: (taskInput: string) => Promise<TaskRecord>;
  loadTaskDetail: (taskId: string) => Promise<void>;
  submitDecision: (taskId: string, decision: 'approved' | 'rejected', feedback?: string) => Promise<void>;
  loadTaskHistory: () => Promise<void>;
}

export const useWorkflowStore = create<WorkflowState>((set, get) => ({
  nodes: [],
  edges: [],
  selectedNodeId: null,
  selectedEdgeId: null,
  workflowId: null,
  workflowName: 'Untitled Workflow',
  workflowVersion: 0,
  isDirty: false,
  savedWorkflows: [],
  currentTask: null,
  taskDetail: null,
  taskHistory: [],

  // ── Node actions ──
  addNode: (type, position) => {
    const id = nextId(type);
    const node: WorkflowNode = { id, type };
    set((s) => ({
      nodes: [...s.nodes, node],
      isDirty: true,
      selectedNodeId: id,
    }));
  },

  updateNode: (id, data) =>
    set((s) => ({
      nodes: s.nodes.map((n) => (n.id === id ? { ...n, ...data } : n)),
      isDirty: true,
    })),

  removeNode: (id) =>
    set((s) => ({
      nodes: s.nodes.filter((n) => n.id !== id),
      edges: s.edges.filter((e) => e.source !== id && e.target !== id),
      selectedNodeId: s.selectedNodeId === id ? null : s.selectedNodeId,
      isDirty: true,
    })),

  selectNode: (id) => set({ selectedNodeId: id }),

  // ── Edge actions ──
  addEdge: (edge) =>
    set((s) => ({
      edges: [...s.edges, edge],
      isDirty: true,
    })),

  updateEdge: (source, target, data) =>
    set((s) => ({
      edges: s.edges.map((e) =>
        e.source === source && e.target === target ? { ...e, ...data } : e
      ),
      isDirty: true,
    })),

  removeEdge: (source, target) =>
    set((s) => ({
      edges: s.edges.filter((e) => !(e.source === source && e.target === target)),
      isDirty: true,
    })),

  selectEdge: (source, target) =>
    set({ selectedEdgeId: source && target ? `${source}->${target}` : null }),

  // ── Canvas actions ──
  setCanvas: (def) =>
    set({
      nodes: def.nodes,
      edges: def.edges,
      isDirty: false,
      selectedNodeId: null,
      selectedEdgeId: null,
    }),

  getDefinition: () => {
    const { nodes, edges } = get();
    return { nodes, edges };
  },

  // ── API actions ──
  loadWorkflows: async () => {
    const data = await api.listWorkflows();
    set({ savedWorkflows: data.workflows });
  },

  saveWorkflow: async () => {
    const { workflowId, workflowName, getDefinition, savedWorkflows } = get();
    const definition = getDefinition();
    let record: WorkflowRecord;

    if (workflowId) {
      record = await api.updateWorkflow(workflowId, { name: workflowName, definition });
    } else {
      record = await api.createWorkflow(workflowName, definition);
    }

    set({ workflowId: record.id, workflowVersion: record.version, isDirty: false });
    await get().loadWorkflows();
    return record;
  },

  loadWorkflow: async (id) => {
    const record = await api.getWorkflow(id);
    set({
      workflowId: record.id,
      workflowName: record.name,
      workflowVersion: record.version,
      nodes: record.definition.nodes,
      edges: record.definition.edges,
      isDirty: false,
      selectedNodeId: null,
      selectedEdgeId: null,
    });
  },

  deleteWorkflow: async (id) => {
    await api.deleteWorkflow(id);
    if (get().workflowId === id) {
      set({ workflowId: null, workflowName: 'Untitled Workflow', workflowVersion: 0 });
    }
    await get().loadWorkflows();
  },

  executeWorkflow: async (taskInput) => {
    const { workflowId } = get();
    if (!workflowId) throw new Error('Save the workflow first.');

    const task = await api.createTask(workflowId, taskInput);
    set({ currentTask: task });
    return task;
  },

  loadTaskDetail: async (taskId) => {
    const detail = await api.getTask(taskId);
    set({ taskDetail: detail, currentTask: detail });
  },

  submitDecision: async (taskId, decision, feedback = '') => {
    await api.submitDecision(taskId, decision, feedback);
    await get().loadTaskDetail(taskId);
  },

  loadTaskHistory: async () => {
    const data = await api.listTasks();
    set({ taskHistory: data.tasks });
  },
}));
