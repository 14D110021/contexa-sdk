"""Unit tests for the resource tracking module."""

import pytest
import unittest.mock as mock
from typing import Dict, Any

from contexa_sdk.runtime.resource_tracking import (
    ResourceTracker, 
    ResourceUsage, 
    ResourceLimits, 
    ResourceType,
    ResourceConstraintViolation
)


class TestResourceTracker:
    """Test the ResourceTracker class."""

    def test_init(self):
        """Test that ResourceTracker initializes correctly."""
        tracker = ResourceTracker()
        assert tracker is not None
        assert isinstance(tracker, ResourceTracker)
    
    def test_resource_limits_init(self):
        """Test that ResourceLimits initializes correctly."""
        limits = ResourceLimits(
            max_memory_mb=1024,
            max_tokens_per_minute=10000,
            max_concurrent_requests=5
        )
        assert limits.max_memory_mb == 1024
        assert limits.max_tokens_per_minute == 10000
        assert limits.max_concurrent_requests == 5
    
    def test_resource_usage_init(self):
        """Test that ResourceUsage initializes correctly."""
        usage = ResourceUsage(
            memory_mb=512,
            tokens_used_last_minute=5000,
            concurrent_requests=3
        )
        assert usage.memory_mb == 512
        assert usage.tokens_used_last_minute == 5000
        assert usage.concurrent_requests == 3
    
    @pytest.mark.asyncio
    async def test_track_resource_usage(self):
        """Test tracking resource usage."""
        tracker = ResourceTracker()
        
        # Mock the internal methods that would calculate resource usage
        with mock.patch.object(tracker, '_calculate_memory_usage', return_value=512):
            with mock.patch.object(tracker, '_calculate_token_usage', return_value=5000):
                with mock.patch.object(tracker, '_calculate_concurrent_requests', return_value=3):
                    # Track an agent's resource usage
                    usage = await tracker.track_resource_usage("agent-123")
                    
                    # Verify the usage reports
                    assert usage.memory_mb == 512
                    assert usage.tokens_used_last_minute == 5000
                    assert usage.concurrent_requests == 3
    
    @pytest.mark.asyncio
    async def test_check_resource_limits(self):
        """Test checking resource limits."""
        tracker = ResourceTracker()
        
        # Create resource limits
        limits = ResourceLimits(
            max_memory_mb=1024,
            max_tokens_per_minute=10000,
            max_concurrent_requests=5
        )
        
        # Set up current usage
        usage = ResourceUsage(
            memory_mb=512,
            tokens_used_last_minute=5000,
            concurrent_requests=3
        )
        
        # Mock the track_resource_usage method
        with mock.patch.object(tracker, 'track_resource_usage', return_value=usage):
            # This should not raise an exception
            await tracker.check_resource_limits("agent-123", limits)
            
            # Now test with usage exceeding limits
            usage.memory_mb = 2048  # Exceeds max_memory_mb
            
            # This should raise a ResourceConstraintViolation
            with pytest.raises(ResourceConstraintViolation):
                await tracker.check_resource_limits("agent-123", limits)
    
    @pytest.mark.asyncio
    async def test_register_agent(self):
        """Test registering an agent with resource limits."""
        tracker = ResourceTracker()
        
        # Create resource limits
        limits = ResourceLimits(
            max_memory_mb=1024,
            max_tokens_per_minute=10000,
            max_concurrent_requests=5
        )
        
        # Register an agent
        tracker.register_agent("agent-123", limits)
        
        # Verify the agent is registered with the given limits
        assert "agent-123" in tracker._agent_limits
        assert tracker._agent_limits["agent-123"] == limits
    
    @pytest.mark.asyncio
    async def test_unregister_agent(self):
        """Test unregistering an agent."""
        tracker = ResourceTracker()
        
        # Create resource limits
        limits = ResourceLimits(
            max_memory_mb=1024,
            max_tokens_per_minute=10000,
            max_concurrent_requests=5
        )
        
        # Register an agent
        tracker.register_agent("agent-123", limits)
        
        # Verify the agent is registered
        assert "agent-123" in tracker._agent_limits
        
        # Unregister the agent
        tracker.unregister_agent("agent-123")
        
        # Verify the agent is no longer registered
        assert "agent-123" not in tracker._agent_limits 