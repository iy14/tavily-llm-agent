from langgraph.graph import StateGraph, END, START
from langgraph.types import Send
from tools.tavily import tavily_search
from tools.openai_summarizer import summarize_content, select_top_points
from typing import TypedDict, Annotated
import operator

# Define the overall state schema
class GraphState(TypedDict):
    profession: str
    time_period: str
    # Use Annotated to collect results from parallel nodes
    search_results: Annotated[list, operator.add]
    summaries: Annotated[list, operator.add]
    final_summary: str
    newsletter: str


# State for individual search tasks
class SearchState(TypedDict):
    profession: str
    time_period: str
    search_type: str  # "news" or "tools"
    results: list
    summary: str


def input_handler(state: GraphState) -> GraphState:
    # Add some context and formatting to the profession
    profession = state.get("profession", "")
    if profession:
        # Capitalize and add some context
        formatted_profession = profession.title()
        state["profession"] = formatted_profession

    # Handle time period with default value
    time_period = state.get("time_period", "day")
    # Validate time period (ensure it's one of the valid options)
    valid_periods = ["day", "week", "month"]
    if time_period not in valid_periods:
        time_period = "day"  # Default to day if invalid
    state["time_period"] = time_period

    return state


def dispatch_searches(state: GraphState):
    """Dispatch parallel searches for news and tools"""
    return [
        Send(
            "search_and_summarize",
            {
                "profession": state["profession"],
                "time_period": state["time_period"],
                "search_type": "news",
            },
        ),
        Send(
            "search_and_summarize",
            {
                "profession": state["profession"],
                "time_period": state["time_period"],
                "search_type": "tools",
            },
        ),
    ]


def search_and_summarize(state: SearchState) -> GraphState:
    """Search and summarize for a specific type (news or tools)"""
    profession = state["profession"]
    time_period = state["time_period"]
    search_type = state["search_type"]

    # Create query based on search type
    if search_type == "news":
        query = f"what are the latest ai news for {profession}s?"
    else:  # tools
        query = f"what are the latest ai tools for {profession}s?"

    # Perform search
    try:
        from tools.tavily import client

        response = client.search(
            query=query,
            search_depth="advanced",
            exclude_domains=["youtube.com"],
            time_range=time_period,
        )
        results = response.get("results", [])
    except Exception as e:
        results = []

    # Summarize results
    if not results:
        summary = f"No recent AI {search_type} found."
    else:
        # Prepare content for OpenAI (max 5 results as specified)
        search_content = ""
        for i, result in enumerate(results[:5], 1):
            search_content += f"\n{i}. {result.get('title', '')}\n"
            search_content += f"   {result.get('content', '')}\n"
            search_content += f"   Source: {result.get('url', '')}\n"

        prompt = f"""Based on the following search results about AI {search_type} for {profession}, 
create a numbered point for EACH result provided. Each point should be:
- Numbered sequentially (1., 2., 3., etc.)
- Concise but informative summary of that specific result
- Specifically relevant to {profession}
- Based SOLELY on the provided search results
- MUST end with exactly "read more at: [URL]" (plain text, no markdown links)

Create one numbered point for each of the {len(results[:5])} results provided.

Search Results:
{search_content}

Please provide your response as numbered points, one for each result, ensuring each point ends with exactly "read more at: [URL]" in plain text format:"""

        try:
            from tools.openai_summarizer import client

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional AI {search_type} summarizer. Create one numbered point for each search result provided. Use plain text formatting only, no markdown links.",
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=500,
                temperature=0.3,
            )
            summary = response.choices[0].message.content.strip()
        except Exception as e:
            summary = f"Error summarizing {search_type}: {str(e)}"

    return {"summaries": [summary]}


def combine_and_select(state: GraphState) -> GraphState:
    """Select top points from all summaries"""
    profession = state.get("profession", "professionals")
    summaries = state.get("summaries", [])

    if not summaries or len(summaries) < 2:
        return {"final_summary": "No relevant AI updates found."}

    # Assume first summary is news, second is tools
    news_summary = summaries[0] if len(summaries) > 0 else ""
    tools_summary = summaries[1] if len(summaries) > 1 else ""

    # Combine all points
    all_points = f"""AI News Points:
{news_summary}

AI Tools Points:
{tools_summary}"""

    prompt = f"""From the following numbered points about AI news and tools for {profession}, 
select the MOST RELEVANT and important points for a {profession} looking for a general industry update.

Requirements:
- Choose AT MOST 5 points, but can be fewer if there isn't enough genuinely relevant information
- Only include points that are truly valuable and relevant to a {profession}
- No redundancy - avoid selecting points that cover similar topics
- Focus on practical value and actionable insights
- Re-number the selected points starting from 1.
- Keep the "read more at: [URL]" format exactly as provided (plain text, no markdown links)
- Mix news and tools based on relevance, not quota
- Quality over quantity - better to have 2-3 highly relevant points than 5 mediocre ones

All Available Points:
{all_points}

Please provide only the most relevant points (1-5 max), re-numbered sequentially, keeping the exact "read more at: [URL]" format:"""

    try:
        from tools.openai_summarizer import client

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": f"You are an expert curator selecting the most relevant AI updates for {profession}s. Focus on practical value and avoid redundancy. Use plain text formatting only, no markdown links.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=400,
            temperature=0.3,
        )
        final_summary = response.choices[0].message.content.strip()
        return {"final_summary": final_summary}
    except Exception as e:
        return {"final_summary": f"Error selecting top points: {str(e)}"}


def create_final_newsletter(state: GraphState) -> GraphState:
    """Create final newsletter with the top curated points"""
    profession = state.get("profession", "Professional")
    time_period = state.get("time_period", "day")
    final_summary = state.get("final_summary", "No relevant AI updates found.")

    # Create a structured newsletter format with the curated points
    newsletter = f"""
🤖 AI Updates for {profession}s
{'=' * (17 + len(profession))}

{final_summary}

---
📅 Generated on: {__import__('datetime').datetime.now().strftime('%B %d, %Y')}
🎯 Tailored for: {profession}s
⏰ Time Range: Last {time_period}
🔍 Curated from latest AI news and tools
"""

    return {"newsletter": newsletter.strip()}

def build_graph():
    # Create the graph with the state schema
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("input_handler", input_handler)
    workflow.add_node("search_and_summarize", search_and_summarize)
    workflow.add_node("combine_and_select", combine_and_select)
    workflow.add_node("create_final_newsletter", create_final_newsletter)

    # Set entry point
    workflow.set_entry_point("input_handler")

    # Add edges
    workflow.add_conditional_edges(
        "input_handler", dispatch_searches, ["search_and_summarize"]
    )
    workflow.add_edge("search_and_summarize", "combine_and_select")
    workflow.add_edge("combine_and_select", "create_final_newsletter")
    workflow.add_edge("create_final_newsletter", END)

    return workflow.compile()
