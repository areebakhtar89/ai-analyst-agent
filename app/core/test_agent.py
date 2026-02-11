from app.agents.sql_agent import run_agent

if __name__ == "__main__":
    question = "Show top 3 customers by revenue"
    output = run_agent(question)

    print("Question:", output["question"])
    print("Generated SQL:", output["sql"])
    print("Result:", output["result"])
