# Spec: Workflow Orchestration

可视化工作流编排能力，提供拖拽式画布供用户定义 LLM Agent 管道。

## ADDED Requirements

### Requirement: Canvas with five node types

系统 SHALL 提供 React Flow 画布，支持五种节点类型：Planner（规划）、Executor（执行）、Reviewer（审核）、Tool（工具调用）和 Conditional Edge（条件边）。用户 SHALL 能从左侧面板拖入节点到画布，并通过连线建立节点间的执行顺序。

#### Scenario: User builds a linear workflow
- **WHEN** 用户依次拖入 Planner → Executor → Reviewer 节点并用连线连接
- **THEN** 画布显示三个节点的线性链，前端状态包含对应的 nodes 和 edges 数据结构

#### Scenario: User adds a tool node
- **WHEN** 用户拖入 Tool 节点并选择绑定 "search" 工具
- **THEN** 节点显示工具名称标签，properties 面板展示可用参数配置项

### Requirement: Node properties configuration

每种节点类型 SHALL 提供独立的属性配置面板。Executor 和 Reviewer 节点 SHALL 支持绑定工具列表（tools 字段）。Reviewer 节点 SHALL 支持人工确认开关（human_confirm 字段）。Tool 节点 SHALL 支持绑定具体工具名称（tool_name 字段）。

#### Scenario: Configure executor tools
- **WHEN** 用户点击 Executor 节点打开属性面板并勾选 ["search", "code_exec"] 工具
- **THEN** 节点数据中 tools 字段更新为 ["search", "code_exec"]，并同步到画布 JSON 状态

#### Scenario: Enable human confirmation on reviewer
- **WHEN** 用户打开 Reviewer 节点属性面板并开启 "需要人工确认" 开关
- **THEN** 节点数据中 human_confirm 字段设置为 true，节点在画布上显示人形图标标记

### Requirement: Conditional edge configuration

用户 SHALL 能在连线之间插入条件判断。条件边 SHALL 支持简单比较模式（field/op/value）和高级表达式模式（Python lambda）。配置内容 SHALL 实时可视化预览在边上。

#### Scenario: Add condition edge
- **WHEN** 用户在 Reviewer → Executor 连线上插入条件 {"field": "approved", "op": "==", "value": false}
- **THEN** 连线变为虚线样式并显示条件标签 "approved == false"

#### Scenario: [TENTATIVE] Advanced expression mode
- **WHEN** 用户切换到高级模式并输入 `lambda state: state["score"] > 0.5`
- **THEN** 表达式被存储为 condition.expression 字段，前端显示截断后的表达式预览

### Requirement: Workflow JSON serialization

画布状态 SHALL 可序列化为标准 JSON 格式。序列化结果 SHALL 包含 nodes 和 edges 两个顶层数组。JSON SHALL 可通过 REST API 保存为工作流定义。

#### Scenario: Export workflow to JSON
- **WHEN** 用户点击"导出"按钮
- **THEN** 系统生成包含完整 nodes 和 edges 数组的 JSON 文件并触发下载

#### Scenario: Import workflow from JSON
- **WHEN** 用户选择导入一个有效的工作流 JSON 文件
- **THEN** 画布重建所有节点和连线，恢复编辑状态

### Requirement: Workflow template CRUD

系统 SHALL 提供工作流模板的创建、读取、更新和删除（CRUD）操作。每个模板 SHALL 包含名称、描述、版本号和 JSON 定义。

#### Scenario: Save workflow template
- **WHEN** 用户编辑完画布后点击保存
- **THEN** 系统将画布 JSON 及元数据持久化到 workflow_definitions 表，返回模板 ID

#### Scenario: Load workflow template
- **WHEN** 用户从模板列表选择一个已保存的工作流
- **THEN** 画布加载对应 JSON 定义并渲染所有节点和连线

### Requirement: Version management

工作流模板 SHALL 支持版本号跟踪。每次保存 SHALL 递增修订号。[EXTENSIBLE] 未来可扩展为完整版本历史与 diff 对比。

#### Scenario: Version increment on save
- **WHEN** 用户保存已存在的工作流模板
- **THEN** 版本号自增，旧版本数据保留用于审计

### Requirement: [EXTENSIBLE] Custom node type plugin

节点类型系统 SHALL 预留扩展接口，允许未来注册自定义节点类型而不修改画布核心代码。

#### Scenario: Plugin registration hook
- **WHEN** 第三方插件注册了新的节点类型 "translator"
- **THEN** 该类型出现在节点面板中，且可像内置类型一样拖拽和配置
