"""Main workflow graph builder for the AI Analyst Agent.

This module defines the LangGraph workflow that orchestrates the multi-agent
pipeline for data analysis, including planning, SQL generation, analysis,
and visualization.
"""

from langgraph.graph import StateGraph, END
from app.agents.state import AgentState
from app.agents.planner import planner_node
from app.agents.sql_node import sql_node
from app.agents.analysis import analysis_node
from app.agents.visualization import visualization_node


def build_graph():
    """Build and compile the LangGraph workflow for data analysis.
    
    Creates a StateGraph with four specialized nodes:
    1. planner - Creates analysis plan
    2. sql_agent - Generates and executes SQL queries
    3. analysis - Extracts business insights
    4. viz - Creates data visualizations
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Initialize the StateGraph with our shared state schema
    workflow = StateGraph(AgentState)

    # Add specialized agent nodes to the workflow
    workflow.add_node("planner", planner_node)
    workflow.add_node("sql_agent", sql_node)
    workflow.add_node("analysis", analysis_node)
    workflow.add_node("viz", visualization_node)

    # Set the entry point for the workflow
    workflow.set_entry_point("planner")

    # Define the sequential flow between agents
    workflow.add_edge("planner", "sql_agent")
    workflow.add_edge("sql_agent", "analysis")
    workflow.add_edge("analysis", "viz")
    workflow.add_edge("viz", END)

    # Compile the workflow for execution
    return workflow.compile()