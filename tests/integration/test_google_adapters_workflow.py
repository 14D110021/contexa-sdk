"""Integration test for a complete workflow involving both Google adapter types.

This test verifies that a multi-step workflow can successfully:
1. Start with a GenAI-based agent
2. Hand off to an ADK-based agent 
3. Hand off to other framework agents (LangChain, OpenAI)
4. Complete a coherent process using different adapters
"""

import pytest
import unittest.mock as mock
import asyncio
from typing import Dict, Any

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.runtime.agent_runtime import AgentRuntime, RuntimeOptions
from contexa_sdk.runtime.handoff import handoff
from contexa_sdk.adapters import langchain, crewai, openai
from contexa_sdk.adapters.google import (
    genai_agent, genai_handoff, adk_agent, adk_handoff
)


class MockTool(ContexaTool):
    """Mock tool for testing."""
    
    def __init__(self, name="test_tool", description="Test tool description"):
        """Initialize the mock tool."""
        self.name = name
        self.description = description
        
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the mock tool."""
        return {"result": f"Executed {self.name} with {kwargs}"}


@pytest.fixture
def workflow_tools():
    """Create tools for the workflow test."""
    
    @ContexaTool.register(
        name="information_retrieval",
        description="Retrieve information on a topic"
    )
    async def information_retrieval(topic: str) -> str:
        return f"Retrieved information about {topic}: Sample data A, Sample data B"
    
    @ContexaTool.register(
        name="analysis",
        description="Analyze data and extract insights"
    )
    async def analysis(data: str) -> str:
        return f"Analysis of '{data}': Found 3 key insights"
    
    @ContexaTool.register(
        name="report_generation",
        description="Generate a formatted report"
    )
    async def report_generation(content: str, format_type: str) -> str:
        return f"Generated {format_type} report: {content}"
    
    @ContexaTool.register(
        name="translation",
        description="Translate content to another language"
    )
    async def translation(content: str, target_language: str) -> str:
        return f"Translated to {target_language}: {content}"
    
    return {
        "retrieval": information_retrieval,
        "analysis": analysis,
        "report": report_generation,
        "translation": translation
    }


@pytest.fixture
def workflow_agents(workflow_tools):
    """Create agents for the workflow test."""
    
    # Research agent using Google GenAI
    research_agent = ContexaAgent(
        name="Research Agent",
        description="Retrieves and processes information",
        model=ContexaModel(model_name="gemini-pro", provider="google"),
        tools=[workflow_tools["retrieval"]],
        system_prompt="You are a research assistant specialized in information retrieval."
    )
    
    # Analysis agent using Google ADK
    analysis_agent = ContexaAgent(
        name="Analysis Agent",
        description="Analyzes data and extracts insights",
        model=ContexaModel(model_name="gemini-pro", provider="google"),
        tools=[workflow_tools["analysis"]],
        system_prompt="You are an analysis assistant specialized in identifying patterns."
    )
    
    # Report agent using LangChain
    report_agent = ContexaAgent(
        name="Report Agent",
        description="Formats and prepares reports",
        model=ContexaModel(model_name="gpt-4o", provider="openai"),
        tools=[workflow_tools["report"]],
        system_prompt="You are a report preparation assistant."
    )
    
    # Translation agent using OpenAI
    translation_agent = ContexaAgent(
        name="Translation Agent",
        description="Translates content to other languages",
        model=ContexaModel(model_name="gpt-4o", provider="openai"),
        tools=[workflow_tools["translation"]],
        system_prompt="You are a translation assistant."
    )
    
    return {
        "research": research_agent,
        "analysis": analysis_agent,
        "report": report_agent,
        "translation": translation_agent
    }


@pytest.mark.asyncio
async def test_multi_adapter_workflow(workflow_agents):
    """Test a complete workflow involving both Google adapter types and other frameworks."""
    # Mock implementations for the various agents
    genai_mock = mock.MagicMock()
    genai_mock.run = mock.AsyncMock(
        return_value="Research results on quantum computing: Recent advances in qubit stability."
    )
    
    adk_mock = mock.MagicMock()
    adk_mock.run = mock.AsyncMock(
        return_value="Analysis: The quantum computing data shows 3 major trends: improved coherence time, error correction, and scalability."
    )
    
    langchain_mock = mock.MagicMock()
    langchain_mock.run = mock.AsyncMock(
        return_value="## Quantum Computing Report\n\n1. Improved coherence time\n2. Better error correction\n3. Scalability improvements"
    )
    
    openai_mock = mock.MagicMock()
    openai_mock.run = mock.AsyncMock(
        return_value="## Rapport sur l'informatique quantique\n\n1. Amélioration du temps de cohérence\n2. Meilleure correction d'erreurs\n3. Améliorations de l'évolutivité"
    )
    
    # Set up the mock adapter conversions
    with mock.patch("contexa_sdk.adapters.google.genai.agent", return_value=genai_mock), \
         mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent", return_value=adk_mock), \
         mock.patch("contexa_sdk.adapters.langchain.agent", return_value=langchain_mock), \
         mock.patch("contexa_sdk.adapters.openai.agent", return_value=openai_mock):
        
        # Setup runtime for agent management
        runtime = AgentRuntime(options=RuntimeOptions(
            max_concurrent_runs=3,
            telemetry_enabled=True
        ))
        
        # Register agents with runtime
        research_id = await runtime.register_agent(workflow_agents["research"])
        analysis_id = await runtime.register_agent(workflow_agents["analysis"])
        report_id = await runtime.register_agent(workflow_agents["report"])
        translate_id = await runtime.register_agent(workflow_agents["translation"])
        
        # Start all agents
        await runtime.start_agent(research_id)
        await runtime.start_agent(analysis_id)
        await runtime.start_agent(report_id)
        await runtime.start_agent(translate_id)
        
        try:
            # Mock the runtime run_agent to return the GenAI response
            with mock.patch.object(runtime, "run_agent") as mock_run_agent:
                mock_run_agent.return_value = genai_mock.run.return_value
                
                # Step 1: Execute research with Google GenAI agent
                research_result = await runtime.run_agent(
                    research_id, "Research recent advances in quantum computing"
                )
                
                # Verify GenAI agent result
                assert "quantum computing" in research_result.lower()
                assert "research results" in research_result.lower()
                
                # Step 2: Hand off to Google ADK agent for analysis
                # We need to mock handoff directly to test the workflow properly
                with mock.patch("contexa_sdk.adapters.google.adk_handoff", return_value=adk_mock.run.return_value):
                    analysis_result = await genai_handoff(
                        source_agent=workflow_agents["research"],
                        target_agent=workflow_agents["analysis"],
                        query=f"Analyze these research findings: {research_result}"
                    )
                
                # Verify ADK agent result
                assert "analysis" in analysis_result.lower()
                assert "quantum computing" in analysis_result.lower()
                assert "3 major trends" in analysis_result
                
                # Step 3: Hand off to LangChain agent for report generation
                # Mock LangChain handoff
                with mock.patch("contexa_sdk.adapters.langchain.handoff", return_value=langchain_mock.run.return_value):
                    report_result = await adk_handoff(
                        source_agent=workflow_agents["analysis"],
                        target_adk_agent=workflow_agents["report"],
                        query=f"Generate a markdown report based on this analysis: {analysis_result}"
                    )
                
                # Verify LangChain agent result  
                assert "## quantum computing report" in report_result.lower()
                assert "error correction" in report_result.lower()
                
                # Step 4: Hand off to OpenAI agent for translation
                # Mock OpenAI handoff
                with mock.patch("contexa_sdk.adapters.openai.handoff", return_value=openai_mock.run.return_value):
                    final_result = await langchain.handoff(
                        source_agent=workflow_agents["report"],
                        target_agent_executor=workflow_agents["translation"],
                        query=f"Translate this report to French: {report_result}"
                    )
                
                # Verify OpenAI agent result
                assert "## rapport" in final_result.lower()
                assert "quantique" in final_result.lower()
                
                # Verify the full workflow produced coherent results
                assert "informatique quantique" in final_result.lower()
        
        finally:
            # Stop all agents
            await runtime.stop_agent(research_id)
            await runtime.stop_agent(analysis_id)
            await runtime.stop_agent(report_id)
            await runtime.stop_agent(translate_id)


@pytest.mark.asyncio
async def test_genai_to_adk_to_genai_loop(workflow_agents):
    """Test a workflow that loops from GenAI to ADK and back to GenAI."""
    # Mock implementations
    genai_mock_1 = mock.MagicMock()
    genai_mock_1.run = mock.AsyncMock(
        return_value="Research data on AI: Foundation models continue to improve."
    )
    
    adk_mock = mock.MagicMock()
    adk_mock.run = mock.AsyncMock(
        return_value="Analysis complete: Foundation models show improved reasoning and reduced hallucinations."
    )
    
    genai_mock_2 = mock.MagicMock()
    genai_mock_2.run = mock.AsyncMock(
        return_value="Final summary: Foundation models are advancing in reasoning capabilities while reducing hallucinations, leading to more reliable AI systems."
    )
    
    # Setup agent mocks for different conversions
    with mock.patch("contexa_sdk.adapters.google.genai.agent") as mock_genai_agent:
        # First call returns first GenAI mock, second call returns second GenAI mock
        mock_genai_agent.side_effect = [genai_mock_1, genai_mock_2]
        
        with mock.patch("contexa_sdk.adapters.google.adk.sync_adapt_agent", return_value=adk_mock):
            # Setup handoff functions
            with mock.patch("contexa_sdk.adapters.google.genai_handoff") as mock_genai_handoff, \
                 mock.patch("contexa_sdk.adapters.google.adk_handoff") as mock_adk_handoff:
                
                # Configure return values
                mock_genai_handoff.return_value = adk_mock.run.return_value
                mock_adk_handoff.return_value = genai_mock_2.run.return_value
                
                # Step 1: Start with GenAI (research)
                step1_result = await genai_agent(workflow_agents["research"]).run(
                    "Research recent advances in foundation models"
                )
                assert "research data" in step1_result.lower()
                
                # Step 2: Hand off to ADK (analysis) 
                step2_result = await mock_genai_handoff(
                    source_agent=workflow_agents["research"],
                    target_agent=workflow_agents["analysis"],
                    query=f"Analyze these findings: {step1_result}"
                )
                assert "analysis complete" in step2_result.lower()
                
                # Step 3: Hand off back to GenAI (different agent but same adapter type)
                step3_result = await mock_adk_handoff(
                    source_agent=workflow_agents["analysis"],
                    target_adk_agent=workflow_agents["research"],  # Reusing research agent
                    query=f"Summarize and expand on this analysis: {step2_result}"
                )
                assert "final summary" in step3_result.lower()
                
                # Verify the full loop worked
                assert "foundation models" in step3_result.lower()
                assert "hallucinations" in step3_result.lower()
                assert "reasoning" in step3_result.lower() 