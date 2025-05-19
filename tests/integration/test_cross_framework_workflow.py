"""Integration test for a complete cross-framework workflow."""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from contexa_sdk.core.tool import ContexaTool
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.runtime.agent_runtime import AgentRuntime, RuntimeOptions
from contexa_sdk.runtime.handoff import handoff


class TestMultiFrameworkWorkflow:
    """Test a complete workflow involving multiple frameworks."""
    
    @pytest.mark.asyncio
    async def test_research_analysis_workflow(self):
        """Test a research and analysis workflow across frameworks."""
        # Setup runtime
        runtime = AgentRuntime(options=RuntimeOptions(
            max_concurrent_runs=3,
            telemetry_enabled=True
        ))
        
        # Create mock tools
        @ContexaTool.register(
            name="web_search",
            description="Search the web for information"
        )
        async def web_search(query: str) -> str:
            return f"Search results for {query}: Example result 1, Example result 2"
        
        @ContexaTool.register(
            name="data_analysis",
            description="Analyze data and provide insights"
        )
        async def data_analysis(data: str) -> str:
            return f"Analysis of {data}: The data shows interesting patterns."
        
        @ContexaTool.register(
            name="content_formatter",
            description="Format content for presentation"
        )
        async def content_formatter(content: str, format_type: str) -> str:
            return f"Formatted content ({format_type}): {content}"
        
        # Create agents
        research_agent = ContexaAgent(
            name="Researcher",
            description="Researches topics using web search",
            model=ContexaModel(model_name="gpt-4o", provider="openai"),
            tools=[web_search]
        )
        
        analysis_agent = ContexaAgent(
            name="Analyst",
            description="Analyzes research data",
            model=ContexaModel(model_name="claude-3-opus", provider="anthropic"),
            tools=[data_analysis]
        )
        
        formatting_agent = ContexaAgent(
            name="Formatter",
            description="Formats content for presentation",
            model=ContexaModel(model_name="gpt-3.5-turbo", provider="openai"),
            tools=[content_formatter]
        )
        
        # Create mock framework agents
        lc_agent = MagicMock()
        lc_agent.name = "LangChain Research Agent"
        lc_agent.run = MagicMock(return_value="Research on AI advances: GPT-4, Claude, Gemini show significant improvements")
        
        crew_agent = MagicMock()
        crew_agent.name = "CrewAI Analysis Agent"
        crew_agent.run = MagicMock(return_value="Analysis: The data shows 3 major trends in AI development")
        
        oa_agent = MagicMock()
        oa_agent.name = "OpenAI Formatting Agent"
        oa_agent.run = MagicMock(return_value="Final Report (Markdown format):\n# AI Research Summary\n## Key Trends\n1. Improved reasoning\n2. Multimodal capabilities\n3. Reduced hallucinations")
        
        # Patch runtime run_agent to return the mock LangChain response
        original_run_agent = runtime.run_agent
        runtime.run_agent = MagicMock(return_value=asyncio.Future())
        runtime.run_agent.return_value.set_result(lc_agent.run())
        
        # Register agents with runtime
        research_id = await runtime.register_agent(research_agent)
        analysis_id = await runtime.register_agent(analysis_agent)
        format_id = await runtime.register_agent(formatting_agent)
        
        # Start agents
        await runtime.start_agent(research_id)
        await runtime.start_agent(analysis_id)
        await runtime.start_agent(format_id)
        
        # Execute full workflow
        # Step 1: Research phase
        research_result = await runtime.run_agent(
            research_id, "Research recent advances in AI models"
        )
        
        # Step 2: Analysis phase
        analysis_result = await handoff(
            from_agent=lc_agent,
            to_agent=crew_agent,
            message=f"Analyze these research findings: {research_result}"
        )
        
        # Step 3: Formatting phase
        final_result = await handoff(
            from_agent=crew_agent,
            to_agent=oa_agent,
            message=f"Format this analysis as a markdown report: {analysis_result}"
        )
        
        # Verify workflow execution
        assert "Research" in research_result
        assert "Analysis" in analysis_result
        assert "Final Report" in final_result
        assert "Markdown" in final_result
        
        # Verify each agent was called with appropriate input
        runtime.run_agent.assert_called_once()
        crew_agent.run.assert_called_once()
        oa_agent.run.assert_called_once()
        
        # Restore original run_agent method
        runtime.run_agent = original_run_agent
        
        # Stop agents
        await runtime.stop_agent(research_id)
        await runtime.stop_agent(analysis_id)
        await runtime.stop_agent(format_id) 