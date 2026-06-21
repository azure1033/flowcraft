"""FlowCraft Graph Compiler — Compiles workflow JSON into LangGraph StateGraph.

This is the core engine. It traverses a workflow JSON definition and dynamically
builds a LangGraph StateGraph with nodes, edges, conditional routing, and retry loops.
"""

import operator
from typing import Any, Callable, Dict, List

from langgraph.graph import StateGraph, END

from .state import AgentState
from .agents import planner_agent, executor_agent, reviewer_agent


# Node type → agent function mapping
NODE_FACTORY: Dict[str, Callable] = {
    "planner": planner_agent,
    "executor": executor_agent,
    "reviewer": reviewer_agent,
}


class GraphCompiler:
    """Compiles a FlowCraft workflow JSON into an executable LangGraph StateGraph.

    Usage:
        compiler = GraphCompiler()
        graph = compiler.compile(workflow_json)
        result = graph.invoke({"task": "Write a poem about Python"})
    """

    def __init__(self, max_retries_default: int = 3):
        self.max_retries_default = max_retries_default

    def compile(self, workflow: dict) -> Any:
        """Compile workflow JSON into executable StateGraph.

        Args:
            workflow: Dict with 'nodes' and 'edges' arrays.

        Returns:
            Compiled LangGraph StateGraph (Runnable).

        Raises:
            ValueError: If workflow structure is invalid.
        """
        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])

        if not nodes:
            raise ValueError("Workflow must contain at least one node.")
        if not edges:
            raise ValueError("Workflow must contain at least one edge.")

        # Build StateGraph
        builder = StateGraph(AgentState)

        # Register nodes
        entry_point = nodes[0]["id"]
        for node in nodes:
            node_id = node["id"]
            node_type = node["type"]

            if node_type not in NODE_FACTORY:
                raise ValueError(
                    f"Unknown node type '{node_type}' for node '{node_id}'. "
                    f"Supported types: {list(NODE_FACTORY.keys())}"
                )

            builder.add_node(node_id, NODE_FACTORY[node_type])

        builder.set_entry_point(entry_point)

        # Compile edges
        retry_edges = self._detect_retry_edges(edges, nodes)

        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            condition = edge.get("condition")

            if condition:
                cond_fn = self._compile_condition(condition)
                # Check if this is a retry loop edge
                if edge in retry_edges:
                    max_retries = edge.get("loop", {}).get("max_retries", self.max_retries_default)
                    cond_fn = self._wrap_retry_guard(cond_fn, max_retries, target)

                routing = {"true": target, "false": self._resolve_false_target(source, target, edges)}
                builder.add_conditional_edges(source, cond_fn, routing)
            else:
                builder.add_edge(source, target)

        # Compile with in-memory checkpointer (MVP — PostgreSQL checkpointing later)
        from langgraph.checkpoint.memory import MemorySaver
        return builder.compile(checkpointer=MemorySaver())

    def _detect_retry_edges(self, edges: List[dict], nodes: List[dict]) -> List[dict]:
        """Detect Reviewer→Executor back-edges that form retry loops.

        Only Reviewer→Executor edges with conditions are treated as retry loops.
        """
        node_types = {n["id"]: n["type"] for n in nodes}
        retry_edges = []

        for edge in edges:
            source_type = node_types.get(edge["source"], "")
            target_type = node_types.get(edge["target"], "")
            if source_type == "reviewer" and target_type == "executor" and edge.get("condition"):
                retry_edges.append(edge)

        return retry_edges

    def _compile_condition(self, condition: dict) -> Callable:
        """Compile a simple condition {field, op, value} into a routing function.

        Returns a function that takes AgentState and returns "true" or "false".
        """
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
            raise ValueError(f"Unsupported operator '{op}'. Supported: {list(ops.keys())}")

        comparator = ops[op]

        def cond_fn(state: AgentState) -> str:
            actual = state.get(field)
            result = comparator(actual, value)
            return "true" if result else "false"

        return cond_fn

    def _wrap_retry_guard(
        self, cond_fn: Callable, max_retries: int, retry_target: str
    ) -> Callable:
        """Wrap a condition function with retry count enforcement.

        When retry_count >= max_retries, forces routing to __end__ regardless
        of the original condition result.
        """
        def guarded_cond(state: AgentState) -> str:
            retry_count = state.get("retry_count", 0)

            if retry_count >= max_retries:
                print(f"  ⚠ Max retries ({max_retries}) exceeded. Forcing termination.")
                return "false"  # Routes to __end__ via false target

            # Increment retry count
            state["retry_count"] = retry_count + 1
            print(f"  ↻ Retry {state['retry_count']}/{max_retries}")

            return cond_fn(state)

        return guarded_cond

    def _resolve_false_target(
        self, source: str, true_target: str, edges: List[dict]
    ) -> str:
        """Find the 'false' routing target for conditional edges.

        Searches for another edge from the same source with a different condition
        to serve as the 'else' branch. Falls back to END if none found.
        """
        for edge in edges:
            if edge["source"] == source and edge["target"] != true_target and edge.get("condition"):
                return edge["target"]

        return END
