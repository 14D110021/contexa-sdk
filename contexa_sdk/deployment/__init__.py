"""Deployment module for Contexa SDK.

This module provides tools for building, packaging, and deploying Contexa agents
to various environments. It includes:

Builder Components:
- build_agent: Main function for packaging agents into deployable artifacts
- build_mcp_agent_server: Creates MCP-compatible server packages

Deployment Components:
- deploy_agent: Deploys packaged agents to Contexa Cloud
- list_deployments: Lists all deployed agents
- list_mcp_agents: Lists all MCP-compatible agent deployments
- get_deployment: Retrieves information about a specific deployment

MCP Generator Components:
- generate_mcp_app_py: Generates server code for MCP-compatible agents
- generate_mcp_requirements_txt: Creates dependency specifications
- generate_mcp_dockerfile: Generates Docker configuration for containerization
- generate_mcp_openapi_spec: Creates OpenAPI specifications for API documentation

The deployment workflow typically involves:
1. Building an agent package with build_agent()
2. Deploying the package with deploy_agent()
3. Retrieving the endpoint information with get_deployment()

Example:
    ```python
    from contexa_sdk.deployment import build_agent, deploy_agent
    
    # Build an agent package
    package_path = build_agent(my_agent, version="1.0.0")
    
    # Deploy the package
    deployment = deploy_agent(package_path)
    
    # Print the endpoint URL
    print(f"Agent available at: {deployment['endpoint_url']}")
    ```
"""

from contexa_sdk.deployment.builder import build_agent, build_mcp_agent_server
from contexa_sdk.deployment.deployer import (
    deploy_agent,
    list_deployments,
    list_mcp_agents,
    get_deployment,
)
from contexa_sdk.deployment.mcp_generator import (
    generate_mcp_app_py,
    generate_mcp_requirements_txt,
    generate_mcp_dockerfile,
    generate_mcp_openapi_spec,
)

__all__ = [
    "build_agent",
    "build_mcp_agent_server",
    "deploy_agent",
    "list_deployments",
    "list_mcp_agents",
    "get_deployment",
    "generate_mcp_app_py",
    "generate_mcp_requirements_txt",
    "generate_mcp_dockerfile",
    "generate_mcp_openapi_spec",
] 