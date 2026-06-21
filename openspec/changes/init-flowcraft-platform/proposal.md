## Why

LLM 应用正从单一 ChatBot 向多 Agent 协作管道演进，但将 Agent 链路编排为可执行工作流仍依赖大量手工代码。FlowCraft 提供一套可视化编排引擎，让用户通过拖拽画布定义 Agent 管道，一键编译为 LangGraph 可执行图，填补了"可视化编排"与"生产级执行引擎"之间的空白。

## What Changes

- 新增**可视化工作流编辑器**（React Flow），支持 5 种节点类型（规划/执行/审核/工具/条件边）的拖拽式编排
- 新增 **LangGraph 图编译器**，将画布 JSON 动态编译为 StateGraph，支持条件分支与重试循环
- 新增**任务状态机**与执行引擎，支持 pending → running → waiting_human → completed/failed 全生命周期
- 新增**人工介入机制**，通过 LangGraph interrupt/resume 实现审核节点的挂起与恢复
- 新增 **MCP 工具集成**，以独立容器运行工具服务器，通过 MCP 协议与引擎解耦通信
- 新增 **WebSocket 实时推送**与审计日志系统
- 新增 **agent-flow CLI** 与 Docker Compose 一键部署

## Capabilities

### New Capabilities

- `workflow-orchestration`: 可视化工作流编辑器，5 种节点类型（Planner, Executor, Reviewer, Tool, Conditional Edge），画布 JSON 序列化/反序列化，工作流模板存储与版本管理
- `langgraph-execution-engine`: JSON→StateGraph 动态编译，PostgreSQL checkpoint 状态持久化，条件表达式路由，受控重试循环，RestrictedPython 安全沙箱
- `human-in-the-loop`: LangGraph interrupt 挂起机制，WebSocket 审核通知推送，人工决策 API（approved/rejected + 反馈），断点恢复与重试上限控制
- `mcp-tool-ecosystem`: MCP 协议客户端，独立容器化工具服务器（搜索/代码沙箱/HTTP 调用），工具注册与动态发现，可扩展工具插件架构
- `execution-observability`: WebSocket 节点级事件流，node_executions 审计日志，human_decisions 决策记录，task_instances 生命周期追踪
- `platform-operations`: agent-flow CLI（init/start/test），Docker Compose 一键部署，FastAPI 自动 OpenAPI 文档，示例工作流模板库

### Modified Capabilities

<!-- 首次创建，无现有 capabilities 需要修改 -->

## Non-goals

- 不实现并行节点执行（多 Agent 同时工作）
- 不实现多用户协作编辑
- 不实现可视化条件表达式构建器
- 不实现通用图灵完备循环（仅支持 Reviewer→Executor 受控重试）
- 不实现 Kubernetes/云原生部署（Phase 1 仅 Docker Compose）

## Impact

- **新增目录**: `apps/frontend/`, `apps/backend/`, `tools/`, `schemas/`, `cli/`, `examples/`
- **新增依赖**: React Flow, LangGraph, LangChain, FastAPI, PostgreSQL, Redis, MCP SDK
- **数据库**: 4 张新表（workflow_definitions, task_instances, node_executions, human_decisions）
- **API**: REST 接口（CRUD 工作流/任务）+ WebSocket 端点（事件推送 + 审核通知）
- **配置**: `.env` 环境变量体系 + `docker-compose.yml` + monorepo workspace 配置
