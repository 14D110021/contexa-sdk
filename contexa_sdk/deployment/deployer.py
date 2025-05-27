"""Deployer module for deploying Contexa agents to Contexa Cloud.

This module provides functionality for deploying packaged Contexa agents to
the Contexa Cloud platform. It handles:

- Uploading agent packages to the deployment service
- Registering MCP-compatible agents in the MCP registry
- Tracking deployment information locally
- Retrieving information about existing deployments

The deployment process creates endpoints that can be accessed via the Contexa API
or directly through MCP-compatible interfaces for MCP agents.

Note: Some functionality in this module currently simulates interactions with
the Contexa Cloud platform, as the actual platform is still under development.
"""

import os
import json
import base64
import hashlib
import re
from typing import Any, Dict, List, Optional, Union

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.config import ContexaConfig


def deploy_agent(
    agent_path: str,
    config: Optional[ContexaConfig] = None,
    register_as_mcp: bool = False,
) -> Dict[str, Any]:
    """Deploy an agent to Contexa Cloud.
    
    This function takes a packaged agent artifact (created with the builder module)
    and deploys it to the Contexa Cloud platform. The deployment process:
    
    1. Verifies the agent package exists
    2. Calculates a checksum to ensure integrity
    3. Uploads the artifact to Contexa Cloud
    4. Registers the agent in the MCP registry if requested or if MCP-compatible
    5. Records deployment information locally
    
    After deployment, the agent will be accessible via an endpoint URL provided
    in the returned deployment information.
    
    Args:
        agent_path: Path to the built agent artifact (.tar.gz) created by the
            builder module. This should be a full path to the artifact file.
        config: Configuration for the deployment containing API credentials, org ID,
            and other settings. If None, a default configuration will be used.
        register_as_mcp: Whether to explicitly register the agent as an MCP server
            in the registry. MCP-compatible agents are automatically registered
            regardless of this setting.
        
    Returns:
        A dictionary containing deployment information including:
        - endpoint_url: URL where the deployed agent can be accessed
        - endpoint_id: Unique identifier for the endpoint
        - version: Version of the deployed agent
        - status: Deployment status
        - created_at: Timestamp of deployment
        - Additional MCP-specific information for MCP agents
        
    Raises:
        FileNotFoundError: If the specified agent artifact file is not found
        
    Example:
        ```python
        from contexa_sdk.deployment import deploy_agent
        from contexa_sdk.core.config import ContexaConfig
        
        # Create a configuration with API credentials
        config = ContexaConfig(
            api_key="your_api_key",
            org_id="your_organization_id"
        )
        
        # Deploy an agent package
        deployment_info = deploy_agent(
            agent_path="./dist/search_agent_1.0.0.tar.gz",
            config=config
        )
        
        # Print the endpoint URL
        print(f"Agent deployed to: {deployment_info['endpoint_url']}")
        
        # Deploy an MCP-compatible agent
        mcp_deployment = deploy_agent(
            agent_path="./dist/search_agent_mcp_1.0_1.0.0.tar.gz",
            config=config
        )
        
        # Print the MCP endpoint
        print(f"MCP endpoint: {mcp_deployment['mcp_endpoint']}")
        ```
    """
    config = config or ContexaConfig()
    
    if not os.path.exists(agent_path):
        raise FileNotFoundError(f"Agent artifact not found: {agent_path}")
        
    # Calculate checksum for the artifact
    sha256_hash = hashlib.sha256()
    with open(agent_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    checksum = sha256_hash.hexdigest()
    
    # Determine if this is an MCP agent
    is_mcp_agent = "_mcp_" in os.path.basename(agent_path)
    
    # Upload the artifact to Contexa Cloud
    deployment_info = _upload_artifact(
        artifact_path=agent_path,
        checksum=checksum,
        config=config,
        is_mcp_agent=is_mcp_agent,
    )
    
    # Register in the MCP registry if requested
    if register_as_mcp or is_mcp_agent:
        _register_in_mcp_registry(
            deployment_info=deployment_info,
            config=config,
        )
    
    # Write deployment info to .ctx/deployments directory
    _write_deployment_info(deployment_info)
    
    return deployment_info


def _upload_artifact(
    artifact_path: str,
    checksum: str,
    config: ContexaConfig,
    is_mcp_agent: bool = False,
) -> Dict[str, Any]:
    """Upload an agent artifact to Contexa Cloud.
    
    This internal function handles the actual upload of the agent artifact to
    the Contexa Cloud platform. It communicates with the deployment API to:
    1. Get a secure upload URL
    2. Upload the artifact
    3. Initiate the deployment process
    
    Args:
        artifact_path: Full path to the agent artifact file to upload
        checksum: SHA-256 checksum of the artifact for integrity verification
        config: Configuration containing API credentials and organization ID
        is_mcp_agent: Boolean flag indicating if this is an MCP-compatible agent
        
    Returns:
        A dictionary containing deployment information including endpoint URLs
        and deployment status
        
    Note:
        This function currently simulates the upload process as the actual
        Contexa Cloud platform is still under development.
    """
    import httpx
    
    # Extract the artifact name from the path
    artifact_name = os.path.basename(artifact_path)
    
    # Get the upload URL
    url = f"{config.api_url}/deployments/upload-url"
    headers = {
        "Content-Type": "application/json",
    }
    
    if config.api_key:
        headers["Authorization"] = f"Bearer {config.api_key}"
        
    payload = {
        "artifact_name": artifact_name,
        "checksum": checksum,
        "org_id": config.org_id,
        "is_mcp_agent": is_mcp_agent,
    }
    
    # This is just a simulation since we don't have a real Contexa API yet
    # In a real implementation, this would make an HTTP request to get a signed upload URL
    print(f"Getting upload URL for {artifact_name}...")
    
    # Extract MCP version if present
    mcp_version = None
    if is_mcp_agent:
        # Pattern like name_mcp_1.0_version.tar.gz
        match = re.search(r"_mcp_([0-9.]+)_", artifact_name)
        if match:
            mcp_version = match.group(1)
    
    # Simulate a Contexa Cloud endpoint
    endpoint_name = artifact_name.split(".")[0]
    endpoint_url = f"https://api.contexa.ai/v0/ctx/{config.org_id or 'default'}/{endpoint_name}"
    
    # For MCP agents, use a different URL format
    if is_mcp_agent:
        endpoint_url = f"https://api.contexa.ai/v0/mcp/{config.org_id or 'default'}/{endpoint_name}"
    
    deployment_info = {
        "endpoint_url": endpoint_url,
        "endpoint_id": f"ctx://{config.org_id or 'default'}/{endpoint_name}",
        "version": "0.1.0",
        "checksum": checksum,
        "artifact_name": artifact_name,
        "status": "deployed",
        "created_at": "2023-06-01T00:00:00Z",
    }
    
    # Add MCP-specific information if applicable
    if is_mcp_agent:
        deployment_info["is_mcp_agent"] = True
        deployment_info["mcp_version"] = mcp_version or "1.0"
        deployment_info["mcp_endpoint"] = f"mcp://{config.org_id or 'default'}/{endpoint_name}"
    
    return deployment_info


def _register_in_mcp_registry(
    deployment_info: Dict[str, Any],
    config: ContexaConfig,
) -> None:
    """Register an agent in the MCP registry.
    
    This internal function handles registering an MCP-compatible agent in the
    Machine Communication Protocol (MCP) registry. Registration makes the agent
    discoverable by other MCP-compatible systems.
    
    The registration process includes:
    1. Extracting the OpenAPI spec from the deployed agent
    2. Extracting MCP metadata
    3. Registering the agent with appropriate tags and metadata
    
    Args:
        deployment_info: Dictionary containing deployment information for the agent
        config: Configuration containing API credentials and organization ID
        
    Note:
        This function currently simulates the registration process as the actual
        MCP registry is still under development.
    """
    # This is a simulation - in a real implementation, this would
    # make a request to the MCP registry service to register the agent
    print(f"Registering agent in MCP registry: {deployment_info['endpoint_id']}")
    
    # In a real implementation, this would:
    # 1. Fetch the OpenAPI spec from the deployed agent
    # 2. Extract MCP metadata
    # 3. Register in the MCP registry with appropriate tags and metadata
    
    # For now, just add some information to the deployment info
    deployment_info["mcp_registry"] = {
        "registered": True,
        "registry_url": f"{config.api_url}/mcp/registry",
        "registry_id": f"mcp-{deployment_info['endpoint_id'].split('://')[-1]}",
    }
    

def _write_deployment_info(deployment_info: Dict[str, Any]) -> None:
    """Write deployment information to local storage.
    
    This internal function saves deployment information to the local filesystem
    in a .ctx/deployments directory. This information can be later retrieved
    using the list_deployments() and get_deployment() functions.
    
    Args:
        deployment_info: Dictionary containing deployment information to save
    """
    # Create the deployments directory if it doesn't exist
    deployments_dir = os.path.join(os.getcwd(), ".ctx", "deployments")
    os.makedirs(deployments_dir, exist_ok=True)
    
    # Write the deployment info
    deployment_path = os.path.join(
        deployments_dir, 
        f"{deployment_info['endpoint_id'].replace('://', '_').replace('/', '_')}.json"
    )
    
    with open(deployment_path, "w") as f:
        json.dump(deployment_info, f, indent=2)
        
    print(f"Deployment info written to {deployment_path}")
    print(f"Endpoint URL: {deployment_info['endpoint_url']}")
    print(f"Endpoint ID: {deployment_info['endpoint_id']}")
    
    # Print MCP-specific information if available
    if deployment_info.get("is_mcp_agent"):
        print(f"MCP Endpoint: {deployment_info['mcp_endpoint']}")
        print(f"MCP Version: {deployment_info['mcp_version']}")
        if "mcp_registry" in deployment_info:
            print(f"Registered in MCP Registry: {deployment_info['mcp_registry']['registry_url']}")


def list_deployments(mcp_only: bool = False) -> List[Dict[str, Any]]:
    """List all agent deployments from local storage.
    
    This function retrieves information about all previously deployed agents
    from the local .ctx/deployments directory. It can optionally filter to
    show only MCP-compatible agent deployments.
    
    Args:
        mcp_only: If True, only returns information about MCP-compatible agent
            deployments. If False (default), returns information about all
            deployments.
        
    Returns:
        A list of dictionaries, each containing deployment information for
        a previously deployed agent.
        
    Example:
        ```python
        from contexa_sdk.deployment import list_deployments
        
        # List all deployments
        all_deployments = list_deployments()
        for deployment in all_deployments:
            print(f"Agent: {deployment['endpoint_id']}")
            print(f"  URL: {deployment['endpoint_url']}")
            print(f"  Status: {deployment['status']}")
            
        # List only MCP-compatible deployments
        mcp_deployments = list_deployments(mcp_only=True)
        for deployment in mcp_deployments:
            print(f"MCP Agent: {deployment['endpoint_id']}")
            print(f"  MCP Endpoint: {deployment['mcp_endpoint']}")
        ```
    """
    deployments_dir = os.path.join(os.getcwd(), ".ctx", "deployments")
    if not os.path.exists(deployments_dir):
        return []
        
    deployments = []
    for filename in os.listdir(deployments_dir):
        if filename.endswith(".json"):
            with open(os.path.join(deployments_dir, filename), "r") as f:
                deployment = json.load(f)
                # Filter by MCP if requested
                if mcp_only and not deployment.get("is_mcp_agent", False):
                    continue
                deployments.append(deployment)
                
    return deployments


def list_mcp_agents() -> List[Dict[str, Any]]:
    """List all MCP-compatible agent deployments.
    
    This function is a convenience wrapper around list_deployments(mcp_only=True)
    that returns information only about MCP-compatible agent deployments.
    
    Returns:
        A list of dictionaries, each containing deployment information for
        a previously deployed MCP-compatible agent.
        
    Example:
        ```python
        from contexa_sdk.deployment import list_mcp_agents
        
        # List all MCP-compatible deployments
        mcp_agents = list_mcp_agents()
        for agent in mcp_agents:
            print(f"MCP Agent: {agent['endpoint_id']}")
            print(f"  Version: {agent['mcp_version']}")
            print(f"  Endpoint: {agent['mcp_endpoint']}")
        ```
    """
    return list_deployments(mcp_only=True)


def get_deployment(endpoint_id: str) -> Optional[Dict[str, Any]]:
    """Get deployment information for a specific endpoint.
    
    This function retrieves deployment information for a specific endpoint ID
    from the local .ctx/deployments directory.
    
    Args:
        endpoint_id: The endpoint ID to retrieve information for. This should
            be in the format "ctx://org_id/endpoint_name" or similar.
        
    Returns:
        A dictionary containing deployment information, or None if the specified
        endpoint ID is not found.
        
    Example:
        ```python
        from contexa_sdk.deployment import get_deployment
        
        # Get information about a specific deployment
        deployment = get_deployment("ctx://my_org/search_agent_1.0.0")
        
        if deployment:
            print(f"Agent: {deployment['endpoint_id']}")
            print(f"  URL: {deployment['endpoint_url']}")
            print(f"  Status: {deployment['status']}")
            print(f"  Created: {deployment['created_at']}")
        else:
            print("Deployment not found")
        ```
    """
    deployments_dir = os.path.join(os.getcwd(), ".ctx", "deployments")
    if not os.path.exists(deployments_dir):
        return None
        
    filename = f"{endpoint_id.replace('://', '_').replace('/', '_')}.json"
    deployment_path = os.path.join(deployments_dir, filename)
    
    if not os.path.exists(deployment_path):
        return None
        
    with open(deployment_path, "r") as f:
        return json.load(f) 