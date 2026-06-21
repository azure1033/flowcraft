基于 **“LangGraph 单框架 + 顺序链为主 + 极简人工介入 + 开源”** 这个组合，重新梳理了优化后的系统架构，确保它既强健又容易落地。

---

## 一、调整后的总体架构（分层仍然清晰）

和上一版保持一致的分层，但每层内部做了简化或强化：

```text
┌─────────────────────────────────────────────┐
│                  前端 (Frontend)              │
│  - 工作流编辑器（线性链 + 条件分支）        │
│  - 任务仪表盘（状态、节点日志）             │
│  - 人工决策弹窗（暂停/继续/修改）           │
│  - 审计日志/历史查询                        │
└──────────────────┬──────────────────────────┘
                   │ HTTP + WebSocket
┌──────────────────▼──────────────────────────┐
│               API 网关 & 控制层              │
│  - REST 接口（CRUD 工作流、任务）            │
│  - WebSocket 推送（节点级执行事件）          │
│  - 人工决策 API（提交决策结果）              │
└──┬──────────────────┬───────────────────────┘
   │                  │
┌──▼──────────┐  ┌───▼─────────────────────────┐
│ 工作流管理   │  │  任务调度 & 状态机          │
│ - 模板存储   │  │  - 创建任务实例              │
│ - 版本控制   │  │  - 状态转移：pending →      │
│ - 校验/编译  │  │    running → waiting_human  │
│  前端 JSON   │  │    → completed/failed       │
└──┬──────────┘  └───┬─────────────────────────┘
   │                  │
   │  ┌───────────────▼───────────────────────┐
   │  │        LangGraph 执行引擎             │
   │  │  - 图编译器（顺序链→StateGraph）      │
   │  │  - 状态持久化（PostgreSQL/检查点）    │
   │  │  - 内嵌 MCP 工具客户端                │
   │  │  - 人工介入节点处理器                 │
   │  └───────────────┬───────────────────────┘
   │                  │ MCP 协议
   │  ┌───────────────▼───────────────────────┐
   │  │         MCP 工具服务器群              │
   │  │  - 搜索工具 (Tavily/SerpAPI)          │
   │  │  - 代码执行沙箱 (Docker 隔离)         │
   │  │  - HTTP API 调用工具                  │
   └──┤  - (可扩展插件)                       │
      └───────────────────────────────────────┘
                 ┌────────────┐
                 │ 数据 & 基础│
                 │ PostgreSQL │
                 │ Redis      │
                 │ Docker     │
                 └────────────┘
```

**核心思路**：所有动态多 Agent 协作都被编译为一张 LangGraph 图，图中的节点就是你的“规划、执行、审核、工具调用”，边则根据画布拖拽生成。

---

## 二、关键模块细化（适配你的新约束）

### 1. 可视化工作流编排：顺序链 + 条件边
编辑器的核心是 **线性链**，用户从左侧拖入节点到画布，并依次连接。节点类型有限：
- **规划 Agent**：负责任务分解，会输出 `plan` 状态字段。
- **执行 Agent**：执行具体步骤，可调用工具。
- **审核 Agent**：检查执行结果，输出 `approved` / `rejected`。
- **工具节点**：直接绑定某个 MCP 工具（如“搜索”、“代码执行”），可配置参数。
- **条件边**：在节点之间可以插入一个条件判断（仅支持简单的 `if/else` 基于状态字段值，例如 `if plan.step_count > 5`），拖拽时可配置字段和比较规则。

**高级模式**：当条件逻辑比较复杂时，用户可以在节点属性中直接写入一段 **Python 表达式或短函数**（例如 `lambda state: "next" if state["score"] > 0.5 else "retry"`），这段代码会被安全沙箱执行并决定路由。这保留了灵活性，无需让画布过于复杂。

