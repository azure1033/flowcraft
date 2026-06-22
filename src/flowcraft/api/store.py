"""In-memory data store for FlowCraft API (MVP — will be replaced by PostgreSQL).

Stores workflows, tasks, node executions, and human decisions in memory.
Thread-safe with simple locks for concurrent access.
"""

import copy
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class Store:
    """Thread-safe in-memory store for FlowCraft entities."""

    def __init__(self):
        self._lock = threading.Lock()
        self._workflows: Dict[str, dict] = {}
        self._tasks: Dict[str, dict] = {}
        self._node_executions: Dict[str, List[dict]] = {}  # task_id -> list
        self._human_decisions: Dict[str, List[dict]] = {}  # task_id -> list

    # ── Workflows ──────────────────────────────────────

    def create_workflow(self, name: str, description: str, definition: dict) -> dict:
        workflow_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        wf = {
            "id": workflow_id,
            "name": name,
            "description": description,
            "definition": definition,
            "version": 1,
            "created_at": now,
            "updated_at": now,
        }
        with self._lock:
            self._workflows[workflow_id] = wf
        return copy.deepcopy(wf)

    def get_workflow(self, workflow_id: str) -> Optional[dict]:
        wf = self._workflows.get(workflow_id)
        return copy.deepcopy(wf) if wf else None

    def list_workflows(self) -> List[dict]:
        with self._lock:
            return [copy.deepcopy(wf) for wf in self._workflows.values()]

    def update_workflow(self, workflow_id: str, **fields) -> Optional[dict]:
        wf = self._workflows.get(workflow_id)
        if not wf:
            return None
        with self._lock:
            for key, value in fields.items():
                if value is not None:
                    wf[key] = value
            wf["version"] += 1
            wf["updated_at"] = datetime.now(timezone.utc)
        return copy.deepcopy(wf)

    def delete_workflow(self, workflow_id: str) -> bool:
        with self._lock:
            if workflow_id in self._workflows:
                del self._workflows[workflow_id]
                return True
            return False

    # ── Tasks ──────────────────────────────────────────

    def create_task(
        self, workflow_id: str, task_input: str, created_by: str = "api"
    ) -> dict:
        task_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        task = {
            "id": task_id,
            "workflow_id": workflow_id,
            "status": "pending",
            "task_input": task_input,
            "created_by": created_by,
            "created_at": now,
            "started_at": None,
            "completed_at": None,
            "current_state_snapshot": None,
        }
        with self._lock:
            self._tasks[task_id] = task
        return copy.deepcopy(task)

    def get_task(self, task_id: str) -> Optional[dict]:
        task = self._tasks.get(task_id)
        return copy.deepcopy(task) if task else None

    def list_tasks(self) -> List[dict]:
        with self._lock:
            return [copy.deepcopy(t) for t in self._tasks.values()]

    def update_task_status(
        self, task_id: str, status: str, snapshot: dict = None
    ) -> Optional[dict]:
        task = self._tasks.get(task_id)
        if not task:
            return None
        with self._lock:
            task["status"] = status
            if snapshot:
                task["current_state_snapshot"] = snapshot
            if status == "running" and not task["started_at"]:
                task["started_at"] = datetime.now(timezone.utc)
            if status in ("completed", "failed"):
                task["completed_at"] = datetime.now(timezone.utc)
        return copy.deepcopy(task)

    # ── Node Executions ────────────────────────────────

    def add_node_execution(
        self, task_id: str, node_id: str, node_type: str, input_snapshot: dict
    ) -> str:
        exec_id = str(uuid.uuid4())
        record = {
            "id": exec_id,
            "task_id": task_id,
            "node_id": node_id,
            "node_type": node_type,
            "status": "running",
            "started_at": datetime.now(timezone.utc),
            "completed_at": None,
            "duration_ms": None,
            "input_snapshot": input_snapshot,
            "output_snapshot": None,
        }
        with self._lock:
            self._node_executions.setdefault(task_id, []).append(record)
        return exec_id

    def complete_node_execution(self, exec_id: str, status: str, output_snapshot: dict):
        with self._lock:
            for records in self._node_executions.values():
                for r in records:
                    if r["id"] == exec_id:
                        r["status"] = status
                        r["completed_at"] = datetime.now(timezone.utc)
                        r["output_snapshot"] = output_snapshot
                        if r["started_at"] and r["completed_at"]:
                            delta = r["completed_at"] - r["started_at"]
                            r["duration_ms"] = int(delta.total_seconds() * 1000)
                        return

    def get_node_executions(self, task_id: str) -> List[dict]:
        return [copy.deepcopy(r) for r in self._node_executions.get(task_id, [])]

    # ── Human Decisions ────────────────────────────────

    def add_human_decision(
        self, task_id: str, node_id: str, decision: str, feedback: str, decided_by: str
    ) -> dict:
        dec_id = str(uuid.uuid4())
        record = {
            "id": dec_id,
            "task_id": task_id,
            "node_id": node_id,
            "decision": decision,
            "feedback": feedback,
            "decided_at": datetime.now(timezone.utc),
            "decided_by": decided_by,
        }
        with self._lock:
            self._human_decisions.setdefault(task_id, []).append(record)
        return copy.deepcopy(record)

    def get_human_decisions(self, task_id: str) -> List[dict]:
        return [copy.deepcopy(d) for d in self._human_decisions.get(task_id, [])]

    # ── Stats ──────────────────────────────────────────

    @property
    def workflow_count(self) -> int:
        return len(self._workflows)

    @property
    def task_count(self) -> int:
        return len(self._tasks)


# Global singleton store instance
store = Store()
