"""Analysis agent for extracting business insights.

This module contains the analysis node that processes SQL query results
and generates meaningful business insights using LLM analysis.
"""

from app.core.llm import get_llm
from app.agents.state import AgentState


def analysis_node(state: AgentState) -> AgentState:
    """Generate business insights from SQL query results.
    
    Takes the raw query results and uses an LLM to extract meaningful
    business insights and patterns from the data.
    
    Args:
        state: Current workflow state containing query results
        
    Returns:
        Updated state with business insights added
    """
    # Debug output to see raw results
    print("RAW RESULT:", state["result"])
    
    # Get the LLM instance for analysis
    llm = get_llm()

    # Create prompt for business analysis
    prompt = f"""
You are a business analyst.

Here is the result of a SQL query:

{state['result']}

Write 2–3 short insights.
"""

    # Generate business insights
    response = llm.invoke(prompt)
    
    # Store insights in the state
    state["insights"] = response.content
    return state