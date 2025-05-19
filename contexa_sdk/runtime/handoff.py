"""Agent handoff functionality for Contexa SDK.

This module enables cross-framework handoffs between agents, allowing
seamless integration of different agent frameworks in a unified workflow.
"""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.observability.tracer import trace, SpanKind


# Create logger for this module
logger = logging.getLogger(__name__)


async def handoff(
    from_agent: Any,
    to_agent: Any,
    message: str,
    context: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    timeout: Optional[float] = None
) -> Any:
    """Handoff control from one agent to another.
    
    This function enables passing control from one agent to another,
    regardless of which framework they are built on. The handoff includes
    the message and optional context/metadata.
    
    Args:
        from_agent: Source agent initiating the handoff
        to_agent: Target agent to receive control
        message: Message to pass to the target agent
        context: Optional context data to include in the handoff
        metadata: Optional metadata about the handoff
        timeout: Optional timeout in seconds
        
    Returns:
        Result from the target agent
        
    Raises:
        TypeError: If the agent types are not supported
        TimeoutError: If the handoff times out
    """
    # Prepare context and metadata
    context = context or {}
    metadata = metadata or {}
    
    # Add handoff tracking info
    handoff_id = str(uuid.uuid4())
    metadata["handoff_id"] = handoff_id
    
    # Log the handoff
    logger.info(
        f"Handoff initiated: {handoff_id} - "
        f"From {getattr(from_agent, 'name', str(from_agent))} "
        f"to {getattr(to_agent, 'name', str(to_agent))}"
    )
    
    # Handle ContexaAgent handoffs directly
    if isinstance(from_agent, ContexaAgent) and isinstance(to_agent, ContexaAgent):
        handoff_data = from_agent.prepare_handoff_data(message, context, metadata)
        to_agent.receive_handoff(handoff_data)
        
        # Format the result and provide it to the target agent  
        if timeout:
            # Run with timeout
            try:
                return await asyncio.wait_for(to_agent.run(message), timeout)
            except asyncio.TimeoutError:
                logger.error(f"Handoff timed out after {timeout} seconds")
                raise TimeoutError(f"Handoff timed out after {timeout} seconds")
        else:
            # Run without timeout
            return await to_agent.run(message)
            
    # Handle framework-specific agents
    # This section handles different patterns in framework-specific agent implementations
    
    # Get common run methods for various frameworks
    run_methods = [
        # Method pattern, args, kwargs
        (getattr(to_agent, "run", None), [message], {}),
        (getattr(to_agent, "invoke", None), [message], {}),
        (getattr(to_agent, "execute", None), [message], {}),
        (getattr(to_agent, "__call__", None), [message], {})
    ]
    
    # Try each method until one works
    for method, args, kwargs in run_methods:
        if callable(method):
            try:
                # Check if it's an async method
                if asyncio.iscoroutinefunction(method):
                    if timeout:
                        return await asyncio.wait_for(method(*args, **kwargs), timeout)
                    else:
                        result = await method(*args, **kwargs)
                        # Check if the result is a Future
                        if isinstance(result, asyncio.Future):
                            return await result
                        return result
                else:
                    # Synchronous method
                    return method(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Method {method.__name__} failed: {str(e)}")
                continue
    
    # If we get here, no method worked
    raise TypeError(
        f"Unsupported agent types for handoff: "
        f"{type(from_agent).__name__} to {type(to_agent).__name__}"
    ) 