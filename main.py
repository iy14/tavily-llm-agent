from workflows.ai_newsletter_graph import build_graph
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

if __name__ == "__main__":

    uri = "mongodb+srv://itamaryacoby:itamarmongo123@tavily-llm-agent.fd6pq9y.mongodb.net/?retryWrites=true&w=majority&appName=tavily-llm-agent"

    # Create a new client and connect to the server
    client = MongoClient(uri, server_api=ServerApi("1"))

    # Send a ping to confirm a successful connection
    try:
        client.admin.command("ping")
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)
    # graph = build_graph()

    # # Test the new workflow with both news and tools flows
    # result = graph.invoke(
    #     {
    #         "profession": "software engineer",
    #         "time_period": "day",  # Can be "day", "week", or "month"
    #     }
    # )

    # print("=== AI Newsletter with News & Tools ===")
    # print(result.get("newsletter", result))
