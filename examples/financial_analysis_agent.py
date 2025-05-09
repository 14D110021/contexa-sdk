"""
Financial Analysis Agent Example with LangChain

This example demonstrates how to build a complex financial analysis agent using:
- Contexa SDK as the foundation
- LangChain as the agent framework
- PDF parsing tools for extracting financial data
- Data visualization tools for creating charts and graphs
- Financial analysis tools for computing metrics

The agent can:
1. Extract financial data from PDF reports
2. Calculate financial metrics and ratios
3. Generate data visualizations
4. Provide analysis and recommendations
"""

import asyncio
import os
import json
import matplotlib.pyplot as plt
import pandas as pd
import io
import base64
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field

# Import Contexa SDK components
from contexa_sdk.core.tool import ContexaTool, ToolOutput
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.adapters.langchain import agent as lc_agent

# Tool input schemas
class PDFExtractionInput(BaseModel):
    """Input for extracting financial data from a PDF."""
    pdf_url: str = Field(description="URL to the financial PDF document")
    pages: Optional[List[int]] = Field(None, description="Specific pages to extract (optional)")
    tables: bool = Field(True, description="Whether to extract tables from the PDF")

class FinancialMetricsInput(BaseModel):
    """Input for calculating financial metrics."""
    revenue: float = Field(description="Revenue amount")
    costs: float = Field(description="Total costs")
    assets: float = Field(description="Total assets")
    liabilities: float = Field(description="Total liabilities")
    equity: float = Field(description="Shareholder equity")

class DataVisualizationInput(BaseModel):
    """Input for creating financial data visualizations."""
    data: Dict[str, List[Union[float, str]]] = Field(
        description="Financial data as a dictionary with keys as column names and values as lists"
    )
    chart_type: str = Field(description="Type of chart to create (bar, line, pie)")
    title: str = Field(description="Chart title")
    x_label: Optional[str] = Field(None, description="Label for x-axis")
    y_label: Optional[str] = Field(None, description="Label for y-axis")

class SentimentAnalysisInput(BaseModel):
    """Input for analyzing sentiment in financial reports."""
    text: str = Field(description="Financial text to analyze sentiment")

# Tool implementations
@ContexaTool.register(
    name="extract_financial_data_from_pdf",
    description="Extract financial data from PDF reports",
)
async def extract_financial_data_from_pdf(input_data: PDFExtractionInput) -> ToolOutput:
    """Extract financial data from PDF reports."""
    # In a real implementation, this would use a PDF parsing library
    # For this example, we'll simulate the extraction
    
    # Simulate processing time
    await asyncio.sleep(1)
    
    # Simulated extraction results
    financial_data = {
        "income_statement": {
            "revenue": 5432100,
            "costs": 4321000,
            "gross_profit": 1111100,
            "operating_expenses": 876500,
            "net_income": 234600
        },
        "balance_sheet": {
            "assets": 12500000,
            "liabilities": 7600000,
            "equity": 4900000
        },
        "cash_flow": {
            "operating_cash_flow": 456700,
            "investing_cash_flow": -234500,
            "financing_cash_flow": -89000,
            "net_cash_flow": 133200
        }
    }
    
    return ToolOutput(
        content=f"Successfully extracted financial data from {input_data.pdf_url}",
        json_data=financial_data
    )

@ContexaTool.register(
    name="calculate_financial_metrics",
    description="Calculate financial metrics and ratios from data",
)
async def calculate_financial_metrics(input_data: FinancialMetricsInput) -> ToolOutput:
    """Calculate key financial metrics and ratios."""
    # Calculate various financial metrics
    gross_profit_margin = (input_data.revenue - input_data.costs) / input_data.revenue
    net_profit_margin = (input_data.revenue - input_data.costs) / input_data.revenue
    debt_to_equity = input_data.liabilities / input_data.equity
    return_on_assets = (input_data.revenue - input_data.costs) / input_data.assets
    current_ratio = input_data.assets / input_data.liabilities
    
    metrics = {
        "gross_profit_margin": round(gross_profit_margin, 4),
        "net_profit_margin": round(net_profit_margin, 4),
        "debt_to_equity": round(debt_to_equity, 4),
        "return_on_assets": round(return_on_assets, 4),
        "current_ratio": round(current_ratio, 4)
    }
    
    return ToolOutput(
        content="Financial metrics calculated successfully",
        json_data=metrics
    )

