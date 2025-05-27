#!/usr/bin/env python3
"""
Simple Interactive Chat with OpenAI Agent

Type your queries and see the agent respond in real-time!
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

async def setup_agent():
    """Set up the OpenAI agent."""
    from agents import Agent, function_tool, Runner
    
    @function_tool
    def get_weather(location: str) -> str:
        """Get weather for any location."""
        weather_data = {
            "paris": "☀️ Sunny, 22°C - Perfect day!",
            "london": "☁️ Cloudy, 15°C - Light jacket recommended",
            "new york": "🌧️ Rainy, 18°C - Umbrella needed!",
            "tokyo": "🌤️ Partly cloudy, 25°C - Great weather!",
            "sydney": "☀️ Sunny, 28°C - Beach weather!"
        }
        return weather_data.get(location.lower(), f"🌍 Weather in {location}: Partly cloudy, 20°C")
    
    @function_tool
    def calculate(expression: str) -> str:
        """Calculate math expressions."""
        try:
            allowed_chars = set('0123456789+-*/.() ')
            if all(c in allowed_chars for c in expression):
                result = eval(expression)
                return f"🧮 {expression} = {result}"
            else:
                return "❌ Only basic math operations allowed"
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    @function_tool
    def search_info(topic: str) -> str:
        """Search for information."""
        info = {
            "python": "🐍 Python: High-level programming language, created by Guido van Rossum in 1991",
            "ai": "🤖 AI: Computer systems that perform tasks requiring human intelligence",
            "openai": "🏢 OpenAI: AI research company, creators of GPT and ChatGPT"
        }
        for key, value in info.items():
            if key in topic.lower():
                return value
        return f"🔍 General info about {topic}: Topic found in knowledge base"
    
    agent = Agent(
        name="ChatBot Pro",
        instructions="You are a helpful assistant with weather, calculator, and search tools. Be friendly and use emojis!",
        tools=[get_weather, calculate, search_info],
        model="gpt-4o"
    )
    
    os.environ["OPENAI_API_KEY"] = os.getenv('OPENAI_API_KEY')
    return agent

async def chat_loop():
    """Simple chat loop."""
    print("🤖 Setting up ChatBot Pro...")
    agent = await setup_agent()
    
    print("\n" + "="*50)
    print("🎉 ChatBot Pro is ready!")
    print("="*50)
    print("💡 Try asking about:")
    print("  • Weather: 'weather in Paris'")
    print("  • Math: 'calculate 15 * 24'") 
    print("  • Info: 'tell me about Python'")
    print("  • Type 'quit' to exit")
    print("-"*50)
    
    from agents import Runner
    
    while True:
        try:
            query = input("\n💬 You: ").strip()
            
            if not query:
                continue
                
            if query.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye! Thanks for chatting!")
                break
            
            print("🤖 ChatBot Pro: ", end="", flush=True)
            result = await Runner.run(agent, query)
            print(result.final_output)
            
        except KeyboardInterrupt:
            print("\n👋 Chat ended. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(chat_loop()) 