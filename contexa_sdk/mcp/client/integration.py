"""
MCP Client Integration for seamless Contexa agent integration.

This module provides classes and functions for automatic conversion of Contexa
agents to MCP servers and seamless integration with existing MCP infrastructure.
It enables one-line agent-to-MCP conversion with automatic capability mapping.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set, Union
from dataclasses import dataclass, field

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.prompt import ContexaPrompt
from contexa_sdk.mcp.server import MCPServer, MCPServerConfig

logger = logging.getLogger(__name__)


@dataclass
class MCPIntegrationConfig:
    """Configuration for MCP integration."""
    server_name: Optional[str] = None
    server_description: Optional[str] = None
    transport_type: str = "stdio"  # "stdio", "http", "sse"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Capability mapping
    auto_map_tools: bool = True
    auto_map_prompts: bool = True
    auto_create_resources: bool = True
    
    # Resource configuration
    create_agent_info_resource: bool = True
    create_tool_list_resource: bool = True
    create_capability_resource: bool = True
    
    # Advanced options
    enable_tool_history: bool = True
    enable_prompt_validation: bool = True
    enable_resource_subscriptions: bool = False
    
    # Logging and monitoring
    enable_integration_logging: bool = True
    log_tool_executions: bool = True
    log_resource_access: bool = False


class MCPIntegration:
    """
    Automatic integration of Contexa agents with MCP servers.
    
    This class provides seamless conversion of Contexa agents to MCP-compatible
    servers with automatic capability mapping, resource creation, and
    configuration management.
    """
    
    def __init__(self, config: Optional[MCPIntegrationConfig] = None):
        self.config = config or MCPIntegrationConfig()
        self.logger = logging.getLogger(f"{__name__}.MCPIntegration")
        
        # Integration state
        self.integrated_agents: Dict[str, ContexaAgent] = {}
        self.created_servers: Dict[str, MCPServer] = {}
        self.capability_mappings: Dict[str, Dict[str, Any]] = {}
        
    async def integrate_agent(
        self, 
        agent: ContexaAgent, 
        agent_name: Optional[str] = None
    ) -> MCPServer:
        """
        Integrate a Contexa agent as an MCP server.
        
        This method automatically converts a Contexa agent into a fully
        functional MCP server with proper capability mapping and resource
        creation.
        
        Args:
            agent: The Contexa agent to integrate
            agent_name: Optional name for the agent (defaults to agent.name)
            
        Returns:
            MCPServer instance ready to be started
            
        Raises:
            ValueError: If agent integration fails
            RuntimeError: If server creation fails
        """
        agent_name = agent_name or agent.name or f"agent_{len(self.integrated_agents)}"
        
        try:
            self.logger.info(f"Starting integration of agent: {agent_name}")
            
            # Extract agent capabilities
            capabilities = await self._extract_agent_capabilities(agent)
            
            # Create MCP server configuration
            server_config = await self._create_server_config(agent, agent_name, capabilities)
            
            # Create MCP server
            server = MCPServer(server_config)
            
            # Register agent with server
            await server.register_agent(agent, agent_name)
            
            # Create additional resources
            if self.config.auto_create_resources:
                await self._create_agent_resources(server, agent, agent_name, capabilities)
            
            # Store integration state
            self.integrated_agents[agent_name] = agent
            self.created_servers[agent_name] = server
            self.capability_mappings[agent_name] = capabilities
            
            self.logger.info(f"Successfully integrated agent: {agent_name}")
            return server
            
        except Exception as e:
            self.logger.error(f"Failed to integrate agent {agent_name}: {str(e)}")
            raise RuntimeError(f"Agent integration failed: {str(e)}") from e
    
    async def _extract_agent_capabilities(self, agent: ContexaAgent) -> Dict[str, Any]:
        """Extract capabilities from a Contexa agent."""
        capabilities = {
            "tools": [],
            "prompts": [],
            "resources": [],
            "model_info": {},
            "metadata": {}
        }
        
        # Extract tool capabilities
        if self.config.auto_map_tools and agent.tools:
            for tool in agent.tools:
                tool_info = {
                    "name": tool.name,
                    "description": tool.description or f"Tool: {tool.name}",
                    "parameters": getattr(tool, 'parameters_schema', {}),
                    "type": "function"
                }
                capabilities["tools"].append(tool_info)
        
        # Extract model information
        if agent.model:
            capabilities["model_info"] = {
                "provider": getattr(agent.model, 'provider', 'unknown'),
                "model_name": getattr(agent.model, 'model_name', 'unknown'),
                "capabilities": ["text_generation"]
            }
        
        # Extract agent metadata
        capabilities["metadata"] = {
            "name": agent.name,
            "description": agent.description,
            "system_prompt": getattr(agent, 'system_prompt', None),
            "tool_count": len(agent.tools) if agent.tools else 0,
            "created_by": "contexa_sdk_integration"
        }
        
        self.logger.debug(f"Extracted capabilities: {len(capabilities['tools'])} tools")
        return capabilities
    
    async def _create_server_config(
        self, 
        agent: ContexaAgent, 
        agent_name: str, 
        capabilities: Dict[str, Any]
    ) -> MCPServerConfig:
        """Create MCP server configuration for the agent."""
        server_name = self.config.server_name or f"MCP Server for {agent_name}"
        server_description = (
            self.config.server_description or 
            f"MCP server exposing {agent_name} capabilities"
        )
        
        config = MCPServerConfig(
            name=server_name,
            description=server_description,
            transport_type=self.config.transport_type,
            host=self.config.host,
            port=self.config.port,
            enable_sampling=True,
            enable_resource_subscriptions=self.config.enable_resource_subscriptions,
            enable_logging=self.config.enable_integration_logging
        )
        
        return config
    
    async def _create_agent_resources(
        self, 
        server: MCPServer, 
        agent: ContexaAgent, 
        agent_name: str, 
        capabilities: Dict[str, Any]
    ):
        """Create additional resources for the agent."""
        resource_handler = server.handlers["resource"]
        
        # Create agent info resource
        if self.config.create_agent_info_resource:
            from contexa_sdk.mcp.server.handlers import MCPResource
            
            agent_info_resource = MCPResource(
                uri=f"agent://{agent_name}/info",
                name=f"{agent_name} Information",
                description=f"Detailed information about {agent_name}",
                mime_type="application/json"
            )
            
            agent_info_content = {
                "name": agent_name,
                "description": agent.description,
                "capabilities": capabilities,
                "status": "active",
                "integration_time": asyncio.get_event_loop().time()
            }
            
            await resource_handler.register_resource(agent_info_resource, agent_info_content)
        
        # Create tool list resource
        if self.config.create_tool_list_resource and capabilities["tools"]:
            tool_list_resource = MCPResource(
                uri=f"agent://{agent_name}/tools",
                name=f"{agent_name} Tools",
                description=f"List of tools available in {agent_name}",
                mime_type="application/json"
            )
            
            tool_list_content = {
                "tools": capabilities["tools"],
                "count": len(capabilities["tools"]),
                "last_updated": asyncio.get_event_loop().time()
            }
            
            await resource_handler.register_resource(tool_list_resource, tool_list_content)
        
        # Create capability resource
        if self.config.create_capability_resource:
            capability_resource = MCPResource(
                uri=f"agent://{agent_name}/capabilities",
                name=f"{agent_name} Capabilities",
                description=f"Full capability matrix for {agent_name}",
                mime_type="application/json"
            )
            
            await resource_handler.register_resource(capability_resource, capabilities)
    
    async def start_server(self, agent_name: str) -> None:
        """Start the MCP server for an integrated agent."""
        if agent_name not in self.created_servers:
            raise ValueError(f"No server found for agent: {agent_name}")
        
        server = self.created_servers[agent_name]
        await server.start()
        
        self.logger.info(f"Started MCP server for agent: {agent_name}")
    
    async def stop_server(self, agent_name: str) -> None:
        """Stop the MCP server for an integrated agent."""
        if agent_name not in self.created_servers:
            raise ValueError(f"No server found for agent: {agent_name}")
        
        server = self.created_servers[agent_name]
        await server.stop()
        
        self.logger.info(f"Stopped MCP server for agent: {agent_name}")
    
    async def stop_all_servers(self) -> None:
        """Stop all integrated MCP servers."""
        for agent_name in list(self.created_servers.keys()):
            await self.stop_server(agent_name)
        
        self.logger.info("Stopped all integrated MCP servers")
    
    def get_server(self, agent_name: str) -> Optional[MCPServer]:
        """Get the MCP server for an integrated agent."""
        return self.created_servers.get(agent_name)
    
    def get_integration_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get integration information for an agent."""
        if agent_name not in self.integrated_agents:
            return None
        
        server = self.created_servers.get(agent_name)
        return {
            "agent": self.integrated_agents[agent_name],
            "server": server,
            "capabilities": self.capability_mappings.get(agent_name, {}),
            "server_info": server.get_server_info() if server else None,
            "running": server.running if server else False
        }
    
    def list_integrated_agents(self) -> List[str]:
        """List all integrated agent names."""
        return list(self.integrated_agents.keys())


