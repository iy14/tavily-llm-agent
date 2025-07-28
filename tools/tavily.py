import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
client = TavilyClient(TAVILY_API_KEY)

def tavily_search(state):
    """Simple search function that uses query from state"""
    query = state.get("query", "")
    time_period = state.get("time_period", "day")

    try:
        response = client.search(
            query=query,
            search_depth="advanced",
            exclude_domains=["youtube.com"],
            time_range=time_period,
        )
        return {
            **state,
            "results": response.get("results", []),
        }
    except Exception as e:
        return {**state, "results": []}
