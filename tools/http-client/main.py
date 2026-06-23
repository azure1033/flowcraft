"""FlowCraft HTTP Client — HTTP request MCP tool.

Makes HTTP requests on behalf of the agent.
"""

SERVER_NAME = "http-client"
TOOL_NAME = "http_request"

print(f"[{SERVER_NAME}] FlowCraft HTTP Client starting...")
print(f"  Tool: {TOOL_NAME}")
print(f"  Methods: GET, POST, PUT, DELETE")
print(f"  Features: headers, body, timeout, redirect following")

if __name__ == "__main__":
    print(f"  Ready for MCP connections.")
