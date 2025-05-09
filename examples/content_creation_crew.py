"""
Content Creation Pipeline Example with CrewAI

This example demonstrates how to build a content creation pipeline using:
- Contexa SDK as the foundation
- CrewAI as the multi-agent orchestration framework
- Multiple specialized agents working together to create content
- Tools for research, writing, editing, and SEO optimization

The pipeline includes:
1. A research agent to gather information on a topic
2. A writing agent to draft content based on research
3. An editing agent to refine and improve the content
4. An SEO agent to optimize content for search engines
"""

import asyncio
import os
import json
import re
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime

# Import Contexa SDK components
from contexa_sdk.core.tool import ContexaTool, ToolOutput
from contexa_sdk.core.model import ContexaModel
from contexa_sdk.core.agent import ContexaAgent
from contexa_sdk.adapters.crewai import agent as crew_agent
from contexa_sdk.adapters.crewai import task as crew_task
from contexa_sdk.adapters.crewai import crew as crew_crew

# Tool input schemas
class WebResearchInput(BaseModel):
    """Input for web research."""
    topic: str = Field(description="Topic to research")
    depth: int = Field(1, description="Research depth (1-3)")
    sources: int = Field(3, description="Number of sources to consult")

class ContentOutlineInput(BaseModel):
    """Input for creating content outlines."""
    topic: str = Field(description="Topic for the content")
    research: Dict[str, Any] = Field(description="Research data to base the outline on")
    style: str = Field(description="Content style (informative, persuasive, tutorial, etc.)")
    sections: int = Field(5, description="Number of sections to include")

class ContentDraftInput(BaseModel):
    """Input for drafting content."""
    topic: str = Field(description="Topic of the content")
    outline: Dict[str, Any] = Field(description="Content outline to follow")
    tone: str = Field(description="Tone of the content (casual, professional, etc.)")
    word_count: int = Field(1000, description="Target word count")

class ContentEditInput(BaseModel):
    """Input for editing content."""
    draft: str = Field(description="Content draft to edit")
    edit_level: str = Field(description="Level of editing (light, medium, heavy)")
    focus_areas: List[str] = Field(description="Areas to focus on when editing")

class SeoOptimizationInput(BaseModel):
    """Input for SEO optimization."""
    content: str = Field(description="Content to optimize")
    target_keywords: List[str] = Field(description="Target keywords to include")
    metadata: Optional[Dict[str, str]] = Field(None, description="Metadata for SEO")

# Tool implementations
@ContexaTool.register(
    name="web_research",
    description="Research a topic on the web and return structured information",
)
async def web_research(input_data: WebResearchInput) -> ToolOutput:
    """Research a topic on the web and return structured information."""
    # In a real implementation, this would use search APIs or web scraping
    # For this example, we'll simulate research results
    
    await asyncio.sleep(2)  # Simulate research time
    
    # Generate fake research results based on the topic
    topic = input_data.topic.lower()
    
    # Simulated research data
    research_data = {
        "sources": [
            {
                "title": f"Complete Guide to {input_data.topic}",
                "url": f"https://example.com/guide-to-{topic.replace(' ', '-')}",
                "summary": f"This comprehensive guide covers all aspects of {input_data.topic}, including history, best practices, and future trends."
            },
            {
                "title": f"{input_data.topic} Strategies for 2025",
                "url": f"https://example.com/{topic.replace(' ', '-')}-strategies",
                "summary": f"Expert analysis of effective {input_data.topic} strategies that are proven to work in today's rapidly changing environment."
            },
            {
                "title": f"The Evolution of {input_data.topic}",
                "url": f"https://example.com/evolution-of-{topic.replace(' ', '-')}",
                "summary": f"Tracing the history and development of {input_data.topic} from its origins to the present day, with insights on where it's heading."
            }
        ],
        "key_points": [
            f"{input_data.topic} has seen significant growth in the last 5 years",
            f"The most effective approach to {input_data.topic} involves strategic planning and continuous optimization",
            f"Experts predict {input_data.topic} will continue to evolve with technological advancements",
            f"Common challenges in {input_data.topic} include resource constraints and keeping up with best practices",
            f"Case studies show that successful implementation of {input_data.topic} can lead to 30% improved outcomes"
        ],
        "statistics": [
            f"87% of organizations plan to increase their {input_data.topic} investment in 2025",
            f"Companies that prioritize {input_data.topic} see 23% higher customer satisfaction",
            f"Only 35% of professionals feel they have mastered {input_data.topic} techniques"
        ]
    }
    
    return ToolOutput(
        content=f"Completed research on {input_data.topic}. Found {len(research_data['sources'])} sources with {len(research_data['key_points'])} key points.",
        json_data=research_data
    )

