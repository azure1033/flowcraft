# Tasks: init-flowcraft-platform

## 1. Project Scaffolding & Shared Schema

- [x] 1.1 Initialize monorepo root: pnpm workspace config, uv workspace config, root package.json/pyproject.toml
- [x] 1.2 Create `schemas/workflow.schema.json` — define JSON Schema for nodes, edges, conditions, retry loop config
- [x] 1.3 Create `.env.example` with all required environment variables (LLM keys, DB URLs, Redis, MCP server endpoints)
- [x] 1.4 Create `.gitignore`, `LICENSE` (Apache 2.0), `CONTRIBUTING.md`, `README.md` (bilingual scaffold)

## 2. Backend — Data Models & Persistence

- [ ] 2.1 Initialize FastAPI project in `apps/backend/` with uv, add dependencies (fastapi, sqlalchemy, asyncpg, langgraph, langchain)
- [ ] 2.2 Implement SQLAlchemy ORM models: `WorkflowDefinition`, `TaskInstance`, `NodeExecution`, `HumanDecision` per design D4
- [ ] 2.3 Implement Alembic migrations for initial schema
- [ ] 2.4 Implement PostgreSQL checkpointer adapter (LangGraph PostgresSaver integration)
- [ ] 2.5 Implement Redis connection manager for WebSocket pub/sub

## 3. Backend — Agent Nodes & State

- [x] 3.1 Implement `AgentState` TypedDict with all fields (messages, plan, current_step, exec_output, review_decision, human_input, retry_count, max_retries)
- [x] 3.2 Implement `planner_agent` node — takes user input, outputs task decomposition `plan` dict via LangChain ChatModel
- [x] 3.3 Implement `executor_agent` node — executes current step, calls tools via LangChain Tool binding, outputs `exec_output`
- [x] 3.4 Implement `review_agent` node — evaluates exec_output against original task, outputs `review_decision` (approved/rejected)
- [ ] 3.5 Implement `tool_executor` node factory — wraps MCP tool as LangChain Tool for agent invocation

## 4. Backend — GraphCompiler & Execution Engine

- [x] 4.1 Implement `GraphCompiler` class — parse JSON nodes into `builder.add_node()` calls per design D5
- [x] 4.2 Implement edge compilation — `add_edge` for direct edges, `add_conditional_edges` for condition edges
- [x] 4.3 Implement simple condition compilation — compile `{field, op, value}` into comparison lambda
- [ ] 4.4 Implement advanced condition compilation — RestrictedPython sandbox with 5s timeout + memory limit
- [x] 4.5 Implement retry loop detection — detect Reviewer→Executor back-edges, inject retry_count guard and max_retries enforcement
- [ ] 4.6 Implement `AgentNodeFactory` with registration interface [EXTENSIBLE]
- [x] 4.7 Implement task state machine — pending → running → waiting_human → completed/failed transitions

## 5. Backend — API & WebSocket Layer

- [ ] 5.1 Implement REST router `/api/workflows` — CRUD with version auto-increment
- [ ] 5.2 Implement REST router `/api/tasks` — create task from workflow, list, detail
- [ ] 5.3 Implement `POST /api/tasks/{id}/human-decision` — accept decision, inject state, resume graph
- [ ] 5.4 Implement `GET /api/tasks/{id}/audit` — aggregate node_executions + human_decisions
- [ ] 5.5 Implement WebSocket handler `ws/tasks/{task_id}` — subscribe to Redis channel, forward events per design D8
- [ ] 5.6 Implement API Key middleware — validate X-API-Key header against `.env` config
- [ ] 5.7 Add request/response Pydantic models and auto-generate OpenAPI docs

## 6. Backend — Human-in-the-Loop Flow

- [ ] 6.1 Implement Reviewer node interrupt — detect `human_confirm=true`, call `interrupt()`, persist checkpoint
- [ ] 6.2 Implement WebSocket notification — push `review_pending` event with execution context to frontend
- [ ] 6.3 Implement state injection on decision — set review_decision + human_input, resume from checkpoint
- [ ] 6.4 Implement simulated review mode — auto-generate random decision when `ENABLE_SIMULATED_REVIEW=true`
- [ ] 6.5 Write integration test: full cycle plan→exec→review(human_confirm)→decision→resume→end

## 7. MCP Tool Ecosystem

- [ ] 7.1 Implement MCP client connection manager — connect to configured servers at engine startup, auto-reconnect
- [ ] 7.2 Implement tool registration — call `tools/list`, wrap each tool as LangChain Tool object
- [ ] 7.3 Implement tool invocation bridge — LangChain Tool → MCP `tools/call` → result → ToolMessage
- [ ] 7.4 [P] Implement `search-server` in `tools/search-server/` — Docker container with Tavily Search MCP server
- [ ] 7.5 [P] Implement `code-sandbox` in `tools/code-sandbox/` — Docker container with isolated Python execution MCP server
- [ ] 7.6 [P] Implement `http-client` in `tools/http-client/` — Docker container with HTTP request MCP server
- [ ] 7.7 Create Dockerfiles and configuration for all three MCP tool servers
- [ ] 7.8 Create MCP server development template and documentation [EXTENSIBLE]

