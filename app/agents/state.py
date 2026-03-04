"""
Shared state schema for the AI Analyst Agent workflow.

Defines the state object passed across all LangGraph agents.
"""

from typing import TypedDict, Any, List, Dict


class AgentState(TypedDict):
    # User input
    question: str

    # Conversational context
    context: str
    structured_memory: Dict[str, Any]

    # Planner output
    plan: str

    # SQL agent output
    sql: str

    # Query results
    result: List[Dict[str, Any]]

    # Analysis agent output
    insights: str

    # Visualization output
    chart_path: str
    chart_type: str

    # Error handling
    error: str
    retry_count: int