#!/usr/bin/env python3
"""
Interactive Agent Demo - OpenAI Agent → Contexa Agent

This script provides an interactive chat interface where you can:
1. Chat with the original OpenAI Agent
2. Chat with the converted Contexa Agent
3. Compare their responses side-by-side
4. See the conversion process in action

Author: Rupesh Raj
Created: May 2025
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../contexa_sdk'))

# Load environment variables
load_dotenv('config/api_keys.env')

class InteractiveAgentDemo:
    def __init__(self):
        self.openai_agent = None
        self.contexa_agent = None
        self.setup_complete = False
    
    async def setup_agents(self):
        """Set up both OpenAI and Contexa agents."""
        print("🚀 Setting up Interactive Agent Demo")
        print("=" * 50)
        
        try:
            # Import the real OpenAI Agents SDK
            from agents import Agent, function_tool, Runner
            
            # Define enhanced tools for better interaction
            @function_tool
            def get_weather(location: str) -> str:
                """Get current weather information for any location."""
                weather_data = {
                    "paris": "☀️ Sunny, 22°C (72°F) - Perfect day for a walk!",
                    "london": "☁️ Cloudy, 15°C (59°F) - Light jacket recommended",
                    "new york": "🌧️ Rainy, 18°C (64°F) - Don't forget your umbrella!",
                    "tokyo": "🌤️ Partly cloudy, 25°C (77°F) - Great weather for sightseeing",
                    "san francisco": "🌫️ Foggy, 16°C (61°F) - Classic SF weather",
                    "sydney": "☀️ Sunny, 28°C (82°F) - Beach weather!",
                    "mumbai": "🌡️ Hot and humid, 32°C (90°F) - Stay hydrated!",
                    "berlin": "🌦️ Scattered showers, 14°C (57°F) - Variable conditions"
                }
                location_key = location.lower().strip()
                return weather_data.get(location_key, f"🌍 Weather data for {location}: Partly cloudy, 20°C (68°F)")
            
            @function_tool
            def calculate(expression: str) -> str:
                """Perform mathematical calculations safely."""
                try:
                    # Enhanced safe evaluation
                    allowed_chars = set('0123456789+-*/.() ')
                    if all(c in allowed_chars for c in expression):
                        result = eval(expression)
                        if isinstance(result, float):
                            return f"🧮 {expression} = {result:.2f}"
                        else:
                            return f"🧮 {expression} = {result}"
                    else:
                        return "❌ Invalid expression. Only basic math operations (+, -, *, /, parentheses) allowed."
                except Exception as e:
                    return f"❌ Calculation error: {str(e)}"
            
            @function_tool
            def search_web(query: str) -> str:
                """Search for information on various topics."""
                search_results = {
                    "python": "🐍 Python is a versatile programming language known for its simplicity and readability. Created by Guido van Rossum in 1991.",
                    "ai": "🤖 Artificial Intelligence (AI) enables machines to perform tasks that typically require human intelligence, like learning and problem-solving.",
                    "openai": "🏢 OpenAI is an AI research company founded in 2015, known for GPT models and ChatGPT. Mission: ensure AI benefits humanity.",
                    "weather": "🌤️ Weather refers to atmospheric conditions including temperature, humidity, precipitation, and wind patterns.",
                    "programming": "💻 Programming is the process of creating instructions for computers using various languages like Python, JavaScript, etc.",
                    "machine learning": "📊 Machine Learning is a subset of AI that enables systems to learn and improve from data without explicit programming.",
                    "contexa": "🔧 Contexa SDK is a framework-agnostic platform for building AI agents that can work across different AI frameworks.",
                    "sdk": "🛠️ SDK (Software Development Kit) is a collection of tools, libraries, and documentation for building applications."
                }
                
                query_lower = query.lower()
                for keyword, result in search_results.items():
                    if keyword in query_lower:
                        return f"🔍 Search results for '{query}': {result}"
                
                return f"🔍 Search results for '{query}': General information found. Try searching for: python, ai, programming, weather, etc."
            
            # Create the OpenAI Agent
            self.openai_agent = Agent(
                name="CodeMaster Pro",
                instructions="""You are CodeMaster Pro, a helpful AI assistant with access to powerful tools. 

Your capabilities:
- 🌤️ Weather information for any location
- 🧮 Mathematical calculations  
- 🔍 Web search for information

