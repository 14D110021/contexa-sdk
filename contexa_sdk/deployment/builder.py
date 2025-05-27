"""Builder module for building and packaging Contexa agents.

This module provides functions for packaging Contexa agents into deployable
artifacts. It supports creating both standard agent packages and MCP-compatible
agent servers that can be deployed as standalone services.

The builder handles:
- Serializing agent configurations and tools
- Packaging memory state (optional)
- Generating MCP-compatible server code
- Creating deployment artifacts (tarballs)
- Generating Docker configurations for containerized deployment

The build process preserves all necessary information to restore and run
the agent in various deployment environments.
"""

import os
import json
import shutil
import tarfile
import tempfile
from typing import Dict, List, Any, Optional, Union

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import BaseTool
from contexa_sdk.core.config import ContexaConfig
from contexa_sdk.deployment.mcp_generator import (
    generate_mcp_app_py,
    generate_mcp_requirements_txt,
    generate_mcp_dockerfile,
    generate_mcp_openapi_spec,
)


def build_agent(
    agent: ContexaAgent,
    output_dir: str = "./build",
    version: str = "0.1.0",
    include_tools: bool = True,
    include_memory: bool = True,
    mcp_compatible: bool = False,
    mcp_version: str = "1.0",
) -> str:
    """Build and package a Contexa agent into a deployable artifact.
    
    This function is the main entry point for building agent packages. It handles
    serializing the agent configuration, tools, and optionally memory state into
    a deployable package. Two types of builds are supported:
    
    1. Standard agent package: A tarball containing agent configuration, tool configurations,
       and optionally memory state.
    2. MCP-compatible agent server: A complete server application package that can be
       deployed as a standalone service, including server code, Docker configuration,
       and OpenAPI specifications.
    
    Args:
        agent: The ContexaAgent instance to build and package
        output_dir: Directory to output the built agent artifact. Will be created
            if it doesn't exist.
        version: Semantic version string for the agent package (e.g., "0.1.0")
        include_tools: Whether to include the agent's tools in the build. When True,
            tools are serialized and included in the package.
        include_memory: Whether to include the agent's memory state in the build.
            This preserves conversation history and other stateful information.
        mcp_compatible: When True, builds an MCP-compatible agent server that can
            be deployed as a standalone service following the Machine Communication
            Protocol (MCP) standard.
        mcp_version: Version of the MCP standard to comply with. Only used when
            mcp_compatible is True.
        
    Returns:
        Path to the built agent artifact (tarball file)
        
    Examples:
        ```python
        from contexa_sdk.core.agent import ContexaAgent
        from contexa_sdk.deployment.builder import build_agent
        
        # Create an agent
        agent = ContexaAgent(
            name="Search Agent",
            description="Agent for performing web searches",
            tools=[search_tool, summarize_tool]
        )
        
        # Build a standard agent package
        package_path = build_agent(
            agent=agent,
            version="1.0.0",
            output_dir="./dist"
        )
        print(f"Agent package built at {package_path}")
        
        # Build an MCP-compatible agent server
        server_path = build_agent(
            agent=agent,
            version="1.0.0",
            output_dir="./dist",
            mcp_compatible=True,
            mcp_version="1.0"
        )
        print(f"MCP server package built at {server_path}")
        ```
    """
    # Create the output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Convert the agent to a dictionary
    agent_dict = agent.to_dict()
    
    # Add version information
    agent_dict["version"] = version
    
    # Create tool configurations
    tools_config = []
    if include_tools and agent.tools:
        for tool in agent.tools:
            tools_config.append(tool.to_dict())
    
    # If MCP compatible, build an MCP agent server
    if mcp_compatible:
        return build_mcp_agent_server(
            agent_dict=agent_dict,
            tools_config=tools_config,
            output_dir=output_dir,
            version=version,
            mcp_version=mcp_version,
        )
    
    # Build a regular agent package
    return _build_regular_agent_package(
        agent_dict=agent_dict,
        tools_config=tools_config,
        output_dir=output_dir,
        version=version,
        include_memory=include_memory,
    )


