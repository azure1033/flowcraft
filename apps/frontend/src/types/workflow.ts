/** Workflow type definitions matching schemas/workflow.schema.json */

export type NodeType = 'planner' | 'executor' | 'reviewer' | 'tool';

export type ConditionOp = '==' | '!=' | '>' | '<' | '>=' | '<=';

export interface Condition {
  field: string;
  op: ConditionOp;
  value: string | number | boolean;
}

export interface WorkflowNode {
  id: string;
  type: NodeType;
  tools?: string[];
  human_confirm?: boolean;
  tool_name?: string;
  model?: string; // [TENTATIVE] per-node model override
}

export interface WorkflowEdge {
  source: string;
  target: string;
  condition?: Condition | null;
  loop?: {
    type: 'retry';
    max_retries: number;
  };
}

export interface WorkflowDefinition {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

export interface WorkflowRecord {
  id: string;
  name: string;
  description: string;
  definition: WorkflowDefinition;
  version: number;
  created_at: string;
  updated_at: string;
}

export type TaskStatus = 'pending' | 'running' | 'waiting_human' | 'completed' | 'failed';

export interface TaskRecord {
  id: string;
  workflow_id: string;
  status: TaskStatus;
  task_input: string;
  created_by: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  current_state_snapshot?: Record<string, unknown>;
}

export interface TaskDetail extends TaskRecord {
  node_executions: NodeExecution[];
  human_decisions: HumanDecision[];
  workflow_name: string;
}

export interface NodeExecution {
  id: string;
  task_id: string;
  node_id: string;
  node_type: string;
  status: 'success' | 'error' | 'interrupted';
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  input_snapshot?: Record<string, unknown>;
  output_snapshot?: Record<string, unknown>;
}

export interface HumanDecision {
  id: string;
  task_id: string;
  node_id: string;
  decision: 'approved' | 'rejected';
  feedback: string;
  decided_at: string;
  decided_by: string;
}