@ContexaTool.register(
    name="create_content_outline",
    description="Create a structured outline for content based on research",
)
async def create_content_outline(input_data: ContentOutlineInput) -> ToolOutput:
    """Create a structured outline for content based on research."""
    # Generate an outline based on the research data and requested style
    
    # Create section titles based on research key points
    key_points = input_data.research.get("key_points", [])
    statistics = input_data.research.get("statistics", [])
    
    # Generate creative section titles based on the topic and style
    section_titles = []
    for i in range(min(input_data.sections, len(key_points))):
        point = key_points[i]
        title = f"Section {i+1}: {re.sub(r'^[a-z]', lambda m: m.group(0).upper(), point)}"
        section_titles.append(title)
        
    # Create the outline structure
    outline = {
        "title": f"The Ultimate Guide to {input_data.topic}",
        "style": input_data.style,
        "introduction": f"An engaging introduction to {input_data.topic} that hooks the reader and establishes the importance of the subject.",
        "sections": section_titles,
        "conclusion": f"A compelling conclusion that summarizes key points about {input_data.topic} and provides actionable next steps.",
        "suggested_statistics": statistics[:3] if statistics else [],
        "estimated_word_count": input_data.sections * 200 + 300  # Intro + each section + conclusion
    }
    
    return ToolOutput(
        content=f"Created a {input_data.style} outline for {input_data.topic} with {len(section_titles)} sections.",
        json_data=outline
    )

@ContexaTool.register(
    name="draft_content",
    description="Draft content based on an outline",
)
async def draft_content(input_data: ContentDraftInput) -> ToolOutput:
    """Draft content based on an outline."""
    # In a real implementation, this might use a separate LLM call
    # For this example, we'll simulate content generation
    
    await asyncio.sleep(3)  # Simulate writing time
    
    # Create structure for the draft
    title = input_data.outline.get("title", f"Article about {input_data.topic}")
    sections = input_data.outline.get("sections", [])
    
    # Generate a simple placeholder for each section
    content_parts = [
        f"# {title}\n\n",
        "_Published: {datetime.now().strftime('%B %d, %Y')}_\n\n",
        "## Introduction\n\n",
        f"Welcome to our comprehensive guide on {input_data.topic}. In this article, we'll explore the key aspects of this subject and provide actionable insights you can apply immediately.\n\n"
    ]
    
    # Add sections
    for section in sections:
        content_parts.append(f"## {section}\n\n")
        content_parts.append(f"This section would contain detailed information about {section.split(': ')[1] if ': ' in section else section}. In a real article, this would be 200-300 words of informative content written in a {input_data.tone} tone.\n\n")
    
    # Add conclusion
    content_parts.append("## Conclusion\n\n")
    content_parts.append(f"In conclusion, {input_data.topic} represents an important area that continues to evolve. By applying the principles discussed in this article, you can improve your understanding and implementation of these concepts.\n\n")
    
    # Join all parts
    draft = "".join(content_parts)
    
    # Calculate approximate word count
    word_count = len(draft.split())
    
    result = {
        "draft": draft,
        "word_count": word_count,
        "title": title,
        "tone": input_data.tone
    }
    
    return ToolOutput(
        content=f"Created a {word_count}-word draft on {input_data.topic} in a {input_data.tone} tone.",
        json_data=result
    )

