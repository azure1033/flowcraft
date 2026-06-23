"""FlowCraft FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .workflows import router as workflows_router
from .tasks import router as tasks_router
from .ws import router as ws_router
from .schemas import HealthResponse
from .store import store

app = FastAPI(
    title="FlowCraft API",
    description="""Open Source Visual Workflow Orchestration Platform for LLM Agent Pipelines.

## Core Concepts

- **Workflows**: Visual agent pipelines stored as JSON definitions (nodes + edges).
- **Tasks**: Executable instances of workflows with full lifecycle tracking.
- **Human Decisions**: Manual review and approval for quality-check nodes.

## Authentication

All endpoints require an `X-API-Key` header. Configure via `API_KEY` in `.env`.
Default (dev): `flowcraft-dev-key-change-in-production`

## Node Types

| Type | Description |
|------|-------------|
| `planner` | Decomposes tasks into execution steps |
| `executor` | Executes individual steps (optionally with tools) |
| `reviewer` | Evaluates results (can require human approval) |
| `tool` | Direct MCP tool invocation |

## Quick Start

```python
# 1. Create a workflow
POST /api/workflows
{
  "name": "Demo",
  "definition": {
    "nodes": [
      {"id": "plan", "type": "planner"},
      {"id": "exec", "type": "executor"},
      {"id": "review", "type": "reviewer"}
    ],
    "edges": [
      {"source": "plan", "target": "exec"},
      {"source": "exec", "target": "review"},
      {"source": "review", "target": "__end__",
       "condition": {"field": "review_decision", "op": "==", "value": "approved"}}
    ]
  }
}

# 2. Execute it
POST /api/tasks
{
  "workflow_id": "<from-above>",
  "task_input": "Write a poem about Python"
}

# 3. Check result
GET /api/tasks/<task_id>
```
""",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(workflows_router)
app.include_router(tasks_router)
app.include_router(ws_router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint — returns service status and counts."""
    return HealthResponse(
        status="ok",
        version="0.1.0",
        workflows_count=store.workflow_count,
        tasks_count=store.task_count,
    )


@app.get("/api/openapi.json", include_in_schema=False)
async def custom_openapi():
    """Expose OpenAPI spec for tooling."""
    return app.openapi()
