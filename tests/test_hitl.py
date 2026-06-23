"""Human-in-the-Loop integration test."""

import os
from fastapi.testclient import TestClient
from flowcraft.api.app import app

os.environ["ENABLE_SIMULATED_REVIEW"] = "true"
client = TestClient(app)
H = {"X-API-Key": "flowcraft-dev-key-change-in-production"}

print("=== HITL Integration Test ===\n")

# Create workflow with human_confirm
wf = client.post(
    "/api/workflows",
    headers=H,
    json={
        "name": "HITL Test",
        "definition": {
            "nodes": [
                {"id": "plan", "type": "planner"},
                {"id": "exec", "type": "executor"},
                {"id": "review", "type": "reviewer", "human_confirm": True},
            ],
            "edges": [
                {"source": "plan", "target": "exec"},
                {"source": "exec", "target": "review"},
                {
                    "source": "review",
                    "target": "__end__",
                    "condition": {
                        "field": "review_decision",
                        "op": "==",
                        "value": "approved",
                    },
                },
                {
                    "source": "review",
                    "target": "exec",
                    "condition": {
                        "field": "review_decision",
                        "op": "==",
                        "value": "rejected",
                    },
                    "loop": {"type": "retry", "max_retries": 2},
                },
            ],
        },
    },
)
assert wf.status_code == 201, f"Create: {wf.status_code}"
wf_id = wf.json()["id"]
print(f"1. Created workflow: {wf_id[:8]}...")

# Create task
task = client.post(
    "/api/tasks",
    headers=H,
    json={
        "workflow_id": wf_id,
        "task_input": "Test HITL flow",
    },
)
assert task.status_code == 201
task_id = task.json()["id"]
print(f"2. Created task: {task_id[:8]}... status={task.json()['status']}")

# Simulated review should auto-complete
import time

for i in range(10):
    time.sleep(0.5)
    r = client.get(f"/api/tasks/{task_id}", headers=H)
    status = r.json()["status"]
    decisions = len(r.json().get("human_decisions", []))
    if status in ("completed", "failed"):
        print(f"3. Auto-completed: status={status} decisions={decisions}")
        break
else:
    status = client.get(f"/api/tasks/{task_id}", headers=H).json()["status"]
    print(f"3. Still running: {status}")

# Test without simulated mode
os.environ["ENABLE_SIMULATED_REVIEW"] = "false"
task2 = client.post(
    "/api/tasks",
    headers=H,
    json={
        "workflow_id": wf_id,
        "task_input": "Non-simulated test",
    },
)
assert task2.status_code == 201
task2_id = task2.json()["id"]

# Should go to waiting_human (or running, LLM dependent)
for i in range(10):
    time.sleep(0.5)
    r = client.get(f"/api/tasks/{task2_id}", headers=H)
    st = r.json()["status"]
    if st in ("waiting_human", "completed", "failed"):
        print(f"4. Non-simulated: status={st}")
        break
else:
    print(f"4. Non-simulated: still running (may need LLM key)")

# Submit human decision
dec = client.post(
    f"/api/tasks/{task2_id}/human-decision",
    headers=H,
    json={
        "decision": "approved",
        "feedback": "Good test",
    },
)
print(f"5. Decision submitted: {dec.status_code}")

# Cleanup
client.delete(f"/api/workflows/{wf_id}", headers=H)
print(f"\n=== HITL Tests Complete ===")
