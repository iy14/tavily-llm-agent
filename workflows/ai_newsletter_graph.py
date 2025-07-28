from langgraph.graph import StateGraph, END
from tools.tavily import tavily_search
from typing import TypedDict, Annotated

# Define the state schema
class GraphState(TypedDict):
    profession: str
    search_results: str
    newsletter: str

# Placeholder functions (will implement later)
def input_handler(state: GraphState) -> GraphState:
    # Add some context and formatting to the profession
    profession = state.get("profession", "")
    if profession:
        # Capitalize and add some context
        formatted_profession = profession.title()
        state["profession"] = formatted_profession
    return state

def llm_summarizer(state: GraphState) -> GraphState:
    profession = state.get("profession", "Professional")
    search_results = state.get("search_results", "No results found.")
    
    # Create a structured newsletter format
    newsletter = f"""
🤖 AI Newsletter for {profession}s
{'=' * (20 + len(profession))}

📰 Latest AI News & Insights

{search_results}

---
📅 Generated on: {__import__('datetime').datetime.now().strftime('%B %d, %Y')}
🎯 Tailored for: {profession}s
"""
    
    return {**state, "newsletter": newsletter.strip()}

def build_graph():
    # Create the graph with the state schema
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("input_handler", input_handler)
    workflow.add_node("tavily_search", tavily_search)
    workflow.add_node("llm_summarizer", llm_summarizer)
    
    # Set entry point
    workflow.set_entry_point("input_handler")
    
    # Add edges
    workflow.add_edge("input_handler", "tavily_search")
    workflow.add_edge("tavily_search", "llm_summarizer")
    workflow.add_edge("llm_summarizer", END)
    
    return workflow.compile()
