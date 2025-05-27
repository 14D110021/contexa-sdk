"""
Basic Usage Test Scenario for Test_real_life-1-rupesh

This script demonstrates basic usage of both OpenAI and Contexa implementations
of CodeMaster Pro, validating core functionality and comparing performance.

Author: Rupesh Raj
Created: May 2025
"""

import asyncio
import json
import logging
import os
import sys
import time
from typing import Dict, Any, List
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../../src'))

# Import our implementations
from src.openai_agent.codemaster_openai import CodeMasterOpenAI
from src.contexa_agent.codemaster_contexa import CodeMasterContexta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BasicUsageTestScenario:
    """
    Basic usage test scenario for CodeMaster Pro implementations.
    
    This class runs a series of tests to validate core functionality
    and compare performance between OpenAI and Contexa implementations.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the test scenario.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.test_results = []
        
    async def setup_agents(self) -> Dict[str, Any]:
        """
        Set up both OpenAI and Contexa agents.
        
        Returns:
            Dictionary containing both agent instances
        """
        logger.info("Setting up agents...")
        
        try:
            openai_agent = CodeMasterOpenAI(api_key=self.api_key)
            contexa_agent = CodeMasterContexta(api_key=self.api_key)
            
            logger.info("✅ Both agents created successfully")
            
            return {
                "openai": openai_agent,
                "contexa": contexa_agent,
                "setup_success": True
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to setup agents: {e}")
            return {
                "openai": None,
                "contexa": None,
                "setup_success": False,
                "error": str(e)
            }
    
    async def run_test_query(
        self, 
        agents: Dict[str, Any], 
        query: str, 
        test_name: str
    ) -> Dict[str, Any]:
        """
        Run a test query on both agents and compare results.
        
        Args:
            agents: Dictionary containing agent instances
            query: Test query to execute
            test_name: Name of the test for reporting
            
        Returns:
            Test results dictionary
        """
        logger.info(f"Running test: {test_name}")
        logger.info(f"Query: {query}")
        
        results = {
            "test_name": test_name,
            "query": query,
            "timestamp": time.time(),
            "openai_result": None,
            "contexa_result": None,
            "comparison": None,
            "success": False
        }
        
        try:
            # Test OpenAI implementation
            logger.info("Testing OpenAI implementation...")
            openai_start = time.time()
            openai_result = await agents["openai"].process_message(query)
            openai_duration = time.time() - openai_start
            
            # Test Contexa implementation
            logger.info("Testing Contexa implementation...")
            contexa_start = time.time()
            contexa_result = await agents["contexa"].process_message(query)
            contexa_duration = time.time() - contexa_start
            
            # Store results
            results["openai_result"] = openai_result
            results["contexa_result"] = contexa_result
            
            # Compare results
            comparison = {
                "both_successful": (
                    openai_result.get("success", False) and 
                    contexa_result.get("success", False)
                ),
                "openai_duration": openai_duration,
                "contexa_duration": contexa_duration,
                "duration_difference": abs(openai_duration - contexa_duration),
                "openai_tokens": openai_result.get("metrics", {}).get("tokens_used", 0),
                "contexa_tokens": contexa_result.get("metrics", {}).get("tokens_used", 0),
                "openai_tool_calls": openai_result.get("metrics", {}).get("tool_calls", 0),
                "contexa_tool_calls": contexa_result.get("metrics", {}).get("tool_calls", 0)
            }
            
            results["comparison"] = comparison
            results["success"] = comparison["both_successful"]
            
            # Log results
            if results["success"]:
                logger.info(f"✅ Test '{test_name}' completed successfully")
                logger.info(f"   OpenAI duration: {openai_duration:.2f}s")
                logger.info(f"   Contexa duration: {contexa_duration:.2f}s")
                logger.info(f"   Duration difference: {comparison['duration_difference']:.2f}s")
            else:
                logger.warning(f"⚠️  Test '{test_name}' had issues")
                if not openai_result.get("success", False):
                    logger.warning(f"   OpenAI error: {openai_result.get('error', 'Unknown')}")
                if not contexa_result.get("success", False):
                    logger.warning(f"   Contexa error: {contexa_result.get('error', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"❌ Test '{test_name}' failed: {e}")
            results["error"] = str(e)
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all basic usage tests.
        
        Returns:
            Complete test results
        """
        logger.info("🚀 Starting Basic Usage Test Scenario")
        logger.info("=" * 50)
        
        # Setup agents
        agents = await self.setup_agents()
        if not agents["setup_success"]:
            return {
                "success": False,
                "error": "Failed to setup agents",
                "details": agents
            }
        
        # Define test scenarios
        test_scenarios = [
            {
                "name": "React Hooks Documentation",
                "query": "How do I use React hooks for state management? Show me a practical example."
            },
            {
                "name": "Python Async Best Practices",
                "query": "What are the best practices for Python async programming? Include code examples."
            },
            {
                "name": "FastAPI Authentication",
                "query": "Help me create a FastAPI endpoint with JWT authentication. Show the complete implementation."
            },
            {
                "name": "JavaScript Performance",
                "query": "How can I optimize JavaScript performance in a React application? Give me specific techniques."
            },
            {
                "name": "Database Design",
                "query": "What are the best practices for designing a PostgreSQL database schema for a user management system?"
            }
        ]
        
        # Run tests
        test_results = []
        for scenario in test_scenarios:
            result = await self.run_test_query(
                agents, 
                scenario["query"], 
                scenario["name"]
            )
            test_results.append(result)
            self.test_results.append(result)
            
            # Brief pause between tests
            await asyncio.sleep(1)
        
        # Generate summary
        summary = self.generate_summary(test_results)
        
        logger.info("\n📊 Test Summary")
        logger.info("=" * 30)
        logger.info(f"Total tests: {summary['total_tests']}")
        logger.info(f"Successful tests: {summary['successful_tests']}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        logger.info(f"Average OpenAI duration: {summary['avg_openai_duration']:.2f}s")
        logger.info(f"Average Contexa duration: {summary['avg_contexa_duration']:.2f}s")
        
        return {
            "success": True,
            "test_results": test_results,
            "summary": summary,
            "agents": {
                "openai_summary": agents["openai"].get_performance_summary(),
                "contexa_summary": agents["contexa"].get_performance_summary()
            }
        }
    
    def generate_summary(self, test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a summary of test results.
        
        Args:
            test_results: List of test result dictionaries
            
        Returns:
            Summary statistics
        """
        total_tests = len(test_results)
        successful_tests = sum(1 for r in test_results if r.get("success", False))
        
        openai_durations = [
            r["comparison"]["openai_duration"] 
            for r in test_results 
            if r.get("comparison")
        ]
        
        contexa_durations = [
            r["comparison"]["contexa_duration"] 
            for r in test_results 
            if r.get("comparison")
        ]
        
        return {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            "avg_openai_duration": sum(openai_durations) / len(openai_durations) if openai_durations else 0,
            "avg_contexa_duration": sum(contexa_durations) / len(contexa_durations) if contexa_durations else 0,
            "total_openai_duration": sum(openai_durations),
            "total_contexa_duration": sum(contexa_durations)
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "basic_usage_results.json"):
        """
        Save test results to a JSON file.
        
        Args:
            results: Test results to save
            filename: Output filename
        """
        output_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "..", 
            "docs", 
            filename
        )
        
        try:
            with open(output_path, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"📄 Results saved to {output_path}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")


async def main():
    """Main function to run the basic usage test scenario."""
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'api_keys.env'))
    
    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        logger.error("❌ OPENAI_API_KEY not found in environment variables")
        logger.error("Please ensure config/api_keys.env is properly configured")
        return
    
    # Create and run test scenario
    test_scenario = BasicUsageTestScenario(api_key)
    
    try:
        results = await test_scenario.run_all_tests()
        
        if results["success"]:
            logger.info("🎉 All tests completed successfully!")
            
            # Save results
            test_scenario.save_results(results)
            
            # Print final summary
            summary = results["summary"]
            print("\n" + "="*60)
            print("🏆 FINAL TEST RESULTS")
            print("="*60)
            print(f"✅ Success Rate: {summary['success_rate']:.1f}%")
            print(f"⏱️  OpenAI Avg Duration: {summary['avg_openai_duration']:.2f}s")
            print(f"⏱️  Contexa Avg Duration: {summary['avg_contexa_duration']:.2f}s")
            print(f"🔧 Total Tests: {summary['total_tests']}")
            print(f"✅ Successful: {summary['successful_tests']}")
            print("="*60)
            
        else:
            logger.error("❌ Test scenario failed")
            logger.error(f"Error: {results.get('error', 'Unknown error')}")
            
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 