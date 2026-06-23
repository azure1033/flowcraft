# Quick engine test
from flowcraft.factory import AgentNodeFactory
from flowcraft.compiler import GraphCompiler
from flowcraft.sandbox import execute_sandbox, SandboxError
import json

# 1. Factory
f = AgentNodeFactory.get_instance()
assert "planner" in f.list_types()
assert "tool" in f.list_types()
print(f"OK factory: {f.list_types()}")

# 2. Compiler with factory
c = GraphCompiler()
wf = json.load(open("examples/demo_workflow.json", "r", encoding="utf-8"))
g = c.compile(wf)
assert "plan" in g.nodes
print(f"OK compiler: {list(g.nodes.keys())}")

# 3. Sandbox
r = execute_sandbox('state.get("x", 0) > 5', {"x": 10})
assert r is True
print(f"OK sandbox: 10>5 = {r}")

# 4. Sandbox safety
try:
    execute_sandbox("__import__('os').system('rm -rf /')", {})
    assert False, "Should have raised SandboxError"
except SandboxError:
    print("OK sandbox security: import blocked")

# 5. Sandbox timeout
try:
    execute_sandbox("sum(range(10**9))", {}, timeout=1)
    assert False, "Should have timed out"
except SandboxError:
    print("OK sandbox timeout: 1s limit enforced")

print("\nAll engine tests passed!")
