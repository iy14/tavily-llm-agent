import os
from dotenv import load_dotenv
from tavily import TavilyClient

load_dotenv()
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
client = TavilyClient(TAVILY_API_KEY)

def tavily_search(state):
    profession = state.get("profession", "")
    query = f"latest AI news for {profession}s"

    try:
        response = client.search(
            query=query,
            include_answer=True,
            search_depth="basic"
        )
        return {**state, "search_results": response.get("answer", "")}
    except Exception as e:
        return {**state, "search_results": f"Tavily error: {str(e)}"}