## 8. Frontend — Project Setup & Canvas

- [ ] 8.1 Initialize React + TypeScript + Vite project in `apps/frontend/`, add deps (reactflow, zustand, socket.io-client)
- [ ] 8.2 Generate TypeScript types from `schemas/workflow.schema.json`
- [ ] 8.3 Implement Zustand store — canvas state (nodes, edges), workflow metadata, WebSocket connection state
- [ ] 8.4 Implement React Flow canvas component with drag-from-sidebar support
- [ ] 8.5 Implement custom node components for all 5 types (Planner, Executor, Reviewer, Tool, Conditional Edge) with type-specific visual styling
- [ ] 8.6 Implement node sidebar panel — draggable node list with type icons and labels

## 9. Frontend — Editor Interaction

- [ ] 9.1 Implement node properties panel — context-sensitive configuration per node type (tools binding, human_confirm toggle, tool_name selection)
- [ ] 9.2 Implement conditional edge editor — simple mode (field/op/value dropdowns) and advanced mode (Python lambda textarea)
- [ ] 9.3 Implement canvas serialization — export workflow JSON
- [ ] 9.4 Implement canvas deserialization — import/load workflow JSON, reconstruct nodes and edges
- [ ] 9.5 Implement toolbar — Save, Export JSON, Import JSON, Run, Undo/Redo (Ctrl+Z/Y)

## 10. Frontend — API & Real-Time Integration

- [ ] 10.1 Implement API client service — wrapped fetch/axios for all REST endpoints
- [ ] 10.2 Implement WebSocket client hook — connect to `ws/tasks/{id}`, dispatch events to Zustand store
- [ ] 10.3 Implement workflow CRUD UI — template list, create, edit, delete
- [ ] 10.4 Implement task dashboard — create task, view status, task history list
- [ ] 10.5 Implement human decision dialog — review context panel, approve/reject buttons, feedback textarea
- [ ] 10.6 Implement real-time execution display — node status overlay on canvas (pending/running/done/error icons)

## 11. Observability & Audit

- [ ] 11.1 Implement node execution event emission — push node_start/node_complete/node_error to Redis channel
- [ ] 11.2 Implement NodeExecution repository — persist each node's execution record (input/output/duration/status)
- [ ] 11.3 Implement HumanDecision repository — persist each human decision record
- [ ] 11.4 Implement audit log API aggregation — join task + node_executions + human_decisions
- [ ] 11.5 Implement frontend audit log view — task detail page with timeline and node execution list

## 12. CLI & Deployment

- [ ] 12.1 Create `cli/` project scaffold with Click/Typer framework
- [ ] 12.2 Implement `agent-flow init` — scaffold project directory with `.env.example`, `docker-compose.yml`, `examples/`
- [ ] 12.3 Implement `agent-flow dev` — start frontend Vite + backend FastAPI + PostgreSQL/Redis containers, dependency check
- [ ] 12.4 Implement `agent-flow test <workflow.json>` — load workflow, execute in simulated mode, print results
- [ ] 12.5 Create `docker-compose.yml` — orchestrate all 6 services (API, engine, PostgreSQL, Redis, search-server, code-sandbox, nginx)
- [ ] 12.6 Create Nginx config — serve frontend static files, proxy `/api` and `/ws` to backend

## 13. Examples & Documentation

- [x] 13.1 [P] Create example workflow \"Daily AI News Briefing\" — Planner → Executor(search) → Reviewer
- [ ] 13.2 [P] Create example workflow "Code Review Assistant" — Planner → Executor(code_sandbox) → Reviewer(human_confirm)
- [ ] 13.3 Write OpenAPI / Swagger API documentation annotations on all endpoints
- [ ] 13.4 Write MCP tool server development guide
- [ ] 13.5 Write user guide — workflow editor usage, task execution, human review flow

## 14. Integration Testing & Polish

- [ ] 14.1 Integration test: full end-to-end flow — create workflow via API → execute → review → human decision → audit
- [ ] 14.2 Integration test: WebSocket event stream — connect, verify all event types received in correct order
- [ ] 14.3 Integration test: simulated review mode — verify auto-decision completes full cycle
- [ ] 14.4 Integration test: retry loop with max_retries enforcement
- [ ] 14.5 Integration test: MCP tool invocation — agent uses search tool, verifies result
- [ ] 14.6 [P] Frontend smoke test — canvas renders, drag nodes, connect edges, export JSON
- [ ] 14.7 [P] CLI smoke test — `agent-flow init`, `agent-flow dev`, `agent-flow test`
- [ ] 14.8 Performance test: workflow with 20+ nodes, verify canvas responsiveness
- [ ] 14.9 Security test: RestrictedPython sandbox bypass attempts, verify blocked
