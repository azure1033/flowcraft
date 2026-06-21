# Design: init-flowcraft-platform

## Context

FlowCraft 是一个开源可视化工作流编排平台，目标用户是需要将 LLM Agent 管道化执行但不想手写 LangGraph 代码的开发者。项目处于绿野阶段，无现有代码。技术栈已锁定为 React + FastAPI + LangGraph + PostgreSQL + Redis + Docker，采用 monorepo（pnpm + uv）管理。

核心约束：单框架（LangGraph）、顺序链为主、极简人工介入、MCP 解耦工具生态。

## Goals / Non-Goals

**Goals:**
- 提供可拖拽的 5 种节点类型画布，输出标准化 JSON
- 实现 JSON → StateGraph 动态编译器，支持条件分支和受控重试
- 通过 LangGraph interrupt 实现人工审核挂起/恢复
- 以 MCP 协议集成独立容器化工具服务器
- 提供 WebSocket 实时事件流和完整审计日志
- 交付 CLI 工具和 Docker Compose 一键部署

**Non-Goals:**
- 不实现并行节点执行（多 Agent 同时工作）
- 不实现图灵完备循环（仅 Reviewer→Executor 受控重试）
- 不实现多用户协作编辑 / RBAC
- 不实现可视化条件表达式构建器
- 不实现 Kubernetes / 云原生部署（Phase 1 仅 Docker Compose）

## Decisions

### D1: Monorepo 工程结构

```
flowcraft/
├── package.json              # pnpm workspace root
├── pnpm-workspace.yaml       # 前端 monorepo 声明
├── pyproject.toml            # Python workspace (uv)
├── docker-compose.yml        # 全栈编排
│
├── schemas/                  # ★ 共享契约（唯一真相源）
│   └── workflow.schema.json  # TypeScript 类型生成 + Pydantic 校验
│
├── apps/
│   ├── frontend/             # React + React Flow + Vite
│   │   ├── src/
│   │   │   ├── components/   # Canvas, NodePanel, PropertiesPanel
│   │   │   ├── stores/       # Zustand 状态管理
│   │   │   ├── hooks/        # WebSocket, API hooks
│   │   │   └── types/        # 从 schema 生成的 TS 类型
│   │   └── package.json
│   │
│   └── backend/              # FastAPI + LangGraph
│       ├── src/
│       │   ├── api/          # REST routers + WebSocket handlers
│       │   ├── engine/       # GraphCompiler, AgentState, checkpointer
│       │   ├── agents/       # planner_agent, executor_agent, review_agent
│       │   ├── mcp_client/   # MCP 客户端封装
│       │   └── models/       # SQLAlchemy ORM models
│       └── tests/
│
├── tools/                    # MCP 工具服务器（独立容器）
│   ├── search-server/        # Tavily 搜索
│   ├── code-sandbox/         # Docker 隔离代码执行
│   └── http-client/          # HTTP 请求工具
│
├── cli/                      # agent-flow 命令行
├── examples/                 # 示例工作流 JSON
└── docs/                     # 项目文档
```

**选择理由**: 共享 schema 是核心契约，放在 monorepo 根级别确保前后端类型同步。tools/ 虽是独立容器但源码归 monorepo 管理，降低贡献门槛。CLI 独立目录，未来可发布为 PyPI 包。

### D2: 前端 — React + React Flow + Zustand

```
┌────────────────────────────────────────┐
│  App Shell                             │
│  ┌──────────┐  ┌───────────────────┐   │
│  │Sidebar   │  │  React Flow       │   │
│  │Node Panel│  │  Canvas           │   │
│  │┌────────┐│  │  ┌──┐  ┌──┐  ┌──┐│   │
│  ││Planner ││  │  │P │─▶│E │─▶│R ││   │
│  ││Executor││  │  └──┘  └──┘  └──┘│   │
│  ││Reviewer││  │                   │   │
│  ││Tool    ││  │  + Properties     │   │
│  ││Cond.   ││  │    Panel (右)     │   │
│  │└────────┘│  └───────────────────┘   │
│  └──────────┘                          │
│  ┌──────────────────────────────────┐  │
│  │  Toolbar (Save/Export/Import/Run)│  │
│  └──────────────────────────────────┘  │
└────────────────────────────────────────┘
```

