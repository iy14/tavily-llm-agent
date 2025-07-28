from langgraph.graph import StateGraph, END
from tools.tavily import tavily_search
from tools.openai_summarizer import summarize_content, select_top_points
from typing import TypedDict, Annotated

# Define the state schema
class GraphState(TypedDict):
    profession: str
    time_period: str
    query: str  # Current query being processed
    results: list  # Current search results
    content_type: str  # "news" or "tools" for summarization
    news_results: list  # News search results
    tools_results: list  # Tools search results
    news_summary: str  # OpenAI summary of news (all results as numbered points)
    tools_summary: str  # OpenAI summary of tools (all results as numbered points)
    final_summary: str  # Top 5 most relevant non-redundant points
    newsletter: str

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


def prepare_news_query(state: GraphState) -> GraphState:
    """Set query for AI news search"""
    profession = state.get("profession", "professionals")
    query = f"what are the latest ai news for {profession}s?"
    return {**state, "query": query}


def store_news_results(state: GraphState) -> GraphState:
    """Store search results as news_results and set content_type"""
    results = state.get("results", [])
    return {**state, "news_results": results, "content_type": "news"}


def prepare_tools_query(state: GraphState) -> GraphState:
    """Set query for AI tools search"""
    profession = state.get("profession", "professionals")
    query = f"what are the latest ai tools for {profession}s?"
    return {**state, "query": query}


def store_tools_results(state: GraphState) -> GraphState:
    """Store search results as tools_results and set content_type"""
    results = state.get("results", [])
    return {**state, "tools_results": results, "content_type": "tools"}


def create_final_newsletter(state: GraphState) -> GraphState:
    """Create final newsletter with the top 5 curated points"""
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

    return {**state, "newsletter": newsletter.strip()}


def build_graph():
    # Create the graph with the state schema
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("input_handler", input_handler)
    workflow.add_node("prepare_news_query", prepare_news_query)
    workflow.add_node("search_news", tavily_search)
    workflow.add_node("store_news_results", store_news_results)
    workflow.add_node("summarize_news", summarize_content)
    workflow.add_node("prepare_tools_query", prepare_tools_query)
    workflow.add_node("search_tools", tavily_search)
    workflow.add_node("store_tools_results", store_tools_results)
    workflow.add_node("summarize_tools", summarize_content)
    workflow.add_node("select_top_points", select_top_points)
    workflow.add_node("create_final_newsletter", create_final_newsletter)

    # Set entry point
    workflow.set_entry_point("input_handler")

    # Add edges for the flow
    workflow.add_edge("input_handler", "prepare_news_query")
    workflow.add_edge("prepare_news_query", "search_news")
    workflow.add_edge("search_news", "store_news_results")
    workflow.add_edge("store_news_results", "summarize_news")
    workflow.add_edge("summarize_news", "prepare_tools_query")
    workflow.add_edge("prepare_tools_query", "search_tools")
    workflow.add_edge("search_tools", "store_tools_results")
    workflow.add_edge("store_tools_results", "summarize_tools")
    workflow.add_edge("summarize_tools", "select_top_points")
    workflow.add_edge("select_top_points", "create_final_newsletter")
    workflow.add_edge("create_final_newsletter", END)

    return workflow.compile()
