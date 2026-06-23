"""Integration tests — full-stack verification."""

import os, time
from fastapi.testclient import TestClient
from flowcraft.api.app import app

os.environ["ENABLE_SIMULATED_REVIEW"] = "true"
client = TestClient(app)
H = {"X-API-Key": "flowcraft-dev-key-change-in-production"}


def test_workflow_crud():
    """Create, list, get, update, delete workflow."""
    r = client.post(
        "/api/workflows",
        headers=H,
        json={
            "name": "Integration Test WF",
            "definition": {
                "nodes": [{"id": "n1", "type": "planner"}],
                "edges": [{"source": "n1", "target": "__end__"}],
            },
        },
    )
    assert r.status_code == 201
    wf_id = r.json()["id"]

    r = client.get("/api/workflows", headers=H)
    assert r.json()["total"] >= 1

    r = client.put(f"/api/workflows/{wf_id}", headers=H, json={"name": "Updated"})
    assert r.json()["version"] == 2

    r = client.delete(f"/api/workflows/{wf_id}", headers=H)
    assert r.status_code == 204


def test_task_lifecycle():
    """Create task and verify status tracking."""
    wf = client.post(
        "/api/workflows",
        headers=H,
        json={
            "name": "Task Lifecycle Test",
            "definition": {
                "nodes": [
                    {"id": "plan", "type": "planner"},
                    {"id": "review", "type": "reviewer", "human_confirm": True},
                ],
                "edges": [
                    {"source": "plan", "target": "review"},
                    {
                        "source": "review",
                        "target": "__end__",
                        "condition": {
                            "field": "review_decision",
                            "op": "==",
                            "value": "approved",
                        },
                    },
                ],
            },
        },
    )
    wf_id = wf.json()["id"]

    task = client.post(
        "/api/tasks", headers=H, json={"workflow_id": wf_id, "task_input": "Test"}
    )
    assert task.status_code == 201
    tid = task.json()["id"]

    # Wait for execution
    for _ in range(10):
        time.sleep(0.3)
        r = client.get(f"/api/tasks/{tid}", headers=H)
        if r.json()["status"] in ("completed", "failed"):
            break

    r = client.get(f"/api/tasks/{tid}", headers=H)
    assert len(r.json().get("node_executions", [])) > 0

    client.delete(f"/api/workflows/{wf_id}", headers=H)


def test_auth():
    """Verify authentication requirements."""
    r = client.get("/api/workflows")
    assert r.status_code == 401

    r = client.get("/api/workflows", headers={"X-API-Key": "wrong"})
    assert r.status_code == 403


def test_openapi():
    """Verify OpenAPI docs are accessible."""
    for path in ["/docs", "/redoc", "/api/openapi.json"]:
        r = client.get(path)
        assert r.status_code == 200


def test_retry_loop():
    """Verify retry loop with max_retries enforcement."""
    wf = client.post(
        "/api/workflows",
        headers=H,
        json={
            "name": "Retry Loop Test",
            "definition": {
                "nodes": [
                    {"id": "plan", "type": "planner"},
                    {"id": "exec", "type": "executor"},
                    {"id": "review", "type": "reviewer"},
                ],
                "edges": [
                    {"source": "plan", "target": "exec"},
                    {"source": "exec", "target": "review"},
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
                    {
                        "source": "review",
                        "target": "__end__",
                        "condition": {
                            "field": "review_decision",
                            "op": "==",
                            "value": "approved",
                        },
                    },
                ],
            },
        },
    )
    assert wf.status_code == 201
    wf_id = wf.json()["id"]

    task = client.post(
        "/api/tasks", headers=H, json={"workflow_id": wf_id, "task_input": "Test retry"}
    )
    assert task.status_code == 201

    for _ in range(15):
        time.sleep(0.3)
        r = client.get(f"/api/tasks/{task.json()['id']}", headers=H)
        if r.json()["status"] in ("completed", "failed"):
            count = r.json()["current_state_snapshot"]["retry_count"]
            assert count <= 2, f"Retry count {count} exceeded max_retries 2"
            break

    client.delete(f"/api/workflows/{wf_id}", headers=H)


def test_human_decision():
    """Verify human decision submission."""
    wf = client.post(
        "/api/workflows",
        headers=H,
        json={
            "name": "Decision Test",
            "definition": {
                "nodes": [{"id": "n1", "type": "planner"}],
                "edges": [{"source": "n1", "target": "__end__"}],
            },
        },
    )
    wf_id = wf.json()["id"]

    task = client.post(
        "/api/tasks", headers=H, json={"workflow_id": wf_id, "task_input": "Test"}
    )
    tid = task.json()["id"]

    # Submitting on non-waiting task should 409
    r = client.post(
        f"/api/tasks/{tid}/human-decision", headers=H, json={"decision": "approved"}
    )
    assert r.status_code == 409

    client.delete(f"/api/workflows/{wf_id}", headers=H)


print("Running integration tests...")
test_workflow_crud()
print("  PASS: workflow CRUD")
test_task_lifecycle()
print("  PASS: task lifecycle")
test_auth()
print("  PASS: authentication")
test_openapi()
print("  PASS: OpenAPI docs")
test_retry_loop()
print("  PASS: retry loop")
test_human_decision()
print("  PASS: human decision validation")
print("\nAll 6 integration tests passed!")
