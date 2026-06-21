# Spec: Execution Observability

任务执行过程中的实时事件推送与审计日志记录。

## ADDED Requirements

### Requirement: Per-task WebSocket event channel

系统 SHALL 为每个运行中的任务实例创建独立的 WebSocket 频道（`task:{task_id}`）。前端 SHALL 通过订阅该频道接收任务执行事件。事件类型 SHALL 包含：node_start（节点开始）、node_complete（节点完成）、node_error（节点错误）、review_pending（等待审核）、task_complete（任务完成）、task_failed（任务失败）。

#### Scenario: Subscribe to task events
- **WHEN** 前端通过 WebSocket 连接到 `ws://host/ws/tasks/{task_id}`
- **THEN** 前端开始接收该任务的所有执行事件推送

#### Scenario: Node execution lifecycle events
- **WHEN** 引擎执行一个 Planner 节点
- **THEN** WebSocket 推送 `{"event": "node_start", "node_id": "plan", "timestamp": "..."}` 然后推送 `{"event": "node_complete", "node_id": "plan", "duration_ms": 1234}`

### Requirement: Audit log persistence

系统 SHALL 将每个节点的执行信息持久化到 node_executions 表。记录 SHALL 包含：task_id、node_id、node_type、input（节点输入状态快照）、output（节点输出状态快照）、started_at、completed_at、duration_ms、status（success/error/interrupted）。

#### Scenario: Record successful execution
- **WHEN** Executor 节点执行成功
- **THEN** node_executions 表插入一条 status=success 的记录，包含完整输入输出和耗时

#### Scenario: Record error execution
- **WHEN** Executor 节点执行过程中抛出异常
- **THEN** node_executions 表插入一条 status=error 的记录，output 字段包含错误堆栈

### Requirement: Human decision audit trail

系统 SHALL 将所有人工决策记录到 human_decisions 表。记录 SHALL 包含：task_id、node_id、decision（approved/rejected）、feedback、decided_at、decided_by（用户标识）。

#### Scenario: Log approval decision
- **WHEN** 用户对审核节点做出 approved 决策
- **THEN** human_decisions 表新增记录，包含决策结果、反馈文本和时间戳

### Requirement: Task state snapshot

task_instances 表 SHALL 包含 current_state_snapshot 字段，存储 LangGraph checkpoint 的序列化状态。该快照 SHALL 在每次 checkpoint 保存时更新，用于任务中断恢复和事后审计。

#### Scenario: State snapshot for recovery
- **WHEN** 任务在 waiting_human 状态挂起
- **THEN** current_state_snapshot 包含完整的 AgentState 序列化数据，引擎可直接从快照恢复

### Requirement: Task lifecycle tracking

task_instances 表 SHALL 追踪任务全生命周期。状态 SHALL 支持：pending → running → waiting_human → completed/failed。每条记录 SHALL 包含 created_at、started_at、completed_at 和 status 字段。

#### Scenario: Full lifecycle trace
- **WHEN** 查询 task_id=abc 的审计日志
- **THEN** 返回包含 workflow_definition 信息、所有 node_executions 记录（按时间排序）、所有 human_decisions 记录和任务最终状态的完整报告

### Requirement: [EXTENSIBLE] Metrics and telemetry

系统 SHALL 预留指标收集接口，未来可扩展为 Prometheus metrics 导出和分布式追踪（OpenTelemetry）集成。

#### Scenario: Extension point for metrics
- **WHEN** 未来需求需要监控节点平均执行时长
- **THEN** 指标收集接口暴露 node_duration 直方图，无需修改核心执行引擎代码
