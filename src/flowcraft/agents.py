"""FlowCraft Agent Nodes — Planner, Executor, and Reviewer implementations.

Each agent node is a function that receives the current AgentState and returns
a partial state update. Nodes use LangChain ChatModel for LLM interactions.
"""

import json
import os
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

from .state import AgentState

load_dotenv()

# --- LLM Factory ---

def _get_llm(model_override: str | None = None) -> ChatOpenAI:
    """Create ChatOpenAI instance from environment config.

    Supports optional per-node model override (TENTATIVE feature).
    """
    model = model_override or os.getenv("LLM_MODEL", "gpt-4o-mini")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not set. Copy .env.example to .env and fill in your API key."
        )

    return ChatOpenAI(model=model, base_url=base_url, api_key=api_key, temperature=0.3)


# --- Planner Agent ---

PLANNER_SYSTEM_PROMPT = """You are a task planning agent. Your job is to decompose a user's task into 
concrete, sequential steps. Output ONLY valid JSON with this structure:

{
  "steps": ["step 1 description", "step 2 description", ...],
  "reasoning": "brief explanation of the decomposition strategy"
}

Each step should be executable by a single agent action. Be specific and actionable."""


def planner_agent(state: AgentState) -> Dict[str, Any]:
    """Decompose the user's task into an ordered list of execution steps.

    Reads state['task'] and populates state['plan'] with structured steps.
    """
    task = state.get("task", "")
    if not task:
        task = str(state.get("messages", [HumanMessage(content="No task provided")])[-1].content)

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=PLANNER_SYSTEM_PROMPT),
        HumanMessage(content=f"Decompose this task into steps:\n\n{task}")
    ])

    # Parse JSON from response
    try:
        plan = json.loads(response.content)
    except json.JSONDecodeError:
        # Fallback: wrap raw response
        plan = {"steps": [response.content], "reasoning": "Direct response (JSON parse failed)"}

    return {
        "plan": plan,
        "current_step": 0,
        "messages": [response],
    }


# --- Executor Agent ---

EXECUTOR_SYSTEM_PROMPT = """You are an execution agent. Execute the given step precisely and report 
the result. Output ONLY valid JSON:

{
  "step_completed": "description of what was done",
  "result": "the actual execution result or analysis",
  "status": "success" or "error"
}

If you cannot fully execute the step, explain why in the result and set status to "error"."""


def executor_agent(state: AgentState) -> Dict[str, Any]:
    """Execute the current step from the plan.

    Reads state['plan'] and state['current_step'], updates state['exec_output'].
    """
    plan = state.get("plan", {})
    steps = plan.get("steps", [])
    current_step = state.get("current_step", 0)

    if current_step >= len(steps):
        return {"exec_output": "All steps completed."}

    step_description = steps[current_step]

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=EXECUTOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Original task: {state.get('task', 'N/A')}\n\n"
                             f"Plan so far: {json.dumps(plan, ensure_ascii=False)}\n\n"
                             f"Execute step {current_step + 1}/{len(steps)}: {step_description}")
    ])

    try:
        result = json.loads(response.content)
        exec_summary = f"[Step {current_step + 1}] {result.get('step_completed', 'Done')}\n"
        exec_summary += f"Result: {result.get('result', response.content)}"
    except json.JSONDecodeError:
        exec_summary = response.content

    return {
        "exec_output": exec_summary,
        "current_step": current_step + 1,
        "messages": [response],
    }


# --- Reviewer Agent ---

REVIEWER_SYSTEM_PROMPT = """You are a quality review agent. Evaluate the execution result against 
the original task. Output ONLY valid JSON:

{
  "decision": "approved" or "rejected",
  "score": 1-10,
  "feedback": "detailed review feedback",
  "issues": ["issue 1", "issue 2"] (empty list if none)
}

Approve if the result adequately addresses the task. Reject if there are significant issues 
or missing information. Be strict but fair."""


def reviewer_agent(state: AgentState) -> Dict[str, Any]:
    """Evaluate execution output against the original task.

    Reads state['exec_output'] and state['task'], outputs state['review_decision'].
    If human_confirm is set in metadata, the interrupt mechanism handles pausing.
    """
    task = state.get("task", "")
    exec_output = state.get("exec_output", "")

    llm = _get_llm()
    response = llm.invoke([
        SystemMessage(content=REVIEWER_SYSTEM_PROMPT),
        HumanMessage(content=f"Original task: {task}\n\n"
                             f"Execution result:\n{exec_output}\n\n"
                             f"Review this execution. Approve or reject with detailed feedback.")
    ])

    try:
        review = json.loads(response.content)
        decision = review.get("decision", "approved")
        feedback = review.get("feedback", response.content)
    except json.JSONDecodeError:
        decision = "approved"
        feedback = response.content

    return {
        "review_decision": decision,
        "messages": [response],
    }
