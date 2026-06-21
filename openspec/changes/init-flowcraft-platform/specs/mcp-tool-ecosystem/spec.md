# Spec: MCP Tool Ecosystem

基于 MCP（Model Context Protocol）协议的工具服务器集成生态。

## ADDED Requirements

### Requirement: MCP client connection lifecycle

引擎 SHALL 在启动时根据配置文件连接所有已声明的 MCP 工具服务器。每个 MCP 服务器 SHALL 以独立 Docker 容器运行。连接信息（名称、地址、端口）SHALL 从 `.env` 或 `mcp_servers.yaml` 配置读取。断线 SHALL 自动重连（指数退避，最多 5 次）。

#### Scenario: Startup with configured servers
- **WHEN** 引擎启动且配置了 search 和 code_sandbox 两个 MCP 服务器
- **THEN** MCP 客户端建立两个连接，各服务器注册其工具列表

#### Scenario: Server reconnection
- **WHEN** MCP 服务器容器意外重启导致连接断开
- **THEN** 客户端检测到断线后自动重连，最多尝试 5 次，每次间隔递增

### Requirement: Tool registration and discovery

每个连接的 MCP 服务器 SHALL 通过 `tools/list` 协议向引擎注册其可用工具。引擎 SHALL 将每个工具封装为 LangChain Tool 对象（name + description + args_schema）。工具列表 SHALL 在 Agent prompt 中可见，Agent 可自主决定调用哪个工具。

#### Scenario: Register tools from server
- **WHEN** search-server 返回 tools/list 结果包含 "search" 工具
- **THEN** 引擎将 "search" 注册为 LangChain Tool，Executor Agent 在 prompt 中看到其描述

#### Scenario: No tools duplicate
- **WHEN** 两个 MCP 服务器注册了同名工具
- **THEN** 系统以 server_name 为前缀区分（如 "search_server1.search" 和 "search_server2.search"）

### Requirement: Tool invocation via LangChain

当 Agent 决定调用工具时，LangChain Tool 抽象层 SHALL 将调用转换为 MCP `tools/call` 请求。请求 SHALL 包含 tool_name 和 arguments。调用结果 SHALL 返回给 Agent 作为对话上下文。

#### Scenario: Agent invokes search tool
- **WHEN** Executor Agent 决定调用 "search" 工具并传入参数 {"query": "Python LangGraph tutorial"}
- **THEN** 引擎通过 MCP 客户端向 search-server 发送 tools/call 请求，结果返回给 Agent 作为函数调用结果

#### Scenario: Tool call error handling
- **WHEN** MCP tools/call 返回错误（如超时、参数无效）
- **THEN** 错误信息格式化为 ToolMessage 返回给 Agent，Agent 可尝试修正参数后重试

### Requirement: Containerized tool servers

每个 MCP 工具服务器 SHALL 拥有独立的 Dockerfile 和源码目录。服务器 SHALL 通过 docker-compose.yml 统一编排。预设工具 SHALL 包含：搜索工具（Tavily Search API）、代码执行沙箱（Docker 隔离）、HTTP 请求工具。

#### Scenario: Search tool server
- **WHEN** Agent 调用搜索工具
- **THEN** search-server 容器接收请求，调用 Tavily API，返回搜索结果摘要

#### Scenario: Code execution sandbox
- **WHEN** Agent 调用代码执行工具传入 Python 代码
- **THEN** code-sandbox 容器在隔离的 Docker 环境中执行代码，返回 stdout/stderr 和执行时间

### Requirement: [EXTENSIBLE] Custom tool server plugin

系统 SHALL 提供工具服务器模板和开发文档，允许开发者创建自定义 MCP 工具服务器。新服务器 SHALL 只需实现 MCP 协议接口并添加一行配置即可集成到引擎。

#### Scenario: Third-party tool integration
- **WHEN** 开发者按照模板创建了 "weather" MCP 服务器并在配置中添加连接信息
- **THEN** 引擎启动时自动连接该服务器，"weather" 工具出现在可用工具列表中

### Requirement: [EXTENSIBLE] Tool marketplace

系统 SHALL 预留 `source` 字段在工具元数据中，未来可扩展到社区工具市场，支持从远程注册表安装工具服务器。
