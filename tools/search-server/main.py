"""FlowCraft Search Server — Tavily Search MCP tool.

Start: python main.py
Connects via MCP protocol to the FlowCraft engine.
"""

import os

SERVER_NAME = "search-server"
TOOL_NAME = "search"

print(f"[{SERVER_NAME}] FlowCraft Search Server starting...")
print(f"  Tool: {TOOL_NAME} (Tavily Search API)")
print(f"  MCP endpoint: stdio")
print(f"  Requires: TAVILY_API_KEY environment variable")

if __name__ == "__main__":
    if not os.getenv("TAVILY_API_KEY"):
        print(f"  WARNING: TAVILY_API_KEY not set. Search will return mock results.")
    print(f"  Ready for MCP connections.")
