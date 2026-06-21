# Spec: Platform Operations

CLI 工具与一键部署能力，降低上手和运维门槛。

## ADDED Requirements

### Requirement: agent-flow CLI initialization

系统 SHALL 提供 `agent-flow` 命令行工具。`agent-flow init` 命令 SHALL 在当前目录创建项目脚手架（`.env.example`、`docker-compose.yml`、基础目录结构）。

#### Scenario: Initialize new project
- **WHEN** 用户运行 `agent-flow init`
- **THEN** 当前目录生成 `.env.example`、`docker-compose.yml`、`examples/` 和 `schemas/` 目录

### Requirement: Development server startup

`agent-flow dev` 命令 SHALL 启动开发环境。前端开发服务器 SHALL 运行在 `localhost:5173`，后端 API 服务器 SHALL 运行在 `localhost:8000`。命令 SHALL 自动检查依赖（Node.js、Python、Docker）并提示缺失项。

#### Scenario: Start dev environment
- **WHEN** 用户运行 `agent-flow dev`
- **THEN** 前端 Vite 开发服务器、FastAPI 后端和 PostgreSQL 容器同时启动，终端输出各服务访问地址

#### Scenario: Missing Docker
- **WHEN** 用户运行 `agent-flow dev` 但 Docker 未安装
- **THEN** CLI 输出 "Docker is required. Please install Docker Desktop: https://docker.com" 并退出

### Requirement: Workflow test execution

`agent-flow test <workflow.json>` 命令 SHALL 加载指定的工作流 JSON 文件并在模拟模式下执行。执行结果 SHALL 输出到终端，包含每个节点的执行状态和耗时。模拟模式下 SHALL 自动处理人工决策节点。

#### Scenario: Test a workflow
- **WHEN** 用户运行 `agent-flow test examples/news-briefing.json`
- **THEN** 引擎编译并执行该工作流，终端打印每个节点的 ✓/✗ 状态和总耗时

### Requirement: Docker Compose one-click deployment

`docker-compose.yml` SHALL 编排以下服务：API 服务器、LangGraph 引擎、PostgreSQL、Redis、MCP 搜索服务器、MCP 代码沙箱服务器、Nginx（前端静态文件）。`.env.example` SHALL 包含所有可配置的环境变量（LLM API Key、数据库连接、MCP 服务器配置等）。

#### Scenario: Full stack startup
- **WHEN** 用户配置 `.env` 后运行 `docker compose up`
- **THEN** 所有 6 个服务容器启动，前端可通过 `http://localhost` 访问，API 文档可通过 `http://localhost:8000/docs` 访问

#### Scenario: Missing .env configuration
- **WHEN** 用户运行 `docker compose up` 但 `.env` 未配置必需的 API Key
- **THEN** 相关服务启动失败并在日志中输出明确的配置缺失提示

### Requirement: OpenAPI auto-documentation

FastAPI SHALL 自动生成 OpenAPI 文档。`/docs` 端点 SHALL 提供 Swagger UI，`/redoc` 端点 SHALL 提供 ReDoc 界面。所有 API 端点 SHALL 包含请求/响应模型和中文描述。

#### Scenario: Access API documentation
- **WHEN** 用户访问 `http://localhost:8000/docs`
- **THEN** Swagger UI 展示所有 REST 端点、WebSocket 端点和对应的请求/响应 schema

### Requirement: Example workflow templates

系统 SHALL 提供至少 2 个开箱即用的示例工作流：每日 AI 新闻简报（搜索 → 执行 → 审核）、代码审查助手（规划 → 执行 → 审核）。每个示例 SHALL 为独立 JSON 文件，存放在 `examples/` 目录。

#### Scenario: Load example workflow
- **WHEN** 用户从 UI 模板列表选择"每日 AI 新闻简报"
- **THEN** 画布加载对应 JSON 并展示 Planner → Executor(搜索) → Reviewer 的完整链路

### Requirement: [EXTENSIBLE] Kubernetes and cloud deployment

部署架构 SHALL 预留云原生扩展接口。docker-compose.yml 的配置结构 SHALL 与未来 Helm Chart 保持一致的命名约定和环境变量体系。

#### Scenario: Future K8s migration
- **WHEN** 未来需要 Kubernetes 部署
- **THEN** 可通过 Helm Chart + 相同的 `.env` 变量体系实现无缝迁移，无需修改应用代码
