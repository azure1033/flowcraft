# FlowCraft

🛠️ Open Source Visual Workflow Orchestration Platform for LLM Agent Pipelines.

**Status**: 🚧 MVP (Work in Progress)

FlowCraft lets you visually design LLM agent workflows on a canvas, export them as JSON,
and execute them via a LangGraph-powered engine. Think "draw your agent pipeline, hit run."

## Quick Start (MVP)

```bash
# 1. Install dependencies
uv sync

# 2. Configure your LLM API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-your-key

# 3. Run the demo
uv run python -m flowcraft.main
```

## Architecture

```
Workflow JSON → GraphCompiler → LangGraph StateGraph → Execution
     ↑                                                    ↓
  Canvas (future)                              Planner → Executor → Reviewer
                                               (with retry loop + human-in-the-loop)
```

## License

Apache 2.0 — see [LICENSE](LICENSE).
