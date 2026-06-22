# FlowCraft

<p align="center">
  <strong>🛠️ Visual Workflow Orchestration Platform for LLM Agent Pipelines</strong>
</p>

<p align="center">
  <em>Draw your agent pipeline on a canvas → export as JSON → execute via LangGraph engine.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/status-MVP-orange" alt="Status: MVP">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue" alt="Apache 2.0">
  <img src="https://img.shields.io/badge/python-3.11%2B-blue" alt="Python 3.11+">
  <img src="https://img.shields.io/badge/react-19-61dafb" alt="React 19">
</p>

---

## What is FlowCraft?

FlowCraft turns LLM agent pipeline design into a **visual drag-and-drop experience**. Instead of writing LangGraph code by hand, you draw your workflow on a canvas — connecting Planner, Executor, and Reviewer nodes — then hit **Run**. The platform compiles your design into an executable LangGraph StateGraph with PostgreSQL checkpointing, retry loops, and human-in-the-loop approval.

## Architecture

```
                  ┌──────────────────────────┐
                  │     Frontend (React)      │
                  │  React Flow Canvas        │
                  │  · Drag-drop 5 node types │
                  │  · JSON export/import     │
                  │  · Real-time status poll  │
                  └──────────┬───────────────┘
                             │ HTTP / WebSocket
                  ┌──────────▼───────────────┐
                  │   API Gateway (FastAPI)   │
                  │  · REST CRUD endpoints    │
                  │  · OpenAPI auto-docs      │
                  │  · API Key auth           │
                  └──────────┬───────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐
│ Workflow      │  │ Task Scheduler  │  │ LangGraph Engine │
│ Manager       │  │ · State Machine │  │ · GraphCompiler  │
│ · Template CRUD│  │ · pending→run  │  │ · Agent Nodes    │
│ · Versioning  │  │ →waiting→done   │  │ · Checkpointing  │
└───────┬───────┘  └────────┬────────┘  │ · MCP Client     │
        │                   │            └────────┬─────────┘
        └───────────────────┼─────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │      PostgreSQL + Redis    │
              │  (persistence + pub/sub)   │
              └───────────────────────────┘
```

**The core trick**: User draws `Plan → Exec → Review` on canvas → exported as JSON → `GraphCompiler` builds a `StateGraph` → LangGraph executes with checkpointing and retry loops.

## Key Features

| Feature | Status |
|---------|--------|
| 🎨 Visual canvas with 5 node types (Planner, Executor, Reviewer, Tool, Condition) | ✅ |
| 🧠 JSON → LangGraph StateGraph compiler | ✅ |
| 🔁 Retry loop (Reviewer → Executor) with max_retries guard | ✅ |
| 👤 Human-in-the-loop (interrupt, approve/reject, resume) | ✅ |
| 🔑 API Key authentication | ✅ |
| 📊 Execution audit trail (node_executions + human_decisions) | ✅ |
| 📝 OpenAPI auto-documentation (Swagger UI + ReDoc) | ✅ |
| 🐳 Docker containerization (backend image verified) | ✅ |
| 🔌 MCP tool integration (Tavily search, code sandbox) | 🚧 Planned |
| 📡 WebSocket real-time events | 🚧 Planned |
| 🐘 PostgreSQL persistence (currently in-memory) | 🚧 Planned |
| 🖥️ `agent-flow` CLI | 🚧 Planned |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 22+ / pnpm
- OpenAI API key (or compatible)
- Docker (optional, for containerized deployment)

### 1. Clone & Install

```bash
git clone https://github.com/azure1033/flowcraft.git
cd flowcraft

# Python backend
uv sync

# Frontend
cd apps/frontend && pnpm install && cd ../..
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env → set OPENAI_API_KEY=sk-your-key-here
```

### 3. Run

**Option A — Local dev (two terminals):**

```bash
# Terminal 1: Backend API
uv run uvicorn flowcraft.api.app:app --reload
# → http://localhost:8000/docs

# Terminal 2: Frontend
cd apps/frontend && pnpm dev
# → http://localhost:5173
```

**Option B — Run engine demo (no UI):**

```bash
uv run python -m flowcraft.main
```

**Option C — Docker:**

```bash
docker compose up
# → Frontend: http://localhost
# → API docs: http://localhost/docs
```

## API Quick Examples