@ContexaTool.register(
    name="edit_content",
    description="Edit and refine content drafts",
)
async def edit_content(input_data: ContentEditInput) -> ToolOutput:
    """Edit and refine content drafts."""
    # In a real implementation, this would use sophisticated NLP for editing
    # For this example, we'll simulate editing with some basic replacements
    
    draft = input_data.draft
    edit_level = input_data.edit_level
    focus_areas = input_data.focus_areas
    
    # Simulate different levels of editing
    if edit_level == "light":
        # Light editing - fix obvious placeholder text
        draft = draft.replace("would contain detailed information about", "explores the important aspects of")
        draft = draft.replace("would be 200-300 words", "provides comprehensive coverage")
    elif edit_level == "medium":
        # Medium editing - more substantial changes
        draft = draft.replace("would contain detailed information about", "delves into the critical elements of")
        draft = draft.replace("would be 200-300 words", "thoroughly examines")
        draft = draft.replace("Welcome to our comprehensive guide", "In this definitive resource")
    elif edit_level == "heavy":
        # Heavy editing - significant rewriting
        draft = draft.replace("would contain detailed information about", "presents an in-depth analysis of")
        draft = draft.replace("would be 200-300 words", "offers readers actionable insights on")
        draft = draft.replace("Welcome to our comprehensive guide", "Discover the essential knowledge")
        draft = draft.replace("In conclusion", "To summarize these key insights")
    
    # Apply focus area edits
    edits_applied = []
    for area in focus_areas:
        if area.lower() == "clarity":
            # Simulate clarity improvements
            draft = draft.replace("this subject", "this important topic")
            edits_applied.append("Improved clarity of references")
        elif area.lower() == "engagement":
            # Simulate engagement improvements
            draft = draft.replace("you can improve", "you'll be able to dramatically enhance")
            edits_applied.append("Enhanced engagement with stronger language")
        elif area.lower() == "grammar":
            # Simulate grammar checks
            draft = draft.replace("  ", " ")  # Fix double spaces
            edits_applied.append("Corrected grammatical issues")
            
    result = {
        "edited_content": draft,
        "edit_level": edit_level,
        "edits_applied": edits_applied,
        "word_count": len(draft.split())
    }
    
    return ToolOutput(
        content=f"Applied {edit_level} editing with focus on {', '.join(focus_areas)}. Made {len(edits_applied)} types of edits.",
        json_data=result
    )

@ContexaTool.register(
    name="optimize_seo",
    description="Optimize content for search engines",
)
async def optimize_seo(input_data: SeoOptimizationInput) -> ToolOutput:
    """Optimize content for search engines."""
    content = input_data.content
    keywords = input_data.target_keywords
    
    # Simple SEO optimization simulation
    optimization_notes = []
    
    # Check keyword presence
    keyword_counts = {}
    for keyword in keywords:
        count = content.lower().count(keyword.lower())
        keyword_counts[keyword] = count
        
        if count == 0:
            # Simulate adding the keyword
            if "# " in content and "\n\n" in content:
                # Add after the title
                title_end = content.find("\n\n", content.find("# ")) + 2
                content = content[:title_end] + f"Keywords: {keyword}, " + content[title_end:]
                optimization_notes.append(f"Added missing keyword '{keyword}'")
        elif count < 3:
            optimization_notes.append(f"Keyword '{keyword}' appears only {count} times - consider adding more instances")
    
    # Check heading structure
    if "# " in content and "## " in content:
        optimization_notes.append("✓ Proper heading structure detected (H1, H2)")
    else:
        optimization_notes.append("⚠️ Improve heading structure with clear H1 and H2 headings")
    
    # Check content length
    word_count = len(content.split())
    if word_count < 500:
        optimization_notes.append(f"⚠️ Content length ({word_count} words) is below recommended minimum of 500 words")
    else:
        optimization_notes.append(f"✓ Content length ({word_count} words) is adequate for SEO")
    
    # Generate metadata
    meta_description = content.split("\n\n")[1] if len(content.split("\n\n")) > 1 else content[:160]
    meta_description = meta_description[:157] + "..." if len(meta_description) > 160 else meta_description
    
    # Generate SEO-optimized title
    main_title = content.split("\n")[0].replace("# ", "") if "# " in content.split("\n")[0] else f"Guide to {keywords[0] if keywords else 'Topic'}"
    seo_title = f"{main_title} | {keywords[0].title() if keywords else 'Complete Guide'}"
    
    metadata = input_data.metadata or {}
    metadata.update({
        "title": seo_title[:60],
        "description": meta_description,
        "keywords": ", ".join(keywords)
    })
    
    result = {
        "optimized_content": content,
        "metadata": metadata,
        "keyword_counts": keyword_counts,
        "optimization_notes": optimization_notes
    }
    
    return ToolOutput(
        content=f"SEO optimization complete. Applied {len(optimization_notes)} optimizations.",
        json_data=result
    )

