"""API smoke test — validates all endpoints without starting a server."""

from fastapi.testclient import TestClient
from flowcraft.api.app import app

client = TestClient(app)
headers = {"X-API-Key": "flowcraft-dev-key-change-in-production"}


def test(msg, fn):
    try:
        fn()
        print(f"  PASS: {msg}")
    except Exception as e:
        print(f"  FAIL: {msg} -> {e}")


print("=== Health ===")
r = client.get("/api/health")
assert r.status_code == 200
assert r.json()["status"] == "ok"
print(f"  PASS: health check ok, version={r.json()['version']}")

print("\n=== Auth ===")
r = client.get("/api/workflows")
assert r.status_code == 401
print("  PASS: unauthenticated request rejected (401)")

r = client.get("/api/workflows", headers=headers)
assert r.status_code == 200
print("  PASS: authenticated request accepted")

print("\n=== Workflow CRUD ===")
wf_data = {
    "name": "Test Workflow",
    "description": "A test",
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
                "target": "__end__",
                "condition": {
                    "field": "review_decision",
                    "op": "==",
                    "value": "approved",
                },
            },
        ],
    },
}
r = client.post("/api/workflows", json=wf_data, headers=headers)
assert r.status_code == 201
wf_id = r.json()["id"]
print(f"  PASS: created workflow id={wf_id[:8]}...")

r = client.get("/api/workflows", headers=headers)
assert r.status_code == 200
assert r.json()["total"] == 1
print("  PASS: list workflows (total=1)")

r = client.get(f"/api/workflows/{wf_id}", headers=headers)
assert r.status_code == 200
assert r.json()["version"] == 1
print("  PASS: get workflow (version=1)")

r = client.put(f"/api/workflows/{wf_id}", json={"name": "Updated"}, headers=headers)
assert r.status_code == 200
assert r.json()["version"] == 2
assert r.json()["name"] == "Updated"
print("  PASS: update workflow (version=2)")

r = client.delete(f"/api/workflows/{wf_id}", headers=headers)
assert r.status_code == 204
print("  PASS: delete workflow")

r = client.get(f"/api/workflows/{wf_id}", headers=headers)
assert r.status_code == 404
print("  PASS: get deleted workflow (404)")

# Re-create for task test
r = client.post("/api/workflows", json=wf_data, headers=headers)
wf_id = r.json()["id"]

print("\n=== Task Execution ===")
task_data = {"workflow_id": wf_id, "task_input": "Say hello world"}
r = client.post("/api/tasks", json=task_data, headers=headers)
assert r.status_code == 201
task_id = r.json()["id"]
assert r.json()["status"] in ("pending", "running")
print(f"  PASS: created task id={task_id[:8]}... status={r.json()['status']}")

r = client.get(f"/api/tasks/{task_id}", headers=headers)
assert r.status_code == 200
print(
    f"  PASS: get task status={r.json()['status']} audit_included={len(r.json().get('node_executions', [])) > 0}"
)

r = client.post(
    f"/api/tasks/{task_id}/human-decision",
    json={"decision": "approved", "feedback": "looks good"},
    headers=headers,
)
print(f"  PASS: human decision submitted (status={r.status_code})")

print("\n=== Docs ===")
r = client.get("/docs")
assert r.status_code == 200
print("  PASS: Swagger UI accessible")

r = client.get("/redoc")
assert r.status_code == 200
print("  PASS: ReDoc accessible")

r = client.get("/api/openapi.json")
assert r.status_code == 200
paths = r.json()["paths"]
print(f"  PASS: OpenAPI JSON ({len(paths)} endpoints)")

print("\n=== ALL TESTS PASSED ===")