```bash
# Health check
curl http://localhost:8000/api/health

# Create a workflow
curl -X POST http://localhost:8000/api/workflows \
  -H "X-API-Key: flowcraft-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Code Review",
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
         "condition": {"field": "review_decision", "op": "==", "value": "approved"}},
        {"source": "review", "target": "exec",
         "condition": {"field": "review_decision", "op": "==", "value": "rejected"},
         "loop": {"type": "retry", "max_retries": 3}}
      ]
    }
  }'

# Execute the workflow
curl -X POST http://localhost:8000/api/tasks \
  -H "X-API-Key: flowcraft-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"workflow_id": "<workflow-id>", "task_input": "Review this Python code for security issues"}'

# Check task status with audit trail
curl http://localhost:8000/api/tasks/<task-id> \
  -H "X-API-Key: flowcraft-dev-key-change-in-production"

# Submit human review decision
curl -X POST http://localhost:8000/api/tasks/<task-id>/human-decision \
  -H "X-API-Key: flowcraft-dev-key-change-in-production" \
  -H "Content-Type: application/json" \
  -d '{"decision": "approved", "feedback": "Looks good"}'
```

## Node Types

```
📋 Planner   — Decomposes tasks into execution steps (outputs plan dict)
⚡ Executor  — Executes individual steps, optionally calls tools
🔍 Reviewer  — Evaluates results, outputs approved/rejected
   👤        — With human_confirm=true: pauses for manual approval
🔧 Tool      — Direct MCP tool invocation (search, code sandbox, HTTP)
──▶ Edge     — Direct connection between nodes
- -▶ Edge    — Conditional edge with {field, op, value} routing
```

## Project Structure

```
flowcraft/
├── src/flowcraft/           # Python backend
│   ├── state.py             # AgentState TypedDict
│   ├── agents.py            # Planner, Executor, Reviewer agents
│   ├── compiler.py          # GraphCompiler (JSON → StateGraph)
│   ├── main.py              # CLI demo runner
│   └── api/                 # FastAPI application
│       ├── app.py           # App factory + OpenAPI
│       ├── schemas.py       # Pydantic request/response models
│       ├── store.py         # In-memory data store
│       ├── deps.py          # API Key middleware
│       ├── workflows.py     # /api/workflows CRUD
│       └── tasks.py         # /api/tasks + human-decision
│
├── apps/frontend/           # React frontend
│   └── src/
│       ├── components/
│       │   ├── Canvas.tsx           # React Flow canvas
│       │   ├── Sidebar.tsx          # Draggable node panel
│       │   ├── Toolbar.tsx          # Save/Export/Import/Run
│       │   ├── PropertiesPanel.tsx  # Node config
│       │   ├── HumanDecisionDialog.tsx
│       │   ├── ExecutionOverlay.tsx # Task status polling
│       │   └── nodes/              # Custom node components
│       ├── stores/workflowStore.ts  # Zustand state
│       ├── api/client.ts           # API client
│       └── types/workflow.ts       # TypeScript types
│
├── schemas/
│   └── workflow.schema.json  # JSON Schema (shared FE/BE contract)
│
├── openspec/                 # OpenSpec spec-driven workflow
│   ├── config.yaml
│   └── changes/init-flowcraft-platform/
│       ├── proposal.md
│       ├── design.md
│       ├── tasks.md          # 83 tasks, 35 complete
│       └── specs/            # 6 capability specs
│
├── Dockerfile                # Backend container
├── docker-compose.yml        # Full-stack orchestration
├── nginx.conf                # Reverse proxy config
└── AGENTS.md                 # OpenCode agent instructions
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 19, React Flow (`@xyflow/react`), Zustand, Vite, TypeScript |
| **Backend API** | Python 3.12, FastAPI, Uvicorn, Pydantic |
| **Orchestration** | LangGraph, LangChain |
| **LLM** | LangChain ChatModel (OpenAI, Anthropic, etc.) |
| **Database** | PostgreSQL (planned), in-memory (current MVP) |
| **Cache/PubSub** | Redis (planned) |
| **Tools** | MCP Protocol (Model Context Protocol) |
| **Infrastructure** | Docker, Docker Compose, Nginx |

## Roadmap

- [x] LangGraph engine (GraphCompiler + Agent nodes + retry)
- [x] FastAPI REST API (CRUD + auth + OpenAPI)
- [x] React Flow canvas (drag-drop + 5 node types + properties)
- [x] Human-in-the-loop (decision dialog + status polling)
- [x] Docker containerization
- [ ] PostgreSQL persistence + Alembic migrations
- [ ] WebSocket real-time events
- [ ] MCP tool servers (Tavily search, code sandbox, HTTP client)
- [ ] `agent-flow` CLI tool
- [ ] Conditional edge editor UI
- [ ] Undo/Redo on canvas

## Contributing

FlowCraft follows a **spec-driven** development workflow via [OpenSpec](https://github.com/azure1033/flowcraft/tree/master/openspec). All changes start with a proposal → specs → design → tasks.

1. Read `AGENTS.md` for project conventions
2. Check `openspec/changes/init-flowcraft-platform/tasks.md` for pending work
3. Use Conventional Commits (`feat:`, `fix:`, `docs:`)
4. Chinese comments OK, English identifiers

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

<p align="center">
  <sub>Built with LangGraph, FastAPI, React Flow · One canvas, infinite agent pipelines.</sub>
</p>