def build_mcp_agent_server(
    agent_dict: Dict[str, Any],
    tools_config: List[Dict[str, Any]],
    output_dir: str = "./build",
    version: str = "0.1.0",
    mcp_version: str = "1.0",
) -> str:
    """Build an MCP-compatible agent server package.
    
    This function generates a complete server application package that implements
    the Machine Communication Protocol (MCP) standard, allowing the agent to be
    deployed as a standalone service with a standardized API. The package includes:
    
    - Server application code (app.py)
    - Dependencies list (requirements.txt)
    - Docker configuration (Dockerfile)
    - OpenAPI specification (openapi.json)
    - Agent and tool configurations
    - Documentation (README.md)
    
    The resulting package can be deployed as a Docker container or as a standalone
    Python application.
    
    Args:
        agent_dict: Dictionary representation of the agent configuration
        tools_config: List of dictionaries containing tool configurations
        output_dir: Directory to output the built artifact
        version: Semantic version string for the agent package (e.g., "0.1.0")
        mcp_version: Version of the MCP standard to comply with. Different versions
            may generate different server code and API specifications.
        
    Returns:
        Path to the built MCP server package (tarball file)
        
    Example:
        ```python
        # Convert agent to dictionary format
        agent_dict = my_agent.to_dict()
        
        # Extract tool configurations
        tools_config = [tool.to_dict() for tool in my_agent.tools]
        
        # Build MCP server package
        server_path = build_mcp_agent_server(
            agent_dict=agent_dict,
            tools_config=tools_config,
            output_dir="./dist",
            version="1.0.0",
            mcp_version="1.0"
        )
        print(f"MCP server package built at {server_path}")
        ```
    """
    # Create a temporary directory for the build
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write the agent configuration to the temporary directory
        with open(os.path.join(temp_dir, "agent_config.json"), "w") as f:
            json.dump(agent_dict, f, indent=2)
        
        # Write the tools configuration to the temporary directory
        with open(os.path.join(temp_dir, "tools_config.json"), "w") as f:
            json.dump(tools_config, f, indent=2)
        
        # Generate the app.py file
        app_py = generate_mcp_app_py(agent_dict, tools_config, mcp_version)
        with open(os.path.join(temp_dir, "app.py"), "w") as f:
            f.write(app_py)
        
        # Generate the requirements.txt file
        requirements_txt = generate_mcp_requirements_txt(mcp_version)
        with open(os.path.join(temp_dir, "requirements.txt"), "w") as f:
            f.write(requirements_txt)
        
        # Generate the Dockerfile
        dockerfile = generate_mcp_dockerfile()
        with open(os.path.join(temp_dir, "Dockerfile"), "w") as f:
            f.write(dockerfile)
        
        # Generate the OpenAPI spec
        openapi_spec = generate_mcp_openapi_spec(agent_dict, tools_config, mcp_version)
        with open(os.path.join(temp_dir, "openapi.json"), "w") as f:
            json.dump(openapi_spec, f, indent=2)
        
        # Create a README.md
        readme = f"""# MCP-Compatible Agent: {agent_dict.get('name', 'Contexa Agent')}

This is an MCP-compatible agent server generated by the Contexa SDK.

## Agent Description

{agent_dict.get('description', 'No description available.')}

## MCP Version

{mcp_version}

## Available Tools

{len(tools_config)} tools available.

## Deployment

This agent can be deployed as a standalone server using the included Dockerfile.

```
docker build -t mcp-agent .
docker run -p 8000:8000 mcp-agent
```

The agent will be available at http://localhost:8000

## API Documentation

The OpenAPI documentation is available at http://localhost:8000/docs
"""
        with open(os.path.join(temp_dir, "README.md"), "w") as f:
            f.write(readme)
        
        # Package the build
        agent_name = agent_dict.get("name", "agent").lower().replace(" ", "_")
        artifact_name = f"{agent_name}_mcp_{mcp_version}_{version}.tar.gz"
        artifact_path = os.path.join(output_dir, artifact_name)
        
        with tarfile.open(artifact_path, "w:gz") as tar:
            for file_name in os.listdir(temp_dir):
                tar.add(
                    os.path.join(temp_dir, file_name),
                    arcname=file_name,
                    recursive=True
                )
        
        print(f"Built MCP-compatible agent server: {artifact_path}")
        return artifact_path


def _build_regular_agent_package(
    agent_dict: Dict[str, Any],
    tools_config: List[Dict[str, Any]],
    output_dir: str = "./build",
    version: str = "0.1.0",
    include_memory: bool = True,
) -> str:
    """Build a regular (non-MCP) agent package.
    
    This internal function creates a standard agent package containing the agent
    configuration, tool configurations, and optionally memory state. The package
    is a tarball that can be used to restore the agent in another environment or
    be deployed using the Contexa deployment mechanisms.
    
    The standard package is primarily used for:
    - Agent serialization and persistence
    - Agent sharing between environments
    - Deployment to Contexa runtimes
    - Version control of agent configurations
    
    Args:
        agent_dict: Dictionary representation of the agent configuration
        tools_config: List of dictionaries containing tool configurations
        output_dir: Directory to output the built artifact
        version: Semantic version string for the agent package (e.g., "0.1.0")
        include_memory: Whether to include the agent's memory state in the package.
            This is useful for preserving conversation history and other state.
        
    Returns:
        Path to the built agent package (tarball file)
    
    Note:
        This is an internal function used by `build_agent()`. Most users should
        use `build_agent()` directly instead of this function.
    """
    # Create a temporary directory for the build
    with tempfile.TemporaryDirectory() as temp_dir:
        # Write the agent configuration to the temporary directory
        with open(os.path.join(temp_dir, "agent_config.json"), "w") as f:
            json.dump(agent_dict, f, indent=2)
        
        # Write the tools configuration to the temporary directory
        with open(os.path.join(temp_dir, "tools_config.json"), "w") as f:
            json.dump(tools_config, f, indent=2)
        
        # Write the memory to the temporary directory if requested
        if include_memory and "memory" in agent_dict:
            with open(os.path.join(temp_dir, "memory.json"), "w") as f:
                json.dump(agent_dict["memory"], f, indent=2)
        
        # Package the build
        agent_name = agent_dict.get("name", "agent").lower().replace(" ", "_")
        artifact_name = f"{agent_name}_{version}.tar.gz"
        artifact_path = os.path.join(output_dir, artifact_name)
        
        with tarfile.open(artifact_path, "w:gz") as tar:
            for file_name in os.listdir(temp_dir):
                tar.add(
                    os.path.join(temp_dir, file_name),
                    arcname=file_name,
                )
        
        print(f"Built agent package: {artifact_path}")
        return artifact_path 