"""FastAPI backend for the AI Analyst Agent.

This module provides the REST API endpoints that serve as the interface
between the Streamlit frontend and the LangGraph agent workflow.
"""

from fastapi import FastAPI
from app.agents.graph import build_graph
import math

# Initialize FastAPI application
app = FastAPI(title="AI Analyst Agent API", description="API for data analysis using AI agents")

# Build and initialize the agent workflow graph
graph = build_graph()


@app.get("/")
def root():
    """Root endpoint to check API status.
    
    Returns:
        Status message indicating the API is running
    """
    return {"message": "AI Analyst API running"}

def clean_result(result):
    """
    Replace NaN or infinite values with None for JSON safety.
    """
    cleaned = []
    for row in result:
        clean_row = {}
        for k, v in row.items():
            if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                clean_row[k] = None
            else:
                clean_row[k] = v
        cleaned.append(clean_row)
    return cleaned

@app.post("/query")
def query_agent(payload: dict):

    question = payload.get("question")


    state = {
        "question": question,
        "plan": "",
        "sql": "",
        "result": [],
        "insights": "",
        "chart_path": "",
        "chart_type": "",
        "error": "",
        "retry_count": 0
    }


    output = graph.invoke(state)


    cleaned_result = clean_result(output.get("result", []))

    return {
        "plan": output.get("plan", ""),
        "sql": output.get("sql", ""),
        "result": cleaned_result,
        "insights": output.get("insights", ""),
        "chart_path": output.get("chart_path", ""),
        "chart_type": output.get("chart_type", "")
    }

