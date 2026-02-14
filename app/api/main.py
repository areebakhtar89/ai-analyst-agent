"""FastAPI backend for the AI Analyst Agent.

This module provides the REST API endpoints that serve as the interface
between the Streamlit frontend and the LangGraph agent workflow.
"""

from fastapi import FastAPI
from app.agents.graph import build_graph

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


@app.post("/query")
def query_agent(payload: dict):
    """Process a natural language data analysis query.
    
    Takes a user question and processes it through the multi-agent workflow
    to generate SQL, execute it, extract insights, and create visualizations.
    
    Args:
        payload: Dictionary containing the user's question
        
    Returns:
        Dictionary containing the complete analysis results:
        - plan: Analysis strategy
        - sql: Generated SQL query
        - result: Query execution results
        - insights: Business insights
        - chart_path: Path to generated chart
        - chart_type: Type of chart created
    """
    # Extract the user's question from the request payload
    question = payload.get("question")

    # Initialize the workflow state with default values
    state = {
        "question": question,
        "plan": "",
        "sql": "",
        "result": [],
        "insights": "",
        "chart_path": "",
        "chart_type": ""
    }

    # Execute the complete agent workflow
    output = graph.invoke(state)

    # Return the analysis results to the frontend
    return {
        "plan": output["plan"],
        "sql": output["sql"],
        "result": output["result"],
        "insights": output["insights"],
        "chart_path": output["chart_path"],
        "chart_type": output["chart_type"]
    }