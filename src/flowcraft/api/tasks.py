"""Task execution and human decision API routes."""

import asyncio
import os
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from ..compiler import GraphCompiler
from .schemas import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskDetailResponse,
    HumanDecisionRequest,
    HumanDecisionResponse,
    NodeExecutionResponse,
)
from .store import store
from .deps import verify_api_key

router = APIRouter(
    prefix="/api/tasks",
    tags=["tasks"],
    dependencies=[Depends(verify_api_key)],
)


async def _execute_workflow(task_id: str, workflow: dict, task_input: str):
    """Execute a workflow in a background thread and update task status.

    This is the core execution bridge between REST API and LangGraph engine.
    """
    try:
        store.update_task_status(task_id, "running")

        compiler = GraphCompiler()
        graph = compiler.compile(workflow)

        initial_state = {
            "task": task_input,
            "current_step": 0,
            "retry_count": 0,
            "max_retries": 3,
            "review_decision": "",
            "human_input": "",
            "exec_output": "",
        }

        # Record node start events
        for node in workflow.get("nodes", []):
            store.add_node_execution(
                task_id, node["id"], node["type"], {"task": task_input}
            )

        config = {"configurable": {"thread_id": task_id}}

        # Run in thread pool (LangGraph invoke is synchronous)
        result = await asyncio.to_thread(graph.invoke, initial_state, config)

        # Update node execution records
        for node in workflow.get("nodes", []):
            # Find and update matching node execution record
            for exec_record in reversed(store.get_node_executions(task_id)):
                if (
                    exec_record["node_id"] == node["id"]
                    and exec_record["status"] == "running"
                ):
                    store.complete_node_execution(
                        exec_record["id"],
                        "success",
                        {"result": str(result.get("exec_output", ""))[:500]},
                    )
                    break

        review_decision = result.get("review_decision", "approved")

        if review_decision == "rejected":
            store.update_task_status(task_id, "failed", result)
        else:
            store.update_task_status(task_id, "completed", result)

    except Exception as e:
        store.update_task_status(task_id, "failed", {"error": str(e)})
        raise


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate):
    """Create and execute a new task instance from a workflow template."""
    workflow = store.get_workflow(body.workflow_id)
    if not workflow:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found."
        )

    task = store.create_task(body.workflow_id, body.task_input, body.created_by)

    # Start execution in background
    asyncio.create_task(
        _execute_workflow(task["id"], workflow["definition"], body.task_input)
    )

    return TaskResponse(**task)


@router.get("", response_model=TaskListResponse)
async def list_tasks():
    """List all task instances."""
    tasks = store.list_tasks()
    return TaskListResponse(
        tasks=[TaskResponse(**t) for t in tasks],
        total=len(tasks),
    )


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    """Get task status with full audit trail."""
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )

    node_executions = store.get_node_executions(task_id)
    human_decisions = store.get_human_decisions(task_id)

    workflow = store.get_workflow(task.get("workflow_id", ""))
    workflow_name = workflow["name"] if workflow else ""

    return TaskDetailResponse(
        **task,
        node_executions=[NodeExecutionResponse(**e) for e in node_executions],
        human_decisions=[HumanDecisionResponse(**d) for d in human_decisions],
        workflow_name=workflow_name,
    )


@router.post("/{task_id}/human-decision", response_model=HumanDecisionResponse)
async def submit_human_decision(task_id: str, body: HumanDecisionRequest):
    """Submit a human review decision for a waiting task."""
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found."
        )

    if task["status"] != "waiting_human":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Task is not waiting for human input. Current status: {task['status']}",
        )

    # Record the decision
    decision = store.add_human_decision(
        task_id=task_id,
        node_id="review",
        decision=body.decision,
        feedback=body.feedback,
        decided_by=body.decided_by,
    )

    # Resume execution (re-run from checkpoint with injected decision)
    if body.decision == "approved":
        store.update_task_status(task_id, "completed")
    else:
        store.update_task_status(task_id, "failed")

    return HumanDecisionResponse(**decision)
