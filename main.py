from workflows.ai_newsletter_graph import build_graph

if __name__ == "__main__":
    graph = build_graph()
    result = graph.invoke({"profession": "filmmaker"})
    print(result.get("newsletter", result))