画布最终保存为一份 JSON，例如：
```json
{
  "nodes": [
    {"id": "plan", "type": "planner"},
    {"id": "exec", "type": "executor", "tools": ["search", "code_exec"]},
    {"id": "review", "type": "reviewer", "human_confirm": true},
    {"id": "tool_1", "type": "tool", "tool_name": "search"}
  ],
  "edges": [
    {"source": "plan", "target": "exec"},
    {"source": "exec", "target": "review", "condition": null},
    {"source": "review", "target": "exec", "condition": {"field": "approved", "op": "==", "value": false}},
    {"source": "review", "target": "__end__", "condition": {"field": "approved", "op": "==", "value": true}}
  ]
}
```

### 2. LangGraph 图编译：从 JSON 到 StateGraph
这是整个引擎最核心的部分。我们写一个 `GraphCompiler`，它遍历 JSON 定义，动态构建 `StateGraph`。

**定义共享状态**（TypedDict）：
```python
class AgentState(TypedDict):
    messages: List[BaseMessage]       # 对话历史
    plan: dict                        # 规划Agent输出的步骤
    current_step: int                 # 当前执行步
    exec_output: str                  # 执行Agent结果
    review_decision: str              # approved / rejected
    human_input: str                  # 人工决策时用户输入
    # 通用数据槽，供条件边读取
```

**构建图的伪代码**：
```python
from langgraph.graph import StateGraph, END

builder = StateGraph(AgentState)
for node in nodes:
    if node.type == "planner":
        builder.add_node(node.id, planner_agent)
    elif node.type == "executor":
        builder.add_node(node.id, executor_agent)
    elif node.type == "reviewer":
        builder.add_node(node.id, review_agent)
    elif node.type == "tool":
        # 工具节点实际被包裹成 Agent 可调用的工具，或者作为普通节点暴露
        builder.add_node(node.id, tool_executor(node.tool_name))
    
# 设置入口点（第一个节点）
builder.set_entry_point(nodes[0].id)

# 添加边，包括条件边
for edge in edges:
    if edge.condition:
        # 如果条件使用了简单表达式，编译成条件函数
        def make_cond(field, op, value):
            def cond_func(state):
                actual = state.get(field)
                if op == "==": return "true" if actual == value else "false"
                # 其他操作符...
            return cond_func
        cond = make_cond(edge.condition["field"], edge.condition["op"], edge.condition["value"])
        builder.add_conditional_edges(edge.source, cond, {"true": edge.target, "false": default_target})
    else:
        builder.add_edge(edge.source, edge.target)

graph = builder.compile(checkpointer=postgres_checkpointer)
```

这样，你在画布上画的任何顺序链和简单条件分支，都能直接被编译为可执行的图，且状态被持久化到 PostgreSQL，支持中断恢复。

### 3. 极简人工介入节点（模拟实现）
审核 Agent 配置中有一个开关 `human_confirm`，当开启时：
- 审核 Agent 运行后，不立即输出最终决策，而是将状态置为 `review_pending`，并通过 WebSocket 向前端推送事件：**“审核节点需要人工确认，当前执行结果：xxx”**。
- 任务状态变为 `waiting_human`，图执行挂起（LangGraph 的 `interrupt` 机制）。
- 前端显示一个弹窗，展示审核所需的上下文（执行输出、原始输入），并提供两个按钮：**“通过”** / **“拒绝”**，还可附加一条文本意见。
- 用户选择后，前端调用 API：`POST /tasks/{task_id}/human-decision`，携带 `{"decision": "approved", "feedback": "..."}`。
- 引擎收到后，将用户的决策和反馈注入状态（例如设置 `review_decision = "approved"`， `human_input = feedback`），然后**从断点恢复图执行**，条件边根据 `review_decision` 决定下一步。

**模拟模式**：如果不想涉及真实的人工交互，我们可以在审核 Agent 内部内置一个“自动模拟决策”逻辑（例如随机通过/拒绝），这样系统也能跑通全流程，用于演示和测试。