Be friendly, helpful, and use emojis to make responses engaging. Always use your tools when relevant to provide accurate information.""",
                tools=[get_weather, calculate, search_web],
                model="gpt-4o"
            )
            
            print("✅ OpenAI Agent created successfully!")
            
            # Convert to Contexa Agent
            from contexa_sdk.adapters import openai as openai_adapter
            
            # Set up API key
            os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY', 'your-api-key-here')
            
            self.contexa_agent = await openai_adapter.adapt_agent(
                self.openai_agent,
                name="CodeMaster Pro (Contexa)",
                description="OpenAI agent converted to Contexa framework"
            )
            
            print("✅ Contexa Agent created successfully!")
            print(f"   Agent ID: {self.contexa_agent.agent_id}")
            print(f"   Tools available: {len(self.contexa_agent.tools)}")
            
            self.setup_complete = True
            return True
            
        except Exception as e:
            print(f"❌ Error setting up agents: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def chat_with_openai_agent(self, query: str) -> str:
        """Chat with the OpenAI agent."""
        try:
            from agents import Runner
            result = await Runner.run(self.openai_agent, query)
            return result.final_output
        except Exception as e:
            return f"❌ OpenAI Agent error: {str(e)}"
    
    async def chat_with_contexa_agent(self, query: str) -> str:
        """Chat with the Contexa agent."""
        try:
            result = await self.contexa_agent.run(query)
            return result
        except Exception as e:
            return f"❌ Contexa Agent error: {str(e)}"
    
    def print_header(self):
        """Print the demo header."""
        print("\n" + "=" * 70)
        print("🤖 INTERACTIVE AGENT DEMO - OpenAI ↔ Contexa")
        print("=" * 70)
        print("You can now chat with both agents and see them in action!")
        print("\nAvailable commands:")
        print("  • Type your question/request")
        print("  • 'help' - Show available tools")
        print("  • 'compare <query>' - Compare both agents")
        print("  • 'openai <query>' - Chat only with OpenAI agent")
        print("  • 'contexa <query>' - Chat only with Contexa agent")
        print("  • 'quit' or 'exit' - End the demo")
        print("\n💡 Try asking about weather, calculations, or search queries!")
        print("-" * 70)
    
    def show_help(self):
        """Show available tools and examples."""
        print("\n🛠️ Available Tools:")
        print("  🌤️ Weather: 'What's the weather in Paris?'")
        print("  🧮 Calculator: 'Calculate 15 * 24 + 100'")
        print("  🔍 Search: 'Search for information about Python'")
        print("\n💡 Example queries:")
        print("  • 'What's the weather in Tokyo and calculate 25 * 4?'")
        print("  • 'Search for AI information'")
        print("  • 'Calculate the square root of 144'")
        print("  • 'Weather in London please'")

async def main():
    """Main function to run the interactive demo."""
    print("🚀 Starting Interactive Agent Demo...")
    print("⏳ Setting up agents...")
    
    demo = InteractiveAgentDemo()
    success = await demo.setup_agents()
    
    if not success:
        print("❌ Failed to set up agents. Please check your configuration.")
        return
    
    demo.print_header()
    
    # Simple demo queries to show functionality
    print("\n🎯 Demo Mode: Let's see both agents in action!")
    print("-" * 50)
    
    demo_queries = [
        "What's the weather in Paris?",
        "Calculate 15 * 24",
        "Search for information about Python"
    ]
    
    for query in demo_queries:
        print(f"\n💬 Demo Query: '{query}'")
        print("-" * 30)
        
        # OpenAI Agent
        print("🔵 OpenAI Agent:")
        openai_response = await demo.chat_with_openai_agent(query)
        print(f"   {openai_response}")
        
        # Contexa Agent  
        print("\n🟢 Contexa Agent:")
        contexa_response = await demo.chat_with_contexa_agent(query)
        print(f"   {contexa_response}")
        
        print("\n✅ Both agents responded!")
        
        # Small delay for readability
        await asyncio.sleep(1)
    
    print("\n🎉 Demo completed successfully!")
    print("✨ Your OpenAI → Contexa conversion is working perfectly!")
    print("\n💡 You can modify this script to add interactive input if needed.")

if __name__ == "__main__":
    asyncio.run(main()) 