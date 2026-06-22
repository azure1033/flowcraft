# FlowCraft 项目经历

## 项目概述

**FlowCraft** — 开源可视化 LLM Agent 工作流编排平台。用户通过可视化画布拖拽设计 Agent 流水线，导出为 JSON，由 LangGraph 引擎编译执行。定位为"画出你的 Agent 流水线，点击运行"。

- **角色**：全栈独立开发者（架构设计 + 后端实现 + API 设计）
- **时间**：2025 年（正在进行）
- **技术栈**：Python 3.11 / FastAPI / LangGraph / LangChain / OpenAI / Pydantic / pytest / PostgreSQL / Redis / Docker
- **许可**：Apache 2.0 开源
- **代码仓库**：本地开发中

---

## 项目背景与目标

大语言模型（LLM）快速普及，但用代码编排多 Agent 协作流程门槛高、调试困难。FlowCraft 目标是降低 LLM Agent 工作流的开发门槛——让非程序员也能通过拖拽节点、连线的方式构建复杂的 AI 流水线，同时保留足够的灵活性供开发者扩展。

核心设计理念：
- **可视化编排**：画布拖拽 → JSON → 执行，全链路打通
- **LangGraph 单框架**：不引入过重的编排层，用 LangGraph 统一建模和运行
- **审核-重试循环**：内置 Planner→Executor→Reviewer 模式，Reviewer 不通过自动重试
- **人在回路**：关键决策点可暂停等待人工审批（LangGraph interrupt 机制）
- **MCP 工具生态**：通过 MCP 协议解耦工具集成，新增工具=新增 Docker 容器

---

## 系统架构

采用 5 层架构，前后端分离：

```
Frontend (React + React Flow)   ← 可视化画布编辑器
        ↓ HTTP + WebSocket
API Gateway (FastAPI)           ← REST 接口 + WS 推送 + 鉴权
        ↓
Task Scheduler                  ← 任务创建、状态机管理
        ↓
LangGraph Execution Engine      ← 图编译、条件路由、重试循环
        ↓ MCP Protocol
MCP Tool Servers (Docker)       ← 搜索/代码执行/HTTP 调用
                                ← 可扩展插件体系

基础设施：PostgreSQL（状态持久化）+ Redis（事件广播）
```

### 核心模块

| 模块 | 说明 | 实现状态 |
|------|------|----------|
| `GraphCompiler` | 将工作流 JSON 编译为 LangGraph StateGraph | ✅ 已实现 |
| `AgentState` | 共享状态 TypedDict，贯穿全图节点 | ✅ 已实现 |
| Planner Agent | 任务分解，输出结构化步骤 | ✅ 已实现 |
| Executor Agent | 逐步执行计划步骤 | ✅ 已实现 |
| Reviewer Agent | 评估执行结果，输出 approved/rejected | ✅ 已实现 |
| Conditional Routing | 条件边：基于状态字段的 if/else 路由 | ✅ 已实现 |
| Retry Loop | Reviewer→Executor 回边，max_retries 保护 | ✅ 已实现 |
| FastAPI REST API | 工作流 CRUD + 任务执行 + 人工决策 | ✅ 已实现 |
| API Key Auth | X-API-Key 鉴权 | ✅ 已实现 |
| In-Memory Store | 线程安全的元数据存储（workflows/tasks/audit） | ✅ 已实现 |
| Human-in-the-Loop | 人工决策 API 端点 | ✅ 已实现 |
| Workflow JSON Schema | 前后端共享的数据契约 | ✅ 已实现 |
| Frontend (React + React Flow) | 可视化画布编辑器 | 🔲 规划中 |
| MCP Tool Servers | 搜索/代码沙箱/HTTP 客户端 | 🔲 规划中 |
| PostgreSQL Persistence | 替代内存存储 | 🔲 规划中 |

---

## 技术亮点

### 1. 图编译器（GraphCompiler）— 核心引擎

将用户绘制的 JSON 工作流动态编译为 LangGraph 可执行图。支持 4 种节点类型（Planner/Executor/Reviewer/Tool）、6 种比较运算符的条件路由、以及 Reviewer→Executor 的自动重试循环。

```python
# 关键设计：条件编译 + 重试保护
# 用户 JSON 中的 {"field": "review_decision", "op": "==", "value": "rejected"}
# → 编译为 operator.eq 条件函数
# → 包裹 retry_guard 装饰器，计数超限后强制终止，防止死循环
```

- 支持 `==`, `!=`, `>`, `<`, `>=`, `<=` 六种比较运算符
- 自动检测 Reviewer→Executor 边为"重试边"，注入 max_retries 保护
- 条件路由自动解析 false 分支（配对条件边），未匹配时回退到 `__end__`
- LangGraph MemorySaver 作为 checkpointer（规划迁移至 PostgreSQL）

### 2. 状态驱动架构 + 审计溯源

AgentState 作为全图共享状态，LangGraph 自动 checkpoint 每个节点执行前后的状态快照：

- `plan`: 规划 Agent 输出的结构化步骤
- `current_step`: 当前执行进度
- `exec_output`: 执行结果
- `review_decision`: 审核决策（approved/rejected）
- `retry_count` / `max_retries`: 重试循环控制
- `human_input`: 人工决策时注入的用户反馈