**选择理由**: React Flow 是 React 生态中最成熟的可视化节点编辑器（22k+ stars），内置拖拽、连线、缩放/平移、小地图。Zustand 轻量（~1KB），无 boilerplate，适合管理画布状态和 WebSocket 连接。Vite 提供亚秒级 HMR。

**备选考虑**: Vue Flow（对等能力但 TS 支持较弱）、自研 Canvas/SVG（开发成本过高）。

### D3: 后端 — FastAPI + LangGraph

```
                    ┌──────────────────┐
 HTTP Requests ────▶│  FastAPI 路由层   │
                    │  /api/workflows   │
                    │  /api/tasks       │
                    │  /ws/tasks/{id}   │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌────────────┐ ┌────────────┐ ┌────────────┐
     │Workflow    │ │Task        │ │WebSocket   │
     │Service     │ │Scheduler   │ │Manager     │
     │(CRUD)      │ │(状态机)     │ │(Redis Pub) │
     └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
           │              │              │
           │    ┌─────────▼──────────┐   │
           │    │  GraphCompiler     │   │
           │    │  JSON → StateGraph │   │
           │    └─────────┬──────────┘   │
           │              │              │
           │    ┌─────────▼──────────┐   │
           │    │  LangGraph Engine  │   │
           │    │  · checkpointer    │   │
           │    │  · interrupt       │   │
           │    │  · MCP client      │───┼──▶ MCP Servers
           │    └────────────────────┘   │
           │              │              │
           ▼              ▼              ▼
     ┌────────────────────────────────────┐
     │          PostgreSQL                │
     └────────────────────────────────────┘
```

**选择理由**: FastAPI 原生支持 WebSocket 和自动 OpenAPI 文档，异步性能优秀，适合 Python 为主的 AI 生态。LangGraph 提供内置的 StateGraph、checkpointer 和 interrupt 机制，刚好对应 FlowCraft 的核心需求。

**备选考虑**: Flask（缺少原生 WebSocket 和自动文档）、Temporal/Prefect（工作流引擎，但与 LLM Agent 集成不如 LangGraph 自然）。

### D4: 数据模型

```
┌──────────────────────────────────────────────────────────────┐
│                    workflow_definitions                       │
├──────────────────────────────────────────────────────────────┤
│ id: UUID (PK)        │ name: str          │ version: int     │
│ description: str     │ definition: JSONB  │ created_at: ts   │
│ updated_at: ts       │ [EXTENSIBLE] source: str (local/mkt)  │
└──────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────┐
│                      task_instances                           │
├──────────────────────────────────────────────────────────────┤
│ id: UUID (PK)        │ workflow_id: FK    │ status: enum     │
│ (pending/running/waiting_human/completed/failed)             │
│ current_state_snapshot: JSONB  │ created_by: str             │
│ trigger_type: enum (manual/scheduled/webhook) [EXTENSIBLE]   │
│ created_at: ts       │ started_at: ts     │ completed_at: ts│
└──────────────────────────────────────────────────────────────┘
          │                           │
          ▼                           ▼
┌──────────────────────┐  ┌──────────────────────────┐
│   node_executions    │  │    human_decisions        │
├──────────────────────┤  ├──────────────────────────┤
│ id: UUID (PK)        │  │ id: UUID (PK)             │
│ task_id: FK          │  │ task_id: FK               │
│ node_id: str         │  │ node_id: str              │
│ node_type: str       │  │ decision: enum            │
│ input: JSONB         │  │ feedback: text            │
│ output: JSONB        │  │ decided_at: ts            │
│ status: enum         │  │ decided_by: str           │
│ started_at: ts       │  └──────────────────────────┘
│ completed_at: ts     │
│ duration_ms: int     │
└──────────────────────┘
```

