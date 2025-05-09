"""Deployer module for deploying Contexa agents to Contexa Cloud."""

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
    
    Args:
        agent_path: Path to the built agent artifact (.tar.gz)
        config: Configuration for the deployment
        register_as_mcp: Whether to register the agent as an MCP server in the registry
        
    Returns:
        Deployment information including the endpoint URL
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
    """Upload an artifact to Contexa Cloud.
    
    Args:
        artifact_path: Path to the artifact to upload
        checksum: SHA-256 checksum of the artifact
        config: Configuration for the upload
        is_mcp_agent: Whether the artifact is an MCP-compatible agent
        
    Returns:
        Deployment information including the endpoint URL
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
    
    Args:
        deployment_info: Deployment information for the agent
        config: Configuration for the registration
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
    """Write deployment info to .ctx/deployments directory.
    
    Args:
        deployment_info: Deployment information to write
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
    """List all deployments.
    
    Args:
        mcp_only: Whether to only list MCP-compatible deployments
        
    Returns:
        List of deployment information dictionaries
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
    
    Returns:
        List of MCP agent deployment information dictionaries
    """
    return list_deployments(mcp_only=True)


def get_deployment(endpoint_id: str) -> Optional[Dict[str, Any]]:
    """Get deployment information for an endpoint.
    
    Args:
        endpoint_id: Endpoint ID to get information for
        
    Returns:
        Deployment information or None if not found
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