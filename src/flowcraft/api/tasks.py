"""Task execution and human decision API routes.

Supports:
- Async workflow execution via LangGraph engine
- Human-in-the-loop: reviewer nodes with human_confirm pause for approval
- Simulated review mode: auto-generates decisions for testing
- State injection + resume on human decision submission
"""

import asyncio
import os
import random
from typing import Any

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

# Per-task graph + config cache for resume
_resume_cache: dict[str, tuple] = {}


async def _execute_workflow(task_id: str, workflow: dict, task_input: str):
    """Execute a workflow in background. Supports interrupt/resume for HITL."""
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

        for node in workflow.get("nodes", []):
            store.add_node_execution(
                task_id, node["id"], node["type"], {"task": task_input}
            )

        config = {"configurable": {"thread_id": task_id}}
        result = await asyncio.to_thread(graph.invoke, initial_state, config)

        # Check for human-in-the-loop
        has_human_confirm = any(
            n.get("human_confirm")
            for n in workflow.get("nodes", [])
            if n["type"] == "reviewer"
        )
        simulated = os.getenv("ENABLE_SIMULATED_REVIEW", "").lower() == "true"

        if has_human_confirm and not simulated:
            # Pause for human decision — cache graph + config for resume
            _resume_cache[task_id] = (graph, config)
            store.update_task_status(task_id, "waiting_human", result)
            _update_node_executions(task_id, workflow, result, "interrupted")
            return

        # Auto complete (no HITL or simulated mode)
        if simulated and has_human_confirm:
            decision = random.choice(["approved", "rejected"])
            feedback = f"[SIMULATED] Auto-{decision}"
            store.add_human_decision(task_id, "review", decision, feedback, "system")
            result["review_decision"] = decision
            result["human_input"] = feedback

        _update_node_executions(task_id, workflow, result, "success")
        final_status = (
            "completed" if result.get("review_decision") != "rejected" else "failed"
        )
        store.update_task_status(task_id, final_status, result)

    except Exception as e:
        store.update_task_status(task_id, "failed", {"error": str(e)})
        raise


async def _resume_execution(task_id: str, decision: str, feedback: str):
    """Resume a waiting_human task with the human's decision."""
    if task_id not in _resume_cache:
        raise HTTPException(
            status_code=500, detail="Cannot resume — no cached graph state."
        )

    graph, config = _resume_cache.pop(task_id)
    state_update = {"review_decision": decision, "human_input": feedback}

    try:
        store.update_task_status(task_id, "running")
        result = await asyncio.to_thread(graph.invoke, state_update, config)
        store.update_task_status(
            task_id, "completed" if decision == "approved" else "failed", result
        )
    except Exception as e:
        store.update_task_status(task_id, "failed", {"error": str(e)})
        raise


def _update_node_executions(task_id: str, workflow: dict, result: dict, status: str):
    for node in workflow.get("nodes", []):
        for exec_record in reversed(store.get_node_executions(task_id)):
            if (
                exec_record["node_id"] == node["id"]
                and exec_record["status"] == "running"
            ):
                store.complete_node_execution(
                    exec_record["id"],
                    status,
                    {"result": str(result.get("exec_output", ""))[:500]},
                )
                break


# ── Routes ──────────────────────────────────────────────


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(body: TaskCreate):
    workflow = store.get_workflow(body.workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found.")
    task = store.create_task(body.workflow_id, body.task_input, body.created_by)
    asyncio.create_task(
        _execute_workflow(task["id"], workflow["definition"], body.task_input)
    )
    return TaskResponse(**task)


@router.get("", response_model=TaskListResponse)
async def list_tasks():
    tasks = store.list_tasks()
    return TaskListResponse(tasks=[TaskResponse(**t) for t in tasks], total=len(tasks))


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(task_id: str):
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    node_execs = store.get_node_executions(task_id)
    hum_decs = store.get_human_decisions(task_id)
    wf = store.get_workflow(task.get("workflow_id", ""))
    return TaskDetailResponse(
        **task,
        node_executions=[NodeExecutionResponse(**e) for e in node_execs],
        human_decisions=[HumanDecisionResponse(**d) for d in hum_decs],
        workflow_name=wf["name"] if wf else "",
    )


@router.post("/{task_id}/human-decision", response_model=HumanDecisionResponse)
async def submit_human_decision(task_id: str, body: HumanDecisionRequest):
    task = store.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")
    if task["status"] != "waiting_human":
        raise HTTPException(
            status_code=409, detail=f"Task is not waiting: {task['status']}"
        )

    decision = store.add_human_decision(
        task_id, "review", body.decision, body.feedback, body.decided_by
    )

    # Resume execution with injected decision
    asyncio.create_task(_resume_execution(task_id, body.decision, body.feedback))

    return HumanDecisionResponse(**decision)
