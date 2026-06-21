# Spec: LangGraph Execution Engine

将工作流 JSON 动态编译为 LangGraph StateGraph 并执行的核心引擎。

## ADDED Requirements

### Requirement: JSON to StateGraph compilation

系统 SHALL 提供 GraphCompiler，遍历画布 JSON 定义动态构建 LangGraph StateGraph。Builder SHALL 根据节点类型映射相应的 Agent 函数（Planner → planner_agent, Executor → executor_agent, Reviewer → review_agent, Tool → tool_executor）。入口点 SHALL 设置为 nodes 数组中第一个节点。

#### Scenario: Compile linear workflow
- **WHEN** GraphCompiler 接收包含 "plan → exec → review" 三个节点的工作流 JSON
- **THEN** builder 添加三个对应节点函数，设置 entry_point 为 "plan"，添加两条直连边 plan→exec 和 exec→review

#### Scenario: Compile workflow with conditional edge
- **WHEN** GraphCompiler 接收包含条件边 {"field": "approved", "op": "==", "value": false} 的工作流 JSON
- **THEN** builder.add_conditional_edges 使用编译后的条件函数，路由映射包含 "true" 和 "false" 两条路径

### Requirement: Shared state management

系统 SHALL 定义 AgentState TypedDict 作为所有节点间的共享状态。状态字段 SHALL 包含：messages（对话历史）、plan（规划输出）、current_step（当前步数）、exec_output（执行结果）、review_decision（审核决定）、human_input（人工输入）、retry_count（重试计数）和 max_retries（最大重试次数）。状态 SHALL 通过 PostgreSQL checkpointer 持久化。

#### Scenario: State flows through nodes
- **WHEN** Planner 节点执行并将分解步骤写入 state["plan"]
- **THEN** 后续 Executor 节点可读取 state["plan"] 获取任务分解结果

#### Scenario: State persistence across restarts
- **WHEN** 引擎在任务执行中途重启
- **THEN** 系统从 PostgreSQL checkpoint 恢复 AgentState，继续执行

### Requirement: Agent node implementations

系统 SHALL 实现四种 Agent 节点。Planner Agent SHALL 输出任务分解 plan。Executor Agent SHALL 执行具体步骤并可调用注册的工具。Reviewer Agent SHALL 评估执行结果输出 approved/rejected。Tool Executor SHALL 将 MCP 工具封装为 LangChain Tool 供 Agent 调用。

#### Scenario: Planner generates task breakdown
- **WHEN** Planner Agent 接收用户输入任务
- **THEN** 输出包含步骤列表的 plan 字典写入 state["plan"]

#### Scenario: Reviewer approves execution
- **WHEN** Reviewer Agent 评估 exec_output 符合预期
- **THEN** state["review_decision"] 设置为 "approved"

### Requirement: Condition expression compilation

条件边 SHALL 支持简单比较模式（field/op/value）和高级表达式模式。简单模式 SHALL 自动编译为比较函数。高级模式 SHALL 使用 RestrictedPython 安全沙箱执行用户提供的 Python lambda，并 SHALL 设置 5 秒超时和内存限制。

#### Scenario: Compile simple condition
- **WHEN** 条件为 {"field": "review_decision", "op": "==", "value": "approved"}
- **THEN** 生成的 cond_func 在 state["review_decision"] == "approved" 时返回 "true"，否则返回 "false"

#### Scenario: Execute advanced expression safely
- **WHEN** 用户 lambda 尝试调用 `os.system("rm")`
- **THEN** RestrictedPython 沙箱阻止该调用并返回安全错误

### Requirement: Retry loop with max retries

当检测到 Reviewer → Executor 回边时，系统 SHALL 视为重试循环。每次循环 SHALL 递增 retry_count。当 retry_count >= max_retries 时，系统 SHALL 强制路由到 `__end__` 终止执行。

#### Scenario: Retry within limit
- **WHEN** Reviewer 返回 rejected 且 retry_count < max_retries
- **THEN** 引擎路由回 Executor，retry_count 自增 1，继续执行

#### Scenario: Retry exceeds limit
- **WHEN** Reviewer 连续 3 次返回 rejected 且 max_retries = 3
- **THEN** 引擎路由到 `__end__`，任务状态变为 failed，node_executions 记录终止原因

### Requirement: [TENTATIVE] LLM provider configuration

系统 SHALL 支持通过全局 `.env` 配置 LLM 连接信息。每个 Agent 节点 SHALL 可选独立覆盖模型配置（model 字段）。系统 SHALL 预留多供应商接口（OpenAI / Anthropic / 本地模型）。默认使用 LangChain ChatModel 抽象层。

#### Scenario: Global default model
- **WHEN** `.env` 中配置 `LLM_PROVIDER=openai` 和 `LLM_MODEL=gpt-4o`
- **THEN** 所有 Agent 节点默认使用该配置，除非节点数据中指定了 model 字段

#### Scenario: [TENTATIVE] Per-node model override
- **WHEN** Executor 节点 data.model 字段设置为 "claude-3-opus"
- **THEN** 该 Executor 节点使用 Anthropic 供应商而非全局默认的 OpenAI

### Requirement: [EXTENSIBLE] Custom agent nodes

系统 SHALL 预留自定义 Agent 节点注册接口，允许未来扩展新的 Agent 类型而不修改编译器和执行引擎核心代码。
