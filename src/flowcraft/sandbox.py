"""RestrictedPython sandbox for safe execution of user-defined condition expressions."""

import threading
from typing import Any


def execute_sandbox(expression: str, state: dict, timeout: int = 5) -> Any:
    """Execute a user-provided expression in a RestrictedPython sandbox.

    Args:
        expression: Python expression string (e.g., 'state["score"] > 0.5').
        state: AgentState dict available as `state` in the sandbox.
        timeout: Maximum execution time in seconds (default 5).
    """
    result_container = {"value": None, "error": None}

    def _run():
        try:
            from RestrictedPython import compile_restricted, safe_builtins

            # Compile the expression
            code = compile_restricted(expression, "<sandbox>", "eval")

            # Build safe globals
            safe_globals = {
                "__builtins__": safe_builtins,
                "state": state,
            }

            result = eval(code, safe_globals)
            result_container["value"] = result

        except SyntaxError as e:
            result_container["error"] = f"Syntax error: {e}"
        except ImportError:
            result_container["error"] = "Import statements are forbidden in sandbox."
        except Exception as e:
            result_container["error"] = f"Sandbox error: {e}"

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        raise SandboxError(f"Expression timed out after {timeout}s.")

    if result_container["error"]:
        raise SandboxError(result_container["error"])

    return result_container["value"]


class SandboxError(Exception):
    """Raised when sandbox execution fails."""

    pass