# Create the specialized agents for the content creation crew
async def create_content_creation_crew():
    """Create a CrewAI crew for content creation."""
    # Define the model to use for all agents
    model = ContexaModel(
        provider="openai", 
        model_id="gpt-4",
        temperature=0.7  # Higher temperature for creativity
    )
    
    # 1. Research Agent
    research_agent = ContexaAgent(
        name="Research Specialist",
        description="Researches topics and gathers comprehensive information",
        tools=[web_research],
        model=model,
        system_prompt="""
        You are a research specialist who gathers in-depth information on topics.
        You're meticulous about finding high-quality sources and extracting key insights.
        Focus on finding diverse perspectives and factual information.
        Always cite your sources and organize information in a structured way.
        """
    )
    
    # 2. Content Outline Agent
    outline_agent = ContexaAgent(
        name="Content Strategist",
        description="Creates structured content outlines based on research",
        tools=[create_content_outline],
        model=model,
        system_prompt="""
        You are a content strategist who creates well-structured outlines.
        Your outlines should have a logical flow and cover the topic comprehensively.
        Consider the audience and purpose of the content when creating outlines.
        Focus on creating section titles that are informative and engaging.
        """
    )
    
    # 3. Content Writing Agent
    writing_agent = ContexaAgent(
        name="Content Writer",
        description="Writes high-quality content based on outlines",
        tools=[draft_content],
        model=model,
        system_prompt="""
        You are a skilled content writer who creates engaging, informative content.
        You write in a clear, conversational style that's easy to understand.
        Your content should always follow the provided outline while adding value.
        Pay attention to flow, transitions, and maintaining a consistent tone.
        """
    )
    
    # 4. Editing Agent
    editing_agent = ContexaAgent(
        name="Content Editor",
        description="Refines and improves content drafts",
        tools=[edit_content],
        model=model,
        system_prompt="""
        You are a detail-oriented editor who refines content to make it exceptional.
        You focus on clarity, coherence, grammar, and engagement.
        Your edits should maintain the author's voice while improving the quality.
        Provide constructive feedback and suggest improvements rather than just making changes.
        """
    )
    
    # 5. SEO Agent
    seo_agent = ContexaAgent(
        name="SEO Specialist",
        description="Optimizes content for search engines",
        tools=[optimize_seo],
        model=model,
        system_prompt="""
        You are an SEO specialist who optimizes content for better search visibility.
        You know how to strategically place keywords without compromising quality.
        You understand the importance of metadata, headings, and content structure for SEO.
        Your optimizations should enhance, not detract from, the user experience.
        """
    )
    
    # Convert to CrewAI agents
    crew_research_agent = crew_agent(research_agent)
    crew_outline_agent = crew_agent(outline_agent)
    crew_writing_agent = crew_agent(writing_agent)
    crew_editing_agent = crew_agent(editing_agent)
    crew_seo_agent = crew_agent(seo_agent)
    
    # Create tasks for each agent
    research_task = crew_task(
        "Research the topic thoroughly",
        crew_research_agent,
        expected_output="Comprehensive research on the topic"
    )
    
    outline_task = crew_task(
        "Create a content outline based on research",
        crew_outline_agent,
        expected_output="Structured content outline"
    )
    
    writing_task = crew_task(
        "Write content based on the outline",
        crew_writing_agent,
        expected_output="First draft of content"
    )
    
    editing_task = crew_task(
        "Edit and refine the content",
        crew_editing_agent,
        expected_output="Polished content"
    )
    
    seo_task = crew_task(
        "Optimize content for search engines",
        crew_seo_agent,
        expected_output="SEO-optimized content with metadata"
    )
    
    # Create the crew with a process flow
    content_crew = crew_crew(
        "Content Creation Crew",
        [
            crew_research_agent, 
            crew_outline_agent, 
            crew_writing_agent, 
            crew_editing_agent, 
            crew_seo_agent
        ],
        tasks=[
            research_task,
            outline_task,
            writing_task,
            editing_task,
            seo_task
        ],
        verbose=True  # Enable detailed logging
    )
    
    return content_crew

