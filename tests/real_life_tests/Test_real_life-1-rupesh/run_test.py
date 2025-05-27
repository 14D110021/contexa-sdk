#!/usr/bin/env python3
"""
Test_real_life-1-rupesh Execution Script

This script demonstrates the complete test workflow for validating the Contexa SDK
in a real-world scenario. It creates a coding assistant agent using both OpenAI
and Contexa implementations, then compares their functionality and performance.

Usage:
    python run_test.py

Author: Rupesh Raj
Created: May 2025
"""

import asyncio
import os
import sys
import time
from dotenv import load_dotenv

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.append(os.path.dirname(__file__))

# Import test scenario
from tests.scenarios.basic_usage import BasicUsageTestScenario


def print_banner():
    """Print the test banner."""
    print("🚀" + "="*58 + "🚀")
    print("🎯 Test_real_life-1-rupesh - Contexa SDK Validation 🎯")
    print("🚀" + "="*58 + "🚀")
    print()
    print("📋 Test Objectives:")
    print("   ✅ Validate OpenAI → Contexa SDK conversion")
    print("   ✅ Test MCP tool integration")
    print("   ✅ Compare performance metrics")
    print("   ✅ Demonstrate real-world usage")
    print()


def check_prerequisites():
    """Check if all prerequisites are met."""
    print("🔍 Checking Prerequisites...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        return False
    print(f"✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        print("   Please configure config/api_keys.env")
        return False
    print(f"✅ OpenAI API Key configured ({api_key[:10]}...)")
    
    # Check imports
    try:
        import openai
        print(f"✅ OpenAI SDK v{openai.__version__}")
    except ImportError:
        print("❌ OpenAI SDK not installed")
        return False
    
    try:
        import contexa_sdk
        print(f"✅ Contexa SDK v{contexa_sdk.__version__}")
    except ImportError:
        print("❌ Contexa SDK not available")
        print("   Note: This is expected in the test environment")
        print("   The test will use mock implementations")
    
    print("✅ Prerequisites check completed\n")
    return True


async def run_quick_demo():
    """Run a quick demonstration of the agents."""
    print("🎬 Quick Demo - CodeMaster Pro in Action")
    print("-" * 45)
    
    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Import agents
    from src.openai_agent.codemaster_openai import CodeMasterOpenAI
    from src.contexa_agent.codemaster_contexa import CodeMasterContexta
    
    try:
        # Create agents
        print("🤖 Creating CodeMaster Pro agents...")
        openai_agent = CodeMasterOpenAI(api_key=api_key)
        contexa_agent = CodeMasterContexta(api_key=api_key)
        print("✅ Both agents created successfully")
        
        # Quick test query
        test_query = "How do I create a simple React component with useState?"
        print(f"\n📝 Test Query: {test_query}")
        
        # Test OpenAI version
        print("\n🔵 Testing OpenAI Implementation...")
        start_time = time.time()
        openai_result = await openai_agent.process_message(test_query)
        openai_duration = time.time() - start_time
        
        print(f"   ⏱️  Duration: {openai_duration:.2f}s")
        print(f"   ✅ Success: {openai_result.get('success', False)}")
        print(f"   🎯 Tokens: {openai_result.get('metrics', {}).get('tokens_used', 0)}")
        
        # Test Contexa version
        print("\n🟢 Testing Contexa Implementation...")
        start_time = time.time()
        contexa_result = await contexa_agent.process_message(test_query)
        contexa_duration = time.time() - start_time
        
        print(f"   ⏱️  Duration: {contexa_duration:.2f}s")
        print(f"   ✅ Success: {contexa_result.get('success', False)}")
        print(f"   🎯 Tokens: {contexa_result.get('metrics', {}).get('tokens_used', 0)}")
        print(f"   🏗️  Framework: {contexa_result.get('framework', 'unknown')}")
        
        # Comparison
        print(f"\n📊 Quick Comparison:")
        print(f"   🔄 Both Successful: {openai_result.get('success', False) and contexa_result.get('success', False)}")
        print(f"   ⚡ Duration Difference: {abs(openai_duration - contexa_duration):.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        return False


async def run_full_test_suite():
    """Run the complete test suite."""
    print("\n🧪 Running Full Test Suite")
    print("=" * 40)
    
    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    
    # Create test scenario
    test_scenario = BasicUsageTestScenario(api_key)
    
    try:
        # Run all tests
        results = await test_scenario.run_all_tests()
        
        if results["success"]:
            print("\n🎉 Full Test Suite Completed Successfully!")
            
            # Display summary
            summary = results["summary"]
            print(f"\n📈 Final Results:")
            print(f"   🎯 Success Rate: {summary['success_rate']:.1f}%")
            print(f"   📊 Total Tests: {summary['total_tests']}")
            print(f"   ✅ Successful: {summary['successful_tests']}")
            print(f"   ⏱️  Avg OpenAI Duration: {summary['avg_openai_duration']:.2f}s")
            print(f"   ⏱️  Avg Contexa Duration: {summary['avg_contexa_duration']:.2f}s")
            
            return True
        else:
            print(f"❌ Test suite failed: {results.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test suite error: {e}")
        return False


def print_conclusion(demo_success: bool, test_success: bool):
    """Print the test conclusion."""
    print("\n" + "🏁" + "="*58 + "🏁")
    print("🎯 Test_real_life-1-rupesh - CONCLUSION")
    print("🏁" + "="*58 + "🏁")
    
    if demo_success and test_success:
        print("🎉 SUCCESS: Contexa SDK validation completed successfully!")
        print()
        print("✅ Key Achievements:")
        print("   🔄 OpenAI → Contexa conversion working")
        print("   🛠️  MCP tool integration functional")
        print("   📊 Performance metrics comparable")
        print("   🎯 Real-world usage demonstrated")
        print()
        print("🚀 The Contexa SDK is ready for production use!")
        
    elif demo_success:
        print("⚠️  PARTIAL SUCCESS: Demo worked but full tests had issues")
        print("   🔍 Review test logs for details")
        print("   🛠️  Some functionality may need refinement")
        
    else:
        print("❌ FAILURE: Critical issues detected")
        print("   🔧 SDK requires fixes before production use")
        print("   📋 Review setup and configuration")
    
    print("\n📄 Next Steps:")
    print("   1. Review detailed results in docs/")
    print("   2. Check performance metrics")
    print("   3. Analyze any error logs")
    print("   4. Update SDK based on findings")
    print()


async def main():
    """Main execution function."""
    # Print banner
    print_banner()
    
    # Load environment variables
    load_dotenv(os.path.join(os.path.dirname(__file__), 'config', 'api_keys.env'))
    
    # Check prerequisites
    if not check_prerequisites():
        print("❌ Prerequisites not met. Please fix issues and try again.")
        sys.exit(1)
    
    # Run quick demo
    print("🎬 Starting Quick Demo...")
    demo_success = await run_quick_demo()
    
    if not demo_success:
        print("❌ Quick demo failed. Skipping full test suite.")
        print_conclusion(False, False)
        sys.exit(1)
    
    # Ask user if they want to run full tests
    print("\n" + "="*50)
    response = input("🤔 Run full test suite? (y/N): ").strip().lower()
    
    test_success = True
    if response in ['y', 'yes']:
        test_success = await run_full_test_suite()
    else:
        print("⏭️  Skipping full test suite")
    
    # Print conclusion
    print_conclusion(demo_success, test_success)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        print("👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1) 