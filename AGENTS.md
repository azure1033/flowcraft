# AGENTS.md

FlowCraft instruction file for OpenCode sessions. Every line should help an agent avoid mistakes.

## Project State

**Greenfield.** No application code exists yet. All implementation specs live in `openspec/changes/init-flowcraft-platform/`. Architecture design doc is `agent.md` (Chinese).

## Architecture at a Glance

```
Frontend (React/TS) ──▶ API (FastAPI) ──▶ LangGraph Engine ──▶ MCP Tool Servers (Docker)
                              │                    │
                         PostgreSQL            Redis
```

5-layer: Frontend → API Gateway → Task Scheduler → LangGraph Engine → MCP Tool Servers.

The core trick: user draws a workflow on canvas → exported as JSON → `GraphCompiler` compiles JSON into a `StateGraph` → LangGraph executes with PostgreSQL checkpointing.

## Monorepo Structure (planned, not yet scaffolded)

```
flowcraft/
├── schemas/workflow.schema.json    # ★ Single source of truth — shared between FE + BE
├── apps/frontend/                  # React 18 + React Flow + Vite + Zustand
├── apps/backend/                   # FastAPI + LangGraph + LangChain + SQLAlchemy
├── tools/                          # MCP tool servers (independent Docker containers)
│   ├── search-server/              # Tavily Search
│   ├── code-sandbox/               # Isolated Python execution
│   └── http-client/                # HTTP request tool
├── cli/                            # agent-flow CLI (Click/Typer)
├── examples/                       # Sample workflow JSON files
└── openspec/                       # OpenSpec spec-driven workflow
```

**Toolchain**: pnpm workspaces for frontend, uv workspaces for Python. Do NOT mix package managers.

## OpenSpec Workflow (SPEC-DRIVEN)

This project uses OpenSpec `spec-driven` schema. Changes follow strict dependency order:

```
proposal.md → specs/<capability>/spec.md → design.md → tasks.md
```

### Key Commands

```bash
# Check what exists
openspec list --json
openspec status --change "<name>"

# Create a new change (interactive artifact workflow)
openspec new change "<kebab-case-name>"

# Get artifact template + instructions
openspec instructions <artifact-id> --change "<name>" --json

# Verify all artifacts are complete before implementing
openspec status --change "<name>"
```

### Artifact Rules (from openspec/config.yaml)

| Artifact | Rule |
|----------|------|
| `proposal` | ≤500 words, MUST include "Non-goals" section |
| `design` | MUST include ASCII architecture diagrams, document extension points explicitly |
| `tasks` | Max 4 hours per task chunk, mark parallelizable tasks with `[P]` prefix |
| `specs` | Use `Given/When/Then` scenarios, mark extensibility slots with `[EXTENSIBLE]` tag |

### Current Change: `init-flowcraft-platform`

**6 capabilities** with individual specs:
- `workflow-orchestration` — Visual canvas, 5 node types, JSON serialization
- `langgraph-execution-engine` — GraphCompiler, AgentState, conditional routing, retry loops
- `human-in-the-loop` — LangGraph interrupt/resume, decision API, simulated mode
- `mcp-tool-ecosystem` — MCP client, tool registration, containerized servers
- `execution-observability` — WebSocket events, audit tables, state snapshots
- `platform-operations` — CLI, Docker Compose, OpenAPI docs, example templates

**83 tasks** across 14 groups. Tasks marked `[P]` can run in parallel.

## Key Architecture Decisions

### Security Model
- **Auth**: Phase 1 = single API Key (`X-API-Key` header, read from `.env`). `created_by`/`decided_by` fields reserved for future OAuth2.
- **Sandbox**: User-written condition lambdas execute via **RestrictedPython** (NOT `eval()`). 5s timeout, memory limit.
- **Code execution**: Docker-isolated container, network-restricted, read-only filesystem.

### Retry Loop Policy
Only **Reviewer→Executor back-edges** (retry loop) are allowed in Phase 1. NOT general-purpose while/for loops. Each retry loop has `max_retries` guard (default 3). When exceeded, routes to `__end__`.

### LLM Configuration [TENTATIVE]
Currently: global key + global model via `.env`, multi-provider interface reserved, per-node `model` field optional override. This decision is marked TENTATIVE and may change.

### Database
4 core tables: `workflow_definitions`, `task_instances` (JSONB `current_state_snapshot`), `node_executions`, `human_decisions`. Redis for WebSocket pub/sub (`task:{id}` channels).

## Extension Points (Phase 1 reserves, does NOT implement)

| Extension | Reserved via |
|-----------|-------------|
| Custom agent node types | `AgentNodeFactory` registration interface |
| Custom MCP tool servers | Config-driven + dev template docs |
| Multi-LLM providers | `model` field + provider registry |
| OAuth2 multi-user | `created_by`/`decided_by` columns |
| Scheduled/webhook triggers | `trigger_type` enum on task_instances |
| K8s deployment | Config naming conventions consistent with docker-compose |
| Prometheus metrics | Metrics collection hook interface |
| Tool marketplace | `source` field on tool metadata |

## Conventions

- **Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`)
- **Language**: Chinese comments allowed, English identifiers (variables, functions, classes)
- **Docs**: Bilingual — Chinese primary for architecture/design, English for API docs and OSS-facing content
- **Shared schema**: `schemas/workflow.schema.json` is the contract. Changes to it MUST update both TypeScript type generation AND Pydantic models in the same PR.
- **.env**: Never commit `.env`. Always provide `.env.example` with all required keys (blank values).
- **License**: Apache 2.0

## Development (planned commands)

```bash
# Backend
cd apps/backend && uv run uvicorn src.main:app --reload

# Frontend
cd apps/frontend && pnpm dev

# Full stack (once docker-compose.yml exists)
docker compose up

# CLI
agent-flow init      # scaffold new project
agent-flow dev       # start all services
agent-flow test <file>  # run a workflow JSON in simulated mode
```

## Gotchas

- **No ripgrep (`rg`)**: The glob and grep tools may fail because `rg` is not in PATH. Use `bash` with `Get-ChildItem` and `Select-String` as fallback, or use explore/librarian agents.
- **OpenSpec CLI v1.3.1**: The `openspec` command IS installed and working. Use it — do NOT manually create `.openspec.yaml` files.
- **`agent.md` is the source of truth**: When in doubt about architecture, read `agent.md` first. The OpenSpec artifacts (proposal, specs, design) are derived from it.
- **TENTATIVE decisions**: The LLM configuration strategy is marked TENTATIVE in both spec and design. Do NOT treat it as final when implementing.
- **`[EXTENSIBLE]` markers**: When implementing, keep these interfaces abstract. Do NOT build Phase 2+ features just because the interface exists.
