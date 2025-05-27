"""
CodeMaster Pro - Contexa SDK Implementation

This module implements the CodeMaster Pro coding assistant using the Contexa SDK.
This demonstrates the conversion from OpenAI to Contexa format,
showcasing the "write once, run anywhere" capability.

Author: Rupesh Raj
Created: May 2025
"""

import asyncio
import json
import logging
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import Contexa SDK components
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../..'))
from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel

# Import our custom tools
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools.context7_tool import Context7Tool, Context7Input, Context7Output
from tools.exa_search_tool import ExaSearchTool, ExaSearchInput, ExaSearchOutput

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for agent execution."""
    start_time: float
    end_time: float
    total_duration: float
    tool_calls: int
    tokens_used: int
    cost_estimate: float


class CodeMasterContexta:
    """
    CodeMaster Pro implementation using Contexa SDK.
    
    This agent provides the same functionality as the OpenAI version but uses
    the Contexa SDK for cross-framework compatibility and standardized tool integration.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1",
        temperature: float = 0.1,
        max_tokens: int = 4000
    ):
        """
        Initialize the CodeMaster Pro Contexa agent.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4.1)
            temperature: Temperature for generation
            max_tokens: Maximum tokens per response
        """
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize tools using Contexa format
        self.context7_tool = self._create_context7_contexa_tool()
        self.exa_tool = self._create_exa_contexa_tool()
        
        # Create Contexa model
        from contexa_sdk.core.config import ContexaConfig
        config = ContexaConfig(api_key=api_key)
        self.model = ContexaModel(
            model_name=model,
            provider="openai",
            config=config
        )
        
        # Create Contexa agent
        self.agent = ContexaAgent(
            tools=[self.context7_tool, self.exa_tool],
            model=self.model,
            name="CodeMaster Pro",
            description="Advanced coding assistant with MCP tool integration",
            system_prompt="""You are CodeMaster Pro, an advanced coding assistant with access to real-time documentation and web search capabilities.

Your capabilities include:
- 📚 Real-time library documentation lookup via Context7
- 🔍 Intelligent web search for technical content via Exa
- 💻 Code generation, analysis, and optimization
- 🛠️ Development workflow guidance and best practices

When helping users:
1. Use your tools to find the most current and accurate information
2. Provide practical, working code examples
3. Explain concepts clearly with proper context
4. Reference official documentation when available
5. Suggest best practices and modern approaches

Always be helpful, accurate, and thorough in your responses."""
        )
        
        # Performance tracking
        self.metrics: List[PerformanceMetrics] = []
        
    def _create_context7_contexa_tool(self) -> ContexaTool:
        """
        Create a Contexa-compatible Context7 tool.
        
        Returns:
            ContexaTool instance for Context7 documentation lookup
        """
        async def context7_lookup(inputs) -> Dict[str, Any]:
            """
            Look up documentation for a library or framework.
            
            Args:
                inputs: Context7Input with library_name, topic, max_tokens
                
            Returns:
                Dictionary containing documentation results
            """
            tool = Context7Tool()
            result = await tool.execute(inputs)
            
            return {
                "success": result.success,
                "content": result.content,
                "library_id": result.library_id,
                "tokens_used": result.tokens_used,
                "error": result.error_message
            }
        
        return ContexaTool(
            func=context7_lookup,
            name="context7_docs",
            description="Retrieve up-to-date documentation for libraries and frameworks",
            schema=Context7Input
        )
    
    def _create_exa_contexa_tool(self) -> ContexaTool:
        """
        Create a Contexa-compatible Exa search tool.
        
        Returns:
            ContexaTool instance for Exa web search
        """
        async def exa_search(inputs) -> Dict[str, Any]:
            """
            Search the web for technical content.
            
            Args:
                inputs: ExaSearchInput with query, num_results, etc.
                
            Returns:
                Dictionary containing search results
            """
            tool = ExaSearchTool()
            result = await tool.execute(inputs)
            
            return {
                "success": result.success,
                "query": result.query,
                "results": [
                    {
                        "title": r.title,
                        "url": r.url,
                        "content": r.content,
                        "score": r.score
                    }
                    for r in result.results
                ],
                "total_results": result.total_results,
                "error": result.error_message
            }
        
        return ContexaTool(
            func=exa_search,
            name="exa_web_search",
            description="Search the web for technical content and solutions using Exa's intelligent search",
            schema=ExaSearchInput
        )
    
    async def process_message(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response using Contexa SDK.
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary containing the response and metadata
        """
        start_time = time.time()
        
        try:
            # Use the Contexa agent directly
            result = await self.agent.run(user_message)
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Extract metrics (simplified for demo)
            tool_calls = 0  # Would be tracked by Contexa SDK
            tokens_used = len(user_message.split()) + len(str(result).split())  # Rough estimate
            cost_estimate = (tokens_used / 1000) * 0.03
            
            # Store metrics
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                total_duration=duration,
                tool_calls=tool_calls,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate
            )
            self.metrics.append(metrics)
            
            return {
                "response": str(result),
                "success": True,
                "metrics": {
                    "duration": duration,
                    "tool_calls": tool_calls,
                    "tokens_used": tokens_used,
                    "cost_estimate": cost_estimate
                },
                "conversation_id": len(self.metrics),
                "framework": "contexa_sdk"
            }
            
        except Exception as e:
            logger.error(f"Error processing message with Contexa SDK: {e}")
            end_time = time.time()
            
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "success": False,
                "metrics": {
                    "duration": end_time - start_time,
                    "tool_calls": 0,
                    "tokens_used": 0,
                    "cost_estimate": 0
                },
                "error": str(e),
                "framework": "contexa_sdk"
            }
    
    async def chat(self, message: str) -> str:
        """
        Simple chat interface for the agent.
        
        Args:
            message: User message
            
        Returns:
            Agent response
        """
        result = await self.process_message(message)
        return result["response"]
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get a summary of performance metrics.
        
        Returns:
            Dictionary containing performance statistics
        """
        if not self.metrics:
            return {"message": "No metrics available"}
        
        total_duration = sum(m.total_duration for m in self.metrics)
        total_tool_calls = sum(m.tool_calls for m in self.metrics)
        total_tokens = sum(m.tokens_used for m in self.metrics)
        total_cost = sum(m.cost_estimate for m in self.metrics)
        
        avg_duration = total_duration / len(self.metrics)
        avg_tool_calls = total_tool_calls / len(self.metrics)
        
        return {
            "framework": "contexa_sdk",
            "total_conversations": len(self.metrics),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "total_tool_calls": total_tool_calls,
            "average_tool_calls": avg_tool_calls,
            "total_tokens": total_tokens,
            "estimated_cost": total_cost
        }
    
    def get_agent_definition(self) -> Dict[str, Any]:
        """
        Get the Contexa agent definition for inspection or export.
        
        Returns:
            Dictionary containing the agent definition
        """
        return {
            "name": self.agent.name,
            "description": self.agent.description,
            "model": {
                "provider": self.model.provider,
                "model_id": self.model.model_id,
                "temperature": self.model.temperature,
                "max_tokens": self.model.max_tokens
            },
            "tools": [tool.name for tool in self.agent.tools],
            "system_prompt": self.agent.system_prompt,
            "framework": "contexa_sdk"
        }


# Convenience function for quick testing
async def create_codemaster_contexa_agent(api_key: str) -> CodeMasterContexta:
    """
    Create a CodeMaster Pro Contexa agent instance.
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        Configured CodeMaster Pro Contexa agent
    """
    return CodeMasterContexta(api_key=api_key)


# Comparison function to test both implementations
async def compare_implementations(api_key: str, test_query: str) -> Dict[str, Any]:
    """
    Compare OpenAI and Contexa implementations side by side.
    
    Args:
        api_key: OpenAI API key
        test_query: Query to test with both implementations
        
    Returns:
        Comparison results
    """
    from openai_agent.codemaster_openai import CodeMasterOpenAI
    
    # Create both agents
    openai_agent = CodeMasterOpenAI(api_key=api_key)
    contexa_agent = CodeMasterContexta(api_key=api_key)
    
    # Test both
    openai_result = await openai_agent.process_message(test_query)
    contexa_result = await contexa_agent.process_message(test_query)
    
    return {
        "query": test_query,
        "openai_result": openai_result,
        "contexa_result": contexa_result,
        "comparison": {
            "openai_duration": openai_result["metrics"]["duration"],
            "contexa_duration": contexa_result["metrics"]["duration"],
            "duration_difference": abs(
                openai_result["metrics"]["duration"] - 
                contexa_result["metrics"]["duration"]
            ),
            "both_successful": (
                openai_result["success"] and contexa_result["success"]
            )
        }
    }


# Example usage and testing
if __name__ == "__main__":
    async def test_codemaster_contexa():
        """Test the CodeMaster Pro Contexa implementation."""
        # Load API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Please set OPENAI_API_KEY environment variable")
            return
        
        # Create agent
        agent = await create_codemaster_contexa_agent(api_key)
        
        # Test scenarios
        test_queries = [
            "How do I use React hooks for state management?",
            "Show me best practices for Python async programming",
            "Help me create a FastAPI endpoint with authentication"
        ]
        
        print("🤖 CodeMaster Pro - Contexa SDK Implementation Test")
        print("=" * 55)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 40)
            
            result = await agent.process_message(query)
            
            print(f"✅ Success: {result['success']}")
            print(f"⏱️  Duration: {result['metrics']['duration']:.2f}s")
            print(f"🔧 Tool Calls: {result['metrics']['tool_calls']}")
            print(f"🎯 Tokens: {result['metrics']['tokens_used']}")
            print(f"💰 Cost: ${result['metrics']['cost_estimate']:.4f}")
            print(f"🏗️  Framework: {result['framework']}")
            print(f"\n📄 Response:\n{result['response'][:300]}...")
        
        # Performance summary
        print("\n📊 Performance Summary")
        print("=" * 30)
        summary = agent.get_performance_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
        
        # Agent definition
        print("\n🔧 Agent Definition")
        print("=" * 25)
        definition = agent.get_agent_definition()
        for key, value in definition.items():
            print(f"{key}: {value}")
    
    # Run the test
    asyncio.run(test_codemaster_contexa()) 