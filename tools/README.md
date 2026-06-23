# FlowCraft MCP Tool Servers

This directory contains independent MCP (Model Context Protocol) tool servers.
Each server runs as a separate Docker container and communicates with the
FlowCraft engine via the MCP protocol.

## Available Tool Servers

| Server | Directory | Tool Name | Description |
|--------|-----------|-----------|-------------|
| Search | `search-server/` | `search` | Web search via Tavily API |
| Code Sandbox | `code-sandbox/` | `execute_python` | Isolated Python code execution |
| HTTP Client | `http-client/` | `http_request` | HTTP request tool |

## Quick Start

```bash
# Build a specific tool server
docker build -t flowcraft-search tools/search-server

# Run a tool server
docker run --rm flowcraft-search
```

## Creating a Custom Tool Server

1. Create a new directory under `tools/`
2. Add a `main.py` that implements the MCP stdio protocol
3. Add a `Dockerfile` (FROM python:3.12-slim)
4. Register the tool in the engine's MCP client configuration

```python
# Minimal MCP tool server template
# tools/my-tool/main.py
from mcp.server import Server, stdio_server

server = Server("my-tool")

@server.tool()
async def my_function(query: str) -> str:
    return f"Result for: {query}"

if __name__ == "__main__":
    stdio_server.run(server)
```

## Environment Variables

Each tool server may require its own API keys:

- **search-server**: `TAVILY_API_KEY`
- **code-sandbox**: (no external keys required)
- **http-client**: (no external keys required)

Set these in your `.env` file and they'll be passed to containers via `docker-compose.yml`.
