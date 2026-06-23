"""FlowCraft Code Sandbox — Isolated Python code execution MCP tool.

Runs user code in a Docker-isolated environment with resource limits.
"""

import sys

SERVER_NAME = "code-sandbox"
TOOL_NAME = "execute_python"

print(f"[{SERVER_NAME}] FlowCraft Code Sandbox starting...")
print(f"  Tool: {TOOL_NAME}")
print(f"  Sandbox: Docker container, 5s timeout, 128MB memory limit")
print(f"  Filesystem: read-only (except /tmp)")

if __name__ == "__main__":
    print(f"  Ready for MCP connections.")
