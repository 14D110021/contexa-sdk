"""
CodeMaster Pro - OpenAI Agent Implementation

This module implements the CodeMaster Pro coding assistant using the OpenAI Agent SDK
with MCP tool integration. This serves as the baseline implementation for comparison
with the Contexa SDK version.

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
import openai
from openai import OpenAI
from pydantic import BaseModel

# Import our custom tools
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from tools.context7_tool import Context7Tool, Context7Input
from tools.exa_search_tool import ExaSearchTool, ExaSearchInput

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


class CodeMasterOpenAI:
    """
    CodeMaster Pro implementation using OpenAI Agent SDK.
    
    This agent provides advanced coding assistance with real-time documentation
    lookup and web search capabilities through MCP tools.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4.1",
        temperature: float = 0.1,
        max_tokens: int = 4000
    ):
        """
        Initialize the CodeMaster Pro OpenAI agent.
        
        Args:
            api_key: OpenAI API key
            model: Model to use (default: gpt-4.1)
            temperature: Temperature for generation
            max_tokens: Maximum tokens per response
        """
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize tools
        self.context7_tool = Context7Tool()
        self.exa_tool = ExaSearchTool()
        
        # Agent configuration
        self.name = "CodeMaster Pro"
        self.description = "Advanced coding assistant with MCP tool integration"
        self.system_prompt = """You are CodeMaster Pro, an advanced coding assistant with access to real-time documentation and web search capabilities.

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
        
        # Performance tracking
        self.metrics: List[PerformanceMetrics] = []
        
    def get_available_functions(self) -> List[Dict[str, Any]]:
        """
        Get the list of available functions for OpenAI function calling.
        
        Returns:
            List of function schemas for OpenAI
        """
        return [
            self.context7_tool.get_openai_function_schema(),
            self.exa_tool.get_openai_function_schema()
        ]
    
    async def execute_function_call(
        self, 
        function_name: str, 
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a function call from the OpenAI agent.
        
        Args:
            function_name: Name of the function to call
            arguments: Arguments for the function
            
        Returns:
            Function execution result
        """
        try:
            if function_name == "context7_docs":
                input_data = Context7Input(**arguments)
                result = await self.context7_tool.execute(input_data)
                return {
                    "success": result.success,
                    "content": result.content,
                    "library_id": result.library_id,
                    "tokens_used": result.tokens_used,
                    "error": result.error_message
                }
                
            elif function_name == "exa_web_search":
                input_data = ExaSearchInput(**arguments)
                result = await self.exa_tool.execute(input_data)
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
                
            else:
                return {
                    "success": False,
                    "error": f"Unknown function: {function_name}"
                }
                
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {e}")
            return {
                "success": False,
                "error": f"Function execution error: {str(e)}"
            }
    
    async def process_message(
        self, 
        user_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and generate a response.
        
        Args:
            user_message: The user's message
            conversation_history: Previous conversation messages
            
        Returns:
            Dictionary containing the response and metadata
        """
        start_time = time.time()
        tool_calls = 0
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user message
            messages.append({"role": "user", "content": user_message})
            
            # Make initial API call
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                functions=self.get_available_functions(),
                function_call="auto",
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            message = response.choices[0].message
            total_tokens = response.usage.total_tokens
            
            # Handle function calls
            while message.function_call:
                tool_calls += 1
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)
                
                logger.info(f"Executing function: {function_name}")
                
                # Execute the function
                function_result = await self.execute_function_call(
                    function_name, 
                    function_args
                )
                
                # Add function call and result to messages
                messages.append({
                    "role": "assistant",
                    "content": None,
                    "function_call": {
                        "name": function_name,
                        "arguments": message.function_call.arguments
                    }
                })
                
                messages.append({
                    "role": "function",
                    "name": function_name,
                    "content": json.dumps(function_result)
                })
                
                # Get next response
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    functions=self.get_available_functions(),
                    function_call="auto",
                    temperature=self.temperature,
                    max_tokens=self.max_tokens
                )
                
                message = response.choices[0].message
                total_tokens += response.usage.total_tokens
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Calculate cost estimate (rough)
            cost_estimate = (total_tokens / 1000) * 0.03  # Rough estimate
            
            # Store metrics
            metrics = PerformanceMetrics(
                start_time=start_time,
                end_time=end_time,
                total_duration=duration,
                tool_calls=tool_calls,
                tokens_used=total_tokens,
                cost_estimate=cost_estimate
            )
            self.metrics.append(metrics)
            
            return {
                "response": message.content,
                "success": True,
                "metrics": {
                    "duration": duration,
                    "tool_calls": tool_calls,
                    "tokens_used": total_tokens,
                    "cost_estimate": cost_estimate
                },
                "conversation_id": len(self.metrics)
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            end_time = time.time()
            
            return {
                "response": f"I apologize, but I encountered an error: {str(e)}",
                "success": False,
                "metrics": {
                    "duration": end_time - start_time,
                    "tool_calls": tool_calls,
                    "tokens_used": 0,
                    "cost_estimate": 0
                },
                "error": str(e)
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
            "total_conversations": len(self.metrics),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "total_tool_calls": total_tool_calls,
            "average_tool_calls": avg_tool_calls,
            "total_tokens": total_tokens,
            "estimated_cost": total_cost
        }


# Convenience function for quick testing
async def create_codemaster_agent(api_key: str) -> CodeMasterOpenAI:
    """
    Create a CodeMaster Pro agent instance.
    
    Args:
        api_key: OpenAI API key
        
    Returns:
        Configured CodeMaster Pro agent
    """
    return CodeMasterOpenAI(api_key=api_key)


# Example usage and testing
if __name__ == "__main__":
    async def test_codemaster_openai():
        """Test the CodeMaster Pro OpenAI implementation."""
        # Load API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("Please set OPENAI_API_KEY environment variable")
            return
        
        # Create agent
        agent = await create_codemaster_agent(api_key)
        
        # Test scenarios
        test_queries = [
            "How do I use React hooks for state management?",
            "Show me best practices for Python async programming",
            "Help me create a FastAPI endpoint with authentication"
        ]
        
        print("🤖 CodeMaster Pro - OpenAI Implementation Test")
        print("=" * 50)
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {query}")
            print("-" * 40)
            
            result = await agent.process_message(query)
            
            print(f"✅ Success: {result['success']}")
            print(f"⏱️  Duration: {result['metrics']['duration']:.2f}s")
            print(f"🔧 Tool Calls: {result['metrics']['tool_calls']}")
            print(f"🎯 Tokens: {result['metrics']['tokens_used']}")
            print(f"💰 Cost: ${result['metrics']['cost_estimate']:.4f}")
            print(f"\n📄 Response:\n{result['response'][:300]}...")
        
        # Performance summary
        print("\n📊 Performance Summary")
        print("=" * 30)
        summary = agent.get_performance_summary()
        for key, value in summary.items():
            print(f"{key}: {value}")
    
    # Run the test
    asyncio.run(test_codemaster_openai()) 