4 张审计表设计：`workflow_definitions` / `task_instances`（含 JSONB 状态快照）/ `node_executions`（含耗时）/ `human_decisions`

### 3. REST API 设计

基于 FastAPI 的 RESTful API，16 个端点，涵盖完整的工作流生命周期：

| 端点 | 功能 |
|------|------|
| `POST /api/workflows` | 创建工作流模板（含节点/边验证） |
| `GET/PUT/DELETE /api/workflows/{id}` | 工作流 CRUD，版本自动递增 |
| `POST /api/tasks` | 创建并异步执行任务（后台线程+asyncio） |
| `GET /api/tasks/{id}` | 获取任务细节（含节点执行记录和人工决策） |
| `POST /api/tasks/{id}/human-decision` | 提交人工审核决定 |
| `GET /api/health` | 健康检查（返回 workflows/tasks 计数） |

- 自动生成 OpenAPI 文档（Swagger + ReDoc）
- X-API-Key 鉴权（Phase 1，预留 OAuth2 扩展点）
- CORS 已配置（支持前端开发服务器）
- 完整请求/响应 Pydantic 模型

### 4. 工程化实践

- **uv** 包管理器 + hatchling 构建系统
- **pyproject.toml** 集中配置（依赖、测试、构建）
- `.env.example` 模板（所有必需的环境变量）
- `test_api_smoke.py` 全端点冒烟测试（无需启动服务器，使用 TestClient）
- `workflow.schema.json` 作为前后端共享契约（单点真理）
- 清晰的模块边界：`compiler` / `agents` / `state` / `api` 各司其职

---

## 难点攻克

### 挑战 1：如何优雅处理 Reviewer→Executor 死循环

**问题**：用户可能设计出 Reviewer 永远 reject 的工作流，导致无限循环消耗 API 额度。

**方案**：
1. 自动检测 Reviewer→Executor 条件边为"重试边"
2. 编译时注入 `retry_guard` 装饰器，跟踪 `retry_count`
3. 当计数达到 `max_retries`（默认 3），强制路由到 `__end__`
4. `max_retries` 可通过 JSON 配置（`loop.max_retries`）

### 挑战 2：条件边的"false 分支"自动推导

**背景**：LangGraph 的条件路由需要明确的 true/false 两条路径，但用户 JSON 中可能只定义了一条条件边。

**方案**：编译器自动扫描同源节点的其他边，若找到配对的条件边则作为 false 分支，否则回退到 `END`。无需用户显式声明 else 分支。

---

## 个人贡献

- 独立完成系统架构设计（5 层架构，参考 LangGraph 官方最佳实践）
- 独立实现核心编译引擎（GraphCompiler，~180 行 Python）
- 独立实现 3 个 LLM Agent 节点（Planner/Executor/Reviewer，~170 行）
- 独立实现 FastAPI REST API（8 个文件，约 350 行业务代码）
- 独立编写完整 API 冒烟测试（覆盖所有端点，包含鉴权/CRUD/任务执行/人工决策）
- 设计前后端共享的 Workflow JSON Schema（JSON Schema Draft-7）
- 项目采用开源标准：Apache 2.0 许可、Conventional Commits、.env.example 配置模板

---

## 技术栈总览

| 层级 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.11+ | 后端核心 |
| Web 框架 | FastAPI 0.115+ | REST API + 自动文档 |
| LLM 编排 | LangGraph 0.2+ / LangChain 0.3+ | 图执行引擎 + Agent 抽象 |
| LLM 提供商 | OpenAI (ChatOpenAI) | LLM 调用 |
| 数据验证 | Pydantic 2.0+ | API Schema + 配置管理 |
| 测试 | pytest 8.0+ / pytest-asyncio | 单元测试 + 集成测试 |
| 包管理 | uv + hatchling | 依赖管理 + 构建 |
| 数据库 | PostgreSQL（规划）/ 内存存储（当前） | 状态持久化 |
| 缓存/消息 | Redis（规划） | WebSocket 事件广播 |
| 工具协议 | MCP (Model Context Protocol) | 工具服务器通信 |
| 容器化 | Docker / Docker Compose（规划） | 部署 + 工具隔离 |
| 前端 | React 18 + React Flow + Vite + Zustand（规划） | 可视化编辑器 |
| 版本控制 | Git + Conventional Commits | 版本管理 |

---

## 未来规划

- **前端画布**：React + React Flow 实现拖拽式工作流编辑器
- **MCP 工具生态**：搜索（Tavily）、代码沙箱（Docker 隔离）、HTTP 客户端
- **PostgreSQL 迁移**：替代内存存储，支持持久化和断点恢复
- **WebSocket 实时推送**：节点级执行事件流
- **CLI 工具**：`agent-flow init/dev/test` 命令
- **Docker Compose 一键部署**：降低开源用户上手门槛
- **示例工作流库**：开箱即用的模板（代码审查、新闻简报等）
- **多 LLM 提供商支持**：预留 provider registry 接口
- **OAuth2 多用户**：预留 `created_by` / `decided_by` 字段
