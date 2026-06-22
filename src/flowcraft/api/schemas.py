"""Pydantic schemas for FlowCraft API request/response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Workflow ────────────────────────────────────────────


class WorkflowCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Workflow name")
    description: str = Field("", description="Workflow description")
    definition: Dict[str, Any] = Field(
        ..., description="Workflow JSON definition (nodes + edges)"
    )


class WorkflowUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    definition: Optional[Dict[str, Any]] = None


class WorkflowResponse(BaseModel):
    id: str
    name: str
    description: str
    definition: Dict[str, Any]
    version: int
    created_at: datetime
    updated_at: datetime


class WorkflowListResponse(BaseModel):
    workflows: List[WorkflowResponse]
    total: int


# ── Task ─────────────────────────────────────────────────


class TaskCreate(BaseModel):
    workflow_id: str = Field(..., description="ID of the workflow to execute")
    task_input: str = Field(
        ..., min_length=1, description="Natural language task description"
    )
    created_by: str = Field(
        "api", description="User identifier (reserved for future OAuth2)"
    )


class TaskResponse(BaseModel):
    id: str
    workflow_id: str
    status: str  # pending | running | waiting_human | completed | failed
    task_input: str
    created_by: str
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    current_state_snapshot: Optional[Dict[str, Any]] = Field(
        None, description="Recent AgentState snapshot"
    )


class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int


# ── Human Decision ───────────────────────────────────────


class HumanDecisionRequest(BaseModel):
    decision: str = Field(
        ..., pattern="^(approved|rejected)$", description="Review decision"
    )
    feedback: str = Field("", description="Optional review feedback")
    decided_by: str = Field("api", description="User identifier")


class HumanDecisionResponse(BaseModel):
    id: str
    task_id: str
    node_id: str
    decision: str
    feedback: str
    decided_at: datetime
    decided_by: str


# ── Task Detail (for audit) ──────────────────────────────


class NodeExecutionResponse(BaseModel):
    id: str
    task_id: str
    node_id: str
    node_type: str
    status: str  # success | error | interrupted
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    input_snapshot: Optional[Dict[str, Any]] = None
    output_snapshot: Optional[Dict[str, Any]] = None


class TaskDetailResponse(TaskResponse):
    node_executions: List[NodeExecutionResponse] = []
    human_decisions: List[HumanDecisionResponse] = []
    workflow_name: str = ""


# ── Health ───────────────────────────────────────────────


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str
    workflows_count: int
    tasks_count: int
