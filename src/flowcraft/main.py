"""FlowCraft MVP — Run a workflow from JSON using the LangGraph compiler.

Usage:
    python -m flowcraft.main [workflow.json]

    If no file is specified, uses the built-in demo workflow.
    Requires: OPENAI_API_KEY in .env file.
"""

import json
import sys
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from flowcraft.compiler import GraphCompiler
from flowcraft.state import AgentState


def load_workflow(path: str) -> dict:
    """Load workflow JSON from file path."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_workflow(workflow: dict, task: str) -> dict:
    """Compile and execute a workflow with the given task.

    Args:
        workflow: Workflow JSON definition.
        task: Natural language task description.

    Returns:
        Final AgentState after execution.
    """
    print(f"\n{'='*60}")
    print(f"  FlowCraft MVP — Workflow Execution Engine")
    print(f"{'='*60}")
    print(f"  Task: {task}")
    print(f"  Nodes: {[n['id'] for n in workflow['nodes']]}")
    print(f"  Edges: {[f\"{e['source']}→{e['target']}\" for e in workflow['edges']]}")
    print(f"{'='*60}\n")

    compiler = GraphCompiler()

    print("Compiling workflow...")
    graph = compiler.compile(workflow)
    print("✓ Graph compiled successfully.\n")

    print("Starting execution...")
    initial_state: AgentState = {
        "task": task,
        "current_step": 0,
        "retry_count": 0,
        "max_retries": 3,
        "review_decision": "",
        "human_input": "",
        "exec_output": "",
    }

    # Use a thread config for checkpointing
    config = {"configurable": {"thread_id": "demo-run"}}

    print("-" * 40)
    result = graph.invoke(initial_state, config)
    print("-" * 40)

    return result


def print_result(result: dict):
    """Pretty-print execution result."""
    print(f"\n{'='*60}")
    print(f"  Execution Complete")
    print(f"{'='*60}")

    plan = result.get("plan", {})
    steps = plan.get("steps", [])
    print(f"  Plan: {len(steps)} step(s)")
    for i, step in enumerate(steps, 1):
        print(f"    {i}. {step}")

    print(f"\n  Review Decision: {result.get('review_decision', 'N/A')}")
    print(f"  Retry Count: {result.get('retry_count', 0)}")

    exec_output = result.get("exec_output", "")
    if exec_output:
        print(f"\n  Execution Output:")
        for line in exec_output.strip().split("\n"):
            print(f"    {line}")

    print(f"{'='*60}\n")


def main():
    # Load workflow
    if len(sys.argv) > 1:
        workflow_path = sys.argv[1]
    else:
        # Default demo: plan → exec → review → (condition back to exec or end)
        workflow_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "examples", "demo_workflow.json"
        )

    workflow_path = os.path.abspath(workflow_path)

    if not os.path.exists(workflow_path):
        print(f"Error: Workflow file not found: {workflow_path}")
        print("Usage: python -m flowcraft.main [workflow.json]")
        sys.exit(1)

    workflow = load_workflow(workflow_path)

    # Task to execute
    task = "Write a short poem about Python programming, then review the result for quality."

    # Run
    try:
        result = run_workflow(workflow, task)
        print_result(result)
    except Exception as e:
        print(f"\n✗ Execution failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