@ContexaTool.register(
    name="create_financial_visualization",
    description="Create data visualizations for financial data",
)
async def create_financial_visualization(input_data: DataVisualizationInput) -> ToolOutput:
    """Create financial data visualizations."""
    # Convert input data to pandas DataFrame
    df = pd.DataFrame(input_data.data)
    
    # Create plt figure
    plt.figure(figsize=(10, 6))
    
    # Create the specified chart type
    if input_data.chart_type.lower() == 'bar':
        df.plot(kind='bar', title=input_data.title)
    elif input_data.chart_type.lower() == 'line':
        df.plot(kind='line', title=input_data.title)
    elif input_data.chart_type.lower() == 'pie' and len(df.columns) >= 1:
        # For pie charts, use the first numeric column
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) > 0:
            df[numeric_cols[0]].plot(kind='pie', title=input_data.title)
    else:
        return ToolOutput(
            content=f"Unsupported chart type: {input_data.chart_type}",
            json_data={"error": "Unsupported chart type"}
        )
    
    # Set labels if provided
    if input_data.x_label:
        plt.xlabel(input_data.x_label)
    if input_data.y_label:
        plt.ylabel(input_data.y_label)
    
    # Save the chart to a bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    
    # Encode the image as base64
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    
    plt.close()  # Close the figure to free memory
    
    return ToolOutput(
        content=f"Created {input_data.chart_type} chart: {input_data.title}",
        json_data={"image_data": img_base64}
    )

@ContexaTool.register(
    name="analyze_financial_sentiment",
    description="Analyze sentiment in financial reports and news",
)
async def analyze_financial_sentiment(input_data: SentimentAnalysisInput) -> ToolOutput:
    """Analyze sentiment in financial text."""
    # In a real implementation, this would use NLP or a sentiment analysis API
    # Here we'll simulate sentiment analysis with simple keyword matching
    
    positive_keywords = ["growth", "profit", "increase", "success", "opportunity", "positive", "strong"]
    negative_keywords = ["loss", "decline", "decrease", "risk", "debt", "negative", "weak"]
    
    text_lower = input_data.text.lower()
    
    positive_count = sum(1 for word in positive_keywords if word in text_lower)
    negative_count = sum(1 for word in negative_keywords if word in text_lower)
    
    # Calculate sentiment score (-1 to 1)
    total = positive_count + negative_count
    sentiment_score = 0 if total == 0 else (positive_count - negative_count) / total
    
    # Determine sentiment category
    if sentiment_score > 0.3:
        sentiment = "positive"
    elif sentiment_score < -0.3:
        sentiment = "negative"
    else:
        sentiment = "neutral"
    
    result = {
        "sentiment": sentiment,
        "score": round(sentiment_score, 2),
        "positive_keywords_found": positive_count,
        "negative_keywords_found": negative_count
    }
    
    return ToolOutput(
        content=f"Sentiment analysis complete. The text has a {sentiment} sentiment with score {sentiment_score:.2f}.",
        json_data=result
    )

# Main financial analysis agent function
async def create_financial_analysis_agent():
    """Create and configure the financial analysis agent."""
    # Register all the tools
    tools = [
        extract_financial_data_from_pdf,
        calculate_financial_metrics,
        create_financial_visualization,
        analyze_financial_sentiment
    ]
    
    # Create the model
    model = ContexaModel(
        provider="openai", 
        model_id="gpt-4",
        temperature=0.1
    )
    
    # Define the system prompt
    system_prompt = """
    You are a financial analysis assistant that helps users analyze financial reports and data.
    You can extract data from financial PDFs, calculate key metrics, create visualizations, and analyze sentiment.
    
    When analyzing financial data, consider these aspects:
    1. Profitability (margins, returns)
    2. Liquidity (ability to meet short-term obligations)
    3. Solvency (long-term financial stability)
    4. Efficiency (asset utilization)
    5. Growth (year-over-year changes)
    
    Always explain your analysis in clear terms that non-financial experts can understand.
    Provide specific recommendations based on the financial data.
    """
    
    # Create the Contexa agent
    financial_agent = ContexaAgent(
        name="Financial Analyst",
        description="Analyzes financial reports and provides insights and visualizations",
        tools=tools,
        model=model,
        system_prompt=system_prompt
    )
    
    # Convert to LangChain agent
    langchain_financial_agent = lc_agent(financial_agent)
    
    return langchain_financial_agent

# Example usage
async def run_financial_analysis_example():
    print("🔍 Creating Financial Analysis Agent with LangChain...")
    agent = await create_financial_analysis_agent()
    
    print("\n📊 Running Financial Analysis Query...")
    query = """
    I need to analyze the Q4 financial report for Acme Corp. The report is available at https://example.com/acme_q4_report.pdf.
    Extract the financial data, calculate key metrics, and create a bar chart of revenue vs. costs.
    Also, analyze the sentiment of this summary: "Despite market challenges, Acme Corp showed resilience with a modest 
    3% revenue growth, though profit margins decreased slightly due to increased operational costs and strategic investments 
    in R&D which are expected to yield returns in the coming fiscal year."
    """
    
    response = await agent.invoke({"input": query})
    print(f"\n🤖 Agent response: {response}")
    
    # In a real application, you would handle displaying the visualizations
    # For example, if response contains a base64 image, you would decode and display it
    
    return response

if __name__ == "__main__":
    asyncio.run(run_financial_analysis_example()) 