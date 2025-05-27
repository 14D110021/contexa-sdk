"""Main CLI entry point for Contexa SDK.

This module implements the command-line interface (CLI) for the Contexa SDK,
providing commands for:

- Project initialization
- Agent building and packaging
- Deployment to Contexa Cloud
- Listing deployed agents
- Running agents locally

The CLI uses Typer for command definition and Rich for terminal output formatting.
Commands are designed to follow a natural workflow from initialization through
development, building, and deployment.

Example usage:
    # Initialize a new project
    ctx init my_project
    
    # Build an agent
    ctx build --agent-path my_project/agent.py
    
    # Deploy the agent
    ctx deploy ./build/my_agent_0.1.0.tar.gz
    
    # List deployed agents
    ctx list
    
    # Run an agent locally
    ctx run "What's the weather like today?"
"""

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
    """Initialize a new Contexa project.
    
    This command creates a new Contexa project with the necessary directory
    structure and template files. It sets up:
    
    - Project configuration directory (.ctx/)
    - Build artifacts directory (.ctx/build/)
    - Deployments tracking directory (.ctx/deployments/)
    - Configuration file (.ctx/config.json)
    - Sample agent file (agent.py)
    - Python project configuration (pyproject.toml)
    
    The created project structure follows best practices for Contexa agent
    development and provides a starting point with a simple agent definition.
    
    Args:
        dir_path: Directory where the project should be initialized. If the
            directory doesn't exist, it will be created. Defaults to the
            current directory.
    
    Example:
        # Initialize in the current directory
        $ ctx init
        
        # Initialize in a new directory
        $ ctx init my_search_agent
    """
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
    """Build an agent for deployment.
    
    This command loads an agent from a Python module and packages it for
    deployment. The agent module must define a ContexaAgent instance as
    the __contexa_agent__ attribute.
    
    The build process:
    1. Loads the agent from the specified module
    2. Serializes the agent configuration and tools
    3. Packages everything into a deployable artifact (.tar.gz)
    
    The resulting artifact can be deployed to Contexa Cloud using the
    'deploy' command.
    
    Args:
        agent_path: Path to the Python module containing the agent definition.
            The module must define a __contexa_agent__ attribute that is a
            ContexaAgent instance. Defaults to "agent.py".
        output_dir: Directory where the build artifact should be placed.
            If not specified, the default build directory (.ctx/build/) is used.
    
    Example:
        # Build an agent from the default agent.py file
        $ ctx build
        
        # Build an agent from a custom module
        $ ctx build --agent-path agents/search_agent.py
        
        # Specify a custom output directory
        $ ctx build --output-dir ./dist
    """
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
    """Deploy an agent to Contexa Cloud.
    
    This command uploads a built agent artifact to Contexa Cloud, making it
    accessible via an API endpoint. The deployment process:
    
    1. Loads the Contexa configuration
    2. Verifies API credentials
    3. Uploads the artifact to Contexa Cloud
    4. Records deployment information locally
    
    The command requires a Contexa API key, which can be provided either
    through the CONTEXA_API_KEY environment variable or in the .ctx/config.json
    file.
    
    Args:
        artifact_path: Path to the built agent artifact (.tar.gz) created by the
            'build' command.
    
    Example:
        # Deploy a specific artifact
        $ ctx deploy .ctx/build/search_agent_0.1.0.tar.gz
        
        # Deploy with API key from environment variable
        $ export CONTEXA_API_KEY=your-api-key
        $ ctx deploy .ctx/build/search_agent_0.1.0.tar.gz
    """
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
    """List deployed agents.
    
    This command displays information about all agents deployed from the
    current project. For each deployment, it shows:
    
    - Endpoint ID: Unique identifier for the endpoint
    - Status: Current deployment status
    - Endpoint URL: URL where the agent can be accessed
    - Created At: Timestamp when the agent was deployed
    
    The command reads deployment information from the local .ctx/deployments/
    directory, which is updated each time an agent is deployed.
    
    Example:
        # List all deployed agents
        $ ctx list
    """
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
    """Run an agent locally.
    
    This command loads an agent from a Python module and runs it locally with
    the specified query. This is useful for testing and debugging agents before
    deploying them.
    
    The command:
    1. Loads the agent from the specified module
    2. Runs the agent with the provided query
    3. Displays the agent's response
    
    Args:
        agent_path: Path to the Python module containing the agent definition.
            The module must define a __contexa_agent__ attribute that is a
            ContexaAgent instance. Defaults to "agent.py".
        query: The query to run against the agent.
    
    Example:
        # Run a query against the default agent
        $ ctx run "What's the weather like today?"
        
        # Run a query against a custom agent
        $ ctx run --agent-path agents/search_agent.py "How tall is Mount Everest?"
    """
    # Load the agent from the module
    agent = _load_agent_from_module(agent_path)
    
    # Run the agent
    with console.status("[bold blue]Running agent...[/bold blue]"):
        import asyncio
        response = asyncio.run(agent.run(query))
        
    console.print("[bold]Agent response:[/bold]")
    console.print(response)


def _load_agent_from_module(module_path: str) -> ContexaAgent:
    """Load an agent from a Python module.
    
    This internal helper function loads a ContexaAgent instance from a Python
    module. The module must define a __contexa_agent__ attribute that is a
    ContexaAgent instance.
    
    The function:
    1. Verifies the module exists
    2. Loads the module
    3. Extracts the __contexa_agent__ attribute
    4. Verifies it's a ContexaAgent instance
    
    Args:
        module_path: Path to the Python module containing the agent definition.
        
    Returns:
        The ContexaAgent instance defined in the module.
        
    Raises:
        SystemExit: If the module doesn't exist, doesn't define __contexa_agent__,
            or __contexa_agent__ is not a ContexaAgent instance.
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