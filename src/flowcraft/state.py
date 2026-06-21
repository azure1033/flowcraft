"""FlowCraft Agent State — shared state flowing through LangGraph nodes."""

from typing import List, TypedDict, Optional, Any
from langchain_core.messages import BaseMessage


class AgentState(TypedDict, total=False):
    """Shared state dictionary flowing through all nodes in the workflow graph.

    Fields are populated by different agent nodes as execution progresses.
    The state is checkpointed by LangGraph for interrupt/resume support.
    """

    # LangChain conversation history (system prompt + user input + assistant responses)
    messages: List[BaseMessage]

    # Planner output: structured task decomposition
    plan: dict

    # Current execution step index
    current_step: int

    # Executor output: result of executing the current step
    exec_output: str

    # Reviewer decision: "approved" or "rejected"
    review_decision: str

    # Human input when manual review is required
    human_input: str

    # Retry loop tracking
    retry_count: int
    max_retries: int

    # Original user task (carried through for context)
    task: str

    # Generic data slots for conditional edge evaluation
    metadata: dict