**Redis 键空间**:
- `ws:task:{task_id}` — Pub/Sub 频道，推送节点级事件
- `task:queue` — 任务队列（Phase 2 用于异步调度）

**AgentState (LangGraph 内存结构)**:
```python
class AgentState(TypedDict):
    messages: List[BaseMessage]     # LangChain 对话历史
    plan: dict                      # Planner 输出
    current_step: int               # 当前执行步
    exec_output: str                # Executor 输出
    review_decision: str            # "approved" | "rejected"
    human_input: str                # 人工输入
    retry_count: int                # 当前重试次数
    max_retries: int                # 上限（从 edge 配置读取）
```

### D5: GraphCompiler 编译流程

```
  Workflow JSON
       │
       ▼
  GraphCompiler.compile(json)
       │
       ├─── parse_nodes()
       │    │  "planner"    → AgentNodeFactory.create("planner", llm_config)
       │    │  "executor"   → AgentNodeFactory.create("executor", tools, llm_config)
       │    │  "reviewer"   → AgentNodeFactory.create("reviewer", human_confirm)
       │    │  "tool"       → ToolNodeFactory.create(tool_name)
       │    └  builder.add_node(id, node_fn)
       │
       ├─── parse_edges()
       │    │  condition == null  → builder.add_edge(src, tgt)
       │    │  condition != null  → compile_condition(edge)
       │    │     │  simple mode  → make_comparison_func(field, op, value)
       │    │     │  advanced     → RestrictedPython sandbox
       │    │     └  builder.add_conditional_edges(src, cond_fn, routing_map)
       │    │
       │    └─── detect_retry_loop()
       │         │  review → exec 回边 ↦ 注入 retry_count guard
       │         └  retry_cond = wrap_with_max_retries(cond_fn, max_retries)
       │
       └─── builder.compile(checkpointer=PostgresSaver)
            │
            ▼
        可执行图 (CompiledStateGraph)
```

**关键设计决策**:
- `AgentNodeFactory` 采用工厂模式，未来新增节点类型只需注册新 Factory
- 条件编译分离 "简单模式"和"高级模式"，高级模式通过 RestrictedPython 沙箱保证安全
- retry loop 检测在编译期完成：遍历 edges 发现 source=reviewer + target=executor 的边自动注入 retry_count 防护

### D6: 安全模型

```
┌─────────────────────────────────────────────────────────────┐
│  安全层                                                      │
│                                                             │
│  传输层      │  API Key (X-API-Key header)                  │
│             │  预留: OAuth2 Bearer Token [EXTENSIBLE]      │
│                                                             │
│  执行层      │  RestrictedPython 沙箱（条件 lambda）        │
│             │  Docker 隔离（代码执行工具）                  │
│             │  max_retries 防护（无限循环）                 │
│                                                             │
│  数据层      │  PostgreSQL 连接池 + SSL                    │
│             │  Redis 密码认证                              │
│             │  .env 管理敏感配置（不入 Git）               │
└─────────────────────────────────────────────────────────────┘
```

- Phase 1 认证：单 API Key，启动时从 `.env` 读取，所有请求需携带 `X-API-Key` Header
- `created_by` 字段预留多用户扩展空间
- 条件 lambda 执行：RestrictedPython + 5 秒超时 + 内存限制
- 代码执行工具：独立 Docker 容器，网络隔离，文件系统只读挂载

### D7: API 设计

