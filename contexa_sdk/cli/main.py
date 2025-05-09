"""Main CLI entry point for Contexa SDK."""

import os
import sys
import json
import importlib.util
from typing import Any, Dict, List, Optional
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.deployment.builder import build_agent
from contexa_sdk.deployment.deployer import deploy_agent, list_deployments, get_deployment


app = typer.Typer(
    name="ctx",
    help="Contexa SDK CLI for building and deploying agents",
    add_completion=False,
)
console = Console()


@app.command("init")
def init_project(
    dir_path: str = typer.Argument(".", help="Directory to initialize in (default: current directory)"),
):
    """Initialize a new Contexa project."""
    path = Path(dir_path)
    if not path.exists():
        path.mkdir(parents=True)
        
    # Create project structure
    config_dir = path / ".ctx"
    config_dir.mkdir(exist_ok=True)
    
    build_dir = config_dir / "build"
    build_dir.mkdir(exist_ok=True)
    
    deployments_dir = config_dir / "deployments"
    deployments_dir.mkdir(exist_ok=True)
    
    # Create config file
    config_file = config_dir / "config.json"
    if not config_file.exists():
        config = {
            "api_url": "https://api.contexa.ai/v0",
            "org_id": None,
        }
        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)
            
    # Create sample agent file
    sample_agent_file = path / "agent.py"
    if not sample_agent_file.exists():
        with open(sample_agent_file, "w") as f:
            f.write("""
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.tool import ContexaTool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str

@ContexaTool.register(
    name="web_search",
    description="Search the web and return text snippet"
)
async def web_search(inp: SearchInput) -> str:
    return f"Top hit for {inp.query}"

# Create an agent with the tool
model = ContexaModel("gpt-4o", provider="openai")
agent = ContexaAgent(
    tools=[web_search.__contexa_tool__],
    model=model,
    name="search_agent",
    description="An agent that can search the web",
    system_prompt="You are a helpful search assistant.",
)

# This will be used by the CLI when building and deploying
__contexa_agent__ = agent
""")
    
    # Create pyproject.toml if it doesn't exist
    pyproject_file = path / "pyproject.toml"
    if not pyproject_file.exists():
        with open(pyproject_file, "w") as f:
            f.write("""
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-contexa-agent"
version = "0.1.0"
description = "My Contexa Agent"
requires-python = ">=3.8"
dependencies = [
    "contexa-sdk>=0.1.0",
]
""")
    
    console.print("[bold green]✓[/bold green] Project initialized successfully!")
    console.print(f"[bold]Next steps:[/bold]")
    console.print("1. Edit agent.py to customize your agent")
    console.print("2. Run [bold]ctx build[/bold] to build your agent")
    console.print("3. Run [bold]ctx deploy[/bold] to deploy your agent to Contexa Cloud")


@app.command("build")
def build_command(
    agent_path: str = typer.Option("agent.py", help="Path to agent module"),
    output_dir: Optional[str] = typer.Option(None, help="Output directory for build artifacts"),
):
    """Build an agent for deployment."""
    # Load the agent from the module
    agent = _load_agent_from_module(agent_path)
    
    # Build the agent
    with console.status("[bold blue]Building agent...[/bold blue]"):
        artifact_path = build_agent(agent, output_dir=output_dir)
        
    console.print(f"[bold green]✓[/bold green] Agent built successfully: {artifact_path}")
    console.print(f"[bold]Next step:[/bold] Deploy with [bold]ctx deploy {artifact_path}[/bold]")


@app.command("deploy")
def deploy_command(
    artifact_path: str = typer.Argument(..., help="Path to built agent artifact"),
):
    """Deploy an agent to Contexa Cloud."""
    # Load config
    config_path = Path(".ctx/config.json")
    config = None
    if config_path.exists():
        with open(config_path, "r") as f:
            config_data = json.load(f)
            config = ContexaConfig(**config_data)
            
    # Check API key
    if not config or not config.api_key:
        api_key = os.environ.get("CONTEXA_API_KEY")
        if not api_key:
            console.print("[bold red]⨯[/bold red] API key not found. Set CONTEXA_API_KEY environment variable or add to .ctx/config.json")
            return
        if config:
            config.api_key = api_key
        else:
            config = ContexaConfig(api_key=api_key)
            
    # Deploy the agent
    with console.status("[bold blue]Deploying agent...[/bold blue]"):
        deployment_info = deploy_agent(artifact_path, config=config)
        
    console.print(f"[bold green]✓[/bold green] Agent deployed successfully!")
    console.print(f"[bold]Endpoint URL:[/bold] {deployment_info['endpoint_url']}")
    console.print(f"[bold]Endpoint ID:[/bold] {deployment_info['endpoint_id']}")


@app.command("list")
def list_command():
    """List deployed agents."""
    deployments = list_deployments()
    
    if not deployments:
        console.print("[bold yellow]No deployments found.[/bold yellow]")
        return
        
    table = Table("ID", "Status", "Endpoint URL", "Created At")
    for deployment in deployments:
        table.add_row(
            deployment["endpoint_id"],
            deployment["status"],
            deployment["endpoint_url"],
            deployment["created_at"],
        )
        
    console.print(table)


@app.command("run")
def run_command(
    agent_path: str = typer.Option("agent.py", help="Path to agent module"),
    query: str = typer.Argument(..., help="Query to run against the agent"),
):
    """Run an agent locally."""
    # Load the agent from the module
    agent = _load_agent_from_module(agent_path)
    
    # Run the agent
    with console.status("[bold blue]Running agent...[/bold blue]"):
        import asyncio
        response = asyncio.run(agent.run(query))
        
    console.print("[bold]Agent response:[/bold]")
    console.print(response)


def _load_agent_from_module(module_path: str) -> ContexaAgent:
    """Load an agent from a module.
    
    Args:
        module_path: Path to the module to load
        
    Returns:
        The loaded agent
    """
    module_path = Path(module_path)
    if not module_path.exists():
        console.print(f"[bold red]⨯[/bold red] Module not found: {module_path}")
        sys.exit(1)
        
    # Load the module
    spec = importlib.util.spec_from_file_location("agent_module", module_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Get the agent
    if not hasattr(module, "__contexa_agent__"):
        console.print(f"[bold red]⨯[/bold red] Module does not define __contexa_agent__: {module_path}")
        sys.exit(1)
        
    agent = module.__contexa_agent__
    if not isinstance(agent, ContexaAgent):
        console.print(f"[bold red]⨯[/bold red] __contexa_agent__ is not a ContexaAgent: {module_path}")
        sys.exit(1)
        
    return agent


if __name__ == "__main__":
    app() 