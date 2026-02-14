from app.agents.graph import build_graph

if __name__ == "__main__":
    graph = build_graph()

    state = {
        "question": "Year over year revenue growth",
        "plan": "",
        "sql": "",
        "result": [],
        "insights": "",
        "chart_path": ""
    }

    output = graph.invoke(state)

    print("Plan:\n", output["plan"])
    print("\nSQL:\n", output["sql"])
    print("\nResult:\n", output["result"])
    print("\nInsights:\n", output["insights"])
    print("\nChart saved at:", output["chart_path"])
