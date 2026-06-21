# Spec: Human-in-the-Loop

通过 LangGraph interrupt 机制实现的人工审核介入流程。

## ADDED Requirements

### Requirement: Reviewer node interrupt

当 Reviewer 节点的 human_confirm 字段为 true 时，系统 SHALL 在审核 Agent 执行后不立即输出最终决策。系统 SHALL 将任务状态置为 waiting_human 并通过 LangGraph interrupt 挂起图执行。检查点状态 SHALL 持久化到 PostgreSQL。

#### Scenario: Interrupt on human_confirm=true
- **WHEN** Reviewer 节点 human_confirm=true 且审核 Agent 完成执行
- **THEN** 图执行调用 interrupt()，任务状态变为 waiting_human，检查点保存到 PostgreSQL

#### Scenario: No interrupt on human_confirm=false
- **WHEN** Reviewer 节点 human_confirm=false
- **THEN** 审核 Agent 完成执行后图自动继续，状态正常流转

### Requirement: Decision notification via WebSocket

当任务进入 waiting_human 状态时，系统 SHALL 通过 WebSocket 向前端推送审核通知。通知 SHALL 包含：task_id、node_id、审核上下文（执行输出、原始输入）、待审核内容摘要。

#### Scenario: Push review notification
- **WHEN** 任务进入 waiting_human 状态
- **THEN** WebSocket 频道 `task:{task_id}` 推送包含审核上下文的 "review_pending" 事件

#### Scenario: Frontend displays review dialog
- **WHEN** 前端收到 "review_pending" 事件
- **THEN** 前端显示审核弹窗，包含执行输出预览、"通过"/"拒绝"按钮及可选反馈文本框

### Requirement: Human decision submission

系统 SHALL 提供 `POST /api/tasks/{task_id}/human-decision` API 接收人工决策。请求体 SHALL 包含 decision（approved/rejected）和可选的 feedback 文本。决策 SHALL 记录到 human_decisions 表。

#### Scenario: Approve with feedback
- **WHEN** 用户点击"通过"并输入反馈文本后提交
- **THEN** API 接收 {"decision": "approved", "feedback": "结果正确，可以继续"}，human_decisions 表新增记录

#### Scenario: Reject decision
- **WHEN** 用户点击"拒绝"提交
- **THEN** API 接收 {"decision": "rejected"}，human_decisions 表新增记录，引擎收到决策后通过条件边路由到重试路径

### Requirement: State injection and resume

收到人工决策后，系统 SHALL 将 decision 和 feedback 注入 AgentState（review_decision 字段和 human_input 字段）。系统 SHALL 从 LangGraph checkpoint 恢复图执行，条件边根据 review_decision 决定下一步路由。

#### Scenario: Resume after approval
- **WHEN** 人工决策为 approved 且引擎从 checkpoint 恢复
- **THEN** state["review_decision"] = "approved"，条件边路由到 `__end__` 或下一个节点

#### Scenario: Resume after rejection
- **WHEN** 人工决策为 rejected 且引擎从 checkpoint 恢复
- **THEN** state["review_decision"] = "rejected"，retry_count 自增，条件边路由回 Executor 节点重试

### Requirement: Simulated review mode

系统 SHALL 支持模拟审核模式。当全局配置 ENABLE_SIMULATED_REVIEW=true 时，human_confirm=true 的节点 SHALL 自动生成随机决策（50% approved / 50% rejected），不等待实际人工输入。

#### Scenario: Auto-decision in simulated mode
- **WHEN** human_confirm=true 且 ENABLE_SIMULATED_REVIEW=true
- **THEN** 系统自动生成 decision 并注入状态，跳过 WebSocket 通知和 API 等待，直接恢复图执行

### Requirement: [EXTENSIBLE] Arbitrary interrupt points

系统 SHALL 预留机制支持未来在任意节点类型（非仅 Reviewer）插入挂起点，并允许人工在恢复时修改任意状态字段。
