"""WebSocket handler for real-time task event streaming.

Polls task status every 2 seconds and pushes events to connected clients.
In Phase 2, this will be replaced by Redis pub/sub for true real-time.
"""

import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .store import store

router = APIRouter(prefix="/ws", tags=["websocket"])


@router.websocket("/tasks/{task_id}")
async def task_events(websocket: WebSocket, task_id: str):
    """Stream task execution events via WebSocket.

    Events: node_start, node_complete, review_pending, task_complete, task_failed
    """
    await websocket.accept()

    last_node_count = 0
    try:
        while True:
            task = store.get_task(task_id)
            if not task:
                await websocket.send_json(
                    {"event": "error", "detail": "Task not found"}
                )
                break

            status = task["status"]
            executions = store.get_node_executions(task_id)

            # Send node events
            for i in range(last_node_count, len(executions)):
                exec_record = executions[i]
                await websocket.send_json(
                    {
                        "event": "node_start",
                        "task_id": task_id,
                        "node_id": exec_record["node_id"],
                        "node_type": exec_record["node_type"],
                        "status": exec_record["status"],
                        "timestamp": str(exec_record.get("started_at", "")),
                    }
                )

            # Check completed nodes
            for exec_record in executions:
                if exec_record["status"] != "running":
                    await websocket.send_json(
                        {
                            "event": "node_complete",
                            "task_id": task_id,
                            "node_id": exec_record["node_id"],
                            "status": exec_record["status"],
                            "duration_ms": exec_record.get("duration_ms"),
                        }
                    )

            last_node_count = len(executions)

            # Special events
            if status == "waiting_human":
                await websocket.send_json(
                    {
                        "event": "review_pending",
                        "task_id": task_id,
                        "context": {"snapshot": task.get("current_state_snapshot", {})},
                    }
                )

            if status in ("completed", "failed"):
                await websocket.send_json(
                    {
                        "event": f"task_{status}",
                        "task_id": task_id,
                        "status": status,
                    }
                )
                break

            await asyncio.sleep(2)

    except WebSocketDisconnect:
        pass
    except Exception:
        pass