async def integrate_mcp_server_with_agent(
    agent: ContexaAgent,
    config: Optional[MCPIntegrationConfig] = None,
    agent_name: Optional[str] = None,
    auto_start: bool = False
) -> MCPServer:
    """
    Convenience function for one-line agent-to-MCP integration.
    
    This function provides a simple way to convert a Contexa agent into
    an MCP server with sensible defaults and automatic configuration.
    
    Args:
        agent: The Contexa agent to integrate
        config: Optional integration configuration
        agent_name: Optional name for the agent
        auto_start: Whether to automatically start the server
        
    Returns:
        MCPServer instance ready to use
        
    Example:
        ```python
        from contexa_sdk.core.agent import ContexaAgent
        from contexa_sdk.mcp.client.integration import integrate_mcp_server_with_agent
        
        # Create your agent
        agent = ContexaAgent(name="MyAgent", tools=[...])
        
        # One-line integration
        server = await integrate_mcp_server_with_agent(agent, auto_start=True)
        
        # Server is now running and exposing agent capabilities via MCP
        ```
        
    Raises:
        ValueError: If agent is invalid
        RuntimeError: If integration fails
    """
    if not agent:
        raise ValueError("Agent cannot be None")
    
    if not agent.name and not agent_name:
        raise ValueError("Agent must have a name or agent_name must be provided")
    
    try:
        # Create integration instance
        integration = MCPIntegration(config)
        
        # Integrate the agent
        server = await integration.integrate_agent(agent, agent_name)
        
        # Auto-start if requested
        if auto_start:
            await server.start()
            logger.info(f"Auto-started MCP server for agent: {agent_name or agent.name}")
        
        return server
        
    except Exception as e:
        logger.error(f"Failed to integrate agent: {str(e)}")
        raise


