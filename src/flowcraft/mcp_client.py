"""MCP Tool Registry — manages tool servers and provides LangChain Tool wrappers.

In MVP mode, uses dummy/fake tool implementations for testing.
Real MCP servers will be connected via the MCP protocol in Phase 2.

Usage:
    from flowcraft.mcp_client import ToolRegistry
    registry = ToolRegistry.get_instance()
    tools = registry.get_langchain_tools()
"""

import json
from typing import Any, Callable


class ToolRegistry:
    """Singleton registry for MCP tool functions.

    Tools are callables that take a dict of arguments and return a dict result.
    Dummy implementations simulate real tool behavior for MVP testing.
    """

    _instance: "ToolRegistry | None" = None

    def __init__(self):
        self._tools: dict[str, dict] = {}  # name -> {desc, fn}
        self._register_defaults()

    @classmethod
    def get_instance(cls) -> "ToolRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def register(self, name: str, description: str, func: Callable) -> None:
        self._tools[name] = {"description": description, "function": func}

    def get_tool(self, name: str) -> dict | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict]:
        return [
            {"name": n, "description": d["description"]} for n, d in self._tools.items()
        ]

    def invoke(self, name: str, arguments: dict) -> dict:
        tool = self.get_tool(name)
        if not tool:
            return {"error": f"Tool '{name}' not found."}
        try:
            return tool["function"](arguments)
        except Exception as e:
            return {"error": str(e)}

    def get_langchain_tools(self) -> list:
        """Return tools wrapped as LangChain Tool objects for agent binding."""
        from langchain_core.tools import tool as lc_tool

        lc_tools = []
        for name, data in self._tools.items():

            @lc_tool(name, description=data["description"])
            def _tool_wrapper(args_str: str, _name=name) -> str:
                try:
                    args = (
                        json.loads(args_str) if isinstance(args_str, str) else args_str
                    )
                except json.JSONDecodeError:
                    args = {"query": args_str}
                result = self.invoke(_name, args)
                return json.dumps(result, ensure_ascii=False)

            lc_tools.append(_tool_wrapper)
        return lc_tools

    def _register_defaults(self) -> None:
        """Register dummy tool implementations for MVP."""
        self.register(
            "search",
            "Search the web for information. Input: query string.",
            self._dummy_search,
        )
        self.register(
            "code_exec",
            "Execute Python code in a sandbox. Input: code string.",
            self._dummy_code_exec,
        )
        self.register(
            "http_request",
            "Make an HTTP request. Input: url, method, headers, body.",
            self._dummy_http_request,
        )

    @staticmethod
    def _dummy_search(args: dict) -> dict:
        query = args.get("query", "")
        return {
            "results": [
                {
                    "title": f"Result for: {query[:50]}",
                    "url": "https://example.com/1",
                    "snippet": f"Found information about {query[:30]}...",
                },
                {
                    "title": f"Related: {query[:30]}",
                    "url": "https://example.com/2",
                    "snippet": "Additional context and references.",
                },
            ],
            "total": 2,
        }

    @staticmethod
    def _dummy_code_exec(args: dict) -> dict:
        code = args.get("code", "print('hello')")
        return {
            "output": f"Executed: {code[:100]}",
            "stdout": f"[simulated output for: {code[:50]}...]",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 42,
        }

    @staticmethod
    def _dummy_http_request(args: dict) -> dict:
        url = args.get("url", "https://httpbin.org/get")
        method = args.get("method", "GET")
        return {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": {"message": f"Simulated {method} response from {url}", "data": {}},
        }
