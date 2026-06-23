"""FlowCraft Graph Compiler — Compiles workflow JSON into LangGraph StateGraph.

This is the core engine. It traverses a workflow JSON definition and dynamically
builds a LangGraph StateGraph with nodes, edges, conditional routing, and retry loops.
"""

import operator
from typing import Any, Callable, Dict, List

from langgraph.graph import StateGraph, END

from .state import AgentState
from .factory import AgentNodeFactory


class GraphCompiler:
    """Compiles a FlowCraft workflow JSON into an executable LangGraph StateGraph.

    Usage:
        compiler = GraphCompiler()
        graph = compiler.compile(workflow_json)
        result = graph.invoke({"task": "Write a poem about Python"})
    """

    def __init__(self, max_retries_default: int = 3):
        self.max_retries_default = max_retries_default
        self._factory = AgentNodeFactory.get_instance()

    def compile(self, workflow: dict) -> Any:
        """Compile workflow JSON into executable StateGraph."""
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        if not nodes:
            raise ValueError("Workflow must contain at least one node.")
        if not edges:
            raise ValueError("Workflow must contain at least one edge.")

        builder = StateGraph(AgentState)

        # Register nodes via factory
        entry_point = nodes[0]["id"]
        for node in nodes:
            node_id = node["id"]
            node_type = node["type"]

            # Build kwargs for factory
            kwargs = {}
            if node_type == "tool":
                kwargs["tool_name"] = node.get("tool_name", "unknown")

            try:
                node_fn = self._factory.create(node_type, **kwargs)
            except ValueError as e:
                raise ValueError(
                    f"Unknown node type '{node_type}' for node '{node_id}'. "
                    f"Registered: {self._factory.list_types()}"
                ) from e

            builder.add_node(node_id, node_fn)

        builder.set_entry_point(entry_point)

        # Compile edges
        retry_edges = self._detect_retry_edges(edges, nodes)

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            condition = edge.get("condition")
            expression = edge.get("expression")  # [TENTATIVE] advanced mode

            if condition or expression:
                cond_fn = self._compile_condition(condition, expression)
                if edge in retry_edges:
                    max_retries = edge.get("loop", {}).get(
                        "max_retries", self.max_retries_default
                    )
                    cond_fn = self._wrap_retry_guard(cond_fn, max_retries, target)

                routing = {
                    "true": target,
                    "false": self._resolve_false_target(source, target, edges),
                }
                builder.add_conditional_edges(source, cond_fn, routing)
            else:
                builder.add_edge(source, target)

        from langgraph.checkpoint.memory import MemorySaver

        return builder.compile(checkpointer=MemorySaver())

    # ── Condition Compilation (simple + advanced) ────

    def _compile_condition(
        self, condition: dict | None, expression: str | None = None
    ) -> Callable:
        """Compile a condition into a routing function.

        Supports two modes:
        - Simple: {field, op, value} → comparison lambda
        - Advanced: Python expression → RestrictedPython sandbox [TENTATIVE]
        """
        # Advanced mode: RestrictedPython sandbox
        if expression:
            from .sandbox import execute_sandbox, SandboxError

            def advanced_cond(state: AgentState) -> str:
                try:
                    result = execute_sandbox(expression, dict(state))
                    return "true" if result else "false"
                except SandboxError as e:
                    print(f"  ⚠ Sandbox error: {e}. Routing to false.")
                    return "false"

            return advanced_cond

        # Simple mode: {field, op, value}
        if not condition:
            raise ValueError(
                "Condition must have either 'condition' or 'expression' field."
            )

        field = condition["field"]
        op = condition["op"]
        value = condition["value"]

        ops = {
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            "<": operator.lt,
            ">=": operator.ge,
            "<=": operator.le,
        }

        if op not in ops:
            raise ValueError(
                f"Unsupported operator '{op}'. Supported: {list(ops.keys())}"
            )

        comparator = ops[op]

        def simple_cond(state: AgentState) -> str:
            actual = state.get(field)
            result = comparator(actual, value)
            return "true" if result else "false"

        return simple_cond

    # ── Retry Loop Detection ────

    def _detect_retry_edges(self, edges: List[dict], nodes: List[dict]) -> List[dict]:
        node_types = {n["id"]: n["type"] for n in nodes}
        retry_edges = []
        for edge in edges:
            st = node_types.get(edge["source"], "")
            tt = node_types.get(edge["target"], "")
            if (
                st == "reviewer"
                and tt == "executor"
                and (edge.get("condition") or edge.get("expression"))
            ):
                retry_edges.append(edge)
        return retry_edges

    def _wrap_retry_guard(
        self, cond_fn: Callable, max_retries: int, retry_target: str
    ) -> Callable:
        def guarded_cond(state: AgentState) -> str:
            retry_count = state.get("retry_count", 0)
            if retry_count >= max_retries:
                print(f"  ⚠ Max retries ({max_retries}) exceeded. Forcing termination.")
                return "false"
            state["retry_count"] = retry_count + 1
            print(f"  ↻ Retry {state['retry_count']}/{max_retries}")
            return cond_fn(state)

        return guarded_cond

    def _resolve_false_target(
        self, source: str, true_target: str, edges: List[dict]
    ) -> str:
        for edge in edges:
            if (
                edge["source"] == source
                and edge["target"] != true_target
                and (edge.get("condition") or edge.get("expression"))
            ):
                return edge["target"]
        return END