```
REST Endpoints:
  POST   /api/workflows              # 创建工作流模板
  GET    /api/workflows              # 列表
  GET    /api/workflows/{id}         # 详情
  PUT    /api/workflows/{id}         # 更新（版本自增）
  DELETE /api/workflows/{id}         # 删除

  POST   /api/tasks                  # 创建并启动任务实例
  GET    /api/tasks                  # 任务列表
  GET    /api/tasks/{id}             # 任务详情 + 状态
  POST   /api/tasks/{id}/human-decision  # 提交人工决策
  GET    /api/tasks/{id}/audit       # 审计日志

WebSocket:
  WS  /ws/tasks/{task_id}            # 订阅任务事件流
      Events: node_start, node_complete, node_error,
              review_pending, task_complete, task_failed

OpenAPI Docs:
  GET  /docs                         # Swagger UI
  GET  /redoc                        # ReDoc
```

### D8: WebSocket 事件协议

```json
// 引擎 → 前端事件
{
  "event": "node_start",
  "task_id": "uuid",
  "node_id": "plan",
  "node_type": "planner",
  "timestamp": "2025-01-01T00:00:00Z"
}

{
  "event": "node_complete",
  "task_id": "uuid",
  "node_id": "plan",
  "node_type": "planner",
  "duration_ms": 1234,
  "timestamp": "2025-01-01T00:00:01Z"
}

{
  "event": "review_pending",
  "task_id": "uuid",
  "node_id": "review",
  "context": {
    "exec_output": "...",
    "original_input": "..."
  },
  "timestamp": "2025-01-01T00:00:02Z"
}
```

## Risks / Trade-offs

| 风险 | 缓解措施 |
|---|---|
| LangGraph 版本不稳定 API 变更 | 锁定版本号，CI 中设置版本矩阵测试 |
| RestrictedPython 沙箱绕过 | 最小化内置函数白名单，添加安全审计 CI |
| MCP 协议早期，SDK 不成熟 | Phase 1 使用稳定子集（tools/list + tools/call），预留升级路径 |
| 前端画布性能（大规模节点） | React Flow 内置虚拟化，设置节点数 > 100 时的性能预警 |
| PostgreSQL checkpoint 序列化开销 | 仅保存 AgentState 而非完整图状态，使用 JSONB 列 |
| 单 API Key 安全风险 | `.env` 不提交，README 明确警告，Phase 2 升级为 OAuth2 |

## Extension Points

以下扩展点在 Phase 1 中以接口/字段预留形式存在，不实现功能：

| 扩展点 | 预留方式 | 目标 Phase |
|---|---|---|
| 自定义节点类型 | `AgentNodeFactory` 注册接口 | Phase 2 |
| 自定义 MCP 服务器 | 配置驱动 + 模板文档 | Phase 2 |
| 多 LLM 供应商 | `model` 字段 + 供应商注册表 | Phase 2 |
| OAuth2 多用户 | `created_by` + `decided_by` 字段 | Phase 3 |
| 定时/Webhook 触发 | `trigger_type` 枚举字段 | Phase 3 |
| K8s 云原生部署 | docker-compose 与 Helm Chart 命名一致 | Phase 3 |
| Prometheus 指标 | 指标收集 hook 接口 | Phase 4 |
| 社区工具市场 | `source` 字段 + registry API | Phase 4 |
| 任意节点人工挂起 | interrupt 通用化接口 | Phase 3 |

## Open Questions

1. **[TENTATIVE] LLM 配置粒度**: 当前决定全局 key + 全局模型 + 多供应商接口预留，Agent 节点 `model` 字段可选覆盖。此决策标记为暂定，后续可能调整。
2. **前端画布撤销/重做**: agent.md 未提及。Phase 1 是否包含？建议最小化实现（操作栈 + Ctrl+Z/Y）。
3. **工作流导入导出版本兼容**: 不同版本的工作流 JSON 之间的向前/向后兼容策略需定义。
4. **WebSocket 重连机制**: 前端断线后的事件回溯（是否从最后 checkpoint 推送漏掉的事件？）。