# Example usage
async def run_content_creation_example():
    print("🔄 Creating Content Creation Crew with CrewAI...")
    crew = await create_content_creation_crew()
    
    print("\n📝 Running Content Creation Process...")
    # In actual CrewAI, you would use crew.run() - here we're simulating
    try:
        result = await simulate_crew_execution(crew, "artificial intelligence in healthcare")
        print(f"\n✅ Content Creation Process Complete!")
        
        # Print the final output
        if "final_content" in result:
            print("\n📄 Final Content Preview (truncated):")
            print(result["final_content"][:500] + "...\n")
        
        print("🔍 SEO Metadata:")
        if "metadata" in result:
            for key, value in result["metadata"].items():
                print(f"  - {key}: {value}")
    
    except Exception as e:
        print(f"❌ Error in content creation process: {str(e)}")
    
    return None

# Function to simulate CrewAI execution (since we don't have actual CrewAI integration)
async def simulate_crew_execution(crew, topic):
    """Simulate the execution of a CrewAI crew."""
    print("\n🔎 [Research Agent] Researching the topic...")
    research_result = await web_research(WebResearchInput(topic=topic, depth=2, sources=5))
    research_data = research_result.json_data
    
    print(f"✅ Research complete. Found {len(research_data['sources'])} sources.")
    
    print("\n📋 [Content Strategist] Creating content outline...")
    outline_result = await create_content_outline(ContentOutlineInput(
        topic=topic,
        research=research_data,
        style="informative",
        sections=5
    ))
    outline_data = outline_result.json_data
    
    print(f"✅ Outline created with {len(outline_data['sections'])} sections.")
    
    print("\n✍️ [Content Writer] Drafting content...")
    draft_result = await draft_content(ContentDraftInput(
        topic=topic,
        outline=outline_data,
        tone="professional",
        word_count=1200
    ))
    draft_data = draft_result.json_data
    
    print(f"✅ Draft created with {draft_data['word_count']} words.")
    
    print("\n🖋️ [Content Editor] Editing content...")
    edit_result = await edit_content(ContentEditInput(
        draft=draft_data['draft'],
        edit_level="medium",
        focus_areas=["clarity", "engagement", "grammar"]
    ))
    edit_data = edit_result.json_data
    
    print(f"✅ Editing complete. Applied {len(edit_data['edits_applied'])} types of edits.")
    
    print("\n🔍 [SEO Specialist] Optimizing for search engines...")
    keywords = [topic, "healthcare AI", "medical technology", "AI diagnosis", "healthcare innovation"]
    seo_result = await optimize_seo(SeoOptimizationInput(
        content=edit_data['edited_content'],
        target_keywords=keywords
    ))
    seo_data = seo_result.json_data
    
    print(f"✅ SEO optimization complete with {len(seo_data['optimization_notes'])} optimizations.")
    
    # Compile the final result
    final_result = {
        "final_content": seo_data["optimized_content"],
        "metadata": seo_data["metadata"],
        "word_count": len(seo_data["optimized_content"].split()),
        "process_stages": {
            "research": research_data,
            "outline": outline_data,
            "draft": draft_data,
            "edit": edit_data,
            "seo": seo_data
        }
    }
    
    return final_result

if __name__ == "__main__":
    asyncio.run(run_content_creation_example()) 