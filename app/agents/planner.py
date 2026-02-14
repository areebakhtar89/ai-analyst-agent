"""Planner agent for creating data analysis strategies.

This module contains the planner node that analyzes user questions
and creates step-by-step plans for answering them using SQL and visualization.
"""

from app.core.llm import get_llm
from app.agents.state import AgentState


def planner_node(state: AgentState) -> AgentState:
    """Generate an analysis plan for the user's question.
    
    Takes the user's natural language question and creates a structured
    plan for how to answer it using SQL queries and data visualization.
    
    Args:
        state: Current workflow state containing the user's question
        
    Returns:
        Updated state with the analysis plan added
    """
    # Get the LLM instance for generating the plan
    llm = get_llm()

    # Create prompt for the planner agent
    prompt = f"""
You are a data analyst.

Create a short step-by-step plan to answer this question using SQL and charts.

Question:
{state['question']}
"""

    # Generate the analysis plan
    response = llm.invoke(prompt)

    # Store the plan in the state
    state["plan"] = response.content
    return state