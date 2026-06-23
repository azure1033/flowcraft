"""AgentNodeFactory — extensible registry for agent node types.

Allows registering custom agent node factories without modifying core code.
Follows the Open/Closed principle: open for extension, closed for modification.
"""

from typing import Any, Callable, Dict


AgentNodeFn = Callable[[dict], dict]
"""An agent node function: receives AgentState, returns partial state update."""


class AgentNodeFactory:
    """Registry-based factory for creating agent node functions.

    Built-in types (planner, executor, reviewer, tool) are pre-registered.
    Custom types can be registered via `register()`.

    Usage:
        factory = AgentNodeFactory()
        factory.register("translator", my_translator_fn)
        node_fn = factory.create("translator")
    """

    _instance: "AgentNodeFactory | None" = None

    def __init__(self):
        self._registry: Dict[str, AgentNodeFn] = {}

    @classmethod
    def get_instance(cls) -> "AgentNodeFactory":
        """Get or create the singleton factory instance."""
        if cls._instance is None:
            cls._instance = cls()
            cls._instance._register_builtins()
        return cls._instance

    def register(self, node_type: str, factory_fn: AgentNodeFn) -> None:
        """Register a new node type.

        Args:
            node_type: Unique type identifier (e.g., "translator").
            factory_fn: Function that creates the node's handler.

        Raises:
            ValueError: If the type is already registered.
        """
        if node_type in self._registry:
            raise ValueError(
                f"Node type '{node_type}' is already registered. "
                "Use a different name or call reset() first."
            )
        self._registry[node_type] = factory_fn

    def create(self, node_type: str, **kwargs: Any) -> AgentNodeFn:
        """Create a node function for the given type.

        Args:
            node_type: The type identifier to look up.
            **kwargs: Additional keyword args passed to the factory function.

        Returns:
            A callable agent node function.

        Raises:
            ValueError: If the node type is not registered.
        """
        if node_type not in self._registry:
            raise ValueError(
                f"Unknown node type '{node_type}'. "
                f"Registered types: {list(self._registry.keys())}. "
                f"Use factory.register('{node_type}', fn) to add it."
            )

        factory_fn = self._registry[node_type]
        if kwargs:
            # If the factory accepts parameters, pass them
            import inspect

            sig = inspect.signature(factory_fn)
            if sig.parameters:
                return factory_fn(node_type=node_type, **kwargs)

        return factory_fn

    def list_types(self) -> list[str]:
        """Return all registered node type names."""
        return list(self._registry.keys())

    def reset(self) -> None:
        """Clear all registered types and re-register builtins."""
        self._registry.clear()
        self._register_builtins()

    def _register_builtins(self) -> None:
        """Register the four built-in node types."""
        from .agents import planner_agent, executor_agent, reviewer_agent, tool_executor

        self._registry["planner"] = planner_agent
        self._registry["executor"] = executor_agent
        self._registry["reviewer"] = reviewer_agent
        self._registry["tool"] = tool_executor