### 4. 工具调用：MCP 客户端集成
LangGraph 的 Agent 节点内部使用 LangChain 的 Tool 抽象，但这些 Tool 我们全部封装为 MCP 客户端调用：
- 引擎启动时，根据配置文件连接多个 MCP 服务器（可用 Docker 容器提供）。
- 每个 MCP 服务器向引擎注册自己的工具列表（如 `search`, `execute_python`, `http_request`）。
- 规划或执行 Agent 在 prompt 中会看到这些工具的描述，并决定调用哪个。

这样，你新增一个工具只需启动一个新的 MCP 服务器容器，并在引擎配置中添加连接信息即可，完全解耦。

### 5. 数据与状态机（PostgreSQL + Redis）
为了追踪和审计，核心表结构保持不变，但增加对人工决策的支持：

- `workflow_definitions`: 存储画布 JSON 和元数据。
- `task_instances`: 新增 `status` 取值：`waiting_human`。包含 `current_state_snapshot` 字段，存储 LangGraph 检查点状态，便于恢复。
- `node_executions`: 记录每个节点的输入、输出和耗时，审计日志的核心来源。
- `human_decisions`: 记录人工介入的具体决策（task_id, node_id, decision, feedback, timestamp）。

**Redis** 用于：
- 任务队列（可选，初期可直接用同步或后台任务）。
- WebSocket 事件广播（频道：`task:{task_id}`，推送节点开始/结束/等待人工等事件）。

---

## 三、开源项目的工程化考虑
要让项目对社区友好、容易上手，以下实践很重要：

1. **一键部署**：提供 `docker-compose.yml` 启动所有服务：API、引擎、PostgreSQL、Redis、MCP 工具容器（搜索、代码沙箱等）。前端静态文件由 API 服务托管或独立 Nginx 容器。
2. **清晰的配置**：所有 MCP 服务器连接信息、API 密钥等通过 `.env` 文件配置，附带 `.env.example`。
3. **CLI 工具**：一个简单的 `agent-flow` CLI 可用于初始化项目、启动开发服务器、执行工作流模板测试等。
4. **详细的 API 文档**：使用 FastAPI 自动生成 OpenAPI 文档，并额外提供工作流 JSON 格式规范、MCP 工具开发指南。
5. **示例工作流库**：提供几个开箱即用的模板（如“每日 AI 新闻简报”、“代码审查助手”），用户导入即可运行。
6. **测试**：单元测试 + 集成测试（用模拟的 MCP 服务器和人工决策端点），保证核心编译和执行逻辑稳定。

---

## 四、当前架构的强弱与进阶方向

**强项**：
- 架构贴合你现在的约束，用 LangGraph 把可视化编排和执行一体化，没有过度设计。
- MCP 让工具生态可扩展，且完全与框架解耦。
- 极简人工介入既满足了企业级需求，又不增加过多开发复杂度。
- 所有状态可持久化、可审计，适合展示复杂系统设计能力。

**未来可扩展点（不必现在做，但设计已预留）**：
- 支持并行节点（如多个执行 Agent 同时工作），只需在编辑器增加“并行网关”并在编译时使用 `Send` API。
- 更复杂的条件编辑器（可视化表达式构建器）。
- 人工干预的升级：支持在任意节点插入“挂起点”，并允许在恢复时修改状态。
- 多用户协作编辑工作流。

---

## 五、下面我们可以深入的部分
我们已经把整体架子搭清楚了，接下来你可以选择最感兴趣或认为最难的一块，咱们深入设计实现细节，例如：

1. **LangGraph 编译器的完整实现（如何处理工具绑定、状态字段映射）**
2. **MCP 客户端在 LangGraph 中的具体集成代码示例**
3. **前端编辑器的画布数据模型设计（节点、边、条件的数据结构）**
4. **人工介入节点的状态机与 API 交互流程（包括断点恢复）**