async def create_multi_agent_mcp_server(
    agents: List[ContexaAgent],
    config: Optional[MCPIntegrationConfig] = None,
    server_name: Optional[str] = None
) -> MCPServer:
    """
    Create a single MCP server that exposes multiple agents.
    
    This function creates one MCP server that can handle requests for
    multiple agents, useful for agent teams or multi-agent systems.
    
    Args:
        agents: List of Contexa agents to integrate
        config: Optional integration configuration
        server_name: Optional name for the multi-agent server
        
    Returns:
        MCPServer instance with all agents integrated
        
    Raises:
        ValueError: If agents list is empty or invalid
        RuntimeError: If integration fails
    """
    if not agents:
        raise ValueError("Agents list cannot be empty")
    
    try:
        # Create integration config
        integration_config = config or MCPIntegrationConfig()
        if server_name:
            integration_config.server_name = server_name
        else:
            agent_names = [agent.name for agent in agents if agent.name]
            integration_config.server_name = f"Multi-Agent MCP Server ({', '.join(agent_names)})"
        
        # Create integration instance
        integration = MCPIntegration(integration_config)
        
        # Integrate first agent to create the server
        primary_server = await integration.integrate_agent(agents[0])
        
        # Register additional agents with the same server
        for agent in agents[1:]:
            await primary_server.register_agent(agent)
        
        logger.info(f"Created multi-agent MCP server with {len(agents)} agents")
        return primary_server
        
    except Exception as e:
        logger.error(f"Failed to create multi-agent MCP server: {str(e)}")
        raise 