"""FlowCraft CLI — agent-flow command."""

import click


@click.group()
@click.version_option(version="0.1.0", prog_name="agent-flow")
def cli():
    """FlowCraft CLI — Visual Workflow Orchestration Platform.

    Scaffold, develop, and test LLM agent pipelines.
    """
    pass


@cli.command()
@click.argument("path", default=".")
def init(path: str):
    """Scaffold a new FlowCraft project.

    Creates .env.example, docker-compose.yml, and examples/ directory.
    """
    import os

    click.echo(f"Initializing FlowCraft project in: {os.path.abspath(path)}")

    os.makedirs(os.path.join(path, "examples"), exist_ok=True)

    env_example = os.path.join(path, ".env.example")
    if not os.path.exists(env_example):
        with open(env_example, "w") as f:
            f.write("# FlowCraft Environment Configuration\n")
            f.write("OPENAI_API_KEY=sk-your-key-here\n")
            f.write("LLM_MODEL=gpt-4o-mini\n")
            f.write("API_KEY=flowcraft-dev-key-change-in-production\n")
            f.write("ENABLE_SIMULATED_REVIEW=true\n")
        click.echo(f"  Created: .env.example")

    docker_compose = os.path.join(path, "docker-compose.yml")
    if not os.path.exists(docker_compose):
        with open(docker_compose, "w") as f:
            f.write("# Basic FlowCraft stack\n")
            f.write("services:\n")
            f.write("  backend:\n")
            f.write("    build: .\n")
            f.write('    ports: ["8000:8000"]\n')
            f.write("    env_file: .env\n")
            f.write("  frontend:\n")
            f.write("    build:\n")
            f.write("      context: .\n")
            f.write("      dockerfile: apps/frontend/Dockerfile\n")
            f.write('    ports: ["80:80"]\n')
            f.write("    depends_on: [backend]\n")
        click.echo(f"  Created: docker-compose.yml")

    click.echo(f"\nDone! Next steps:")
    click.echo(f"  1. Edit .env.example -> .env and set OPENAI_API_KEY")
    click.echo(f"  2. Run: agent-flow dev")
    click.echo(f"  3. Open: http://localhost:5173")


@cli.command()
def dev():
    """Start FlowCraft development servers.

    Prints startup instructions for backend + frontend.
    """
    click.echo("FlowCraft Development Mode")
    click.echo("=" * 40)
    click.echo()
    click.echo("Start these in separate terminals:")
    click.echo()
    click.echo("  Terminal 1 — Backend API:")
    click.echo("    uv run uvicorn flowcraft.api.app:app --reload")
    click.echo("    -> http://localhost:8000/docs")
    click.echo()
    click.echo("  Terminal 2 — Frontend:")
    click.echo("    cd apps/frontend && pnpm dev")
    click.echo("    -> http://localhost:5173")
    click.echo()
    click.echo("  Or with Docker:")
    click.echo("    docker compose up")
    click.echo("    -> http://localhost")


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("--task", "-t", default="Execute this workflow", help="Task description")
def test(workflow_file: str, task: str):
    """Test a workflow JSON file in simulated mode.

    WORKFLOW_FILE: Path to a workflow JSON file.
    """
    import json
    import os

    os.environ["ENABLE_SIMULATED_REVIEW"] = "true"

    click.echo(f"Testing workflow: {workflow_file}")
    click.echo(f"Task: {task}")
    click.echo("-" * 40)

    try:
        with open(workflow_file, "r", encoding="utf-8") as f:
            wf = json.load(f)
    except Exception as e:
        click.echo(f"Error loading workflow: {e}", err=True)
        return

    from flowcraft.compiler import GraphCompiler

    compiler = GraphCompiler()
    try:
        graph = compiler.compile(wf)
        click.echo(f"Compiled: {len(wf['nodes'])} nodes, {len(wf['edges'])} edges")
    except Exception as e:
        click.echo(f"Compile error: {e}", err=True)
        return

    try:
        state = {
            "task": task,
            "current_step": 0,
            "retry_count": 0,
            "max_retries": 3,
            "review_decision": "",
            "human_input": "",
            "exec_output": "",
        }
        config = {"configurable": {"thread_id": "cli-test"}}
        click.echo("Executing...")
        result = graph.invoke(state, config)
        click.echo(f"Done. Decision: {result.get('review_decision', 'N/A')}")
        click.echo(f"Output: {str(result.get('exec_output', ''))[:200]}")
    except Exception as e:
        click.echo(f"Execution error: {e}", err=True)


if __name__ == "__main__":
    cli()
